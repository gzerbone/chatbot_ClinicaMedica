"""
Testes para Sistema de Templates LangChain
"""
from unittest.mock import MagicMock, patch

from django.test import TestCase

from langchain_integration.prompts.medical_prompts import IntentInstructions
from langchain_integration.prompts.template_manager import TemplateManager


class TemplateManagerTestCase(TestCase):
    """Testes para o TemplateManager"""
    
    def setUp(self):
        """Configuração inicial dos testes"""
        self.template_manager = TemplateManager()
        
        # Dados de teste
        self.test_message = "Quero agendar com cardiologista"
        self.test_session = {
            'current_state': 'idle',
            'patient_name': None,
            'selected_doctor': None
        }
        self.test_conversation_history = [
            {'is_user': True, 'content': 'Oi'},
            {'is_user': False, 'content': 'Olá! Como posso ajudar?'}
        ]
        self.test_clinic_data = {
            'clinica_info': {
                'nome': 'Clínica Teste',
                'endereco': 'Rua Teste, 123',
                'telefone_contato': '11999999999',
                'whatsapp_contato': '11999999999'
            },
            'medicos': [
                {
                    'nome': 'Dr. João Silva',
                    'especialidades_display': 'Cardiologia',
                    'preco_particular': '150.00'
                }
            ],
            'especialidades': [
                {'nome': 'Cardiologia', 'descricao': 'Especialidade do coração'}
            ],
            'exames': [
                {'nome': 'Hemograma', 'preco': '50.00', 'duracao_formatada': '30 min'}
            ]
        }
    
    def test_get_analysis_prompt(self):
        """Testa geração de prompt de análise"""
        prompt = self.template_manager.get_analysis_prompt(
            self.test_message,
            self.test_session,
            self.test_conversation_history,
            self.test_clinic_data
        )
        
        # Verificar se o prompt contém elementos essenciais
        self.assertIn("Análise da mensagem", prompt)
        self.assertIn(self.test_message, prompt)
        self.assertIn("Clínica Teste", prompt)
        self.assertIn("Cardiologia", prompt)
        self.assertIn("JSON válido", prompt)
    
    def test_get_response_prompt(self):
        """Testa geração de prompt de resposta"""
        analysis_result = {
            'intent': 'agendar_consulta',
            'next_state': 'selecionando_medico',
            'entities': {'especialidade': 'cardiologia'}
        }
        
        prompt = self.template_manager.get_response_prompt(
            self.test_message,
            analysis_result,
            self.test_session,
            self.test_conversation_history,
            self.test_clinic_data
        )
        
        # Verificar se o prompt contém elementos essenciais
        self.assertIn("agendar_consulta", prompt)
        self.assertIn("selecionando_medico", prompt)
        self.assertIn("Dr. João Silva", prompt)
        self.assertIn("Cardiologia", prompt)
    
    def test_get_appointment_confirmation_prompt(self):
        """Testa geração de prompt de confirmação"""
        prompt = self.template_manager.get_appointment_confirmation_prompt(
            patient_name="João Silva",
            doctor_name="Dr. João",
            appointment_date="15/09/2024",
            appointment_time="14:00",
            appointment_type="Consulta",
            clinic_name="Clínica Teste"
        )
        
        # Verificar se o prompt contém elementos essenciais
        self.assertIn("João Silva", prompt)
        self.assertIn("Dr. João", prompt)
        self.assertIn("15/09/2024", prompt)
        self.assertIn("14:00", prompt)
        self.assertIn("Clínica Teste", prompt)
    
    def test_get_info_search_prompt(self):
        """Testa geração de prompt de busca"""
        prompt = self.template_manager.get_info_search_prompt(
            query="endereço da clínica",
            clinic_data=self.test_clinic_data
        )
        
        # Verificar se o prompt contém elementos essenciais
        self.assertIn("endereço da clínica", prompt)
        self.assertIn("Clínica Teste", prompt)
        self.assertIn("Rua Teste, 123", prompt)
    
    def test_get_greeting_prompt(self):
        """Testa geração de prompt de saudação"""
        prompt = self.template_manager.get_greeting_prompt(self.test_clinic_data)
        
        # Verificar se o prompt contém elementos essenciais
        self.assertIn("Clínica Teste", prompt)
        self.assertIn("Cardiologia", prompt)
        self.assertIn("saudação", prompt.lower())
    
    def test_get_farewell_prompt(self):
        """Testa geração de prompt de despedida"""
        prompt = self.template_manager.get_farewell_prompt(
            patient_name="João Silva",
            appointment_status="confirmado",
            clinic_name="Clínica Teste"
        )
        
        # Verificar se o prompt contém elementos essenciais
        self.assertIn("João Silva", prompt)
        self.assertIn("confirmado", prompt)
        self.assertIn("Clínica Teste", prompt)
    
    def test_format_conversation_history(self):
        """Testa formatação do histórico da conversa"""
        history_text = self.template_manager._format_conversation_history(
            self.test_conversation_history
        )
        
        self.assertIn("Histórico da conversa", history_text)
        self.assertIn("Paciente: Oi", history_text)
        self.assertIn("Assistente: Olá! Como posso ajudar?", history_text)
    
    def test_format_doctors_for_prompt(self):
        """Testa formatação de médicos para prompt"""
        doctors_text = self.template_manager._format_doctors_for_prompt(
            self.test_clinic_data['medicos']
        )
        
        self.assertIn("Dr. João Silva", doctors_text)
        self.assertIn("Cardiologia", doctors_text)
        self.assertIn("R$ 150.00", doctors_text)
    
    def test_format_specialties_for_prompt(self):
        """Testa formatação de especialidades para prompt"""
        specialties_text = self.template_manager._format_specialties_for_prompt(
            self.test_clinic_data['especialidades']
        )
        
        self.assertIn("Cardiologia", specialties_text)
        self.assertIn("Especialidade do coração", specialties_text)
    
    def test_format_exams_for_prompt(self):
        """Testa formatação de exames para prompt"""
        exams_text = self.template_manager._format_exams_for_prompt(
            self.test_clinic_data['exames']
        )
        
        self.assertIn("Hemograma", exams_text)
        self.assertIn("R$ 50.00", exams_text)
        self.assertIn("30 min", exams_text)
    
    def test_validate_template_data(self):
        """Testa validação de dados para templates"""
        # Dados válidos
        valid_data = {
            'message': 'Teste',
            'session': {},
            'clinic_data': {}
        }
        self.assertTrue(self.template_manager.validate_template_data(valid_data))
        
        # Dados inválidos (faltando campo obrigatório)
        invalid_data = {
            'message': 'Teste',
            'session': {}
            # clinic_data faltando
        }
        self.assertFalse(self.template_manager.validate_template_data(invalid_data))
    
    def test_fallback_prompts(self):
        """Testa prompts de fallback"""
        # Teste prompt de análise de fallback
        fallback_analysis = self.template_manager._get_fallback_analysis_prompt(
            "Teste", {}
        )
        self.assertIn("Teste", fallback_analysis)
        self.assertIn("JSON", fallback_analysis)
        
        # Teste prompt de resposta de fallback
        fallback_response = self.template_manager._get_fallback_response_prompt(
            "Teste"
        )
        self.assertIn("Teste", fallback_response)
        self.assertIn("cordial", fallback_response)


class IntentInstructionsTestCase(TestCase):
    """Testes para IntentInstructions"""
    
    def test_get_instructions(self):
        """Testa obtenção de instruções por intenção"""
        # Teste intenção existente
        instructions = IntentInstructions.get_instructions('saudacao')
        self.assertIn('Cumprimente', instructions)
        self.assertIn('Apresente-se', instructions)
        
        # Teste intenção não existente (deve retornar instruções de dúvida)
        instructions = IntentInstructions.get_instructions('intencao_inexistente')
        self.assertIn('educado', instructions)
        self.assertIn('esclarecimentos', instructions)
    
    def test_all_intentions_have_instructions(self):
        """Testa se todas as intenções têm instruções"""
        intentions = [
            'saudacao', 'buscar_info', 'agendar_consulta', 'confirmar_agendamento',
            'buscar_medico', 'buscar_exame', 'buscar_horarios', 'cancelar_agendamento',
            'despedida', 'duvida'
        ]
        
        for intention in intentions:
            instructions = IntentInstructions.get_instructions(intention)
            self.assertIsNotNone(instructions)
            self.assertGreater(len(instructions.strip()), 0)
    
    def test_instructions_content(self):
        """Testa conteúdo das instruções"""
        # Teste instruções de agendamento
        agendar_instructions = IntentInstructions.get_instructions('agendar_consulta')
        self.assertIn('processo de agendamento', agendar_instructions)
        self.assertIn('nome completo', agendar_instructions)
        
        # Teste instruções de busca de médico
        medico_instructions = IntentInstructions.get_instructions('buscar_medico')
        self.assertIn('médicos disponíveis', medico_instructions)
        self.assertIn('especialidades', medico_instructions)
        
        # Teste instruções de busca de exame
        exame_instructions = IntentInstructions.get_instructions('buscar_exame')
        self.assertIn('procedimento', exame_instructions)
        self.assertIn('preparação', exame_instructions)
