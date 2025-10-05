"""
Comando Django para testar agents LangChain
"""
from django.conf import settings
from django.core.management.base import BaseCommand

from langchain_integration.agents.compatibility_agents import \
    compatibility_agent_service


class Command(BaseCommand):
    help = 'Testa o sistema de agents LangChain'

    def add_arguments(self, parser):
        parser.add_argument(
            '--phone',
            type=str,
            default='5511999999999',
            help='Número de telefone para teste',
        )
        parser.add_argument(
            '--message',
            type=str,
            help='Mensagem de teste (se não fornecida, usa mensagens padrão)',
        )
        parser.add_argument(
            '--stats',
            action='store_true',
            help='Mostrar estatísticas dos agents',
        )
        parser.add_argument(
            '--test-tools',
            action='store_true',
            help='Testar ferramentas dos agents',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🤖 Testando sistema de agents LangChain...')
        )

        phone_number = options['phone']

        try:
            if options['stats']:
                self.stdout.write('\n📊 Estatísticas dos Agents:')
                agent_stats = compatibility_agent_service.get_agent_stats()
                for key, value in agent_stats.items():
                    self.stdout.write(f"  {key}: {value}")
                return

            if options['test_tools']:
                self.stdout.write('\n🔧 Testando Ferramentas dos Agents:')
                tool_results = compatibility_agent_service.test_agent_tools()
                for tool_name, result in tool_results.items():
                    self.stdout.write(f"\n  {tool_name}:")
                    if result['status'] == 'success':
                        self.stdout.write(f"    Status: ✅ {result['status']}")
                        self.stdout.write(f"    Resultado: {result['result_preview']}")
                    else:
                        self.stdout.write(f"    Status: ❌ {result['status']}")
                        self.stdout.write(f"    Erro: {result['error']}")
                return

            # Teste de mensagens complexas
            test_messages = [
                "Quero agendar com cardiologista e também saber sobre exames disponíveis",
                "Qual é o melhor médico especialista em cardiologia e quanto custa uma consulta?",
                "Preciso de um exame para verificar o coração e também quero saber o endereço da clínica",
                "Quero agendar para amanhã às 14h com um cardiologista e também preciso saber sobre preparação para exames",
                "Oi, tudo bem? Quero agendar uma consulta"
            ]

            if options['message']:
                test_messages = [options['message']]

            for i, message in enumerate(test_messages, 1):
                self.stdout.write(f'\n💬 Teste {i}: {message}')
                
                # Verificar se é mensagem complexa
                is_complex = compatibility_agent_service._is_complex_message(message)
                self.stdout.write(f"  Complexa: {'✅ Sim' if is_complex else '❌ Não'}")
                
                if is_complex:
                    # Simular dados de sessão e clínica
                    session = {
                        'current_state': 'idle',
                        'patient_name': None,
                        'selected_doctor': None
                    }
                    clinic_data = {
                        'clinica_info': {
                            'nome': 'Clínica Teste',
                            'endereco': 'Rua Teste, 123',
                            'telefone_contato': '11999999999'
                        },
                        'medicos': [
                            {'nome': 'Dr. João Silva', 'especialidades_display': 'Cardiologia'}
                        ],
                        'especialidades': [
                            {'nome': 'Cardiologia', 'descricao': 'Especialidade do coração'}
                        ],
                        'exames': [
                            {'nome': 'Hemograma', 'preco': '50.00', 'duracao_formatada': '30 min'}
                        ]
                    }
                    
                    # Processar mensagem complexa
                    result = compatibility_agent_service.process_complex_message(
                        phone_number, message, session, clinic_data
                    )
                    
                    if result:
                        self.stdout.write(f"  Resposta: {result.get('response', 'N/A')[:100]}...")
                        self.stdout.write(f"  Intenção: {result.get('intent', 'N/A')}")
                        self.stdout.write(f"  Confiança: {result.get('confidence', 0):.2f}")
                        self.stdout.write(f"  Agente: {result.get('agent', 'N/A')}")
                        
                        # Mostrar ferramentas usadas
                        tools_used = result.get('tools_used', [])
                        if tools_used:
                            self.stdout.write(f"  Ferramentas usadas: {len(tools_used)}")
                            for step in tools_used[:2]:  # Mostrar apenas as primeiras 2
                                if isinstance(step, list) and len(step) >= 2:
                                    action = step[0].get('tool', 'unknown') if isinstance(step[0], dict) else 'unknown'
                                    self.stdout.write(f"    - {action}")
                    else:
                        self.stdout.write("  ❌ Agent não processou a mensagem")
                else:
                    self.stdout.write("  ℹ️ Mensagem não é complexa o suficiente para usar agent")

            # Teste de detecção de complexidade
            self.stdout.write(f'\n🔍 Testando Detecção de Complexidade:')
            test_cases = [
                ("Oi", False),
                ("Quero agendar", False),
                ("Quero agendar e também saber sobre exames", True),
                ("Qual é o melhor médico especialista em cardiologia?", True),
                ("Quanto custa uma consulta?", True),
                ("Olá, gostaria de agendar uma consulta com um cardiologista para amanhã às 14h e também quero saber sobre os exames disponíveis", True)
            ]
            
            for message, expected in test_cases:
                is_complex = compatibility_agent_service._is_complex_message(message)
                status = "✅" if is_complex == expected else "❌"
                self.stdout.write(f"  {status} '{message[:30]}...' -> {is_complex} (esperado: {expected})")

            self.stdout.write(
                self.style.SUCCESS('\n🎉 Testes de agents concluídos com sucesso!')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erro nos testes: {e}')
            )
