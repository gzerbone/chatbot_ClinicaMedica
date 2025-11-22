# 🏗️ Arquitetura do Sistema de Chatbot para Clínica Médica

> **Documentação Acadêmica - Trabalho de Conclusão de Curso**  
> Descrição Completa da Arquitetura de Software

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Arquitetura em Camadas](#arquitetura-em-camadas)
3. [Componentes Principais](#componentes-principais)
4. [Padrões de Design Aplicados](#padrões-de-design-aplicados)
5. [Fluxo de Dados](#fluxo-de-dados)
6. [Modelo de Dados](#modelo-de-dados)
7. [Integrações Externas](#integrações-externas)
8. [Segurança e Performance](#segurança-e-performance)

---

## 1. Visão Geral

### 1.1. Contexto do Sistema

O **Sistema de Chatbot para Clínica Médica** é uma aplicação web desenvolvida para automatizar e otimizar o processo de agendamento de consultas médicas através da plataforma WhatsApp. O sistema utiliza Inteligência Artificial (Google Gemini) para compreender solicitações em linguagem natural e gerenciar conversas contextuais.

### 1.2. Objetivos Arquiteturais

A arquitetura foi projetada para atender os seguintes objetivos:

| Objetivo | Descrição | Estratégia Adotada |
|----------|-----------|-------------------|
| **Modularidade** | Componentes independentes e reutilizáveis | Separação em módulos especializados |
| **Escalabilidade** | Suportar crescimento de usuários e funcionalidades | Arquitetura em camadas, serviços stateless |
| **Manutenibilidade** | Facilitar evolução e correções | Código limpo, padrões de design, documentação |
| **Performance** | Tempo de resposta < 3s | Cache, processamento assíncrono, otimizações |
| **Confiabilidade** | Alta disponibilidade e recuperação de falhas | Tratamento de erros, logging, mensagens genéricas |
| **Extensibilidade** | Adicionar novas features sem reescrita | Interfaces bem definidas, baixo acoplamento |

### 1.3. Decisões Arquiteturais Principais

```
┌─────────────────────────────────────────────────────────────────┐
│              DECISÕES ARQUITETURAIS CHAVE                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. ARQUITETURA EM CAMADAS                                      │
│     Decisão: Separar apresentação, lógica e dados              │
│     Justificativa: Facilita manutenção e testes                 │
│     Trade-off: +Complexidade inicial                            │
│                                                                  │
│  2. MODULARIZAÇÃO DO GEMINI                                     │
│     Decisão: Separar em 5 módulos especializados               │
│     Justificativa: Single Responsibility Principle              │
│     Trade-off: +Arquivos, +Coordenação                          │
│                                                                  │
│  3. AGENT ROUTER PATTERN                                        │
│     Decisão: Centralizar roteamento de mensagens               │
│     Justificativa: Facilita extensão e debugging                │
│     Trade-off: Ponto único de falha (mitigado com tratamento de erros) │
│                                                                  │
│  4. MÁQUINA DE ESTADOS PERSISTIDA                               │
│     Decisão: Estado em banco de dados, não em memória          │
│     Justificativa: Permite continuação após falhas              │
│     Trade-off: +Latência de I/O (mitigado com cache)           │
│                                                                  │
│  5. INTEGRAÇÃO SÍNCRONA COM APIs                                │
│     Decisão: Chamadas síncronas (sem filas)                    │
│     Justificativa: Simplicidade para MVP                        │
│     Trade-off: Latência afeta tempo de resposta                 │
│     Melhoria futura: Adicionar Celery/Redis para async         │
│                                                                  │
│  6. SQLite EM DESENVOLVIMENTO, PostgreSQL EM PRODUÇÃO           │
│     Decisão: Bancos diferentes por ambiente                     │
│     Justificativa: SQLite simples para dev, PostgreSQL robusto  │
│     Trade-off: Possíveis incompatibilidades (mitigado com ORM) │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Arquitetura em Camadas

### 2.1. Diagrama de Camadas

```
┌───────────────────────────────────────────────────────────────────┐
│                       ARQUITETURA EM 5 CAMADAS                     │
├───────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  CAMADA 1: APRESENTAÇÃO (Presentation Layer)                │ │
│  ├─────────────────────────────────────────────────────────────┤ │
│  │                                                             │ │
│  │  • WhatsApp Business API (Entrada/Saída)                   │ │
│  │  • Webhook Receiver (views.py)                             │ │
│  │  • Message Formatter (formatação de respostas)             │ │
│  │                                                             │ │
│  │  Responsabilidades:                                         │ │
│  │  - Receber mensagens do WhatsApp                           │ │
│  │  - Validar formato de webhook                              │ │
│  │  - Enviar respostas formatadas                             │ │
│  │                                                             │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                              │                                    │
│                              ▼                                    │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  CAMADA 2: ORQUESTRAÇÃO (Orchestration Layer)              │ │
│  ├─────────────────────────────────────────────────────────────┤ │
│  │                                                             │ │
│  │  • GeminiChatbotService (CoreService)                      │ │
│  │    └─ Agent Router Pattern                                 │ │
│  │                                                             │ │
│  │  Responsabilidades:                                         │ │
│  │  - Coordenar módulos especializados                        │ │
│  │  - Decidir roteamento de mensagens                         │ │
│  │  - Gerenciar fluxo de conversação                          │ │
│  │  - Integrar com serviços externos                          │ │
│  │                                                             │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                              │                                    │
│                              ▼                                    │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  CAMADA 3: PROCESSAMENTO IA (AI Processing Layer)          │ │
│  ├─────────────────────────────────────────────────────────────┤ │
│  │                                                             │ │
│  │  Módulos Gemini (5 especializados):                        │ │
│  │  ├─ IntentDetector (Detecção de intenções)                 │ │
│  │  ├─ EntityExtractor (Extração de entidades)                │ │
│  │  ├─ ResponseGenerator (Geração de respostas)               │ │
│  │  ├─ SessionManager (Gerenciamento de sessões)              │ │
│  │  └─ (Coordenado por CoreService)                           │ │
│  │                                                             │ │
│  │  Responsabilidades:                                         │ │
│  │  - Processar linguagem natural                             │ │
│  │  - Extrair informações estruturadas                        │ │
│  │  - Gerar respostas contextuais                             │ │
│  │  - Manter contexto da conversação                          │ │
│  │                                                             │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                              │                                    │
│                              ▼                                    │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  CAMADA 4: LÓGICA DE NEGÓCIO (Business Logic Layer)        │ │
│  ├─────────────────────────────────────────────────────────────┤ │
│  │                                                             │ │
│  │  Serviços Especializados:                                  │ │
│  │  ├─ ConversationService (Gestão de conversação)            │ │
│  │  ├─ SmartSchedulingService (Agendamento inteligente)       │ │
│  │  ├─ HandoffService (Transferência para humano)             │ │
│  │  ├─ RAGService (Base de conhecimento)                      │ │
│  │  └─ GoogleCalendarService (Integração calendário)          │ │
│  │                                                             │ │
│  │  Responsabilidades:                                         │ │
│  │  - Implementar regras de negócio                           │ │
│  │  - Validar dados e consistência                            │ │
│  │  - Gerenciar estados e transições                          │ │
│  │  - Integrar com APIs externas                              │ │
│  │                                                             │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                              │                                    │
│                              ▼                                    │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  CAMADA 5: PERSISTÊNCIA (Data Layer)                       │ │
│  ├─────────────────────────────────────────────────────────────┤ │
│  │                                                             │ │
│  │  • Django ORM                                              │ │
│  │  • SQLite (Dev) / PostgreSQL (Prod)                        │ │
│  │                                                             │ │
│  │  Modelos Principais:                                        │ │
│  │  ├─ ConversationSession (Estado da conversa)               │ │
│  │  ├─ ConversationMessage (Histórico)                        │ │
│  │  ├─ Doctor (Médicos)                                       │ │
│  │  ├─ Specialty (Especialidades)                             │ │
│  │  ├─ ClinicInfo (Informações da clínica)                    │ │
│  │  └─ HandoffRecord (Registro de transferências)             │ │
│  │                                                             │ │
│  │  Responsabilidades:                                         │ │
│  │  - Persistir dados de forma confiável                      │ │
│  │  - Garantir integridade referencial                        │ │
│  │  - Fornecer queries otimizadas                             │ │
│  │                                                             │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### 2.2. Comunicação Entre Camadas

```
┌──────────────┐
│ Apresentação │  (WhatsApp API, Views)
└──────┬───────┘
       │ HTTP/REST
       ▼
┌──────────────┐
│ Orquestração │  (CoreService, Agent Router)
└──────┬───────┘
       │ Chamadas de método
       ▼
┌──────────────┐
│ IA Processing│  (Gemini Modules)
└──────┬───────┘
       │ Chamadas de método + API calls
       ▼
┌──────────────┐
│ Lógica Negócio│  (Services)
└──────┬───────┘
       │ ORM queries
       ▼
┌──────────────┐
│ Persistência │  (Database)
└──────────────┘

REGRAS:
• Camada superior só pode chamar camada imediatamente inferior
• Camada inferior não conhece camada superior (inversão de dependência)
• Comunicação sempre de cima para baixo
• Exceção: Callbacks e eventos (quando necessário)
```

---

## 3. Componentes Principais

### 3.1. Mapa de Componentes

```
┌─────────────────────────────────────────────────────────────────────┐
│                       MAPA DE COMPONENTES                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  API GATEWAY (api_gateway/)                                          │
│  ├─ views.py                    # Endpoints HTTP                     │
│  ├─ models.py                   # Modelos Django                     │
│  ├─ urls.py                     # Roteamento                         │
│  │                                                                    │
│  ├─ services/                   # Camada de Serviços                 │
│  │  │                                                                 │
│  │  ├─ gemini/                  # Módulos de IA                       │
│  │  │  ├─ core_service.py       # Orquestrador (Agent Router)        │
│  │  │  ├─ intent_detector.py    # Detecção de intenções              │
│  │  │  ├─ entity_extractor.py   # Extração de entidades              │
│  │  │  ├─ response_generator.py # Geração de respostas               │
│  │  │  └─ session_manager.py    # Gestão de sessões                  │
│  │  │                                                                 │
│  │  ├─ conversation_service.py  # Gestão de conversação              │
│  │  ├─ smart_scheduling_service.py # Agendamento inteligente         │
│  │  ├─ handoff_service.py       # Geração de handoffs                │
│  │  ├─ rag_service.py           # Base de conhecimento               │
│  │  └─ google_calendar_service.py # Integração Google Calendar       │
│  │                                                                    │
│  └─ migrations/                 # Migrações de banco                 │
│                                                                      │
│  CONFIGURAÇÃO (chatbot_clinica/)                                     │
│  ├─ settings.py                 # Configurações Django                │
│  ├─ urls.py                     # URLs principais                    │
│  └─ wsgi.py                     # WSGI entry point                   │
│                                                                      │
│  TESTES (tests/)                                                     │
│  ├─ api_gateway/                                                     │
│  │  ├─ test_core_service.py                                          │
│  │  ├─ test_intent_detector.py                                       │
│  │  └─ test_conversation_service.py                                  │
│  │                                                                    │
│  └─ integration/                                                     │
│     └─ test_full_flow.py                                             │
│                                                                      │
│  DOCUMENTAÇÃO (docs/)                                                │
│  ├─ 01_arquitetura/                                                  │
│  ├─ 04_fluxos_processos/                                             │
│  └─ 08_agent_router/                                                 │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2. Descrição dos Componentes

#### 3.2.1. GeminiChatbotService (CoreService)

**Localização**: `api_gateway/services/gemini/core_service.py`

**Tipo**: Orquestrador / Agent Router

**Responsabilidades**:
- Coordenar processamento de mensagens
- Decidir roteamento baseado em intenção e estado
- Gerenciar fluxo de conversação
- Integrar módulos especializados

**Dependências**:
- IntentDetector
- EntityExtractor
- ResponseGenerator
- SessionManager
- ConversationService
- SmartSchedulingService
- HandoffService

**Interfaces Principais**:
```python
class GeminiChatbotService:
    def process_message(phone: str, message: str) -> Dict
    def _handle_patient_name_flow() -> Optional[Dict]
    def _handle_scheduling_request() -> Dict
    def _determine_routing() -> Dict
```

#### 3.2.2. IntentDetector

**Localização**: `api_gateway/services/gemini/intent_detector.py`

**Tipo**: Módulo de IA

**Responsabilidades**:
- Classificar mensagem em intenção
- Calcular confiança da classificação
- Determinar próximo estado sugerido

**Intenções Suportadas**:
- `saudacao`
- `buscar_info`
- `agendar_consulta`
- `confirmar_agendamento`
- `cancelar`
- `duvida`

**Interfaces Principais**:
```python
class IntentDetector:
    def analyze_message(message: str, session: Dict, 
                       history: List, clinic_data: Dict) -> Dict
```

#### 3.2.3. EntityExtractor

**Localização**: `api_gateway/services/gemini/entity_extractor.py`

**Tipo**: Módulo de IA

**Responsabilidades**:
- Extrair entidades estruturadas da mensagem
- Validar entidades contra banco de dados
- Normalizar formatos (datas, horários)

**Entidades Extraídas**:
- `patient_name`: Nome do paciente
- `specialties`: Especialidades médicas
- `doctors`: Nomes de médicos
- `dates`: Datas mencionadas
- `times`: Horários mencionados

**Técnicas**:
- Gemini AI (único método)
- Regex para parsing de datas e horários (complementar)
- Validação contra BD

**Interfaces Principais**:
```python
class EntityExtractor:
    def extract_entities(message: str, session: Dict,
                        history: List, clinic_data: Dict) -> Dict
```

#### 3.2.4. ConversationService

**Localização**: `api_gateway/services/conversation_service.py`

**Tipo**: Serviço de Negócio

**Responsabilidades**:
- Gerenciar sessões de conversação
- Implementar sistema pausar/retomar
- Processar e confirmar nome do paciente
- Validar completude de informações

**Interfaces Principais**:
```python
class ConversationService:
    def get_or_create_session(phone: str) -> ConversationSession
    def add_message(phone: str, content: str, type: str) -> Message
    def pause_for_question(phone: str) -> bool
    def resume_appointment(phone: str) -> Dict
    def confirm_patient_name(phone: str, confirmation: str) -> Dict
    def get_missing_appointment_info(phone: str) -> Dict
```

#### 3.2.5. SmartSchedulingService

**Localização**: `api_gateway/services/smart_scheduling_service.py`

**Tipo**: Serviço de Negócio

**Responsabilidades**:
- Analisar solicitações de agendamento
- Consultar disponibilidade no Google Calendar
- Validar médicos e especialidades
- Formatar informações de horários

**Interfaces Principais**:
```python
class SmartSchedulingService:
    def analyze_scheduling_request(message: str, session: Dict) -> Dict
    def get_doctor_availability(doctor: str, days: int = 7) -> Dict
    def _validate_doctor(name: str) -> Optional[Dict]
    def _get_doctor_list_message() -> str
```

#### 3.2.6. HandoffService

**Localização**: `api_gateway/services/handoff_service.py`

**Tipo**: Serviço de Negócio

**Responsabilidades**:
- Gerar links de handoff para WhatsApp
- Registrar transferências no banco
- Formatar mensagens para secretária

**Interfaces Principais**:
```python
class HandoffService:
    def generate_appointment_handoff_link(
        patient_name: str,
        doctor_name: str,
        specialty: str,
        date: str,
        time: str
    ) -> str
```

---

## 4. Padrões de Design Aplicados

### 4.1. Padrões Arquiteturais

#### 4.1.1. Layered Architecture (Arquitetura em Camadas)

**Descrição**: Sistema organizado em 5 camadas com responsabilidades bem definidas.

**Benefícios**:
- Separação de responsabilidades
- Facilita testes unitários
- Reduz acoplamento

#### 4.1.2. Service-Oriented Architecture (SOA)

**Descrição**: Funcionalidades encapsuladas em serviços reutilizáveis.

**Benefícios**:
- Reutilização de código
- Facilita escalabilidade
- Permite evolução independente

### 4.2. Padrões de Design (GoF)

#### 4.2.1. Strategy Pattern

**Aplicação**: ResponseGenerator seleciona estratégia de geração de resposta.

```python
class ResponseGenerator:
    def generate_response(self, context: Dict) -> str:
        # Selecionar estratégia baseada no contexto
        if self._should_use_template(context):
            strategy = TemplateResponseStrategy()
        elif self._should_use_rag(context):
            strategy = RAGResponseStrategy()
        else:
            strategy = LLMResponseStrategy()
        
        return strategy.generate(context)
```

**Benefícios**:
- Facilita adição de novas estratégias
- Código mais limpo e manutenível

#### 4.2.2. Facade Pattern

**Aplicação**: CoreService atua como fachada para subsistemas complexos.

```python
class GeminiChatbotService:  # Facade
    def __init__(self):
        # Encapsula complexidade de múltiplos subsistemas
        self.intent_detector = IntentDetector()
        self.entity_extractor = EntityExtractor()
        self.response_generator = ResponseGenerator()
        self.session_manager = SessionManager()
    
    def process_message(self, phone: str, message: str) -> Dict:
        # Interface simples para cliente
        # Coordena chamadas complexas internamente
        pass
```

**Benefícios**:
- Interface simplificada para clientes
- Reduz acoplamento com subsistemas

#### 4.2.3. Repository Pattern

**Aplicação**: SessionManager abstrai acesso a dados.

```python
class SessionManager:  # Repository
    def get_or_create_session(self, phone: str) -> ConversationSession:
        # Abstrai detalhes de acesso ao banco
        session, created = ConversationSession.objects.get_or_create(
            phone_number=phone,
            defaults={'current_state': 'idle'}
        )
        return session
    
    def save_messages(self, phone: str, user_msg: str, bot_msg: str):
        # Encapsula lógica de persistência
        pass
```

**Benefícios**:
- Desacopla lógica de negócio do banco de dados
- Facilita testes (mocks)
- Permite trocar implementação de persistência

#### 4.2.4. Chain of Responsibility Pattern

**Aplicação**: Processamento de mensagem passa por cadeia de handlers.

```
Message → ValidationHandler → IntentHandler → EntityHandler 
       → RoutingHandler → ResponseHandler → StorageHandler
```

**Benefícios**:
- Flexibilidade para adicionar/remover handlers
- Cada handler tem responsabilidade única

### 4.3. Padrões de Integração

#### 4.3.1. Adapter Pattern

**Aplicação**: GoogleCalendarService adapta API do Google para interface interna.

```python
class GoogleCalendarService:  # Adapter
    def get_doctor_availability(self, doctor: str, days: int) -> Dict:
        # Adapta chamada complexa do Google Calendar API
        # para interface simples usada internamente
        
        service = self._get_google_service()  # API do Google
        events = service.events().list(...).execute()
        
        # Transforma para formato interno
        return self._transform_to_internal_format(events)
```

---

## 5. Fluxo de Dados

### 5.1. Fluxo End-to-End

```
┌──────────┐
│ USUÁRIO  │ Envia mensagem via WhatsApp
└────┬─────┘
     │ 1. Mensagem de texto
     ▼
┌──────────────────┐
│ WhatsApp API     │ Recebe e encaminha via webhook
└────┬─────────────┘
     │ 2. POST /webhook com payload JSON
     ▼
┌──────────────────┐
│ Django View      │ Valida e extrai dados
│ (views.py)       │
└────┬─────────────┘
     │ 3. phone_number + message_text
     ▼
┌──────────────────┐
│ CoreService      │ Orquestra processamento
│ (Agent Router)   │
└────┬─────────────┘
     │ 4. Coordena módulos
     ├────────────────────────┐
     ▼                        ▼
┌──────────────┐      ┌──────────────┐
│IntentDetector│      │EntityExtractor│
└────┬─────────┘      └────┬─────────┘
     │ 5a. Intent           │ 5b. Entities
     └──────────┬───────────┘
                ▼
┌──────────────────────────┐
│ CoreService              │ Decisão de roteamento
│ (Routing Decision)       │
└────┬─────────────────────┘
     │ 6. Seleciona serviço apropriado
     │
     ├──────────────┬──────────────┬─────────────┐
     ▼              ▼              ▼             ▼
┌────────┐  ┌──────────┐  ┌────────┐  ┌─────────┐
│Conversa│  │ Smart    │  │Handoff │  │   RAG   │
│Service │  │Scheduling│  │Service │  │ Service │
└────┬───┘  └────┬─────┘  └────┬───┘  └────┬────┘
     │           │              │           │
     │ 7. Executa lógica de negócio        │
     │           │              │           │
     └───────────┴──────────────┴───────────┘
                 │
                 ▼
┌──────────────────────────┐
│ ResponseGenerator        │ Gera resposta
└────┬─────────────────────┘
     │ 8. Texto formatado da resposta
     ▼
┌──────────────────────────┐
│ SessionManager           │ Atualiza estado e salva histórico
└────┬─────────────────────┘
     │ 9. Persiste no banco
     ▼
┌──────────────────────────┐
│ Database                 │
└──────────────────────────┘
     │
     │ 10. Resposta retorna ao usuário
     ▼
┌──────────────────┐
│ WhatsApp API     │ Envia resposta
└────┬─────────────┘
     │
     ▼
┌──────────┐
│ USUÁRIO  │ Recebe mensagem
└──────────┘
```

### 5.2. Fluxo de Dados por Tipo de Mensagem

#### 5.2.1. Saudação

```
Usuário: "Olá"
   ↓
IntentDetector → "saudacao"
   ↓
EntityExtractor → {} (sem entidades)
   ↓
ResponseGenerator → Template de boas-vindas
   ↓
Resposta: "Olá! Como posso ajudá-lo?"
```

#### 5.2.2. Busca de Informação

```
Usuário: "Quais especialidades vocês têm?"
   ↓
IntentDetector → "buscar_info"
   ↓
RAGService → Busca em base de conhecimento
   ↓
ResponseGenerator → Lista de especialidades do BD
   ↓
Resposta: "Temos Cardiologia, Ortopedia, ..."
```

#### 5.2.3. Agendamento

```
Usuário: "Quero agendar com Dr. Carlos"
   ↓
IntentDetector → "agendar_consulta"
   ↓
EntityExtractor → {doctors: ["Dr. Carlos"]}
   ↓
SmartSchedulingService:
   ├─ Valida médico existe no BD
   ├─ Consulta Google Calendar API
   └─ Retorna horários disponíveis
   ↓
ResponseGenerator → Formata lista de horários
   ↓
Resposta: "Dr. Carlos tem horários disponíveis em..."
```

---

## 6. Modelo de Dados

### 6.1. Diagrama Entidade-Relacionamento (ER)

```
┌─────────────────────────────────────────────────────────────────┐
│                    MODELO DE DADOS PRINCIPAL                     │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────────┐
│ ConversationSession      │
├──────────────────────────┤
│ PK  id                   │
│     phone_number         │ UNIQUE
│     current_state        │
│     previous_state       │ NULL (pausar/retomar)
│     patient_name         │ NULL
│     pending_name         │ NULL (confirmação)
│     name_confirmed       │ BOOLEAN
│     selected_specialty   │ NULL
│     selected_doctor      │ NULL
│     preferred_date       │ NULL
│     preferred_time       │ NULL
│     created_at           │
│     last_activity        │
└──────┬───────────────────┘
       │
       │ 1:N
       │
       ▼
┌──────────────────────────┐
│ ConversationMessage      │
├──────────────────────────┤
│ PK  id                   │
│ FK  session_id           │
│     message_type         │ (user/bot)
│     content              │ TEXT
│     intent               │ NULL
│     confidence           │ NULL
│     entities             │ JSON
│     timestamp            │
└──────────────────────────┘


┌──────────────────────────┐
│ Doctor                   │
├──────────────────────────┤
│ PK  id                   │
│     name                 │
│     specialties          │ M2M
│     price_particular     │ DECIMAL
│     calendar_id          │ (Google Calendar)
│     created_at           │
└──────┬───────────────────┘
       │
       │ M:N
       │
       ▼
┌──────────────────────────┐
│ Specialty                │
├──────────────────────────┤
│ PK  id                   │
│     name                 │
│     description          │ TEXT
│     created_at           │
└──────────────────────────┘


┌──────────────────────────┐
│ ClinicInfo               │
├──────────────────────────┤
│ PK  id                   │
│     name                 │
│     address              │
│     phone                │
│     business_hours       │ JSON
│     accepted_insurance   │ JSON
│     created_at           │
│     updated_at           │
└──────────────────────────┘


┌──────────────────────────┐
│ HandoffRecord            │
├──────────────────────────┤
│ PK  id                   │
│     patient_name         │
│     doctor_name          │
│     specialty            │
│     appointment_date     │
│     appointment_time     │
│     status               │ (pending/confirmed/cancelled)
│     handoff_link         │
│     created_at           │
│     confirmed_at         │ NULL
└──────────────────────────┘
```

### 6.2. Descrição das Entidades

| Entidade | Descrição | Campos-Chave |
|----------|-----------|--------------|
| **ConversationSession** | Estado persistido da conversação | `phone_number` (único), `current_state`, `previous_state` |
| **ConversationMessage** | Histórico de mensagens | `session_id` (FK), `message_type`, `content`, `intent` |
| **Doctor** | Cadastro de médicos | `name`, `specialties` (M2M), `price_particular`, `calendar_id` |
| **Specialty** | Especialidades médicas | `name`, `description` |
| **ClinicInfo** | Dados da clínica | `name`, `address`, `phone`, `business_hours` |
| **HandoffRecord** | Registro de transferências | `patient_name`, `doctor_name`, `appointment_date`, `status` |

---

## 7. Integrações Externas

### 7.1. WhatsApp Business API

**Propósito**: Canal de comunicação com usuários

**Tipo**: REST API (Webhook + Envio)

**Fluxos**:
1. **Recepção**: WhatsApp → Webhook → Django View
2. **Envio**: Django → WhatsApp API → Usuário

**Configuração**:
```python
WHATSAPP_API_URL = "https://graph.facebook.com/v18.0"
WHATSAPP_TOKEN = os.getenv('WHATSAPP_TOKEN')
WHATSAPP_PHONE_ID = os.getenv('WHATSAPP_PHONE_ID')
```

### 7.2. Google Gemini AI

**Propósito**: Processamento de linguagem natural

**Tipo**: REST API

**Modelos Utilizados**:
- `gemini-1.5-flash`: Modelo rápido para produção
- `gemini-1.5-pro`: Modelo mais capaz (testes)

**Uso**:
- Detecção de intenções
- Extração de entidades
- Geração de respostas (casos complexos)

**Configuração**:
```python
import google.generativeai as genai

genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
```

### 7.3. Google Calendar API

**Propósito**: Consulta de disponibilidade real dos médicos

**Tipo**: REST API (OAuth 2.0)

**Operações**:
- Listar eventos de um calendário
- Verificar conflitos de horário
- (Futuro) Criar eventos automaticamente

**Fluxo de Autenticação**:
```python
from google.oauth2 import service_account

credentials = service_account.Credentials.from_service_account_file(
    'service_account.json',
    scopes=['https://www.googleapis.com/auth/calendar.readonly']
)

service = build('calendar', 'v3', credentials=credentials)
```

---

## 8. Segurança e Performance

### 8.1. Segurança

#### 8.1.1. Validação de Webhooks

```python
def validate_whatsapp_signature(request):
    """
    Valida assinatura do webhook do WhatsApp
    Previne ataques de replay e MITM
    """
    signature = request.headers.get('X-Hub-Signature-256')
    expected_signature = hmac.new(
        settings.WHATSAPP_APP_SECRET.encode(),
        request.body,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, f'sha256={expected_signature}')
```

#### 8.1.2. Proteção de Dados Sensíveis

- **Variáveis de Ambiente**: Chaves API nunca em código
- **HTTPS Obrigatório**: Toda comunicação criptografada
- **Sanitização de Inputs**: Validação rigorosa de entradas
- **Logs Seguros**: Não logar informações pessoais sensíveis

### 8.2. Performance

#### 8.2.1. Cache

```python
from django.core.cache import cache

def get_clinic_data_optimized():
    """
    Cache de dados da clínica (raramente mudam)
    Reduz queries ao banco de dados
    """
    cache_key = 'clinic_data_v1'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return cached_data
    
    data = {
        'medicos': list(Doctor.objects.all().values()),
        'especialidades': list(Specialty.objects.all().values()),
        'info_clinica': ClinicInfo.objects.first()
    }
    
    cache.set(cache_key, data, timeout=3600)  # 1 hora
    return data
```

#### 8.2.2. Otimizações de Query

```python
# ❌ Ruim: N+1 queries
for message in session.messages.all():
    print(message.session.phone_number)  # Query adicional

# ✅ Bom: 1 query com select_related
messages = session.messages.select_related('session').all()
for message in messages:
    print(message.session.phone_number)  # Sem query adicional
```

#### 8.2.3. Gestão de Tokens Gemini

```python
def optimize_token_usage(message: str, history: List[Dict]) -> str:
    """
    Limita contexto enviado ao Gemini para reduzir custos
    """
    # Limitar histórico às últimas 10 mensagens
    recent_history = history[-10:]
    
    # Resumir mensagens muito longas
    if len(message) > 500:
        message = message[:500] + "..."
    
    return format_prompt(message, recent_history)
```

---

## 9. Conclusão

### 9.1. Princípios Arquiteturais Seguidos

✅ **SOLID Principles**
- **S**ingle Responsibility: Cada módulo tem uma responsabilidade única
- **O**pen/Closed: Aberto para extensão, fechado para modificação
- **L**iskov Substitution: Subtipos podem substituir tipos base
- **I**nterface Segregation: Interfaces específicas e focadas
- **D**ependency Inversion: Depender de abstrações, não implementações

✅ **Clean Architecture**
- Independência de frameworks
- Testabilidade alta
- Independência de UI
- Independência de banco de dados
- Regras de negócio isoladas

✅ **Domain-Driven Design (parcial)**
- Linguagem ubíqua (estados, intenções, entidades)
- Agregados bem definidos (Session + Messages)
- Serviços de domínio (ConversationService, SmartSchedulingService)

### 9.2. Trade-offs Aceitos

| Decisão | Benefício | Custo |
|---------|-----------|-------|
| Chamadas síncronas | Simplicidade | Latência |
| SQLite em dev | Setup rápido | Diferenças com prod |
| Gemini API | Capacidade IA | Custo por token |
| Modularização | Manutenibilidade | Complexidade inicial |

### 9.3. Evolução Futura

**Melhorias Planejadas**:

🔮 **Processamento Assíncrono**: Implementar Celery + Redis para webhooks

🔮 **Cache Distribuído**: Redis para cache compartilhado entre instâncias

🔮 **Monitoramento**: Prometheus + Grafana para métricas em tempo real

🔮 **Escalabilidade Horizontal**: Load balancer + múltiplas instâncias

🔮 **CI/CD**: Pipeline automatizado de testes e deploy

---

**Autor**: [Seu Nome]  
**Orientador**: [Nome do Orientador]  
**Instituição**: [Nome da Instituição]  
**Data**: Novembro de 2025  
**Versão**: 1.0


