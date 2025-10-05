"""
Chains de Conversação LangChain
Sistema para gerenciar fluxos complexos de conversação
"""
import json
import logging
from typing import Any, Dict, List, Optional

from langchain_core.chains import LLMChain
from langchain_core.language_models import BaseLanguageModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from ..config import LANGCHAIN_CONFIG
from ..memory.conversation_memory import memory_manager
from ..prompts.template_manager import template_manager

logger = logging.getLogger(__name__)


class ConversationChainManager:
    """
    Gerenciador de Chains para conversação
    
    Responsabilidades:
    1. Gerenciar chains de conversação
    2. Coordenar fluxos complexos
    3. Integrar memória e templates
    4. Gerenciar estados de conversa
    """
    
    def __init__(self):
        self.llm = self._initialize_llm()
        self.chains = {}
        self._create_chains()
    
    def _initialize_llm(self) -> BaseLanguageModel:
        """Inicializa o modelo de linguagem"""
        try:
            llm = ChatGoogleGenerativeAI(
                model=LANGCHAIN_CONFIG['GEMINI_MODEL'],
                google_api_key=LANGCHAIN_CONFIG['GEMINI_API_KEY'],
                temperature=LANGCHAIN_CONFIG['TEMPERATURE'],
                max_output_tokens=LANGCHAIN_CONFIG['MAX_TOKENS']
            )
            logger.info("✅ LLM inicializado com sucesso")
            return llm
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar LLM: {e}")
            raise
    
    def _create_chains(self):
        """Cria chains de conversação"""
        try:
            # Chain de análise de mensagem
            self.chains['analysis'] = LLMChain(
                llm=self.llm,
                prompt=template_manager.templates.ANALYSIS_PROMPT,
                output_key='analysis_result'
            )
            
            # Chain de geração de resposta
            self.chains['response'] = LLMChain(
                llm=self.llm,
                prompt=template_manager.templates.RESPONSE_PROMPT,
                output_key='response_text'
            )
            
            # Chain de confirmação de agendamento
            self.chains['confirmation'] = LLMChain(
                llm=self.llm,
                prompt=template_manager.templates.APPOINTMENT_CONFIRMATION_PROMPT,
                output_key='confirmation_text'
            )
            
            # Chain de busca de informações
            self.chains['info_search'] = LLMChain(
                llm=self.llm,
                prompt=template_manager.templates.INFO_SEARCH_PROMPT,
                output_key='info_text'
            )
            
            # Chain de saudação
            self.chains['greeting'] = LLMChain(
                llm=self.llm,
                prompt=template_manager.templates.GREETING_PROMPT,
                output_key='greeting_text'
            )
            
            # Chain de despedida
            self.chains['farewell'] = LLMChain(
                llm=self.llm,
                prompt=template_manager.templates.FAREWELL_PROMPT,
                output_key='farewell_text'
            )
            
            logger.info("✅ Chains de conversação criadas com sucesso")
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar chains: {e}")
            raise
    
    def process_message(self, phone_number: str, message: str, 
                      session: Dict, clinic_data: Dict) -> Dict[str, Any]:
        """
        Processa mensagem usando chains de conversação
        
        Args:
            phone_number: Número do telefone
            message: Mensagem do usuário
            session: Dados da sessão
            clinic_data: Dados da clínica
            
        Returns:
            Resultado do processamento
        """
        try:
            # Adicionar mensagem do usuário à memória
            memory_manager.add_user_message(phone_number, message)
            
            # Obter histórico da conversa
            conversation_history = memory_manager.get_conversation_history(phone_number)
            
            # 1. Análise da mensagem
            analysis_result = self._analyze_message(
                message, session, conversation_history, clinic_data
            )
            
            # 2. Geração de resposta baseada na intenção
            response_result = self._generate_response(
                message, analysis_result, session, conversation_history, clinic_data
            )
            
            # 3. Adicionar resposta da IA à memória
            memory_manager.add_ai_message(phone_number, response_result['response'])
            
            # 4. Sincronizar com banco de dados
            memory_manager.sync_with_database(phone_number)
            
            # 5. Preparar resultado final
            result = {
                'response': response_result['response'],
                'intent': analysis_result['intent'],
                'confidence': analysis_result['confidence'],
                'state': analysis_result['next_state'],
                'session_data': session,
                'analysis': analysis_result,
                'agent': 'langchain_chains',
                'memory_stats': memory_manager.get_memory_stats(phone_number)
            }
            
            logger.info(f"🔗 Chain processou mensagem: {analysis_result['intent']} - {analysis_result['confidence']:.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro no processamento da chain: {e}")
            return self._get_fallback_result(message)
    
    def _analyze_message(self, message: str, session: Dict, 
                        conversation_history: List, clinic_data: Dict) -> Dict[str, Any]:
        """
        Analisa mensagem usando chain de análise
        """
        try:
            # Preparar dados para o template
            template_data = {
                'message': message,
                'current_state': session.get('current_state', 'idle'),
                'patient_name': session.get('patient_name', 'Não informado'),
                'selected_doctor': session.get('selected_doctor', 'Não selecionado'),
                'conversation_history': template_manager._format_conversation_history(conversation_history),
                'clinic_name': clinic_data.get('clinica_info', {}).get('nome', 'clínica médica'),
                'specialties': ', '.join([esp.get('nome', '') for esp in clinic_data.get('especialidades', [])[:5]]),
                'doctors': ', '.join([med.get('nome', '') for med in clinic_data.get('medicos', [])[:3]])
            }
            
            # Executar chain de análise
            result = self.chains['analysis'].run(**template_data)
            
            # Extrair análise da resposta
            analysis = self._extract_analysis_from_response(result)
            analysis['original_message'] = message
            
            return analysis
            
        except Exception as e:
            logger.error(f"Erro na análise da mensagem: {e}")
            return self._get_fallback_analysis(message, session)
    
    def _generate_response(self, message: str, analysis_result: Dict,
                          session: Dict, conversation_history: List,
                          clinic_data: Dict) -> Dict[str, Any]:
        """
        Gera resposta usando chain de resposta
        """
        try:
            intent = analysis_result['intent']
            
            # Escolher chain baseado na intenção
            if intent == 'confirmar_agendamento':
                return self._handle_appointment_confirmation(
                    message, analysis_result, session, clinic_data
                )
            elif intent in ['buscar_info', 'buscar_medico', 'buscar_exame', 'buscar_horarios']:
                return self._handle_info_search(
                    message, analysis_result, session, clinic_data
                )
            elif intent == 'saudacao':
                return self._handle_greeting(
                    message, analysis_result, session, clinic_data
                )
            elif intent == 'despedida':
                return self._handle_farewell(
                    message, analysis_result, session, clinic_data
                )
            else:
                return self._handle_general_response(
                    message, analysis_result, session, conversation_history, clinic_data
                )
                
        except Exception as e:
            logger.error(f"Erro na geração de resposta: {e}")
            return self._get_fallback_response(message)
    
    def _handle_appointment_confirmation(self, message: str, analysis_result: Dict,
                                       session: Dict, clinic_data: Dict) -> Dict[str, Any]:
        """Processa confirmação de agendamento"""
        try:
            entities = analysis_result.get('entities', {})
            clinic_name = clinic_data.get('clinica_info', {}).get('nome', 'Clínica Médica')
            
            # Extrair dados do agendamento
            patient_name = entities.get('nome_paciente') or session.get('patient_name', 'Paciente')
            doctor_name = entities.get('medico') or session.get('selected_doctor', 'Médico')
            appointment_date = entities.get('data') or session.get('preferred_date', 'Data a definir')
            appointment_time = entities.get('horario') or session.get('preferred_time', 'Horário a definir')
            
            # Executar chain de confirmação
            result = self.chains['confirmation'].run(
                clinic_name=clinic_name,
                patient_name=patient_name,
                doctor_name=doctor_name,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                appointment_type='Consulta'
            )
            
            return {
                'response': result,
                'intent': 'confirmar_agendamento',
                'confidence': analysis_result['confidence']
            }
            
        except Exception as e:
            logger.error(f"Erro na confirmação de agendamento: {e}")
            return self._get_fallback_response(message)
    
    def _handle_info_search(self, message: str, analysis_result: Dict,
                           session: Dict, clinic_data: Dict) -> Dict[str, Any]:
        """Processa busca de informações"""
        try:
            # Executar chain de busca de informações
            result = self.chains['info_search'].run(
                query=message,
                clinic_data=template_manager._format_clinic_data_for_prompt(clinic_data)
            )
            
            return {
                'response': result,
                'intent': analysis_result['intent'],
                'confidence': analysis_result['confidence']
            }
            
        except Exception as e:
            logger.error(f"Erro na busca de informações: {e}")
            return self._get_fallback_response(message)
    
    def _handle_greeting(self, message: str, analysis_result: Dict,
                        session: Dict, clinic_data: Dict) -> Dict[str, Any]:
        """Processa saudação"""
        try:
            # Executar chain de saudação
            result = self.chains['greeting'].run(
                clinic_name=clinic_data.get('clinica_info', {}).get('nome', 'Clínica Médica'),
                specialties=', '.join([esp.get('nome', '') for esp in clinic_data.get('especialidades', [])[:3]]),
                clinic_hours=clinic_data.get('clinica_info', {}).get('horario_funcionamento', 'Horário não informado')
            )
            
            return {
                'response': result,
                'intent': 'saudacao',
                'confidence': analysis_result['confidence']
            }
            
        except Exception as e:
            logger.error(f"Erro na saudação: {e}")
            return self._get_fallback_response(message)
    
    def _handle_farewell(self, message: str, analysis_result: Dict,
                        session: Dict, clinic_data: Dict) -> Dict[str, Any]:
        """Processa despedida"""
        try:
            clinic_name = clinic_data.get('clinica_info', {}).get('nome', 'Clínica Médica')
            patient_name = session.get('patient_name', 'Paciente')
            
            # Executar chain de despedida
            result = self.chains['farewell'].run(
                clinic_name=clinic_name,
                patient_name=patient_name,
                appointment_status='em_andamento'
            )
            
            return {
                'response': result,
                'intent': 'despedida',
                'confidence': analysis_result['confidence']
            }
            
        except Exception as e:
            logger.error(f"Erro na despedida: {e}")
            return self._get_fallback_response(message)
    
    def _handle_general_response(self, message: str, analysis_result: Dict,
                                session: Dict, conversation_history: List,
                                clinic_data: Dict) -> Dict[str, Any]:
        """Processa resposta geral"""
        try:
            # Preparar dados para o template
            template_data = {
                'message': message,
                'current_state': session.get('current_state', 'idle'),
                'next_state': analysis_result.get('next_state', 'idle'),
                'intent': analysis_result['intent'],
                'patient_name': session.get('patient_name', 'Não informado'),
                'selected_doctor': session.get('selected_doctor', 'Não selecionado'),
                'clinic_name': clinic_data.get('clinica_info', {}).get('nome', 'Clínica Médica'),
                'clinic_address': clinic_data.get('clinica_info', {}).get('endereco', 'Endereço não informado'),
                'clinic_phone': clinic_data.get('clinica_info', {}).get('telefone_contato', 'Telefone não informado'),
                'clinic_whatsapp': clinic_data.get('clinica_info', {}).get('whatsapp_contato', 'WhatsApp não informado'),
                'doctors_info': template_manager._format_doctors_for_prompt(clinic_data.get('medicos', [])),
                'specialties_info': template_manager._format_specialties_for_prompt(clinic_data.get('especialidades', [])),
                'exams_info': template_manager._format_exams_for_prompt(clinic_data.get('exames', [])),
                'intent_instructions': template_manager.intent_instructions.get_instructions(analysis_result['intent'])
            }
            
            # Executar chain de resposta
            result = self.chains['response'].run(**template_data)
            
            return {
                'response': result,
                'intent': analysis_result['intent'],
                'confidence': analysis_result['confidence']
            }
            
        except Exception as e:
            logger.error(f"Erro na resposta geral: {e}")
            return self._get_fallback_response(message)
    
    def _extract_analysis_from_response(self, response_text: str) -> Dict[str, Any]:
        """Extrai análise da resposta do LLM"""
        try:
            # Limpar resposta
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].strip()
            
            # Parsear JSON
            analysis = json.loads(response_text)
            
            # Validar campos obrigatórios
            required_fields = ['intent', 'next_state', 'entities', 'confidence']
            for field in required_fields:
                if field not in analysis:
                    raise ValueError(f"Campo obrigatório '{field}' não encontrado")
            
            # Validar entidades
            if not isinstance(analysis['entities'], dict):
                analysis['entities'] = {}
            
            # Limpar entidades de valores "null" ou vazios
            cleaned_entities = {}
            for key, value in analysis['entities'].items():
                if value and str(value).lower() not in ['null', 'none', '']:
                    cleaned_entities[key] = str(value).strip()
            
            analysis['entities'] = cleaned_entities
            
            # Validar confiança
            confidence = float(analysis.get('confidence', 0.5))
            if not 0.0 <= confidence <= 1.0:
                confidence = 0.5
            
            analysis['confidence'] = confidence
            
            return analysis
            
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.warning(f"Erro ao parsear análise: {e}")
            return self._get_fallback_analysis("", {})
    
    def _get_fallback_analysis(self, message: str, session: Dict) -> Dict[str, Any]:
        """Análise de fallback"""
        message_lower = message.lower()
        
        # Análise simples baseada em palavras-chave
        if any(word in message_lower for word in ['oi', 'olá', 'ola', 'bom dia', 'boa tarde', 'boa noite']):
            intent = 'saudacao'
            next_state = 'coletando_nome'
        elif any(word in message_lower for word in ['agendar', 'marcar', 'consulta', 'horário']):
            intent = 'agendar_consulta'
            next_state = 'coletando_nome'
        elif any(word in message_lower for word in ['médico', 'medicos', 'doutor', 'doutora']):
            intent = 'buscar_medico'
            next_state = 'fornecendo_info'
        elif any(word in message_lower for word in ['exame', 'exames', 'procedimento']):
            intent = 'buscar_exame'
            next_state = 'fornecendo_info'
        elif any(word in message_lower for word in ['endereço', 'endereco', 'telefone', 'contato']):
            intent = 'buscar_info'
            next_state = 'fornecendo_info'
        else:
            intent = 'duvida'
            next_state = session.get('current_state', 'idle')

        return {
            'intent': intent,
            'next_state': next_state,
            'entities': {},
            'confidence': 0.6,
            'reasoning': 'Análise de fallback baseada em palavras-chave'
        }
    
    def _get_fallback_response(self, message: str) -> Dict[str, Any]:
        """Resposta de fallback"""
        return {
            'response': "Desculpe, estou temporariamente indisponível. Como posso ajudá-lo?",
            'intent': 'duvida',
            'confidence': 0.5
        }
    
    def _get_fallback_result(self, message: str) -> Dict[str, Any]:
        """Resultado de fallback completo"""
        return {
            'response': "Desculpe, estou temporariamente indisponível. Como posso ajudá-lo?",
            'intent': 'duvida',
            'confidence': 0.5,
            'state': 'idle',
            'session_data': {},
            'analysis': {'intent': 'duvida', 'confidence': 0.5},
            'agent': 'fallback',
            'memory_stats': {'error': 'Memória indisponível'}
        }
    
    def get_chain_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas das chains"""
        try:
            return {
                'total_chains': len(self.chains),
                'available_chains': list(self.chains.keys()),
                'llm_model': LANGCHAIN_CONFIG['GEMINI_MODEL'],
                'status': 'active'
            }
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas das chains: {e}")
            return {'error': str(e)}


# Instância global do gerenciador de chains
chain_manager = ConversationChainManager()
