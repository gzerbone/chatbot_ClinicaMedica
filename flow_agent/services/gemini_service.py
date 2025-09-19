"""
Serviço de integração com Google Gemini AI
"""
import json
import logging
from typing import Any, Dict, List, Optional

import google.generativeai as genai
from django.conf import settings

logger = logging.getLogger(__name__)


class GeminiService:
    """
    Serviço para integração com Google Gemini AI
    """
    
    def __init__(self):
        self.api_key = getattr(settings, 'GEMINI_API_KEY', '')
        
        # Verificar se Gemini está habilitado
        self.enabled = getattr(settings, 'GEMINI_ENABLED', True)
        
        if not self.api_key:
            logger.warning("GEMINI_API_KEY não configurada nas settings")
            self.enabled = False
        
        if not self.enabled:
            logger.warning("Gemini AI está desabilitado nas configurações")
            return
        
        # Configurar o Gemini apenas se habilitado e com API key
        try:
            genai.configure(api_key=self.api_key)
        except Exception as e:
            logger.error(f"Erro ao configurar Gemini: {e}")
            self.enabled = False
        
        # Obter configurações do Django
        model_name = getattr(settings, 'GEMINI_MODEL', 'gemini-1.5-flash')
        temperature = getattr(settings, 'GEMINI_TEMPERATURE', 0.7)
        max_tokens = getattr(settings, 'GEMINI_MAX_TOKENS', 1024)
        
        self.model = genai.GenerativeModel(model_name)
        
        # Configurações de geração
        self.generation_config = {
            "temperature": temperature,
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": max_tokens,
        }
    
    def generate_response(self, 
                         user_message: str, 
                         intent: str, 
                         context: Dict = None,
                         clinic_data: Dict = None) -> str:
        """
        Gera uma resposta usando o Gemini AI baseada na mensagem do usuário,
        intenção detectada e contexto da clínica.
        
        Args:
            user_message: Mensagem original do usuário
            intent: Intenção detectada pelo sistema
            context: Contexto da conversa
            clinic_data: Dados da clínica (médicos, especialidades, etc.)
            
        Returns:
            Resposta gerada pelo Gemini
        """
        # Se o Gemini não está habilitado ou configurado, usar resposta de fallback
        if not self.enabled or not hasattr(self, 'model'):
            logger.warning("Gemini não disponível, usando resposta de fallback")
            return self._get_fallback_response(intent)
            
        try:
            # Construir prompt baseado na intenção e contexto
            prompt = self._build_prompt(user_message, intent, context, clinic_data)
            
            # Gerar resposta
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config
            )
            
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Erro ao gerar resposta com Gemini: {e}")
            return self._get_fallback_response(intent)
    
    def _build_prompt(self, 
                     user_message: str, 
                     intent: str, 
                     context: Dict = None,
                     clinic_data: Dict = None) -> str:
        """
        Constrói o prompt para o Gemini baseado no contexto
        """
        # Prompt base do sistema
        # Buscar nome da clínica dinamicamente do banco de dados
        clinic_name = "clínica médica"  # valor padrão
        if clinic_data and 'nome' in clinic_data:
            clinic_name = clinic_data['nome']

        
        system_prompt = f"""Você é um assistente virtual especializado da {clinic_name}. 
        Seu papel é ajudar pacientes com informações sobre a clínica, agendamentos, médicos e exames.
        
        IMPORTANTE:
        - Seja sempre cordial, profissional e prestativo
        - Use emojis moderadamente para tornar a conversa mais amigável
        - Mantenha respostas concisas e diretas
        - NÃO mencione telefone ou WhatsApp da clínica a menos que o paciente peça especificamente
        - NÃO repita informações de contato em cada resposta
        - Foque apenas no que o paciente perguntou
        - Se não souber algo específico, oriente o paciente a entrar em contato
        - Sempre mantenha o foco em saúde e bem-estar
        - Use linguagem clara e acessível
        
        Contexto da clínica:"""
        
        # Adicionar informações da clínica se disponíveis
        if clinic_data:
            system_prompt += f"\n\nInformações da clínica:\n{json.dumps(clinic_data, indent=2, ensure_ascii=False)}"
        
        # Adicionar histórico da conversa se disponível
        if context and 'conversation_history' in context:
            history = context['conversation_history']
            if history:
                system_prompt += "\n\nHistórico recente da conversa:"
                for i, msg in enumerate(history, 1):
                    role = "Paciente" if msg.get('is_user', True) else "Assistente"
                    content = msg.get('content', '')[:100]  # Limitar tamanho
                    system_prompt += f"\n{i}. {role}: {content}"
        
        # Adicionar contexto adicional da conversa
        if context:
            # Remover histórico do contexto para evitar duplicação
            context_copy = {k: v for k, v in context.items() if k != 'conversation_history'}
            if context_copy:
                system_prompt += f"\n\nContexto atual:\n{json.dumps(context_copy, indent=2, ensure_ascii=False)}"
        
        # Adicionar instruções específicas baseadas na intenção
        intent_instructions = self._get_intent_instructions(intent)
        system_prompt += f"\n\nInstruções específicas para esta intenção ({intent}):\n{intent_instructions}"
        
        # Adicionar lógica para contatos
        contact_logic = self._get_contact_logic(intent, user_message)
        system_prompt += f"\n\nLógica de contatos:\n{contact_logic}"
        
        # Adicionar a mensagem do usuário
        system_prompt += f"\n\nMensagem do paciente: {user_message}\n\nResposta:"
        
        return system_prompt
    
    def _get_intent_instructions(self, intent: str) -> str:
        """
        Retorna instruções específicas baseadas na intenção detectada
        """
        instructions = {
            'saudacao': """
            - Cumprimente calorosamente o paciente
            - Apresente-se como assistente da clínica
            - Pergunte como posso ajudar
            """,
            
            'buscar_especialidade': """
            - Explique brevemente o que a especialidade perguntada trata
            - Sugira agendamento se o paciente demonstrar interesse
            """,
            
            'buscar_medico': """
            - Apresente os médicos disponíveis que atendem a especialidade perguntada
            - Informe nome, especialidade, convênios aceitos e horários de atendimento
            - Informe preço da consulta particular se relevante
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
            
            'buscar_info_clinica': """
            - Forneça APENAS as informações específicas que o paciente perguntou
            - Se perguntar sobre endereço, forneça apenas o endereço
            - Se perguntar sobre telefone, forneça apenas o telefone
            - Se perguntar sobre horários, forneça apenas os horários
            - Se perguntar sobre convênios, liste apenas os convênios aceitos por cada médico
            - Se perguntar sobre políticas, explique apenas as políticas da clínica
            - NÃO forneça informações não solicitadas
            """,
            
            'agendar_consulta': """
            - Guie o paciente através do processo de agendamento
            - Seja claro sobre as etapas necessárias
            - Seja claro sobre os horários disponíveis
            - Seja claro sobre os médicos disponíveis
            - Seja claro sobre os exames disponíveis
            - Seja claro sobre os convênios disponíveis
            - Seja claro sobre os preços das consultas
            - Seja claro sobre os preços dos exames
            - Seja claro sobre os planos de saúde aceitos por cada médico
            - Não faça um texto longo, faça um texto curto e direto
            - Mantenha o processo organizado e fácil
            """,
            
            'confirmar_agendamento': """
            - Verifique agendamentos pendentes
            - Confirme informações importantes como nome completo e telefone de contato do paciente
            - Oriente sobre próximos passos
            - Tranquilize o paciente sobre o processo
            """,
            
            'cancelar_agendamento': """
            - Seja compreensivo e acolhedor
            - Facilite o processo de cancelamento, informando que o cancelamento deve ser feito pelo WhatsApp da clínica ou pelo número de telefone da clínica
            - Sugira reagendamento se apropriado
            - Mantenha a porta aberta para futuras consultas
            """,
            
            'horarios_disponiveis': """
            - Apresente horários de forma clara
            - Considere preferências do paciente
            - Sugira alternativas se necessário
            - Facilite a escolha do horário
            """,
            
            'despedida': """
            - Despeça-se cordialmente
            - Reforce que está disponível para ajudar
            - Deseje boa saúde
            - Convide para retornar quando necessário
            """,
            
            'ajuda': """
            - Explique claramente como pode ajudar
            - Liste os principais serviços
            - Oriente sobre como proceder
            - Seja proativo em oferecer ajuda
            """,
            
            'desconhecida': """
            - Seja educado ao não entender
            - Peça esclarecimentos de forma gentil
            - Ofereça opções de como pode ajudar
            - Mantenha o tom acolhedor
            """
        }
        
        return instructions.get(intent, instructions['desconhecida'])
    
    def _get_contact_logic(self, intent: str, user_message: str) -> str:
        """
        Retorna lógica específica para quando mostrar contatos da clínica
        """
        message_lower = user_message.lower()
        
        # Palavras-chave que indicam necessidade de contato
        contact_keywords = [
            'telefone', 'whatsapp', 'contato', 'ligar', 'falar', 'agendar',
            'marcar', 'confirmar', 'disponibilidade', 'horário', 'horarios'
        ]
        
        # Verificar se o paciente pediu contato especificamente
        asked_for_contact = any(keyword in message_lower for keyword in contact_keywords)
        
        # Intenções que geralmente precisam de contato
        contact_intents = ['agendar_consulta', 'confirmar_agendamento', 'buscar_info_clinica']
        
        if asked_for_contact or intent in contact_intents:
            return """
            - Se o paciente pediu telefone/WhatsApp, forneça APENAS o que foi solicitado
            - Se o paciente quer agendar, forneça contatos para agendamento
            - Se o paciente quer confirmar, forneça contatos para confirmação
            - Seja específico: telefone para ligar, WhatsApp para mensagem
            """
        else:
            return """
            - NÃO mencione telefone ou WhatsApp nesta resposta
            - Foque apenas no que o paciente perguntou
            - Se o paciente demonstrar interesse em agendar, aí sim ofereça contatos
            """
    
    def _get_fallback_response(self, intent: str) -> str:
        """
        Retorna uma resposta de fallback caso o Gemini falhe
        """
        fallback_responses = {
            'saudacao': "Olá! 😊 Como posso ajudá-lo hoje?",
            'buscar_especialidade': "Aqui estão nossas especialidades. Qual você gostaria de conhecer?",
            'buscar_medico': "Aqui estão nossos médicos. Qual especialidade você precisa?",
            'buscar_exame': "Posso fornecer informações sobre nossos exames. Qual você gostaria de conhecer?",
            'buscar_info_clinica': "Que informação você precisa sobre a clínica?",
            'agendar_consulta': "Vou ajudá-lo a agendar. Qual especialidade você precisa?",
            'confirmar_agendamento': "Vou verificar seus agendamentos.",
            'cancelar_agendamento': "Entendo que precisa cancelar. Como posso ajudar?",
            'horarios_disponiveis': "Vou verificar os horários disponíveis.",
            'despedida': "Até logo! Foi um prazer ajudá-lo! 😊",
            'ajuda': "Posso ajudá-lo com informações sobre médicos, exames e agendamentos.",
            'desconhecida': "Desculpe, não entendi. Como posso ajudá-lo?"
        }
        
        return fallback_responses.get(intent, fallback_responses['desconhecida'])
    
    def generate_contextual_response(self, 
                                   user_message: str,
                                   intent: str,
                                   conversation_history: List[Dict],
                                   clinic_data: Dict = None) -> str:
        """
        Gera resposta considerando o histórico da conversa
        
        Args:
            user_message: Mensagem atual do usuário
            intent: Intenção detectada
            conversation_history: Histórico da conversa
            clinic_data: Dados da clínica
            
        Returns:
            Resposta contextualizada
        """
        try:
            # Construir contexto do histórico
            history_context = self._build_conversation_context(conversation_history)
            
            # Construir prompt com histórico
            prompt = self._build_contextual_prompt(
                user_message, intent, history_context, clinic_data
            )
            
            # Gerar resposta
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config
            )
            
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Erro ao gerar resposta contextual: {e}")
            return self.generate_response(user_message, intent, clinic_data=clinic_data)
    
    def _build_conversation_context(self, history: List[Dict]) -> str:
        """
        Constrói contexto a partir do histórico da conversa
        """
        if not history:
            return "Primeira interação com o paciente."
        
        context = "Histórico da conversa:\n"
        for i, msg in enumerate(history[-5:], 1):  # Últimas 5 mensagens
            role = "Paciente" if msg.get('tipo') == 'entrada' else "Assistente"
            content = msg.get('conteudo', '')
            context += f"{i}. {role}: {content}\n"
        
        return context
    
    def _build_contextual_prompt(self, 
                               user_message: str,
                               intent: str,
                               history_context: str,
                               clinic_data: Dict = None) -> str:
        """
        Constrói prompt considerando o histórico da conversa
        """
        system_prompt = """Você é um assistente virtual especializado de uma clínica médica.
        Considere o histórico da conversa para dar respostas mais personalizadas e contextuais.
        
        IMPORTANTE:
        - Use o histórico para entender melhor o que o paciente precisa
        - Mantenha consistência com respostas anteriores
        - Seja proativo baseado no contexto da conversa
        - Continue fluxos de agendamento ou consultas de forma natural
        """
        
        if clinic_data:
            system_prompt += f"\n\nInformações da clínica:\n{json.dumps(clinic_data, indent=2, ensure_ascii=False)}"
        
        system_prompt += f"\n\n{history_context}"
        
        intent_instructions = self._get_intent_instructions(intent)
        system_prompt += f"\n\nInstruções para esta intenção ({intent}):\n{intent_instructions}"
        
        system_prompt += f"\n\nMensagem atual do paciente: {user_message}\n\nResposta:"
        
        return system_prompt
    
    def test_connection(self) -> bool:
        """
        Testa a conexão com o Gemini AI
        
        Returns:
            True se a conexão estiver funcionando
        """
        if not self.enabled or not hasattr(self, 'model'):
            logger.warning("Gemini não está configurado para teste")
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
