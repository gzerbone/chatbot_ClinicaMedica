"""
Middleware customizado para API Gateway
"""
import logging

from django.urls import resolve
from django.utils.deprecation import MiddlewareMixin
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)


class WhatsAppWebhookCSRFExemptMiddleware(MiddlewareMixin):
    """
    Middleware para isentar o webhook do WhatsApp da verificação CSRF
    """
    
    def process_request(self, request):
        """
        Processa a requisição antes de chegar à view
        """
        # Verificar se é o endpoint do webhook do WhatsApp
        if request.path.startswith('/api/webhook/whatsapp/'):
            # Marcar como isento de CSRF
            setattr(request, '_dont_enforce_csrf_checks', True)
            logger.debug("CSRF check disabled for WhatsApp webhook")
        
        return None


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware para log de requests (apenas para desenvolvimento)
    """
    
    def process_request(self, request):
        """
        Log de requests recebidos
        """
        if request.path.startswith('/api/'):
            logger.info(f"API Request: {request.method} {request.path}")
            
            # Log do body para webhooks (apenas primeiros 200 caracteres)
            if request.path.startswith('/api/webhook/') and request.body:
                body_preview = request.body.decode('utf-8', errors='ignore')[:200]
                logger.debug(f"Request body preview: {body_preview}...")
        
        return None
    
    def process_response(self, request, response):
        """
        Log de responses enviados
        """
        if request.path.startswith('/api/'):
            logger.info(f"API Response: {request.method} {request.path} -> {response.status_code}")
        
        return response
