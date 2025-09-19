"""
Gerenciador de Contexto de Conversas
Mantém histórico e consciência contextual para melhor detecção de intenções
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)


class ConversationContext:
    """
    Classe para representar o contexto de uma conversa individual
    """
    
    def __init__(self, phone_number: str):
        self.phone_number = phone_number
        self.messages: List[Dict] = []
        self.last_intent: Optional[str] = None
        self.last_entities: Dict = {}
        self.pending_confirmation: Optional[Dict] = None
        self.conversation_state: str = "idle"  # idle, waiting_confirmation, collecting_info
        self.patient_info: Dict = {}  # Informações coletadas do paciente
        self.created_at = timezone.now()
        self.updated_at = timezone.now()
    
    def add_message(self, message: str, intent: str, entities: Dict, confidence: float, is_user: bool = True):
        """Adiciona uma mensagem ao histórico"""
        message_data = {
            'content': message,
            'intent': intent,
            'entities': entities,
            'confidence': confidence,
            'is_user': is_user,
            'timestamp': timezone.now().isoformat()
        }
        
        self.messages.append(message_data)
        
        # Manter apenas últimas 10 mensagens para performance
        if len(self.messages) > 10:
            self.messages = self.messages[-10:]
        
        if is_user:
            self.last_intent = intent
            self.last_entities = entities
            # Atualizar informações do paciente baseado nas entidades
            self._update_patient_info(entities)
        
        self.updated_at = timezone.now()
    
    def _update_patient_info(self, entities: Dict):
        """Atualiza informações do paciente baseado nas entidades extraídas"""
        if 'specialties' in entities and entities['specialties']:
            self.patient_info['specialty'] = entities['specialties'][0]
        
        if 'times' in entities and entities['times']:
            self.patient_info['preferred_time'] = entities['times'][0]
        
        if 'dates' in entities and entities['dates']:
            self.patient_info['preferred_date'] = entities['dates'][0]
        
        # Detectar convênios mencionados
        common_insurances = ['unimed', 'sulamerica', 'amil', 'bradesco', 'particular']
        for insurance in common_insurances:
            if insurance in str(entities).lower():
                self.patient_info['insurance'] = insurance.title()
                break
        
        # Detectar nome do paciente
        if 'patient_name' in entities and entities['patient_name']:
            # Usar o primeiro nome encontrado
            self.patient_info['patient_name'] = entities['patient_name'][0]
    
    def set_patient_info(self, key: str, value: str):
        """Define informação específica do paciente"""
        self.patient_info[key] = value
    
    def get_patient_info(self) -> Dict[str, str]:
        """Retorna informações coletadas do paciente"""
        return self.patient_info.copy()
    
    def get_last_user_message(self) -> Optional[Dict]:
        """Retorna a última mensagem do usuário"""
        for message in reversed(self.messages):
            if message['is_user']:
                return message
        return None
    
    def get_last_relevant_intent(self) -> Tuple[Optional[str], Dict]:
        """Retorna a última intenção relevante com confiança > 0.5"""
        for message in reversed(self.messages):
            if message['is_user'] and message['confidence'] > 0.5:
                return message['intent'], message['entities']
        return None, {}
    
    def set_pending_confirmation(self, confirmation_type: str, data: Dict):
        """Define uma confirmação pendente"""
        self.pending_confirmation = {
            'type': confirmation_type,
            'data': data,
            'created_at': timezone.now().isoformat()
        }
        self.conversation_state = "waiting_confirmation"
    
    def clear_pending_confirmation(self):
        """Limpa confirmação pendente"""
        self.pending_confirmation = None
        self.conversation_state = "idle"
    
    def to_dict(self) -> Dict:
        """Converte contexto para dicionário"""
        return {
            'phone_number': self.phone_number,
            'messages': self.messages,
            'last_intent': self.last_intent,
            'last_entities': self.last_entities,
            'pending_confirmation': self.pending_confirmation,
            'conversation_state': self.conversation_state,
            'patient_info': self.patient_info,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        """Cria contexto a partir de dicionário"""
        context = cls(data['phone_number'])
        context.messages = data.get('messages', [])
        context.last_intent = data.get('last_intent')
        context.last_entities = data.get('last_entities', {})
        context.pending_confirmation = data.get('pending_confirmation')
        context.conversation_state = data.get('conversation_state', 'idle')
        context.patient_info = data.get('patient_info', {})
        context.created_at = datetime.fromisoformat(data['created_at'])
        context.updated_at = datetime.fromisoformat(data['updated_at'])
        return context


class ContextManager:
    """
    Gerenciador de contextos de conversas com cache
    """
    
    CACHE_PREFIX = "conversation_context_"
    CACHE_TIMEOUT = 3600 * 24  # 24 horas
    
    # Respostas de confirmação
    POSITIVE_RESPONSES = [
        'sim', 'yes', 'ok', 'okay', 'certo', 'correto', 'confirmo', 'confirmar',
        'perfeito', 'exato', 'isso', 'isso mesmo', 'claro', 'com certeza',
        'pode ser', 'aceito', 'concordo', 'tá bom', 'beleza', 'fechado',
        '👍', '✅', 'positivo', 'afirmativo'
    ]
    
    NEGATIVE_RESPONSES = [
        'não', 'no', 'nao', 'negativo', 'não quero', 'não precisa',
        'cancelar', 'desistir', 'outro', 'diferente', 'errado',
        'não é isso', 'não era isso', 'mudei de ideia',
        '👎', '❌', 'não concordo'
    ]
    
    # Respostas que indicam continuação
    CONTINUATION_RESPONSES = [
        'e', 'também', 'mais', 'ainda', 'além disso', 'outra coisa',
        'gostaria também', 'preciso também', 'quero mais'
    ]
    
    def __init__(self):
        self.contexts: Dict[str, ConversationContext] = {}
    
    def get_context(self, phone_number: str) -> ConversationContext:
        """Obtém ou cria contexto para um número de telefone"""
        cache_key = f"{self.CACHE_PREFIX}{phone_number}"
        
        # Tentar buscar do cache primeiro
        cached_data = cache.get(cache_key)
        if cached_data:
            try:
                return ConversationContext.from_dict(cached_data)
            except Exception as e:
                logger.error(f"Erro ao restaurar contexto do cache: {e}")
        
        # Buscar da memória local
        if phone_number in self.contexts:
            return self.contexts[phone_number]
        
        # Criar novo contexto
        context = ConversationContext(phone_number)
        self.contexts[phone_number] = context
        self._save_context(context)
        
        return context
    
    def _save_context(self, context: ConversationContext):
        """Salva contexto no cache"""
        cache_key = f"{self.CACHE_PREFIX}{context.phone_number}"
        try:
            cache.set(cache_key, context.to_dict(), self.CACHE_TIMEOUT)
            self.contexts[context.phone_number] = context
        except Exception as e:
            logger.error(f"Erro ao salvar contexto no cache: {e}")
    
    def analyze_contextual_intent(self, phone_number: str, message: str) -> Tuple[str, float, Dict]:
        """
        Analisa intenção considerando contexto da conversa
        
        Returns:
            Tuple com (intent, confidence, entities)
        """
        context = self.get_context(phone_number)
        message_lower = message.lower().strip()
        
        # 1. Verificar se é resposta simples
        if self._is_simple_response(message_lower):
            return self._handle_simple_response(context, message_lower)
        
        # 2. Verificar se há confirmação pendente
        if context.pending_confirmation:
            return self._handle_pending_confirmation(context, message, message_lower)
        
        # 3. Verificar continuação de conversa
        if self._is_continuation_response(message_lower):
            return self._handle_continuation(context, message)
        
        # 4. Análise contextual baseada em mensagens anteriores
        return self._analyze_with_context(context, message, message_lower)
    
    def _is_simple_response(self, message: str) -> bool:
        """Verifica se é uma resposta simples (sim/não/ok)"""
        return (
            len(message) <= 20 and (
                message in self.POSITIVE_RESPONSES or
                message in self.NEGATIVE_RESPONSES or
                message in ['', ' ', '.', '!', '?']
            )
        )
    
    def _is_continuation_response(self, message: str) -> bool:
        """Verifica se é uma resposta de continuação"""
        return any(word in message for word in self.CONTINUATION_RESPONSES)
    
    def _handle_simple_response(self, context: ConversationContext, message: str) -> Tuple[str, float, Dict]:
        """Trata respostas simples baseado no contexto"""
        
        # Se há confirmação pendente, tratar como confirmação
        if context.pending_confirmation:
            if message in self.POSITIVE_RESPONSES:
                return self._confirm_pending_action(context)
            elif message in self.NEGATIVE_RESPONSES:
                return self._reject_pending_action(context)
        
        # Se não há confirmação pendente, usar última intenção relevante
        last_intent, last_entities = context.get_last_relevant_intent()
        
        if last_intent:
            if message in self.POSITIVE_RESPONSES:
                return f"confirmar_{last_intent}", 0.9, last_entities
            elif message in self.NEGATIVE_RESPONSES:
                return f"negar_{last_intent}", 0.9, last_entities
        
        # Fallback para resposta genérica
        return 'resposta_simples', 0.8, {'response_type': message}
    
    def _handle_pending_confirmation(self, context: ConversationContext, message: str, message_lower: str) -> Tuple[str, float, Dict]:
        """Trata confirmações pendentes"""
        confirmation = context.pending_confirmation
        confirmation_type = confirmation['type']
        
        if message_lower in self.POSITIVE_RESPONSES:
            context.clear_pending_confirmation()
            
            if confirmation_type == 'agendamento':
                return 'confirmar_agendamento', 0.95, confirmation['data']
            elif confirmation_type == 'cancelamento':
                return 'cancelar_agendamento', 0.95, confirmation['data']
            elif confirmation_type == 'informacao_medico':
                return 'buscar_medico', 0.9, confirmation['data']
        
        elif message_lower in self.NEGATIVE_RESPONSES:
            context.clear_pending_confirmation()
            return 'cancelar_acao', 0.9, {'cancelled_action': confirmation_type}
        
        # Se não é sim/não, analisar a mensagem normalmente
        return self._analyze_with_context(context, message, message_lower)
    
    def _handle_continuation(self, context: ConversationContext, message: str) -> Tuple[str, float, Dict]:
        """Trata continuação de conversa"""
        last_intent, last_entities = context.get_last_relevant_intent()
        
        if last_intent:
            # Manter mesmo contexto mas analisar nova mensagem
            return last_intent, 0.7, {**last_entities, 'continuation': True, 'additional_info': message}
        
        return 'desconhecida', 0.3, {'continuation': True}
    
    def _analyze_with_context(self, context: ConversationContext, message: str, message_lower: str) -> Tuple[str, float, Dict]:
        """Analisa intenção considerando contexto completo"""
        
        # Buscar palavras-chave na mensagem atual
        from .intent_detection_service import IntentDetectionService
        intent_service = IntentDetectionService()
        current_intent, current_confidence = intent_service.detect_intent(message)
        current_entities = intent_service.extract_entities(message)
        
        # Se confiança é alta, usar intenção atual
        if current_confidence >= 0.8:
            return current_intent, current_confidence, current_entities
        
        # Se confiança é baixa, considerar contexto
        if current_confidence < 0.5:
            last_intent, last_entities = context.get_last_relevant_intent()
            
            if last_intent and self._is_related_to_last_intent(message_lower, last_intent):
                # Combinar contexto anterior com nova informação
                combined_entities = {**last_entities, **current_entities}
                return last_intent, 0.7, combined_entities
        
        return current_intent, current_confidence, current_entities
    
    def _is_related_to_last_intent(self, message: str, last_intent: str) -> bool:
        """Verifica se mensagem atual está relacionada à última intenção"""
        
        related_keywords = {
            'buscar_medico': ['doutor', 'médico', 'consulta', 'especialista'],
            'agendar_consulta': ['horário', 'data', 'quando', 'disponível', 'agenda'],
            'buscar_especialidade': ['especialidade', 'área', 'tipo'],
            'buscar_exame': ['exame', 'teste', 'resultado'],
            'buscar_info_clinica': ['endereço', 'telefone', 'localização', 'horário']
        }
        
        keywords = related_keywords.get(last_intent, [])
        return any(keyword in message for keyword in keywords)
    
    def _confirm_pending_action(self, context: ConversationContext) -> Tuple[str, float, Dict]:
        """Confirma ação pendente"""
        confirmation = context.pending_confirmation
        context.clear_pending_confirmation()
        
        return f"confirmar_{confirmation['type']}", 0.95, confirmation['data']
    
    def _reject_pending_action(self, context: ConversationContext) -> Tuple[str, float, Dict]:
        """Rejeita ação pendente"""
        confirmation = context.pending_confirmation
        context.clear_pending_confirmation()
        
        return 'cancelar_acao', 0.9, {'rejected_action': confirmation['type']}
    
    def _continue_intent(self, intent: str, entities: Dict, positive: bool) -> Tuple[str, float, Dict]:
        """Continua intenção anterior com confirmação positiva/negativa"""
        
        if positive:
            return f"confirmar_{intent}", 0.9, entities
        else:
            return f"negar_{intent}", 0.9, entities
    
    def add_message_to_context(self, phone_number: str, message: str, intent: str, entities: Dict, confidence: float, is_user: bool = True):
        """Adiciona mensagem ao contexto"""
        context = self.get_context(phone_number)
        context.add_message(message, intent, entities, confidence, is_user)
        self._save_context(context)
    
    def set_pending_confirmation(self, phone_number: str, confirmation_type: str, data: Dict):
        """Define confirmação pendente para um usuário"""
        context = self.get_context(phone_number)
        context.set_pending_confirmation(confirmation_type, data)
        self._save_context(context)
    
    def get_conversation_history(self, phone_number: str, limit: int = 5) -> List[Dict]:
        """Obtém histórico de conversa"""
        context = self.get_context(phone_number)
        return context.messages[-limit:] if context.messages else []
    
    def clear_context(self, phone_number: str):
        """Limpa contexto de um usuário"""
        cache_key = f"{self.CACHE_PREFIX}{phone_number}"
        cache.delete(cache_key)
        if phone_number in self.contexts:
            del self.contexts[phone_number]
    
    def cleanup_old_contexts(self, hours_old: int = 24):
        """Remove contextos antigos para liberar memória"""
        cutoff_time = timezone.now() - timedelta(hours=hours_old)
        
        to_remove = []
        for phone_number, context in self.contexts.items():
            if context.updated_at < cutoff_time:
                to_remove.append(phone_number)
        
        for phone_number in to_remove:
            self.clear_context(phone_number)
        
        logger.info(f"Removidos {len(to_remove)} contextos antigos")
    
    def prepare_handoff_data(self, phone_number: str, doctor_name: str, date: str, time: str) -> Dict[str, str]:
        """
        Prepara dados para handoff baseado no contexto da conversa
        
        Args:
            phone_number: Número do telefone do usuário
            doctor_name: Nome do médico selecionado
            date: Data escolhida
            time: Horário escolhido
            
        Returns:
            Dicionário com dados formatados para handoff
        """
        context = self.get_context(phone_number)
        
        # Extrair informações do paciente do histórico
        from .handoff_service import handoff_service
        patient_info = handoff_service.extract_patient_info_from_context(
            context.messages, context.last_entities
        )
        
        # Combinar com informações já coletadas
        combined_info = {**context.patient_info, **patient_info}
        
        # Determinar especialidade baseada no médico ou contexto
        specialty = self._determine_specialty(doctor_name, combined_info)
        
        # Preparar dados finais
        handoff_data = {
            'patient_name': combined_info.get('patient_name', 'Paciente'),
            'doctor_name': doctor_name,
            'specialty': specialty,
            'appointment_type': combined_info.get('appointment_type', 'Consulta'),
            'date': date,
            'time': time,
            'phone_number': phone_number,
            'insurance': combined_info.get('insurance', 'Não informado')
        }
        
        return handoff_data
    
    def _determine_specialty(self, doctor_name: str, patient_info: Dict) -> str:
        """Determina especialidade baseada no médico ou contexto usando dados do banco"""
        
        # Primeiro, tentar obter do contexto
        if 'specialty' in patient_info:
            return patient_info['specialty']
        
        # Buscar especialidade do médico no banco de dados via RAGService
        try:
            from .rag_service import RAGService

            # Usar método específico do RAGService para obter especialidade
            specialty = RAGService.get_doctor_specialty(doctor_name)
            
            if specialty and specialty != 'Consulta Geral':
                logger.info(f"Especialidade encontrada para {doctor_name}: {specialty}")
                return specialty
            
            logger.warning(f"Especialidade não encontrada para {doctor_name}, usando padrão")
            
        except Exception as e:
            logger.error(f"Erro ao buscar especialidade do médico no banco: {e}")
        
        return 'Consulta Geral'
    
    def set_pending_handoff(self, phone_number: str, handoff_data: Dict):
        """Define handoff pendente para confirmação"""
        self.set_pending_confirmation(phone_number, 'handoff', handoff_data)


# Instância global do gerenciador de contexto
context_manager = ContextManager()
