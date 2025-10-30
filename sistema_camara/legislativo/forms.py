from django import forms
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm
from .models import Projeto, VereadorProfile, Cargo

# Renomeia para evitar conflito de nome se necessário, mas usa o nome canônico no views.py
# O erro original era porque UserCreationForm não estava em .forms
class UserCreationForm(BaseUserCreationForm):
    class Meta(BaseUserCreationForm.Meta):
        fields = BaseUserCreationForm.Meta.fields + ('email', 'first_name', 'last_name')

class ProjetoForm(forms.ModelForm):
    class Meta:
        model = Projeto
        # A Secretaria só precisa cadastrar estes campos. 
        # O 'status' inicial será sempre 'PREPARACAO' (definido no Model).
        # O 'abertura_voto' será definido pelo Gerente.
        fields = ['titulo', 'autor', 'tipo', 'descricao', 'quorum_minimo', 'tempo_limite_segundos']
        
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 4}),
        }

class VereadorProfileForm(forms.ModelForm):
    class Meta:
        model = VereadorProfile
        fields = [
            'nome_completo', 
            'nome_candidatura', 
            'partido', 
            'foto', 
            'ata_posse', 
            'cargo_mesa', 
            'ativo', 
            'ausente_na_sessao'
        ]

