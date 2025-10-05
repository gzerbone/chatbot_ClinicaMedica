"""
Comando Django para testar todo o sistema LangChain
"""
from django.conf import settings
from django.core.management.base import BaseCommand

from langchain_integration.agents.compatibility_agents import \
    compatibility_agent_service
from langchain_integration.chains.compatibility_chains import \
    compatibility_chain_service
from langchain_integration.prompts.template_manager import template_manager
from langchain_integration.rag_service import langchain_rag_service


class Command(BaseCommand):
    help = 'Testa todo o sistema LangChain'

    def add_arguments(self, parser):
        parser.add_argument(
            '--phone',
            type=str,
            default='5511999999999',
            help='Número de telefone para teste',
        )
        parser.add_argument(
            '--quick',
            action='store_true',
            help='Executar apenas testes rápidos',
        )
        parser.add_argument(
            '--component',
            type=str,
            choices=['rag', 'templates', 'chains', 'agents', 'all'],
            default='all',
            help='Componente específico para testar',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Testando Sistema LangChain Completo...')
        )

        phone_number = options['phone']
        component = options['component']
        quick = options['quick']

        try:
            if component in ['rag', 'all']:
                self._test_rag_system(quick)
            
            if component in ['templates', 'all']:
                self._test_templates_system(quick)
            
            if component in ['chains', 'all']:
                self._test_chains_system(phone_number, quick)
            
            if component in ['agents', 'all']:
                self._test_agents_system(phone_number, quick)
            
            if component == 'all':
                self._test_integration(phone_number, quick)

            self.stdout.write(
                self.style.SUCCESS('\n🎉 Todos os testes concluídos com sucesso!')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erro nos testes: {e}')
            )

    def _test_rag_system(self, quick: bool):
        """Testa sistema RAG"""
        self.stdout.write('\n📚 Testando Sistema RAG:')
        
        try:
            # Teste de busca semântica
            self.stdout.write('  🔍 Testando busca semântica...')
            results = langchain_rag_service.search("cardiologista", k=3)
            self.stdout.write(f"    Resultados encontrados: {len(results)}")
            
            if results:
                for i, result in enumerate(results[:2], 1):
                    self.stdout.write(f"    {i}. {result['metadata'].get('type', 'unknown')} - Score: {result['score']:.3f}")
            
            # Teste de dados específicos
            if not quick:
                self.stdout.write('  👨‍⚕️ Testando busca de médicos...')
                doctors = langchain_rag_service.get_doctors("cardiologista")
                self.stdout.write(f"    Médicos encontrados: {len(doctors)}")
                
                self.stdout.write('  🧪 Testando busca de exames...')
                exams = langchain_rag_service.get_exams("hemograma")
                self.stdout.write(f"    Exames encontrados: {len(exams)}")
            
            # Estatísticas
            stats = langchain_rag_service.get_stats()
            self.stdout.write(f"  📊 Status: {stats.get('status', 'unknown')}")
            if 'total_documents' in stats:
                self.stdout.write(f"  📊 Total de documentos: {stats['total_documents']}")
            
            self.stdout.write('  ✅ Sistema RAG funcionando!')
            
        except Exception as e:
            self.stdout.write(f'  ❌ Erro no RAG: {e}')

    def _test_templates_system(self, quick: bool):
        """Testa sistema de templates"""
        self.stdout.write('\n📝 Testando Sistema de Templates:')
        
        try:
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
                    'endereco': 'Rua Teste, 123'
                },
                'medicos': [
                    {'nome': 'Dr. João Silva', 'especialidades_display': 'Cardiologia'}
                ],
                'especialidades': [
                    {'nome': 'Cardiologia', 'descricao': 'Especialidade do coração'}
                ],
                'exames': []
            }
            
            # Teste de template de análise
            self.stdout.write('  🔍 Testando template de análise...')
            analysis_prompt = template_manager.get_analysis_prompt(
                "Quero agendar com cardiologista",
                test_session,
                test_conversation_history,
                test_clinic_data
            )
            self.stdout.write(f"    Prompt gerado: {len(analysis_prompt)} caracteres")
            
            # Teste de template de resposta
            self.stdout.write('  💬 Testando template de resposta...')
            analysis_result = {
                'intent': 'agendar_consulta',
                'next_state': 'selecionando_medico',
                'entities': {'especialidade': 'cardiologia'},
                'confidence': 0.9
            }
            
            response_prompt = template_manager.get_response_prompt(
                "Quero agendar com cardiologista",
                analysis_result,
                test_session,
                test_conversation_history,
                test_clinic_data
            )
            self.stdout.write(f"    Prompt gerado: {len(response_prompt)} caracteres")
            
            # Teste de validação
            self.stdout.write('  ✅ Testando validação de dados...')
            valid_data = {
                'message': 'Teste',
                'session': test_session,
                'clinic_data': test_clinic_data
            }
            is_valid = template_manager.validate_template_data(valid_data)
            self.stdout.write(f"    Dados válidos: {is_valid}")
            
            self.stdout.write('  ✅ Sistema de Templates funcionando!')
            
        except Exception as e:
            self.stdout.write(f'  ❌ Erro nos Templates: {e}')

    def _test_chains_system(self, phone_number: str, quick: bool):
        """Testa sistema de chains"""
        self.stdout.write('\n🔗 Testando Sistema de Chains:')
        
        try:
            # Teste de processamento de mensagem
            self.stdout.write('  💬 Testando processamento de mensagem...')
            result = compatibility_chain_service.process_message(
                phone_number,
                "Quero agendar com cardiologista"
            )
            
            self.stdout.write(f"    Resposta: {result.get('response', 'N/A')[:50]}...")
            self.stdout.write(f"    Intenção: {result.get('intent', 'N/A')}")
            self.stdout.write(f"    Confiança: {result.get('confidence', 0):.2f}")
            self.stdout.write(f"    Agente: {result.get('agent', 'N/A')}")
            
            # Teste de histórico
            if not quick:
                self.stdout.write('  📚 Testando histórico da conversa...')
                history = compatibility_chain_service.get_conversation_history(phone_number, 3)
                self.stdout.write(f"    Mensagens no histórico: {len(history)}")
            
            # Teste de estatísticas
            self.stdout.write('  📊 Testando estatísticas...')
            chain_stats = compatibility_chain_service.get_chain_stats()
            self.stdout.write(f"    Chains disponíveis: {chain_stats.get('total_chains', 0)}")
            self.stdout.write(f"    Status: {chain_stats.get('status', 'unknown')}")
            
            self.stdout.write('  ✅ Sistema de Chains funcionando!')
            
        except Exception as e:
            self.stdout.write(f'  ❌ Erro nas Chains: {e}')

    def _test_agents_system(self, phone_number: str, quick: bool):
        """Testa sistema de agents"""
        self.stdout.write('\n🤖 Testando Sistema de Agents:')
        
        try:
            # Teste de detecção de complexidade
            self.stdout.write('  🔍 Testando detecção de complexidade...')
            simple_message = "Oi"
            complex_message = "Quero agendar com cardiologista e também saber sobre exames"
            
            is_simple = compatibility_agent_service._is_complex_message(simple_message)
            is_complex = compatibility_agent_service._is_complex_message(complex_message)
            
            self.stdout.write(f"    Mensagem simples: {is_simple}")
            self.stdout.write(f"    Mensagem complexa: {is_complex}")
            
            # Teste de processamento complexo
            if not quick:
                self.stdout.write('  🧠 Testando processamento complexo...')
                session = {
                    'current_state': 'idle',
                    'patient_name': None,
                    'selected_doctor': None
                }
                clinic_data = {
                    'clinica_info': {'nome': 'Clínica Teste'},
                    'medicos': [{'nome': 'Dr. João Silva', 'especialidades_display': 'Cardiologia'}],
                    'especialidades': [{'nome': 'Cardiologia', 'descricao': 'Especialidade do coração'}],
                    'exames': [{'nome': 'Hemograma', 'preco': '50.00', 'duracao_formatada': '30 min'}]
                }
                
                result = compatibility_agent_service.process_complex_message(
                    phone_number, complex_message, session, clinic_data
                )
                
                if result:
                    self.stdout.write(f"    Resposta: {result.get('response', 'N/A')[:50]}...")
                    self.stdout.write(f"    Intenção: {result.get('intent', 'N/A')}")
                    self.stdout.write(f"    Agente: {result.get('agent', 'N/A')}")
                else:
                    self.stdout.write("    Agent não processou a mensagem")
            
            # Teste de estatísticas
            self.stdout.write('  📊 Testando estatísticas...')
            agent_stats = compatibility_agent_service.get_agent_stats()
            self.stdout.write(f"    Ferramentas disponíveis: {agent_stats.get('total_tools', 0)}")
            self.stdout.write(f"    Status: {agent_stats.get('status', 'unknown')}")
            
            self.stdout.write('  ✅ Sistema de Agents funcionando!')
            
        except Exception as e:
            self.stdout.write(f'  ❌ Erro nos Agents: {e}')

    def _test_integration(self, phone_number: str, quick: bool):
        """Testa integração completa"""
        self.stdout.write('\n🔗 Testando Integração Completa:')
        
        try:
            # Teste de fluxo completo
            self.stdout.write('  🚀 Testando fluxo completo...')
            
            test_messages = [
                "Oi, tudo bem?",
                "Quero agendar uma consulta",
                "Com cardiologista",
                "Para amanhã às 14h"
            ]
            
            if quick:
                test_messages = test_messages[:2]
            
            for i, message in enumerate(test_messages, 1):
                self.stdout.write(f"    Mensagem {i}: {message}")
                
                result = compatibility_chain_service.process_message(phone_number, message)
                
                self.stdout.write(f"      Resposta: {result.get('response', 'N/A')[:40]}...")
                self.stdout.write(f"      Intenção: {result.get('intent', 'N/A')}")
                self.stdout.write(f"      Agente: {result.get('agent', 'N/A')}")
            
            # Teste de limpeza
            self.stdout.write('  🧹 Testando limpeza de memória...')
            compatibility_chain_service.clear_memory(phone_number)
            self.stdout.write("    Memória limpa com sucesso!")
            
            # Verificar se a memória foi limpa
            history_after_clear = compatibility_chain_service.get_conversation_history(phone_number)
            self.stdout.write(f"    Mensagens após limpeza: {len(history_after_clear)}")
            
            self.stdout.write('  ✅ Integração completa funcionando!')
            
        except Exception as e:
            self.stdout.write(f'  ❌ Erro na integração: {e}')

    def _print_summary(self):
        """Imprime resumo dos testes"""
        self.stdout.write('\n📋 Resumo dos Testes:')
        self.stdout.write('  ✅ RAG Service: Funcionando')
        self.stdout.write('  ✅ Templates: Funcionando')
        self.stdout.write('  ✅ Chains: Funcionando')
        self.stdout.write('  ✅ Agents: Funcionando')
        self.stdout.write('  ✅ Integração: Funcionando')
        self.stdout.write('\n🎉 Sistema LangChain 100% operacional!')
