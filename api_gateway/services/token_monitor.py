"""
Sistema de Monitoramento de Tokens Gemini
Gerencia o uso de tokens para controle de custos e limites
"""
import logging
from datetime import date
from typing import Any, Dict, Optional

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class TokenMonitor:
    """
    Monitor de tokens para controle de uso e custos do Gemini
    """
    
    def __init__(self):
        self.enabled = getattr(settings, 'GEMINI_TOKEN_MONITORING', True)
        self.daily_token_limit = getattr(settings, 'GEMINI_DAILY_TOKEN_LIMIT', 1500000)  # 1.5M tokens
        self.token_usage_today = 0
        self.session_token_usage = {}
        self.economy_mode = False
        
        if self.enabled:
            self._initialize_token_monitoring()
    
    def _initialize_token_monitoring(self):
        """
        Inicializa o sistema de monitoramento de tokens
        """
        try:
            # Verificar se é um novo dia
            today = date.today().isoformat()
            cache_key = f"gemini_tokens_{today}"
            
            # Recuperar uso de tokens do dia
            self.token_usage_today = cache.get(cache_key, 0)
            
            # Log do status atual
            usage_percentage = (self.token_usage_today / self.daily_token_limit) * 100
            logger.info(f"📊 Tokens hoje: {self.token_usage_today:,} / {self.daily_token_limit:,} ({usage_percentage:.1f}%)")
            
            # Alertas baseados no uso
            if usage_percentage >= 95:
                logger.critical(f"🚨 CRÍTICO: Uso de tokens em {usage_percentage:.1f}% do limite diário!")
                self._activate_economy_mode()
            elif usage_percentage >= 90:
                logger.error(f"⚠️ ALERTA: Uso de tokens em {usage_percentage:.1f}% do limite diário")
            elif usage_percentage >= 80:
                logger.warning(f"⚠️ AVISO: Uso de tokens em {usage_percentage:.1f}% do limite diário")
                
        except Exception as e:
            logger.error(f"Erro ao inicializar monitoramento de tokens: {e}")
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estima o número de tokens em um texto
        Aproximação: 1 token ≈ 4 caracteres para português
        """
        if not text:
            return 0
        
        # Contar caracteres e dividir por 4 (aproximação)
        char_count = len(text)
        estimated_tokens = char_count // 4
        
        # Ajuste para português (caracteres acentuados contam mais)
        accent_chars = sum(1 for char in text if char in 'áàâãéèêíìîóòôõúùûçÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇ')
        estimated_tokens += accent_chars // 2
        
        return max(estimated_tokens, 1)  # Mínimo 1 token
    
    def log_token_usage(self, operation: str, input_text: str, output_text: str = "", phone_number: str = None) -> int:
        """
        Registra o uso de tokens para monitoramento
        """
        try:
            if not self.enabled:
                return 0
            
            # Calcular tokens
            input_tokens = self.estimate_tokens(input_text)
            output_tokens = self.estimate_tokens(output_text)
            total_tokens = input_tokens + output_tokens
            
            # Atualizar contadores
            self.token_usage_today += total_tokens
            if phone_number:
                if phone_number not in self.session_token_usage:
                    self.session_token_usage[phone_number] = 0
                self.session_token_usage[phone_number] += total_tokens
            
            # Salvar no cache
            today = date.today().isoformat()
            cache_key = f"gemini_tokens_{today}"
            cache.set(cache_key, self.token_usage_today, 86400)  # 24 horas
            
            # Log detalhado
            logger.info(f"📊 TOKENS - {operation}: Input={input_tokens:,}, Output={output_tokens:,}, Total={total_tokens:,}")
            
            # Log da sessão se especificada
            if phone_number:
                session_total = self.session_token_usage[phone_number]
                logger.info(f"📊 SESSÃO {phone_number}: Total={total_tokens:,}, Acumulado={session_total:,}")
            
            # Log do dia
            usage_percentage = (self.token_usage_today / self.daily_token_limit) * 100
            logger.info(f"📊 DIA: Total={self.token_usage_today:,}, Limite={self.daily_token_limit:,}, Uso={usage_percentage:.1f}%")
            
            # Alertas baseados no uso
            if usage_percentage >= 95:
                logger.critical(f"🚨 CRÍTICO: Uso de tokens em {usage_percentage:.1f}% do limite diário!")
                self._activate_economy_mode()
            elif usage_percentage >= 90:
                logger.error(f"⚠️ ALERTA: Uso de tokens em {usage_percentage:.1f}% do limite diário")
            elif usage_percentage >= 80:
                logger.warning(f"⚠️ AVISO: Uso de tokens em {usage_percentage:.1f}% do limite diário")
            
            # Aviso se o prompt estiver muito grande
            if input_tokens > 2000:
                logger.warning(f"⚠️ Prompt grande: {input_tokens:,} tokens (operação: {operation})")
            
            return total_tokens
            
        except Exception as e:
            logger.error(f"Erro ao registrar uso de tokens: {e}")
            return 0
    
    def _activate_economy_mode(self):
        """
        Ativa modo econômico quando o limite de tokens está próximo
        """
        try:
            if self.economy_mode:
                return  # Já está ativo
                
            logger.warning("🔄 Ativando modo econômico para preservar tokens")
            self.economy_mode = True
            logger.info("✅ Modo econômico ativado - tokens preservados")
            
        except Exception as e:
            logger.error(f"Erro ao ativar modo econômico: {e}")
    
    def get_token_usage_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas de uso de tokens
        """
        try:
            usage_percentage = (self.token_usage_today / self.daily_token_limit) * 100
            
            return {
                'tokens_used_today': self.token_usage_today,
                'daily_limit': self.daily_token_limit,
                'usage_percentage': usage_percentage,
                'tokens_remaining': self.daily_token_limit - self.token_usage_today,
                'session_usage': self.session_token_usage,
                'economy_mode': self.economy_mode,
                'enabled': self.enabled
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas de tokens: {e}")
            return {}
    
    def is_economy_mode_active(self) -> bool:
        """Verifica se o modo econômico está ativo"""
        return self.economy_mode
    
    def get_economy_config(self) -> Dict[str, Any]:
        """Retorna configurações de modo econômico"""
        if self.economy_mode:
            return {
                "temperature": 0.5,
                "max_output_tokens": 512
            }
        return {}
    
    def get_cache_timeout(self) -> int:
        """Retorna timeout do cache (em segundos)"""
        return 3600  # 1 hora


# Criar instância global usando lazy initialization
_token_monitor_instance = None

def get_token_monitor():
    """Retorna a instância do TokenMonitor (lazy loading)"""
    global _token_monitor_instance
    if _token_monitor_instance is None:
        _token_monitor_instance = TokenMonitor()
    return _token_monitor_instance

# Para compatibilidade, criar instância somente quando Django estiver configurado
try:
    token_monitor = TokenMonitor()
except Exception:
    # Fallback para lazy loading
    token_monitor = type('TokenMonitor', (), {
        '__getattr__': lambda self, name: getattr(get_token_monitor(), name)
    })()