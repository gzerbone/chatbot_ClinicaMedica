"""
Serviço de Compatibilidade para Chains
Mantém compatibilidade com código existente durante migração
"""
import logging
from typing import Any, Dict, List

from ..memory.conversation_memory import memory_manager
from .conversation_chains import chain_manager

logger = logging.getLogger(__name__)


class CompatibilityChainService:
    """
    Serviço de compatibilidade que mantém a interface do Gemini Chatbot Service
    mas usa LangChain Chains internamente
    """
    
    def __init__(self):
        self.chain_manager = chain_manager
        self.memory_manager = memory_manager
    
    def process_message(self, phone_number: str, message: str) -> Dict[str, Any]:
        """
        Processa mensagem usando chains LangChain
        
        Args:
            phone_number: Número do telefone
            message: Mensagem do usuário
            
        Returns:
            Resultado do processamento
        """
        try:
            # Obter sessão da conversa
            session = self._get_or_create_session(phone_number)
            
            # Obter dados da clínica
            from ..compatibility_service import compatibility_rag_service
            clinic_data = compatibility_rag_service.get_all_clinic_data()
            
            # Processar mensagem usando chains
            result = self.chain_manager.process_message(
                phone_number, message, session, clinic_data
            )
            
            # Atualizar sessão
            self._update_session(phone_number, session, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Erro no processamento da mensagem: {e}")
            return self._get_fallback_response(message)
    
    def _get_or_create_session(self, phone_number: str) -> Dict[str, Any]:
        """Obtém ou cria sessão da conversa"""
        try:
            from django.core.cache import cache
            from django.utils import timezone
            
            cache_key = f"langchain_session_{phone_number}"
            session = cache.get(cache_key)
            
            if not session:
                session = {
                    'phone_number': phone_number,
                    'current_state': 'idle',
                    'patient_name': None,
                    'selected_doctor': None,
                    'preferred_date': None,
                    'preferred_time': None,
                    'insurance_type': None,
                    'created_at': timezone.now().isoformat(),
                    'last_activity': timezone.now().isoformat()
                }
                cache.set(cache_key, session, 3600)  # 1 hora
            
            return session
            
        except Exception as e:
            logger.error(f"Erro ao obter/criar sessão: {e}")
            return {
                'phone_number': phone_number,
                'current_state': 'idle',
                'patient_name': None,
                'selected_doctor': None
            }
    
    def _update_session(self, phone_number: str, session: Dict, result: Dict):
        """Atualiza sessão com base no resultado"""
        try:
            from django.core.cache import cache
            from django.utils import timezone

            # Atualizar estado
            session['current_state'] = result.get('state', session.get('current_state', 'idle'))
            session['last_activity'] = timezone.now().isoformat()
            
            # Atualizar entidades extraídas
            analysis = result.get('analysis', {})
            entities = analysis.get('entities', {})
            
            # Atualizar nome do paciente
            if entities.get('nome_paciente'):
                session['patient_name'] = entities['nome_paciente']
            
            # Atualizar médico selecionado
            if entities.get('medico'):
                session['selected_doctor'] = entities['medico']
            
            # Atualizar data preferida
            if entities.get('data'):
                session['preferred_date'] = entities['data']
            
            # Atualizar horário preferido
            if entities.get('horario'):
                session['preferred_time'] = entities['horario']
            
            # Salvar sessão
            cache_key = f"langchain_session_{phone_number}"
            cache.set(cache_key, session, 3600)
            
            # Sincronizar com banco de dados
            self._sync_session_to_database(phone_number, session)
            
        except Exception as e:
            logger.error(f"Erro ao atualizar sessão: {e}")
    
    def _sync_session_to_database(self, phone_number: str, session: Dict):
        """Sincroniza sessão com banco de dados"""
        try:
            from django.utils import timezone

            from api_gateway.models import ConversationSession

            # Obter ou criar sessão no banco
            db_session, created = ConversationSession.objects.get_or_create(
                phone_number=phone_number,
                defaults={
                    'current_state': session.get('current_state', 'idle'),
                    'patient_name': session.get('patient_name'),
                    'name_confirmed': bool(session.get('patient_name')),
                    'pending_name': None,
                    'insurance_type': session.get('insurance_type'),
                    'created_at': timezone.now(),
                    'updated_at': timezone.now()
                }
            )
            
            if not created:
                # Atualizar sessão existente
                db_session.current_state = session.get('current_state', 'idle')
                db_session.patient_name = session.get('patient_name')
                db_session.name_confirmed = bool(session.get('patient_name'))
                db_session.insurance_type = session.get('insurance_type')
                db_session.updated_at = timezone.now()
                db_session.save()
            
        except Exception as e:
            logger.error(f"Erro ao sincronizar sessão com banco: {e}")
    
    def _get_fallback_response(self, message: str) -> Dict[str, Any]:
        """Resposta de fallback"""
        return {
            'response': "Desculpe, estou temporariamente indisponível. Como posso ajudá-lo?",
            'intent': 'duvida',
            'confidence': 0.5,
            'state': 'idle',
            'session_data': {},
            'analysis': {'intent': 'duvida', 'confidence': 0.5},
            'agent': 'fallback'
        }
    
    def get_conversation_history(self, phone_number: str, limit: int = 5) -> List[Dict]:
        """Obtém histórico da conversa"""
        try:
            return self.memory_manager.get_conversation_history(phone_number, limit)
        except Exception as e:
            logger.error(f"Erro ao obter histórico: {e}")
            return []
    
    def clear_memory(self, phone_number: str):
        """Limpa memória da conversa"""
        try:
            self.memory_manager.clear_memory(phone_number)
        except Exception as e:
            logger.error(f"Erro ao limpar memória: {e}")
    
    def get_memory_stats(self, phone_number: str) -> Dict[str, Any]:
        """Obtém estatísticas da memória"""
        try:
            return self.memory_manager.get_memory_stats(phone_number)
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas da memória: {e}")
            return {'error': str(e)}
    
    def get_chain_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas das chains"""
        try:
            return self.chain_manager.get_chain_stats()
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas das chains: {e}")
            return {'error': str(e)}


# Instância global do serviço de compatibilidade
compatibility_chain_service = CompatibilityChainService()
