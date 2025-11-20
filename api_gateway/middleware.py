"""
Middleware customizado para API Gateway
"""
import json
import logging
from datetime import datetime

from django.urls import resolve
from django.utils.deprecation import MiddlewareMixin
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)


class JSONFormatter(logging.Formatter):
    """
    Formatador customizado para JSON mais legível
    """

    def format(self, record):
        if hasattr(record, 'json_data') and record.json_data:
            # Formatar JSON de forma mais limpa
            try:
                formatted_json = json.dumps(record.json_data, indent=2, ensure_ascii=False)
                record.json_data = formatted_json
            except:
                pass
        return super().format(record)


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
            #logger.info(f"📡 API Request: {request.method} {request.path}")

            # Log mais detalhado para webhooks
            if request.path.startswith('/api/webhook/') and request.body:
                try:
                    body_data = json.loads(request.body.decode('utf-8'))
                    #logger.info(f"📱 WhatsApp Webhook - {len(body_data.get('entry', []))} entries")

                    # Log resumido das mensagens
                    for entry in body_data.get('entry', []):
                        for change in entry.get('changes', []):
                            if change.get('field') == 'messages':
                                messages = change.get('value', {}).get('messages', [])
                                for msg in messages:
                                    msg_type = msg.get('type', 'unknown')
                                    from_number = msg.get('from', 'unknown')
                                    #logger.info(f"💬 Mensagem recebida: {msg_type} de {from_number}")

                except Exception as e:
                    logger.debug(f"Erro ao parsear webhook: {e}")

        return None

    def process_response(self, request, response):
        """
        Log de responses enviados
        """
        if request.path.startswith('/api/'):
            logger.info(f"📤 API Response: {request.method} {request.path} -> {response.status_code}")

        return response
