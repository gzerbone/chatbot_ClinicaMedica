from rest_framework import serializers

from .models import (ClinicaInfo, Convenio, Especialidade, Exame,
                     HorarioTrabalho, Medico)


class EspecialidadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Especialidade
        fields = ['id', 'nome', 'descricao', 'ativa']


class ConvenioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Convenio
        fields = ['id', 'nome']


class ClinicaInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClinicaInfo
        fields = [
            'id', 'nome', 'objetivo_geral', 'secretaria_nome',
            'telefone_contato', 'whatsapp_contato', 'email_contato', 'endereco',
            'referencia_localizacao', 'politica_agendamento',
            'google_calendar_id'
        ]


class HorarioTrabalhoSerializer(serializers.ModelSerializer):
    dia_da_semana_display = serializers.CharField(source='get_dia_da_semana_display', read_only=True)
    
    class Meta:
        model = HorarioTrabalho
        fields = [
            'id', 'dia_da_semana', 'dia_da_semana_display',
            'hora_inicio', 'hora_fim'
        ]


class MedicoSerializer(serializers.ModelSerializer):
    especialidades = EspecialidadeSerializer(many=True, read_only=True)
    convenios = ConvenioSerializer(many=True, read_only=True)
    horarios_trabalho = HorarioTrabalhoSerializer(many=True, read_only=True)
    especialidades_display = serializers.CharField(source='get_especialidades_display', read_only=True)
    
    class Meta:
        model = Medico
        fields = [
            'id', 'nome', 'especialidades', 'especialidades_display',
            'bio', 'convenios', 'preco_particular', 'formas_pagamento',
            'retorno_info', 'horarios_trabalho'
        ]


class MedicoResumoSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagens"""
    especialidades_display = serializers.CharField(source='get_especialidades_display', read_only=True)
    
    class Meta:
        model = Medico
        fields = ['id', 'nome', 'especialidades_display', 'preco_particular']


class ExameSerializer(serializers.ModelSerializer):
    duracao_formatada = serializers.SerializerMethodField()
    
    class Meta:
        model = Exame
        fields = [
            'id', 'nome', 'o_que_e', 'como_funciona',
            'preparacao', 'vantagem', 'preco', 'duracao_estimada',
            'duracao_formatada'
        ]
    
    def get_duracao_formatada(self, obj):
        """Retorna duração em formato legível"""
        if obj.duracao_estimada:
            total_seconds = int(obj.duracao_estimada.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            
            if hours > 0:
                return f"{hours}h {minutes}min"
            else:
                return f"{minutes}min"
        return None
