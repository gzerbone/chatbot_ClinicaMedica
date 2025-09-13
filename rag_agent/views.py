from django.shortcuts import get_object_or_404
from rest_framework import generics, status, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import (ClinicaInfo, Convenio, Especialidade, Exame,
                     HorarioTrabalho, Medico)
from .serializers import (ClinicaInfoSerializer, ConvenioSerializer,
                          EspecialidadeSerializer, ExameSerializer,
                          HorarioTrabalhoSerializer, MedicoResumoSerializer,
                          MedicoSerializer)


class EspecialidadeListView(generics.ListAPIView):
    """Lista especialidades ativas"""
    queryset = Especialidade.objects.filter(ativa=True)
    serializer_class = EspecialidadeSerializer


class ClinicaInfoView(generics.RetrieveAPIView):
    """Retorna informações da clínica"""
    serializer_class = ClinicaInfoSerializer
    
    def get_object(self):
        return ClinicaInfo.objects.first()


class ConvenioListView(generics.ListAPIView):
    """Lista convênios disponíveis"""
    queryset = Convenio.objects.all()
    serializer_class = ConvenioSerializer


class MedicoViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para médicos"""
    queryset = Medico.objects.prefetch_related('especialidades', 'convenios', 'horarios_trabalho')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return MedicoResumoSerializer
        return MedicoSerializer


class ExameListView(generics.ListAPIView):
    """Lista exames disponíveis"""
    queryset = Exame.objects.all()
    serializer_class = ExameSerializer


@api_view(['GET'])
def medicos_por_especialidade(request, especialidade_id):
    """Retorna médicos de uma especialidade específica"""
    try:
        especialidade = Especialidade.objects.get(id=especialidade_id, ativa=True)
        medicos = Medico.objects.filter(especialidades=especialidade)
        serializer = MedicoResumoSerializer(medicos, many=True)
        
        return Response({
            'especialidade': especialidade.nome,
            'medicos': serializer.data
        })
    except Especialidade.DoesNotExist:
        return Response(
            {'error': 'Especialidade não encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
def search_info(request):
    """
    Endpoint para busca de informações gerais
    Útil para o chatbot buscar respostas
    """
    query = request.GET.get('q', '').lower()
    
    if not query:
        return Response({'error': 'Parâmetro q (query) é obrigatório'})
    
    results = {}
    
    # Buscar na clínica info
    clinica = ClinicaInfo.objects.first()
    if clinica:
        results['clinica'] = ClinicaInfoSerializer(clinica).data
    
    # Buscar especialidades
    especialidades = Especialidade.objects.filter(
        nome__icontains=query, ativa=True
    )
    if especialidades.exists():
        results['especialidades'] = EspecialidadeSerializer(especialidades, many=True).data
    
    # Buscar médicos
    medicos = Medico.objects.filter(nome__icontains=query)
    if medicos.exists():
        results['medicos'] = MedicoResumoSerializer(medicos, many=True).data
    
    # Buscar exames
    exames = Exame.objects.filter(nome__icontains=query)
    if exames.exists():
        results['exames'] = ExameSerializer(exames, many=True).data
    
    return Response(results)
