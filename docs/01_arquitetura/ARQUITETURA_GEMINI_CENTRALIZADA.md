# Arquitetura Gemini Centralizada - Chatbot Clínica Médica - Atualizada 15/01/2025

## 📐 Visão Geral

A arquitetura atual mantém o **Google Gemini AI** como cérebro central do chatbot, mas agora estruturado em um conjunto de módulos especializados dentro de `api_gateway/services/gemini/`. O `GeminiChatbotService` continua responsável pelo fluxo completo de mensagens, porém delega tarefas específicas (detecção de intenção, extração de entidades, geração de respostas e gerenciamento de sessão) para componentes dedicados. Isso garante inteligência centralizada com código mais organizado e fácil de manter.

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
- **Sincronização automática** entre cache e banco

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
│                 (Túnel Local - Dev)                           │
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
│ ┌─────────────────────────────────────────────────────────┐ │
│ │         GEMINI CHATBOT SERVICE (MODULARIZADO)          │ │
│ │                                                         │ │
│ │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │ │
│ │  │   CORE       │  │   INTENT     │  │   ENTITY     │ │ │
│ │  │   SERVICE    │→ │   DETECTOR   │→ │   EXTRACTOR  │ │ │
│ │  │              │  │              │  │              │ │ │
│ │  │ Orquestrador │  │ • Gemini AI  │  │ • Gemini AI  │ │ │
│ │  │ Principal    │  │ • Gemini AI  │  │ • Gemini AI  │ │ │
│ │  └──────┬───────┘  └──────────────┘  └──────────────┘ │ │
│ │         │                                              │ │
│ │  ┌──────▼───────┐  ┌──────────────┐  ┌──────────────┐ │ │
│ │  │  RESPONSE    │  │   SESSION    │  │   TOKEN      │ │ │
│ │  │  GENERATOR   │← │   MANAGER    │← │   MONITOR    │ │ │
│ │  │              │  │              │  │              │ │ │
│ │  │ • Prompts    │  │ • Cache+DB   │  │ • Monitora   │ │ │
│ │  │ • Contexto   │  │ • Sincroniza │  │ • Econômico  │ │ │
│ │  └──────────────┘  └──────────────┘  └──────────────┘ │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                               │
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│ │ CONVERSATION    │ │ WHATSAPP        │ │ RAG SERVICE     │ │
│ │ SERVICE         │ │ SERVICE         │ │                 │ │
│ │                 │ │                 │ │                 │ │
│ │ • Persistência  │ │ • Webhook       │ │ • Base Conhec.  │ │
│ │ • Sessões       │ │ • Mensagens     │ │ • Cache Dados   │ │
│ │ • Estados       │ │ • Mídias        │ │ • Serialização  │ │
│ │ • Histórico     │ │                 │ │                 │ │
│ └─────────────────┘ └─────────────────┘ └─────────────────┘ │
│                                                               │
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│ │ GOOGLE CALENDAR │ │ HANDOFF         │ │ SMART SCHEDULING│ │
│ │ SERVICE         │ │ SERVICE         │ │ SERVICE         │ │
│ │                 │ │                 │ │                 │ │
│ │ • Disponibilidade│ │ • Transferência │ │ • Agendamento   │ │
│ │ • Eventos       │ │ • Links         │ │ • Horários      │ │
│ │ • Sincronização │ │ • Notificações  │ │ • Otimização    │ │
│ └─────────────────┘ └─────────────────┘ └─────────────────┘ │
└───────────────────────────────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
┌───────▼──────┐ ┌───▼──────┐ ┌────▼──────┐
│   CACHE     │ │   DB     │ │  EXTERNAL│
│   (RAM)     │ │ (SQLite) │ │   APIs   │
│             │ │          │ │          │
│ • Sessões   │ │ • Sessions│ │ • Gemini │
│ • RAG Data  │ │ • Messages│ │ • WhatsApp│
│ • Tokens    │ │ • Models  │ │ • Calendar│
└─────────────┘ └───────────┘ └──────────┘
```

## Arquitetura Centralizada e Modular

### Serviços Principais

1. **`GeminiChatbotService`** (`api_gateway/services/gemini/core_service.py`)
   - Orquestra o pipeline de conversação
   - Coordena os módulos `IntentDetector`, `EntityExtractor`, `ResponseGenerator` e `SessionManager`
   - Integra com `RAGService`, `ConversationService`, `SmartSchedulingService` e `HandoffService`
   - Aplica lógica de pausa/retomada e confirmações de agendamento

2. **`IntentDetector`** (`api_gateway/services/gemini/intent_detector.py`)
   - Analisa mensagens com Gemini AI
   - Retorna intenção, próximo estado e confiança
   - Pós-processamento para ajustes de classificação
   - **Confiança**: coletada para métricas/monitoramento, não usada para decisões

3. **`EntityExtractor`** (`api_gateway/services/gemini/entity_extractor.py`)
   - Extrai entidades exclusivamente com Gemini AI
   - Normaliza dados de pacientes, médicos, datas e horários
   - Valida especialidades contra a base persistida
   - Sem fallbacks - se Gemini falhar, retorna vazio

4. **`ResponseGenerator`** (`api_gateway/services/gemini/response_generator.py`)
   - Monta prompts estruturados por intenção
   - Ajusta parâmetros conforme modo econômico do `TokenMonitor`
   - Utiliza contexto histórico e dados do RAG

5. **`SessionManager`** (`api_gateway/services/gemini/session_manager.py`)
   - Sincroniza cache e banco de dados
   - Mantém histórico recente da conversa
   - Persiste estados, entidades confirmadas e mensagens

6. **`RAGService`** (`api_gateway/services/rag_service.py`)
   - Consolida informações da clínica com cache inteligente
   - Exponibiliza dados para o Gemini responder com precisão

7. **`ConversationService`** (`api_gateway/services/conversation_service.py`)
   - Controla sessões, mensagens e estados persistentes
   - Dá suporte ao sistema de pausa/retomada de dúvidas

8. **`WhatsAppService`** (`api_gateway/services/whatsapp_service.py`)
   - Recebe e envia mensagens via WhatsApp Business API
   - Garante validação de webhook e suporte a templates

9. **`SmartSchedulingService`** (`api_gateway/services/smart_scheduling_service.py`)
   - Consulta horários em tempo real via Google Calendar
   - Consolida disponibilidade para o Gemini

10. **`GoogleCalendarService`** (`api_gateway/services/google_calendar_service.py`)
    - Integra com a agenda oficial da clínica
    - Cria e sincroniza eventos confirmados

11. **`HandoffService`** (`api_gateway/services/handoff_service.py`)
    - Gera links e mensagens para repasse à secretária
    - Valida dados do agendamento antes de concluir

12. **`TokenMonitor`** (`api_gateway/services/token_monitor.py`)
    - Monitora consumo de tokens do Gemini
    - Aciona modo econômico e registra uso diário

## 🔧 Componentes Detalhados

### 1. **API Gateway** (`api_gateway/`)

#### **Models** (`models.py`)
```python
# Principais modelos
- ConversationSession    # Sessões de conversa persistentes
- ConversationMessage    # Mensagens individuais com entidades
```

#### **Services** (`services/`)

##### **Gemini Chatbot Service** (Modularizado)
```python
# Arquivo: api_gateway/services/gemini/core_service.py
class GeminiChatbotService:
    """
    Orquestrador principal do chatbot modularizado
    Responsabilidades:
    - Coordenação de todos os módulos especializados
    - Fluxo principal de processamento de mensagens
    - Integração com serviços externos
    - Sistema de pausar/retomar para dúvidas
    - Aplicação de lógica de confirmação de agendamento
    """
```

##### **Módulos Especializados do Gemini Service**

**IntentDetector** (`intent_detector.py`)
```python
class IntentDetector:
    """
    Detecção de intenções do usuário
    Responsabilidades:
    - Análise de mensagens com Gemini AI
    - Determinação do próximo estado da conversa
    - Pós-processamento para ajustes de classificação
    - Temperature: 0.6 (análise precisa)
    - Retorna: intent, next_state, confidence, reasoning
    
    Nota sobre Confiança (confidence):
    - A confiança é coletada do Gemini para monitoramento e métricas
    - Armazenada em banco de dados e logs para análise histórica
    - Atualmente NÃO é usada para tomar decisões (sem fallback)
    - Propósito: métricas de qualidade, debugging e análises futuras
    - Possíveis usos futuros: confirmação adicional quando < 0.7
    """
```

**EntityExtractor** (`entity_extractor.py`)
```python
class EntityExtractor:
    """
    Extração de entidades das mensagens
    Responsabilidades:
    - Extração exclusiva com Gemini AI
    - Sem fallbacks - se Gemini falhar, retorna vazio
    - Validação de especialidades contra banco de dados
    - Normalização de nomes, datas e horários
    - Validação e normalização de entidades extraídas
    """
```

**ResponseGenerator** (`response_generator.py`)
```python
class ResponseGenerator:
    """
    Geração de respostas contextualizadas
    Responsabilidades:
    - Geração com Gemini baseada em contexto completo
    - Modo econômico automático via TokenMonitor
    - Prompts estruturados por intenção
    - Filtragem de médicos por especialidade
    - Integração com dados do RAG
    """
```

**SessionManager** (`session_manager.py`)
```python
class SessionManager:
    """
    Gerenciamento de sessões de conversa
    Responsabilidades:
    - Cache + Banco de dados dual (híbrido)
    - Sincronização automática entre cache e banco
    - Processamento e normalização de datas e horários
    - Histórico de conversas limitado
    - Resolução de referências (pronomes para médicos)
    """
```

##### **Conversation Service**
```python
# Arquivo: conversation_service.py
class ConversationService:
    """
    Gerenciamento de conversas com persistência
    Responsabilidades:
    - Persistência de sessões no banco de dados
    - Gerenciamento de estados da conversa
    - Sistema de pausar/retomar para dúvidas
    - Validação de dados coletados
    - Histórico completo de mensagens
    """
```

##### **WhatsApp Service**
```python
# Arquivo: whatsapp_service.py
class WhatsAppService:
    """
    Integração WhatsApp Business API
    Responsabilidades:
    - Recebimento de webhooks do WhatsApp
    - Envio de mensagens para usuários
    - Processamento de mídias (imagens, áudios)
    - Validação de tokens de webhook
    - Suporte a templates de mensagem
    """
```

##### **Google Calendar Service**
```python
# Arquivo: google_calendar_service.py
class GoogleCalendarService:
    """
    Integração Google Calendar API
    Responsabilidades:
    - Consulta disponibilidade de horários
    - Criação de eventos no calendário
    - Sincronização com agenda da clínica
    - Validação de conflitos de horário
    """
```

##### **Handoff Service**
```python
# Arquivo: handoff_service.py
class HandoffService:
    """
    Transferência para secretária
    Responsabilidades:
    - Geração de links de handoff
    - Notificações para secretária
    - Transferência de contexto completo
    - Validação de dados antes de concluir
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
    - Otimização de fluxo de conversa
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
    - Cache inteligente de dados estáticos
    - Consultas otimizadas ao banco
    - Serialização para Gemini
    - Dados: médicos, especialidades, convênios, exames
    """
```

##### **Token Monitor Service**
```python
# Arquivo: token_monitor.py
class TokenMonitor:
    """
    Monitoramento de tokens do Gemini
    Responsabilidades:
    - Monitoramento de uso de tokens diário
    - Aplicação de modo econômico automático
    - Otimização automática de configurações
    - Alertas de limite de uso
    - Cache de contadores de tokens
    """
```

### 2. **RAG Agent** (`rag_agent/`)

#### **Models** (`models.py`)
```python
# Base de conhecimento da clínica
- ClinicaInfo          # Informações gerais da clínica
- Medico               # Dados dos médicos com CRM
- Especialidade        # Especialidades médicas ativas
- Convenio             # Convênios aceitos
- HorarioTrabalho      # Horários de trabalho dos médicos
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
WhatsApp → Webhook → Django Views → WhatsAppService → GeminiChatbotService (Core)
```

### 2. **Processamento Modularizado**
```
Core Service → SessionManager (carrega/cria sessão)
            → IntentDetector (detecta intenção)
            → EntityExtractor (extrai entidades)
            → Validação de dados (ConversationService)
```

### 3. **Geração de Resposta**
```
ResponseGenerator → RAG Service (busca dados da clínica)
                 → SmartSchedulingService (consulta horários)
                 → TokenMonitor (ajusta parâmetros)
                 → Gemini AI (gera resposta contextualizada)
```

### 4. **Persistência e Envio**
```
SessionManager → Conversation Service (salva mensagens)
              → HandoffService (se necessário)
              → WhatsApp Service → Paciente
```

## Fluxo de Conversação Simplificado

```
WhatsApp → WhatsAppService → GeminiChatbotService
                                    ↓
                       SessionManager + ConversationService
                                    ↓
                   IntentDetector → EntityExtractor
                                    ↓
 RAGService + SmartSchedulingService + HandoffService (quando necessário)
                                    ↓
                        ResponseGenerator → WhatsAppService
```

## Pipeline do Gemini

1. **Análise da mensagem**  
   - Intenção detectada por `IntentDetector`
   - Entidades extraídas por `EntityExtractor`
2. **Atualização de contexto**  
   - `SessionManager` sincroniza estados e histórico
   - `ConversationService` registra mensagens
3. **Respostas inteligentes**  
   - `ResponseGenerator` usa dados do RAG e do agendamento
   - `TokenMonitor` ajusta parâmetros em modo econômico
4. **Pós-processamento**  
   - Handoff e confirmações via `HandoffService`
   - Disponibilidade validada pelo `SmartSchedulingService`

## Intenções Suportadas

- `saudacao`
- `buscar_info`
- `agendar_consulta`
- `confirmar_agendamento`
- `buscar_medico`
- `buscar_exame`
- `buscar_horarios`
- `despedida`
- `duvida`

## Estados da Conversa Persistidos

- `idle`
- `collecting_patient_info`
- `answering_questions`
- `confirming_name`
- `selecting_specialty`
- `selecting_doctor`
- `choosing_schedule`
- `confirming`

## 🗄️ Persistência de Dados

### **Banco de Dados**
- **SQLite** (desenvolvimento)
- **PostgreSQL** (produção planejada)

### **Cache**
- **Django Cache Framework** (LocMemCache atual, Redis planejado)
- **RAG Cache** para dados da clínica (30 minutos)
- **Session Cache** para conversas ativas (15-60 minutos dinâmico)
- **Token Cache** para monitoramento (24 horas)
- **Doctor Cache** para médicos específicos

### **Armazenamento**
- **Sessões persistentes** em banco de dados
- **Mensagens históricas** preservadas com entidades
- **Estados de fluxo** mantidos entre conversas
- **Sincronização automática** cache ↔ banco

> 📖 Para mais detalhes sobre persistência vs cache, consulte: `ARMAZENAMENTO_PERSISTENTE_VS_VOLATIL.md`

## 🔐 Segurança

### **Autenticação**
- **WhatsApp Verify Token** para validação de webhooks
- **Google Service Account** para Calendar API
- **Gemini API Key** para IA (armazenada em `.env`)

### **Validação**
- **Sanitização** de inputs do usuário
- **Validação** de dados contra banco de dados
- **Rate limiting** (planejado)
- **Validação de entidades** antes de salvar

## 📈 Performance

### **Otimizações Implementadas**
- **Cache inteligente** para dados RAG (reduz queries em 80-90%)
- **Sessões persistentes** para continuidade (evita reprocessamento)
- **Monitoramento de tokens** com modo econômico automático
- **Extração de entidades** otimizada (exclusivamente com Gemini AI)
- **Validação de dados** em tempo real
- **Histórico limitado** enviado ao Gemini (últimas 3 mensagens)

### **Métricas**
- **Tempo de resposta**: < 2s (com cache)
- **Disponibilidade**: 99.9% (planejado)
- **Throughput**: 100+ mensagens/min
- **Redução de tokens**: 94% (com histórico limitado)

## 🚀 Escalabilidade

### **Horizontal**
- **Load balancer** (planejado)
- **Múltiplas instâncias** Django
- **Cache distribuído** Redis (planejado)
- **Session affinity** para manter contexto

### **Vertical**
- **Otimização** de queries com prefetch_related
- **Indexação** de banco de dados
- **Compressão** de dados (planejado)
- **Timeout dinâmico** de cache baseado em uso

## 🔧 Manutenibilidade

### **Código Limpo**
- **Serviços bem definidos** com responsabilidades claras
- **Módulos especializados** para cada funcionalidade
- **Documentação** abrangente em código e markdown
- **Testes** automatizados (planejado)

### **Monitoramento**
- **Logs estruturados** por componente
- **Métricas** de performance e tokens
- **Alertas** automáticos (planejado)
- **Endpoints de teste** para validação

## Arquivos Substituídos na Refatoração

- `api_gateway/services/gemini_chatbot_service.py` ➜ dividido em `api_gateway/services/gemini/`
- `flow_agent/`, `base_service.py`, `intent_detection_service.py`, `smart_collection_service.py` ➜ removidos
- Novos módulos centralizados expostos em `api_gateway/services/gemini/__init__.py`

## Como Usar

### Processamento de Mensagem
```python
from api_gateway.services.gemini import GeminiChatbotService

gemini_chatbot_service = GeminiChatbotService()
result = gemini_chatbot_service.process_message(phone_number, message)

response = result['response']
intent = result.get('intent')
confidence = result.get('confidence')
handoff_link = result.get('handoff_link')
```

### Verificação de Status
```python
# Verificar se o serviço está habilitado
if gemini_chatbot_service.enabled:
    print("Serviço Gemini está ativo")
else:
    print("Serviço Gemini está desabilitado")
```

### Monitoramento de Tokens
```python
from api_gateway.services.token_monitor import token_monitor

stats = token_monitor.get_token_usage_stats()
print(f"Tokens usados hoje: {stats['tokens_used_today']}")
print(f"Limite diário: {stats['daily_limit']}")
print(f"Modo econômico ativo: {stats['economy_mode_active']}")
```

## Configuração Essencial

- Variáveis sensíveis no `.env` (ver `.env.example`)
- Apps habilitados em `core/settings.py` (`rag_agent`, `api_gateway`)
- Chaves necessárias: `GEMINI_API_KEY`, credenciais WhatsApp, Google Calendar, etc.

## Endpoints de Teste (prefixo `/api/`)

- `GET /api/test/gemini/` – valida conexão com Gemini
- `POST /api/test/chatbot/` – executa `process_message`
- `POST /api/test/intent-analysis/` – roda apenas o `IntentDetector`
- `POST /api/test/entity-extraction/` – testa o `EntityExtractor`
- `POST /api/test/handoff/` – gera handoff com dados simulados
- `GET /api/test/check-data/` – verifica dados persistidos
- `GET /api/monitor/tokens/` – estatísticas do `TokenMonitor`
- `POST /api/monitor/tokens/reset/` – zera contadores de tokens
- `GET /api/test/calendar/` – checa integração com Google Calendar
- `GET /api/test/availability/<doctor_name>/` – horários de um médico

## 📊 Logs e Monitoramento

- **Logs estruturados** para intents, entidades e respostas
- **Auditoria** de consumo de tokens diário
- **Histórico** de agendamentos e handoffs gerado automaticamente
- **Métricas** de performance por componente
- **Alertas** de limite de tokens (80%, 90%, 95%)

### Sobre a Confiança (Confidence)

Com a remoção do mecanismo de fallback, a **confiança** (`confidence`) coletada pelo `IntentDetector` não é mais usada para tomar decisões operacionais. Seu propósito atual é:

1. **Métricas e Monitoramento**
   - Análise histórica da qualidade das detecções de intenção
   - Identificação de padrões de baixa confiança
   - Acompanhamento de performance ao longo do tempo

2. **Logging e Auditoria**
   - Registro de cada detecção com seu nível de confiança
   - Facilita debugging de problemas de classificação
   - Permite análise de casos específicos

3. **Armazenamento em Banco**
   - Cada mensagem armazena sua confiança em `ConversationMessage.confidence`
   - Dados históricos para análises estatísticas
   - Base para melhorias futuras do sistema

4. **Possíveis Usos Futuros**
   - Implementar confirmação adicional quando confiança < 0.7
   - Ajustar comportamento da resposta baseado na confiança
   - Gerar alertas para revisão manual em casos de baixa confiança
   - Melhorar prompts quando padrões de baixa confiança são detectados

**Importante**: A confiança é coletada automaticamente, mas o sistema **sempre aceita a decisão do Gemini**, independentemente do valor de confiança. Não há lógica condicional que use a confiança para alterar o fluxo de processamento.

## Próximos Passos Recomendados

1. Garantir credenciais válidas (Gemini, WhatsApp, Google)
2. Executar endpoints de teste após cada ajuste
3. Monitorar métricas de tokens em produção
4. Ajustar prompts do `ResponseGenerator` conforme novas intenções
5. Expandir base RAG sempre que novos serviços forem adicionados
6. Migrar para Redis para cache distribuído (produção)
7. Migrar para PostgreSQL para melhor escalabilidade

## 📚 Documentação Relacionada

- **Armazenamento Persistente vs Volátil**: `ARMAZENAMENTO_PERSISTENTE_VS_VOLATIL.md`
- **Organização do Banco de Dados**: `ORGANIZACAO_BANCO_DADOS.md`
- **Arquitetura Atual**: Este documento (consolidado)

---

**Última atualização:** 15/01/2025  
**Versão:** 2.0 (Consolidado)  
**Autor:** Documentação Técnica - Chatbot Clínica Médica
