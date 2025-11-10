"""
Serviço para acessar dados do RAG Agent
"""
import logging
from typing import Any, Dict, List

from django.core.cache import cache

from rag_agent.models import (ClinicaInfo, Convenio, Especialidade, Exame,
                              Medico)
from rag_agent.serializers import (ClinicaInfoSerializer, ConvenioSerializer,
                                   EspecialidadeSerializer, ExameSerializer,
                                   MedicoResumoSerializer)

logger = logging.getLogger(__name__)

# Timeout de cache para dados RAG (30 minutos = 1800 segundos)
# Dados da clínica mudam raramente, então cache por mais tempo é eficiente
RAG_CACHE_TIMEOUT = 1800

class RAGService:
    """
    Serviço para acessar dados da base de conhecimento (RAG Agent)
    """
    
    @staticmethod
    def get_clinic_info() -> Dict[str, Any]:
        """
        Obtém informações da clínica (com cache)
        
        Returns:
            Dicionário com informações da clínica ou None se não encontrada
        """
        cache_key = 'rag_clinic_info'
        clinica_data = cache.get(cache_key)
        
        if clinica_data is not None:
            logger.debug("🎯 Cache HIT: Informações da clínica")
            return clinica_data
        
        try:
            logger.debug("💾 Cache MISS: Buscando informações da clínica no banco")
            clinica = ClinicaInfo.objects.first()
            if clinica:
                clinica_data = ClinicaInfoSerializer(clinica).data
                cache.set(cache_key, clinica_data, RAG_CACHE_TIMEOUT)
                return clinica_data
            return None
        except Exception as e:
            logger.error(f"Erro ao obter informações da clínica: {e}")
            return None
    
    @staticmethod
    def get_especialidades() -> List[Dict[str, Any]]:
        """
        Obtém lista de especialidades ativas (com cache)
        
        Returns:
            Lista de especialidades ou lista vazia se erro
        """
        cache_key = 'rag_especialidades'
        especialidades_data = cache.get(cache_key)
        
        if especialidades_data is not None:
            logger.debug("🎯 Cache HIT: Especialidades")
            return especialidades_data
        
        try:
            logger.debug("💾 Cache MISS: Buscando especialidades no banco")
            especialidades = Especialidade.objects.filter(ativa=True)
            especialidades_data = EspecialidadeSerializer(especialidades, many=True).data
            cache.set(cache_key, especialidades_data, RAG_CACHE_TIMEOUT)
            return especialidades_data
        except Exception as e:
            logger.error(f"Erro ao obter especialidades: {e}")
            return []
    
    @staticmethod
    def get_convenios() -> List[Dict[str, Any]]:
        """
        Obtém lista de convênios disponíveis (com cache)
        
        Returns:
            Lista de convênios ou lista vazia se erro
        """
        cache_key = 'rag_convenios'
        convenios_data = cache.get(cache_key)
        
        if convenios_data is not None:
            logger.debug("🎯 Cache HIT: Convênios")
            return convenios_data
        
        try:
            logger.debug("💾 Cache MISS: Buscando convênios no banco")
            convenios = Convenio.objects.all()
            convenios_data = ConvenioSerializer(convenios, many=True).data
            cache.set(cache_key, convenios_data, RAG_CACHE_TIMEOUT)
            return convenios_data
        except Exception as e:
            logger.error(f"Erro ao obter convênios: {e}")
            return []
    
    @staticmethod
    def get_medicos() -> List[Dict[str, Any]]:
        """
        Obtém lista de médicos com suas especialidades (com cache)
        
        Returns:
            Lista de médicos ou lista vazia se erro
        """
        cache_key = 'rag_medicos'
        medicos_data = cache.get(cache_key)
        
        if medicos_data is not None:
            logger.debug("🎯 Cache HIT: Médicos")
            return medicos_data
        
        try:
            logger.debug("💾 Cache MISS: Buscando médicos no banco")
            medicos = Medico.objects.prefetch_related('especialidades', 'convenios')
            medicos_data = MedicoResumoSerializer(medicos, many=True).data
            cache.set(cache_key, medicos_data, RAG_CACHE_TIMEOUT)
            return medicos_data
        except Exception as e:
            logger.error(f"Erro ao obter médicos: {e}")
            return []
    
    @staticmethod
    def get_exames() -> List[Dict[str, Any]]:
        """
        Obtém lista de exames disponíveis (com cache)
        
        Returns:
            Lista de exames ou lista vazia se erro
        """
        cache_key = 'rag_exames'
        exames_data = cache.get(cache_key)
        
        if exames_data is not None:
            logger.debug("🎯 Cache HIT: Exames")
            return exames_data
        
        try:
            logger.debug("💾 Cache MISS: Buscando exames no banco")
            exames = Exame.objects.all()
            exames_data = ExameSerializer(exames, many=True).data
            cache.set(cache_key, exames_data, RAG_CACHE_TIMEOUT)
            return exames_data
        except Exception as e:
            logger.error(f"Erro ao obter exames: {e}")
            return []
    
    @staticmethod
    def get_medico_by_id(medico_id: int) -> Dict[str, Any]:
        """
        Obtém detalhes de um médico específico
        
        Args:
            medico_id: ID do médico
            
        Returns:
            Dados do médico ou None se não encontrado
        """
        try:
            medico = Medico.objects.prefetch_related(
                'especialidades', 'convenios', 'horarios_trabalho'
            ).get(id=medico_id)
            from rag_agent.serializers import MedicoSerializer
            return MedicoSerializer(medico).data
        except Medico.DoesNotExist:
            logger.warning(f"Médico com ID {medico_id} não encontrado")
            return None
        except Exception as e:
            logger.error(f"Erro ao obter médico {medico_id}: {e}")
            return None
    
    @staticmethod
    def get_medicos_por_especialidade(especialidade_id: int) -> List[Dict[str, Any]]:
        """
        Obtém médicos de uma especialidade específica
        
        Args:
            especialidade_id: ID da especialidade
            
        Returns:
            Lista de médicos da especialidade
        """
        try:
            especialidade = Especialidade.objects.get(id=especialidade_id, ativa=True)
            medicos = Medico.objects.filter(especialidades=especialidade)
            return MedicoResumoSerializer(medicos, many=True).data
        except Especialidade.DoesNotExist:
            logger.warning(f"Especialidade com ID {especialidade_id} não encontrada")
            return []
        except Exception as e:
            logger.error(f"Erro ao obter médicos da especialidade {especialidade_id}: {e}")
            return []
    
    @staticmethod
    def search_info(query: str) -> Dict[str, Any]:
        """
        Busca informações gerais baseada em uma query
        
        Args:
            query: Termo de busca
            
        Returns:
            Dicionário com resultados da busca
        """
        try:
            query_lower = query.lower()
            results = {}
            
            # Buscar na clínica info
            clinica = ClinicaInfo.objects.first()
            if clinica:
                results['clinica'] = ClinicaInfoSerializer(clinica).data
            
            # Buscar especialidades
            especialidades = Especialidade.objects.filter(
                nome__icontains=query_lower, ativa=True
            )
            if especialidades.exists():
                results['especialidades'] = EspecialidadeSerializer(especialidades, many=True).data
            
            # Buscar médicos
            medicos = Medico.objects.filter(nome__icontains=query_lower)
            if medicos.exists():
                results['medicos'] = MedicoResumoSerializer(medicos, many=True).data
            
            # Buscar exames
            exames = Exame.objects.filter(nome__icontains=query_lower)
            if exames.exists():
                results['exames'] = ExameSerializer(exames, many=True).data
            
            return results
        except Exception as e:
            logger.error(f"Erro na busca por '{query}': {e}")
            return {}
    
    @staticmethod
    def get_doctor_availability(doctor_name: str, days_ahead: int = 7) -> Dict[str, Any]:
        """
        Obtém disponibilidade de horários de um médico
        
        Args:
            doctor_name: Nome do médico
            days_ahead: Quantos dias à frente consultar
            
        Returns:
            Dicionário com disponibilidade do médico
        """
        try:
            from .google_calendar_service import google_calendar_service
            return google_calendar_service.get_doctor_availability(doctor_name, days_ahead)
        except Exception as e:
            logger.error(f"Erro ao obter disponibilidade do médico {doctor_name}: {e}")
            return {'error': f'Erro ao consultar disponibilidade de {doctor_name}'}
    
    @staticmethod
    def get_all_doctors_availability(days_ahead: int = 7) -> Dict[str, Any]:
        """
        Obtém disponibilidade de todos os médicos
        
        Args:
            days_ahead: Quantos dias à frente consultar
            
        Returns:
            Dicionário com disponibilidade de todos os médicos
        """
        try:
            from .google_calendar_service import google_calendar_service
            return google_calendar_service.get_all_doctors_availability(days_ahead)
        except Exception as e:
            logger.error(f"Erro ao obter disponibilidade dos médicos: {e}")
            return {'error': 'Erro ao consultar disponibilidade dos médicos'}
    
    @staticmethod
    def get_medico_by_name(doctor_name: str) -> Dict[str, Any]:
        """
        Busca médico específico por nome
        
        Args:
            doctor_name: Nome do médico (pode incluir Dr./Dra.)
            
        Returns:
            Dados do médico ou None se não encontrado
        """
        try:
            # Normalizar nome para busca
            normalized_name = doctor_name.lower().replace('dr. ', '').replace('dra. ', '')
            
            # Buscar médico no banco
            medico = Medico.objects.prefetch_related('especialidades', 'convenios').filter(
                nome__icontains=normalized_name
            ).first()
            
            if medico:
                from rag_agent.serializers import MedicoSerializer
                return MedicoSerializer(medico).data
            
            logger.warning(f"Médico {doctor_name} não encontrado no banco de dados")
            return None
            
        except Exception as e:
            logger.error(f"Erro ao buscar médico {doctor_name}: {e}")
            return None
    
    @staticmethod
    def get_doctor_specialty(doctor_name: str) -> str:
        """
        Obtém especialidade principal de um médico
        
        Args:
            doctor_name: Nome do médico
            
        Returns:
            Nome da especialidade ou 'Consulta Geral' se não encontrado
        """
        try:
            medico_data = RAGService.get_medico_by_name(doctor_name)
            
            if medico_data and 'especialidades' in medico_data:
                especialidades = medico_data['especialidades']
                if especialidades:
                    # Retornar primeira especialidade
                    if isinstance(especialidades[0], dict):
                        return especialidades[0].get('nome', 'Consulta Geral')
                    else:
                        return str(especialidades[0])
            
            return 'Consulta Geral'
            
        except Exception as e:
            logger.error(f"Erro ao obter especialidade do médico {doctor_name}: {e}")
            return 'Consulta Geral'
    
    @staticmethod
    def get_doctor_insurances(doctor_name: str) -> List[str]:
        """
        Obtém convênios aceitos por um médico
        
        Args:
            doctor_name: Nome do médico
            
        Returns:
            Lista de convênios aceitos
        """
        try:
            medico_data = RAGService.get_medico_by_name(doctor_name)
            
            if medico_data and 'convenios' in medico_data:
                convenios = medico_data['convenios']
                if convenios:
                    return [conv.get('nome', '') if isinstance(conv, dict) else str(conv) for conv in convenios]
            
            return ['Particular']
            
        except Exception as e:
            logger.error(f"Erro ao obter convênios do médico {doctor_name}: {e}")
            return ['Particular']
    
    @staticmethod
    def get_all_clinic_data() -> Dict[str, Any]:
        """
        Obtém todos os dados da clínica de uma vez
        
        Returns:
            Dicionário com todos os dados da clínica
        """
        return {
            'clinica_info': RAGService.get_clinic_info(),
            'especialidades': RAGService.get_especialidades(),
            'convenios': RAGService.get_convenios(),
            'medicos': RAGService.get_medicos(),
            'exames': RAGService.get_exames(),
            'disponibilidade_medicos': RAGService.get_all_doctors_availability(7)
        }
    
    # Métodos de compatibilidade para o Gemini modularizado
    @staticmethod
    def get_clinica_info() -> Dict[str, Any]:
        """Alias para get_clinic_info para compatibilidade"""
        return RAGService.get_clinic_info()
    
    @staticmethod
    def get_telefone() -> str:
        """
        Obtém telefone da clínica
        
        Returns:
            String com telefone da clínica ou telefone padrão
        """
        try:
            clinica_info = RAGService.get_clinic_info()
            if clinica_info and 'telefone' in clinica_info and clinica_info['telefone']:
                return clinica_info['telefone']
            # Telefone padrão se não encontrar
            return "(11) 99999-9999"
        except Exception as e:
            logger.error(f"Erro ao obter telefone da clínica: {e}")
            return "(11) 99999-9999"
    
    # Remover métodos duplicados que causam recursão infinita