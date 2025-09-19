from django.contrib import admin

from .models import (ClinicaInfo, Convenio, Especialidade, Exame,
                     HorarioTrabalho, Medico)

# Register your models here.

@admin.register(Especialidade)
class EspecialidadeAdmin(admin.ModelAdmin):
    list_display = ['nome', 'ativa']
    list_filter = ['ativa']
    search_fields = ['nome']

@admin.register(ClinicaInfo)
class ClinicaInfoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'telefone_contato', 'email_contato']
    
    def has_add_permission(self, request):
        # Só permite um registro
        return not ClinicaInfo.objects.exists()

@admin.register(Convenio)
class ConvenioAdmin(admin.ModelAdmin):
    list_display = ['nome']
    search_fields = ['nome']

@admin.register(Medico)
class MedicoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'crm', 'get_especialidades_display', 'preco_particular']
    list_filter = ['especialidades', 'convenios']
    search_fields = ['nome', 'crm']
    filter_horizontal = ['especialidades', 'convenios']

@admin.register(HorarioTrabalho)
class HorarioTrabalhoAdmin(admin.ModelAdmin):
    list_display = ['medico', 'dia_da_semana', 'hora_inicio', 'hora_fim']
    list_filter = ['dia_da_semana', 'medico']

@admin.register(Exame)
class ExameAdmin(admin.ModelAdmin):
    list_display = ['nome', 'preco', 'duracao_estimada']
    search_fields = ['nome']
