"""
Serviço de Compatibilidade - Fase 1
Mantém compatibilidade com código existente durante migração
"""
import logging
from typing import Any, Dict, List

from .rag_service import langchain_rag_service

logger = logging.getLogger(__name__)


class CompatibilityRAGService:
    """
    Serviço de compatibilidade que mantém a interface do RAG original
    mas usa LangChain internamente
    """
    
    @staticmethod
    def get_clinic_info() -> Dict[str, Any]:
        """Compatibilidade com RAGService.get_clinic_info()"""
        return langchain_rag_service.get_clinic_info()
    
    @staticmethod
    def get_especialidades() -> List[Dict[str, Any]]:
        """Compatibilidade com RAGService.get_especialidades()"""
        return langchain_rag_service.get_specialties()
    
    @staticmethod
    def get_convenios() -> List[Dict[str, Any]]:
        """Compatibilidade com RAGService.get_convenios()"""
        # Por enquanto, manter implementação original
        try:
            from rag_agent.models import Convenio
            from rag_agent.serializers import ConvenioSerializer
            convenios = Convenio.objects.all()
            return ConvenioSerializer(convenios, many=True).data
        except Exception as e:
            logger.error(f"Erro ao obter convênios: {e}")
            return []
    
    @staticmethod
    def get_medicos() -> List[Dict[str, Any]]:
        """Compatibilidade com RAGService.get_medicos()"""
        return langchain_rag_service.get_doctors()
    
    @staticmethod
    def get_exames() -> List[Dict[str, Any]]:
        """Compatibilidade com RAGService.get_exames()"""
        return langchain_rag_service.get_exams()
    
    @staticmethod
    def get_medico_by_id(medico_id: int) -> Dict[str, Any]:
        """Compatibilidade com RAGService.get_medico_by_id()"""
        try:
            from rag_agent.models import Medico
            from rag_agent.serializers import MedicoSerializer
            medico = Medico.objects.prefetch_related(
                'especialidades', 'convenios', 'horarios_trabalho'
            ).get(id=medico_id)
            return MedicoSerializer(medico).data
        except Exception as e:
            logger.error(f"Erro ao obter médico {medico_id}: {e}")
            return None
    
    @staticmethod
    def get_medicos_por_especialidade(especialidade_id: int) -> List[Dict[str, Any]]:
        """Compatibilidade com RAGService.get_medicos_por_especialidade()"""
        try:
            from rag_agent.models import Especialidade
            from rag_agent.serializers import MedicoResumoSerializer
            especialidade = Especialidade.objects.get(id=especialidade_id, ativa=True)
            medicos = especialidade.medico_set.all()
            return MedicoResumoSerializer(medicos, many=True).data
        except Exception as e:
            logger.error(f"Erro ao obter médicos da especialidade {especialidade_id}: {e}")
            return []
    
    @staticmethod
    def search_info(query: str) -> Dict[str, Any]:
        """Compatibilidade com RAGService.search_info()"""
        try:
            # Usar busca semântica do LangChain
            results = langchain_rag_service.search(query, k=5)
            
            # Organizar resultados por tipo
            organized_results = {}
            for result in results:
                doc_type = result['metadata'].get('type', 'unknown')
                if doc_type not in organized_results:
                    organized_results[doc_type] = []
                organized_results[doc_type].append(result)
            
            return organized_results
            
        except Exception as e:
            logger.error(f"Erro na busca por '{query}': {e}")
            return {}
    
    @staticmethod
    def get_doctor_availability(doctor_name: str, days_ahead: int = 7) -> Dict[str, Any]:
        """Compatibilidade com RAGService.get_doctor_availability()"""
        try:
            from api_gateway.services.google_calendar_service import \
                google_calendar_service
            return google_calendar_service.get_doctor_availability(doctor_name, days_ahead)
        except Exception as e:
            logger.error(f"Erro ao obter disponibilidade do médico {doctor_name}: {e}")
            return {'error': f'Erro ao consultar disponibilidade de {doctor_name}'}
    
    @staticmethod
    def get_all_doctors_availability(days_ahead: int = 7) -> Dict[str, Any]:
        """Compatibilidade com RAGService.get_all_doctors_availability()"""
        try:
            from api_gateway.services.google_calendar_service import \
                google_calendar_service
            return google_calendar_service.get_all_doctors_availability(days_ahead)
        except Exception as e:
            logger.error(f"Erro ao obter disponibilidade dos médicos: {e}")
            return {'error': 'Erro ao consultar disponibilidade dos médicos'}
    
    @staticmethod
    def get_medico_by_name(doctor_name: str) -> Dict[str, Any]:
        """Compatibilidade com RAGService.get_medico_by_name()"""
        try:
            from rag_agent.models import Medico
            from rag_agent.serializers import MedicoSerializer

            # Normalizar nome para busca
            normalized_name = doctor_name.lower().replace('dr. ', '').replace('dra. ', '')
            
            # Buscar médico no banco
            medico = Medico.objects.prefetch_related('especialidades', 'convenios').filter(
                nome__icontains=normalized_name
            ).first()
            
            if medico:
                return MedicoSerializer(medico).data
            
            logger.warning(f"Médico {doctor_name} não encontrado no banco de dados")
            return None
            
        except Exception as e:
            logger.error(f"Erro ao buscar médico {doctor_name}: {e}")
            return None
    
    @staticmethod
    def get_doctor_specialty(doctor_name: str) -> str:
        """Compatibilidade com RAGService.get_doctor_specialty()"""
        try:
            medico_data = CompatibilityRAGService.get_medico_by_name(doctor_name)
            
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
        """Compatibilidade com RAGService.get_doctor_insurances()"""
        try:
            medico_data = CompatibilityRAGService.get_medico_by_name(doctor_name)
            
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
        """Compatibilidade com RAGService.get_all_clinic_data()"""
        return {
            'clinica_info': CompatibilityRAGService.get_clinic_info(),
            'especialidades': CompatibilityRAGService.get_especialidades(),
            'convenios': CompatibilityRAGService.get_convenios(),
            'medicos': CompatibilityRAGService.get_medicos(),
            'exames': CompatibilityRAGService.get_exames(),
            'disponibilidade_medicos': CompatibilityRAGService.get_all_doctors_availability(7)
        }


# Instância global para compatibilidade
compatibility_rag_service = CompatibilityRAGService()
