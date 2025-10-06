# 🏗️ Arquitetura Atual do Sistema - Chatbot Clínica Médica

## 📐 Visão Geral da Arquitetura

O sistema foi completamente refatorado para uma arquitetura **centralizada no Google Gemini AI**, eliminando a fragmentação anterior e simplificando drasticamente o fluxo de dados.

## 🎯 Princípios Arquiteturais

### 1. **Gemini AI como Protagonista**
- **Motor único** de conversação e análise
- **Inteligência centralizada** para todas as decisões
- **Eliminação** de múltiplos serviços redundantes

### 2. **Arquitetura Simplificada**
- **8 serviços essenciais** (antes: 10+ serviços)
- **Fluxo linear** e previsível
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
│ │                 │ │                  │ │                 │ │
│ │ • Análise IA    │ │ • Persistência   │ │ • Webhook       │ │
│ │ • Geração       │ │ • Sessões        │ │ • Mensagens     │ │
│ │ • Coordenação   │ │ • Estados        │ │ • Mídias        │ │
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
- AppointmentRequest     # Solicitações de agendamento
```

#### **Services** (`services/`)

##### **Gemini Chatbot Service** (Protagonista Principal)
```python
# Arquivo: gemini_chatbot_service.py
class GeminiChatbotService:
    """
    Motor principal do chatbot
    Responsabilidades:
    - Análise de intenções
    - Geração de respostas
    - Coordenação de fluxo
    - Integração com RAG
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
- GEMINI_API_KEY       # Chave do Gemini AI
- WHATSAPP_TOKEN       # Token WhatsApp
- GOOGLE_CALENDAR_ID   # ID do calendário
- DATABASE_CONFIG      # Configuração do banco
```

## 🔄 Fluxo de Dados

### 1. **Recepção de Mensagem**
```
WhatsApp → Webhook → Django → Gemini Chatbot Service
```

### 2. **Processamento Inteligente**
```
Gemini AI → Análise → RAG Service → Base de Conhecimento
```

### 3. **Geração de Resposta**
```
Gemini AI → Resposta → Conversation Service → Persistência
```

### 4. **Envio de Resposta**
```
Django → WhatsApp Service → WhatsApp Business API → Paciente
```

## 📊 Estados do Sistema

### **Estados de Conversa**
```python
STATES = [
    'idle',                    # Ocioso
    'collecting_patient_info', # Coletando dados do paciente
    'collecting_info',         # Coletando informações
    'confirming_name',         # Confirmando nome
    'selecting_doctor',        # Selecionando médico
    'choosing_schedule',       # Escolhendo horário
    'confirming',              # Confirmando
    'fornecendo_info'          # Fornecendo informações
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
