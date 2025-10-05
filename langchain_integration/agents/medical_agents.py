"""
Agents Médicos LangChain
Sistema de agents inteligentes para decisões complexas
"""
import json
import logging
from typing import Any, Dict, List, Optional

from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool
from langchain_core.language_models import BaseLanguageModel
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from ..compatibility_service import compatibility_rag_service
from ..config import LANGCHAIN_CONFIG

logger = logging.getLogger(__name__)


class MedicalAgentTools:
    """
    Ferramentas para agents médicos
    """
    
    def __init__(self):
        self.rag_service = compatibility_rag_service
    
    def search_doctors(self, query: str) -> str:
        """
        Busca médicos baseado em critérios
        
        Args:
            query: Critérios de busca (especialidade, nome, etc.)
            
        Returns:
            Lista de médicos encontrados
        """
        try:
            doctors = self.rag_service.get_doctors(query)
            
            if not doctors:
                return "Nenhum médico encontrado com os critérios fornecidos."
            
            result = "Médicos encontrados:\n"
            for doctor in doctors[:5]:  # Limitar a 5 médicos
                name = doctor.get('nome', 'Nome não informado')
                specialties = doctor.get('especialidades_display', 'Especialidade não informada')
                price = doctor.get('preco_particular', 'Preço não informado')
                result += f"- {name}: {specialties} (Particular: R$ {price})\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Erro na busca de médicos: {e}")
            return f"Erro ao buscar médicos: {str(e)}"
    
    def search_exams(self, query: str) -> str:
        """
        Busca exames baseado em critérios
        
        Args:
            query: Critérios de busca (tipo, nome, etc.)
            
        Returns:
            Lista de exames encontrados
        """
        try:
            exams = self.rag_service.get_exams(query)
            
            if not exams:
                return "Nenhum exame encontrado com os critérios fornecidos."
            
            result = "Exames encontrados:\n"
            for exam in exams[:5]:  # Limitar a 5 exames
                name = exam.get('nome', 'Nome não informado')
                price = exam.get('preco', 'Preço não informado')
                duration = exam.get('duracao_formatada', 'Duração não informada')
                result += f"- {name}: R$ {price} ({duration})\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Erro na busca de exames: {e}")
            return f"Erro ao buscar exames: {str(e)}"
    
    def search_specialties(self, query: str) -> str:
        """
        Busca especialidades médicas
        
        Args:
            query: Critérios de busca
            
        Returns:
            Lista de especialidades encontradas
        """
        try:
            specialties = self.rag_service.get_specialties(query)
            
            if not specialties:
                return "Nenhuma especialidade encontrada com os critérios fornecidos."
            
            result = "Especialidades encontradas:\n"
            for specialty in specialties[:5]:  # Limitar a 5 especialidades
                name = specialty.get('nome', 'Nome não informado')
                description = specialty.get('descricao', 'Descrição não informada')
                result += f"- {name}: {description}\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Erro na busca de especialidades: {e}")
            return f"Erro ao buscar especialidades: {str(e)}"
    
    def get_clinic_info(self, query: str = "") -> str:
        """
        Obtém informações da clínica
        
        Args:
            query: Tipo de informação solicitada
            
        Returns:
            Informações da clínica
        """
        try:
            clinic_info = self.rag_service.get_clinic_info(query)
            
            if not clinic_info:
                return "Informações da clínica não disponíveis."
            
            result = "Informações da Clínica:\n"
            result += f"Nome: {clinic_info.get('nome', 'Não informado')}\n"
            result += f"Endereço: {clinic_info.get('endereco', 'Não informado')}\n"
            result += f"Telefone: {clinic_info.get('telefone_contato', 'Não informado')}\n"
            result += f"WhatsApp: {clinic_info.get('whatsapp_contato', 'Não informado')}\n"
            result += f"Horário: {clinic_info.get('horario_funcionamento', 'Não informado')}\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Erro ao obter informações da clínica: {e}")
            return f"Erro ao obter informações da clínica: {str(e)}"
    
    def check_availability(self, doctor_name: str, date: str = "") -> str:
        """
        Verifica disponibilidade de um médico
        
        Args:
            doctor_name: Nome do médico
            date: Data específica (opcional)
            
        Returns:
            Informações de disponibilidade
        """
        try:
            # Por enquanto, retornar informação genérica
            # Em implementação futura, integrar com Google Calendar
            return f"Para verificar a disponibilidade do Dr. {doctor_name}, entre em contato conosco pelo WhatsApp ou telefone."
            
        except Exception as e:
            logger.error(f"Erro ao verificar disponibilidade: {e}")
            return f"Erro ao verificar disponibilidade: {str(e)}"
    
    def create_appointment_request(self, patient_name: str, doctor_name: str, 
                                 date: str, time: str) -> str:
        """
        Cria solicitação de agendamento
        
        Args:
            patient_name: Nome do paciente
            doctor_name: Nome do médico
            date: Data desejada
            time: Horário desejado
            
        Returns:
            Confirmação da solicitação
        """
        try:
            # Por enquanto, retornar confirmação genérica
            # Em implementação futura, integrar com sistema de agendamento
            return f"Solicitação de agendamento criada:\nPaciente: {patient_name}\nMédico: {doctor_name}\nData: {date}\nHorário: {time}\n\nNossa equipe entrará em contato para confirmar a disponibilidade."
            
        except Exception as e:
            logger.error(f"Erro ao criar solicitação de agendamento: {e}")
            return f"Erro ao criar solicitação de agendamento: {str(e)}"
    
    def get_tools(self) -> List[Tool]:
        """
        Retorna lista de ferramentas disponíveis
        
        Returns:
            Lista de ferramentas
        """
        return [
            Tool(
                name="search_doctors",
                description="Busca médicos por especialidade, nome ou outros critérios. Use quando o paciente perguntar sobre médicos específicos ou especialidades.",
                func=self.search_doctors
            ),
            Tool(
                name="search_exams",
                description="Busca exames e procedimentos disponíveis. Use quando o paciente perguntar sobre exames específicos.",
                func=self.search_exams
            ),
            Tool(
                name="search_specialties",
                description="Busca especialidades médicas disponíveis. Use quando o paciente perguntar sobre especialidades.",
                func=self.search_specialties
            ),
            Tool(
                name="get_clinic_info",
                description="Obtém informações gerais da clínica como endereço, telefone, horários. Use quando o paciente perguntar sobre informações da clínica.",
                func=self.get_clinic_info
            ),
            Tool(
                name="check_availability",
                description="Verifica disponibilidade de horários de um médico específico. Use quando o paciente quiser verificar horários disponíveis.",
                func=self.check_availability
            ),
            Tool(
                name="create_appointment_request",
                description="Cria uma solicitação de agendamento com os dados fornecidos. Use quando o paciente quiser agendar uma consulta.",
                func=self.create_appointment_request
            )
        ]


class MedicalAgentManager:
    """
    Gerenciador de Agents Médicos
    
    Responsabilidades:
    1. Gerenciar agents inteligentes
    2. Coordenar decisões complexas
    3. Integrar com ferramentas
    4. Gerenciar fluxos de conversação
    """
    
    def __init__(self):
        self.llm = self._initialize_llm()
        self.tools = MedicalAgentTools()
        self.agent = None
        self.agent_executor = None
        self._create_agent()
    
    def _initialize_llm(self) -> BaseLanguageModel:
        """Inicializa o modelo de linguagem"""
        try:
            llm = ChatGoogleGenerativeAI(
                model=LANGCHAIN_CONFIG['GEMINI_MODEL'],
                google_api_key=LANGCHAIN_CONFIG['GEMINI_API_KEY'],
                temperature=LANGCHAIN_CONFIG['TEMPERATURE'],
                max_output_tokens=LANGCHAIN_CONFIG['MAX_TOKENS']
            )
            logger.info("✅ LLM para agents inicializado com sucesso")
            return llm
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar LLM para agents: {e}")
            raise
    
    def _create_agent(self):
        """Cria agent médico"""
        try:
            # Usar o prompt padrão do ReAct e customizar apenas o prefixo
            from langchain.agents import create_react_agent
            from langchain import hub
            
            # Tentar obter o prompt do ReAct do hub
            try:
                agent_prompt = hub.pull("hwchase17/react")
            except:
                # Se não conseguir do hub, usar prompt padrão
                from langchain.agents import PromptTemplate
                agent_prompt = PromptTemplate.from_template("""
Você é um assistente virtual especializado em agendamentos médicos da Clínica PneumoSono.

Você tem acesso às seguintes ferramentas:

{tools}

Use o seguinte formato:

Question: a pergunta de entrada que você deve responder
Thought: você deve sempre pensar sobre o que fazer
Action: a ação a ser tomada, deve ser uma das [{tool_names}]
Action Input: a entrada para a ação
Observation: o resultado da ação
... (este Thought/Action/Action Input/Observation pode repetir N vezes)
Thought: agora sei a resposta final
Final Answer: a resposta final para a pergunta de entrada

Question: {input}
Thought: {agent_scratchpad}
                """)
            
            # Criar agent
            self.agent = create_react_agent(
                llm=self.llm,
                tools=self.tools.get_tools(),
                prompt=agent_prompt
            )
            
            # Criar executor
            self.agent_executor = AgentExecutor(
                agent=self.agent,
                tools=self.tools.get_tools(),
                verbose=True,
                max_iterations=3,
                handle_parsing_errors=True
            )
            
            logger.info("✅ Agent médico criado com sucesso")
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar agent médico: {e}")
            raise
    
    def process_complex_request(self, phone_number: str, message: str, 
                              session: Dict, clinic_data: Dict) -> Dict[str, Any]:
        """
        Processa solicitações complexas usando agent
        
        Args:
            phone_number: Número do telefone
            message: Mensagem do usuário
            session: Dados da sessão
            clinic_data: Dados da clínica
            
        Returns:
            Resultado do processamento
        """
        try:
            # Preparar contexto
            clinic_name = clinic_data.get('clinica_info', {}).get('nome', 'Clínica Médica')
            
            # Obter histórico da conversa
            from ..memory.conversation_memory import memory_manager
            conversation_history = memory_manager.get_conversation_history(phone_number, 5)
            
            # Formatar histórico para o agent
            chat_history = self._format_chat_history(conversation_history)
            
            # Executar agent
            result = self.agent_executor.invoke({
                'input': message,
                'clinic_name': clinic_name,
                'chat_history': chat_history
            })
            
            # Processar resultado
            response = result.get('output', 'Desculpe, não consegui processar sua solicitação.')
            
            # Determinar intenção baseada na resposta
            intent = self._determine_intent_from_response(response, message)
            
            # Adicionar mensagens à memória
            memory_manager.add_user_message(phone_number, message)
            memory_manager.add_ai_message(phone_number, response)
            
            # Sincronizar com banco de dados
            memory_manager.sync_with_database(phone_number)
            
            return {
                'response': response,
                'intent': intent,
                'confidence': 0.9,  # Agents têm alta confiança
                'state': session.get('current_state', 'idle'),
                'session_data': session,
                'analysis': {
                    'intent': intent,
                    'confidence': 0.9,
                    'entities': {},
                    'reasoning': 'Processado por agent médico'
                },
                'agent': 'medical_agent',
                'tools_used': result.get('intermediate_steps', [])
            }
            
        except Exception as e:
            logger.error(f"❌ Erro no processamento do agent: {e}")
            return self._get_fallback_result(message)
    
    def _format_chat_history(self, conversation_history: List[Dict]) -> str:
        """Formata histórico da conversa para o agent"""
        if not conversation_history:
            return "Nenhum histórico de conversa disponível."
        
        formatted = "Histórico da conversa:\n"
        for msg in conversation_history[-5:]:  # Últimas 5 mensagens
            role = "Paciente" if msg.get('is_user') else "Assistente"
            content = msg.get('content', '')
            formatted += f"- {role}: {content}\n"
        
        return formatted
    
    def _determine_intent_from_response(self, response: str, original_message: str) -> str:
        """Determina intenção baseada na resposta do agent"""
        response_lower = response.lower()
        message_lower = original_message.lower()
        
        # Análise baseada em palavras-chave na resposta
        if any(word in response_lower for word in ['agendamento', 'agendar', 'consulta', 'marcar']):
            return 'agendar_consulta'
        elif any(word in response_lower for word in ['médico', 'doutor', 'especialista']):
            return 'buscar_medico'
        elif any(word in response_lower for word in ['exame', 'procedimento', 'teste']):
            return 'buscar_exame'
        elif any(word in response_lower for word in ['endereço', 'telefone', 'horário', 'funcionamento']):
            return 'buscar_info'
        elif any(word in response_lower for word in ['especialidade', 'área']):
            return 'buscar_especialidade'
        else:
            return 'duvida'
    
    def _get_fallback_result(self, message: str) -> Dict[str, Any]:
        """Resultado de fallback"""
        return {
            'response': "Desculpe, estou temporariamente indisponível. Como posso ajudá-lo?",
            'intent': 'duvida',
            'confidence': 0.5,
            'state': 'idle',
            'session_data': {},
            'analysis': {'intent': 'duvida', 'confidence': 0.5},
            'agent': 'fallback',
            'tools_used': []
        }
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do agent"""
        try:
            return {
                'total_tools': len(self.tools.get_tools()),
                'available_tools': [tool.name for tool in self.tools.get_tools()],
                'llm_model': LANGCHAIN_CONFIG['GEMINI_MODEL'],
                'max_iterations': 3,
                'status': 'active'
            }
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas do agent: {e}")
            return {'error': str(e)}


# Instância global do gerenciador de agents
agent_manager = MedicalAgentManager()
