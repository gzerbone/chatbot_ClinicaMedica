"""
Serviço para integração com WhatsApp Business API
"""
import json
import logging
from typing import Any, Dict, Optional

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class WhatsAppService:
    """
    Serviço para integração com WhatsApp Business API
    """
    
    def __init__(self):
        self.access_token = getattr(settings, 'WHATSAPP_ACCESS_TOKEN', '')
        self.phone_number_id = getattr(settings, 'WHATSAPP_PHONE_NUMBER_ID', '')
        self.api_url = getattr(settings, 'WHATSAPP_API_URL', 'https://graph.facebook.com/v18.0')
        
        # Log de aviso se as configurações estão vazias (mas não falha para permitir testes)
        if not self.access_token:
            logger.warning("WHATSAPP_ACCESS_TOKEN não configurado")
        if not self.phone_number_id:
            logger.warning("WHATSAPP_PHONE_NUMBER_ID não configurado")
    
    def send_message(self, to: str, message: str) -> bool:
        """
        Envia uma mensagem de texto via WhatsApp API
        
        Args:
            to: Número do destinatário (formato: 5511999999999)
            message: Mensagem a ser enviada
            
        Returns:
            True se a mensagem foi enviada com sucesso
        """
        try:
            url = f"{self.api_url}/{self.phone_number_id}/messages"
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "text",
                "text": {
                    "body": message
                }
            }
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                logger.info(f"📱 Mensagem enviada para {to}")
                return True
            else:
                logger.error(f"❌ Erro ao enviar mensagem: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao enviar mensagem via WhatsApp: {e}")
            return False
    
    def send_template_message(self, to: str, template_name: str, parameters: list = None) -> bool:
        """
        Envia uma mensagem de template via WhatsApp API
        
        Args:
            to: Número do destinatário
            template_name: Nome do template aprovado
            parameters: Parâmetros do template
            
        Returns:
            True se a mensagem foi enviada com sucesso
        """
        try:
            url = f"{self.api_url}/{self.phone_number_id}/messages"
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {
                        "code": "pt_BR"
                    }
                }
            }
            
            if parameters:
                data["template"]["components"] = [
                    {
                        "type": "body",
                        "parameters": [{"type": "text", "text": param} for param in parameters]
                    }
                ]
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                logger.info(f"Template enviado com sucesso para {to}")
                return True
            else:
                logger.error(f"Erro ao enviar template: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao enviar template via WhatsApp: {e}")
            return False
    
    def mark_message_as_read(self, message_id: str) -> bool:
        """
        Marca uma mensagem como lida
        
        Args:
            message_id: ID da mensagem a ser marcada como lida
            
        Returns:
            True se marcada com sucesso
        """
        try:
            url = f"{self.api_url}/{self.phone_number_id}/messages"
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                "messaging_product": "whatsapp",
                "status": "read",
                "message_id": message_id
            }
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                logger.info(f"Mensagem {message_id} marcada como lida")
                return True
            else:
                logger.error(f"Erro ao marcar mensagem como lida: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao marcar mensagem como lida: {e}")
            return False
    
    def get_profile_info(self, phone_number: str) -> Optional[Dict]:
        """
        Obtém informações do perfil do usuário
        
        Args:
            phone_number: Número de telefone do usuário
            
        Returns:
            Dicionário com informações do perfil ou None se erro
        """
        try:
            url = f"{self.api_url}/{phone_number}"
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            params = {
                'fields': 'profile'
            }
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Erro ao obter perfil: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao obter perfil do usuário: {e}")
            return None
    
    def validate_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """
        Valida o webhook do WhatsApp
        
        Args:
            mode: Modo de verificação
            token: Token de verificação
            challenge: Challenge string
            
        Returns:
            Challenge string se válido, None caso contrário
        """
        verify_token = getattr(settings, 'WHATSAPP_VERIFY_TOKEN', '')
        
        if mode == 'subscribe' and token == verify_token:
            logger.info("Webhook do WhatsApp verificado com sucesso")
            return challenge
        else:
            logger.warning("Falha na verificação do webhook do WhatsApp")
            return None
