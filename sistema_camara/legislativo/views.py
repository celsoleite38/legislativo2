# legislativo/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
from .models import Projeto, Voto, TokenAtivacao, VereadorProfile, Configuracao
from .forms import ProjetoForm, UserCreationForm, VereadorProfileForm

TOTAL_VEREADORES = User.objects.count()

def check_is_secretaria(user):
    return user.groups.filter(name='Secretaria Geral').exists()

def check_is_gerente(user):
    return user.groups.filter(name='Gerente de Votação').exists()



# --- 1. Autenticação/Ativação da Secretaria ---

def ativar_conta_secretaria(request, token):
    try:
        token_ativacao = TokenAtivacao.objects.select_related('user').get(token=token)
    except TokenAtivacao.DoesNotExist:
        return render(request, 'legislativo/ativacao_invalida.html', {'mensagem': 'Token de ativação inválido.'})

    if timezone.now() > token_ativacao.expira_em:
        token_ativacao.delete()
        return render(request, 'legislativo/ativacao_invalida.html', {'mensagem': 'O token de ativação expirou.'})

    user = token_ativacao.user
    if user.is_active:
        return render(request, 'legislativo/ativacao_invalida.html', {'mensagem': 'Esta conta já está ativa.'})

    # Ativa a conta e remove o token
    user.is_active = True
    user.save()
    token_ativacao.delete()

    return render(request, 'legislativo/ativacao_sucesso.html', {'user': user})

def tela_principal(request):
    # Pega o projeto que está ATIVO ou o último FECHADO
    projeto = Projeto.objects.filter(status__in=['ABERTO', 'FECHADO']).order_by('-abertura_voto').first()
    
    context = {
        'projeto_ativo': projeto,
        'total_vereadores': TOTAL_VEREADORES
    }
    return render(request, 'legislativo/tela_principal.html', context)


# --- 2. Painel do Vereador/Gerente ---
@login_required
def painel_vereador(request):
    
    # 1. Redirecionamento da Secretaria Geral
    if check_is_secretaria(request.user):
        return redirect('legislativo:painel_secretaria')
        
    # 2. Redirecionamento do Presidente
    profile = getattr(request.user, 'vereadorprofile', None)
    if profile and profile.is_presidente:
        return redirect('legislativo:painel_vereador')
        
    # --- Lógica do Vereador Comum ---
    
    # Pega o projeto que está ABERTO para votação
    projeto_ativo = Projeto.objects.filter(status='ABERTO').order_by('-abertura_voto').first()

    # Inicializa voto_vereador para evitar o NameError se não houver projeto ativo
    voto_vereador = None 
    
    # Pega o perfil do vereador
    vereador_profile = get_object_or_404(VereadorProfile, user=request.user)
    
    if projeto_ativo:
        # Busca o voto do usuário para o projeto ativo
        voto_vereador = Voto.objects.filter(
            projeto=projeto_ativo, 
            vereador=request.user
        ).first()

    # Busca projetos na pauta (embora um vereador comum não deva interagir com eles,
    # mantemos a variável para consistência se você quiser exibir algo.)
    projetos_na_pauta = Projeto.objects.filter(status='PREPARACAO').order_by('id')


    context = {
        'projeto_ativo': projeto_ativo,
        'voto_vereador': voto_vereador,
        'vereador_profile': vereador_profile, # Adiciona o perfil do vereador
        'projetos_na_pauta': projetos_na_pauta, # Adicionada para que o template a use se necessário
    }
    return render(request, 'legislativo/painel_vereador.html', context)


@login_required
def painel_presidente(request):
        # Apenas o presidente pode acessar este painel
    profile = getattr(request.user, 'vereadorprofile', None)
    if not profile or not profile.is_presidente:
        return HttpResponseForbidden("Acesso negado. Você não é o Presidente da Câmara.")
        
    projeto_ativo = Projeto.objects.filter(status='ABERTO').order_by('-abertura_voto').first()
    
    # Projetos em pauta ou preparação
    projetos_na_pauta = Projeto.objects.filter(status__in=['PREPARACAO', 'EM_PAUTA']).order_by('id')
    projetos_encerrados = Projeto.objects.filter(status='FECHADO').order_by('-abertura_voto')[:5]
    
    # Vereadores ativos e ausentes
    vereadores_ativos = VereadorProfile.objects.filter(ativo=True).select_related('user').order_by('nome_completo')

    context = {
        'projeto_ativo': projeto_ativo,
        'projetos_na_pauta': projetos_na_pauta,
        'projetos_encerrados': projetos_encerrados,
        'vereadores_ativos': vereadores_ativos
    }
    return render(request, 'legislativo/painel_presidente.html', context)


@login_required
@require_POST
def votar(request, projeto_id):
    projeto = get_object_or_404(Projeto, pk=projeto_id)
    escolha = request.POST.get('escolha') 
    
    # 1. Validação de Abertura/Tempo
    agora = timezone.now()
    limite = projeto.abertura_voto + timedelta(seconds=projeto.tempo_limite_segundos)
    
    if projeto.status != 'ABERTO' or agora > limite:
        # Votação não está aberta ou tempo expirou
        # Se o tempo expirou, encerra a votação automaticamente
        if projeto.status == 'ABERTO' and agora > limite:
            projeto.status = 'FECHADO'
            projeto.save()
        return redirect('legislativo:painel_vereador') # Redireciona para o painel do vereador
        
    # 1.5. Validação de Ausência
    profile = get_object_or_404(VereadorProfile, user=request.user)
    if profile.ausente_na_sessao:
        messages.error(request, "Você está marcado como ausente e não pode votar.")
        return redirect('legislativo:painel_vereador') 

    # 2. Validação de Voto Único
    voto_existente = Voto.objects.filter(projeto=projeto, vereador=request.user).exists()
    if voto_existente:
        # Já votou
        return redirect('legislativo:painel_vereador')

    # 3. Cria e salva o voto
    Voto.objects.create(
        projeto=projeto, 
        vereador=request.user, 
        escolha=escolha
    )
    
    return redirect('legislativo:painel_vereador')

# --- 4. Ações do Gerente (Abrir/Fechar Votação) ---
def check_is_gerente(user):
    return user.groups.filter(name='Gerente de Votação').exists()

@login_required
def iniciar_votacao(request, projeto_id):
    profile = getattr(request.user, 'vereadorprofile', None)
    if not profile or not profile.is_presidente:
        return HttpResponseForbidden("Acesso negado. Apenas o Presidente pode iniciar a votação.")
    
    projeto = get_object_or_404(Projeto, pk=projeto_id)
    
    # Zera votos de votações anteriores deste projeto
    Voto.objects.filter(projeto=projeto).delete()
    
    # Atualiza status e marca a hora de início
    projeto.status = 'ABERTO'
    projeto.abertura_voto = timezone.now()
    projeto.save()
    
    return redirect('legislativo:painel_vereador')


@login_required
def encerrar_votacao(request, projeto_id):
    profile = getattr(request.user, 'vereadorprofile', None)
    if not profile or not profile.is_presidente:
        return HttpResponseForbidden("Acesso negado. Apenas o Presidente pode encerrar a votação.")
        
    projeto = get_object_or_404(Projeto, pk=projeto_id)
    projeto.status = 'FECHADO'
    projeto.save()
    
    return redirect('legislativo:painel_vereador')


# --- 5. API de Resultados em Tempo Real ---
def resultados_api(request, projeto_id):
    projeto = get_object_or_404(Projeto, pk=projeto_id)
    agora = timezone.now()

    # Cálculo do tempo restante
    tempo_restante = 0
    if projeto.status == 'ABERTO':
        limite = projeto.abertura_voto + timedelta(seconds=projeto.tempo_limite_segundos)
        if limite > agora:
            tempo_restante = int((limite - agora).total_seconds())
        else:
            # Tempo esgotado, mas o gerente não fechou (a API notifica a expiração)
            tempo_restante = 0 
            
    votos_computados = projeto.voto_set.count()

    # Lista de vereadores e seus votos (para o placar público)
    vereadores_profiles = VereadorProfile.objects.filter(ativo=True).select_related('user').order_by('nome_completo')
    votos_individuais = []
    
    for profile in vereadores_profiles:
        vereador = profile.user
        voto = Voto.objects.filter(projeto=projeto, vereador=vereador).first()
        
        status_voto = 'NÃO VOTOU'
        if voto:
            status_voto = voto.escolha
        elif profile.ausente_na_sessao:
            status_voto = 'AUSENTE'
            
        votos_individuais.append({
            'vereador_id': vereador.id,
            'nome': profile.nome_completo,
            'partido': profile.partido,
            'foto_url': profile.foto.url if profile.foto.name else None,
            'voto': status_voto,
        })
        
    TOTAL_VEREADORES = vereadores_profiles.count()
    
    # Retorna o JSON
    return JsonResponse({
        'id': projeto.id,
        'titulo': projeto.titulo,
        'status': projeto.status,
        'tempo_restante': tempo_restante,
        'sim': projeto.votos_sim(),
        'nao': projeto.votos_nao(),
        'abstencao': projeto.votos_abstencao(),
        'votos_computados': votos_computados,
        'total_vereadores': TOTAL_VEREADORES,
        'votos_individuais': votos_individuais,
        'quorum_necessario': projeto.get_quorum_minimo_display(),
    })
@login_required
def painel_secretaria(request):
    if not check_is_secretaria(request.user):
        return HttpResponseForbidden("Acesso negado. Você não pertence ao grupo Secretaria Geral.")
    
    projetos = Projeto.objects.filter(status='PREPARACAO').order_by('-id')
    
    if request.method == 'POST':
        form = ProjetoForm(request.POST)
        if form.is_valid():
            projeto = form.save(commit=False)
            # O status já é 'PREPARACAO' por padrão no Model.
            projeto.save()
            return redirect('legislativo:painel_secretaria')
    else:
        form = ProjetoForm()
        
    context = {
        'form': form,
        'projetos': projetos,
        'is_superuser': request.user.is_superuser # Adiciona o status de superusuário
    }
    return render(request, 'legislativo/painel_secretaria.html', context)

@login_required
def gerenciar_vereadores(request):
    if not check_is_secretaria(request.user):
        return HttpResponseForbidden("Acesso negado. Você não pertence ao grupo Secretaria Geral.")

    vereadores = VereadorProfile.objects.all().select_related('user', 'cargo_mesa').order_by('nome_completo')
    
    context = {
        'vereadores': vereadores
    }
    return render(request, 'legislativo/gerenciar_vereadores.html', context)

@login_required
def cadastrar_vereador(request):
    if not check_is_secretaria(request.user):
        return HttpResponseForbidden("Acesso negado. Você não pertence ao grupo Secretaria Geral.")

    # Verifica o limite de vereadores
    config = Configuracao.objects.first()
    limite = config.limite_vereadores if config else 15
    vereadores_atuais = VereadorProfile.objects.count()
    
    if vereadores_atuais >= limite:
        return render(request, 'legislativo/limite_vereadores_atingido.html', {'limite': limite})

    if request.method == 'POST':
        user_form = UserCreationForm(request.POST)
        profile_form = VereadorProfileForm(request.POST, request.FILES)
        
        if user_form.is_valid() and profile_form.is_valid():
            # 1. Cria o Usuário
            user = user_form.save(commit=False)
            user.set_password(user_form.cleaned_data['password'])
            user.is_staff = True # Vereadores precisam de acesso ao admin para gerenciar o próprio perfil (se necessário)
            user.save()
            
            # 2. Cria o Perfil do Vereador
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            
            # 3. Adiciona ao grupo 'Vereadores' (se existir)
            # from django.contrib.auth.models import Group
            # group, created = Group.objects.get_or_create(name='Vereadores')
            # user.groups.add(group)
            
            return redirect('legislativo:gerenciar_vereadores')
    else:
        user_form = UserCreationForm()
        profile_form = VereadorProfileForm()

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'limite': limite,
        'vereadores_atuais': vereadores_atuais
    }
    return render(request, 'legislativo/cadastrar_vereador.html', context)

@login_required
def editar_vereador(request, user_id):
    if not check_is_secretaria(request.user):
        return HttpResponseForbidden("Acesso negado. Você não pertence ao grupo Secretaria Geral.")

    user = get_object_or_404(User, pk=user_id)
    profile = get_object_or_404(VereadorProfile, user=user)

    if request.method == 'POST':
        profile_form = VereadorProfileForm(request.POST, request.FILES, instance=profile)
        
        if profile_form.is_valid():
            profile_form.save()
            # Se a secretaria precisar editar dados do User (nome, email), um UserEditForm seria necessário.
            # Por enquanto, focamos no VereadorProfile.
            return redirect('legislativo:gerenciar_vereadores')
    else:
        profile_form = VereadorProfileForm(instance=profile)

    context = {
        'user': user,
        'profile_form': profile_form
    }
    return render(request, 'legislativo/editar_vereador.html', context)

@login_required
def remover_vereador(request, user_id):
    if not check_is_secretaria(request.user):
        return HttpResponseForbidden("Acesso negado. Você não pertence ao grupo Secretaria Geral.")

    user = get_object_or_404(User, pk=user_id)
    
    if request.method == 'POST':
        user.delete() # O VereadorProfile será deletado em cascata
        return redirect('legislativo:gerenciar_vereadores')
        
    return render(request, 'legislativo/confirmar_remocao.html', {'user': user})

@login_required
@require_POST
def marcar_ausencia(request, user_id):
    if not check_is_secretaria(request.user):
        return HttpResponseForbidden("Acesso negado. Você não pertence ao grupo Secretaria Geral.")

    profile = get_object_or_404(VereadorProfile, user_id=user_id)
    
    # Alterna o status de ausência
    profile.ausente_na_sessao = not profile.ausente_na_sessao
    profile.save()
    
    return redirect('legislativo:gerenciar_vereadores')



@login_required
def cadastrar_secretaria(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Acesso negado. Apenas o Superusuário pode cadastrar novos usuários da Secretaria.")

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            # 1. Cria o Usuário (inativo)
            user = form.save(commit=False)
            user.is_active = False # Inativo até a confirmação por email
            user.set_password(form.cleaned_data['password'])
            user.save()
            
            # 2. Adiciona ao grupo 'Secretaria Geral'
            from django.contrib.auth.models import Group
            group, created = Group.objects.get_or_create(name='Secretaria Geral')
            user.groups.add(group)
            
            # 3. Cria o Token de Ativação
            token_obj = TokenAtivacao.objects.create(user=user)
            
            # 4. Simula o Envio de Email (Apenas para demonstração)
            # Na produção, você usaria o sistema de email do Django.
            ativacao_link = request.build_absolute_uri(f'/contas/ativar/{token_obj.token}/')
            
            # Mensagem de sucesso (substitui o email real)
            context = {
                'link_ativacao': ativacao_link,
                'user_email': user.email,
                'user_username': user.username
            }
            return render(request, 'legislativo/cadastro_secretaria_sucesso.html', context)
    else:
        form = UserCreationForm()
        
    is_superuser = request.user.is_superuser
    
    context = {
        'form': form,
        'projetos': projetos,
        'is_superuser': is_superuser
    }
    return render(request, 'legislativo/painel_secretaria.html', context)