"""
Serviço Gemini Centralizado - Protagonista Principal do Chatbot
Gerencia todo o fluxo de conversação e responde pacientes com base no RAG
"""
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

import google.generativeai as genai
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from .rag_service import RAGService
from .smart_scheduling_service import smart_scheduling_service

logger = logging.getLogger(__name__)


class GeminiChatbotService:
    """
    Serviço Gemini Centralizado - Protagonista Principal do Chatbot
    
    Este serviço é responsável por:
    1. Gerenciar todo o fluxo de conversação
    2. Identificar intenções e estados da conversa
    3. Responder pacientes com base nas informações do RAG
    4. Coordenar pré-agendamentos e informações da clínica
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
        
        # Configurar o Gemini
        try:
            genai.configure(api_key=self.api_key)
            model_name = getattr(settings, 'GEMINI_MODEL', 'gemini-2.0-flash')
            self.model = genai.GenerativeModel(model_name)
            
            # Configurações de geração
            self.generation_config = {
                "temperature": 0.7,
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 1024,
            }
            
            logger.info("✅ Gemini Chatbot Service inicializado com sucesso")
            
        except Exception as e:
            logger.error(f"❌ Erro ao configurar Gemini: {e}")
            self.enabled = False
    
    def process_message(self, phone_number: str, message: str) -> Dict[str, Any]:
        """
        Processa mensagem do usuário usando o Gemini como protagonista principal
        
        Args:
            phone_number: Número do telefone do usuário
            message: Mensagem do usuário
            
        Returns:
            Dict com resposta e informações do processamento
        """
        try:
            if not self.enabled:
                return self._get_fallback_response(message)
            
            # Obter sessão da conversa
            session = self._get_or_create_session(phone_number)
            
            # Obter dados da clínica
            clinic_data = RAGService.get_all_clinic_data()
            
            # Obter histórico da conversa
            conversation_history = self._get_conversation_history(phone_number)
            
            # Verificar se é solicitação de horários
            if self._is_scheduling_request(message):
                # Usar serviço de consulta de horários
                scheduling_result = smart_scheduling_service.analyze_scheduling_request(message, session)
                analysis_result = self._convert_scheduling_to_gemini_format(scheduling_result)
                response_result = {
                    'response': scheduling_result['message'],
                    'intent': 'buscar_horarios',
                    'confidence': 0.9
                }
            else:
                # Usar Gemini para outras solicitações
                analysis_result = self._analyze_message_with_gemini(
                    message, session, conversation_history, clinic_data
                )

                response_result = self._generate_response_with_gemini(
                    message, analysis_result, session, conversation_history, clinic_data
                )
            
            # Verificar se é confirmação de agendamento e gerar handoff
            if analysis_result['intent'] == 'confirmar_agendamento':
                handoff_result = self._handle_appointment_confirmation(phone_number, session, analysis_result)
                if handoff_result:
                    response_result['response'] = handoff_result['message']
                    response_result['handoff_link'] = handoff_result['handoff_link']
            
            # Atualizar sessão
            self._update_session(phone_number, session, analysis_result, response_result)
            
            # Salvar mensagens no histórico com entidades
            self._save_conversation_messages(phone_number, message, response_result['response'], analysis_result)
            
            logger.info(f"🤖 [{analysis_result['intent'].upper()}] {analysis_result['confidence']:.2f} - {response_result['response'][:100]}...")
            
            return {
                'response': response_result['response'],
                'intent': analysis_result['intent'],
                'confidence': analysis_result['confidence'],
                'state': session['current_state'],
                'session_data': session,
                'analysis': analysis_result,
                'agent': 'gemini'
            }
            
        except Exception as e:
            logger.error(f"❌ Erro no processamento da mensagem: {e}")
            return self._get_fallback_response(message)
    
    def _analyze_message_with_gemini(self, message: str, session: Dict, 
                                   conversation_history: List, clinic_data: Dict) -> Dict[str, Any]:
        """
        Analisa mensagem usando Gemini para identificar intenção e estado da conversa
        """
        try:
            # Construir prompt de análise
            analysis_prompt = self._build_analysis_prompt(
                message, session, conversation_history, clinic_data
            )
            
            # Gerar análise com Gemini
            response = self.model.generate_content(
                analysis_prompt,
                generation_config={
                    "temperature": 0.1,  # Baixa temperatura para análise mais determinística
                    "top_p": 0.8,
                    "top_k": 20,
                    "max_output_tokens": 300
                }
            )
            
            # Extrair análise da resposta
            analysis_result = self._extract_analysis_from_response(response.text)
            analysis_result['original_message'] = message  # Adicionar mensagem original para fallback
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Erro na análise com Gemini: {e}")
            return self._get_fallback_analysis(message, session)
    
    def _generate_response_with_gemini(self, message: str, analysis_result: Dict,
                                     session: Dict, conversation_history: List,
                                     clinic_data: Dict) -> Dict[str, Any]:
        """
        Gera resposta usando Gemini baseada na análise e contexto
        """
        try:
            # Construir prompt de resposta
            response_prompt = self._build_response_prompt(
                message, analysis_result, session, conversation_history, clinic_data
            )
            
            # Gerar resposta com Gemini
            response = self.model.generate_content(
                response_prompt,
                generation_config=self.generation_config
            )
            
            return {
                'response': response.text.strip(),
                'intent': analysis_result['intent'],
                'confidence': analysis_result['confidence']
            }
            
        except Exception as e:
            logger.error(f"Erro na geração de resposta com Gemini: {e}")
            return self._get_fallback_response(message)
    
    def _build_analysis_prompt(self, message: str, session: Dict, 
                             conversation_history: List, clinic_data: Dict) -> str:
        """
        Constrói prompt para análise da mensagem
        """
        # Informações da clínica
        clinic_info = clinic_data.get('clinica_info', {})
        medicos = clinic_data.get('medicos', [])
        especialidades = clinic_data.get('especialidades', [])
        
        # Estado atual da sessão
        current_state = session.get('current_state', 'idle')
        patient_name = session.get('patient_name')
        selected_doctor = session.get('selected_doctor')
        
        # Histórico da conversa
        history_text = ""
        if conversation_history:
            history_text = "Histórico da conversa:\n"
            for msg in conversation_history[-3:]:  # Últimas 3 mensagens
                role = "Paciente" if msg['is_user'] else "Assistente"
                history_text += f"- {role}: {msg['content']}\n"
        
        prompt = f"""Você é um assistente virtual especializado da {clinic_info.get('nome', 'clínica médica')}.

ANÁLISE DA MENSAGEM:
Mensagem do paciente: "{message}"

CONTEXTO ATUAL:
- Estado da conversa: {current_state}
- Nome do paciente: {patient_name or 'Não informado'}
- Médico selecionado: {selected_doctor or 'Não selecionado'}

{history_text}

INFORMAÇÕES DA CLÍNICA:
- Nome: {clinic_info.get('nome', 'Clínica Médica')}
- Especialidades: {', '.join([esp['nome'] for esp in especialidades[:5]])}
- Médicos: {', '.join([med['nome'] for med in medicos[:3]])}

ANÁLISE NECESSÁRIA:
Analise a mensagem e determine:

EXEMPLOS DE EXTRAÇÃO DE ENTIDADES:
- "Meu nome é João Silva" → nome_paciente: "João Silva"
- "Quero agendar com Dr. João Carvalho" → medico: "Dr. João Carvalho"
- "Quero agendar para segunda-feira às 14h" → data: "segunda-feira", horario: "14:00"
- "Preciso de um cardiologista" → especialidade: "cardiologia"
- "Quero fazer um hemograma" → exame: "hemograma"

1. INTENÇÃO PRINCIPAL (uma das opções abaixo):
   - saudacao: Cumprimentos, oi, olá, bom dia
   - buscar_info: Perguntas sobre clínica, médicos, exames, preços, endereço
   - agendar_consulta: Quero agendar, marcar consulta, agendamento
   - confirmar_agendamento: Confirmar dados, sim, está correto
   - cancelar_agendamento: Cancelar, desmarcar, não posso mais
   - buscar_medico: Quais médicos, médico específico, especialidade
   - buscar_exame: Exames disponíveis, procedimentos
   - buscar_horarios: Horários disponíveis, quando atende
   - despedida: Tchau, obrigado, até logo
   - duvida: Não entendi, pode repetir, ajuda

2. PRÓXIMO ESTADO DA CONVERSA:
   - idle: Estado inicial
   - coletando_nome: Coletando nome do paciente
   - confirmando_nome: Confirmando nome extraído
   - selecionando_medico: Escolhendo médico
   - escolhendo_horario: Escolhendo data/horário
   - confirmando_agendamento: Confirmando dados finais
   - agendamento_concluido: Processo finalizado
   - fornecendo_info: Fornecendo informações solicitadas

3. ENTIDADES EXTRAÍDAS (EXTRAIA SEMPRE QUE POSSÍVEL):
   - nome_paciente: Nome completo do paciente (ex: "João Silva", "Maria Santos")
   - medico: Nome do médico mencionado (ex: "Dr. João", "Dra. Ana", "João Carvalho")
   - especialidade: Especialidade médica (ex: "cardiologia", "dermatologia", "pediatria")
   - data: Data em formato DD/MM/YYYY ou texto (ex: "15/09/2024", "segunda-feira", "amanhã")
   - horario: Horário em formato HH:MM ou texto (ex: "14:30", "2h30", "2 da tarde")
   - exame: Nome do exame mencionado (ex: "hemograma", "raio-x", "ultrassom")

IMPORTANTE: Se a mensagem contém informações como nome, médico, data ou horário, EXTRAIA essas informações mesmo que já estejam na sessão anterior. O paciente pode estar corrigindo ou confirmando dados.

4. CONFIANÇA: Nível de confiança na análise (0.0 a 1.0)

INSTRUÇÕES PARA EXTRAÇÃO DE ENTIDADES:
- Se encontrar um nome (ex: "João Silva"), coloque em "nome_paciente"
- Se encontrar médico (ex: "Dr. João"), coloque em "medico"  
- Se encontrar data (ex: "15/09", "segunda"), coloque em "data"
- Se encontrar horário (ex: "14h", "2 da tarde"), coloque em "horario"
- Se encontrar especialidade (ex: "cardiologia"), coloque em "especialidade"
- Se encontrar exame (ex: "hemograma"), coloque em "exame"
- Se NÃO encontrar a informação, use null

Responda APENAS com um JSON válido no formato:
{{
    "intent": "intenção_detectada",
    "next_state": "próximo_estado",
    "entities": {{
        "nome_paciente": "nome_extraído_ou_null",
        "medico": "médico_extraído_ou_null",
        "especialidade": "especialidade_extraída_ou_null",
        "data": "data_extraída_ou_null",
        "horario": "horário_extraído_ou_null",
        "exame": "exame_extraído_ou_null"
    }},
    "confidence": 0.95,
    "reasoning": "Explicação breve da análise"
}}"""
        
        return prompt
    
    def _build_response_prompt(self, message: str, analysis_result: Dict,
                             session: Dict, conversation_history: List,
                             clinic_data: Dict) -> str:
        """
        Constrói prompt para geração de resposta
        """
        intent = analysis_result['intent']
        entities = analysis_result['entities']
        next_state = analysis_result['next_state']
        
        # Informações da clínica
        clinic_info = clinic_data.get('clinica_info', {})
        medicos = clinic_data.get('medicos', [])
        especialidades = clinic_data.get('especialidades', [])
        exames = clinic_data.get('exames', [])
        
        # Estado atual da sessão
        current_state = session.get('current_state', 'idle')
        patient_name = session.get('patient_name')
        selected_doctor = session.get('selected_doctor')
        
        prompt = f"""Você é um assistente virtual especializado da {clinic_info.get('nome', 'clínica médica')}.

CONTEXTO DA CONVERSA:
- Estado atual: {current_state}
- Próximo estado: {next_state}
- Intenção detectada: {intent}
- Nome do paciente: {patient_name or 'Não informado'}
- Médico selecionado: {selected_doctor or 'Não selecionado'}

MENSAGEM DO PACIENTE: "{message}"

INFORMAÇÕES DA CLÍNICA:
- Nome: {clinic_info.get('nome', 'Clínica Médica')}
- Endereço: {clinic_info.get('endereco', 'Endereço não informado')}
- Telefone: {clinic_info.get('telefone_contato', 'Telefone não informado')}
- WhatsApp: {clinic_info.get('whatsapp_contato', 'WhatsApp não informado')}

MÉDICOS DISPONÍVEIS:
{self._format_medicos_for_prompt(medicos)}

ESPECIALIDADES:
{self._format_especialidades_for_prompt(especialidades)}

EXAMES DISPONÍVEIS:
{self._format_exames_for_prompt(exames)}

INSTRUÇÕES ESPECÍFICAS PARA INTENÇÃO "{intent}":
{self._get_intent_instructions(intent)}

REGRAS IMPORTANTES:
1. Seja sempre cordial, profissional e prestativo
2. Use emojis moderadamente para tornar a conversa mais amigável
3. Mantenha respostas concisas e diretas
4. NÃO mencione telefone ou WhatsApp a menos que o paciente peça especificamente
5. Foque apenas no que o paciente perguntou
6. Se não souber algo específico, oriente o paciente a entrar em contato
7. Use linguagem clara e acessível
8. Mantenha o foco em saúde e bem-estar

Gere uma resposta apropriada para a intenção "{intent}" considerando o contexto atual da conversa."""
        
        return prompt
    
    def _extract_analysis_from_response(self, response_text: str) -> Dict[str, Any]:
        """
        Extrai análise da resposta do Gemini
        """
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
            
            # Se não conseguiu extrair entidades, tentar com regex
            if not cleaned_entities:
                cleaned_entities = self._extract_entities_with_regex(analysis.get('original_message', ''))
                logger.info(f"🔄 Fallback regex extraiu: {cleaned_entities}")
            
            analysis['entities'] = cleaned_entities
            
            # Validar confiança
            confidence = float(analysis.get('confidence', 0.5))
            if not 0.0 <= confidence <= 1.0:
                confidence = 0.5
            
            analysis['confidence'] = confidence
            
            return analysis
            
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.warning(f"Erro ao parsear análise do Gemini: {e}")
            return self._get_fallback_analysis("", {})
    
    def _get_intent_instructions(self, intent: str) -> str:
        """
        Retorna instruções específicas para cada intenção
        """
        instructions = {
            'saudacao': """
            - Cumprimente calorosamente o paciente
            - Apresente-se como assistente da clínica
            - Pergunte como pode ajudar
            - Se for primeira interação, inicie coleta do nome
            """,
            
            'buscar_info': """
            - Forneça APENAS as informações específicas que o paciente perguntou
            - Se perguntar sobre endereço, forneça apenas o endereço
            - Se perguntar sobre telefone, forneça apenas o telefone
            - Se perguntar sobre horários, forneça apenas os horários
            - Se perguntar sobre convênios, liste apenas os convênios aceitos
            - NÃO forneça informações não solicitadas
            """,
            
            'agendar_consulta': """
            - Guie o paciente através do processo de agendamento
            - Se não tiver o nome, solicite o nome completo primeiro
            - Se tiver o nome, prossiga para seleção de médico
            - Seja claro sobre as etapas necessárias
            - Mantenha o processo organizado e fácil
            """,
            
            'confirmar_agendamento': """
            - Verifique se tem todas as informações necessárias
            - Confirme nome, médico, data e horário
            - Se estiver tudo correto, gere link de handoff
            - Oriente sobre próximos passos
            """,
            
            'buscar_medico': """
            - Apresente os médicos disponíveis
            - Informe especialidades, convênios aceitos e preços
            - Se houver mais de um médico, pergunte qual deseja agendar
            - NÃO mencione telefone/WhatsApp a menos que o paciente peça
            """,
            
            'buscar_exame': """
            - Explique o que é o exame de forma clara
            - Detalhe como funciona o procedimento
            - Mencione preparação necessária
            - Informe preço e duração
            - Destaque benefícios do exame
            """,
            
            'buscar_horarios': """
            - Apresente horários de forma clara
            - Considere preferências do paciente
            - Sugira alternativas se necessário
            - Facilite a escolha do horário
            """,
            
            'cancelar_agendamento': """
            - Seja compreensivo e acolhedor
            - Facilite o processo de cancelamento
            - Sugira reagendamento se apropriado
            - Mantenha a porta aberta para futuras consultas
            """,
            
            'despedida': """
            - Despeça-se cordialmente
            - Reforce que está disponível para ajudar
            - Deseje boa saúde
            - Convide para retornar quando necessário
            """,
            
            'duvida': """
            - Seja educado ao não entender
            - Peça esclarecimentos de forma gentil
            - Ofereça opções de como pode ajudar
            - Mantenha o tom acolhedor
            """
        }
        
        return instructions.get(intent, instructions['duvida'])
    
    def _format_medicos_for_prompt(self, medicos: List[Dict]) -> str:
        """Formata médicos para o prompt"""
        if not medicos:
            return "Nenhum médico cadastrado"
        
        formatted = []
        for medico in medicos[:5]:  # Limitar a 5 médicos
            nome = medico.get('nome', 'Nome não informado')
            especialidades = medico.get('especialidades_display', 'Especialidade não informada')
            preco = medico.get('preco_particular', 'Preço não informado')
            formatted.append(f"- {nome}: {especialidades} (Particular: R$ {preco})")
        
        return "\n".join(formatted)
    
    def _format_especialidades_for_prompt(self, especialidades: List[Dict]) -> str:
        """Formata especialidades para o prompt"""
        if not especialidades:
            return "Nenhuma especialidade cadastrada"
        
        formatted = []
        for esp in especialidades[:5]:  # Limitar a 5 especialidades
            nome = esp.get('nome', 'Nome não informado')
            descricao = esp.get('descricao', 'Descrição não informada')
            formatted.append(f"- {nome}: {descricao}")
        
        return "\n".join(formatted)
    
    def _format_exames_for_prompt(self, exames: List[Dict]) -> str:
        """Formata exames para o prompt"""
        if not exames:
            return "Nenhum exame cadastrado"
        
        formatted = []
        for exame in exames[:3]:  # Limitar a 3 exames
            nome = exame.get('nome', 'Nome não informado')
            preco = exame.get('preco', 'Preço não informado')
            duracao = exame.get('duracao_formatada', 'Duração não informada')
            formatted.append(f"- {nome}: R$ {preco} ({duracao})")
        
        return "\n".join(formatted)
    
    def _get_or_create_session(self, phone_number: str) -> Dict[str, Any]:
        """Obtém ou cria sessão da conversa"""
        cache_key = f"gemini_session_{phone_number}"
        session = cache.get(cache_key)
        
        if not session:
            session = {
                'phone_number': phone_number,
                'current_state': 'idle',
                'patient_name': None,
                'selected_doctor': None,
                'preferred_date': None,
                'preferred_time': None,
                'insurance_type': None,
                'created_at': timezone.now().isoformat(),
                'last_activity': timezone.now().isoformat()
            }
            cache.set(cache_key, session, 3600)  # 1 hora
        
        return session
    
    def _update_session(self, phone_number: str, session: Dict, 
                       analysis_result: Dict, response_result: Dict):
        """Atualiza sessão com base na análise e resposta"""
        try:
            # Atualizar estado
            session['current_state'] = analysis_result['next_state']
            session['last_activity'] = timezone.now().isoformat()
            
            # Atualizar entidades extraídas
            entities = analysis_result['entities']
            
            # Log das entidades extraídas para debug
            if entities:
                logger.info(f"🔍 Entidades extraídas: {entities}")
            
            # Atualizar nome do paciente
            if entities.get('nome_paciente') and entities['nome_paciente'] != 'null':
                session['patient_name'] = entities['nome_paciente']
                logger.info(f"✅ Nome atualizado: {entities['nome_paciente']}")
            
            # Atualizar médico selecionado
            if entities.get('medico') and entities['medico'] != 'null':
                session['selected_doctor'] = entities['medico']
                logger.info(f"✅ Médico atualizado: {entities['medico']}")
            
            # Atualizar data preferida
            if entities.get('data') and entities['data'] != 'null':
                session['preferred_date'] = entities['data']
                logger.info(f"✅ Data atualizada: {entities['data']}")
            
            # Atualizar horário preferido
            if entities.get('horario') and entities['horario'] != 'null':
                session['preferred_time'] = entities['horario']
                logger.info(f"✅ Horário atualizado: {entities['horario']}")
            
            # Salvar sessão
            cache_key = f"gemini_session_{phone_number}"
            cache.set(cache_key, session, 3600)
            
            # Log do estado final da sessão
            logger.info(f"📋 Sessão atualizada - Estado: {session['current_state']}, Nome: {session.get('patient_name')}, Médico: {session.get('selected_doctor')}")
            
            # Sincronizar com banco de dados
            self._sync_session_to_database(phone_number, session)
            
        except Exception as e:
            logger.error(f"Erro ao atualizar sessão: {e}")
    
    def _sync_session_to_database(self, phone_number: str, session: Dict):
        """Sincroniza sessão do cache com o banco de dados"""
        try:
            from api_gateway.models import ConversationSession

            # Obter ou criar sessão no banco
            db_session, created = ConversationSession.objects.get_or_create(
                phone_number=phone_number,
                defaults={
                    'current_state': session.get('current_state', 'idle'),
                    'patient_name': session.get('patient_name'),
                    'name_confirmed': bool(session.get('patient_name')),
                    'pending_name': None,
                    'insurance_type': session.get('insurance_type'),
                    'created_at': timezone.now(),
                    'updated_at': timezone.now()
                }
            )
            
            if not created:
                # Atualizar sessão existente
                db_session.current_state = session.get('current_state', 'idle')
                db_session.patient_name = session.get('patient_name')
                db_session.name_confirmed = bool(session.get('patient_name'))
                db_session.insurance_type = session.get('insurance_type')
                db_session.updated_at = timezone.now()
                db_session.save()
            
            logger.info(f"💾 Sessão sincronizada com banco - ID: {db_session.id}, Nome: {db_session.patient_name}")
            
        except Exception as e:
            logger.error(f"Erro ao sincronizar sessão com banco: {e}")
    
    def _get_conversation_history(self, phone_number: str, limit: int = 5) -> List[Dict]:
        """Obtém histórico da conversa"""
        try:
            from .conversation_service import conversation_service
            return conversation_service.get_conversation_history(phone_number, limit)
        except:
            return []
    
    def _save_conversation_messages(self, phone_number: str, user_message: str, bot_response: str, 
                                   analysis_result: Dict = None):
        """Salva mensagens no histórico com entidades extraídas"""
        try:
            from .conversation_service import conversation_service

            # Preparar entidades para salvar no banco
            entities_to_save = {}
            if analysis_result and analysis_result.get('entities'):
                entities_to_save = analysis_result['entities']
            
            # Salvar mensagem do usuário com entidades
            user_msg = conversation_service.add_message(
                phone_number, user_message, 'user',
                analysis_result.get('intent', 'user_message') if analysis_result else 'user_message',
                analysis_result.get('confidence', 1.0) if analysis_result else 1.0,
                entities_to_save
            )
            
            if user_msg:
                logger.info(f"💾 Mensagem do usuário salva no banco com ID: {user_msg.id}")
                logger.info(f"🔍 Entidades salvas: {entities_to_save}")
            
            # Salvar resposta do bot
            bot_msg = conversation_service.add_message(
                phone_number, bot_response, 'bot',
                'bot_response', 1.0, {}
            )
            
            if bot_msg:
                logger.info(f"💾 Resposta do bot salva no banco com ID: {bot_msg.id}")
            
        except Exception as e:
            logger.error(f"Erro ao salvar mensagens: {e}")
    
    def _extract_entities_with_regex(self, message: str) -> Dict[str, str]:
        """
        Extrai entidades usando regex como fallback quando o Gemini falha
        """
        import re
        entities = {}
        message_lower = message.lower()
        
        # Extrair nome do paciente
        name_patterns = [
            r'meu\s+nome\s+é\s+([A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+)*)',
            r'sou\s+([A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+)*)',
            r'chamo-me\s+([A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+)*)',
            r'nome\s+é\s+([A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+)*)',
            r'me\s+chamo\s+([A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+)*)',
            r'^([A-Za-zÀ-ÿ]+\s+[A-Za-zÀ-ÿ]+)(?:\s|,|$)'
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Limitar a 3 palavras (nome + sobrenome + sobrenome)
                name_parts = name.split()[:3]
                if len(name_parts) >= 2:  # Pelo menos nome e sobrenome
                    entities['nome_paciente'] = ' '.join(name_parts).title()
                    break
        
        # Extrair médico
        doctor_patterns = [
            r'dr\.?\s+([A-Za-zÀ-ÿ]+)',
            r'dra\.?\s+([A-Za-zÀ-ÿ]+)',
            r'doutor\s+([A-Za-zÀ-ÿ]+)',
            r'doutora\s+([A-Za-zÀ-ÿ]+)',
            r'com\s+([A-Za-zÀ-ÿ]+)'
        ]
        
        for pattern in doctor_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                doctor_name = match.group(0).strip()
                # Limitar a 3 palavras
                doctor_parts = doctor_name.split()[:3]
                entities['medico'] = ' '.join(doctor_parts)
                break
        
        # Extrair data
        date_patterns = [
            r'(\d{1,2})/(\d{1,2})/(\d{2,4})',
            r'(\d{1,2})/(\d{1,2})',
            r'(segunda|terça|quarta|quinta|sexta|sábado|domingo)',
            r'(amanhã|hoje|depois)'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                entities['data'] = match.group(0).strip()
                break
        
        # Extrair horário
        time_patterns = [
            r'(\d{1,2}):(\d{2})',
            r'(\d{1,2})h(\d{2})?',
            r'(\d{1,2})\s+da\s+(manhã|tarde|noite)'
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                entities['horario'] = match.group(0).strip()
                break
        
        return entities
    
    def _get_fallback_analysis(self, message: str, session: Dict) -> Dict[str, Any]:
        """Análise de fallback quando Gemini não está disponível"""
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

        # Tentar extrair entidades com regex como fallback
        entities = self._extract_entities_with_regex(message)
        logger.info(f"🔄 Fallback extraiu entidades: {entities}")

        return {
            'intent': intent,
            'next_state': next_state,
            'entities': entities,
            'confidence': 0.6,
            'reasoning': 'Análise de fallback baseada em palavras-chave e regex'
        }
    
    def _get_fallback_response(self, message: str) -> Dict[str, Any]:
        """Resposta de fallback quando Gemini não está disponível"""
        return {
            'response': "Desculpe, estou temporariamente indisponível. Como posso ajudá-lo?",
            'intent': 'duvida',
            'confidence': 0.5,
            'state': 'idle',
            'session_data': {},
            'analysis': {'intent': 'duvida', 'confidence': 0.5},
            'agent': 'fallback'
        }
    
    def _is_scheduling_request(self, message: str) -> bool:
        """
        Verifica se a mensagem é uma solicitação de horários/agendamento
        
        Args:
            message: Mensagem do usuário
            
        Returns:
            True se for solicitação de horários
        """
        message_lower = message.lower()
        
        # Palavras-chave que indicam solicitação de horários
        scheduling_keywords = [
            'horário', 'horarios', 'horários',
            'agendar', 'marcar', 'consulta',
            'disponível', 'disponivel', 'disponibilidade',
            'quando', 'que horas', 'que hora',
            'manhã', 'manha', 'tarde', 'noite',
            'segunda', 'terça', 'quarta', 'quinta', 'sexta',
            'sábado', 'sabado', 'domingo',
            'amanhã', 'amanha', 'hoje', 'depois'
        ]
        
        # Verificar se contém palavras-chave de agendamento
        for keyword in scheduling_keywords:
            if keyword in message_lower:
                return True
        
        return False
    
    def _convert_scheduling_to_gemini_format(self, scheduling_result: Dict) -> Dict[str, Any]:
        """
        Converte resultado do smart_scheduling_service para formato do Gemini
        
        Args:
            scheduling_result: Resultado do smart_scheduling_service
            
        Returns:
            Dict no formato esperado pelo Gemini
        """
        return {
            'intent': 'buscar_horarios',
            'next_state': 'fornecendo_info',
            'entities': scheduling_result.get('entities', {}),
            'confidence': 0.9,
            'reasoning': 'Análise de horários via smart_scheduling_service'
        }
    
    def _handle_appointment_confirmation(self, phone_number: str, session: Dict, analysis_result: Dict) -> Optional[Dict]:
        """
        Processa confirmação de agendamento e gera handoff
        
        Args:
            phone_number: Número do telefone
            session: Sessão da conversa
            analysis_result: Resultado da análise
            
        Returns:
            Dict com mensagem e link de handoff ou None
        """
        try:
            # Obter informações da sessão e entidades
            entities = analysis_result.get('entities', {})
            
            # Extrair informações das entidades com fallbacks
            patient_name = entities.get('nome_paciente') or session.get('patient_name') or 'Paciente'
            doctor_name = entities.get('medico') or session.get('selected_doctor') or 'Médico'
            date_mentioned = entities.get('data') or session.get('preferred_date') or 'Data a definir'
            time_mentioned = entities.get('horario') or session.get('preferred_time') or 'Horário a definir'
            
            # Gerar link de handoff
            from .handoff_service import handoff_service
            
            handoff_link = handoff_service.generate_appointment_handoff_link(
                patient_name=patient_name,
                doctor_name=doctor_name,
                date=date_mentioned,
                time=time_mentioned,
                appointment_type='Consulta'
            )
            
            # Criar mensagem de confirmação com link
            confirmation_message = f"""✅ **Perfeito, {patient_name}! Vamos confirmar seu agendamento:**

📋 **RESUMO:**
👤 Paciente: {patient_name}
👨‍⚕️ Médico: {doctor_name}
💼 Tipo de Consulta: {appointment_type}
📅 Data: {date_mentioned}
🕐 Horário: {time_mentioned}

**🔄 Para FINALIZAR o agendamento:**
👩‍💼 Nossa secretária validará a disponibilidade e confirmará seu agendamento através do link abaixo.

**📞 Clique no link abaixo para falar diretamente com nossa equipe:**
{handoff_link}"""
            
            return {
                'message': confirmation_message,
                'handoff_link': handoff_link
            }
            
        except Exception as e:
            logger.error(f"Erro ao gerar handoff: {e}")
            return None
    
    def test_connection(self) -> bool:
        """Testa conexão com Gemini"""
        if not self.enabled:
            return False
        
        try:
            test_response = self.model.generate_content(
                "Teste de conexão. Responda apenas 'OK'.",
                generation_config={"max_output_tokens": 10}
            )
            return "ok" in test_response.text.lower()
        except Exception as e:
            logger.error(f"Erro ao testar conexão com Gemini: {e}")
            return False


# Instância global do serviço
gemini_chatbot_service = GeminiChatbotService()
