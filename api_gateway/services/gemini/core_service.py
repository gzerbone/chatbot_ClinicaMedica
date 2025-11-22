"""
Core Service - Orquestrador Principal do Chatbot Gemini

Responsável por:
- Orquestrar todos os módulos especializados
- Processar mensagens do usuário
- Coordenar fluxo de conversação
"""

import logging
from typing import Any, Dict, Optional

from django.conf import settings

from ..conversation_service import conversation_service
from ..handoff_service import handoff_service
from ..rag_service import RAGService
from ..smart_scheduling_service import smart_scheduling_service
from .entity_extractor import EntityExtractor
from .intent_detector import IntentDetector
from .response_generator import ResponseGenerator
from .session_manager import SessionManager

logger = logging.getLogger(__name__)


class GeminiChatbotService:
    """
    Orquestrador Principal do Chatbot - Serviço Modularizado
    
    Delega responsabilidades para módulos especializados:
    - IntentDetector: Detecta intenções
    - EntityExtractor: Extrai entidades
    - ResponseGenerator: Gera respostas
    - SessionManager: Gerencia sessões
    """
    
    def __init__(self):
        self.api_key = getattr(settings, 'GEMINI_API_KEY', '')
        self.enabled = getattr(settings, 'GEMINI_ENABLED', True)
        
        if not self.api_key:
            logger.warning("GEMINI_API_KEY não configurada nas settings")
            self.enabled = False
        
        if not self.enabled:
            logger.warning("Gemini AI está desabilitado nas configurações")
            return
        
        try:
            # Inicializar módulos especializados
            self.intent_detector = IntentDetector()
            self.entity_extractor = EntityExtractor()
            self.response_generator = ResponseGenerator()
            self.session_manager = SessionManager()
            self.rag_service = RAGService()
                        
        except Exception as e:
            logger.error(f"❌ Erro ao configurar Gemini: {e}")
            self.enabled = False
    
    def process_message(self, phone_number: str, message: str) -> Dict[str, Any]:
        """
        Processa mensagem do usuário - Método Principal
        
        Args:
            phone_number: Número do telefone do usuário
            message: Mensagem do usuário
            
        Returns:
            Dict com resposta e informações do processamento
        """
        try:
            if not self.enabled:
                return self._get_fallback_response(message)
            # Django controla o fluxo:
            # 1. Obter sessão
            session = self.session_manager.get_or_create_session(phone_number)
            logger.info(f"📊 Estado atual da sessão: {session.get('current_state')}")
            
            # 2. Verificar se há agendamento pausado (sistema de dúvidas)
            if conversation_service.has_paused_appointment(phone_number):
                # Detectar palavras-chave para retomar
                if any(keyword in message.lower() for keyword in ['continuar', 'retomar', 'voltar']):
                    resume_result = conversation_service.resume_appointment(phone_number)
                    
                    # Atualizar sessão em memória para refletir o estado restaurado
                    if resume_result.get('resumed'):
                        session['current_state'] = resume_result.get('restored_state')
                        session['previous_state'] = None
                        logger.info(f"▶️ Sessão em memória atualizada após RETOMADA: current_state={session['current_state']}")
                    
                    return {
                        'response': resume_result.get('message', '✅ Vamos continuar!'),
                        'intent': 'retomar_agendamento',  #impotante para debbung
                        'confidence': 1.0
                    }
            
            # 3. Obter histórico e dados da clínica
            conversation_history = self.session_manager.get_conversation_history(phone_number)
            clinic_data = self._get_clinic_data_optimized()
            
            # 4. Detectar intenção (sem entidades)
            intent_result = self.intent_detector.analyze_message(
                message, session, conversation_history, clinic_data
            )
            
            logger.info(f"🔍 Intent detectado: {intent_result['intent']}, Confiança: {intent_result['confidence']}")
            
            # 5. Extrair entidades (usando apenas Gemini - sem fallback)
            entities_result = self.entity_extractor.extract_entities(
                message, session, conversation_history, clinic_data
            )
            
            logger.info(f"📦 Entidades extraídas: {entities_result}")
            
            # 6. Combinar resultados
            analysis_result = {
                'intent': intent_result['intent'],
                'next_state': intent_result['next_state'],
                'confidence': intent_result['confidence'],
                'entities': entities_result,
                'reasoning': intent_result.get('reasoning', ''),
                'raw_message': message  # 🔍 Guarda mensagem original para análises posteriores (pronome etc.)
            }

            # 6.1 Fluxo dedicado para confirmação precoce do nome do paciente
            manual_name_response = self._handle_patient_name_flow(
                phone_number=phone_number,
                session=session,
                message=message,
                analysis_result=analysis_result
            )
            if manual_name_response:
                response_result = manual_name_response

                # Atualizar sessão com base no fluxo manual de nome
                self.session_manager.update_session(
                    phone_number, session, analysis_result, response_result
                )

                # Salvar histórico e retornar imediatamente
                self.session_manager.save_messages(
                    phone_number, message, response_result['response'], analysis_result
                )

                return response_result

            # 7. Detectar se usuário quer tirar dúvidas durante agendamento
            # NÃO pausar se estiver confirmando (última etapa) ou em estados iniciais
            if analysis_result['intent'] in ['buscar_info', 'duvida']:
                # Só pausa se estiver no MEIO do agendamento (não no início nem no fim)
                pausable_states = ['collecting_patient_info', 'selecting_specialty', 'selecting_doctor', 'choosing_schedule', 'confirming_name']
                if session['current_state'] in pausable_states:
                    # IMPORTANTE: Salvar o estado anterior ANTES de pausar
                    # (porque pause_for_question já muda o current_state no banco)
                    previous_state_before_pause = session['current_state']
                    
                    # Pausar agendamento (salva no banco)
                    paused = conversation_service.pause_for_question(phone_number)
                    if paused:
                        # Atualizar variável session em memória para refletir a mudança
                        session['previous_state'] = previous_state_before_pause
                        session['current_state'] = 'answering_questions'
                        logger.info(f"⏸️ Sessão em memória atualizada: current_state={session['current_state']}, previous_state={session['previous_state']}")

            # 7.5. Verificar se usuário está perguntando explicitamente sobre disponibilidade
            message_lower = message.lower()
            asking_availability = any(word in message_lower for word in [
                'quais horario', 'que horario', 'horario disponivel', 'horário disponível',
                'quais os horario', 'quais sao os horario', 'quais são os horário',
                'quais horarios', 'quais horários', 'que horarios', 'que horários',
                'tem disponivel', 'tem disponível', 'está disponivel', 'está disponível',
                'horarios disponiveis', 'horários disponíveis', 'livre', 'vago',
                'datas disponiveis', 'datas disponíveis', 'quais datas', 'quais são as datas'
            ])
            
            # Se está em choosing_schedule e tem médico, responder diretamente com horários disponíveis
            if asking_availability and session.get('selected_doctor') and session.get('current_state') == 'choosing_schedule':
                logger.info(f"🔍 DETECTADO: Usuário perguntando sobre disponibilidade no estado choosing_schedule")
                doctor_name = session.get('selected_doctor')
                date_filter = session.get('preferred_date')  # Pode ser None se não tiver data ainda
                
                # Consultar horários disponíveis
                availability = smart_scheduling_service.get_doctor_availability(
                    doctor_name=doctor_name,
                    days_ahead=7,
                    date_filter=date_filter
                )
                
                if availability.get('has_availability'):
                    days_info = availability.get('days_info', availability.get('days', []))
                    if days_info:
                        if date_filter:
                            # Se tem data específica, mostrar apenas esse dia
                            day_info = days_info[0] if days_info else None
                            if day_info:
                                available_times = day_info.get('available_times', [])
                                date_str = day_info.get('date')
                                weekday = day_info.get('weekday')
                                
                                if available_times:
                                    response_text = f"📅 **Horários disponíveis para {weekday}, {date_str}:**\n\n"
                                    response_text += "✅ " + ", ".join(available_times[:10])
                                    
                                    if len(available_times) > 10:
                                        response_text += f" (+{len(available_times) - 10} outros)"
                                    
                                    response_text += "\n\nQual desses horários você prefere?"
                                    
                                    response_result = {
                                        'response': response_text,
                                        'intent': 'buscar_info',
                                        'confidence': 1.0
                                    }
                                    
                                    self.session_manager.update_session(
                                        phone_number, session, analysis_result, response_result
                                    )
                                    self.session_manager.save_messages(
                                        phone_number, message, response_result['response'], analysis_result
                                    )
                                    
                                    return response_result
                        else:
                            # Se não tem data específica, mostrar todos os dias disponíveis
                            response_text = f"📅 *Horários disponíveis para o Dr. {doctor_name.split()[-1] if ' ' in doctor_name else doctor_name}:*\n\n"
                            
                            for day in days_info[:5]:  # Mostrar até 5 dias
                                date_str = day.get('date', '')
                                weekday = day.get('weekday', '')
                                available_times = day.get('available_times', [])
                                
                                if available_times:
                                    times_display = ", ".join(available_times[:6])  # Até 6 horários por dia
                                    if len(available_times) > 6:
                                        times_display += f" (+{len(available_times) - 6} outros)"
                                    response_text += f"**{weekday} ({date_str}):** {times_display}\n"
                            
                            if len(days_info) > 5:
                                response_text += f"\n*E mais {len(days_info) - 5} dias com horários disponíveis*\n"
                            
                            response_text += "\nQual data e horário você prefere?"
                            
                            response_result = {
                                'response': response_text,
                                'intent': 'buscar_info',
                                'confidence': 1.0
                            }
                            
                            self.session_manager.update_session(
                                phone_number, session, analysis_result, response_result
                            )
                            self.session_manager.save_messages(
                                phone_number, message, response_result['response'], analysis_result
                            )
                            
                            return response_result
            
            # 7.6. Verificar disponibilidade real se for solicitação de agendamento
            # OU se estiver no estado choosing_schedule (precisa mostrar horários disponíveis)
            current_state = session.get('current_state', 'idle')
            doctor_name = session.get('selected_doctor')
            
            # Se está no estado choosing_schedule e tem médico, SEMPRE consultar disponibilidade
            if (current_state == 'choosing_schedule' and doctor_name) or analysis_result['intent'] == 'agendar_consulta':
                # Verificar se usuário está perguntando explicitamente sobre horários disponíveis
                message_lower = message.lower()
                asking_availability = any(word in message_lower for word in [
                    'quais horarios', 'que horarios', 'horarios disponiveis', 'horários disponíveis',
                    'quais horários', 'tem disponivel', 'tem disponível', 'está disponivel', 'está disponível',
                    'livre', 'vago', 'datas disponiveis', 'datas disponíveis', 'quais datas'
                ])
                
                # Se está em choosing_schedule OU usuário pergunta sobre disponibilidade, consultar
                if current_state == 'choosing_schedule' or asking_availability:
                    logger.info(f"📅 Consultando disponibilidade para {doctor_name} (estado: {current_state}, perguntando: {asking_availability})")
                    
                    # Consultar disponibilidade diretamente
                    availability = smart_scheduling_service.get_doctor_availability(
                        doctor_name=doctor_name,
                        days_ahead=7
                    )
                    
                    if availability.get('has_availability'):
                        # Adicionar informações de disponibilidade ao analysis_result
                        analysis_result['scheduling_info'] = {
                            'has_availability_info': True,
                            'calendar_availability': {
                                'has_availability': True,
                                'doctor_name': doctor_name,
                                'available_slots': availability.get('available_slots', 0),
                                'days_info': availability.get('days_info', [])
                            }
                        }
                        logger.info(f"✅ Disponibilidade consultada: {availability.get('available_slots', 0)} horários disponíveis")
                    else:
                        analysis_result['scheduling_info'] = {
                            'has_availability_info': True,
                            'calendar_availability': {
                                'has_availability': False,
                                'doctor_name': doctor_name
                            }
                        }
                else:
                    # Para outros casos, usar o método normal
                    scheduling_analysis = self._handle_scheduling_request(
                        message, session, analysis_result
                    )
                    if scheduling_analysis.get('has_availability_info'):
                        # Se temos informações de disponibilidade, usar na resposta
                        analysis_result['scheduling_info'] = scheduling_analysis
            
            # 7.7. NÃO retomar aqui - será feito DEPOIS da geração da resposta
            # A retomada automática foi movida para depois da geração da resposta (linha ~860)
            # para garantir que dúvidas sejam respondidas antes de retomar o agendamento
            
            # 7.8. Validar se usuário está tentando fornecer data/horário sem ter médico e especialidade
            entities = analysis_result.get('entities', {})
            if (entities.get('data') or entities.get('horario')) and not (session.get('selected_specialty') and session.get('selected_doctor')):
                logger.warning("⚠️ Usuário tentou fornecer data/horário sem ter especialidade E médico selecionados")
                
                # Determinar o que falta
                missing_parts = []
                if not session.get('selected_specialty'):
                    missing_parts.append('especialidade')
                if not session.get('selected_doctor'):
                    missing_parts.append('médico')
                
                # Gerar resposta informando que precisa selecionar especialidade/médico primeiro
                missing_text = ' e '.join(missing_parts)
                response_text = f"Para escolher data e horário, primeiro preciso saber a {missing_text} que você deseja. "
                
                if not session.get('selected_specialty'):
                    response_text += "Qual especialidade médica você procura?"
                elif not session.get('selected_doctor'):
                    response_text += "Qual médico você prefere?"
                
                # Retornar resposta diretamente sem gerar com Gemini
                return {
                    'response': response_text,
                    'intent': analysis_result['intent'],
                    'confidence': 1.0
                }
            
            # 8. Atualizar sessão ANTES de verificar informações faltantes
            self.session_manager.update_session(
                phone_number, session, analysis_result, {'response': ''}
            )
            
            # 8.1. Verificar se a data fornecida não pôde ser normalizada
            if session.get('invalid_date_provided'):
                invalid_date = session.get('invalid_date_provided')
                # Limpar o flag
                session['invalid_date_provided'] = None
                
                response_text = f"Desculpe, não consegui entender a data '{invalid_date}'. 😊\n\n"
                response_text += "Por favor, informe a data no formato numérico, por exemplo:\n"
                response_text += "• **21/11** (dia e mês)\n"
                response_text += "• **21/11/2025** (dia, mês e ano)\n"
                response_text += "• **21 de novembro**\n\n"
                response_text += "Qual data você prefere para a consulta?"
                
                response_result = {
                    'response': response_text,
                    'intent': 'solicitar_data_numerica',
                    'confidence': 1.0
                }
                
                self.session_manager.update_session(
                    phone_number, session, analysis_result, response_result
                )
                self.session_manager.save_messages(
                    phone_number, message, response_result['response'], analysis_result
                )
                
                return response_result

            # ═══════════════════════════════════════════════════════════════════════════════
            # 8.5. VALIDAR HORÁRIO ASSIM QUE FOR FORNECIDO (não esperar confirmação)
            # ═══════════════════════════════════════════════════════════════════════════════
            # Se o usuário acabou de fornecer data E horário, validar imediatamente
            # Isso evita perguntar "gostaria de confirmar?" para então descobrir que está indisponível
            # ═══════════════════════════════════════════════════════════════════════════════
            entities = analysis_result.get('entities', {})
            if (entities.get('data') or entities.get('horario')) and analysis_result['intent'] == 'agendar_consulta':
                doctor_name = session.get('selected_doctor')
                # IMPORTANTE: Usar a data extraída nas entidades (mais recente) ou a da sessão
                # Se há data nas entidades, usar essa (foi extraída agora)
                # Se não há, usar a da sessão (foi extraída anteriormente)
                requested_date = entities.get('data') or session.get('preferred_date')
                # IMPORTANTE: Usar o horário extraído nas entidades (mais recente) ou o da sessão
                requested_time = entities.get('horario') or session.get('preferred_time')
                
                # Log para debug
                logger.info(f"🔍 DEBUG - Validação de horário:")
                logger.info(f"  - Data nas entidades: {entities.get('data')}")
                logger.info(f"  - Data na sessão: {session.get('preferred_date')}")
                logger.info(f"  - Data escolhida para validação: {requested_date}")
                logger.info(f"  - Horário nas entidades: {entities.get('horario')}")
                logger.info(f"  - Horário na sessão: {session.get('preferred_time')}")
                logger.info(f"  - Horário escolhido para validação: {requested_time}")
                
                # Se agora temos médico, data E horário, validar disponibilidade
                if doctor_name and requested_date and requested_time:
                    logger.info(f"🔍 Validando horário fornecido: {requested_time} em {requested_date} para {doctor_name}")
                    
                    time_slot_check = smart_scheduling_service.is_time_slot_available(
                        doctor_name=doctor_name,
                        requested_date=requested_date,
                        requested_time=requested_time
                    )
                    
                    logger.info(f"📊 DEBUG - Resultado da validação: available={time_slot_check.get('available')}, alternative_times={len(time_slot_check.get('alternative_times', []))} horários")
                    
                    if not time_slot_check.get('available'):
                        # ❌ HORÁRIO NÃO DISPONÍVEL
                        logger.warning(f"⚠️ Horário {requested_time} em {requested_date} não está disponível para {doctor_name}")
                        
                        # IMPORTANTE: Limpar o horário das entidades também para que update_session não o salve novamente
                        if 'horario' in entities:
                            del entities['horario']
                        if 'data' in entities and not session.get('preferred_date'):
                            # Se a data ainda não estava salva, não salvar agora também
                            del entities['data']
                        analysis_result['entities'] = entities
                        
                        # Limpar APENAS O HORÁRIO da sessão (manter a data!)
                        session['preferred_time'] = None
                        
                        # Atualizar no banco também - APENAS O HORÁRIO
                        db_session = conversation_service.get_or_create_session(phone_number)
                        db_session.preferred_time = None
                        db_session.save()
                        
                        # Construir mensagem informativa
                        date_formatted = time_slot_check.get('date_formatted', requested_date)
                        time_formatted = time_slot_check.get('time_formatted', requested_time)
                        weekday = time_slot_check.get('weekday', '')
                        
                        # Formatar mensagem inicial
                        if weekday:
                            response_text = f"❌ O horário {time_formatted} não está disponível para {weekday}, {date_formatted}.\n\n"
                        else:
                            response_text = f"❌ O horário {time_formatted} não está disponível para {date_formatted}.\n\n"
                        
                        # Sugerir horários alternativos
                        alternative_times = time_slot_check.get('alternative_times', [])
                        if alternative_times:
                            weekday_display = weekday if weekday else date_formatted
                            response_text += f"📅 **Horários disponíveis para {weekday_display}:**\n"
                            response_text += "✅ " + ", ".join(alternative_times[:8])  # Mostrar até 8 horários
                            
                            total_alternatives = time_slot_check.get('total_alternatives', len(alternative_times))
                            if total_alternatives > 8:
                                response_text += f" (+{total_alternatives - 8} outros)"
                            
                            response_text += "\n\nQual desses horários você prefere?"
                        else:
                            # Se não há horários neste dia, sugerir outros dias
                            alternative_days = time_slot_check.get('alternative_days', [])
                            if alternative_days:
                                response_text += "📅 **Horários disponíveis em outros dias:**\n\n"
                                for alt_day in alternative_days[:3]:
                                    day_date = alt_day.get('date')
                                    day_weekday = alt_day.get('weekday')
                                    day_times = alt_day.get('times', [])
                                    response_text += f"**{day_weekday} ({day_date}):** {', '.join(day_times[:5])}\n"
                                response_text += "\nQual data e horário você prefere?"
                            else:
                                # Evitar "Dr. Dr." - verificar se já tem "Dr." no nome
                                doctor_display = doctor_name if doctor_name.startswith('Dr') else f"Dr. {doctor_name}"
                                response_text += f"Por favor, consulte os horários disponíveis para {doctor_display}."
                        
                        # Retornar resposta sem gerar handoff
                        response_result = {
                            'response': response_text,
                            'intent': 'informar_horario_indisponivel',
                            'confidence': 1.0
                        }
                        
                        # Atualizar sessão (agora sem o horário nas entidades)
                        self.session_manager.update_session(
                            phone_number, session, analysis_result, response_result
                        )
                        
                        # Salvar mensagens no histórico
                        self.session_manager.save_messages(
                            phone_number, message, response_result['response'], analysis_result
                        )
                        
                        return response_result

            # ═══════════════════════════════════════════════════════════════════════════════
            # 9. VERIFICAR SE É CONFIRMAÇÃO DE AGENDAMENTO E GERAR HANDOFF
            # ═══════════════════════════════════════════════════════════════════════════════
            # Este bloco é responsável por:
            # 1. Detectar quando o usuário quer confirmar o agendamento
            # 2. Verificar se todas as informações necessárias foram coletadas
            # 3. Gerar o link de handoff para a secretaria (primeira confirmação)
            # 4. Evitar gerar handoff duplicado se já foi confirmado
            # ═══════════════════════════════════════════════════════════════════════════════
            
            response_result = {}
            if analysis_result['intent'] == 'confirmar_agendamento':
                # Verificar quais informações ainda faltam para o agendamento completo
                # (nome, médico, especialidade, data, horário)
                missing_info_result = conversation_service.get_missing_appointment_info(phone_number)
                
                # ═══════════════════════════════════════════════════════════════════
                # VERIFICAÇÃO ADICIONAL: Se horário ainda não está salvo, não confirmar
                # ═══════════════════════════════════════════════════════════════════
                # Mesmo que missing_info diga que está completo, se preferred_time
                # for None, significa que foi rejeitado e o usuário precisa escolher outro
                # ═══════════════════════════════════════════════════════════════════
                if not session.get('preferred_time'):
                    logger.info("⚠️ Tentativa de confirmar sem horário válido - solicitando escolha de horário")
                    missing_info_result['is_complete'] = False
                    if 'preferred_time' not in missing_info_result['missing_info']:
                        missing_info_result['missing_info'].append('preferred_time')
                
                # Se todas as informações estão completas, podemos prosseguir
                if missing_info_result['is_complete']:
                    
                    # ═══════════════════════════════════════════════════════════════════
                    # VALIDAR DISPONIBILIDADE DO HORÁRIO ESPECÍFICO
                    # ═══════════════════════════════════════════════════════════════════
                    # Antes de gerar o handoff, precisamos verificar se o horário
                    # específico solicitado pelo usuário está realmente disponível
                    # no calendário do médico
                    # ═══════════════════════════════════════════════════════════════════
                    doctor_name = session.get('selected_doctor')
                    requested_date = session.get('preferred_date')
                    requested_time = session.get('preferred_time')
                    
                    if doctor_name and requested_date and requested_time:
                        # Verificar disponibilidade do horário específico
                        logger.info(f"🔍 Validando horário na confirmação: {requested_time} em {requested_date} para {doctor_name}")
                        time_slot_check = smart_scheduling_service.is_time_slot_available(
                            doctor_name=doctor_name,
                            requested_date=requested_date,
                            requested_time=requested_time
                        )
                        
                        logger.info(f"📊 DEBUG - Resultado na confirmação: available={time_slot_check.get('available')}, alternative_times={len(time_slot_check.get('alternative_times', []))} horários")
                        
                        if not time_slot_check.get('available'):
                            # ❌ HORÁRIO NÃO DISPONÍVEL
                            logger.warning(f"⚠️ Horário {requested_time} em {requested_date} não está disponível para {doctor_name}")
                            
                            # IMPORTANTE: Limpar o horário das entidades também para que update_session não o salve novamente
                            entities_to_update = analysis_result.get('entities', {}).copy()
                            if 'horario' in entities_to_update:
                                del entities_to_update['horario']
                            if 'data' in entities_to_update and not session.get('preferred_date'):
                                # Se a data ainda não estava salva, não salvar agora também
                                del entities_to_update['data']
                            analysis_result['entities'] = entities_to_update
                            
                            # Limpar APENAS O HORÁRIO da sessão (manter a data!)
                            session['preferred_time'] = None
                            # NÃO limpar a data: session['preferred_date'] continua com o valor
                            
                            # Atualizar no banco também - APENAS O HORÁRIO
                            db_session = conversation_service.get_or_create_session(phone_number)
                            db_session.preferred_time = None
                            # NÃO limpar a data no banco: db_session.preferred_date continua com o valor
                            db_session.save()
                            
                            # Construir mensagem informativa
                            date_formatted = time_slot_check.get('date_formatted', requested_date)
                            time_formatted = time_slot_check.get('time_formatted', requested_time)
                            weekday = time_slot_check.get('weekday', '')
                            
                            # Formatar mensagem inicial
                            if weekday:
                                response_text = f"❌ O horário {time_formatted} não está disponível para {weekday}, {date_formatted}.\n\n"
                            else:
                                response_text = f"❌ O horário {time_formatted} não está disponível para {date_formatted}.\n\n"
                            
                            # Sugerir horários alternativos
                            alternative_times = time_slot_check.get('alternative_times', [])
                            if alternative_times:
                                weekday_display = weekday if weekday else date_formatted
                                response_text += f"📅 **Horários disponíveis para {weekday_display}:**\n"
                                response_text += "✅ " + ", ".join(alternative_times[:8])  # Mostrar até 8 horários
                                
                                total_alternatives = time_slot_check.get('total_alternatives', len(alternative_times))
                                if total_alternatives > 8:
                                    response_text += f" (+{total_alternatives - 8} outros)"
                                
                                response_text += "\n\nQual desses horários você prefere?"
                            else:
                                # Se não há horários neste dia, sugerir outros dias
                                alternative_days = time_slot_check.get('alternative_days', [])
                                if alternative_days:
                                    response_text += "📅 **Horários disponíveis em outros dias:**\n\n"
                                    for alt_day in alternative_days[:3]:
                                        day_date = alt_day.get('date')
                                        day_weekday = alt_day.get('weekday')
                                        day_times = alt_day.get('times', [])
                                        response_text += f"**{day_weekday} ({day_date}):** {', '.join(day_times[:5])}\n"
                                    response_text += "\nQual data e horário você prefere?"
                                else:
                                    # Evitar "Dr. Dr." - verificar se já tem "Dr." no nome
                                    doctor_display = doctor_name if doctor_name.startswith('Dr') else f"Dr. {doctor_name}"
                                    response_text += f"Por favor, consulte os horários disponíveis para {doctor_display}."
                            
                            # Retornar resposta sem gerar handoff
                            response_result = {
                                'response': response_text,
                                'intent': 'informar_horario_indisponivel',
                                'confidence': 1.0
                            }
                            
                            # Atualizar sessão (agora sem o horário nas entidades)
                            self.session_manager.update_session(
                                phone_number, session, analysis_result, response_result
                            )
                            
                            # Salvar mensagens no histórico
                            self.session_manager.save_messages(
                                phone_number, message, response_result['response'], analysis_result
                            )
                            
                            return response_result
                    
                    # ═══════════════════════════════════════════════════════════════════
                    # HORÁRIO DISPONÍVEL - CONTINUAR COM O HANDOFF
                    # ═══════════════════════════════════════════════════════════════════
                    
                    # ─────────────────────────────────────────────────────────────────
                    # VERIFICAR SE JÁ FOI CONFIRMADO ANTERIORMENTE
                    # ─────────────────────────────────────────────────────────────────
                    # O estado 'confirming' indica que o handoff já foi gerado
                    # Se não estiver neste estado, é a PRIMEIRA confirmação
                    # Se já estiver, é uma CONFIRMAÇÃO DUPLICADA (usuário repetiu)
                    # ─────────────────────────────────────────────────────────────────
                    
                    if session.get('current_state') != 'confirming':
                        # ✅ PRIMEIRA CONFIRMAÇÃO - Processar normalmente
                        logger.info(f"✅ Primeira confirmação detectada - gerando handoff para {phone_number}")
                        
                        # Gerar link de handoff para a secretaria
                        handoff_result = self._handle_appointment_confirmation(
                            phone_number, session, analysis_result
                        )
                        
                        if handoff_result:
                            # Armazenar a mensagem de confirmação e o link do handoff
                            response_result['response'] = handoff_result['message']
                            response_result['handoff_link'] = handoff_result['handoff_link']
                            
                            # Mudar o estado para 'confirming' para indicar que já foi confirmado
                            session['current_state'] = 'confirming'
                            analysis_result['next_state'] = 'confirming'
                            
                            # Atualizar a sessão no banco de dados com o novo estado
                            self.session_manager.update_session(
                                phone_number, session, analysis_result, response_result
                            )
                    
                    else:
                        # ⚠️ CONFIRMAÇÃO DUPLICADA - Usuário já confirmou anteriormente
                        # Não devemos gerar outro handoff, apenas informar que já foi confirmado
                        
                        # ─────────────────────────────────────────────────────────────────
                        # BUSCAR DADOS DA SESSÃO PARA MOSTRAR RESUMO
                        # ─────────────────────────────────────────────────────────────────
                        # Como já foi confirmado, vamos buscar os dados confirmados
                        # e mostrar um resumo amigável ao usuário
                        # ─────────────────────────────────────────────────────────────────
                        
                        patient_name = session.get('patient_name', 'Paciente')
                        doctor = session.get('selected_doctor', 'médico')
                        specialty = session.get('selected_specialty', 'especialidade')
                        date = session.get('preferred_date')
                        time = session.get('preferred_time')
                        
                        # ─────────────────────────────────────────────────────────────────
                        # FORMATAR DATA E HORA PARA EXIBIÇÃO AMIGÁVEL
                        # ─────────────────────────────────────────────────────────────────
                        # Os dados podem estar em formatos diferentes (string ou objeto)
                        # Precisamos normalizar para mostrar ao usuário
                        # ─────────────────────────────────────────────────────────────────
                        
                        if date:
                            try:
                                from datetime import datetime

                                # Se for string, converter para datetime
                                if isinstance(date, str):
                                    date_obj = datetime.fromisoformat(date)
                                    date_str = date_obj.strftime('%d/%m/%Y')
                                else:
                                    # Se já for objeto datetime
                                    date_str = date.strftime('%d/%m/%Y')
                            except Exception as e:
                                logger.warning(f"Erro ao formatar data: {e}")
                                date_str = str(date)
                        else:
                            date_str = 'data a definir'
                        
                        if time:
                            try:
                                # Extrair apenas HH:MM do horário
                                if isinstance(time, str):
                                    time_str = time[:5]  # Pega apenas "HH:MM"
                                else:
                                    time_str = time.strftime('%H:%M')
                            except Exception as e:
                                logger.warning(f"Erro ao formatar horário: {e}")
                                time_str = str(time)
                        else:
                            time_str = 'horário a definir'
                        
                        # ─────────────────────────────────────────────────────────────────
                        # BUSCAR LINK DE HANDOFF ANTERIOR (se existir)
                        # ─────────────────────────────────────────────────────────────────
                        # Se o handoff já foi gerado anteriormente, o link estará
                        # armazenado na sessão. Vamos incluí-lo na resposta caso o
                        # usuário queira vê-lo novamente.
                        # ─────────────────────────────────────────────────────────────────
                        
                        handoff_link = session.get('handoff_link', '')
                        
                        # ─────────────────────────────────────────────────────────────────
                        # GERAR RESPOSTA AMIGÁVEL INFORMANDO QUE JÁ FOI CONFIRMADO
                        # ─────────────────────────────────────────────────────────────────
                        # Esta resposta evita que o Gemini seja chamado e peça
                        # as informações novamente (que era o problema original)
                        # 
                        # Inclui o link de handoff se estiver disponível, permitindo
                        # que o usuário acesse novamente se necessário
                        # ─────────────────────────────────────────────────────────────────
                        
                        response_text = f"""✅ Seu agendamento já foi confirmado anteriormente!

Dados do seu agendamento:
Paciente: {patient_name}
Especialidade: {specialty}
Médico: Dr. {doctor}
Data: {date_str}
Horário: {time_str}

Nossa secretaria entrará em contato em breve para finalizar seu agendamento."""
                        
                        # Adicionar link de handoff se existir
                        if handoff_link:
                            response_text += f"\n\n🔗 Link de confirmação: {handoff_link}"
                        
                        response_text += "\n\nHá algo mais em que posso ajudar? 😊"
                        
                        response_result['response'] = response_text
                        
                        # Se o link existe, incluir no resultado também
                        if handoff_link:
                            response_result['handoff_link'] = handoff_link
                
                else:
                    # ─────────────────────────────────────────────────────────────────
                    # INFORMAÇÕES AINDA INCOMPLETAS
                    # ─────────────────────────────────────────────────────────────────
                    # Se o usuário tentou confirmar mas ainda faltam informações
                    # (ex: falta médico, data, etc), mudamos o intent para continuar
                    # coletando as informações faltantes
                    # ─────────────────────────────────────────────────────────────────
                    
                    logger.info(f"🔄 Informações faltantes para handoff: {missing_info_result['missing_info']}")
                    
                    # Mudar intent para 'agendar_consulta' para continuar coletando dados
                    analysis_result['intent'] = 'agendar_consulta'
                    analysis_result['missing_info'] = missing_info_result['missing_info']
            
            # 9.5. Obter missing_info quando o estado é collecting_patient_info
            # ═══════════════════════════════════════════════════════════════════════════════
            # Quando o estado é collecting_patient_info (ex: após saudação), precisamos
            # obter as informações faltantes para que o response_generator saiba o que perguntar
            # ═══════════════════════════════════════════════════════════════════════════════
            current_state = session.get('current_state', 'idle')
            if current_state == 'collecting_patient_info' and 'missing_info' not in analysis_result:
                logger.info(f"📋 Obtendo informações faltantes para estado collecting_patient_info")
                missing_info_result = conversation_service.get_missing_appointment_info(phone_number)
                analysis_result['missing_info'] = missing_info_result.get('missing_info', [])
                logger.info(f"📋 Informações faltantes: {analysis_result['missing_info']}")
            
            # 10. Gerar resposta se ainda não foi gerada
            if not response_result.get('response'):
                response_result = self.response_generator.generate_response(
                    message, analysis_result, session, conversation_history, clinic_data
                )
                
                # ═══════════════════════════════════════════════════════════════════
                # VERIFICAÇÃO FINAL: Interceptar se Gemini perguntou data sem especialidade
                # ═══════════════════════════════════════════════════════════════════
                response_text = response_result.get('response', '')
                has_specialty = bool(session.get('selected_specialty'))
                has_doctor = bool(session.get('selected_doctor'))
                
                # Verificar se a resposta contém perguntas sobre data/horário sem ter especialidade
                response_lower = response_text.lower()
                asking_date_time = any(keyword in response_lower for keyword in [
                    'data', 'horário', 'horario', 'dia', 'quando', 'qual data', 'qual horário'
                ])
                
                if asking_date_time and not (has_specialty and has_doctor):
                    # Gemini tentou perguntar data/horário sem ter especialidade E médico
                    logger.warning("⚠️ Gemini tentou perguntar data/horário sem especialidade E médico - interceptando")
                    
                    # Determinar o que falta
                    if not has_specialty:
                        # Obter especialidades do médico se tiver médico selecionado
                        if has_doctor:
                            doctor_name = session.get('selected_doctor')
                            # Buscar especialidades do médico (usar clinic_data que já foi carregado)
                            medicos = clinic_data.get('medicos', [])
                            doctor_specialties = []
                            for medico in medicos:
                                if medico.get('nome', '').lower() == doctor_name.lower():
                                    especialidades_medico = medico.get('especialidades_display', '')
                                    if especialidades_medico:
                                        specialties_list_raw = especialidades_medico.replace(';', ',').split(',')
                                        doctor_specialties = [s.strip() for s in specialties_list_raw if s.strip()]
                                    break
                            
                            if doctor_specialties:
                                specialties_display = ', '.join(doctor_specialties)
                                response_result['response'] = f"Para agendar com o {doctor_name}, primeiro preciso saber qual especialidade você precisa. As especialidades disponíveis são: {specialties_display}. Qual especialidade você gostaria?"
                            else:
                                response_result['response'] = f"Para agendar com o {doctor_name}, primeiro preciso saber qual especialidade você precisa. Qual especialidade você gostaria?"
                        else:
                            # Não tem nem médico nem especialidade
                            response_result['response'] = "Para agendar sua consulta, primeiro preciso saber qual especialidade médica você procura. Qual especialidade você gostaria?"
                    elif not has_doctor:
                        # Tem especialidade mas falta médico
                        response_result['response'] = f"Para a especialidade de {session.get('selected_specialty')}, qual médico você prefere?"
                
                # Atualizar sessão com a resposta final
                self.session_manager.update_session(
                    phone_number, session, analysis_result, response_result
                )

            # 10.5. Retomar automaticamente se usuário fornecer informações de agendamento enquanto está em answering_questions
            # IMPORTANTE: Isso é feito DEPOIS da geração da resposta para garantir que dúvidas sejam respondidas primeiro
            if session.get('current_state') == 'answering_questions' and session.get('previous_state'):
                entities = analysis_result.get('entities', {})
                
                # Verificar se há entidades NOVAS de agendamento sendo fornecidas
                # NÃO considerar nome_paciente se já estava na sessão (sempre é extraído)
                has_new_appointment_entities = any([
                    entities.get('medico') and entities.get('medico') != session.get('selected_doctor'),
                    entities.get('especialidade') and entities.get('especialidade') != session.get('selected_specialty'),
                    entities.get('data'),
                    entities.get('horario')
                ])
                
                intent = analysis_result.get('intent', '')
                
                # LÓGICA DE RETOMADA:
                # 1. Se há entidades NOVAS de agendamento (data, horário, médico, especialidade), 
                #    retomar SEMPRE, mesmo que a intenção seja buscar_info ou duvida
                #    (porque o usuário está fornecendo informações, não apenas perguntando)
                # 2. Se a intenção é explicitamente de agendamento, retomar
                # 3. NÃO retomar se é apenas uma pergunta sem entidades de agendamento
                should_resume = False
                
                if has_new_appointment_entities:
                    # Se há entidades de agendamento, retomar independente da intenção
                    # (usuário está fornecendo informações, não apenas perguntando)
                    should_resume = True
                    logger.info(f"🔄 Retomada automática detectada: há entidades de agendamento (data/horário/médico/especialidade) mesmo com intent={intent}")
                elif intent in ['agendar_consulta', 'confirmar_agendamento', 'selecionar_especialidade', 'confirming_name']:
                    # Se a intenção é explicitamente de agendamento, retomar
                    should_resume = True
                
                if should_resume:
                    restored_state = session.get('previous_state')
                    session['current_state'] = restored_state
                    session['previous_state'] = None
                    # Atualizar no banco também
                    db_session = conversation_service.get_or_create_session(phone_number)
                    db_session.current_state = restored_state
                    db_session.previous_state = None
                    db_session.save()
                    logger.info(f"🔄 Retomada automática do agendamento: answering_questions → {restored_state} (usuário forneceu informações de agendamento)")

            # 11. Salvar mensagens no histórico
            self.session_manager.save_messages(
                phone_number, message, response_result['response'], analysis_result
            )   
            
            return response_result
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar mensagem: {e}")
            import traceback
            traceback.print_exc()
            return self._get_fallback_response(message)
    
    def _handle_scheduling_request(self, message: str, session: Dict, 
                                  analysis_result: Dict) -> Dict:
        """
        Processa solicitação de agendamento e verifica disponibilidade real
        
        Baseado no GUIA_SECRETARIA_CALENDAR.md:
        - Consulta Google Calendar em tempo real
        - Filtra eventos por nome do médico (padrão: "Dr. Nome - Tipo")
        - Calcula horários livres baseado nos ocupados
        - Retorna informações de disponibilidade para o paciente
        """
        try:
            logger.info(f"🗓️ Processando solicitação de agendamento")
            
            # Usar o smart_scheduling_service para analisar a solicitação
            scheduling_analysis = smart_scheduling_service.analyze_scheduling_request(
                message, session
            )
            
            logger.info(f"📊 Análise de agendamento: {scheduling_analysis.get('response_type')}")
            
            # Se temos informações suficientes para consultar disponibilidade
            if scheduling_analysis.get('response_type') == 'availability_info':
                # Preservar a mensagem formatada que já vem do analyze_scheduling_request
                formatted_message = scheduling_analysis.get('message')
                availability = scheduling_analysis.get('availability', {})
                
                doctor_info = scheduling_analysis.get('doctor_info')
                if doctor_info and doctor_info.get('nome'):
                    doctor_name = doctor_info['nome']
                    logger.info(f"👨‍⚕️ Consultando disponibilidade para: {doctor_name}")
                    
                    # Se já temos disponibilidade do analyze_scheduling_request, usar ela
                    # Caso contrário, fazer nova consulta
                    if not availability:
                        availability = smart_scheduling_service.get_doctor_availability(
                            doctor_name=doctor_name,
                            days_ahead=7  # Próximos 7 dias
                        )
                    
                    if availability.get('has_availability'):
                        scheduling_analysis['calendar_availability'] = availability
                        scheduling_analysis['has_availability_info'] = True
                        # Preservar mensagem formatada se existir
                        if formatted_message:
                            scheduling_analysis['formatted_availability_message'] = formatted_message
                        logger.info(f"✅ Encontrados {availability['available_slots']} horários disponíveis")
                    else:
                        logger.warning(f"⚠️ Nenhum horário disponível encontrado para {doctor_name}")
                        scheduling_analysis['has_availability_info'] = False
                        # Preservar mensagem formatada mesmo sem disponibilidade
                        if formatted_message:
                            scheduling_analysis['formatted_availability_message'] = formatted_message
            
            return scheduling_analysis
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar solicitação de agendamento: {e}")
            return {
                'response_type': 'error',
                'message': 'Desculpe, ocorreu um erro ao consultar a disponibilidade. Tente novamente.',
                'has_availability_info': False
            }

    def _handle_patient_name_flow(self, phone_number: str, session: Dict, message: str,
                                  analysis_result: Dict) -> Optional[Dict[str, Any]]:
        """Gerencia coleta e confirmação antecipada do nome do paciente."""
        try:
            # Se o nome já está confirmado, não há nada a fazer
            if session.get('patient_name') and session.get('name_confirmed', False):
                return None

            session.setdefault('pending_name', None)
            session.setdefault('name_confirmed', False)

            message_lower = message.lower().strip()
            last_response = (session.get('last_response') or '').lower()

            # ──────────────────────────────────────────────────────────────────────
            # 1) Se estamos aguardando confirmação de um nome pendente
            # ──────────────────────────────────────────────────────────────────────
            if session.get('pending_name'):
                confirmation = conversation_service.confirm_patient_name(phone_number, message)
                status = confirmation.get('status')

                if status == 'confirmed':
                    confirmed_name = confirmation.get('patient_name') or session['pending_name']
                    session['patient_name'] = confirmed_name
                    session['pending_name'] = None
                    session['name_confirmed'] = True

                    # Determinar próximo estado correto baseado no que falta
                    missing_info = conversation_service.get_missing_appointment_info(phone_number)
                    next_action = missing_info.get('next_action', 'ask_general')
                    
                    # Mapear next_action para next_state correto
                    action_to_state = {
                        'ask_specialty': 'selecting_specialty',
                        'ask_doctor': 'selecting_doctor',
                        'ask_date': 'choosing_schedule',
                        'ask_time': 'choosing_schedule',
                        'generate_handoff': 'confirming',
                        'ask_general': 'idle'
                    }
                    next_state = action_to_state.get(next_action, 'idle')
                    
                    # Log de debug caso use o fallback
                    if next_action not in action_to_state:
                        logger.warning(f"⚠️ next_action inesperado: '{next_action}'. Usando fallback 'idle'")

                    analysis_result['intent'] = 'confirmar_nome'
                    analysis_result['next_state'] = next_state
                    analysis_result['entities'] = {'nome_paciente': confirmed_name}
                    logger.info(f"🔄 Próximo estado determinado: {next_state} (baseado em next_action: {next_action})")

                    follow_up = self._build_follow_up_after_name(phone_number, session)
                    response_text = f"Perfeito, {confirmed_name}! {follow_up}"

                    return {
                        'response': response_text,
                        'intent': 'confirmar_nome',
                        'confidence': 1.0
                    }

                if status == 'rejected':
                    session['pending_name'] = None
                    session['patient_name'] = None
                    session['name_confirmed'] = False

                    analysis_result['intent'] = 'confirmar_nome'
                    analysis_result['next_state'] = 'collecting_patient_info'
                    analysis_result['entities'] = {}

                    response_text = confirmation.get(
                        'message',
                        'Tudo bem! Por favor, informe novamente seu nome completo.'
                    )

                    return {
                        'response': response_text,
                        'intent': 'confirmar_nome',
                        'confidence': 0.6
                    }

                if status in ['error', 'name_not_found']:
                    analysis_result['intent'] = 'confirmar_nome'
                    analysis_result['next_state'] = 'collecting_patient_info'
                    analysis_result['entities'] = {}

                    response_text = confirmation.get(
                        'message',
                        'Não consegui confirmar seu nome. Digite novamente seu nome completo, por favor.'
                    )

                    return {
                        'response': response_text,
                        'intent': 'confirmar_nome',
                        'confidence': 0.6
                    }

                # status "no_pending_name" ou outros: seguir fluxo normal
                return None

            # ──────────────────────────────────────────────────────────────────────
            # 2) Se ainda não temos nome confirmado, tentar extrair e confirmar
            # ──────────────────────────────────────────────────────────────────────
            expecting_name = 'nome' in last_response or any(
                keyword in message_lower
                for keyword in ['meu nome', 'me chamo', 'chamo-me', 'nome é', 'sou ']
            )

            if not expecting_name:
                return None

            # PRIORIDADE: Usar o nome já extraído pelo entity_extractor (que está correto)
            # ao invés de chamar conversation_service que usa regex e pode truncar
            extracted_name = None
            entities = analysis_result.get('entities', {})
            
            if entities.get('nome_paciente'):
                # Usar o nome extraído pelo Gemini/entity_extractor (já validado e completo)
                extracted_name = entities['nome_paciente'].strip()
            else:
                # Se entity_extractor não extraiu, pedir nome novamente
                # (EntityExtractor já tentou Gemini + regex interno)
                logger.warning("⚠️ Nome não extraído - solicitando novamente")
                analysis_result['intent'] = 'confirmar_nome'
                analysis_result['next_state'] = 'collecting_patient_info'
                analysis_result['entities'] = {}
                
                return {
                    'response': 'Por favor, informe seu nome completo (nome e sobrenome).',
                    'intent': 'confirmar_nome',
                    'confidence': 0.7
                }
            
            if extracted_name:
                session['pending_name'] = extracted_name
                session['name_confirmed'] = False
                
                # Sincronizar pending_name com o banco imediatamente para garantir que está salvo completo
                try:
                    self.session_manager.sync_to_database(phone_number, session)
                except Exception as e:
                    logger.error(f"Erro ao sincronizar pending_name com banco: {e}")

                analysis_result['intent'] = 'confirmar_nome'
                analysis_result['next_state'] = 'confirming_name'
                # Manter as entidades extraídas (incluindo o nome completo)
                if not analysis_result.get('entities'):
                    analysis_result['entities'] = {}

                response_text = (
                    f"Entendi. Confirma se seu nome completo é {extracted_name}? "
                    "Se estiver correto, responda com 'sim'. Caso contrário, digite novamente seu nome completo."
                )

                return {
                    'response': response_text,
                    'intent': 'confirmar_nome',
                    'confidence': 0.9
                }

            return None

        except Exception as e:
            logger.error(f"Erro ao processar fluxo de confirmação do nome: {e}")
            return None

    def _build_follow_up_after_name(self, phone_number: str, session: Dict) -> str:
        """Gera pergunta apropriada após confirmar o nome do paciente."""
        try:
            missing_info = conversation_service.get_missing_appointment_info(phone_number)
            next_action = missing_info.get('next_action', 'ask_general')

            specialty = session.get('selected_specialty')
            doctor = session.get('selected_doctor')
            date_str = self._format_date_for_user(session.get('preferred_date'))

            if next_action == 'ask_specialty':
                return "Para continuarmos, qual especialidade você deseja consultar?"
            if next_action == 'ask_doctor':
                if specialty:
                    return f"Certo! Qual médico você prefere na especialidade de {specialty}?"
                return "Perfeito! Qual médico você prefere para a sua consulta?"
            if next_action == 'ask_date':
                if doctor:
                    return f"Ótimo! Qual data você prefere para ser atendido pelo Dr. {doctor}?"
                return "Ótimo! Qual data você prefere para a consulta?"
            if next_action == 'ask_time':
                if doctor and date_str:
                    return f"Obrigado! Qual horário funciona melhor para você no dia {date_str} com o Dr. {doctor}?"
                if date_str:
                    return f"Obrigado! Qual horário funciona melhor para você no dia {date_str}?"
                return "Obrigado! Qual horário funciona melhor para você?"

            return "Como posso te ajudar na sequência?"
        except Exception:
            return "Como posso te ajudar na sequência?"

    def _format_date_for_user(self, date_value: Any) -> str:
        """Normaliza datas (string ou date) para formato DD/MM/YYYY amigável."""
        if not date_value:
            return ''
        try:
            from datetime import date, datetime

            if isinstance(date_value, str):
                try:
                    parsed = datetime.fromisoformat(date_value)
                except ValueError:
                    parsed = datetime.strptime(date_value, '%Y-%m-%d')
                return parsed.strftime('%d/%m/%Y')
            if isinstance(date_value, date):
                return date_value.strftime('%d/%m/%Y')
        except Exception:
            return str(date_value)
        return str(date_value)
    
    def _get_clinic_data_optimized(self) -> Dict:
        """Obtém dados da clínica de forma otimizada"""
        try:
            return {
                'clinica_info': self.rag_service.get_clinica_info(),
                'medicos': self.rag_service.get_medicos(),
                'especialidades': self.rag_service.get_especialidades(),
                'convenios': self.rag_service.get_convenios(),
                'telefone': self.rag_service.get_telefone()
            }
        except Exception as e:
            logger.error(f"Erro ao obter dados da clínica: {e}")
            return {}
    
    def _handle_appointment_confirmation(self, phone_number: str, 
                                        session: Dict, analysis_result: Dict) -> Dict:
        """Processa confirmação de agendamento e gera handoff"""
        try:
            # Coletar informações do agendamento
            patient_name = session.get('patient_name', 'Paciente')
            doctor = session.get('selected_doctor', 'Médico a definir')
            specialty = session.get('selected_specialty', 'Especialidade a definir')
            date = session.get('preferred_date', 'Data a definir')
            time = session.get('preferred_time', 'Horário a definir')
            
            # Gerar link de handoff
            handoff_link = handoff_service.generate_appointment_handoff_link(
                patient_name=patient_name,
                doctor_name=doctor,
                specialty=specialty,
                date=date,
                time=time
            )
            
            # Gerar mensagem de confirmação
            confirmation_message = handoff_service.create_confirmation_message(
                doctor_name=doctor,
                specialty=specialty,
                date=date,
                time=time,
                patient_info={'patient_name': patient_name}
            )
            
            # Adicionar o link à mensagem de confirmação
            full_message = f"{confirmation_message}\n{handoff_link}"
            
            logger.info(f"✅ Handoff gerado com sucesso para {phone_number}")
            
            return {
                'message': full_message,
                'handoff_link': handoff_link
            }
            
        except Exception as e:
            logger.error(f"Erro ao processar confirmação: {e}")
            return None
    
    def _get_fallback_response(self, message: str) -> Dict[str, Any]:
        """
        Resposta de fallback quando o serviço não está disponível
        
        Args:
            message: Mensagem do usuário (usado para log)
            
        Returns:
            Dict com resposta de erro
        """
        logger.warning(f"⚠️ Serviço do Gemini indisponível - Mensagem recebida: '{message[:50]}...'")
        
        # Tentar obter telefone da clínica se rag_service estiver disponível
        telefone_info = ""
        try:
            if hasattr(self, 'rag_service') and self.rag_service:
                telefone = self.rag_service.get_telefone()
                if telefone:
                    telefone_info = f" ou entre em contato com o telefone da clínica {telefone}"
        except Exception as e:
            logger.debug(f"Não foi possível obter telefone da clínica: {e}")
        
        return {
            'response': f"Desculpe, estou com dificuldades técnicas no momento. Por favor, tente novamente em alguns instantes{telefone_info}.",
            'intent': 'error',
            'confidence': 0.0
        }
