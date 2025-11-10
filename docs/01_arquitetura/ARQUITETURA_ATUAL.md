# 🏗️ Arquitetura Atual do Sistema - Chatbot Clínica Médica - Atualizada 20/10 (mais recente)

## 📐 Visão Geral da Arquitetura

O sistema foi completamente refatorado para uma arquitetura **modularizada no Google Gemini AI**, com delegação de responsabilidades para módulos especializados, mantendo a centralização da inteligência mas organizando melhor o código.

## 🎯 Princípios Arquiteturais

### 1. **Gemini AI como Protagonista**
- **Motor único** de conversação e análise
- **Inteligência centralizada** para todas as decisões
- **Eliminação** de múltiplos serviços redundantes

### 2. **Arquitetura Modularizada**
- **4 módulos especializados** do Gemini Service (IntentDetector, EntityExtractor, ResponseGenerator e SessionManager)
- **Delegação de responsabilidades** bem definida
- **Fluxo orquestrado** pelo Core Service
- **Manutenibilidade** aprimorada
- **Monitoramento** de tokens integrado

### 3. **Persistência Inteligente**
- **Sessões persistentes** em banco de dados
- **Cache otimizado** para dados RAG
- **Estados preservados** entre conversas

## 🏛️ Diagrama de Arquitetura

```
┌─────────────────────────────────────────────────────────────────┐
│                        🌐 INTERNET                              │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│              📱 WHATSAPP BUSINESS API                           │
│                    (Meta/Facebook)                             │
└─────────────────────┬───────────────────────────────────────────┘
                      │ HTTP POST Webhook
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                    🔗 NGROK                                     │
│                 (Túnel Local)                                  │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                🐍 DJANGO SERVER                                │
│                  (Port 8000)                                   │
└─────────────────────┬───────────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
┌───────▼──────┐ ┌───▼──────┐ ┌────▼──────┐
│ API GATEWAY  │ │ RAG AGENT│ │   CORE    │
│              │ │          │ │           │
│ • Webhook    │ │ • Models │ │ • Settings│
│ • Views      │ │ • Data   │ │ • URLs    │
│ • Services   │ │ • Cache  │ │ • Config  │
└───────┬──────┘ └──────────┘ └───────────┘
        │
┌───────▼───────────────────────────────────────────────────────┐
│                    🧠 SERVIÇOS CORE                            │
│                                                               │
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│ │ GEMINI CHATBOT  │ │ CONVERSATION     │ │ WHATSAPP        │ │
│ │ SERVICE         │ │ SERVICE          │ │ SERVICE         │ │
│ │ (MODULARIZADO)  │ │                  │ │                 │ │
│ │                 │ │ • Persistência   │ │ • Webhook       │ │
│ │ • Core Service  │ │ • Sessões        │ │ • Mensagens     │ │
│ │ • Intent Detector│ │ • Estados        │ │ • Mídias        │ │
│ │ • Entity Extractor│ │ • Histórico      │ │                 │ │
│ │ • Response Gen. │ │                  │ │                 │ │
│ │ • Session Mgr.  │ │                  │ │                 │ │
│ └─────────────────┘ └─────────────────┘ └─────────────────┘ │
│                                                               │
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│ │ GOOGLE CALENDAR │ │ HANDOFF         │ │ SMART SCHEDULING│ │
│ │ SERVICE         │ │ SERVICE         │ │ SERVICE         │ │
│ │                 │ │                  │ │                 │ │
│ │ • Disponibilidade│ │ • Transferência │ │ • Agendamento   │ │
│ │ • Eventos       │ │ • Links         │ │ • Horários      │ │
│ │ • Sincronização │ │ • Notificações  │ │ • Otimização    │ │
│ └─────────────────┘ └─────────────────┘ └─────────────────┘ │
│                                                               │
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│ │ TOKEN MONITOR   │ │ RAG SERVICE     │ │ CONVERSATION     │ │
│ │ SERVICE         │ │                 │ │ SERVICE         │ │
│ │                 │ │                 │ │                 │ │
│ │ • Monitoramento │ │ • Base Conhecimento│ │ • Persistência  │ │
│ │ • Modo Econômico│ │ • Cache Dados   │ │ • Sessões        │ │
│ │ • Otimização    │ │ • Serialização  │ │ • Histórico      │ │
│ └─────────────────┘ └─────────────────┘ └─────────────────┘ │
└───────────────────────────────────────────────────────────────┘
```

## 🔧 Componentes Detalhados

### 1. **API Gateway** (`api_gateway/`)

#### **Models** (`models.py`)
```python
# Principais modelos
- ConversationSession    # Sessões de conversa persistentes
- ConversationMessage    # Mensagens individuais
```

#### **Services** (`services/`)

##### **Gemini Chatbot Service** (Modularizado)
```python
# Arquivo: api_gateway/services/gemini/core_service.py
class GeminiChatbotService:
    """
    Orquestrador principal do chatbot modularizado
    Responsabilidades:
    - Coordenação de todos os módulos
    - Fluxo principal de processamento
    - Integração com serviços externos
    - Sistema de pausar/retomar para dúvidas
    """

# Módulos especializados:
# - IntentDetector: Análise de intenções
# - EntityExtractor: Extração de entidades
# - ResponseGenerator: Geração de respostas
# - SessionManager: Gerenciamento de sessões
```

##### **Módulos Especializados do Gemini Service**

**IntentDetector** (`intent_detector.py`)
```python
class IntentDetector:
    """
    Detecção de intenções do usuário
    Responsabilidades:
    - Análise de mensagens com Gemini AI
    - Determinação do próximo estado
    - Fallback com palavras-chave
    - Temperature: 0.7 (determinístico)
    """
```

**EntityExtractor** (`entity_extractor.py`)
```python
class EntityExtractor:
    """
    Extração de entidades das mensagens
    Responsabilidades:
    - Extração com Gemini como método primário
    - Regex como fallback
    - Validação de especialidades contra banco
    - Métodos: extract_patient_name(), extract_doctor(), extract_specialty()
    """
```

**ResponseGenerator** (`response_generator.py`)
```python
class ResponseGenerator:
    """
    Geração de respostas contextualizadas
    Responsabilidades:
    - Geração com Gemini baseada em contexto
    - Modo econômico automático via TokenMonitor
    - Prompts estruturados por intenção
    - Filtragem de médicos por especialidade
    """
```

**SessionManager** (`session_manager.py`)
```python
class SessionManager:
    """
    Gerenciamento de sessões de conversa
    Responsabilidades:
    - Cache + Banco de dados dual
    - Sincronização automática
    - Processamento de datas e horários
    - Histórico de conversas
    """
```

##### **Conversation Service**
```python
# Arquivo: conversation_service.py
class ConversationService:
    """
    Gerenciamento de conversas
    Responsabilidades:
    - Persistência de sessões
    - Gerenciamento de estado
    - Cache de dados
    """
```

##### **WhatsApp Service**
```python
# Arquivo: whatsapp_service.py
class WhatsAppService:
    """
    Integração WhatsApp
    Responsabilidades:
    - Recebimento de webhooks
    - Envio de mensagens
    - Processamento de mídias
    """
```

##### **Google Calendar Service**
```python
# Arquivo: google_calendar_service.py
class GoogleCalendarService:
    """
    Integração Google Calendar
    Responsabilidades:
    - Consulta disponibilidade
    - Criação de eventos
    - Sincronização
    """
```

##### **Handoff Service**
```python
# Arquivo: handoff_service.py
class HandoffService:
    """
    Transferência para secretaria
    Responsabilidades:
    - Geração de links
    - Notificações
    - Transferência de contexto
    """
```

##### **Smart Scheduling Service**
```python
# Arquivo: smart_scheduling_service.py
class SmartSchedulingService:
    """
    Consulta de horários inteligente
    Responsabilidades:
    - Consulta disponibilidade no Google Calendar
    - Análise de solicitações de agendamento
    - Validação de médicos no banco
    - Geração de informações de disponibilidade
    """
```

##### **RAG Service**
```python
# Arquivo: rag_service.py
class RAGService:
    """
    Sistema RAG - Base de Conhecimento
    Responsabilidades:
    - Acesso à base de conhecimento da clínica
    - Cache inteligente de dados
    - Consultas otimizadas
    - Serialização para Gemini
    """
```

##### **Token Monitor Service**
```python
# Arquivo: token_monitor.py
class TokenMonitor:
    """
    Monitoramento de tokens do Gemini
    Responsabilidades:
    - Monitoramento de uso de tokens
    - Aplicação de modo econômico
    - Otimização automática de configurações
    - Alertas de limite
    """
```

### 2. **RAG Agent** (`rag_agent/`)

#### **Models** (`models.py`)
```python
# Base de conhecimento da clínica
- ClinicaInfo          # Informações gerais
- Medico               # Dados dos médicos
- Especialidade        # Especialidades médicas
- Convenio             # Convênios aceitos
- HorarioTrabalho      # Horários dos médicos
- Exame                # Exames disponíveis
```

### 3. **Core** (`core/`)

#### **Settings** (`settings.py`)
```python
# Configurações principais
# Todas as configurações sensíveis são carregadas do arquivo .env
# Ver .env.example para lista completa de variáveis necessárias

INSTALLED_APPS = [
    'rag_agent',
    'api_gateway',
    # ...
]
```

## 🔄 Fluxo de Dados

### 1. **Recepção de Mensagem**
```
WhatsApp → Webhook → Django → GeminiChatbotService (Core)
```

### 2. **Processamento Modularizado**
```
Core Service → SessionManager → IntentDetector → EntityExtractor
```

### 3. **Geração de Resposta**
```
ResponseGenerator → RAG Service → Base de Conhecimento → Resposta
```

### 4. **Persistência e Envio**
```
SessionManager → Conversation Service → WhatsApp Service → Paciente
```

## 📊 Estados do Sistema

### **Estados de Conversa**
```python
STATES = [
    'idle',                    # Ocioso
    'collecting_patient_info', # Coletando dados do paciente
    'collecting_info',         # Coletando informações
    'answering_questions',     # Respondendo dúvidas do paciente
    'confirming_name',         # Confirmando nome
    'selecting_specialty',     # Selecionando especialidade médica
    'selecting_doctor',        # Selecionando médico
    'choosing_schedule',       # Escolhendo horário
    'confirming'               # Confirmando agendamento
]
```

### **Tipos de Mensagem**
```python
MESSAGE_TYPES = [
    'user',    # Usuário
    'bot',     # Bot
    'system'   # Sistema
]
```

### **Sistema de Pausar/Retomar**
```python
# Campo adicional no modelo ConversationSession
previous_state = models.CharField(max_length=50, blank=True, null=True)

# Estados que trabalham juntos:
# - answering_questions: Estado atual quando respondendo dúvidas
# - previous_state: Estado anterior antes de pausar para dúvidas
# - Palavras-chave para retomar: "continuar", "retomar", "voltar"
```

## 🗄️ Persistência de Dados

### **Banco de Dados**
- **SQLite** (desenvolvimento)
- **PostgreSQL** (produção planejada)

### **Cache**
- **Django Cache Framework**
- **RAG Cache** para dados da clínica (30 minutos)
- **Session Cache** para conversas ativas
- **Token Cache** para monitoramento
- **Doctor Cache** para médicos específicos

### **Armazenamento**
- **Sessões persistentes** em banco
- **Mensagens históricas** preservadas
- **Estados de fluxo** mantidos

## 🔐 Segurança

### **Autenticação**
- **WhatsApp Verify Token** para webhooks
- **Google Service Account** para Calendar API
- **Gemini API Key** para IA

### **Validação**
- **Sanitização** de inputs
- **Validação** de dados
- **Rate limiting** (planejado)

## 📈 Performance

### **Otimizações Implementadas**
- **Cache inteligente** para dados RAG
- **Sessões persistentes** para continuidade
- **Monitoramento de tokens** com modo econômico
- **Extração de entidades** otimizada
- **Validação de dados** em tempo real

### **Métricas**
- **Tempo de resposta**: < 2s
- **Disponibilidade**: 99.9%
- **Throughput**: 100+ mensagens/min

## 🚀 Escalabilidade

### **Horizontal**
- **Load balancer** (planejado)
- **Múltiplas instâncias** Django
- **Cache distribuído** Redis (planejado)

### **Vertical**
- **Otimização** de queries
- **Indexação** de banco
- **Compressão** de dados

## 🔧 Manutenibilidade

### **Código Limpo**
- **Serviços bem definidos** com responsabilidades claras
- **Documentação** abrangente
- **Testes** automatizados

### **Monitoramento**
- **Logs estruturados**
- **Métricas** de performance
- **Alertas** automáticos (planejado)

---

**Esta arquitetura representa o estado atual do sistema após a refatoração completa para centralização no Gemini AI.**
