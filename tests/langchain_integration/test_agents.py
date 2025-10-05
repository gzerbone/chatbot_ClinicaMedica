"""
Testes para Sistema de Agents LangChain
"""
from unittest.mock import MagicMock, patch

from django.test import TestCase

from langchain_integration.agents.compatibility_agents import \
    CompatibilityAgentService
from langchain_integration.agents.medical_agents import (MedicalAgentManager,
                                                         MedicalAgentTools)


class MedicalAgentToolsTestCase(TestCase):
    """Testes para MedicalAgentTools"""
    
    def setUp(self):
        """Configuração inicial dos testes"""
        self.tools = MedicalAgentTools()
        
        # Mock do RAG service
        self.rag_patcher = patch('langchain_integration.agents.medical_agents.compatibility_rag_service')
        self.mock_rag_service = self.rag_patcher.start()
    
    def tearDown(self):
        """Limpeza após os testes"""
        self.rag_patcher.stop()
    
    def test_search_doctors(self):
        """Testa busca de médicos"""
        # Mock do RAG service
        self.mock_rag_service.get_doctors.return_value = [
            {
                'nome': 'Dr. João Silva',
                'especialidades_display': 'Cardiologia',
                'preco_particular': '150.00'
            }
        ]
        
        result = self.tools.search_doctors('cardiologista')
        
        # Verificar resultado
        self.assertIn('Dr. João Silva', result)
        self.assertIn('Cardiologia', result)
        self.assertIn('R$ 150.00', result)
        self.mock_rag_service.get_doctors.assert_called_once_with('cardiologista')
    
    def test_search_exams(self):
        """Testa busca de exames"""
        # Mock do RAG service
        self.mock_rag_service.get_exams.return_value = [
            {
                'nome': 'Hemograma',
                'preco': '50.00',
                'duracao_formatada': '30 min'
            }
        ]
        
        result = self.tools.search_exams('hemograma')
        
        # Verificar resultado
        self.assertIn('Hemograma', result)
        self.assertIn('R$ 50.00', result)
        self.assertIn('30 min', result)
        self.mock_rag_service.get_exams.assert_called_once_with('hemograma')
    
    def test_search_specialties(self):
        """Testa busca de especialidades"""
        # Mock do RAG service
        self.mock_rag_service.get_specialties.return_value = [
            {
                'nome': 'Cardiologia',
                'descricao': 'Especialidade do coração'
            }
        ]
        
        result = self.tools.search_specialties('cardiologia')
        
        # Verificar resultado
        self.assertIn('Cardiologia', result)
        self.assertIn('Especialidade do coração', result)
        self.mock_rag_service.get_specialties.assert_called_once_with('cardiologia')
    
    def test_get_clinic_info(self):
        """Testa obtenção de informações da clínica"""
        # Mock do RAG service
        self.mock_rag_service.get_clinic_info.return_value = {
            'nome': 'Clínica Teste',
            'endereco': 'Rua Teste, 123',
            'telefone_contato': '11999999999',
            'whatsapp_contato': '11999999999',
            'horario_funcionamento': '8h às 18h'
        }
        
        result = self.tools.get_clinic_info()
        
        # Verificar resultado
        self.assertIn('Clínica Teste', result)
        self.assertIn('Rua Teste, 123', result)
        self.assertIn('11999999999', result)
        self.assertIn('8h às 18h', result)
        self.mock_rag_service.get_clinic_info.assert_called_once_with('')
    
    def test_check_availability(self):
        """Testa verificação de disponibilidade"""
        result = self.tools.check_availability('Dr. João', '15/09/2024')
        
        # Verificar resultado
        self.assertIn('Dr. João', result)
        self.assertIn('disponibilidade', result)
    
    def test_create_appointment_request(self):
        """Testa criação de solicitação de agendamento"""
        result = self.tools.create_appointment_request(
            'João Silva', 'Dr. João', '15/09/2024', '14:00'
        )
        
        # Verificar resultado
        self.assertIn('João Silva', result)
        self.assertIn('Dr. João', result)
        self.assertIn('15/09/2024', result)
        self.assertIn('14:00', result)
        self.assertIn('Solicitação de agendamento criada', result)
    
    def test_get_tools(self):
        """Testa obtenção de ferramentas"""
        tools = self.tools.get_tools()
        
        # Verificar se retorna lista de ferramentas
        self.assertIsInstance(tools, list)
        self.assertGreater(len(tools), 0)
        
        # Verificar se cada ferramenta tem os atributos necessários
        for tool in tools:
            self.assertHasAttr(tool, 'name')
            self.assertHasAttr(tool, 'description')
            self.assertHasAttr(tool, 'func')
    
    def test_error_handling(self):
        """Testa tratamento de erros"""
        # Mock do RAG service para gerar erro
        self.mock_rag_service.get_doctors.side_effect = Exception('Erro de teste')
        
        result = self.tools.search_doctors('teste')
        
        # Verificar se retorna mensagem de erro
        self.assertIn('Erro ao buscar médicos', result)
        self.assertIn('Erro de teste', result)


class MedicalAgentManagerTestCase(TestCase):
    """Testes para MedicalAgentManager"""
    
    def setUp(self):
        """Configuração inicial dos testes"""
        # Mock do LLM
        self.llm_patcher = patch('langchain_integration.agents.medical_agents.ChatGoogleGenerativeAI')
        self.mock_llm = self.llm_patcher.start()
        
        # Mock do memory manager
        self.memory_patcher = patch('langchain_integration.agents.medical_agents.memory_manager')
        self.mock_memory_manager = self.memory_patcher.start()
    
    def tearDown(self):
        """Limpeza após os testes"""
        self.llm_patcher.stop()
        self.memory_patcher.stop()
    
    def test_initialization(self):
        """Testa inicialização do gerenciador de agents"""
        with patch('langchain_integration.agents.medical_agents.LANGCHAIN_CONFIG', {'GEMINI_API_KEY': 'test-key', 'GEMINI_MODEL': 'gemini-2.0-flash'}):
            manager = MedicalAgentManager()
            self.assertIsNotNone(manager.llm)
            self.assertIsNotNone(manager.tools)
            self.assertIsNotNone(manager.agent)
            self.assertIsNotNone(manager.agent_executor)
    
    def test_process_complex_request(self):
        """Testa processamento de solicitação complexa"""
        with patch('langchain_integration.agents.medical_agents.LANGCHAIN_CONFIG', {'GEMINI_API_KEY': 'test-key', 'GEMINI_MODEL': 'gemini-2.0-flash'}):
            manager = MedicalAgentManager()
            
            # Mock do agent executor
            manager.agent_executor.invoke = MagicMock(return_value={
                'output': 'Resposta do agent',
                'intermediate_steps': [{'action': 'search_doctors', 'observation': 'Médicos encontrados'}]
            })
            
            # Mock do memory manager
            self.mock_memory_manager.get_conversation_history.return_value = []
            self.mock_memory_manager.add_user_message.return_value = None
            self.mock_memory_manager.add_ai_message.return_value = None
            self.mock_memory_manager.sync_with_database.return_value = None
            
            result = manager.process_complex_request(
                '5511999999999',
                'Quero agendar com cardiologista e também saber sobre exames',
                {'current_state': 'idle'},
                {'clinica_info': {'nome': 'Clínica Teste'}}
            )
            
            # Verificar resultado
            self.assertIn('response', result)
            self.assertIn('intent', result)
            self.assertIn('confidence', result)
            self.assertIn('agent', result)
            self.assertEqual(result['agent'], 'medical_agent')
    
    def test_format_chat_history(self):
        """Testa formatação do histórico da conversa"""
        with patch('langchain_integration.agents.medical_agents.LANGCHAIN_CONFIG', {'GEMINI_API_KEY': 'test-key', 'GEMINI_MODEL': 'gemini-2.0-flash'}):
            manager = MedicalAgentManager()
            
            conversation_history = [
                {'is_user': True, 'content': 'Oi'},
                {'is_user': False, 'content': 'Olá!'}
            ]
            
            formatted = manager._format_chat_history(conversation_history)
            
            # Verificar formatação
            self.assertIn('Histórico da conversa', formatted)
            self.assertIn('Paciente: Oi', formatted)
            self.assertIn('Assistente: Olá!', formatted)
    
    def test_determine_intent_from_response(self):
        """Testa determinação de intenção baseada na resposta"""
        with patch('langchain_integration.agents.medical_agents.LANGCHAIN_CONFIG', {'GEMINI_API_KEY': 'test-key', 'GEMINI_MODEL': 'gemini-2.0-flash'}):
            manager = MedicalAgentManager()
            
            # Teste com resposta de agendamento
            response = 'Vou ajudá-lo a agendar uma consulta com cardiologista.'
            intent = manager._determine_intent_from_response(response, 'Quero agendar')
            self.assertEqual(intent, 'agendar_consulta')
            
            # Teste com resposta sobre médicos
            response = 'Aqui estão os médicos disponíveis na especialidade.'
            intent = manager._determine_intent_from_response(response, 'Quais médicos')
            self.assertEqual(intent, 'buscar_medico')
            
            # Teste com resposta sobre exames
            response = 'Vou buscar informações sobre os exames disponíveis.'
            intent = manager._determine_intent_from_response(response, 'Quais exames')
            self.assertEqual(intent, 'buscar_exame')
    
    def test_get_agent_stats(self):
        """Testa obtenção de estatísticas do agent"""
        with patch('langchain_integration.agents.medical_agents.LANGCHAIN_CONFIG', {'GEMINI_API_KEY': 'test-key', 'GEMINI_MODEL': 'gemini-2.0-flash'}):
            manager = MedicalAgentManager()
            
            stats = manager.get_agent_stats()
            
            # Verificar estatísticas
            self.assertIn('total_tools', stats)
            self.assertIn('available_tools', stats)
            self.assertIn('llm_model', stats)
            self.assertIn('status', stats)
            self.assertEqual(stats['status'], 'active')


class CompatibilityAgentServiceTestCase(TestCase):
    """Testes para CompatibilityAgentService"""
    
    def setUp(self):
        """Configuração inicial dos testes"""
        self.service = CompatibilityAgentService()
        
        # Mock do agent manager
        self.agent_patcher = patch('langchain_integration.agents.compatibility_agents.agent_manager')
        self.mock_agent_manager = self.agent_patcher.start()
    
    def tearDown(self):
        """Limpeza após os testes"""
        self.agent_patcher.stop()
    
    def test_is_complex_message(self):
        """Testa detecção de mensagens complexas"""
        # Mensagem simples
        simple_message = "Oi"
        self.assertFalse(self.service._is_complex_message(simple_message))
        
        # Mensagem complexa com múltiplas solicitações
        complex_message = "Quero agendar com cardiologista e também saber sobre exames"
        self.assertTrue(self.service._is_complex_message(complex_message))
        
        # Mensagem complexa com busca específica
        complex_message2 = "Qual é o melhor médico especialista em cardiologia?"
        self.assertTrue(self.service._is_complex_message(complex_message2))
        
        # Mensagem complexa com preço
        complex_message3 = "Quanto custa uma consulta com cardiologista?"
        self.assertTrue(self.service._is_complex_message(complex_message3))
        
        # Mensagem longa
        long_message = "Olá, gostaria de agendar uma consulta com um cardiologista para amanhã às 14h e também quero saber sobre os exames disponíveis"
        self.assertTrue(self.service._is_complex_message(long_message))
    
    def test_process_complex_message(self):
        """Testa processamento de mensagem complexa"""
        # Mock do agent manager
        self.mock_agent_manager.process_complex_request.return_value = {
            'response': 'Resposta do agent',
            'intent': 'agendar_consulta',
            'confidence': 0.9,
            'agent': 'medical_agent'
        }
        
        result = self.service.process_complex_message(
            '5511999999999',
            'Quero agendar com cardiologista e também saber sobre exames',
            {'current_state': 'idle'},
            {'clinica_info': {'nome': 'Clínica Teste'}}
        )
        
        # Verificar resultado
        self.assertIsNotNone(result)
        self.assertEqual(result['intent'], 'agendar_consulta')
        self.assertEqual(result['agent'], 'medical_agent')
    
    def test_process_simple_message(self):
        """Testa processamento de mensagem simples"""
        # Mock do agent manager
        self.mock_agent_manager.process_complex_request.return_value = {
            'response': 'Resposta do agent',
            'intent': 'saudacao',
            'confidence': 0.9
        }
        
        result = self.service.process_complex_message(
            '5511999999999',
            'Oi',
            {'current_state': 'idle'},
            {'clinica_info': {'nome': 'Clínica Teste'}}
        )
        
        # Verificar que retorna None para mensagem simples
        self.assertIsNone(result)
    
    def test_get_agent_stats(self):
        """Testa obtenção de estatísticas do agent"""
        # Mock do agent manager
        self.mock_agent_manager.get_agent_stats.return_value = {
            'total_tools': 6,
            'available_tools': ['search_doctors', 'search_exams'],
            'status': 'active'
        }
        
        stats = self.service.get_agent_stats()
        
        # Verificar resultado
        self.assertEqual(stats['total_tools'], 6)
        self.assertIn('search_doctors', stats['available_tools'])
        self.assertEqual(stats['status'], 'active')
    
    def test_test_agent_tools(self):
        """Testa teste das ferramentas do agent"""
        # Mock do agent manager
        mock_tools = [
            MagicMock(name='search_doctors', func=MagicMock(return_value='Médicos encontrados')),
            MagicMock(name='search_exams', func=MagicMock(return_value='Exames encontrados'))
        ]
        self.mock_agent_manager.tools.get_tools.return_value = mock_tools
        
        test_results = self.service.test_agent_tools()
        
        # Verificar resultado
        self.assertIn('search_doctors', test_results)
        self.assertIn('search_exams', test_results)
        self.assertEqual(test_results['search_doctors']['status'], 'success')
        self.assertEqual(test_results['search_exams']['status'], 'success')
