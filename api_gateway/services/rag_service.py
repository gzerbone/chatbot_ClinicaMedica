"""
Serviço para acessar dados do RAG Agent
"""
import logging
from typing import Any, Dict, List

from rag_agent.models import (ClinicaInfo, Convenio, Especialidade, Exame,
                              Medico)
from rag_agent.serializers import (ClinicaInfoSerializer, ConvenioSerializer,
                                   EspecialidadeSerializer, ExameSerializer,
                                   MedicoResumoSerializer)

logger = logging.getLogger(__name__)


class RAGService:
    """
    Serviço para acessar dados da base de conhecimento (RAG Agent)
    """
    
    @staticmethod
    def get_clinic_info() -> Dict[str, Any]:
        """
        Obtém informações da clínica
        
        Returns:
            Dicionário com informações da clínica ou None se não encontrada
        """
        try:
            clinica = ClinicaInfo.objects.first()
            if clinica:
                return ClinicaInfoSerializer(clinica).data
            return None
        except Exception as e:
            logger.error(f"Erro ao obter informações da clínica: {e}")
            return None
    
    @staticmethod
    def get_especialidades() -> List[Dict[str, Any]]:
        """
        Obtém lista de especialidades ativas
        
        Returns:
            Lista de especialidades ou lista vazia se erro
        """
        try:
            especialidades = Especialidade.objects.filter(ativa=True)
            return EspecialidadeSerializer(especialidades, many=True).data
        except Exception as e:
            logger.error(f"Erro ao obter especialidades: {e}")
            return []
    
    @staticmethod
    def get_convenios() -> List[Dict[str, Any]]:
        """
        Obtém lista de convênios disponíveis
        
        Returns:
            Lista de convênios ou lista vazia se erro
        """
        try:
            convenios = Convenio.objects.all()
            return ConvenioSerializer(convenios, many=True).data
        except Exception as e:
            logger.error(f"Erro ao obter convênios: {e}")
            return []
    
    @staticmethod
    def get_medicos() -> List[Dict[str, Any]]:
        """
        Obtém lista de médicos com suas especialidades
        
        Returns:
            Lista de médicos ou lista vazia se erro
        """
        try:
            medicos = Medico.objects.prefetch_related('especialidades', 'convenios')
            return MedicoResumoSerializer(medicos, many=True).data
        except Exception as e:
            logger.error(f"Erro ao obter médicos: {e}")
            return []
    
    @staticmethod
    def get_exames() -> List[Dict[str, Any]]:
        """
        Obtém lista de exames disponíveis
        
        Returns:
            Lista de exames ou lista vazia se erro
        """
        try:
            exames = Exame.objects.all()
            return ExameSerializer(exames, many=True).data
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
            'exames': RAGService.get_exames()
        }
