"""
Sistema de Memória para Conversas
Gerenciamento inteligente de memória usando LangChain
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from django.core.cache import cache
from django.utils import timezone
from langchain.memory import (ConversationBufferWindowMemory,
                              ConversationSummaryMemory)
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import (AIMessage, BaseMessage, HumanMessage,
                                     SystemMessage)

from ..config import MEMORY_CONFIG

logger = logging.getLogger(__name__)


class DjangoChatMessageHistory(BaseChatMessageHistory):
    """
    Implementação de histórico de mensagens usando Django
    """
    
    def __init__(self, phone_number: str):
        self.phone_number = phone_number
        self.cache_key = f"chat_history_{phone_number}"
    
    @property
    def messages(self) -> List[BaseMessage]:
        """Retorna mensagens do histórico"""
        try:
            cached_messages = cache.get(self.cache_key, [])
            return self._deserialize_messages(cached_messages)
        except Exception as e:
            logger.error(f"Erro ao obter mensagens do histórico: {e}")
            return []
    
    def add_message(self, message: BaseMessage) -> None:
        """Adiciona mensagem ao histórico"""
        try:
            messages = self.messages
            messages.append(message)
            
            # Limitar tamanho do histórico
            max_messages = MEMORY_CONFIG['WINDOW_SIZE'] * 2  # *2 para incluir user e assistant
            if len(messages) > max_messages:
                messages = messages[-max_messages:]
            
            # Salvar no cache
            serialized_messages = self._serialize_messages(messages)
            cache.set(self.cache_key, serialized_messages, 3600)  # 1 hora
            
        except Exception as e:
            logger.error(f"Erro ao adicionar mensagem ao histórico: {e}")
    
    def clear(self) -> None:
        """Limpa o histórico"""
        try:
            cache.delete(self.cache_key)
        except Exception as e:
            logger.error(f"Erro ao limpar histórico: {e}")
    
    def _serialize_messages(self, messages: List[BaseMessage]) -> List[Dict]:
        """Serializa mensagens para cache"""
        serialized = []
        for msg in messages:
            serialized.append({
                'type': msg.__class__.__name__,
                'content': msg.content,
                'timestamp': timezone.now().isoformat()
            })
        return serialized
    
    def _deserialize_messages(self, serialized_messages: List[Dict]) -> List[BaseMessage]:
        """Deserializa mensagens do cache"""
        messages = []
        for msg_data in serialized_messages:
            msg_type = msg_data.get('type', 'HumanMessage')
            content = msg_data.get('content', '')
            
            if msg_type == 'HumanMessage':
                messages.append(HumanMessage(content=content))
            elif msg_type == 'AIMessage':
                messages.append(AIMessage(content=content))
            elif msg_type == 'SystemMessage':
                messages.append(SystemMessage(content=content))
        
        return messages


class ConversationMemoryManager:
    """
    Gerenciador de memória para conversas
    
    Responsabilidades:
    1. Gerenciar memória de conversas
    2. Implementar diferentes tipos de memória
    3. Sincronizar com banco de dados
    4. Otimizar performance
    """
    
    def __init__(self):
        self.memories = {}  # Cache de memórias por phone_number
    
    def get_memory(self, phone_number: str, memory_type: str = 'window') -> BaseChatMessageHistory:
        """
        Obtém memória para uma conversa
        
        Args:
            phone_number: Número do telefone
            memory_type: Tipo de memória ('window', 'summary')
            
        Returns:
            Memória da conversa
        """
        try:
            cache_key = f"memory_{phone_number}_{memory_type}"
            
            if cache_key not in self.memories:
                if memory_type == 'window':
                    memory = ConversationBufferWindowMemory(
                        k=MEMORY_CONFIG['WINDOW_SIZE'],
                        chat_memory=DjangoChatMessageHistory(phone_number),
                        return_messages=True
                    )
                elif memory_type == 'summary':
                    # Para summary, precisaríamos de um LLM
                    # Por enquanto, usar window memory
                    memory = ConversationBufferWindowMemory(
                        k=MEMORY_CONFIG['WINDOW_SIZE'],
                        chat_memory=DjangoChatMessageHistory(phone_number),
                        return_messages=True
                    )
                else:
                    raise ValueError(f"Tipo de memória inválido: {memory_type}")
                
                self.memories[cache_key] = memory
            
            return self.memories[cache_key]
            
        except Exception as e:
            logger.error(f"Erro ao obter memória para {phone_number}: {e}")
            # Retornar memória vazia em caso de erro
            return ConversationBufferWindowMemory(
                k=MEMORY_CONFIG['WINDOW_SIZE'],
                return_messages=True
            )
    
    def add_user_message(self, phone_number: str, message: str) -> None:
        """
        Adiciona mensagem do usuário à memória
        
        Args:
            phone_number: Número do telefone
            message: Mensagem do usuário
        """
        try:
            memory = self.get_memory(phone_number)
            memory.chat_memory.add_user_message(message)
            logger.info(f"💬 Mensagem do usuário adicionada à memória: {phone_number}")
            
        except Exception as e:
            logger.error(f"Erro ao adicionar mensagem do usuário: {e}")
    
    def add_ai_message(self, phone_number: str, message: str) -> None:
        """
        Adiciona mensagem da IA à memória
        
        Args:
            phone_number: Número do telefone
            message: Mensagem da IA
        """
        try:
            memory = self.get_memory(phone_number)
            memory.chat_memory.add_ai_message(message)
            logger.info(f"🤖 Mensagem da IA adicionada à memória: {phone_number}")
            
        except Exception as e:
            logger.error(f"Erro ao adicionar mensagem da IA: {e}")
    
    def get_conversation_history(self, phone_number: str, limit: int = None) -> List[Dict[str, Any]]:
        """
        Obtém histórico da conversa
        
        Args:
            phone_number: Número do telefone
            limit: Limite de mensagens (opcional)
            
        Returns:
            Lista de mensagens do histórico
        """
        try:
            memory = self.get_memory(phone_number)
            messages = memory.chat_memory.messages
            
            # Converter para formato esperado pelo sistema
            history = []
            for msg in messages:
                if isinstance(msg, HumanMessage):
                    history.append({
                        'is_user': True,
                        'content': msg.content,
                        'type': 'user'
                    })
                elif isinstance(msg, AIMessage):
                    history.append({
                        'is_user': False,
                        'content': msg.content,
                        'type': 'bot'
                    })
            
            # Aplicar limite se especificado
            if limit:
                history = history[-limit:]
            
            return history
            
        except Exception as e:
            logger.error(f"Erro ao obter histórico da conversa: {e}")
            return []
    
    def clear_memory(self, phone_number: str) -> None:
        """
        Limpa memória de uma conversa
        
        Args:
            phone_number: Número do telefone
        """
        try:
            # Limpar cache de memórias
            for cache_key in list(self.memories.keys()):
                if phone_number in cache_key:
                    del self.memories[cache_key]
            
            # Limpar histórico no banco/cache
            memory = self.get_memory(phone_number)
            memory.chat_memory.clear()
            
            logger.info(f"🧹 Memória limpa para: {phone_number}")
            
        except Exception as e:
            logger.error(f"Erro ao limpar memória: {e}")
    
    def get_memory_stats(self, phone_number: str) -> Dict[str, Any]:
        """
        Obtém estatísticas da memória
        
        Args:
            phone_number: Número do telefone
            
        Returns:
            Estatísticas da memória
        """
        try:
            memory = self.get_memory(phone_number)
            messages = memory.chat_memory.messages
            
            user_messages = [msg for msg in messages if isinstance(msg, HumanMessage)]
            ai_messages = [msg for msg in messages if isinstance(msg, AIMessage)]
            
            return {
                'total_messages': len(messages),
                'user_messages': len(user_messages),
                'ai_messages': len(ai_messages),
                'memory_type': 'window',
                'window_size': MEMORY_CONFIG['WINDOW_SIZE']
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas da memória: {e}")
            return {'error': str(e)}
    
    def sync_with_database(self, phone_number: str) -> None:
        """
        Sincroniza memória com banco de dados
        
        Args:
            phone_number: Número do telefone
        """
        try:
            from api_gateway.services.conversation_service import \
                conversation_service

            # Obter histórico da memória
            memory_history = self.get_conversation_history(phone_number)
            
            # Sincronizar com conversation_service
            for msg in memory_history:
                if msg['is_user']:
                    conversation_service.add_message(
                        phone_number=phone_number,
                        content=msg['content'],
                        message_type='user',
                        intent='user_message',
                        confidence=1.0,
                        entities={}
                    )
                else:
                    conversation_service.add_message(
                        phone_number=phone_number,
                        content=msg['content'],
                        message_type='bot',
                        intent='bot_response',
                        confidence=1.0,
                        entities={}
                    )
            
            logger.info(f"🔄 Memória sincronizada com banco: {phone_number}")
            
        except Exception as e:
            logger.error(f"Erro ao sincronizar memória com banco: {e}")


# Instância global do gerenciador de memória
memory_manager = ConversationMemoryManager()
