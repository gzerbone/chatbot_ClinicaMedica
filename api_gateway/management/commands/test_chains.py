"""
Comando Django para testar chains LangChain
"""
from django.conf import settings
from django.core.management.base import BaseCommand

from langchain_integration.chains.compatibility_chains import \
    compatibility_chain_service


class Command(BaseCommand):
    help = 'Testa o sistema de chains LangChain'

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
            default='Quero agendar com cardiologista',
            help='Mensagem de teste',
        )
        parser.add_argument(
            '--stats',
            action='store_true',
            help='Mostrar estatísticas das chains',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔗 Testando sistema de chains LangChain...')
        )

        phone_number = options['phone']
        message = options['message']

        try:
            if options['stats']:
                self.stdout.write('\n📊 Estatísticas das Chains:')
                chain_stats = compatibility_chain_service.get_chain_stats()
                for key, value in chain_stats.items():
                    self.stdout.write(f"  {key}: {value}")
                
                self.stdout.write('\n📊 Estatísticas da Memória:')
                memory_stats = compatibility_chain_service.get_memory_stats(phone_number)
                for key, value in memory_stats.items():
                    self.stdout.write(f"  {key}: {value}")
                
                return

            # Teste de processamento de mensagem
            self.stdout.write(f'\n💬 Testando processamento de mensagem:')
            self.stdout.write(f"Telefone: {phone_number}")
            self.stdout.write(f"Mensagem: {message}")
            
            result = compatibility_chain_service.process_message(phone_number, message)
            
            # Exibir resultado
            self.stdout.write(f"\n📋 Resultado:")
            self.stdout.write(f"  Resposta: {result.get('response', 'N/A')[:100]}...")
            self.stdout.write(f"  Intenção: {result.get('intent', 'N/A')}")
            self.stdout.write(f"  Confiança: {result.get('confidence', 0):.2f}")
            self.stdout.write(f"  Estado: {result.get('state', 'N/A')}")
            self.stdout.write(f"  Agente: {result.get('agent', 'N/A')}")
            
            # Teste de histórico
            self.stdout.write(f"\n📚 Testando histórico da conversa:")
            history = compatibility_chain_service.get_conversation_history(phone_number, 3)
            self.stdout.write(f"  Total de mensagens: {len(history)}")
            for i, msg in enumerate(history[-2:], 1):  # Últimas 2 mensagens
                role = "Usuário" if msg.get('is_user') else "Bot"
                content = msg.get('content', '')[:50]
                self.stdout.write(f"  {i}. {role}: {content}...")
            
            # Teste de estatísticas da memória
            self.stdout.write(f"\n📊 Estatísticas da Memória:")
            memory_stats = compatibility_chain_service.get_memory_stats(phone_number)
            for key, value in memory_stats.items():
                self.stdout.write(f"  {key}: {value}")
            
            # Teste de múltiplas mensagens
            self.stdout.write(f"\n🔄 Testando múltiplas mensagens:")
            test_messages = [
                "Oi, tudo bem?",
                "Quero agendar uma consulta",
                "Com cardiologista",
                "Para amanhã às 14h"
            ]
            
            for i, test_msg in enumerate(test_messages, 1):
                self.stdout.write(f"\n  Mensagem {i}: {test_msg}")
                result = compatibility_chain_service.process_message(phone_number, test_msg)
                self.stdout.write(f"    Resposta: {result.get('response', 'N/A')[:80]}...")
                self.stdout.write(f"    Intenção: {result.get('intent', 'N/A')}")
            
            # Teste de limpeza de memória
            self.stdout.write(f"\n🧹 Testando limpeza de memória:")
            compatibility_chain_service.clear_memory(phone_number)
            self.stdout.write("  Memória limpa com sucesso!")
            
            # Verificar se a memória foi limpa
            history_after_clear = compatibility_chain_service.get_conversation_history(phone_number)
            self.stdout.write(f"  Mensagens após limpeza: {len(history_after_clear)}")

            self.stdout.write(
                self.style.SUCCESS('\n🎉 Testes de chains concluídos com sucesso!')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erro nos testes: {e}')
            )
