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

from .services.conversation_service import conversation_service
from .services.gemini_chatbot_service import gemini_chatbot_service
from .services.whatsapp_service import WhatsAppService

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

        # Log mais limpo do webhook
        logger.info("📨 Webhook do WhatsApp processado com sucesso")

        # Verificar se é uma mensagem válida
        if 'entry' not in body:
            logger.warning("Webhook sem entries válidas")
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

        logger.info(f"✅ Webhook processado: {total_messages} mensagens")

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

        # Marcar mensagem como lida
        whatsapp_service.mark_message_as_read(message_id)

        # Processar apenas mensagens de texto
        if message_type == 'text':
            text_content = message.get('text', {}).get('body', '')

            if text_content:
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
                        logger.info(f"✅ RESPOSTA ENVIADA ({agent})")
                        logger.info(f"💬 GEMINI: {response_text}")

                        # Log limpo da conversação
                        from .services.conversation_service import \
                            conversation_logger
                        conversation_logger.info(f"💬 {from_number} → {text_content}")
                        conversation_logger.info(f"🤖 GEMINI → {response_text}")
                    else:
                        logger.error(f"❌ Falha ao enviar resposta para {from_number}")

                except Exception as e:
                    logger.error(f"❌ Erro no Gemini Chatbot Service: {e}")
                    
                    # Fallback simples
                    response_text = "Desculpe, estou temporariamente indisponível. Como posso ajudá-lo?"
                    success = whatsapp_service.send_message(from_number, response_text)
                    
                    if success:
                        logger.info("✅ Resposta fallback enviada")
                        logger.info(f"💬 FALLBACK: {response_text}")
                    else:
                        logger.error(f"❌ Falha ao enviar resposta fallback para {from_number}")

        elif message_type == 'interactive':
            # Processar mensagens interativas (botões, listas)
            logger.info(f"🔘 Mensagem interativa recebida de {from_number}")
            handle_interactive_message(message, from_number)

        else:
            logger.info(f"ℹ️ Tipo de mensagem não suportado: {message_type}")

    except Exception as e:
        logger.error(f"❌ Erro ao processar mensagem: {e}")


def handle_interactive_message(message, from_number):
    """
    Processa mensagens interativas (botões, listas) usando o Gemini Chatbot Service
    """
    try:
        interactive = message.get('interactive', {})
        interactive_type = interactive.get('type')

        if interactive_type == 'button_reply':
            button_text = interactive.get('button_reply', {}).get('title', '')
            logger.info(f"🔘 Botão clicado por {from_number}: {button_text}")

            # Usar Gemini Chatbot Service para processar resposta do botão
            try:
                result = gemini_chatbot_service.process_message(
                    from_number,
                    f"Botão clicado: {button_text}"
                )

                response_text = result.get('response', f"Entendi que você clicou em: {button_text}")
                intent = result.get('intent', 'interactive_response')

                logger.info(f"🤖 [{intent.upper()}] Processando botão: {button_text}")
                logger.info(f"💬 GEMINI: {response_text}")

                # Log da conversação interativa
                from .services.conversation_service import conversation_logger
                conversation_logger.info(f"🔘 {from_number} → Botão: {button_text}")
                conversation_logger.info(f"🤖 GEMINI → {response_text}")

                whatsapp_service.send_message(from_number, response_text)

            except Exception as e:
                logger.error(f"❌ Erro no Gemini para botão: {e}")
                response_text = f"Entendi que você clicou em: {button_text}. Como posso ajudá-lo?"
                whatsapp_service.send_message(from_number, response_text)

        elif interactive_type == 'list_reply':
            list_item = interactive.get('list_reply', {})
            item_title = list_item.get('title', '')
            item_id = list_item.get('id', '')

            logger.info(f"📋 Item da lista selecionado por {from_number}: {item_title} (ID: {item_id})")

            # Usar Gemini Chatbot Service para processar resposta da lista
            try:
                result = gemini_chatbot_service.process_message(
                    from_number,
                    f"Item selecionado: {item_title}"
                )

                response_text = result.get('response', f"Entendi que você selecionou: {item_title}")
                intent = result.get('intent', 'interactive_response')

                logger.info(f"🤖 [{intent.upper()}] Processando seleção: {item_title}")
                logger.info(f"💬 GEMINI: {response_text}")

                # Log da conversação interativa
                from .services.conversation_service import conversation_logger
                conversation_logger.info(f"📋 {from_number} → Lista: {item_title}")
                conversation_logger.info(f"🤖 GEMINI → {response_text}")

                whatsapp_service.send_message(from_number, response_text)

            except Exception as e:
                logger.error(f"❌ Erro no Gemini para lista: {e}")
                response_text = f"Entendi que você selecionou: {item_title}. Como posso ajudá-lo?"
                whatsapp_service.send_message(from_number, response_text)

    except Exception as e:
        logger.error(f"❌ Erro ao processar mensagem interativa: {e}")


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
        is_connected = gemini_chatbot_service.test_connection()
        
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






@api_view(['GET'])
@permission_classes([AllowAny])
def test_calendar_connection(request):
    """
    Endpoint para testar a conexão com Google Calendar
    """
    try:
        from .services.google_calendar_service import google_calendar_service
        
        is_connected = google_calendar_service.test_connection()
        
        return Response({
            'google_calendar_enabled': google_calendar_service.enabled,
            'connection_status': 'connected' if is_connected else 'disconnected',
            'message': 'Google Calendar funcionando' if is_connected else 'Google Calendar não disponível (usando dados simulados)'
        })
        
    except Exception as e:
        logger.error(f"Erro ao testar Google Calendar: {e}")
        return Response(
            {'error': f'Erro na conexão com Google Calendar: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def get_doctor_availability(request, doctor_name):
    """
    Endpoint para consultar disponibilidade de um médico específico
    """
    try:
        days_ahead = int(request.GET.get('days', 7))
        
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


@api_view(['POST'])
@permission_classes([AllowAny])
def test_chatbot_service(request):
    """
    Endpoint para testar o novo serviço de chatbot Gemini centralizado
    """
    try:
        data = request.data
        phone_number = data.get('phone_number', '5511999999999')
        message = data.get('message', 'Olá, gostaria de agendar uma consulta')

        if not message:
            return Response(
                {'error': 'Mensagem é obrigatória'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Processar mensagem com o Gemini Chatbot Service
        result = gemini_chatbot_service.process_message(phone_number, message)

        return Response({
            'phone_number': phone_number,
            'message': message,
            'response': result.get('response'),
            'intent': result.get('intent'),
            'confidence': result.get('confidence'),
            'state': result.get('state'),
            'session_data': result.get('session_data', {}),
            'analysis': result.get('analysis', {}),
            'agent': result.get('agent', 'gemini')
        })

    except Exception as e:
        logger.error(f"Erro no teste do chatbot: {e}")
        return Response(
            {'error': 'Erro interno do servidor'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def test_intent_analysis(request):
    """
    Endpoint para testar a análise de intenção usando Gemini centralizado
    """
    try:
        data = request.data
        message = data.get('message', 'Olá, quais médicos vocês têm?')
        phone_number = data.get('phone_number', '5511999999999')

        if not message:
            return Response(
                {'error': 'Mensagem é obrigatória'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Processar mensagem com Gemini centralizado
        result = gemini_chatbot_service.process_message(phone_number, message)

        return Response({
            'message': message,
            'phone_number': phone_number,
            'intent': result.get('intent'),
            'confidence': result.get('confidence'),
            'state': result.get('state'),
            'analysis': result.get('analysis', {}),
            'response': result.get('response'),
            'session_data': result.get('session_data', {}),
            'agent': result.get('agent', 'gemini'),
            'gemini_available': gemini_chatbot_service.enabled
        })

    except Exception as e:
        logger.error(f"Erro no teste de análise de intenção: {e}")
        return Response(
            {'error': 'Erro interno do servidor'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def test_entity_extraction(request):
    """
    Endpoint para testar especificamente a extração de entidades
    """
    try:
        data = request.data
        message = data.get('message', 'Meu nome é João Silva, quero agendar com Dr. João Carvalho para segunda-feira às 14h')
        phone_number = data.get('phone_number', '5511999999999')

        if not message:
            return Response(
                {'error': 'Mensagem é obrigatória'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Processar mensagem com Gemini centralizado
        result = gemini_chatbot_service.process_message(phone_number, message)

        return Response({
            'message': message,
            'phone_number': phone_number,
            'intent': result.get('intent'),
            'confidence': result.get('confidence'),
            'state': result.get('state'),
            'entities_extracted': result.get('analysis', {}).get('entities', {}),
            'session_data': result.get('session_data', {}),
            'response': result.get('response'),
            'agent': result.get('agent', 'gemini'),
            'gemini_available': gemini_chatbot_service.enabled
        })

    except Exception as e:
        logger.error(f"Erro no teste de extração de entidades: {e}")
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


@api_view(['POST'])
@permission_classes([AllowAny])
def test_handoff_generation(request):
    """
    Endpoint para testar geração de links de handoff
    """
    try:
        from .services.handoff_service import handoff_service
        
        data = request.data
        
        # Dados de exemplo ou fornecidos
        patient_name = data.get('patient_name', 'João Silva')
        doctor_name = data.get('doctor_name', 'Dr. João Carvalho')
        specialty = data.get('specialty', 'Cardiologia')
        appointment_type = data.get('appointment_type', 'Particular')
        date = data.get('date', '15/09/2025')
        time = data.get('time', '14:30')
        
        # Gerar link de handoff
        whatsapp_link = handoff_service.generate_appointment_handoff_link(
            patient_name=patient_name,
            doctor_name=doctor_name,
            specialty=specialty,
            appointment_type=appointment_type,
            date=date,
            time=time,
            additional_info={
                'telefone_paciente': '5511999999999',
                'convenio': appointment_type
            }
        )
        
        # Gerar mensagem de confirmação
        confirmation_message = handoff_service.create_confirmation_message(
            doctor_name, date, time, {
                'patient_name': patient_name,
                'appointment_type': appointment_type
            }
        )
        
        return Response({
            'patient_name': patient_name,
            'doctor_name': doctor_name,
            'specialty': specialty,
            'date': date,
            'time': time,
            'whatsapp_link': whatsapp_link,
            'confirmation_message': confirmation_message,
            'link_preview': f"Link gerado com sucesso",
            'message': 'Link de handoff gerado com sucesso'
        })
        
    except Exception as e:
        logger.error(f"Erro ao testar handoff: {e}")
        return Response(
            {'error': 'Erro interno do servidor'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
