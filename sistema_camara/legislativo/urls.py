# legislativo/urls.py
from django.urls import path
from . import views

app_name = 'legislativo'

urlpatterns = [
    # Tela Pública (Placar)
    path('', views.tela_principal, name='tela_principal'), 
    
    # URLs de Ativação (Superusuário)
    path('contas/ativar/<uuid:token>/', views.ativar_conta_secretaria, name='ativar_conta_secretaria'),
    path('contas/cadastrar_secretaria/', views.cadastrar_secretaria, name='cadastrar_secretaria'),
    
    path('painel/', views.painel_vereador, name='painel_vereador'),
    path('secretaria/', views.painel_secretaria, name='painel_secretaria'),
    path('secretaria/vereadores/', views.gerenciar_vereadores, name='gerenciar_vereadores'),
    path('secretaria/vereadores/cadastrar/', views.cadastrar_vereador, name='cadastrar_vereador'),
    path('secretaria/vereadores/editar/<int:user_id>/', views.editar_vereador, name='editar_vereador'),
    path('secretaria/vereadores/remover/<int:user_id>/', views.remover_vereador, name='remover_vereador'),
    path('secretaria/vereadores/ausencia/<int:user_id>/', views.marcar_ausencia, name='marcar_ausencia'),
    path('presidente/', views.painel_presidente, name='painel_presidente'), 
    path('votar/<int:projeto_id>/', views.votar, name='votar'),
    
    
    path('iniciar_votacao/<int:projeto_id>/', views.iniciar_votacao, name='iniciar_votacao'),
    path('encerrar_votacao/<int:projeto_id>/', views.encerrar_votacao, name='encerrar_votacao'),
    
    path('api/resultados/<int:projeto_id>/', views.resultados_api, name='resultados_api'),
]