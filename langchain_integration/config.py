"""
Configurações para integração LangChain
"""
import os

from django.conf import settings

# Configurações do LangChain
LANGCHAIN_CONFIG = {
    'GEMINI_MODEL': getattr(settings, 'GEMINI_MODEL', 'gemini-2.0-flash'),
    'GEMINI_API_KEY': getattr(settings, 'GEMINI_API_KEY', ''),
    'EMBEDDING_MODEL': 'models/embedding-001',
    'VECTOR_STORE_PATH': os.path.join(settings.BASE_DIR, 'langchain_integration', 'vectorstore'),
    'CACHE_TTL': 3600,  # 1 hora
    'MAX_TOKENS': 1024,
    'TEMPERATURE': 0.7,
    'TOP_P': 0.8,
    'TOP_K': 40,
}

# Configurações de RAG
RAG_CONFIG = {
    'CHUNK_SIZE': 1000,
    'CHUNK_OVERLAP': 200,
    'K_RETRIEVAL': 3,
    'SIMILARITY_THRESHOLD': 0.7,
}

# Configurações de Memória
MEMORY_CONFIG = {
    'WINDOW_SIZE': 5,  # Últimas 5 mensagens
    'SUMMARY_LENGTH': 500,
    'MAX_TOKEN_LIMIT': 2000,
}
