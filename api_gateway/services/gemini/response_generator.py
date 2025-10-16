"""
Response Generator - Geração de Respostas Contextualizadas

Responsável por:
- Gerar respostas usando Gemini
- Construir prompts contextualizados
- Formatar respostas para o usuário
"""

import logging
from typing import Any, Dict, List

import google.generativeai as genai
from django.conf import settings

from ..token_monitor import token_monitor

logger = logging.getLogger(__name__)


class ResponseGenerator:
    """Geração de respostas contextualizadas"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'GEMINI_API_KEY', '')
        self.model = None
        
        self.generation_config = {
            "temperature": 0.7,
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 1024,
        }
        
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                model_name = getattr(settings, 'GEMINI_MODEL', 'gemini-2.0-flash')
                self.model = genai.GenerativeModel(model_name)
                
                # Aplicar configurações de modo econômico se necessário
                self._apply_economy_config()
            except Exception as e:
                logger.error(f"Erro ao configurar Gemini no ResponseGenerator: {e}")
    
    def _apply_economy_config(self):
        """Aplica configurações de modo econômico se necessário"""
        try:
            if token_monitor.is_economy_mode_active():
                economy_config = token_monitor.get_economy_config()
                if economy_config:
                    self.generation_config.update(economy_config)
                    logger.info("💰 Configurações de modo econômico aplicadas")
        except Exception as e:
            logger.error(f"Erro ao aplicar configurações de modo econômico: {e}")
    
    def generate_response(self, message: str, analysis_result: Dict,
                         session: Dict, conversation_history: List,
                         clinic_data: Dict) -> Dict[str, Any]:
        """
        Gera resposta usando Gemini baseada na análise e contexto
        
        Args:
            message: Mensagem do usuário
            analysis_result: Resultado da análise de intenção
            session: Sessão atual
            conversation_history: Histórico de conversas
            clinic_data: Dados da clínica
            
        Returns:
            Dict com response, intent, confidence
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
            
            # Log do uso de tokens para resposta
            token_monitor.log_token_usage("RESPOSTA", response_prompt, response.text, session.get('phone_number'))
            
            return {
                'response': response.text.strip(),
                'intent': analysis_result['intent'],
                'confidence': analysis_result['confidence']
            }
            
        except Exception as e:
            logger.error(f"Erro na geração de resposta com Gemini: {e}")
            return self._get_fallback_response(message)
    
    def _build_response_prompt(self, message: str, analysis_result: Dict,
                             session: Dict, conversation_history: List,
                             clinic_data: Dict) -> str:
        """Constrói prompt para geração de resposta com contexto otimizado"""
        intent = analysis_result['intent']
        entities = analysis_result.get('entities', {})
        
        # Informações da clínica
        clinic_info = clinic_data.get('clinica_info', {})
        medicos = clinic_data.get('medicos', [])
        especialidades = clinic_data.get('especialidades', [])
        
        # Informações já coletadas
        patient_name = session.get('patient_name')
        selected_doctor = session.get('selected_doctor')
        selected_specialty = session.get('selected_specialty')
        preferred_date = session.get('preferred_date')
        preferred_time = session.get('preferred_time')
        
        # Criar lista de informações já coletadas
        collected_info = []
        if patient_name:
            collected_info.append(f"✅ Nome do paciente: {patient_name}")
        if selected_specialty:
            collected_info.append(f"✅ Especialidade escolhida: {selected_specialty}")
        if selected_doctor:
            collected_info.append(f"✅ Médico escolhido: {selected_doctor}")
        if preferred_date:
            collected_info.append(f"✅ Data preferida: {preferred_date}")
        if preferred_time:
            collected_info.append(f"✅ Horário preferido: {preferred_time}")
        
        collected_info_str = '\n'.join(collected_info) if collected_info else "Nenhuma informação coletada ainda."
        
        # Obter especialidades disponíveis
        specialties_list = ', '.join([esp.get('nome', '') for esp in especialidades[:5]]) if especialidades else 'diversas especialidades'
        
        # Obter médicos disponíveis
        medicos_list = []
        if medicos:
            for medico in medicos:
                nome = medico.get('nome', '')
                especialidades_medico = medico.get('especialidades_display', '')
                medicos_list.append(f"• {nome} ({especialidades_medico})")
        
        medicos_text = '\n'.join(medicos_list) if medicos_list else 'Nenhum médico cadastrado'
        
        # Verificar se temos informações de disponibilidade real
        scheduling_info = analysis_result.get('scheduling_info', {})
        availability_context = ""
        
        # Verificar se há informações faltantes
        missing_info = analysis_result.get('missing_info', [])
        missing_context = ""
        
        if missing_info:
            missing_names = {
                'patient_name': 'nome do paciente',
                'selected_specialty': 'especialidade médica',
                'selected_doctor': 'médico',
                'preferred_date': 'data da consulta',
                'preferred_time': 'horário da consulta'
            }
            missing_list = [missing_names.get(info, info) for info in missing_info]
            missing_context = f"""
INFORMAÇÕES AINDA NECESSÁRIAS:
❌ Faltam: {', '.join(missing_list)}
⚠️ IMPORTANTE: Pergunte APENAS a próxima informação faltante, não todas de uma vez!"""
        
        if scheduling_info.get('has_availability_info'):
            calendar_availability = scheduling_info.get('calendar_availability', {})
            if calendar_availability.get('has_availability'):
                days_info = calendar_availability.get('days_info', [])
                doctor_name = calendar_availability.get('doctor_name', 'Médico')
                total_slots = calendar_availability.get('available_slots', 0)
                
                availability_context = f"""
DISPONIBILIDADE REAL DO GOOGLE CALENDAR:
✅ {doctor_name} tem {total_slots} horários disponíveis nos próximos 7 dias
📅 Informações detalhadas por dia:"""
                
                for day in days_info[:3]:  # Mostrar até 3 dias no prompt
                    date_str = day.get('date', '')
                    weekday = day.get('weekday', '')
                    available_times = day.get('available_times', [])
                    if available_times:
                        times_str = ', '.join(available_times[:4])  # Até 4 horários por dia
                        if len(available_times) > 4:
                            times_str += f" (+{len(available_times) - 4} outros)"
                        availability_context += f"\n• {weekday} ({date_str}): {times_str}"
                
                availability_context += f"\n\n⚠️ IMPORTANTE: Use essas informações REAIS do calendário para informar horários disponíveis!"
            else:
                doctor_name = calendar_availability.get('doctor_name', 'Médico')
                availability_context = f"""
DISPONIBILIDADE REAL DO GOOGLE CALENDAR:
❌ {doctor_name} não tem horários disponíveis nos próximos 7 dias
⚠️ Informe que o médico está sem agenda disponível e sugira outro médico ou que entre em contato."""
        
        prompt = f"""Você é um assistente virtual da {clinic_info.get('nome', 'Clínica Médica')}.

MENSAGEM DO PACIENTE: "{message}"

INTENÇÃO DETECTADA: {intent}

INFORMAÇÕES JÁ COLETADAS (NÃO PERGUNTE NOVAMENTE):
{collected_info_str}
{availability_context}
{missing_context}

ENTIDADES EXTRAÍDAS AGORA:
{entities}

ESPECIALIDADES DISPONÍVEIS: {specialties_list}

MÉDICOS DISPONÍVEIS:
{medicos_text}

INSTRUÇÕES:
1. Responda de forma natural, educada e profissional
2. NÃO repita perguntas sobre informações já coletadas (veja acima)
3. Se TODAS as informações estiverem coletadas, pergunte se deseja confirmar o pré-agendamento
4. Se faltar alguma informação, pergunte APENAS a informação faltante
5. Use emojis moderadamente para deixar a conversa mais amigável
6. Seja objetivo e direto
7. Não mencione que você é uma IA

REGRAS IMPORTANTES:
- Se intent = "saudacao" E não tiver nome: SEMPRE pergunte o nome primeiro ("Olá! Para começar, qual é o seu nome?")
- Se já tiver nome, especialidade, médico, data e horário: pergunte se deseja confirmar
- Se faltar apenas UMA informação: pergunte essa informação
- NÃO solicite informações que já estão na lista "INFORMAÇÕES JÁ COLETADAS"

ORDEM DE COLETA DE INFORMAÇÕES (SEMPRE SEGUIR ESTA ORDEM):
1. Nome do paciente (já coletado se chegou aqui)
2. Especialidade desejada
3. Médico específico (após escolher especialidade)
4. Data preferida
5. Horário preferido
6. Confirmação final

NÃO pule etapas! Se faltar especialidade, pergunte APENAS a especialidade. Se faltar médico, pergunte APENAS o médico.

REGRAS CRÍTICAS:
- NUNCA invente nomes de médicos! Use APENAS os médicos listados em "MÉDICOS DISPONÍVEIS"
- Se o usuário perguntar sobre médicos, liste APENAS os médicos reais do banco de dados
- Se não houver médicos para uma especialidade, informe que não há médicos disponíveis

DISTINÇÃO ENTRE DÚVIDAS E AGENDAMENTO:
- Se intent = "buscar_info": Forneça APENAS a informação solicitada, NÃO inicie processo de agendamento
- Se intent = "agendar_consulta": Inicie ou continue o processo de agendamento, coletando informações necessárias
- Se usuário pergunta sobre médicos/especialidades mas NÃO quer agendar: use "buscar_info"
- Se usuário quer agendar E menciona médico/especialidade: use "agendar_consulta"

Gere a resposta:"""
        
        return prompt
    
    def _get_fallback_response(self, message: str) -> Dict[str, Any]:
        """Resposta de fallback quando há erro"""
        return {
            'response': "Desculpe, tive um problema temporário. Poderia reformular sua pergunta?",
            'intent': 'duvida',
            'confidence': 0.3
        }


