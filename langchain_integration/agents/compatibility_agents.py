"""
Serviço de Compatibilidade para Agents
Mantém compatibilidade com código existente durante migração
"""
import logging
from typing import Any, Dict, List

from .medical_agents import agent_manager

logger = logging.getLogger(__name__)


class CompatibilityAgentService:
    """
    Serviço de compatibilidade que mantém a interface do Gemini Chatbot Service
    mas usa LangChain Agents internamente para decisões complexas
    """
    
    def __init__(self):
        self.agent_manager = agent_manager
    
    def process_complex_message(self, phone_number: str, message: str, 
                              session: Dict, clinic_data: Dict) -> Dict[str, Any]:
        """
        Processa mensagens complexas usando agents
        
        Args:
            phone_number: Número do telefone
            message: Mensagem do usuário
            session: Dados da sessão
            clinic_data: Dados da clínica
            
        Returns:
            Resultado do processamento
        """
        try:
            # Verificar se a mensagem é complexa o suficiente para usar agent
            if not self._is_complex_message(message):
                return None  # Deixar para chains normais processarem
            
            # Processar com agent
            result = self.agent_manager.process_complex_request(
                phone_number, message, session, clinic_data
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Erro no processamento do agent: {e}")
            return None
    
    def _is_complex_message(self, message: str) -> bool:
        """
        Determina se a mensagem é complexa o suficiente para usar agent
        
        Args:
            message: Mensagem do usuário
            
        Returns:
            True se for complexa, False caso contrário
        """
        message_lower = message.lower()
        
        # Palavras-chave que indicam complexidade
        complex_keywords = [
            # Múltiplas solicitações
            'e também', 'além disso', 'também quero', 'e quero',
            
            # Buscas específicas
            'médico que', 'especialista em', 'exame para', 'procedimento que',
            
            # Comparações
            'qual é melhor', 'diferença entre', 'comparar', 'recomenda',
            
            # Informações detalhadas
            'preço de', 'custo de', 'quanto custa', 'valor de',
            'quanto tempo', 'duração de', 'como funciona',
            
            # Condições específicas
            'se eu', 'caso eu', 'quando eu', 'depois que',
            
            # Múltiplas perguntas
            '?', 'e?', 'também?'
        ]
        
        # Verificar se contém palavras-chave de complexidade
        for keyword in complex_keywords:
            if keyword in message_lower:
                return True
        
        # Verificar comprimento da mensagem (mensagens longas tendem a ser complexas)
        if len(message.split()) > 10:
            return True
        
        # Verificar se contém múltiplas intenções
        intent_keywords = [
            'agendar', 'marcar', 'consulta',
            'médico', 'doutor', 'especialista',
            'exame', 'procedimento',
            'endereço', 'telefone', 'horário',
            'preço', 'custo', 'valor'
        ]
        
        intent_count = sum(1 for keyword in intent_keywords if keyword in message_lower)
        if intent_count >= 2:
            return True
        
        return False
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas do agent"""
        try:
            return self.agent_manager.get_agent_stats()
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas do agent: {e}")
            return {'error': str(e)}
    
    def test_agent_tools(self) -> Dict[str, Any]:
        """Testa ferramentas do agent"""
        try:
            tools = self.agent_manager.tools.get_tools()
            test_results = {}
            
            for tool in tools:
                try:
                    # Testar cada ferramenta com uma consulta simples
                    if tool.name == 'search_doctors':
                        result = tool.func('cardiologista')
                    elif tool.name == 'search_exams':
                        result = tool.func('hemograma')
                    elif tool.name == 'search_specialties':
                        result = tool.func('cardiologia')
                    elif tool.name == 'get_clinic_info':
                        result = tool.func()
                    elif tool.name == 'check_availability':
                        result = tool.func('Dr. João')
                    elif tool.name == 'create_appointment_request':
                        result = tool.func('João Silva', 'Dr. João', '15/09/2024', '14:00')
                    else:
                        result = 'Teste não implementado'
                    
                    test_results[tool.name] = {
                        'status': 'success',
                        'result_length': len(str(result)),
                        'result_preview': str(result)[:100] + '...' if len(str(result)) > 100 else str(result)
                    }
                    
                except Exception as e:
                    test_results[tool.name] = {
                        'status': 'error',
                        'error': str(e)
                    }
            
            return test_results
            
        except Exception as e:
            logger.error(f"Erro ao testar ferramentas do agent: {e}")
            return {'error': str(e)}


# Instância global do serviço de compatibilidade
compatibility_agent_service = CompatibilityAgentService()
