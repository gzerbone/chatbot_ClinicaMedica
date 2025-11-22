# 🏗️ Plano de Modularização do Projeto

> **📜 PLANO HISTÓRICO - JÁ IMPLEMENTADO**  
> Este documento descreve o plano de modularização que foi seguido.  
> **Status:** ✅ Modularização do `gemini_chatbot_service.py` concluída com sucesso.  
> Veja `docs/06_modularizacao/MODULARIZACAO_GEMINI_COMPLETA.md` para o resultado final.  
> Este documento é mantido como registro histórico do planejamento.

---

## 📊 Análise Atual

### Arquivos Mais Problemáticos (por tamanho):
1. **`gemini_chatbot_service.py`** - 1.526 linhas, 34 funções (arquivo já foi modularizado)
2. **`conversation_service.py`** - 590 linhas, 18 funções  
3. **`smart_scheduling_service.py`** - 580 linhas, 15 funções
4. **`google_calendar_service.py`** - 502 linhas, 15 funções

### Problemas Identificados:
- ❌ Arquivos muito grandes (1500+ linhas)
- ❌ Muitas responsabilidades em uma classe
- ❌ Funções não utilizadas
- ❌ Código duplicado
- ❌ Dificuldade de manutenção

---

## 🎯 Estratégia de Modularização

### 1. **GeminiChatbotService** (1.526 linhas → ~200 linhas)

**Problema**: Classe monolítica com muitas responsabilidades

**Solução**: Dividir em módulos especializados

```
api_gateway/services/
├── gemini/
│   ├── __init__.py
│   ├── core_service.py          # Classe principal (200 linhas)
│   ├── intent_detector.py       # Detecção de intenções
│   ├── entity_extractor.py      # Extração de entidades
│   ├── response_generator.py    # Geração de respostas
│   ├── session_manager.py       # Gerenciamento de sessões
│   ├── prompt_builder.py        # Construção de prompts
│   └── validators.py            # Validações
```

**Responsabilidades por módulo**:

#### `core_service.py` (200 linhas)
```python
class GeminiChatbotService:
    """Orquestrador principal - delega para módulos especializados"""
    
    def __init__(self):
        self.intent_detector = IntentDetector()
        self.entity_extractor = EntityExtractor()
        self.response_generator = ResponseGenerator()
        self.session_manager = SessionManager()
    
    def process_message(self, phone_number: str, message: str) -> Dict:
        """Método principal - orquestra o fluxo"""
        # 1. Detectar intenção
        # 2. Extrair entidades
        # 3. Gerenciar sessão
        # 4. Gerar resposta
        pass
```

#### `intent_detector.py` (150 linhas)
```python
class IntentDetector:
    """Detecção de intenções do usuário"""
    
    def detect_intent(self, message: str, context: Dict) -> Dict:
        """Detecta a intenção da mensagem"""
        pass
    
    def _analyze_with_gemini(self, message: str) -> Dict:
        """Análise via Gemini"""
        pass
```

#### `entity_extractor.py` (200 linhas)
```python
class EntityExtractor:
    """Extração de entidades das mensagens"""
    
    def extract_entities(self, message: str, intent: str) -> Dict:
        """Extrai entidades relevantes"""
        pass
    
    def extract_patient_name(self, message: str) -> Optional[str]:
        """Extrai nome do paciente"""
        pass
    
    def extract_date_time(self, message: str) -> Optional[Dict]:
        """Extrai data e horário"""
        pass
```

#### `response_generator.py` (300 linhas)
```python
class ResponseGenerator:
    """Geração de respostas contextualizadas"""
    
    def generate_response(self, intent: str, entities: Dict, session: Dict) -> str:
        """Gera resposta baseada no contexto"""
        pass
    
    def _build_appointment_response(self, session: Dict) -> str:
        """Resposta para agendamento"""
        pass
    
    def _build_info_response(self, query: str) -> str:
        """Resposta para informações"""
        pass
```

#### `session_manager.py` (200 linhas)
```python
class SessionManager:
    """Gerenciamento de sessões de conversa"""
    
    def get_or_create_session(self, phone_number: str) -> Dict:
        """Obtém ou cria sessão"""
        pass
    
    def update_session(self, phone_number: str, data: Dict) -> None:
        """Atualiza dados da sessão"""
        pass
    
    def save_session_to_db(self, phone_number: str, session: Dict) -> None:
        """Salva sessão no banco"""
        pass
```

#### `prompt_builder.py` (250 linhas)
```python
class PromptBuilder:
    """Construção de prompts para o Gemini"""
    
    def build_system_prompt(self) -> str:
        """Prompt do sistema"""
        pass
    
    def build_response_prompt(self, session: Dict, entities: Dict) -> str:
        """Prompt para resposta"""
        pass
    
    def build_intent_prompt(self, message: str) -> str:
        """Prompt para detecção de intenção"""
        pass
```

#### `validators.py` (150 linhas)
```python
class AppointmentValidator:
    """Validação de informações de agendamento"""
    
    def validate_appointment_info(self, session: Dict, entities: Dict) -> Dict:
        """Valida informações do agendamento"""
        pass
    
    def check_missing_info(self, session: Dict) -> List[str]:
        """Verifica informações faltantes"""
        pass
```

### 2. **ConversationService** (590 linhas → ~200 linhas)

**Dividir em**:
```
api_gateway/services/conversation/
├── __init__.py
├── flow_manager.py      # Gerenciamento de fluxo
├── state_manager.py     # Gerenciamento de estados
├── question_handler.py  # Sistema de dúvidas
└── session_persistence.py # Persistência de sessões
```

### 3. **SmartSchedulingService** (580 linhas → ~200 linhas)

**Dividir em**:
```
api_gateway/services/scheduling/
├── __init__.py
├── core_scheduler.py    # Lógica principal
├── date_processor.py    # Processamento de datas
├── time_processor.py    # Processamento de horários
└── availability_checker.py # Verificação de disponibilidade
```

### 4. **GoogleCalendarService** (502 linhas → ~200 linhas)

**Dividir em**:
```
api_gateway/services/calendar/
├── __init__.py
├── core_calendar.py     # Lógica principal
├── event_manager.py     # Gerenciamento de eventos
├── auth_handler.py      # Autenticação
└── sync_manager.py      # Sincronização
```

---

## 🛠️ Implementação Passo a Passo

### Fase 1: Preparação (1-2 dias)
1. **Criar estrutura de pastas**
2. **Identificar funções não utilizadas**
3. **Mapear dependências entre módulos**

### Fase 2: Refatoração do Gemini (3-4 dias)
1. **Extrair `IntentDetector`**
2. **Extrair `EntityExtractor`**
3. **Extrair `ResponseGenerator`**
4. **Refatorar classe principal**

### Fase 3: Refatoração dos Outros Serviços (2-3 dias)
1. **ConversationService**
2. **SmartSchedulingService**
3. **GoogleCalendarService**

### Fase 4: Limpeza e Otimização (1 dia)
1. **Remover funções não utilizadas**
2. **Consolidar imports**
3. **Atualizar testes**

---

## 📋 Checklist de Modularização

### ✅ Antes de Começar
- [ ] Backup do código atual
- [ ] Identificar todas as dependências
- [ ] Mapear funções não utilizadas
- [ ] Criar testes para funcionalidades críticas

### ✅ Durante a Refatoração
- [ ] Manter funcionalidade idêntica
- [ ] Testar cada módulo extraído
- [ ] Atualizar imports
- [ ] Documentar interfaces

### ✅ Após a Refatoração
- [ ] Executar todos os testes
- [ ] Verificar performance
- [ ] Atualizar documentação
- [ ] Code review

---

## 🎯 Benefícios Esperados

### Manutenibilidade
- ✅ Arquivos menores (200-300 linhas)
- ✅ Responsabilidades claras
- ✅ Fácil localização de bugs
- ✅ Testes mais focados

### Reutilização
- ✅ Módulos independentes
- ✅ Interfaces bem definidas
- ✅ Fácil troca de implementações
- ✅ Componentes testáveis

### Performance
- ✅ Imports mais rápidos
- ✅ Menos memória
- ✅ Lazy loading possível
- ✅ Cache mais eficiente

### Desenvolvimento
- ✅ Menos conflitos no Git
- ✅ Desenvolvimento paralelo
- ✅ Code review mais fácil
- ✅ Onboarding mais rápido

---

## 🚀 Próximos Passos

1. **Começar pelo `GeminiChatbotService`** (mais crítico)
2. **Extrair um módulo por vez**
3. **Testar após cada extração**
4. **Documentar interfaces**
5. **Refatorar gradualmente**

---

**Data**: 16/10/2025  
**Prioridade**: 🔴 **ALTA** - Impacto significativo na manutenibilidade
