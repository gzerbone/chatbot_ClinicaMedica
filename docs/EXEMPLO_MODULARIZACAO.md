# 🏗️ Exemplo Prático de Modularização

## 📋 Cenário: Refatorar `GeminiChatbotService` (1.526 linhas)

### ❌ **ANTES**: Arquivo Monolítico

```python
# gemini_chatbot_service.py (1.526 linhas)
class GeminiChatbotService:
    def __init__(self):
        # 50 linhas de configuração
        pass
    
    def process_message(self, phone_number: str, message: str):
        # 200 linhas de lógica principal
        pass
    
    def _detect_intent(self, message: str):
        # 150 linhas de detecção de intenção
        pass
    
    def _extract_entities(self, message: str):
        # 200 linhas de extração de entidades
        pass
    
    def _generate_response(self, intent: str, entities: Dict):
        # 300 linhas de geração de resposta
        pass
    
    def _build_prompt(self, session: Dict):
        # 250 linhas de construção de prompt
        pass
    
    def _validate_appointment(self, session: Dict):
        # 200 linhas de validação
        pass
    
    # ... mais 15 métodos com 1.000+ linhas
```

### ✅ **DEPOIS**: Arquitetura Modular

#### 1. **Estrutura de Pastas**
```
api_gateway/services/
├── gemini/
│   ├── __init__.py
│   ├── core_service.py          # 200 linhas
│   ├── intent_detector.py       # 150 linhas
│   ├── entity_extractor.py      # 200 linhas
│   ├── response_generator.py    # 300 linhas
│   ├── session_manager.py       # 200 linhas
│   ├── prompt_builder.py        # 250 linhas
│   └── validators.py            # 150 linhas
```

#### 2. **Core Service** (Orquestrador Principal)

```python
# gemini/core_service.py (200 linhas)
from .intent_detector import IntentDetector
from .entity_extractor import EntityExtractor
from .response_generator import ResponseGenerator
from .session_manager import SessionManager

class GeminiChatbotService:
    """Orquestrador principal - delega para módulos especializados"""
    
    def __init__(self):
        self.intent_detector = IntentDetector()
        self.entity_extractor = EntityExtractor()
        self.response_generator = ResponseGenerator()
        self.session_manager = SessionManager()
    
    def process_message(self, phone_number: str, message: str) -> Dict:
        """Método principal - orquestra o fluxo"""
        try:
            # 1. Detectar intenção
            intent_result = self.intent_detector.detect_intent(message)
            
            # 2. Extrair entidades
            entities = self.entity_extractor.extract_entities(
                message, intent_result['intent']
            )
            
            # 3. Gerenciar sessão
            session = self.session_manager.get_or_create_session(phone_number)
            self.session_manager.update_session(phone_number, entities)
            
            # 4. Gerar resposta
            response = self.response_generator.generate_response(
                intent_result, entities, session
            )
            
            return {
                'response': response,
                'intent': intent_result['intent'],
                'entities': entities
            }
            
        except Exception as e:
            logger.error(f"Erro no processamento: {e}")
            return {'response': 'Desculpe, ocorreu um erro. Tente novamente.'}
```

#### 3. **Intent Detector** (Especializado)

```python
# gemini/intent_detector.py (150 linhas)
import google.generativeai as genai
from typing import Dict

class IntentDetector:
    """Detecção de intenções do usuário"""
    
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.0-flash')
    
    def detect_intent(self, message: str) -> Dict:
        """Detecta a intenção da mensagem"""
        prompt = self._build_intent_prompt(message)
        
        try:
            response = self.model.generate_content(prompt)
            return self._parse_intent_response(response.text)
        except Exception as e:
            logger.error(f"Erro na detecção de intenção: {e}")
            return {'intent': 'unknown', 'confidence': 0.0}
    
    def _build_intent_prompt(self, message: str) -> str:
        """Constrói prompt para detecção de intenção"""
        return f"""
        Analise a mensagem e identifique a intenção:
        Mensagem: "{message}"
        
        Intenções possíveis:
        - saudacao: Cumprimentos
        - agendar_consulta: Quero agendar
        - buscar_info: Perguntas sobre clínica
        - confirmar_agendamento: Confirmar dados
        """
    
    def _parse_intent_response(self, response: str) -> Dict:
        """Parse da resposta do Gemini"""
        # Lógica de parsing
        pass
```

#### 4. **Entity Extractor** (Especializado)

```python
# gemini/entity_extractor.py (200 linhas)
import re
from typing import Dict, Optional
from datetime import datetime

class EntityExtractor:
    """Extração de entidades das mensagens"""
    
    def extract_entities(self, message: str, intent: str) -> Dict:
        """Extrai entidades relevantes baseadas na intenção"""
        entities = {}
        
        if intent == 'agendar_consulta':
            entities.update(self._extract_appointment_entities(message))
        elif intent == 'buscar_info':
            entities.update(self._extract_info_entities(message))
        
        return entities
    
    def _extract_appointment_entities(self, message: str) -> Dict:
        """Extrai entidades para agendamento"""
        return {
            'patient_name': self.extract_patient_name(message),
            'specialty': self.extract_specialty(message),
            'doctor': self.extract_doctor(message),
            'date': self.extract_date(message),
            'time': self.extract_time(message)
        }
    
    def extract_patient_name(self, message: str) -> Optional[str]:
        """Extrai nome do paciente"""
        # Regex para nomes
        name_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
        matches = re.findall(name_pattern, message)
        return matches[0] if matches else None
    
    def extract_date(self, message: str) -> Optional[str]:
        """Extrai data da mensagem"""
        # Lógica de extração de data
        pass
    
    def extract_time(self, message: str) -> Optional[str]:
        """Extrai horário da mensagem"""
        # Lógica de extração de horário
        pass
```

#### 5. **Response Generator** (Especializado)

```python
# gemini/response_generator.py (300 linhas)
from typing import Dict
from .prompt_builder import PromptBuilder

class ResponseGenerator:
    """Geração de respostas contextualizadas"""
    
    def __init__(self):
        self.prompt_builder = PromptBuilder()
    
    def generate_response(self, intent_result: Dict, entities: Dict, session: Dict) -> str:
        """Gera resposta baseada no contexto"""
        intent = intent_result['intent']
        
        if intent == 'agendar_consulta':
            return self._generate_appointment_response(entities, session)
        elif intent == 'buscar_info':
            return self._generate_info_response(entities, session)
        elif intent == 'confirmar_agendamento':
            return self._generate_confirmation_response(entities, session)
        else:
            return self._generate_default_response()
    
    def _generate_appointment_response(self, entities: Dict, session: Dict) -> str:
        """Gera resposta para agendamento"""
        # Lógica específica para agendamento
        pass
    
    def _generate_info_response(self, entities: Dict, session: Dict) -> str:
        """Gera resposta para informações"""
        # Lógica específica para informações
        pass
```

#### 6. **Session Manager** (Especializado)

```python
# gemini/session_manager.py (200 linhas)
from django.core.cache import cache
from api_gateway.models import ConversationSession
from typing import Dict

class SessionManager:
    """Gerenciamento de sessões de conversa"""
    
    def get_or_create_session(self, phone_number: str) -> Dict:
        """Obtém ou cria sessão"""
        cache_key = f"session_{phone_number}"
        session = cache.get(cache_key)
        
        if not session:
            # Tentar carregar do banco
            db_session = ConversationSession.objects.filter(
                phone_number=phone_number
            ).first()
            
            if db_session:
                session = self._convert_db_to_dict(db_session)
            else:
                session = self._create_empty_session()
            
            cache.set(cache_key, session, 3600)  # 1 hora
        
        return session
    
    def update_session(self, phone_number: str, data: Dict) -> None:
        """Atualiza dados da sessão"""
        session = self.get_or_create_session(phone_number)
        session.update(data)
        
        # Salvar no cache
        cache_key = f"session_{phone_number}"
        cache.set(cache_key, session, 3600)
        
        # Salvar no banco
        self._save_to_db(phone_number, session)
    
    def _convert_db_to_dict(self, db_session: ConversationSession) -> Dict:
        """Converte sessão do banco para dict"""
        return {
            'patient_name': db_session.patient_name,
            'selected_doctor': db_session.selected_doctor,
            'selected_specialty': db_session.selected_specialty,
            'preferred_date': db_session.preferred_date,
            'preferred_time': db_session.preferred_time,
            'current_state': db_session.current_state
        }
```

#### 7. **Prompt Builder** (Especializado)

```python
# gemini/prompt_builder.py (250 linhas)
from typing import Dict

class PromptBuilder:
    """Construção de prompts para o Gemini"""
    
    def build_system_prompt(self) -> str:
        """Prompt do sistema"""
        return """
        Você é um assistente virtual da Clínica PneumoSono.
        Sua função é ajudar pacientes com agendamentos e informações.
        
        REGRAS:
        1. Seja sempre educado e profissional
        2. Colete informações de forma sequencial
        3. Não repita perguntas já respondidas
        4. Confirme dados antes de finalizar
        """
    
    def build_response_prompt(self, session: Dict, entities: Dict) -> str:
        """Prompt para geração de resposta"""
        collected_info = self._format_collected_info(session)
        
        return f"""
        INFORMAÇÕES JÁ COLETADAS:
        {collected_info}
        
        ENTIDADES EXTRAÍDAS:
        {entities}
        
        Gere uma resposta apropriada baseada no contexto.
        """
    
    def _format_collected_info(self, session: Dict) -> str:
        """Formata informações já coletadas"""
        info_lines = []
        
        if session.get('patient_name'):
            info_lines.append(f"✅ Nome: {session['patient_name']}")
        if session.get('selected_specialty'):
            info_lines.append(f"✅ Especialidade: {session['selected_specialty']}")
        # ... mais campos
        
        return '\n'.join(info_lines) if info_lines else "Nenhuma informação coletada ainda."
```

#### 8. **Validators** (Especializado)

```python
# gemini/validators.py (150 linhas)
from typing import Dict, List

class AppointmentValidator:
    """Validação de informações de agendamento"""
    
    def validate_appointment_info(self, session: Dict, entities: Dict) -> Dict:
        """Valida informações do agendamento"""
        missing_info = self.check_missing_info(session)
        
        if not missing_info:
            return {
                'is_valid': True,
                'message': 'Todas as informações estão completas'
            }
        else:
            return {
                'is_valid': False,
                'missing_info': missing_info,
                'message': f'Ainda faltam: {", ".join(missing_info)}'
            }
    
    def check_missing_info(self, session: Dict) -> List[str]:
        """Verifica informações faltantes"""
        required_fields = [
            'patient_name', 'selected_specialty', 
            'selected_doctor', 'preferred_date', 'preferred_time'
        ]
        
        missing = []
        for field in required_fields:
            if not session.get(field):
                missing.append(field)
        
        return missing
```

---

## 🎯 **Benefícios da Modularização**

### ✅ **Manutenibilidade**
- **Antes**: 1 arquivo com 1.526 linhas
- **Depois**: 8 arquivos com ~200 linhas cada
- **Resultado**: Muito mais fácil de navegar e entender

### ✅ **Responsabilidades Claras**
- **IntentDetector**: Só detecta intenções
- **EntityExtractor**: Só extrai entidades
- **ResponseGenerator**: Só gera respostas
- **SessionManager**: Só gerencia sessões

### ✅ **Testabilidade**
```python
# Teste isolado do IntentDetector
def test_intent_detection():
    detector = IntentDetector()
    result = detector.detect_intent("Quero agendar consulta")
    assert result['intent'] == 'agendar_consulta'
```

### ✅ **Reutilização**
```python
# Usar EntityExtractor em outros lugares
from gemini.entity_extractor import EntityExtractor

extractor = EntityExtractor()
name = extractor.extract_patient_name("Meu nome é João")
```

### ✅ **Desenvolvimento Paralelo**
- Pessoa A: Trabalha no `IntentDetector`
- Pessoa B: Trabalha no `ResponseGenerator`
- Sem conflitos no Git

---

## 🚀 **Próximos Passos**

1. **Criar estrutura de pastas**
2. **Extrair um módulo por vez**
3. **Testar após cada extração**
4. **Aplicar mesmo padrão nos outros serviços**

---

**Resultado**: Código mais limpo, manutenível e escalável! 🎉
