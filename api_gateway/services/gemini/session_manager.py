"""
Session Manager - Gerenciamento de Sessões de Conversa

Responsável por:
- Criar e recuperar sessões
- Atualizar dados da sessão
- Sincronizar com cache e banco de dados
- Gerenciar histórico de conversas
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from django.core.cache import cache
from django.utils import timezone

from ..token_monitor import token_monitor

logger = logging.getLogger(__name__)


class SessionManager:
    """Gerenciamento de sessões de conversa"""
    
    def get_or_create_session(self, phone_number: str) -> Dict[str, Any]:
        """
        Obtém ou cria sessão da conversa - carrega do banco se necessário
        
        Args:
            phone_number: Número de telefone do usuário
            
        Returns:
            Dict com dados da sessão
        """
        cache_key = f"gemini_session_{phone_number}"
        session = cache.get(cache_key)
        
        if not session:
            # Tentar carregar do banco de dados
            try:
                from api_gateway.models import ConversationSession
                db_session = ConversationSession.objects.filter(phone_number=phone_number).first()
                
                if db_session:
                    # Carregar dados do banco para o cache
                    session = {
                        'phone_number': phone_number,
                        'current_state': db_session.current_state,
                        'patient_name': db_session.patient_name,
                        'selected_doctor': db_session.selected_doctor,
                        'selected_specialty': db_session.selected_specialty,
                        'preferred_date': db_session.preferred_date.isoformat() if db_session.preferred_date else None,
                        'preferred_time': db_session.preferred_time.isoformat() if db_session.preferred_time else None,
                        'insurance_type': db_session.insurance_type,
                        'created_at': db_session.created_at.isoformat(),
                        'last_activity': timezone.now().isoformat()
                    }
                    logger.info(f"📥 Sessão carregada do banco - Nome: {db_session.patient_name}, Médico: {db_session.selected_doctor}")
                else:
                    # Criar nova sessão
                    session = self._create_empty_session(phone_number)
                    logger.info(f"🆕 Nova sessão criada para {phone_number}")
            except Exception as e:
                logger.error(f"Erro ao carregar sessão do banco: {e}")
                # Fallback: criar sessão vazia
                session = self._create_empty_session(phone_number)
            
            cache.set(cache_key, session, token_monitor.get_cache_timeout())
        
        return session
    
    def _create_empty_session(self, phone_number: str) -> Dict[str, Any]:
        """Cria uma sessão vazia"""
        return {
            'phone_number': phone_number,
            'current_state': 'idle',
            'patient_name': None,
            'selected_doctor': None,
            'selected_specialty': None,
            'preferred_date': None,
            'preferred_time': None,
            'insurance_type': None,
            'created_at': timezone.now().isoformat(),
            'last_activity': timezone.now().isoformat()
        }
    
    def update_session(self, phone_number: str, session: Dict, 
                      analysis_result: Dict, response_result: Dict):
        """
        Atualiza sessão com base na análise e resposta
        
        Args:
            phone_number: Número de telefone
            session: Sessão atual
            analysis_result: Resultado da análise de intenção
            response_result: Resultado da geração de resposta
        """
        try:
            # Atualizar estado (não sobrescrever se já estiver confirmando)
            if session.get('current_state') != 'confirming':
                session['current_state'] = analysis_result['next_state']
            session['last_activity'] = timezone.now().isoformat()
            
            # Atualizar entidades extraídas
            entities = analysis_result['entities']
            
            # Log das entidades extraídas para debug
            if entities:
                logger.info(f"🔍 Entidades extraídas: {entities}")
            
            # Atualizar nome do paciente
            if entities.get('nome_paciente') and entities['nome_paciente'] != 'null':
                session['patient_name'] = entities['nome_paciente']
                logger.info(f"✅ Nome atualizado: {entities['nome_paciente']}")
            
            # Atualizar médico selecionado
            if entities.get('medico') and entities['medico'] != 'null':
                session['selected_doctor'] = entities['medico']
                logger.info(f"✅ Médico atualizado: {entities['medico']}")
            
            # Atualizar especialidade selecionada
            if entities.get('especialidade') and entities['especialidade'] != 'null':
                session['selected_specialty'] = entities['especialidade']
                logger.info(f"✅ Especialidade atualizada: {entities['especialidade']}")
            
            # Atualizar data preferida
            if entities.get('data') and entities['data'] != 'null':
                session['preferred_date'] = self._process_date(entities['data'])
            
            # Atualizar horário preferido
            if entities.get('horario') and entities['horario'] != 'null':
                session['preferred_time'] = self._process_time(entities['horario'])
            
            # Log do status das informações coletadas
            info_status = {
                'nome': bool(session.get('patient_name')),
                'medico': bool(session.get('selected_doctor')),
                'especialidade': bool(session.get('selected_specialty')),
                'data': bool(session.get('preferred_date')),
                'horario': bool(session.get('preferred_time'))
            }
            logger.info(f"📋 Status das informações: {info_status}")
            
            # Salvar sessão no cache
            cache_key = f"gemini_session_{phone_number}"
            cache.set(cache_key, session, token_monitor.get_cache_timeout())
            
            # Log do estado final da sessão
            logger.info(f"📋 Sessão atualizada - Estado: {session['current_state']}, Nome: {session.get('patient_name')}, Médico: {session.get('selected_doctor')}")
            
            # Sincronizar com banco de dados
            self.sync_to_database(phone_number, session)
            
        except Exception as e:
            logger.error(f"Erro ao atualizar sessão: {e}")
    
    def _process_date(self, date_str: str) -> Optional[str]:
        """Processa e normaliza string de data"""
        try:
            import re

            # Primeiro, tentar extrair data de formatos como "Sexta (10/10/2025)"
            date_pattern = r'\((\d{1,2}/\d{1,2}/\d{4})\)'
            match = re.search(date_pattern, date_str)
            if match:
                extracted_date = match.group(1)
                logger.info(f"🔍 Data extraída do padrão: {extracted_date}")
                date_str = extracted_date
            
            # Normalizar data
            from ..conversation_service import conversation_service
            normalized_date = conversation_service.normalize_date_for_database(date_str)
            
            if normalized_date:
                logger.info(f"✅ Data atualizada (normalizada): {normalized_date}")
                return normalized_date
            else:
                # Se não conseguir normalizar, salvar como string
                logger.info(f"✅ Data atualizada (string): {date_str}")
                return date_str
                
        except Exception as e:
            logger.error(f"Erro ao processar data: {e}")
            logger.info(f"✅ Data atualizada (fallback): {date_str}")
            return date_str
    
    def _process_time(self, time_str: str) -> Optional[str]:
        """Processa e normaliza string de horário"""
        try:
            # Tentar diferentes formatos de horário
            from datetime import datetime
            time_formats = ['%H:%M', '%H:%M:%S', '%I:%M %p', '%I:%M:%S %p']
            parsed_time = None
            
            for fmt in time_formats:
                try:
                    parsed_time = datetime.strptime(time_str, fmt).time()
                    break
                except ValueError:
                    continue
            
            if parsed_time:
                logger.info(f"✅ Horário atualizado: {parsed_time}")
                return parsed_time.isoformat()
            else:
                # Se não conseguir fazer parse, salvar como string
                logger.info(f"✅ Horário atualizado (string): {time_str}")
                return time_str
                
        except Exception as e:
            logger.error(f"Erro ao processar horário: {e}")
            logger.info(f"✅ Horário atualizado (fallback): {time_str}")
            return time_str
    
    def sync_to_database(self, phone_number: str, session: Dict):
        """
        Sincroniza sessão do cache com o banco de dados
        
        Args:
            phone_number: Número de telefone
            session: Dados da sessão
        """
        try:
            from api_gateway.models import ConversationSession

            from ..conversation_service import conversation_service

            # Normalizar data antes de salvar
            normalized_date = conversation_service.normalize_date_for_database(session.get('preferred_date'))

            # Obter ou criar sessão no banco
            db_session, created = ConversationSession.objects.get_or_create(
                phone_number=phone_number,
                defaults={
                    'current_state': session.get('current_state', 'idle'),
                    'patient_name': session.get('patient_name'),
                    'name_confirmed': bool(session.get('patient_name')),
                    'pending_name': 'Paciente',
                    'insurance_type': session.get('insurance_type'),
                    'selected_doctor': session.get('selected_doctor'),
                    'selected_specialty': session.get('selected_specialty'),
                    'preferred_date': normalized_date,
                    'preferred_time': session.get('preferred_time'),
                    'additional_notes': session.get('additional_notes'),
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
                db_session.selected_doctor = session.get('selected_doctor')
                db_session.selected_specialty = session.get('selected_specialty')
                db_session.preferred_date = normalized_date
                db_session.preferred_time = session.get('preferred_time')
                db_session.additional_notes = session.get('additional_notes')
                db_session.updated_at = timezone.now()
                db_session.save()
            
            logger.info(f"💾 Sessão sincronizada com banco - ID: {db_session.id}, Nome: {db_session.patient_name}, Data: {normalized_date}")
            
        except Exception as e:
            logger.error(f"Erro ao sincronizar sessão com banco: {e}")
    
    def get_conversation_history(self, phone_number: str, limit: int = 10) -> List[Dict]:
        """
        Obtém histórico da conversa
        
        Args:
            phone_number: Número de telefone
            limit: Limite de mensagens a retornar
            
        Returns:
            Lista de mensagens do histórico
        """
        try:
            from ..conversation_service import conversation_service
            return conversation_service.get_conversation_history(phone_number, limit)
        except:
            return []
    
    def save_messages(self, phone_number: str, user_message: str, bot_response: str, 
                     analysis_result: Dict = None):
        """
        Salva mensagens no histórico com entidades extraídas
        
        Args:
            phone_number: Número de telefone
            user_message: Mensagem do usuário
            bot_response: Resposta do bot
            analysis_result: Resultado da análise (opcional)
        """
        try:
            from ..conversation_service import conversation_service

            # Preparar entidades para salvar no banco
            entities_to_save = {}
            if analysis_result and analysis_result.get('entities'):
                entities_to_save = analysis_result['entities']
            
            # Salvar mensagem do usuário com entidades
            user_msg = conversation_service.add_message(
                phone_number, user_message, 'user',
                analysis_result.get('intent', 'user_message') if analysis_result else 'user_message',
                analysis_result.get('confidence', 1.0) if analysis_result else 1.0,
                entities_to_save
            )
            
            if user_msg:
                logger.info(f"💾 Mensagem do usuário salva no banco com ID: {user_msg.id}")
                logger.info(f"🔍 Entidades salvas: {entities_to_save}")
            
            # Salvar resposta do bot
            bot_msg = conversation_service.add_message(
                phone_number, bot_response, 'bot',
                'bot_response', 1.0, {}
            )
            
            if bot_msg:
                logger.info(f"💾 Resposta do bot salva no banco com ID: {bot_msg.id}")
            
        except Exception as e:
            logger.error(f"Erro ao salvar mensagens: {e}")


