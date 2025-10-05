"""
Comando Django para configurar LangChain
"""
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from langchain_integration.rag_service import langchain_rag_service


class Command(BaseCommand):
    help = 'Configura e inicializa o LangChain RAG Service'

    def add_arguments(self, parser):
        parser.add_argument(
            '--refresh',
            action='store_true',
            help='Recriar o vector store do zero',
        )
        parser.add_argument(
            '--stats',
            action='store_true',
            help='Mostrar estatísticas do vector store',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Iniciando configuração do LangChain...')
        )

        # Verificar configurações
        if not hasattr(settings, 'GEMINI_API_KEY') or not settings.GEMINI_API_KEY:
            self.stdout.write(
                self.style.ERROR('❌ GEMINI_API_KEY não configurada nas settings')
            )
            return

        try:
            if options['refresh']:
                self.stdout.write('🔄 Recriando vector store...')
                langchain_rag_service.refresh_vectorstore()
                self.stdout.write(
                    self.style.SUCCESS('✅ Vector store recriado com sucesso!')
                )

            if options['stats']:
                stats = langchain_rag_service.get_stats()
                self.stdout.write('\n📊 Estatísticas do Vector Store:')
                self.stdout.write(f"Status: {stats.get('status', 'unknown')}")
                if 'total_documents' in stats:
                    self.stdout.write(f"Total de documentos: {stats['total_documents']}")
                if 'embedding_dimension' in stats:
                    self.stdout.write(f"Dimensão dos embeddings: {stats['embedding_dimension']}")

            # Teste básico
            self.stdout.write('\n🧪 Testando busca semântica...')
            test_results = langchain_rag_service.search("cardiologista", k=2)
            if test_results:
                self.stdout.write(f"✅ Busca funcionando! Encontrados {len(test_results)} resultados")
                for i, result in enumerate(test_results[:2], 1):
                    self.stdout.write(f"  {i}. {result['metadata'].get('type', 'unknown')} - Score: {result['score']:.3f}")
            else:
                self.stdout.write(self.style.WARNING('⚠️ Nenhum resultado encontrado na busca de teste'))

            self.stdout.write(
                self.style.SUCCESS('\n🎉 LangChain configurado com sucesso!')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erro na configuração: {e}')
            )
