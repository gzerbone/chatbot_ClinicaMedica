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
    
    def _update_session_state(self, session: ConversationSession, intent: str, entities: Dict):
        """
        Atualiza estado da sessão baseado na intenção
        
        INTENÇÕES PRINCIPAIS (definidas no IntentDetector):
        1. saudacao - Cumprimentos iniciais
        2. buscar_info - Perguntas sobre a clínica (apenas dúvidas)
        3. agendar_consulta - Solicitar agendamento
        4. confirmar_agendamento - Confirmar dados do agendamento
        5. duvida - Não compreendeu, pedir ajuda
        
        INTENÇÕES INTERNAS (usadas no core_service.py):
        - retomar_agendamento - Retomar agendamento pausado
        - selecionar_especialidade - Selecionar especialidade
        - confirmar_nome - Confirmar nome do paciente
        - solicitar_data_numerica - Solicitar data em formato numérico
        - informar_horario_indisponivel - Informar que horário está indisponível
        - error - Erro no processamento
        """
        if not intent:
            return
        
        # Mapear intenções para estados
        intent_to_state = {
            'saudacao': 'collecting_patient_info',
            'buscar_info': 'answering_questions',  # Apenas para tirar dúvidas
            'duvida': 'answering_questions',
            'confirmar_agendamento': 'confirming',
        }
        
        # Para agendar_consulta, determinar o estado baseado nas informações já coletadas
        # ORDEM OBRIGATÓRIA: nome → especialidade → médico → data/horário
        if intent == 'agendar_consulta':
            # Verificar o que falta para determinar o próximo estado
            missing_info_result = self.get_missing_appointment_info(session.phone_number)
            missing_info = missing_info_result.get('missing_info', [])
            
            # Determinar próximo estado baseado na ordem obrigatória
            if 'patient_name' in missing_info:
                # Se não tem nome, pode estar coletando ou confirmando
                if session.pending_name:
                    new_state = 'confirming_name'
                else:
                    new_state = 'collecting_patient_info'
            elif 'selected_specialty' in missing_info:
                new_state = 'selecting_specialty'
            elif 'selected_doctor' in missing_info:
                new_state = 'selecting_doctor'
            elif 'preferred_date' in missing_info or 'preferred_time' in missing_info:
                new_state = 'choosing_schedule'
            else:
                # Todas as informações coletadas, pode ir para confirmação
                new_state = 'choosing_schedule'  # Mantém escolhendo horário até confirmar
        else:
            # Para outras intenções, usar mapeamento direto
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
        VALIDA se especialidade e médico salvos são válidos no banco
        
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
            
            # VALIDAR especialidade salva (pode estar inválida)
            if not session.selected_specialty:
                missing_info.append('selected_specialty')
            else:
                # Validar se especialidade salva existe no banco
                if not self._validate_specialty_in_db(session.selected_specialty):
                    logger.warning(f"⚠️ Especialidade salva '{session.selected_specialty}' é inválida. Considerando como faltante.")
                    missing_info.append('selected_specialty')
                    # Limpar especialidade inválida
                    session.selected_specialty = None
                    session.save()
            
            # VALIDAR médico salvo (pode estar inválido)
            if not session.selected_doctor:
                missing_info.append('selected_doctor')
            else:
                # Validar se médico salvo existe no banco
                if not self._validate_doctor_in_db(session.selected_doctor, session.selected_specialty):
                    logger.warning(f"⚠️ Médico salvo '{session.selected_doctor}' é inválido. Considerando como faltante.")
                    missing_info.append('selected_doctor')
                    # Limpar médico inválido
                    session.selected_doctor = None
                    session.save()
            
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
            current_state = session.current_state
            
            # Mensagens baseadas na próxima ação, considerando o estado atual
            # Se já temos nome, não perguntar novamente
            if action == 'ask_name' and patient_name:
                # Se já tem nome, pular para próxima ação
                if session.selected_specialty:
                    action = 'ask_doctor' if not session.selected_doctor else 'ask_date'
                else:
                    action = 'ask_specialty'
            
            action_messages = {
                'ask_name': 'Olá, sou a assistente virtual da clínica, antes de iniciar agendamento e tirar suas dúvidas, preciso saber seu nome completo. Qual é seu nome?',
                'ask_specialty': f'Olá {patient_name}! Qual especialidade médica você procura?' if patient_name else 'Qual especialidade médica você procura?',
                'ask_doctor': f'Perfeito {patient_name}! Temos médicos disponíveis nessa especialidade. Qual médico você prefere?' if patient_name else 'Temos médicos disponíveis nessa especialidade. Qual médico você prefere?',
                'ask_date': f'Ótimo {patient_name}! Para qual data você gostaria de agendar?' if patient_name else 'Para qual data você gostaria de agendar?',
                'ask_time': f'Perfeito! Qual horário seria melhor para você?'
            }
            
            return action_messages.get(action, 'Como posso ajudá-lo com seu agendamento?')
            
        except Exception as e:
            logger.error(f"Erro ao gerar próxima pergunta: {e}")
            return None
    
    def _validate_specialty_in_db(self, specialty_name: str) -> bool:
        """
        Valida se especialidade existe no banco de dados
        
        Args:
            specialty_name: Nome da especialidade a validar
            
        Returns:
            True se especialidade é válida, False caso contrário
        """
        try:
            from rag_agent.models import Especialidade
            
            if not specialty_name:
                return False
            
            specialty_name_lower = specialty_name.lower().strip()
            
            # Busca exata (case-insensitive)
            especialidade = Especialidade.objects.filter(
                nome__iexact=specialty_name_lower,
                ativa=True
            ).first()
            
            if especialidade:
                return True
            
            # Busca parcial (contém)
            especialidade = Especialidade.objects.filter(
                nome__icontains=specialty_name_lower,
                ativa=True
            ).first()
            
            return especialidade is not None
            
        except Exception as e:
            logger.error(f"Erro ao validar especialidade '{specialty_name}': {e}")
            return False
    
    def _validate_doctor_in_db(self, doctor_name: str, specialty: Optional[str] = None) -> bool:
        """
        Valida se médico existe no banco de dados
        
        Args:
            doctor_name: Nome do médico a validar
            specialty: Especialidade (opcional) para validar se médico tem essa especialidade
            
        Returns:
            True se médico é válido, False caso contrário
        """
        try:
            from rag_agent.models import Medico
            
            if not doctor_name:
                return False
            
            doctor_name_lower = doctor_name.lower().strip()
            
            # Buscar médico diretamente no banco (mais confiável que via serializer)
            medicos = Medico.objects.prefetch_related('especialidades').all()
            
            # Buscar médico por nome (busca flexível)
            for medico in medicos:
                medico_name = medico.nome
                medico_name_lower = medico_name.lower()
                
                # Busca exata ou parcial
                if (doctor_name_lower in medico_name_lower or 
                    medico_name_lower in doctor_name_lower):
                    
                    # Se especialidade foi fornecida, validar se médico tem essa especialidade
                    if specialty:
                        # Buscar especialidades do médico diretamente do banco
                        especialidades_medico = medico.especialidades.filter(ativa=True)
                        especialidades_nomes = [esp.nome.lower() for esp in especialidades_medico]
                        specialty_lower = specialty.lower()
                        
                        if specialty_lower not in especialidades_nomes:
                            continue
                    
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Erro ao validar médico '{doctor_name}': {e}")
            return False
    
    def _get_next_action(self, missing_info: List[str]) -> str:
        """
        Determina a próxima ação baseada nas informações faltantes
        
        ORDEM OBRIGATÓRIA:
        1. Nome do paciente
        2. Especialidade médica
        3. Médico (obrigatório antes de data/horário)
        4. Data
        5. Horário
        
        Args:
            missing_info: Lista de informações faltantes
            
        Returns:
            Próxima ação sugerida
        """
        if not missing_info:
            return 'generate_handoff'
        
        # Fluxo sequencial OBRIGATÓRIO de coleta
        # Ordem: nome → especialidade → médico → data → horário
        if 'patient_name' in missing_info:
            return 'ask_name'
        elif 'selected_specialty' in missing_info:
            return 'ask_specialty'
        elif 'selected_doctor' in missing_info:
            # IMPORTANTE: Médico DEVE ser selecionado antes de data/horário
            return 'ask_doctor'
        elif 'preferred_date' in missing_info:
            # Só pergunta data se já tiver especialidade E médico
            return 'ask_date'
        elif 'preferred_time' in missing_info:
            # Só pergunta horário se já tiver data
            return 'ask_time'
        else:
            return 'ask_general'
    

    def confirm_patient_name(self, phone_number: str, confirmation: str) -> Dict[str, Any]:
        """
        Confirma ou rejeita o nome do paciente
        """
        try:
            session = self.get_or_create_session(phone_number)
            
            # Verificar se há nome pendente
            if not session.pending_name:
                return {
                    'status': 'no_pending_name',
                    'message': 'Não há nome pendente de confirmação.'
                }
            
            # Verificar confirmação
            confirmation_lower = confirmation.lower()
            if any(word in confirmation_lower for word in ['sim', 's', 'yes', 'confirmo', 'correto', 'certo', 'isso']):
                # Confirmar nome
                session.patient_name = session.pending_name
                session.name_confirmed = True
                session.pending_name = None
                session.save()
                
                return {
                    'status': 'confirmed',
                    'message': f'Perfeito, {session.patient_name}! Como posso ajudá-lo hoje?',
                    'patient_name': session.patient_name
                }
            else:
                # Rejeitar nome
                session.pending_name = None
                session.save()
                
                return {
                    'status': 'rejected',
                    'message': 'Entendi. Por favor, digite seu nome completo novamente.'
                }
                
        except Exception as e:
            logger.error(f"Erro ao confirmar nome do paciente: {e}")
            return {
                'status': 'error',
                'message': 'Ocorreu um erro ao processar sua confirmação. Tente novamente.'
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
                parsed_date = smart_service._parse_date(date_str)
                if parsed_date:
                    return parsed_date.strftime('%Y-%m-%d')

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
