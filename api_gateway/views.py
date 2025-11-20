"""
Views para API Gateway - Integração com WhatsApp
"""
import json
import logging
from typing import Dict, List

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .services.conversation_service import (conversation_logger,
                                            conversation_service)
from .services.gemini import GeminiChatbotService
from .services.whatsapp_service import WhatsAppService

# Instância global do serviço Gemini (versão modular)
gemini_chatbot_service = GeminiChatbotService()

logger = logging.getLogger(__name__)

# Inicializar serviços
whatsapp_service = WhatsAppService()
# Obter dados da clínica através do RAGService
def get_clinic_data():
    """Obtém dados atualizados da clínica"""
    from .services.rag_service import RAGService
    return RAGService.get_all_clinic_data()

@csrf_exempt
@require_http_methods(["GET", "POST"])
def whatsapp_webhook(request):
    """
    Webhook para receber mensagens do WhatsApp
    """
    if request.method == 'GET':
        return verify_webhook(request)
    elif request.method == 'POST':
        return handle_webhook(request)


def verify_webhook(request):
    """
    Verifica o webhook do WhatsApp (GET)
    """
    try:
        mode = request.GET.get('hub.mode')
        token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')
        
        result = whatsapp_service.validate_webhook(mode, token, challenge)
        
        if result:
            return HttpResponse(result, content_type='text/plain')
        else:
            return HttpResponse('Verification failed', status=403)
            
    except Exception as e:
        logger.error(f"Erro na verificação do webhook: {e}")
        return HttpResponse('Error', status=500)


def handle_webhook(request):
    """
    Processa mensagens recebidas do WhatsApp (POST)
    """
    try:
        body = json.loads(request.body.decode('utf-8'))

        # Verificar se é uma mensagem válida
        if 'entry' not in body:
            return JsonResponse({'status': 'ok'})

        total_messages = 0
        for entry in body['entry']:
            if 'changes' not in entry:
                continue

            for change in entry['changes']:
                if change.get('field') == 'messages':
                    messages = change.get('value', {}).get('messages', [])
                    total_messages += len(messages)

                    for message in messages:
                        process_message(message, change['value'])

        return JsonResponse({'status': 'ok'})

    except Exception as e:
        logger.error(f"❌ Erro ao processar webhook: {e}")
        return JsonResponse({'status': 'error'}, status=500)


def process_message(message, webhook_data):
    """
    Processa uma mensagem individual
    """
    try:
        # Extrair informações da mensagem
        message_id = message.get('id')
        from_number = message.get('from')
        message_type = message.get('type')
        timestamp = message.get('timestamp')

        logger.info(f"🔄 Processando mensagem {message_id} de {from_number}")

        # Verificar se é mensagem de texto válida
        if message_type == 'text':
            text_content = message.get('text', {}).get('body', '')

            # Validar se o conteúdo de texto não está vazio e tem tamanho mínimo
            if text_content and len(text_content.strip()) > 0:
                logger.info(f"👤 USUÁRIO ({from_number}): {text_content}")

                # NOVO: Usar Gemini Chatbot Service como protagonista principal
                try:
                    # Processar mensagem com Gemini centralizado
                    result = gemini_chatbot_service.process_message(from_number, text_content)

                    response_text = result.get('response', 'Como posso ajudá-lo?')
                    intent = result.get('intent', 'unknown')
                    confidence = result.get('confidence', 0.0)
                    state = result.get('state', 'unknown')
                    agent = result.get('agent', 'gemini')

                    logger.info(f"🤖 [{intent.upper()}] State: {state} | Conf: {confidence:.2f} | Agent: {agent}")

                    # Enviar resposta
                    success = whatsapp_service.send_message(from_number, response_text)

                    if success:
                        # Log limpo da conversação
                        conversation_logger.info(f"💬 {from_number} → {text_content}")
                        conversation_logger.info(f"🤖 GEMINI → {response_text}")
                    else:
                        logger.error(f"❌ Falha ao enviar resposta para {from_number}")

                except Exception as e:
                    logger.error(f"❌ Erro no Gemini Chatbot Service: {e}")
                    
                    # Fallback simples
                    response_text = "Desculpe, estou temporariamente indisponível. Como posso ajudá-lo?"
                    success = whatsapp_service.send_message(from_number, response_text)
                    
                    if not success:
                        logger.error(f"❌ Falha ao enviar resposta fallback para {from_number}")

            else:
                # Mensagem de texto vazia ou inválida
                response_text = "❌ Desculpe, não consegui processar sua mensagem. Por favor, envie uma mensagem de texto válida."
                whatsapp_service.send_message(from_number, response_text)

        else:
            # Rejeitar todos os outros tipos de mensagem (imagem, áudio, vídeo, documento, etc.)
            logger.warning(f"❌ Tipo de mensagem não suportado: {message_type} de {from_number}")
            
            # Mensagem de erro personalizada baseada no tipo
            error_messages = {
                'image': "📷 Desculpe, não consigo processar imagens. Por favor, envie sua mensagem como texto.",
                'audio': "🎵 Desculpe, não consigo processar áudios. Por favor, envie sua mensagem como texto.",
                'video': "🎬 Desculpe, não consigo processar vídeos. Por favor, envie sua mensagem como texto.",
                'document': "📄 Desculpe, não consigo processar documentos. Por favor, envie sua mensagem como texto.",
                'sticker': "😊 Desculpe, não consigo processar figurinhas. Por favor, envie sua mensagem como texto.",
                'location': "📍 Desculpe, não consigo processar localizações. Por favor, envie sua mensagem como texto.",
                'contacts': "👥 Desculpe, não consigo processar contatos. Por favor, envie sua mensagem como texto.",
                'interactive': "🔘 Desculpe, não consigo processar mensagens interativas. Por favor, envie sua mensagem como texto.",
                'button': "🔘 Desculpe, não consigo processar botões. Por favor, envie sua mensagem como texto.",
                'list': "📋 Desculpe, não consigo processar listas. Por favor, envie sua mensagem como texto."
            }
            
            # Mensagem padrão para tipos não mapeados
            response_text = error_messages.get(message_type, 
                f"❌ Desculpe, não consigo processar mensagens do tipo '{message_type}'. Por favor, envie sua mensagem como texto.")
            
            # Enviar mensagem de erro
            whatsapp_service.send_message(from_number, response_text)

    except Exception as e:
        logger.error(f"❌ Erro ao processar mensagem: {e}")


@api_view(['GET'])
@permission_classes([AllowAny])
def get_doctor_availability(request, doctor_name):
    """
    Endpoint para consultar disponibilidade de um médico específico
    """
    try:
        days_ahead = int(request.GET.get('days', 7))
        
        from .services.rag_service import RAGService
        availability = RAGService.get_doctor_availability(doctor_name, days_ahead)
        
        return Response({
            'doctor': doctor_name,
            'availability': availability,
            'requested_days': days_ahead
        })
        
    except Exception as e:
        logger.error(f"Erro ao consultar disponibilidade: {e}")
        return Response(
            {'error': 'Erro interno do servidor'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([AllowAny])
def check_stored_data(request):
    """
    Endpoint para verificar dados armazenados no cache e banco
    """
    try:
        phone_number = request.GET.get('phone_number', '5511999999999')
        
        # Verificar sessão no cache
        from django.core.cache import cache
        cache_key = f"gemini_session_{phone_number}"
        cached_session = cache.get(cache_key)
        
        # Verificar sessão no banco
        from .models import ConversationMessage, ConversationSession
        db_session = ConversationSession.objects.filter(phone_number=phone_number).first()
        
        # Verificar mensagens no banco
        messages = ConversationMessage.objects.filter(session__phone_number=phone_number).order_by('-timestamp')[:5]
        
        return Response({
            'phone_number': phone_number,
            'cache_session': cached_session,
            'database_session': {
                'id': db_session.id if db_session else None,
                'current_state': db_session.current_state if db_session else None,
                'patient_name': db_session.patient_name if db_session else None,
                'name_confirmed': db_session.name_confirmed if db_session else None,
                'created_at': db_session.created_at if db_session else None,
                'updated_at': db_session.updated_at if db_session else None,
            },
            'recent_messages': [
                {
                    'id': msg.id,
                    'content': msg.content[:100] + '...' if len(msg.content) > 100 else msg.content,
                    'message_type': msg.message_type,
                    'intent': msg.intent,
                    'entities': msg.entities,
                    'created_at': msg.timestamp
                } for msg in messages
            ],
            'cache_available': cached_session is not None,
            'database_available': db_session is not None
        })

    except Exception as e:
        logger.error(f"Erro ao verificar dados armazenados: {e}")
        return Response(
            {'error': 'Erro interno do servidor'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def token_usage_stats(request):
    """
    Endpoint para monitorar uso de tokens do Gemini
    """
    try:
        # Obter estatísticas de tokens
        from .services.token_monitor import token_monitor
        stats = token_monitor.get_token_usage_stats()
        
        # Adicionar informações adicionais
        stats['monitoring_enabled'] = token_monitor.enabled
        stats['daily_limit_formatted'] = f"{stats.get('daily_limit', 0):,}"
        stats['tokens_used_formatted'] = f"{stats.get('tokens_used_today', 0):,}"
        stats['tokens_remaining_formatted'] = f"{stats.get('tokens_remaining', 0):,}"
        
        # Status baseado no uso
        usage_percentage = stats.get('usage_percentage', 0)
        if usage_percentage >= 95:
            status_level = 'CRITICAL'
            status_message = 'Uso crítico de tokens - modo econômico ativado'
        elif usage_percentage >= 90:
            status_level = 'WARNING'
            status_message = 'Uso alto de tokens - atenção necessária'
        elif usage_percentage >= 80:
            status_level = 'CAUTION'
            status_message = 'Uso moderado de tokens - monitorar'
        else:
            status_level = 'NORMAL'
            status_message = 'Uso normal de tokens'
        
        stats['status'] = {
            'level': status_level,
            'message': status_message,
            'percentage': usage_percentage
        }
        
        return Response({
            'success': True,
            'data': stats,
            'message': 'Estatísticas de tokens obtidas com sucesso'
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas de tokens: {e}")
        return Response(
            {'error': 'Erro ao obter estatísticas de tokens'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_token_usage(request):
    """
    Endpoint para resetar contador de tokens (usar com cuidado!)
    """
    try:
        # Verificar se é uma requisição autorizada (adicionar autenticação se necessário)
        from .services.token_monitor import token_monitor
        token_monitor.reset_daily_token_usage()
        
        return Response({
            'success': True,
            'message': 'Contador de tokens resetado com sucesso'
        })
        
    except Exception as e:
        logger.error(f"Erro ao resetar contador de tokens: {e}")
        return Response(
            {'error': 'Erro ao resetar contador de tokens'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
