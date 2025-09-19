"""
Serviço Inteligente de Coleta de Informações
Coleta dados do paciente de forma proativa e inteligente
"""
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from .base_service import BaseService
from .conversation_service import conversation_service

logger = logging.getLogger(__name__)


class SmartCollectionService:
    """
    Serviço para coleta inteligente de informações do paciente
    """
    
    def __init__(self):
        self.conversation_service = conversation_service
    
    def process_message_with_collection(self, 
                                      phone_number: str, 
                                      message: str, 
                                      intent: str, 
                                      entities: Dict) -> Dict[str, Any]:
        """
        Processa mensagem com coleta inteligente de informações
        
        Returns:
            Dict com resposta e próximos passos
        """
        try:
            # Verificar informações essenciais
            info_status = self.conversation_service.check_required_info(phone_number)
            
            # Se não tem nome completo, tentar extrair da mensagem
            if not info_status['has_name']:
                extracted_name = self.conversation_service.extract_patient_name(message)
                if extracted_name:
                    self.conversation_service.update_patient_info(
                        phone_number, patient_name=extracted_name
                    )
                    info_status = self.conversation_service.check_required_info(phone_number)
            
            # Determinar resposta baseada no status
            if not info_status['is_complete']:
                return self._handle_incomplete_info(phone_number, message, intent, entities, info_status)
            else:
                return self._handle_complete_info(phone_number, message, intent, entities)
                
        except Exception as e:
            logger.error(f"Erro no processamento inteligente: {e}")
            return {
                'response': "Desculpe, houve um erro. Como posso ajudá-lo?",
                'next_action': 'ask_general',
                'requires_handoff': False
            }
    
    def _handle_incomplete_info(self, 
                               phone_number: str, 
                               message: str, 
                               intent: str, 
                               entities: Dict, 
                               info_status: Dict) -> Dict[str, Any]:
        """
        Lida com informações incompletas do paciente
        """
        next_action = info_status['next_action']
        
        if next_action == 'ask_name':
            return {
                'response': self._get_name_request_message(phone_number),
                'next_action': 'waiting_for_name',
                'requires_handoff': False,
                'info_status': info_status
            }
        
        elif next_action == 'ask_phone':
            return {
                'response': self._get_phone_request_message(phone_number),
                'next_action': 'waiting_for_phone',
                'requires_handoff': False,
                'info_status': info_status
            }
        
        else:
            return {
                'response': self._get_general_info_request_message(phone_number),
                'next_action': 'waiting_for_info',
                'requires_handoff': False,
                'info_status': info_status
            }
    
    def _handle_complete_info(self, 
                             phone_number: str, 
                             message: str, 
                             intent: str, 
                             entities: Dict) -> Dict[str, Any]:
        """
        Lida com informações completas - prossegue com fluxo normal
        """
        # Atualizar informações baseado nas entidades
        if entities:
            self._update_patient_info_from_entities(phone_number, entities)
        
        # Determinar se precisa de handoff
        requires_handoff = self._should_trigger_handoff(intent, message)
        
        return {
            'response': None,  # Será preenchido pelo Gemini
            'next_action': 'proceed',
            'requires_handoff': requires_handoff,
            'info_status': {'is_complete': True}
        }
    
    def _get_name_request_message(self, phone_number: str) -> str:
        """
        Gera mensagem para solicitar nome completo
        """
        # Verificar se já tentou antes
        session = self.conversation_service.get_or_create_session(phone_number)
        message_count = session.messages.filter(message_type='bot').count()
        
        if message_count <= 1:
            return """👋 Olá! Bem-vindo à nossa clínica! 

Para podermos ajudá-lo melhor, preciso do seu **nome completo** para o agendamento.

Por favor, me informe seu nome e sobrenome. 😊"""
        else:
            return """📝 Preciso do seu **nome completo** para prosseguir com o agendamento.

Por favor, me informe seu nome e sobrenome. Exemplo: "João Silva" """
    
    def _get_phone_request_message(self, phone_number: str) -> str:
        """
        Gera mensagem para solicitar telefone (caso necessário)
        """
        return """📱 Para confirmar seu agendamento, preciso do seu número de telefone.

Por favor, me informe seu número com DDD. Exemplo: (11) 99999-9999"""
    
    def _get_general_info_request_message(self, phone_number: str) -> str:
        """
        Gera mensagem geral para solicitar informações
        """
        return """📋 Para prosseguir com seu agendamento, preciso de algumas informações:

• Seu nome completo
• Especialidade desejada
• Convênio (se houver)

Como posso ajudá-lo? 😊"""
    
    def _update_patient_info_from_entities(self, phone_number: str, entities: Dict):
        """
        Atualiza informações do paciente baseado nas entidades extraídas
        """
        try:
            update_data = {}
            
            if 'specialties' in entities and entities['specialties']:
                update_data['specialty_interest'] = entities['specialties'][0]
            
            if 'insurance' in entities:
                update_data['insurance_type'] = entities['insurance']
            
            if 'dates' in entities and entities['dates']:
                try:
                    date_str = entities['dates'][0]
                    if '/' in date_str:
                        day, month, year = date_str.split('/')
                        if len(year) == 2:
                            year = '20' + year
                        update_data['preferred_date'] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                except:
                    pass
            
            if 'times' in entities and entities['times']:
                update_data['preferred_time'] = entities['times'][0]
            
            if 'doctors' in entities and entities['doctors']:
                update_data['selected_doctor'] = entities['doctors'][0]
            
            if update_data:
                self.conversation_service.update_patient_info(phone_number, **update_data)
                
        except Exception as e:
            logger.error(f"Erro ao atualizar informações do paciente: {e}")
    
    def _should_trigger_handoff(self, intent: str, message: str) -> bool:
        """
        Determina se deve acionar o handoff
        """
        return BaseService.should_trigger_handoff(intent, message)
    
    def validate_patient_name(self, name: str) -> Tuple[bool, str]:
        """
        Valida se o nome fornecido é válido
        
        Returns:
            Tuple (is_valid, error_message)
        """
        return BaseService.validate_patient_name(name)
    
    def extract_phone_from_message(self, message: str) -> Optional[str]:
        """
        Extrai número de telefone da mensagem
        """
        return BaseService.extract_phone_from_message(message)


# Instância global do serviço
smart_collection_service = SmartCollectionService()
