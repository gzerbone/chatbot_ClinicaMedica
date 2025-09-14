"""
Views para API Gateway - Integração com WhatsApp
"""
import json
import logging

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from flow_agent.services.gemini_service import GeminiService

from .services.intent_detection_service import IntentDetectionService
from .services.rag_service import RAGService
from .services.whatsapp_service import WhatsAppService

logger = logging.getLogger(__name__)

# Inicializar serviços
whatsapp_service = WhatsAppService()
intent_service = IntentDetectionService()
gemini_service = GeminiService()
# Obter dados da clínica através do RAGService
def get_clinic_data():
    """Obtém dados atualizados da clínica"""
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
        
        logger.info(f"Tentativa de verificação do webhook: mode={mode}, token={token}")
        
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
        logger.info(f"Webhook recebido: {json.dumps(body, indent=2)}")
        
        # Verificar se é uma mensagem válida
        if 'entry' not in body:
            return JsonResponse({'status': 'ok'})
        
        for entry in body['entry']:
            if 'changes' not in entry:
                continue
                
            for change in entry['changes']:
                if change.get('field') == 'messages':
                    messages = change.get('value', {}).get('messages', [])
                    
                    for message in messages:
                        process_message(message, change['value'])
        
        return JsonResponse({'status': 'ok'})
        
    except Exception as e:
        logger.error(f"Erro ao processar webhook: {e}")
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
        
        logger.info(f"Processando mensagem {message_id} de {from_number}")
        
        # Marcar mensagem como lida
        whatsapp_service.mark_message_as_read(message_id)
        
        # Processar apenas mensagens de texto
        if message_type == 'text':
            text_content = message.get('text', {}).get('body', '')
            
            if text_content:
                # Detectar intenção
                intent, confidence = intent_service.detect_intent(text_content)
                logger.info(f"Intenção detectada: {intent} (confiança: {confidence})")
                
                # Extrair entidades
                entities = intent_service.extract_entities(text_content)
                
                # Gerar resposta com Gemini
                response_text = gemini_service.generate_response(
                    user_message=text_content,
                    intent=intent,
                    context={
                        'entities': entities,
                        'confidence': confidence,
                        'message_id': message_id,
                        'timestamp': timestamp
                    },
                    clinic_data=get_clinic_data()
                )
                
                # Enviar resposta
                success = whatsapp_service.send_message(from_number, response_text)
                
                if success:
                    logger.info(f"Resposta enviada com sucesso para {from_number}")
                else:
                    logger.error(f"Falha ao enviar resposta para {from_number}")
        
        elif message_type == 'interactive':
            # Processar mensagens interativas (botões, listas)
            handle_interactive_message(message, from_number)
            
        else:
            logger.info(f"Tipo de mensagem não suportado: {message_type}")
            
    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {e}")


def handle_interactive_message(message, from_number):
    """
    Processa mensagens interativas (botões, listas)
    """
    try:
        interactive = message.get('interactive', {})
        interactive_type = interactive.get('type')
        
        if interactive_type == 'button_reply':
            button_text = interactive.get('button_reply', {}).get('title', '')
            logger.info(f"Botão clicado: {button_text}")
            
            # Processar resposta do botão
            response_text = gemini_service.generate_response(
                user_message=f"Botão clicado: {button_text}",
                intent='interactive_response',
                context={'interactive_type': 'button', 'button_text': button_text},
                clinic_data=get_clinic_data()
            )
            
            whatsapp_service.send_message(from_number, response_text)
            
        elif interactive_type == 'list_reply':
            list_item = interactive.get('list_reply', {})
            item_title = list_item.get('title', '')
            item_id = list_item.get('id', '')
            
            logger.info(f"Item da lista selecionado: {item_title} (ID: {item_id})")
            
            # Processar resposta da lista
            response_text = gemini_service.generate_response(
                user_message=f"Item selecionado: {item_title}",
                intent='interactive_response',
                context={'interactive_type': 'list', 'item_title': item_title, 'item_id': item_id},
                clinic_data=get_clinic_data()
            )
            
            whatsapp_service.send_message(from_number, response_text)
            
    except Exception as e:
        logger.error(f"Erro ao processar mensagem interativa: {e}")


@api_view(['POST'])
@permission_classes([AllowAny])
def send_test_message(request):
    """
    Endpoint para testar o envio de mensagens (apenas para desenvolvimento)
    """
    try:
        data = request.data
        phone_number = data.get('phone_number')
        message = data.get('message', 'Teste do chatbot da clínica médica!')
        
        if not phone_number:
            return Response(
                {'error': 'Número de telefone é obrigatório'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        success = whatsapp_service.send_message(phone_number, message)
        
        if success:
            return Response({'status': 'Mensagem enviada com sucesso'})
        else:
            return Response(
                {'error': 'Falha ao enviar mensagem'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    except Exception as e:
        logger.error(f"Erro no teste de envio: {e}")
        return Response(
            {'error': 'Erro interno do servidor'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def test_gemini_connection(request):
    """
    Endpoint para testar a conexão com o Gemini
    """
    try:
        is_connected = gemini_service.test_connection()
        
        if is_connected:
            return Response({'status': 'Conexão com Gemini OK'})
        else:
            return Response(
                {'error': 'Falha na conexão com Gemini'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    except Exception as e:
        logger.error(f"Erro no teste do Gemini: {e}")
        return Response(
            {'error': f'Erro na conexão com Gemini: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def test_intent_detection(request):
    """
    Endpoint para testar a detecção de intenções
    """
    try:
        data = request.data
        message = data.get('message', '')
        
        if not message:
            return Response(
                {'error': 'Mensagem é obrigatória'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        intent, confidence = intent_service.detect_intent(message)
        entities = intent_service.extract_entities(message)
        
        return Response({
            'message': message,
            'intent': intent,
            'confidence': confidence,
            'entities': entities,
            'is_question': intent_service.is_question(message)
        })
        
    except Exception as e:
        logger.error(f"Erro no teste de detecção de intenção: {e}")
        return Response(
            {'error': 'Erro interno do servidor'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
