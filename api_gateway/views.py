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

from flow_agent.services.gemini_service import GeminiService

from .services.conversation_service import conversation_service
from .services.intent_detection_service import IntentDetectionService
from .services.rag_service import RAGService
from .services.smart_collection_service import smart_collection_service
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


def handle_appointment_confirmation(phone_number: str, message: str, intent: str, entities: Dict, conversation_history: List) -> str:
    """
    Trata confirmação de agendamento e gera link de handoff
    
    Args:
        phone_number: Número do telefone do usuário
        message: Mensagem atual
        intent: Intenção detectada
        entities: Entidades extraídas
        conversation_history: Histórico da conversa
        
    Returns:
        Resposta com link de handoff personalizado
    """
    try:
        from .services.handoff_service import handoff_service

        # Obter informações do paciente da sessão persistente
        patient_info = conversation_service.get_patient_info(phone_number)
        
        # Buscar informações de agendamento no histórico
        doctor_name = patient_info.get('selected_doctor') or 'Dr. João Carvalho'  # Fallback para médico padrão
        date = patient_info.get('preferred_date') or 'Data a definir'
        time = patient_info.get('preferred_time') or 'Horário a definir'
        
        # Se não temos informações suficientes, buscar no histórico
        if doctor_name == 'Dr. João Carvalho' or date == 'Data a definir':
            for msg in reversed(conversation_history):
                msg_content = msg.get('content', '').lower()
                msg_entities = msg.get('entities', {})
                
                # Buscar nome do médico
                if 'dr.' in msg_content or 'dra.' in msg_content:
                    words = msg_content.split()
                    for i, word in enumerate(words):
                        if word in ['dr.', 'dra.', 'doutor', 'doutora']:
                            if i + 1 < len(words):
                                if i + 2 < len(words):
                                    doctor_name = f"{word.title()} {words[i+1].title()} {words[i+2].title()}"
                                else:
                                    doctor_name = f"{word.title()} {words[i+1].title()}"
                                break
                
                # Buscar data e horário
                if 'dates' in msg_entities and msg_entities['dates']:
                    date = msg_entities['dates'][0]
                
                if 'times' in msg_entities and msg_entities['times']:
                    time = msg_entities['times'][0]
        
        # Converter data para formato correto se necessário
        if date and date != 'Data a definir':
            try:
                # Se for uma data em formato brasileiro (DD/MM/YYYY)
                if '/' in str(date):
                    day, month, year = str(date).split('/')
                    if len(year) == 2:
                        year = '20' + year
                    date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                # Se for uma data em formato de texto (segunda, terça, etc.)
                elif any(day in str(date).lower() for day in ['segunda', 'terça', 'quarta', 'quinta', 'sexta', 'sábado', 'sabado', 'domingo']):
                    # Para testes, usar data padrão
                    from datetime import datetime, timedelta
                    today = datetime.now()
                    # Encontrar próxima segunda-feira
                    days_ahead = 0 - today.weekday()  # Monday is 0
                    if days_ahead <= 0:  # Target day already happened this week
                        days_ahead += 7
                    next_monday = today + timedelta(days=days_ahead)
                    date = next_monday.strftime('%Y-%m-%d')
            except Exception as e:
                logger.warning(f"Erro ao converter data '{date}': {e}")
                date = 'Data a definir'
        
        # Preparar dados do handoff
        handoff_data = {
            'patient_name': patient_info.get('patient_name', 'Paciente'),
            'doctor_name': doctor_name,
            'specialty': patient_info.get('specialty_interest', 'Consulta Geral'),
            'appointment_type': patient_info.get('insurance_type', 'Consulta'),
            'preferred_date': date,
            'preferred_time': time,
            'phone_number': phone_number,
            'insurance': patient_info.get('insurance_type', 'Não informado')
        }
        
        # Criar solicitação de agendamento no banco
        appointment_data = handoff_data.copy()
        appointment_data.pop('phone_number', None)  # Remover phone_number do dict
        
        appointment_request = conversation_service.create_appointment_request(
            phone_number,
            **appointment_data
        )
        
        # Gerar link de handoff
        logger.info(f"Gerando link de handoff com dados: {handoff_data}")
        
        whatsapp_link = handoff_service.generate_appointment_handoff_link(
            patient_name=handoff_data['patient_name'],
            doctor_name=handoff_data['doctor_name'],
            specialty=handoff_data['specialty'],
            appointment_type=handoff_data['appointment_type'],
            date=handoff_data['preferred_date'],
            time=handoff_data['preferred_time'],
            additional_info={
                'telefone_paciente': phone_number,
                'convenio': handoff_data.get('insurance', 'Não informado')
            }
        )
        
        # Atualizar link no banco
        if appointment_request:
            appointment_request.handoff_link = whatsapp_link
            appointment_request.save()
        
        # Criar mensagem de confirmação
        confirmation_message = handoff_service.create_confirmation_message(
            handoff_data['doctor_name'],
            handoff_data['preferred_date'],
            handoff_data['preferred_time'],
            handoff_data
        )
        
        # Combinar mensagem de confirmação com link
        final_message = f"""{confirmation_message}

🔗 **CLIQUE AQUI PARA CONFIRMAR:**
{whatsapp_link}

💡 **Como funciona:**
1️⃣ Clique no link acima
2️⃣ Será direcionado para WhatsApp da clínica
3️⃣ Mensagem será preenchida automaticamente
4️⃣ Nossa secretária confirmará seu agendamento

⚡ **Importante:** Este é um pré-agendamento. A confirmação final será feita pela nossa equipe!"""
        
        logger.info(f"Handoff gerado para {phone_number}: {doctor_name} - {date} {time}")
        
        return final_message
        
    except Exception as e:
        logger.error(f"Erro ao processar confirmação de agendamento: {e}")
        return "Houve um erro ao processar seu agendamento. Por favor, entre em contato conosco: (11) 99999-9999"


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
                # Detectar intenção com contexto
                intent, confidence, entities = intent_service.detect_intent_with_context(
                    from_number, text_content
                )
                logger.info(f"Intenção contextual detectada: {intent} (confiança: {confidence})")
                
                # Processar com coleta inteligente de informações
                collection_result = smart_collection_service.process_message_with_collection(
                    from_number, text_content, intent, entities
                )
                
                # Obter histórico da conversa para contexto
                conversation_history = conversation_service.get_conversation_history(from_number, limit=3)
                
                # Se tem resposta específica da coleta, usar ela
                if collection_result['response']:
                    response_text = collection_result['response']
                # Se precisa de handoff, processar confirmação
                elif collection_result['requires_handoff']:
                    response_text = handle_appointment_confirmation(
                        from_number, text_content, intent, entities, conversation_history
                    )
                else:
                    # Gerar resposta normal com Gemini
                    response_text = gemini_service.generate_response(
                        user_message=text_content,
                        intent=intent,
                        context={
                            'entities': entities,
                            'confidence': confidence,
                            'message_id': message_id,
                            'timestamp': timestamp,
                            'conversation_history': conversation_history,
                            'info_status': collection_result.get('info_status', {})
                        },
                        clinic_data=get_clinic_data()
                    )
                
                # Enviar resposta
                success = whatsapp_service.send_message(from_number, response_text)
                
                if success:
                    logger.info(f"Resposta enviada com sucesso para {from_number}")
                    
                    # Adicionar mensagens ao banco de dados
                    conversation_service.add_message(
                        from_number, text_content, 'user', intent, confidence, entities
                    )
                    conversation_service.add_message(
                        from_number, response_text, 'bot', 'resposta_bot', 1.0, {}
                    )
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
        phone_number = data.get('phone_number', 'test_user')
        use_context = data.get('use_context', False)
        
        if not message:
            return Response(
                {'error': 'Mensagem é obrigatória'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if use_context:
            # Usar detecção contextual
            intent, confidence, entities = intent_service.detect_intent_with_context(
                phone_number, message
            )
            
            # Obter histórico para mostrar contexto
            from .services.context_manager import context_manager
            history = context_manager.get_conversation_history(phone_number, limit=5)
            
            return Response({
                'message': message,
                'phone_number': phone_number,
                'intent': intent,
                'confidence': confidence,
                'entities': entities,
                'conversation_history': history,
                'contextual_analysis': True
            })
        else:
            # Usar detecção tradicional
            intent, confidence = intent_service.detect_intent(message)
            entities = intent_service.extract_entities(message)
            
            return Response({
                'message': message,
                'intent': intent,
                'confidence': confidence,
                'entities': entities,
                'is_question': intent_service.is_question(message),
                'contextual_analysis': False
            })
        
    except Exception as e:
        logger.error(f"Erro no teste de detecção de intenção: {e}")
        return Response(
            {'error': 'Erro interno do servidor'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def clear_context(request):
    """
    Endpoint para limpar contexto de conversa (apenas para testes)
    """
    try:
        data = request.data
        phone_number = data.get('phone_number', 'test_user')
        
        from .services.context_manager import context_manager
        context_manager.clear_context(phone_number)
        
        return Response({
            'message': f'Contexto limpo para {phone_number}',
            'phone_number': phone_number
        })
        
    except Exception as e:
        logger.error(f"Erro ao limpar contexto: {e}")
        return Response(
            {'error': 'Erro interno do servidor'}, 
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
