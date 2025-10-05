"""
Gerenciador de Templates LangChain
Sistema para gerenciar e formatar templates de prompts
"""
import logging
from typing import Any, Dict, List, Optional

from .medical_prompts import IntentInstructions, MedicalPromptTemplates

logger = logging.getLogger(__name__)


class TemplateManager:
    """
    Gerenciador de templates para prompts do chatbot médico
    
    Responsabilidades:
    1. Gerenciar templates de prompts
    2. Formatar dados para templates
    3. Aplicar instruções específicas por intenção
    4. Validar dados de entrada
    """
    
    def __init__(self):
        self.templates = MedicalPromptTemplates()
        self.intent_instructions = IntentInstructions()
    
    def get_analysis_prompt(self, message: str, session: Dict, 
                           conversation_history: List, clinic_data: Dict) -> str:
        """
        Gera prompt para análise de mensagem
        
        Args:
            message: Mensagem do usuário
            session: Dados da sessão
            conversation_history: Histórico da conversa
            clinic_data: Dados da clínica
            
        Returns:
            Prompt formatado para análise
        """
        try:
            # Extrair dados da clínica
            clinic_info = clinic_data.get('clinica_info', {})
            medicos = clinic_data.get('medicos', [])
            especialidades = clinic_data.get('especialidades', [])
            
            # Estado atual da sessão
            current_state = session.get('current_state', 'idle')
            patient_name = session.get('patient_name', 'Não informado')
            selected_doctor = session.get('selected_doctor', 'Não selecionado')
            
            # Formatar histórico da conversa
            history_text = self._format_conversation_history(conversation_history)
            
            # Formatar dados da clínica
            clinic_name = clinic_info.get('nome', 'clínica médica')
            specialties_text = ', '.join([esp.get('nome', '') for esp in especialidades[:5]])
            doctors_text = ', '.join([med.get('nome', '') for med in medicos[:3]])
            
            # Formatar prompt
            prompt = self.templates.ANALYSIS_PROMPT.format(
                clinic_name=clinic_name,
                message=message,
                current_state=current_state,
                patient_name=patient_name,
                selected_doctor=selected_doctor,
                conversation_history=history_text,
                specialties=specialties_text,
                doctors=doctors_text
            )
            
            return prompt
            
        except Exception as e:
            logger.error(f"Erro ao gerar prompt de análise: {e}")
            return self._get_fallback_analysis_prompt(message, session)
    
    def get_response_prompt(self, message: str, analysis_result: Dict,
                           session: Dict, conversation_history: List,
                           clinic_data: Dict) -> str:
        """
        Gera prompt para geração de resposta
        
        Args:
            message: Mensagem do usuário
            analysis_result: Resultado da análise
            session: Dados da sessão
            conversation_history: Histórico da conversa
            clinic_data: Dados da clínica
            
        Returns:
            Prompt formatado para resposta
        """
        try:
            intent = analysis_result.get('intent', 'duvida')
            next_state = analysis_result.get('next_state', 'idle')
            
            # Extrair dados da clínica
            clinic_info = clinic_data.get('clinica_info', {})
            medicos = clinic_data.get('medicos', [])
            especialidades = clinic_data.get('especialidades', [])
            exames = clinic_data.get('exames', [])
            
            # Estado atual da sessão
            current_state = session.get('current_state', 'idle')
            patient_name = session.get('patient_name', 'Não informado')
            selected_doctor = session.get('selected_doctor', 'Não selecionado')
            
            # Formatar dados da clínica
            clinic_name = clinic_info.get('nome', 'Clínica Médica')
            clinic_address = clinic_info.get('endereco', 'Endereço não informado')
            clinic_phone = clinic_info.get('telefone_contato', 'Telefone não informado')
            clinic_whatsapp = clinic_info.get('whatsapp_contato', 'WhatsApp não informado')
            
            # Formatar informações para o prompt
            doctors_info = self._format_doctors_for_prompt(medicos)
            specialties_info = self._format_specialties_for_prompt(especialidades)
            exams_info = self._format_exams_for_prompt(exames)
            
            # Obter instruções específicas da intenção
            intent_instructions = self.intent_instructions.get_instructions(intent)
            
            # Formatar prompt
            prompt = self.templates.RESPONSE_PROMPT.format(
                clinic_name=clinic_name,
                current_state=current_state,
                next_state=next_state,
                intent=intent,
                patient_name=patient_name,
                selected_doctor=selected_doctor,
                message=message,
                clinic_address=clinic_address,
                clinic_phone=clinic_phone,
                clinic_whatsapp=clinic_whatsapp,
                doctors_info=doctors_info,
                specialties_info=specialties_info,
                exams_info=exams_info,
                intent_instructions=intent_instructions
            )
            
            return prompt
            
        except Exception as e:
            logger.error(f"Erro ao gerar prompt de resposta: {e}")
            return self._get_fallback_response_prompt(message)
    
    def get_appointment_confirmation_prompt(self, patient_name: str, doctor_name: str,
                                          appointment_date: str, appointment_time: str,
                                          appointment_type: str, clinic_name: str) -> str:
        """
        Gera prompt para confirmação de agendamento
        
        Args:
            patient_name: Nome do paciente
            doctor_name: Nome do médico
            appointment_date: Data do agendamento
            appointment_time: Horário do agendamento
            appointment_type: Tipo do agendamento
            clinic_name: Nome da clínica
            
        Returns:
            Prompt formatado para confirmação
        """
        try:
            prompt = self.templates.APPOINTMENT_CONFIRMATION_PROMPT.format(
                clinic_name=clinic_name,
                patient_name=patient_name,
                doctor_name=doctor_name,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                appointment_type=appointment_type
            )
            
            return prompt
            
        except Exception as e:
            logger.error(f"Erro ao gerar prompt de confirmação: {e}")
            return f"Confirme o agendamento: {patient_name} com {doctor_name} em {appointment_date} às {appointment_time}"
    
    def get_info_search_prompt(self, query: str, clinic_data: Dict) -> str:
        """
        Gera prompt para busca de informações
        
        Args:
            query: Consulta do usuário
            clinic_data: Dados da clínica
            
        Returns:
            Prompt formatado para busca
        """
        try:
            # Formatar dados da clínica para o prompt
            clinic_data_text = self._format_clinic_data_for_prompt(clinic_data)
            
            prompt = self.templates.INFO_SEARCH_PROMPT.format(
                query=query,
                clinic_data=clinic_data_text
            )
            
            return prompt
            
        except Exception as e:
            logger.error(f"Erro ao gerar prompt de busca: {e}")
            return f"Responda sobre: {query}"
    
    def get_greeting_prompt(self, clinic_data: Dict) -> str:
        """
        Gera prompt para saudação inicial
        
        Args:
            clinic_data: Dados da clínica
            
        Returns:
            Prompt formatado para saudação
        """
        try:
            clinic_info = clinic_data.get('clinica_info', {})
            especialidades = clinic_data.get('especialidades', [])
            
            clinic_name = clinic_info.get('nome', 'Clínica Médica')
            clinic_hours = clinic_info.get('horario_funcionamento', 'Horário não informado')
            specialties_text = ', '.join([esp.get('nome', '') for esp in especialidades[:3]])
            
            prompt = self.templates.GREETING_PROMPT.format(
                clinic_name=clinic_name,
                specialties=specialties_text,
                clinic_hours=clinic_hours
            )
            
            return prompt
            
        except Exception as e:
            logger.error(f"Erro ao gerar prompt de saudação: {e}")
            return "Gere uma saudação inicial para a clínica médica"
    
    def get_farewell_prompt(self, patient_name: str, appointment_status: str, clinic_name: str) -> str:
        """
        Gera prompt para despedida
        
        Args:
            patient_name: Nome do paciente
            appointment_status: Status do agendamento
            clinic_name: Nome da clínica
            
        Returns:
            Prompt formatado para despedida
        """
        try:
            prompt = self.templates.FAREWELL_PROMPT.format(
                clinic_name=clinic_name,
                patient_name=patient_name,
                appointment_status=appointment_status
            )
            
            return prompt
            
        except Exception as e:
            logger.error(f"Erro ao gerar prompt de despedida: {e}")
            return f"Despeça-se de {patient_name} de forma cordial"
    
    def _format_conversation_history(self, conversation_history: List) -> str:
        """Formata histórico da conversa para o prompt"""
        if not conversation_history:
            return ""
        
        history_text = "Histórico da conversa:\n"
        for msg in conversation_history[-3:]:  # Últimas 3 mensagens
            role = "Paciente" if msg.get('is_user', False) else "Assistente"
            content = msg.get('content', '')
            history_text += f"- {role}: {content}\n"
        
        return history_text
    
    def _format_doctors_for_prompt(self, medicos: List[Dict]) -> str:
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
    
    def _format_specialties_for_prompt(self, especialidades: List[Dict]) -> str:
        """Formata especialidades para o prompt"""
        if not especialidades:
            return "Nenhuma especialidade cadastrada"
        
        formatted = []
        for esp in especialidades[:5]:  # Limitar a 5 especialidades
            nome = esp.get('nome', 'Nome não informado')
            descricao = esp.get('descricao', 'Descrição não informada')
            formatted.append(f"- {nome}: {descricao}")
        
        return "\n".join(formatted)
    
    def _format_exams_for_prompt(self, exames: List[Dict]) -> str:
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
    
    def _format_clinic_data_for_prompt(self, clinic_data: Dict) -> str:
        """Formata dados da clínica para o prompt"""
        try:
            clinic_info = clinic_data.get('clinica_info', {})
            medicos = clinic_data.get('medicos', [])
            especialidades = clinic_data.get('especialidades', [])
            exames = clinic_data.get('exames', [])
            
            formatted = f"""
INFORMAÇÕES DA CLÍNICA:
- Nome: {clinic_info.get('nome', 'Clínica Médica')}
- Endereço: {clinic_info.get('endereco', 'Endereço não informado')}
- Telefone: {clinic_info.get('telefone_contato', 'Telefone não informado')}
- WhatsApp: {clinic_info.get('whatsapp_contato', 'WhatsApp não informado')}

MÉDICOS DISPONÍVEIS:
{self._format_doctors_for_prompt(medicos)}

ESPECIALIDADES:
{self._format_specialties_for_prompt(especialidades)}

EXAMES DISPONÍVEIS:
{self._format_exams_for_prompt(exames)}
            """
            
            return formatted.strip()
            
        except Exception as e:
            logger.error(f"Erro ao formatar dados da clínica: {e}")
            return "Dados da clínica não disponíveis"
    
    def _get_fallback_analysis_prompt(self, message: str, session: Dict) -> str:
        """Prompt de fallback para análise"""
        return f"""
        Analise a mensagem: "{message}"
        
        Estado da sessão: {session.get('current_state', 'idle')}
        
        Responda com JSON contendo:
        - intent: intenção detectada
        - next_state: próximo estado
        - entities: entidades extraídas
        - confidence: nível de confiança
        """
    
    def _get_fallback_response_prompt(self, message: str) -> str:
        """Prompt de fallback para resposta"""
        return f"""
        Responda à mensagem: "{message}"
        
        Seja cordial, profissional e prestativo.
        Use linguagem clara e acessível.
        """
    
    def validate_template_data(self, data: Dict[str, Any]) -> bool:
        """
        Valida dados para templates
        
        Args:
            data: Dados a serem validados
            
        Returns:
            True se válido, False caso contrário
        """
        try:
            required_fields = ['message', 'session', 'clinic_data']
            for field in required_fields:
                if field not in data:
                    logger.warning(f"Campo obrigatório '{field}' não encontrado")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Erro na validação de dados: {e}")
            return False


# Instância global do gerenciador
template_manager = TemplateManager()
