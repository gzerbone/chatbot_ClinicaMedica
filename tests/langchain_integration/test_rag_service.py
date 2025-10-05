"""
Testes para LangChain RAG Service
"""
import os
import tempfile
from unittest.mock import MagicMock, patch

from django.conf import settings
from django.test import TestCase

from langchain_integration.compatibility_service import CompatibilityRAGService
from langchain_integration.rag_service import LangChainRAGService


class LangChainRAGServiceTestCase(TestCase):
    """Testes para o LangChain RAG Service"""
    
    def setUp(self):
        """Configuração inicial dos testes"""
        # Mock das configurações
        self.settings_patcher = patch.object(settings, 'GEMINI_API_KEY', 'test-key')
        self.settings_patcher.start()
        
        # Mock do embeddings
        self.embeddings_patcher = patch('langchain_integration.rag_service.GoogleGenerativeAIEmbeddings')
        self.mock_embeddings = self.embeddings_patcher.start()
        
        # Mock do FAISS
        self.faiss_patcher = patch('langchain_integration.rag_service.FAISS')
        self.mock_faiss = self.faiss_patcher.start()
        
        # Mock do vector store
        self.mock_vectorstore = MagicMock()
        self.mock_faiss.from_documents.return_value = self.mock_vectorstore
        self.mock_faiss.load_local.return_value = self.mock_vectorstore
        
        # Mock dos documentos
        self.mock_docs = [
            MagicMock(page_content="Teste médico", metadata={"type": "medico"}),
            MagicMock(page_content="Teste especialidade", metadata={"type": "especialidade"})
        ]
        self.mock_vectorstore.similarity_search_with_score.return_value = [
            (self.mock_docs[0], 0.9),
            (self.mock_docs[1], 0.8)
        ]
    
    def tearDown(self):
        """Limpeza após os testes"""
        self.settings_patcher.stop()
        self.embeddings_patcher.stop()
        self.faiss_patcher.stop()
    
    def test_initialization(self):
        """Testa inicialização do serviço"""
        service = LangChainRAGService()
        self.assertIsNotNone(service.embeddings)
        self.assertIsNotNone(service.vectorstore)
    
    def test_search_functionality(self):
        """Testa funcionalidade de busca"""
        service = LangChainRAGService()
        results = service.search("cardiologista", k=2)
        
        self.assertEqual(len(results), 2)
        self.assertIn('content', results[0])
        self.assertIn('metadata', results[0])
        self.assertIn('score', results[0])
        self.assertIn('relevance', results[0])
    
    def test_get_clinic_info(self):
        """Testa obtenção de informações da clínica"""
        service = LangChainRAGService()
        
        # Teste com query
        result = service.get_clinic_info("endereço")
        self.assertIsInstance(result, dict)
        
        # Teste sem query
        result = service.get_clinic_info()
        self.assertIsInstance(result, dict)
    
    def test_get_doctors(self):
        """Testa obtenção de médicos"""
        service = LangChainRAGService()
        
        # Teste com query
        result = service.get_doctors("cardiologista")
        self.assertIsInstance(result, list)
        
        # Teste sem query
        result = service.get_doctors()
        self.assertIsInstance(result, list)
    
    def test_get_exams(self):
        """Testa obtenção de exames"""
        service = LangChainRAGService()
        
        result = service.get_exams("hemograma")
        self.assertIsInstance(result, list)
    
    def test_get_specialties(self):
        """Testa obtenção de especialidades"""
        service = LangChainRAGService()
        
        result = service.get_specialties("cardiologia")
        self.assertIsInstance(result, list)
    
    def test_get_stats(self):
        """Testa obtenção de estatísticas"""
        service = LangChainRAGService()
        
        # Mock do index
        mock_index = MagicMock()
        mock_index.ntotal = 100
        mock_index.d = 768
        service.vectorstore.index = mock_index
        
        stats = service.get_stats()
        self.assertIn('status', stats)
        self.assertIn('total_documents', stats)
        self.assertIn('embedding_dimension', stats)


class CompatibilityRAGServiceTestCase(TestCase):
    """Testes para o serviço de compatibilidade"""
    
    def setUp(self):
        """Configuração inicial dos testes"""
        self.service = CompatibilityRAGService()
    
    @patch('langchain_integration.compatibility_service.langchain_rag_service')
    def test_get_clinic_info(self, mock_rag_service):
        """Testa compatibilidade get_clinic_info"""
        mock_rag_service.get_clinic_info.return_value = {"nome": "Clínica Teste"}
        
        result = self.service.get_clinic_info()
        self.assertEqual(result["nome"], "Clínica Teste")
        mock_rag_service.get_clinic_info.assert_called_once()
    
    @patch('langchain_integration.compatibility_service.langchain_rag_service')
    def test_get_medicos(self, mock_rag_service):
        """Testa compatibilidade get_medicos"""
        mock_rag_service.get_doctors.return_value = [{"nome": "Dr. Teste"}]
        
        result = self.service.get_medicos()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["nome"], "Dr. Teste")
        mock_rag_service.get_doctors.assert_called_once()
    
    @patch('langchain_integration.compatibility_service.langchain_rag_service')
    def test_search_info(self, mock_rag_service):
        """Testa compatibilidade search_info"""
        mock_results = [
            {
                'content': 'Teste médico',
                'metadata': {'type': 'medico'},
                'score': 0.9,
                'relevance': 'high'
            }
        ]
        mock_rag_service.search.return_value = mock_results
        
        result = self.service.search_info("cardiologista")
        self.assertIn('medico', result)
        self.assertEqual(len(result['medico']), 1)
        mock_rag_service.search.assert_called_once_with("cardiologista", k=5)
    
    def test_get_all_clinic_data(self):
        """Testa obtenção de todos os dados da clínica"""
        with patch.object(self.service, 'get_clinic_info') as mock_clinic, \
             patch.object(self.service, 'get_especialidades') as mock_esp, \
             patch.object(self.service, 'get_convenios') as mock_conv, \
             patch.object(self.service, 'get_medicos') as mock_med, \
             patch.object(self.service, 'get_exames') as mock_exam, \
             patch.object(self.service, 'get_all_doctors_availability') as mock_avail:
            
            mock_clinic.return_value = {"nome": "Clínica"}
            mock_esp.return_value = [{"nome": "Cardiologia"}]
            mock_conv.return_value = [{"nome": "Unimed"}]
            mock_med.return_value = [{"nome": "Dr. Teste"}]
            mock_exam.return_value = [{"nome": "Hemograma"}]
            mock_avail.return_value = {"disponibilidade": "ok"}
            
            result = self.service.get_all_clinic_data()
            
            self.assertIn('clinica_info', result)
            self.assertIn('especialidades', result)
            self.assertIn('convenios', result)
            self.assertIn('medicos', result)
            self.assertIn('exames', result)
            self.assertIn('disponibilidade_medicos', result)
