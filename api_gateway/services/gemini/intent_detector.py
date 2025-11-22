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
                model_name = getattr(settings, 'GEMINI_MODEL', 'gemini-2.5-flash-lite')
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
                    "temperature": 0.6,  # Ligeiramente reduzido para análise mais precisa (mas ainda flexível)
                    "top_p": 0.85,       # Aumentado para melhor compreensão de contexto
                    "top_k": 30,         # Aumentado de 20 para considerar mais opções na análise
                    "max_output_tokens": 400  # Aumentado de 300 para permitir análises mais detalhadas
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
            analysis_result = self._extract_analysis_from_response(response.text, message, session)
            
            # ETAPA 5: Retornar resultado da análise
            # O resultado contém todas as informações necessárias para o chatbot
            # decidir como responder ao usuário
            return analysis_result
            
        except Exception as e:
            # TRATAMENTO DE ERRO: Se algo der errado com o Gemini, retornar erro
            # O sistema não tentará continuar com lógica simplificada
            logger.error(f"Erro na análise com Gemini: {e}")
            
            # Retornar erro para o usuário pedir reformulação
            return {
                'intent': 'error',
                'next_state': session.get('current_state', 'idle'),
                'confidence': 0.0,
                'reasoning': f'Erro ao processar com Gemini: {str(e)}'
            }
    
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

Histórico (últimas 4):
{history_text or '- vazio'}

OBSERVAÇÕES IMPORTANTES:
- Se a mensagem for apenas um nome (ex.: "Gabriela"), considere que o paciente está informando o nome. NÃO classifique como saudação; use o estado 'confirming_name'.
- Evite redefinir a conversa para saudação se já estivermos coletando dados.

ANÁLISE NECESSÁRIA:
Analise a mensagem e determine:

1. INTENÇÃO PRINCIPAL (uma das opções abaixo):
   - saudacao: Cumprimentos, oi, olá, bom dia, boa tarde, boa noite, tudo bem?, tudo bem
   - buscar_info: Perguntas sobre clínica, médicos, exames, preços, endereço, convênios, planos de saúde, especialidades - APENAS DÚVIDAS
   - agendar_consulta: Quero agendar, marcar consulta, agendamento
   - confirmar_agendamento: Confirmar dados, sim, está correto, confirmado
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
   - selecting_specialty: Escolhendo especialidade médica
   - selecting_doctor: Escolhendo médico
   - choosing_schedule: Escolhendo data/horário
   - confirming: Confirmando dados finais do agendamento
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
    
    def _extract_analysis_from_response(self, response_text: str, message: str, session: Dict) -> Dict[str, Any]:
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
            
            return self._post_process_analysis(analysis, message, session)
            
        except Exception as e:
            logger.error(f"Erro ao extrair análise: {e}")
            logger.error(f"Resposta recebida: {response_text}")


    def _post_process_analysis(self, analysis: Dict[str, Any], message: str, session: Dict) -> Dict[str, Any]:
        """Ajusta resultados para evitar classificações incorretas (ex.: nome tratado como saudação)."""
        try:
            msg = (message or '').strip()
            if not msg:
                return analysis
            
            msg_lower = msg.lower()
            current_state = session.get('current_state', 'idle')
            greeting_keywords = ['oi', 'olá', 'ola', 'bom dia', 'boa tarde', 'boa noite', 'boa madrugada', 'hello', 'hi', 'hey']
            
            if analysis.get('intent') == 'saudacao':
                is_greeting = any(keyword in msg_lower for keyword in greeting_keywords)
                if not is_greeting and self._is_probable_name(msg):
                    analysis['intent'] = 'agendar_consulta'
                    if current_state in ['collecting_patient_info', 'idle', 'confirming_name']:
                        analysis['next_state'] = 'confirming_name'
                    analysis['confidence'] = max(analysis.get('confidence', 0.7), 0.85)
                    analysis['reasoning'] = 'Detectado nome do paciente; ajustando para fluxo de coleta de dados.'
            
            return analysis
        except Exception as e:
            logger.error(f"Erro no pós-processamento da análise: {e}")
            return analysis




