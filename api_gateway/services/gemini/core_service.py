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
            
            logger.info("✅ Gemini Chatbot Service (Modularizado) inicializado com sucesso")
            
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
            logger.info(f"📱 Processando mensagem de {phone_number}: '{message[:50]}...'")
            logger.info(f"📊 Estado atual da sessão: {session.get('current_state')}")
            
            # 2. Verificar se há agendamento pausado (sistema de dúvidas)
            if conversation_service.has_paused_appointment(phone_number):
                # Detectar palavras-chave para retomar
                if any(keyword in message.lower() for keyword in ['continuar', 'retomar', 'voltar']):
                    conversation_service.resume_appointment(phone_number)
                    return {'response': '✅ Certo! Vamos continuar com seu agendamento. Onde paramos?'}
            
            # 3. Obter histórico e dados da clínica
            conversation_history = self.session_manager.get_conversation_history(phone_number)
            clinic_data = self._get_clinic_data_optimized()
            
            # 4. Detectar intenção (sem entidades)
            intent_result = self.intent_detector.analyze_message(
                message, session, conversation_history, clinic_data
            )
            
            logger.info(f"🔍 Intent detectado: {intent_result['intent']}, Confiança: {intent_result['confidence']}")
            
            # 5. Extrair entidades (método principal - Gemini + Regex fallback)
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

                logger.info(f"✅ Fluxo de confirmação de nome tratado para {phone_number}")
                return response_result

            # 7. Detectar se usuário quer tirar dúvidas durante agendamento
            if analysis_result['intent'] in ['buscar_info', 'duvida']:
                if session['current_state'] not in ['idle', 'answering_questions']:
                    conversation_service.pause_for_question(phone_number)

            # 7.5. Verificar disponibilidade real se for solicitação de agendamento
            if analysis_result['intent'] == 'agendar_consulta':
                scheduling_analysis = self._handle_scheduling_request(
                    message, session, analysis_result
                )
                if scheduling_analysis.get('has_availability_info'):
                    # Se temos informações de disponibilidade, usar na resposta
                    analysis_result['scheduling_info'] = scheduling_analysis
            
            # 8. Atualizar sessão ANTES de verificar informações faltantes
            self.session_manager.update_session(
                phone_number, session, analysis_result, {'response': ''}
            )

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
                
                # Se todas as informações estão completas, podemos prosseguir
                if missing_info_result['is_complete']:
                    
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
                            
                            logger.info(f"🔗 Handoff gerado com sucesso para {phone_number}")
                    
                    else:
                        # ⚠️ CONFIRMAÇÃO DUPLICADA - Usuário já confirmou anteriormente
                        # Não devemos gerar outro handoff, apenas informar que já foi confirmado
                        logger.warning(f"⚠️ Confirmação duplicada detectada para {phone_number} - estado já é 'confirming'")
                        
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

📋 Dados do seu agendamento:
👤 Paciente: {patient_name}
🏥 Especialidade: {specialty}
👨‍⚕️ Médico: Dr. {doctor}
📅 Data: {date_str}
⏰ Horário: {time_str}

Nossa secretaria entrará em contato em breve para finalizar seu agendamento."""
                        
                        # Adicionar link de handoff se existir
                        if handoff_link:
                            response_text += f"\n\n🔗 Link de confirmação: {handoff_link}"
                        
                        response_text += "\n\nHá algo mais em que posso ajudar? 😊"
                        
                        response_result['response'] = response_text
                        
                        # Se o link existe, incluir no resultado também
                        if handoff_link:
                            response_result['handoff_link'] = handoff_link
                        
                        logger.info(f"📤 Resposta de confirmação duplicada gerada para {phone_number}")
                
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
            
            # 10. Gerar resposta se ainda não foi gerada
            if not response_result.get('response'):
                response_result = self.response_generator.generate_response(
                    message, analysis_result, session, conversation_history, clinic_data
                )
                
                # Atualizar sessão com a resposta final
                self.session_manager.update_session(
                    phone_number, session, analysis_result, response_result
                )

            # 11. Salvar mensagens no histórico
            self.session_manager.save_messages(
                phone_number, message, response_result['response'], analysis_result
            )   
            
            logger.info(f"✅ Resposta gerada com sucesso para {phone_number}")
            
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
            logger.info(f"🗓️ Processando solicitação de agendamento: {message[:50]}...")
            
            # Usar o smart_scheduling_service para analisar a solicitação
            scheduling_analysis = smart_scheduling_service.analyze_scheduling_request(
                message, session
            )
            
            logger.info(f"📊 Análise de agendamento: {scheduling_analysis.get('response_type')}")
            
            # Se temos informações suficientes para consultar disponibilidade
            if scheduling_analysis.get('response_type') == 'availability_info':
                doctor_info = scheduling_analysis.get('doctor_info')
                if doctor_info and doctor_info.get('nome'):
                    doctor_name = doctor_info['nome']
                    logger.info(f"👨‍⚕️ Consultando disponibilidade para: {doctor_name}")
                    
                    # Consultar horários disponíveis no Google Calendar
                    availability = smart_scheduling_service.get_doctor_availability(
                        doctor_name=doctor_name,
                        days_ahead=7  # Próximos 7 dias
                    )
                    
                    if availability.get('has_availability'):
                        scheduling_analysis['calendar_availability'] = availability
                        scheduling_analysis['has_availability_info'] = True
                        logger.info(f"✅ Encontrados {availability['available_slots']} horários disponíveis")
                    else:
                        logger.warning(f"⚠️ Nenhum horário disponível encontrado para {doctor_name}")
                        scheduling_analysis['has_availability_info'] = False
            
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
                    logger.info(f"📝 Confirmando nome: '{confirmed_name}' (tamanho: {len(confirmed_name) if confirmed_name else 0}, palavras: {len(confirmed_name.split()) if confirmed_name else 0})")
                    session['patient_name'] = confirmed_name
                    session['pending_name'] = None
                    session['name_confirmed'] = True

                    analysis_result['intent'] = 'confirmar_nome'
                    analysis_result['next_state'] = 'collecting_info'
                    analysis_result['entities'] = {'nome_paciente': confirmed_name}
                    logger.info(f"✅ Nome confirmado e salvo: '{confirmed_name}' (tamanho: {len(confirmed_name) if confirmed_name else 0})")

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
                logger.info(f"✅ Usando nome extraído pelo entity_extractor: '{extracted_name}' (tamanho: {len(extracted_name)}, palavras: {len(extracted_name.split())})")
            else:
                # Fallback: se entity_extractor não extraiu, tentar com conversation_service
                logger.warning("⚠️ Entity extractor não extraiu nome, usando fallback do conversation_service")
                name_processing = conversation_service.process_patient_name(phone_number, message)
                status = name_processing.get('status')
                
                if status == 'confirmation_needed':
                    extracted_name = name_processing.get('extracted_name')
                elif status == 'name_not_found':
                    analysis_result['intent'] = 'confirmar_nome'
                    analysis_result['next_state'] = 'collecting_patient_info'
                    analysis_result['entities'] = {}
                    
                    response_text = name_processing.get(
                        'message',
                        'Por favor, informe seu nome completo (nome e sobrenome).'
                    )
                    
                    return {
                        'response': response_text,
                        'intent': 'confirmar_nome',
                        'confidence': 0.7
                    }
                elif status == 'error':
                    analysis_result['intent'] = 'confirmar_nome'
                    analysis_result['next_state'] = 'collecting_patient_info'
                    analysis_result['entities'] = {}
                    
                    return {
                        'response': name_processing.get('message', 'Tive um problema ao entender seu nome. Pode informar novamente?'),
                        'intent': 'confirmar_nome',
                        'confidence': 0.5
                    }
            
            if extracted_name:
                logger.info(f"📝 Nome extraído para confirmação: '{extracted_name}' (tamanho: {len(extracted_name)}, palavras: {len(extracted_name.split())})")
                session['pending_name'] = extracted_name
                session['name_confirmed'] = False
                
                # Sincronizar pending_name com o banco imediatamente para garantir que está salvo completo
                try:
                    self.session_manager.sync_to_database(phone_number, session)
                    logger.info(f"💾 pending_name sincronizado com banco: '{extracted_name}'")
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
            logger.info(f"🔗 Link: {handoff_link}")
            
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
        
        return {
            'response': f"Desculpe, estou com dificuldades técnicas no momento. Por favor, tente novamente em alguns instantes ou entre em contato com o telefone da clínica {self.rag_service.get_telefone()}",
            'intent': 'error',
            'confidence': 0.0
        }
    
    def test_connection(self) -> Dict[str, Any]:
        """Testa a conexão com o Gemini (método de compatibilidade)"""
        try:
            if not self.enabled:
                return {
                    'success': False,
                    'message': 'Gemini está desabilitado',
                    'details': 'GEMINI_ENABLED=False ou GEMINI_API_KEY não configurada'
                }
            
            # Testar com uma mensagem simples
            test_response = self.process_message(
                phone_number="+5511999999999",
                message="teste"
            )
            
            return {
                'success': True,
                'message': 'Conexão com Gemini funcionando',
                'details': f'Resposta de teste: {test_response.get("response", "")[:50]}...'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Erro na conexão com Gemini: {str(e)}',
                'details': str(e)
            }

