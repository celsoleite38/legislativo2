from django.contrib import admin
from .models import Projeto, Voto, Cargo, VereadorProfile, Configuracao

admin.site.register(VereadorProfile)
admin.site.register(Cargo)

admin.site.register(Projeto)
admin.site.register(Voto)
admin.site.register(Configuracao)