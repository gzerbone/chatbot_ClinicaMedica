"""
Serviço de Conversas com Persistência em Banco de Dados
Gerencia conversas de agendamento de forma persistente
"""
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from django.core.cache import cache
from django.utils import timezone

from ..models import ConversationMessage, ConversationSession

''
logger = logging.getLogger(__name__)

# Logger específico para conversação
conversation_logger = logging.getLogger('conversation')


class ConversationService:
    """
    Serviço para gerenciar conversas de agendamento com persistência
    """
    
    
    def get_or_create_session(self, phone_number: str) -> ConversationSession:
        """
        Obtém ou cria uma sessão de conversa
        """
        try:
            session, created = ConversationSession.objects.get_or_create(
                phone_number=phone_number,
                defaults={
                    'current_state': 'idle',
                    'last_activity': timezone.now()
                }
            )
            
            if not created:
                # Atualizar atividade se sessão existente
                session.update_activity()
            
            return session
            
        except Exception as e:
            logger.error(f"Erro ao obter/criar sessão para {phone_number}: {e}")
            # Fallback: criar sessão básica
            return ConversationSession.objects.create(
                phone_number=phone_number,
                current_state='idle'
            )
    
    def add_message(self, 
                   phone_number: str, 
                   content: str, 
                   message_type: str = 'user',
                   intent: str = None,
                   confidence: float = None,
                   entities: Dict = None) -> ConversationMessage:
        """
        Adiciona uma mensagem à conversa
        """
        try:
            session = self.get_or_create_session(phone_number)
            
            message = ConversationMessage.objects.create(
                session=session,
                message_type=message_type,
                content=content,
                intent=intent,
                confidence=confidence,
                entities=entities or {}
            )
            
            # Atualizar estado da sessão baseado na intenção
            self._update_session_state(session, intent, entities)
            
            logger.info(f"Mensagem adicionada para {phone_number}: {content[:50]}...")
            return message
            
        except Exception as e:
            logger.error(f"Erro ao adicionar mensagem: {e}")
            raise
    
    def get_conversation_history(self, phone_number: str, limit: int = 10) -> List[Dict]:
        """
        Obtém histórico da conversa
        """
        try:
            session = self.get_or_create_session(phone_number)
            messages = session.messages.all()[:limit]
            # O Django automaticamente:
            # 1. Busca todas as ConversationMessage onde session_id = session.id
            # 2. Aplica o limite especificado
            # 3. Retorna um QuerySet das mensagens
            
            # Cria um dicionário para cada mensagem
            return [
                {
                    'content': msg.content,
                    'message_type': msg.message_type,
                    'intent': msg.intent,
                    'confidence': msg.confidence,
                    'entities': msg.entities,
                    'timestamp': msg.timestamp.isoformat(),
                    'is_user': msg.message_type == 'user'
                }
                for msg in messages
            ]
            
        except Exception as e:
            logger.error(f"Erro ao obter histórico: {e}")
            return []
    
    def update_patient_info(self, phone_number: str, **kwargs) -> bool:
        """
        Atualiza informações do paciente na sessão
        """
        try:
            session = self.get_or_create_session(phone_number)
            
            # Atualizar campos permitidos
            allowed_fields = [
                'patient_name', 'insurance_type','preferred_date', 
                'preferred_time', 'selected_doctor','selected_specialty',
                'additional_notes'
            ]
            
            for field, value in kwargs.items():
                if field in allowed_fields and value:
                    setattr(session, field, value)
            
            session.save()
            logger.info(f"Informações do paciente atualizadas para {phone_number}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao atualizar informações do paciente: {e}")
            return False
    
    def get_patient_info(self, phone_number: str) -> Dict[str, Any]:
        """
        Obtém informações do paciente da sessão
        """
        try:
            session = self.get_or_create_session(phone_number)
            
            return {
                'patient_name': session.patient_name,
                'selected_specialty': session.selected_specialty,
                'insurance_type': session.insurance_type,
                'preferred_date': session.preferred_date.isoformat() if session.preferred_date else None,
                'preferred_time': session.preferred_time.isoformat() if session.preferred_time else None,
                'selected_doctor': session.selected_doctor,
                'additional_notes': session.additional_notes,
                'current_state': session.current_state
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter informações do paciente: {e}")
            return {}
    
    def finalize_session(self, phone_number: str) -> bool:
        """
        Finaliza uma sessão e reseta o nome confirmado para permitir nova sessão
        
        Args:
            phone_number: Número do telefone
            
        Returns:
            True se finalizada com sucesso
        """
        try:
            session = self.get_or_create_session(phone_number)
            
            # Resetar nome confirmado para permitir nova sessão
            session.name_confirmed = False
            session.pending_name = None
            
            # Atualizar estado da sessão
            session.current_state = 'idle'
            session.save()
            
            logger.info(f"Sessão finalizada para {phone_number}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao finalizar sessão: {e}")
            return False
    
    
    def _update_session_state(self, session: ConversationSession, intent: str, entities: Dict):
        """
        Atualiza estado da sessão baseado na intenção
        """
        if not intent:
            return
        
        # Mapear intenções para estados
        intent_to_state = {
            'saudacao': 'collecting_patient_info',
            'buscar_info': 'answering_questions',  # Apenas para tirar dúvidas
            'agendar_consulta': 'choosing_schedule',  # Inclui seleção de médico/especialidade
            'confirmar_agendamento': 'confirming',
            'duvida': 'answering_questions'
        }
        
        # Se o intent existir no dicionário: retorna o valor correspondente (o estado)
        # Ex: intent_to_state.get('saudacao') → retorna 'collecting_patient_info'
        # Se o intent não existir no dicionário: retorna None
        # Ex: intent_to_state.get('buscar_exame') → retorna None
        new_state = intent_to_state.get(intent)
        
        # Verifica se o novo estado é diferente do estado atual da sessão. Se for, atualiza o estado da sessão.
        if new_state and new_state != session.current_state:
            session.current_state = new_state
            session.save()
        
        # Atualizar informações baseado nas entidades
        if entities:
            update_data = {}
            
            if 'patient_name' in entities and entities['patient_name']:
                update_data['patient_name'] = entities['patient_name'][0]
            
            if 'specialties' in entities and entities['specialties']:
                update_data['selected_specialty'] = entities['specialties'][0]
            
            if 'insurance' in entities:
                update_data['insurance_type'] = entities['insurance']
            
            if 'dates' in entities and entities['dates']:
                # Converter data para formato correto
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
            
            if update_data:
                for field, value in update_data.items():
                    setattr(session, field, value)
                session.save()
    
    
    def get_missing_appointment_info(self, phone_number: str) -> Dict[str, Any]:
        """
        Verifica quais informações faltam para completar o agendamento
        
        Args:
            phone_number: Número do telefone
            
        Returns:
            Dict com informações faltantes e próxima ação sugerida
        """
        try:
            session = self.get_or_create_session(phone_number)
            
            missing_info = []
            
            # Verificar informações obrigatórias
            if not session.patient_name:
                missing_info.append('patient_name')
            
            if not session.selected_specialty:
                missing_info.append('selected_specialty')
            
            if not session.selected_doctor:
                missing_info.append('selected_doctor')
            
            if not session.preferred_date:
                missing_info.append('preferred_date')
            
            if not session.preferred_time:
                missing_info.append('preferred_time')
            
            # Determinar próxima ação
            next_action = self._get_next_action(missing_info)
            
            return {
                'missing_info': missing_info,
                'next_action': next_action,
                'is_complete': len(missing_info) == 0,
                'current_state': session.current_state
            }
            
        except Exception as e:
            logger.error(f"Erro ao verificar informações faltantes: {e}")
            return {
                'missing_info': [],
                'next_action': 'proceed',
                'is_complete': False,
                'current_state': 'idle'
            }
    
    def pause_for_question(self, phone_number: str) -> bool:
        """
        Pausa o fluxo de agendamento para responder dúvidas
        Salva o estado atual para retornar depois
        
        Args:
            phone_number: Número do telefone
            
        Returns:
            True se pausou com sucesso
        """
        try:
            session = self.get_or_create_session(phone_number)
            
            # Salvar estado atual antes de pausar
            if session.current_state != 'answering_questions':
                session.previous_state = session.current_state
                session.current_state = 'answering_questions'
                session.save()
                
                logger.info(f"⏸️ Agendamento pausado para dúvidas. Estado anterior: {session.previous_state}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Erro ao pausar para dúvidas: {e}")
            return False
    
    def resume_appointment(self, phone_number: str) -> Dict[str, Any]:
        """
        Retoma o fluxo de agendamento após responder dúvidas
        
        Args:
            phone_number: Número do telefone
            
        Returns:
            Dict com informações sobre o retorno
        """
        try:
            session = self.get_or_create_session(phone_number)
            
            if session.current_state == 'answering_questions' and session.previous_state:
                # Restaurar estado anterior
                restored_state = session.previous_state
                session.current_state = restored_state
                session.previous_state = None
                session.save()
                
                logger.info(f"▶️ Agendamento retomado. Estado restaurado: {restored_state}")
                
                # Obter próxima pergunta do fluxo
                next_question = self.get_next_question(phone_number)
                
                return {
                    'resumed': True,
                    'restored_state': restored_state,
                    'next_question': next_question,
                    'message': f'Perfeito! Vamos continuar seu agendamento de onde paramos. {next_question}'
                }
            
            return {
                'resumed': False,
                'message': 'Não há agendamento pausado para retomar.'
            }
            
        except Exception as e:
            logger.error(f"Erro ao retomar agendamento: {e}")
            return {
                'resumed': False,
                'message': 'Ocorreu um erro ao retomar o agendamento.'
            }
    
    def is_in_question_mode(self, phone_number: str) -> bool:
        """
        Verifica se o usuário está no modo de dúvidas
        
        Args:
            phone_number: Número do telefone
            
        Returns:
            True se está em modo de dúvidas
        """
        try:
            session = self.get_or_create_session(phone_number)
            return session.current_state == 'answering_questions'
        except:
            return False
    
    def has_paused_appointment(self, phone_number: str) -> bool:
        """
        Verifica se há um agendamento pausado
        
        Args:
            phone_number: Número do telefone
            
        Returns:
            True se há agendamento pausado
        """
        try:
            session = self.get_or_create_session(phone_number)
            return session.current_state == 'answering_questions' and session.previous_state is not None
        except:
            return False
    
    def get_next_question(self, phone_number: str) -> Optional[str]:
        """
        Gera a próxima pergunta apropriada baseada nas informações faltantes
        
        Args:
            phone_number: Número do telefone
            
        Returns:
            Próxima pergunta sugerida ou None
        """
        try:
            missing_info_result = self.get_missing_appointment_info(phone_number)
            
            if missing_info_result['is_complete']:
                return None
            
            action = missing_info_result['next_action']
            session = self.get_or_create_session(phone_number)
            patient_name = session.patient_name or 'paciente'
            
            # Mensagens baseadas na próxima ação
            action_messages = {
                'ask_name': 'Para começar o agendamento, preciso saber seu nome completo. Qual é seu nome?',
                'ask_specialty': f'Olá {patient_name}! Qual especialidade médica você procura?',
                'ask_doctor': f'Perfeito {patient_name}! Temos médicos disponíveis nessa especialidade. Qual médico você prefere?',
                'ask_date': f'Ótimo {patient_name}! Para qual data você gostaria de agendar?',
                'ask_time': f'Perfeito! Qual horário seria melhor para você?'
            }
            
            return action_messages.get(action, 'Como posso ajudá-lo com seu agendamento?')
            
        except Exception as e:
            logger.error(f"Erro ao gerar próxima pergunta: {e}")
            return None
    
    def _get_next_action(self, missing_info: List[str]) -> str:
        """
        Determina a próxima ação baseada nas informações faltantes
        
        Args:
            missing_info: Lista de informações faltantes
            
        Returns:
            Próxima ação sugerida
        """
        if not missing_info:
            return 'generate_handoff'
        
        # Fluxo sequencial de coleta
        if 'patient_name' in missing_info:
            return 'ask_name'
        elif 'selected_specialty' in missing_info:
            return 'ask_specialty'
        elif 'selected_doctor' in missing_info:
            return 'ask_doctor'
        elif 'preferred_date' in missing_info:
            return 'ask_date'
        elif 'preferred_time' in missing_info:
            return 'ask_time'
        else:
            return 'ask_general'
    
    def extract_patient_name(self, message: str) -> Optional[str]:
        """
        Extrai nome completo do paciente da mensagem
        """
        import re

        # Padrões para extrair nome
        name_patterns = [
            r'meu\s+nome\s+é\s+([A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+)*)',
            r'sou\s+([A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+)*)',
            r'chamo-me\s+([A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+)*)',
            r'nome\s+é\s+([A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+)*)',
            r'me\s+chamo\s+([A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+)*)',
            r'^([A-Za-zÀ-ÿ]+\s+[A-Za-zÀ-ÿ]+)(?:\s|,|$)'
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Limitar a 3 palavras (nome + sobrenome + sobrenome)
                name_parts = name.split()[:3]
                if len(name_parts) >= 2:  # Pelo menos nome e sobrenome
                    return ' '.join(name_parts).title()
        
        return None
    
    def process_patient_name(self, phone_number: str, message: str) -> Dict[str, Any]:
        """
        Processa nome do paciente com confirmação
        """
        try:
            session = self.get_or_create_session(phone_number)
            
            # Extrair nome da mensagem
            extracted_name = self.extract_patient_name(message)
            
            if extracted_name:
                # Armazenar nome pendente de confirmação
                session.pending_name = extracted_name
                session.save()
                
                return {
                    'status': 'confirmation_needed',
                    'message': f'Confirma se seu nome é {extracted_name}?',
                    'extracted_name': extracted_name
                }
            else:
                return {
                    'status': 'name_not_found',
                    'message': 'Não consegui identificar seu nome. Por favor, digite seu nome completo.'
                }
                
        except Exception as e:
            logger.error(f"Erro ao processar nome do paciente: {e}")
            return {
                'status': 'error',
                'message': 'Ocorreu um erro ao processar seu nome. Tente novamente.'
            }

    
    def normalize_date_for_database(self, date_str: str) -> Optional[str]:
        """
        Normaliza string de data para formato do banco de dados
        
        Args:
            date_str: String de data em vários formatos
            
        Returns:
            Data normalizada em formato YYYY-MM-DD ou None se inválida
        """
        if not date_str:
            return None
            
        try:
            from datetime import datetime, timedelta

            from django.utils import timezone

            date_lower = date_str.lower().strip()
            
            # Tratar palavras especiais primeiro
            today = timezone.now().date()
            
            if 'hoje' in date_lower:
                return today.strftime('%Y-%m-%d')
            elif 'amanhã' in date_lower or 'amanha' in date_lower:
                tomorrow = today + timedelta(days=1)
                return tomorrow.strftime('%Y-%m-%d')
            elif 'depois de amanhã' in date_lower or 'depois de amanha' in date_lower:
                day_after = today + timedelta(days=2)
                return day_after.strftime('%Y-%m-%d')
            elif any(day in date_lower for day in ['segunda', 'terça', 'quarta', 'quinta', 'sexta', 'sábado', 'domingo']):
                # Para dias da semana, usar a lógica do smart_scheduling_service
                from .smart_scheduling_service import SmartSchedulingService
                smart_service = SmartSchedulingService()
                normalized_date = smart_service._normalize_date(date_str)
                if normalized_date:
                    return normalized_date.strftime('%Y-%m-%d')

            # Tentar diferentes formatos de data
            date_formats = [
                '%d/%m/%Y',  # 15/09/2024
                '%d/%m/%y',  # 15/09/24
                '%d-%m-%Y',  # 15-09-2024
                '%Y-%m-%d',  # 2024-09-15
                '%d/%m',     # 15/09 (assumir ano atual)
            ]
            
            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(date_str, fmt)
                    
                    # Se não tem ano, assumir ano atual
                    if fmt == '%d/%m':
                        parsed_date = parsed_date.replace(year=datetime.now().year)
                    
                    return parsed_date.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            
            # Se não conseguiu fazer parse, retornar string original
            logger.warning(f"Data não pôde ser normalizada: {date_str}")
            return date_str
            
        except Exception as e:
            logger.error(f"Erro ao normalizar data '{date_str}': {e}")
            return date_str

# Instância global do serviço
conversation_service = ConversationService()
