"""
Intent Detector - Detecção de Intenções do Usuário

Responsável por:
- Analisar mensagens e detectar intenções
- Extrair entidades da mensagem
- Determinar o próximo estado da conversa
"""

import json
import logging
import re
from typing import Any, Dict, List

import google.generativeai as genai
from django.conf import settings

from ..token_monitor import token_monitor

logger = logging.getLogger(__name__)


class IntentDetector:
    """Detecção de intenções do usuário"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'GEMINI_API_KEY', '')
        self.model = None
        
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                model_name = getattr(settings, 'GEMINI_MODEL', 'gemini-2.0-flash')
                self.model = genai.GenerativeModel(model_name)
            except Exception as e:
                logger.error(f"Erro ao configurar Gemini no IntentDetector: {e}")
    
    def analyze_message(self, message: str, session: Dict, 
                       conversation_history: List, clinic_data: Dict) -> Dict[str, Any]:
        """
        Analisa mensagem usando Gemini para identificar intenção e estado da conversa
        
        Esta é a função principal de análise de intenções do chatbot. Ela recebe uma mensagem
        do usuário e usa o modelo Gemini para determinar:
        - Qual a intenção do usuário (agendar, buscar info, etc.)
        - Qual deve ser o próximo estado da conversa
        - O nível de confiança na análise
        
        Args:
            message: Mensagem de texto enviada pelo usuário via WhatsApp
            session: Dicionário com dados da sessão atual (estado, nome do paciente, etc.)
            conversation_history: Lista com histórico das últimas mensagens da conversa
            clinic_data: Dados da clínica (médicos, especialidades, horários, etc.)
            
        Returns:
            Dict contendo:
                - intent: Intenção detectada (ex: 'agendar_consulta', 'buscar_info')
                - next_state: Próximo estado da conversa (ex: 'collecting_patient_info')
                - confidence: Nível de confiança da análise (0.0 a 1.0)
                - reasoning: Explicação da análise (opcional)
        """
        try:
            # ETAPA 1: Construir o prompt de análise
            # O prompt é uma instrução detalhada para o Gemini explicando:
            # - O contexto da conversa (estado atual, histórico)
            # - As possíveis intenções que podem ser detectadas
            # - Como extrair entidades da mensagem
            # - O formato de resposta esperado (JSON estruturado)
            analysis_prompt = self._build_analysis_prompt(
                message, session, conversation_history, clinic_data
            )
            
            # ETAPA 2: Enviar prompt para o modelo Gemini e obter resposta
            # O Gemini analisa a mensagem e retorna um JSON com a análise estruturada
            response = self.model.generate_content(
                analysis_prompt,
                generation_config={
                    "temperature": 0.7,  # Baixa temperatura = respostas mais determinísticas e consistentes
                    "top_p": 0.8,        # Controla diversidade das respostas (0.8 = boa diversidade)
                    "top_k": 20,         # Considera apenas os 20 tokens mais prováveis
                    "max_output_tokens": 300  # Limita resposta a 300 tokens (suficiente para JSON)
                }
            )
            
            # ETAPA 3: Monitorar uso de tokens para controle de custos
            # Registra quantos tokens foram usados na análise para:
            # - Controle de custos da API do Gemini
            # - Monitoramento de performance
            # - Otimização futura dos prompts
            token_monitor.log_token_usage("ANÁLISE", analysis_prompt, response.text, session.get('phone_number'))
            
            # ETAPA 4: Processar a resposta do Gemini
            # A resposta vem como texto, mas precisa ser convertida para JSON estruturado
            # Esta função extrai e valida o JSON retornado pelo Gemini
            analysis_result = self._extract_analysis_from_response(response.text)
            
            # ETAPA 5: Retornar resultado da análise
            # O resultado contém todas as informações necessárias para o chatbot
            # decidir como responder ao usuário
            return analysis_result
            
        except Exception as e:
            # TRATAMENTO DE ERRO: Se algo der errado com o Gemini
            # (API indisponível, resposta inválida, etc.), usar análise de fallback
            # que tenta detectar intenções usando palavras-chave simples
            logger.error(f"Erro na análise com Gemini: {e}")
            return self._get_fallback_analysis(message, session)
    
    def _build_analysis_prompt(self, message: str, session: Dict, 
                             conversation_history: List, clinic_data: Dict) -> str:
        """Constrói prompt para análise da mensagem com contexto otimizado"""
        # Informações da clínica
        clinic_info = clinic_data.get('clinica_info', {})
        
        # Estado atual da sessão
        current_state = session.get('current_state', 'idle')
        patient_name = session.get('patient_name')
        selected_doctor = session.get('selected_doctor')
        selected_specialty = session.get('selected_specialty')
        preferred_date = session.get('preferred_date')
        preferred_time = session.get('preferred_time')
        insurance_type = session.get('insurance_type')
        
        # Histórico da conversa
        history_text = ""
        if conversation_history:
            history_text = "Histórico da conversa:\n"
            for msg in conversation_history[-4:]:  # Últimas 4 mensagens
                role = "Paciente" if msg['is_user'] else "Assistente"
                history_text += f"- {role}: {msg['content']}\n"
        
        prompt = f"""Você é um assistente virtual especializado da {clinic_info.get('nome', 'clínica médica')}.

ANÁLISE DA MENSAGEM:
Mensagem do paciente: "{message}"

CONTEXTO ATUAL:
- Estado da conversa: {current_state}
- Nome do paciente: {patient_name or 'Não informado'}
- Médico selecionado: {selected_doctor or 'Não selecionado'}
- Especialidade escolhida: {selected_specialty or 'Não selecionada'}
- Data preferida: {preferred_date or 'Não informada'}
- Horário preferido: {preferred_time or 'Não informado'}
- Tipo de convênio: {insurance_type or 'Não informado'}

{history_text}

ANÁLISE NECESSÁRIA:
Analise a mensagem e determine:

1. INTENÇÃO PRINCIPAL (uma das opções abaixo):
   - saudacao: Cumprimentos, oi, olá, bom dia, boa tarde, boa noite, tudo bem?, tudo bem
   - buscar_info: Perguntas sobre clínica, médicos, exames, preços, endereço, convênios, planos de saúde, especialidades - APENAS DÚVIDAS
   - agendar_consulta: Quero agendar, marcar consulta, agendamento
   - confirmar_agendamento: Confirmar dados, sim, está correto, confirmado
   - despedida: Tchau, obrigado, até logo
   - duvida: Não entendi, pode repetir, ajuda

IMPORTANTE - DISTINÇÃO ENTRE DÚVIDAS E AGENDAMENTO:
- Use "buscar_info" quando o usuário quer APENAS informações
- Use "agendar_consulta" quando o usuário quer agendar E menciona médico/especialidade
- Palavras-chave para "buscar_info": "quais", "quem", "que", "tem", "atendem"
- Palavras-chave para "agendar_consulta": "quero", "agendar", "marcar", "consulta"

2. PRÓXIMO ESTADO DA CONVERSA:
   - idle: Estado inicial
   - collecting_patient_info: Coletando nome do paciente
   - confirming_name: Confirmando nome extraído
   - selecting_doctor: Escolhendo médico
   - selecting_specialty: Escolhendo especialidade médica
   - choosing_schedule: Escolhendo data/horário
   - confirming: Confirmando dados finais do agendamento
   - collecting_info: Fornecendo informações solicitadas
   - answering_questions: Respondendo dúvidas do paciente

3. CONFIANÇA: Nível de confiança na análise (0.0 a 1.0)

Responda APENAS com um JSON válido no formato:
{{
    "intent": "intenção_detectada",
    "next_state": "próximo_estado",
    "confidence": 0.95,
    "reasoning": "Explicação breve da análise"
}}"""
        
        return prompt
    
    def _extract_analysis_from_response(self, response_text: str) -> Dict[str, Any]:
        """Extrai análise estruturada da resposta do Gemini"""
        try:
            # Remover possíveis marcadores de código
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            # Tentar fazer parse do JSON
            analysis = json.loads(response_text.strip())
            
            # Validar campos obrigatórios
            if 'intent' not in analysis or 'next_state' not in analysis:
                raise ValueError("Campos obrigatórios faltando na análise")
            
            # CORREÇÃO: Não permitir que o Gemini defina estado 'confirming'
            # Este estado deve ser definido apenas pelo core_service quando o handoff for gerado
            if analysis['next_state'] == 'confirming':
                analysis['next_state'] = 'choosing_schedule'
            
            # Garantir que confidence existe
            if 'confidence' not in analysis:
                analysis['confidence'] = 0.7
            
            return analysis
            
        except Exception as e:
            logger.error(f"Erro ao extrair análise: {e}")
            logger.error(f"Resposta recebida: {response_text}")
            
            # Fallback: tentar extrair intent manualmente
            return self._manual_intent_extraction(response_text)
    
    def _manual_intent_extraction(self, response_text: str) -> Dict[str, Any]:
        """Extração manual de intent como fallback"""
        intent = "duvida"  # Default
        
        # Tentar encontrar intent na resposta
        if "agendar" in response_text.lower():
            intent = "agendar_consulta"
        elif "info" in response_text.lower() or "informação" in response_text.lower():
            intent = "buscar_info"
        elif "saudação" in response_text.lower() or "olá" in response_text.lower():
            intent = "saudacao"
        elif "confirmar" in response_text.lower():
            intent = "confirmar_agendamento"
        
        return {
            'intent': intent,
            'next_state': 'collecting_info',
            'confidence': 0.3,
            'reasoning': 'Extração manual de fallback'
        }
    
    def _get_fallback_analysis(self, message: str, session: Dict) -> Dict[str, Any]:
        """
        Análise de fallback quando o Gemini falha
        
        Args:
            message: Mensagem do usuário
            session: Dados da sessão atual (usado para contexto)
            
        Returns:
            Dict com análise baseada em palavras-chave
        """
        message_lower = message.lower()
        current_state = session.get('current_state', 'idle')
        
        # Detectar intent baseado em palavras-chave
        if any(word in message_lower for word in ['oi', 'olá', 'bom dia', 'boa tarde', 'boa noite']):
            intent = 'saudacao'
            next_state = 'idle'
        elif any(word in message_lower for word in ['agendar', 'marcar', 'consulta','consultar', 'agendamento', 'com', 'para', 'com especialista', 'com médico', 'com doutor', 'com doutora']):
            intent = 'agendar_consulta'
            # Se já tem nome, vai direto para escolher médico/especialidade
            if session.get('patient_name'):
                next_state = 'selecting_doctor'
            else:
                next_state = 'collecting_patient_info'
        elif any(word in message_lower for word in ['sim', 'confirmar', 'confirmado', 'está correto']):
            intent = 'confirmar_agendamento'
            # Não alterar estado aqui - deixar o core_service decidir baseado nas informações completas
            next_state = current_state
        elif any(word in message_lower for word in ['quais', 'quem', 'que', 'tem', 'atendem', 'disponível', 'especialista', 'médico', 'doutor', 'doutora', 'dr', 'dra']):
            intent = 'buscar_info'
            next_state = 'answering_questions'
        else:
            intent = 'buscar_info'
            next_state = 'answering_questions'
        
        return {
            'intent': intent,
            'next_state': next_state,
            'confidence': 0.5,
            'reasoning': f'Análise de fallback baseada em palavras-chave (estado atual: {current_state})'
        }


