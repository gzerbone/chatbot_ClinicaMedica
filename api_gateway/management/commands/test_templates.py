"""
Comando Django para testar templates LangChain
"""
from django.conf import settings
from django.core.management.base import BaseCommand

from langchain_integration.prompts.template_manager import template_manager


class Command(BaseCommand):
    help = 'Testa o sistema de templates LangChain'

    def add_arguments(self, parser):
        parser.add_argument(
            '--template',
            type=str,
            help='Tipo de template para testar (analysis, response, confirmation, info, greeting, farewell)',
        )
        parser.add_argument(
            '--message',
            type=str,
            default='Quero agendar com cardiologista',
            help='Mensagem de teste',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🧪 Testando sistema de templates LangChain...')
        )

        # Dados de teste
        test_session = {
            'current_state': 'idle',
            'patient_name': None,
            'selected_doctor': None
        }
        
        test_conversation_history = [
            {'is_user': True, 'content': 'Oi'},
            {'is_user': False, 'content': 'Olá! Como posso ajudar?'}
        ]
        
        test_clinic_data = {
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

        message = options['message']
        template_type = options.get('template')

        try:
            if not template_type or template_type == 'analysis':
                self.stdout.write('\n📝 Testando Template de Análise:')
                prompt = template_manager.get_analysis_prompt(
                    message, test_session, test_conversation_history, test_clinic_data
                )
                self.stdout.write(f"Prompt gerado ({len(prompt)} caracteres):")
                self.stdout.write(prompt[:500] + "..." if len(prompt) > 500 else prompt)

            if not template_type or template_type == 'response':
                self.stdout.write('\n💬 Testando Template de Resposta:')
                analysis_result = {
                    'intent': 'agendar_consulta',
                    'next_state': 'selecionando_medico',
                    'entities': {'especialidade': 'cardiologia'}
                }
                prompt = template_manager.get_response_prompt(
                    message, analysis_result, test_session, test_conversation_history, test_clinic_data
                )
                self.stdout.write(f"Prompt gerado ({len(prompt)} caracteres):")
                self.stdout.write(prompt[:500] + "..." if len(prompt) > 500 else prompt)

            if not template_type or template_type == 'confirmation':
                self.stdout.write('\n✅ Testando Template de Confirmação:')
                prompt = template_manager.get_appointment_confirmation_prompt(
                    patient_name="João Silva",
                    doctor_name="Dr. João",
                    appointment_date="15/09/2024",
                    appointment_time="14:00",
                    appointment_type="Consulta",
                    clinic_name="Clínica Teste"
                )
                self.stdout.write(f"Prompt gerado ({len(prompt)} caracteres):")
                self.stdout.write(prompt)

            if not template_type or template_type == 'info':
                self.stdout.write('\n🔍 Testando Template de Busca de Informações:')
                prompt = template_manager.get_info_search_prompt(
                    query="endereço da clínica",
                    clinic_data=test_clinic_data
                )
                self.stdout.write(f"Prompt gerado ({len(prompt)} caracteres):")
                self.stdout.write(prompt[:500] + "..." if len(prompt) > 500 else prompt)

            if not template_type or template_type == 'greeting':
                self.stdout.write('\n👋 Testando Template de Saudação:')
                prompt = template_manager.get_greeting_prompt(test_clinic_data)
                self.stdout.write(f"Prompt gerado ({len(prompt)} caracteres):")
                self.stdout.write(prompt)

            if not template_type or template_type == 'farewell':
                self.stdout.write('\n👋 Testando Template de Despedida:')
                prompt = template_manager.get_farewell_prompt(
                    patient_name="João Silva",
                    appointment_status="confirmado",
                    clinic_name="Clínica Teste"
                )
                self.stdout.write(f"Prompt gerado ({len(prompt)} caracteres):")
                self.stdout.write(prompt)

            # Teste de validação
            self.stdout.write('\n✅ Testando Validação de Dados:')
            valid_data = {
                'message': message,
                'session': test_session,
                'clinic_data': test_clinic_data
            }
            is_valid = template_manager.validate_template_data(valid_data)
            self.stdout.write(f"Dados válidos: {is_valid}")

            # Teste de formatação
            self.stdout.write('\n📋 Testando Formatação:')
            doctors_text = template_manager._format_doctors_for_prompt(test_clinic_data['medicos'])
            self.stdout.write(f"Médicos formatados: {doctors_text}")
            
            specialties_text = template_manager._format_specialties_for_prompt(test_clinic_data['especialidades'])
            self.stdout.write(f"Especialidades formatadas: {specialties_text}")

            self.stdout.write(
                self.style.SUCCESS('\n🎉 Testes de templates concluídos com sucesso!')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erro nos testes: {e}')
            )
