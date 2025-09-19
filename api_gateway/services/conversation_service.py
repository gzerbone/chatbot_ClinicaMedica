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

from ..models import (AppointmentRequest, ConversationMessage,
                      ConversationSession, RAGCache)
from .base_service import BaseService

logger = logging.getLogger(__name__)


class ConversationService:
    """
    Serviço para gerenciar conversas de agendamento com persistência
    """
    
    # Cache para dados RAG (temporário)
    RAG_CACHE_PREFIX = "rag_data_"
    RAG_CACHE_TIMEOUT = 3600  # 1 hora
    
    def __init__(self):
        self.rag_cache = RAGCacheService()
    
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
                'patient_name', 'specialty_interest', 'insurance_type',
                'preferred_date', 'preferred_time', 'selected_doctor',
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
                'specialty_interest': session.specialty_interest,
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
    
    def create_appointment_request(self, phone_number: str, **appointment_data) -> Optional[AppointmentRequest]:
        """
        Cria uma solicitação de agendamento
        """
        try:
            session = self.get_or_create_session(phone_number)
            
            # Verificar se já existe uma solicitação pendente
            if hasattr(session, 'appointment_request') and session.appointment_request.status == 'pending':
                logger.warning(f"Já existe solicitação pendente para {phone_number}")
                return session.appointment_request
            
            appointment = AppointmentRequest.objects.create(
                session=session,
                **appointment_data
            )
            
            # Atualizar estado da sessão
            session.current_state = 'completed'
            session.save()
            
            logger.info(f"Solicitação de agendamento criada para {phone_number}")
            return appointment
            
        except Exception as e:
            logger.error(f"Erro ao criar solicitação de agendamento: {e}")
            return None
    
    def get_appointment_request(self, phone_number: str) -> Optional[AppointmentRequest]:
        """
        Obtém solicitação de agendamento da sessão
        """
        try:
            session = self.get_or_create_session(phone_number)
            return getattr(session, 'appointment_request', None)
            
        except Exception as e:
            logger.error(f"Erro ao obter solicitação de agendamento: {e}")
            return None
    
    def _update_session_state(self, session: ConversationSession, intent: str, entities: Dict):
        """
        Atualiza estado da sessão baseado na intenção
        """
        if not intent:
            return
        
        # Mapear intenções para estados
        intent_to_state = {
            'saudacao': 'collecting_patient_info',
            'buscar_medico': 'selecting_doctor',
            'buscar_especialidade': 'collecting_info',
            'agendar_consulta': 'choosing_schedule',
            'confirmar_agendamento': 'confirming'
        }
        
        new_state = intent_to_state.get(intent)
        if new_state and new_state != session.current_state:
            session.current_state = new_state
            session.save()
        
        # Atualizar informações baseado nas entidades
        if entities:
            update_data = {}
            
            if 'patient_name' in entities and entities['patient_name']:
                update_data['patient_name'] = entities['patient_name'][0]
            
            if 'specialties' in entities and entities['specialties']:
                update_data['specialty_interest'] = entities['specialties'][0]
            
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
    
    def check_required_info(self, phone_number: str) -> Dict[str, Any]:
        """
        Verifica se as informações essenciais do paciente estão completas
        
        Returns:
            Dict com status das informações e próximos passos
        """
        try:
            session = self.get_or_create_session(phone_number)
            
            missing_info = []
            has_name = bool(session.patient_name and len(session.patient_name.split()) >= 2)
            has_phone = bool(phone_number and len(phone_number) >= 10)
            
            if not has_name:
                missing_info.append('nome_completo')
            
            if not has_phone:
                missing_info.append('telefone')
            
            return {
                'is_complete': len(missing_info) == 0,
                'missing_info': missing_info,
                'has_name': has_name,
                'has_phone': has_phone,
                'current_state': session.current_state,
                'next_action': self._get_next_action(session, missing_info)
            }
            
        except Exception as e:
            logger.error(f"Erro ao verificar informações: {e}")
            return {
                'is_complete': False,
                'missing_info': ['nome_completo', 'telefone'],
                'has_name': False,
                'has_phone': False,
                'current_state': 'idle',
                'next_action': 'ask_name'
            }
    
    def _get_next_action(self, session: ConversationSession, missing_info: List[str]) -> str:
        """
        Determina a próxima ação baseada nas informações faltantes
        """
        if not missing_info:
            return 'proceed'
        
        if 'nome_completo' in missing_info:
            return 'ask_name'
        elif 'telefone' in missing_info:
            return 'ask_phone'
        else:
            return 'ask_general'
    
    def extract_patient_name(self, message: str) -> Optional[str]:
        """
        Extrai nome completo do paciente da mensagem
        """
        return BaseService.extract_patient_name(message)
    
    def process_patient_name(self, phone_number: str, message: str) -> Dict[str, Any]:
        """
        Processa nome do paciente com confirmação
        """
        try:
            session = self.get_or_create_session(phone_number)
            
            # Se já tem nome confirmado, não processar novamente
            if session.name_confirmed and session.patient_name:
                return {
                    'status': 'already_confirmed',
                    'confirmed_name': session.patient_name,
                    'message': f'Já temos seu nome confirmado como: {session.patient_name}'
                }
            
            # Extrair nome da mensagem
            extracted_name = self.extract_patient_name(message)
            
            if not extracted_name:
                return {
                    'status': 'no_name_found',
                    'message': 'Não consegui identificar seu nome completo. Por favor, me informe seu nome e sobrenome.'
                }
            
            # Se já tem um nome pendente, verificar se é o mesmo
            if session.pending_name and session.pending_name.lower() == extracted_name.lower():
                return {
                    'status': 'same_name',
                    'pending_name': session.pending_name,
                    'message': f'Você já informou o nome "{session.pending_name}". Por favor, confirme se está correto.'
                }
            
            # Armazenar nome pendente e solicitar confirmação
            session.pending_name = extracted_name
            session.current_state = 'confirming_name'
            session.save()
            
            return {
                'status': 'confirmation_needed',
                'pending_name': extracted_name,
                'message': f'Entendi que seu nome é "{extracted_name}". Este é realmente o nome do paciente que deseja ser atendido? (Responda "sim" para confirmar ou "não" para informar outro nome)'
            }
            
        except Exception as e:
            logger.error(f"Erro ao processar nome do paciente: {e}")
            return {
                'status': 'error',
                'message': 'Ocorreu um erro ao processar seu nome. Tente novamente.'
            }
    
    def confirm_patient_name(self, phone_number: str, confirmation: str) -> Dict[str, Any]:
        """
        Confirma ou rejeita o nome do paciente
        """
        try:
            session = self.get_or_create_session(phone_number)
            
            if not session.pending_name:
                return {
                    'status': 'no_pending_name',
                    'message': 'Não há nome pendente para confirmar. Por favor, me informe seu nome completo.'
                }
            
            # Verificar confirmação
            confirmation_lower = confirmation.lower().strip()
            
            # Palavras de confirmação (mais específicas)
            confirm_words = ['sim', 's', 'yes', 'y', 'confirmo']
            # Palavras de rejeição (mais específicas)
            reject_words = ['não', 'nao', 'n', 'no', 'incorreto', 'errado']
            
            # Casos especiais: "está correto" vs "está errado" (prioridade)
            if 'está errado' in confirmation_lower or 'esta errado' in confirmation_lower:
                is_rejected = True
                is_confirmed = False
            elif 'está correto' in confirmation_lower or 'esta correto' in confirmation_lower:
                is_confirmed = True
                is_rejected = False
            else:
                # Verificar se contém palavras de confirmação
                is_confirmed = any(word in confirmation_lower for word in confirm_words)
                # Verificar se contém palavras de rejeição
                is_rejected = any(word in confirmation_lower for word in reject_words)
            
            if is_confirmed:
                # Confirmar nome
                session.patient_name = session.pending_name
                session.name_confirmed = True
                session.pending_name = None
                session.current_state = 'collecting_patient_info'
                session.save()
                
                return {
                    'status': 'confirmed',
                    'confirmed_name': session.patient_name,
                    'message': f'Perfeito! Seu nome "{session.patient_name}" foi confirmado. Agora vamos continuar com o agendamento.'
                }
            
            elif is_rejected:
                # Rejeitar nome e solicitar novo
                session.pending_name = None
                session.current_state = 'collecting_patient_info'
                session.save()
                
                return {
                    'status': 'rejected',
                    'message': 'Entendi. Por favor, me informe novamente seu nome completo para que possamos continuar.'
                }
            
            else:
                # Resposta não clara
                return {
                    'status': 'unclear_response',
                    'pending_name': session.pending_name,
                    'message': f'Não entendi sua resposta. O nome "{session.pending_name}" está correto? Responda "sim" para confirmar ou "não" para informar outro nome.'
                }
                
        except Exception as e:
            logger.error(f"Erro ao confirmar nome do paciente: {e}")
            return {
                'status': 'error',
                'message': 'Ocorreu um erro ao processar sua confirmação. Tente novamente.'
            }
    
    def cleanup_old_sessions(self, days_old: int = 7):
        """
        Remove sessões antigas
        """
        try:
            cutoff_date = timezone.now() - timedelta(days=days_old)
            old_sessions = ConversationSession.objects.filter(last_activity__lt=cutoff_date)
            count = old_sessions.count()
            old_sessions.delete()
            
            logger.info(f"Removidas {count} sessões antigas")
            return count
            
        except Exception as e:
            logger.error(f"Erro ao limpar sessões antigas: {e}")
            return 0


class RAGCacheService:
    """
    Serviço para cache de dados RAG
    """
    
    def get_clinic_data(self) -> Dict[str, Any]:
        """
        Obtém dados da clínica do cache ou banco
        """
        cache_key = "clinic_data"
        
        # Tentar cache primeiro
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        # Buscar do banco de dados RAG
        try:
            from .rag_service import RAGService
            clinic_data = RAGService.get_all_clinic_data()
            
            # Armazenar no cache
            cache.set(cache_key, clinic_data, self.RAG_CACHE_TIMEOUT)
            
            return clinic_data
            
        except Exception as e:
            logger.error(f"Erro ao obter dados da clínica: {e}")
            return {}
    
    def get_doctor_info(self, doctor_name: str) -> Dict[str, Any]:
        """
        Obtém informações de um médico específico
        """
        cache_key = f"doctor_{doctor_name.lower().replace(' ', '_')}"
        
        # Tentar cache primeiro
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        # Buscar do banco
        try:
            from .rag_service import RAGService
            doctor_data = RAGService.get_medico_by_name(doctor_name)
            
            if doctor_data:
                cache.set(cache_key, doctor_data, self.RAG_CACHE_TIMEOUT)
            
            return doctor_data or {}
            
        except Exception as e:
            logger.error(f"Erro ao obter dados do médico {doctor_name}: {e}")
            return {}
    
    def clear_cache(self, pattern: str = None):
        """
        Limpa cache RAG
        """
        try:
            if pattern:
                # Limpar cache específico
                cache.delete(pattern)
            else:
                # Limpar todo cache RAG
                cache.delete_many(cache.keys(f"{self.RAG_CACHE_PREFIX}*"))
            
            logger.info("Cache RAG limpo")
            
        except Exception as e:
            logger.error(f"Erro ao limpar cache RAG: {e}")


# Instância global do serviço
conversation_service = ConversationService()
