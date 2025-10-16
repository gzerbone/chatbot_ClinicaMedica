"""
Módulo Gemini - Serviço de Chatbot Modularizado

Este módulo contém os componentes especializados do chatbot:
- IntentDetector: Detecção de intenções
- EntityExtractor: Extração de entidades
- ResponseGenerator: Geração de respostas
- SessionManager: Gerenciamento de sessões
- GeminiChatbotService: Orquestrador principal
"""

from .core_service import GeminiChatbotService
from .entity_extractor import EntityExtractor
from .intent_detector import IntentDetector
from .response_generator import ResponseGenerator
from .session_manager import SessionManager

__all__ = [
    'GeminiChatbotService',
    'IntentDetector',
    'EntityExtractor',
    'ResponseGenerator',
    'SessionManager',
]

