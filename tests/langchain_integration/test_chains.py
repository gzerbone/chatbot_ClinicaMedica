"""
Testes para Sistema de Chains LangChain
"""
from unittest.mock import MagicMock, patch

from django.test import TestCase

from langchain_integration.chains.compatibility_chains import \
    CompatibilityChainService
from langchain_integration.chains.conversation_chains import \
    ConversationChainManager
from langchain_integration.memory.conversation_memory import memory_manager


class ConversationChainManagerTestCase(TestCase):
    """Testes para o ConversationChainManager"""
    
    def setUp(self):
        """Configuração inicial dos testes"""
        # Mock do LLM
        self.llm_patcher = patch('langchain_integration.chains.conversation_chains.ChatGoogleGenerativeAI')
        self.mock_llm = self.llm_patcher.start()
        
        # Mock do template manager
        self.template_patcher = patch('langchain_integration.chains.conversation_chains.template_manager')
        self.mock_template_manager = self.template_patcher.start()
        
        # Mock do memory manager
        self.memory_patcher = patch('langchain_integration.chains.conversation_chains.memory_manager')
        self.mock_memory_manager = self.memory_patcher.start()
        
        # Dados de teste
        self.test_phone_number = "5511999999999"
        self.test_message = "Quero agendar com cardiologista"
        self.test_session = {
            'current_state': 'idle',
            'patient_name': None,
            'selected_doctor': None
        }
        self.test_clinic_data = {
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
    
    def tearDown(self):
        """Limpeza após os testes"""
        self.llm_patcher.stop()
        self.template_patcher.stop()
        self.memory_patcher.stop()
    
    def test_initialization(self):
        """Testa inicialização do gerenciador de chains"""
        with patch('langchain_integration.chains.conversation_chains.LANGCHAIN_CONFIG', {'GEMINI_API_KEY': 'test-key', 'GEMINI_MODEL': 'gemini-2.0-flash'}):
            manager = ConversationChainManager()
            self.assertIsNotNone(manager.llm)
            self.assertIsNotNone(manager.chains)
    
    def test_create_chains(self):
        """Testa criação de chains"""
        with patch('langchain_integration.chains.conversation_chains.LANGCHAIN_CONFIG', {'GEMINI_API_KEY': 'test-key', 'GEMINI_MODEL': 'gemini-2.0-flash'}):
            manager = ConversationChainManager()
            
            # Verificar se chains foram criadas
            expected_chains = ['analysis', 'response', 'confirmation', 'info_search', 'greeting', 'farewell']
            for chain_name in expected_chains:
                self.assertIn(chain_name, manager.chains)
    
    def test_process_message(self):
        """Testa processamento de mensagem"""
        with patch('langchain_integration.chains.conversation_chains.LANGCHAIN_CONFIG', {'GEMINI_API_KEY': 'test-key', 'GEMINI_MODEL': 'gemini-2.0-flash'}):
            manager = ConversationChainManager()
            
            # Mock das chains
            manager.chains['analysis'].run = MagicMock(return_value='{"intent": "agendar_consulta", "next_state": "selecionando_medico", "entities": {}, "confidence": 0.9}')
            manager.chains['response'].run = MagicMock(return_value='Resposta de teste')
            
            # Mock do memory manager
            self.mock_memory_manager.get_conversation_history.return_value = []
            self.mock_memory_manager.add_user_message.return_value = None
            self.mock_memory_manager.add_ai_message.return_value = None
            self.mock_memory_manager.sync_with_database.return_value = None
            self.mock_memory_manager.get_memory_stats.return_value = {'total_messages': 2}
            
            result = manager.process_message(
                self.test_phone_number,
                self.test_message,
                self.test_session,
                self.test_clinic_data
            )
            
            # Verificar resultado
            self.assertIn('response', result)
            self.assertIn('intent', result)
            self.assertIn('confidence', result)
            self.assertIn('agent', result)
            self.assertEqual(result['agent'], 'langchain_chains')
    
    def test_analyze_message(self):
        """Testa análise de mensagem"""
        with patch('langchain_integration.chains.conversation_chains.LANGCHAIN_CONFIG', {'GEMINI_API_KEY': 'test-key', 'GEMINI_MODEL': 'gemini-2.0-flash'}):
            manager = ConversationChainManager()
            
            # Mock da chain de análise
            manager.chains['analysis'].run = MagicMock(return_value='{"intent": "agendar_consulta", "next_state": "selecionando_medico", "entities": {"especialidade": "cardiologia"}, "confidence": 0.9}')
            
            result = manager._analyze_message(
                self.test_message,
                self.test_session,
                [],
                self.test_clinic_data
            )
            
            # Verificar resultado
            self.assertEqual(result['intent'], 'agendar_consulta')
            self.assertEqual(result['next_state'], 'selecionando_medico')
            self.assertEqual(result['entities']['especialidade'], 'cardiologia')
            self.assertEqual(result['confidence'], 0.9)
    
    def test_generate_response(self):
        """Testa geração de resposta"""
        with patch('langchain_integration.chains.conversation_chains.LANGCHAIN_CONFIG', {'GEMINI_API_KEY': 'test-key', 'GEMINI_MODEL': 'gemini-2.0-flash'}):
            manager = ConversationChainManager()
            
            # Mock das chains
            manager.chains['response'].run = MagicMock(return_value='Resposta de teste')
            
            analysis_result = {
                'intent': 'agendar_consulta',
                'next_state': 'selecionando_medico',
                'entities': {'especialidade': 'cardiologia'},
                'confidence': 0.9
            }
            
            result = manager._generate_response(
                self.test_message,
                analysis_result,
                self.test_session,
                [],
                self.test_clinic_data
            )
            
            # Verificar resultado
            self.assertIn('response', result)
            self.assertIn('intent', result)
            self.assertIn('confidence', result)
    
    def test_handle_appointment_confirmation(self):
        """Testa confirmação de agendamento"""
        with patch('langchain_integration.chains.conversation_chains.LANGCHAIN_CONFIG', {'GEMINI_API_KEY': 'test-key', 'GEMINI_MODEL': 'gemini-2.0-flash'}):
            manager = ConversationChainManager()
            
            # Mock da chain de confirmação
            manager.chains['confirmation'].run = MagicMock(return_value='Confirmação de agendamento')
            
            analysis_result = {
                'intent': 'confirmar_agendamento',
                'entities': {
                    'nome_paciente': 'João Silva',
                    'medico': 'Dr. João',
                    'data': '15/09/2024',
                    'horario': '14:00'
                }
            }
            
            result = manager._handle_appointment_confirmation(
                self.test_message,
                analysis_result,
                self.test_session,
                self.test_clinic_data
            )
            
            # Verificar resultado
            self.assertIn('response', result)
            self.assertEqual(result['intent'], 'confirmar_agendamento')
    
    def test_handle_info_search(self):
        """Testa busca de informações"""
        with patch('langchain_integration.chains.conversation_chains.LANGCHAIN_CONFIG', {'GEMINI_API_KEY': 'test-key', 'GEMINI_MODEL': 'gemini-2.0-flash'}):
            manager = ConversationChainManager()
            
            # Mock da chain de busca
            manager.chains['info_search'].run = MagicMock(return_value='Informações encontradas')
            
            analysis_result = {
                'intent': 'buscar_info',
                'confidence': 0.9
            }
            
            result = manager._handle_info_search(
                self.test_message,
                analysis_result,
                self.test_session,
                self.test_clinic_data
            )
            
            # Verificar resultado
            self.assertIn('response', result)
            self.assertEqual(result['intent'], 'buscar_info')
    
    def test_extract_analysis_from_response(self):
        """Testa extração de análise da resposta"""
        with patch('langchain_integration.chains.conversation_chains.LANGCHAIN_CONFIG', {'GEMINI_API_KEY': 'test-key', 'GEMINI_MODEL': 'gemini-2.0-flash'}):
            manager = ConversationChainManager()
            
            # Teste com JSON válido
            json_response = '{"intent": "agendar_consulta", "next_state": "selecionando_medico", "entities": {"especialidade": "cardiologia"}, "confidence": 0.9}'
            result = manager._extract_analysis_from_response(json_response)
            
            self.assertEqual(result['intent'], 'agendar_consulta')
            self.assertEqual(result['next_state'], 'selecionando_medico')
            self.assertEqual(result['entities']['especialidade'], 'cardiologia')
            self.assertEqual(result['confidence'], 0.9)
            
            # Teste com JSON inválido
            invalid_response = 'Resposta inválida'
            result = manager._extract_analysis_from_response(invalid_response)
            
            self.assertIn('intent', result)
            self.assertIn('confidence', result)
    
    def test_get_chain_stats(self):
        """Testa obtenção de estatísticas das chains"""
        with patch('langchain_integration.chains.conversation_chains.LANGCHAIN_CONFIG', {'GEMINI_API_KEY': 'test-key', 'GEMINI_MODEL': 'gemini-2.0-flash'}):
            manager = ConversationChainManager()
            
            stats = manager.get_chain_stats()
            
            self.assertIn('total_chains', stats)
            self.assertIn('available_chains', stats)
            self.assertIn('status', stats)
            self.assertEqual(stats['status'], 'active')


class CompatibilityChainServiceTestCase(TestCase):
    """Testes para o CompatibilityChainService"""
    
    def setUp(self):
        """Configuração inicial dos testes"""
        self.service = CompatibilityChainService()
        
        # Mock do chain manager
        self.chain_patcher = patch('langchain_integration.chains.compatibility_chains.chain_manager')
        self.mock_chain_manager = self.chain_patcher.start()
        
        # Mock do memory manager
        self.memory_patcher = patch('langchain_integration.chains.compatibility_chains.memory_manager')
        self.mock_memory_manager = self.memory_patcher.start()
        
        # Mock do compatibility RAG service
        self.rag_patcher = patch('langchain_integration.chains.compatibility_chains.compatibility_rag_service')
        self.mock_rag_service = self.rag_patcher.start()
    
    def tearDown(self):
        """Limpeza após os testes"""
        self.chain_patcher.stop()
        self.memory_patcher.stop()
        self.rag_patcher.stop()
    
    def test_process_message(self):
        """Testa processamento de mensagem"""
        # Mock do chain manager
        self.mock_chain_manager.process_message.return_value = {
            'response': 'Resposta de teste',
            'intent': 'agendar_consulta',
            'confidence': 0.9,
            'state': 'selecionando_medico',
            'session_data': {'current_state': 'selecionando_medico'},
            'analysis': {'intent': 'agendar_consulta', 'confidence': 0.9},
            'agent': 'langchain_chains'
        }
        
        # Mock do RAG service
        self.mock_rag_service.get_all_clinic_data.return_value = {
            'clinica_info': {'nome': 'Clínica Teste'},
            'medicos': [],
            'especialidades': [],
            'exames': []
        }
        
        result = self.service.process_message("5511999999999", "Quero agendar")
        
        # Verificar resultado
        self.assertIn('response', result)
        self.assertIn('intent', result)
        self.assertIn('confidence', result)
        self.assertEqual(result['intent'], 'agendar_consulta')
    
    def test_get_conversation_history(self):
        """Testa obtenção de histórico da conversa"""
        # Mock do memory manager
        self.mock_memory_manager.get_conversation_history.return_value = [
            {'is_user': True, 'content': 'Oi'},
            {'is_user': False, 'content': 'Olá!'}
        ]
        
        history = self.service.get_conversation_history("5511999999999", 5)
        
        # Verificar resultado
        self.assertEqual(len(history), 2)
        self.assertTrue(history[0]['is_user'])
        self.assertFalse(history[1]['is_user'])
    
    def test_clear_memory(self):
        """Testa limpeza de memória"""
        # Mock do memory manager
        self.mock_memory_manager.clear_memory.return_value = None
        
        # Não deve gerar exceção
        self.service.clear_memory("5511999999999")
        
        # Verificar se foi chamado
        self.mock_memory_manager.clear_memory.assert_called_once_with("5511999999999")
    
    def test_get_memory_stats(self):
        """Testa obtenção de estatísticas da memória"""
        # Mock do memory manager
        self.mock_memory_manager.get_memory_stats.return_value = {
            'total_messages': 5,
            'user_messages': 3,
            'ai_messages': 2
        }
        
        stats = self.service.get_memory_stats("5511999999999")
        
        # Verificar resultado
        self.assertEqual(stats['total_messages'], 5)
        self.assertEqual(stats['user_messages'], 3)
        self.assertEqual(stats['ai_messages'], 2)
    
    def test_get_chain_stats(self):
        """Testa obtenção de estatísticas das chains"""
        # Mock do chain manager
        self.mock_chain_manager.get_chain_stats.return_value = {
            'total_chains': 6,
            'available_chains': ['analysis', 'response', 'confirmation'],
            'status': 'active'
        }
        
        stats = self.service.get_chain_stats()
        
        # Verificar resultado
        self.assertEqual(stats['total_chains'], 6)
        self.assertIn('analysis', stats['available_chains'])
        self.assertEqual(stats['status'], 'active')
