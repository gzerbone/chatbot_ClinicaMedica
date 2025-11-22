# 🤖 Chatbot Clínica Médica - Sistema Inteligente de Agendamento

## 📋 Visão Geral

Sistema de chatbot inteligente desenvolvido em **Django REST Framework** para automatizar o agendamento de consultas médicas na **Clínica PneumoSono**. O sistema utiliza **Google Gemini AI 2.0 Flash** como motor principal de conversação, com integração completa ao **WhatsApp Business API** e **Google Calendar** para gerenciamento inteligente de agendamentos.

### 🎯 Principais Diferenciais

- ✅ **Conversação Natural** - Powered by Gemini AI 2.0 Flash
- ✅ **Agendamento Inteligente** - Integração em tempo real com Google Calendar
- ✅ **Sistema RAG** - Base de conhecimento contextual da clínica
- ✅ **Persistência Completa** - Sessões e histórico de conversas
- ✅ **Monitoramento de Tokens** - Controle de custos da API Gemini
- ✅ **Handoff para Secretaria** - Transferência humanizada quando necessário

## 🏗️ Arquitetura Atual

### Estrutura do Projeto

```
chatbot_ClinicaMedica/
├── api_gateway/                 # Gateway principal da API
│   ├── models.py                # Modelos de dados (sessões, mensagens)
│   ├── services/                # Serviços de negócio
│   │   ├── conversation_service.py      # Gerenciamento de sessões e persistência
│   │   ├── gemini_chatbot_service.py    # Motor principal Gemini AI
│   │   ├── whatsapp_service.py          # Integração WhatsApp Business API
│   │   ├── google_calendar_service.py   # Integração Google Calendar
│   │   ├── handoff_service.py           # Transferência para secretaria
│   │   ├── rag_service.py               # Sistema RAG (Retrieval Augmented Generation)
│   │   ├── smart_scheduling_service.py  # Agendamento inteligente
│   │   └── token_monitor.py             # Monitoramento de tokens Gemini
│   ├── views.py                 # Endpoints da API (webhooks)
│   ├── urls.py                  # Roteamento de URLs
│   └── middleware.py            # Middlewares customizados
├── rag_agent/                   # Agente de conhecimento
│   ├── models.py                # Modelos: ClinicaInfo, Medico, Especialidade, Exame
│   ├── views.py                 # API REST para dados da clínica
│   ├── serializers.py           # Serializers DRF
│   └── urls.py                  # Roteamento RAG API
├── core/                        # Configurações Django
│   ├── settings.py              # Configurações principais (com python-decouple)
│   └── urls.py                  # Roteamento global
├── docs/                        # 📚 Documentação completa organizada
│   ├── README.md                # Índice geral da documentação
│   ├── 01_arquitetura/          # Documentos de arquitetura
│   ├── 02_setup_configuracao/   # Guias de instalação e configuração
│   ├── 03_desenvolvimento/      # Guias e dicas para desenvolvimento
│   ├── 04_fluxos_processos/     # Documentação de fluxos de negócio
│   ├── 05_otimizacoes/          # Gestão de recursos e performance
│   ├── 06_modularizacao/        # Refatoração e organização do código
│   ├── 07_correcoes/            # Histórico de correções implementadas
│   └── _obsoletos/              # Documentos obsoletos
├── scripts/                     # Scripts utilitários e testes
│   ├── criar_dados_pneumosono.py # Popula dados iniciais
│   ├── verificar_banco_dados.py  # Verifica estado do banco
│   └── ... (15+ scripts de teste)
├── tests/                       # Testes automatizados
│   ├── api_gateway/             # Testes da API Gateway
│   └── rag_agent/               # Testes do RAG Agent
├── service-account-key.json    # ⚠️ Chave Google Service Account (não commitar!)
├── .env                        # ⚠️ Variáveis de ambiente (não commitar!)
├── requirements.txt            # Dependências Python
└── manage.py                   # Django management
```

### Componentes Principais

#### 1. **Gemini Chatbot Service** 🤖 (Motor Principal)
- **Arquivo**: `api_gateway/services/gemini/core_service.py` (modularizado)
- **Modelo**: Google Gemini AI 2.0 Flash
- **Estrutura Modular**:
  - `core_service.py`: Orquestrador principal (GeminiChatbotService)
  - `intent_detector.py`: Detecção de intenções
  - `entity_extractor.py`: Extração de entidades
  - `response_generator.py`: Geração de respostas
  - `session_manager.py`: Gerenciamento de sessões
- **Responsabilidades**:
  - Gerenciamento completo do fluxo de conversação
  - Análise de intenções e extração de entidades (nome, telefone, especialidade)
  - Geração de respostas contextuais e naturais
  - Coordenação com RAG Service para contexto
  - Controle de estados de conversação

#### 2. **Conversation Service** 💾
- **Arquivo**: `api_gateway/services/conversation_service.py`
- **Responsabilidades**:
  - Persistência de sessões de conversa (modelo `ConversationSession`)
  - Gerenciamento de estados do fluxo (idle, collecting_info, selecting_doctor, etc.)
  - Histórico completo de mensagens (modelo `ConversationMessage`)
  - Cache de dados do paciente
  - Validação de sessões ativas (timeout 24h)

#### 3. **RAG Service** 📚 (Base de Conhecimento)
- **Arquivo**: `api_gateway/services/rag_service.py`
- **Modelos**: `rag_agent/models.py` (ClinicaInfo, Medico, Especialidade, Exame)
- **Responsabilidades**:
  - Retrieval Augmented Generation para contexto
  - Informações sobre médicos, especialidades, exames
  - Políticas de agendamento e atendimento
  - Dados de contato e localização da clínica
  - Horários de funcionamento

#### 4. **WhatsApp Service** 💬
- **Arquivo**: `api_gateway/services/whatsapp_service.py`
- **Responsabilidades**:
  - Integração com WhatsApp Business API (Cloud API)
  - Envio e recebimento de mensagens
  - Processamento de webhooks (verificação e mensagens)
  - Suporte a diferentes tipos de mídia
  - Formatação de mensagens

#### 5. **Google Calendar Service** 📅
- **Arquivo**: `api_gateway/services/google_calendar_service.py`
- **Responsabilidades**:
  - Autenticação via Service Account
  - Consulta de disponibilidade em tempo real
  - **Identificação inteligente de eventos** - Gera automaticamente padrões de busca para médicos do banco de dados
  - Criação de eventos de agendamento
  - Sincronização com calendário único compartilhado da clínica
  - Gerenciamento de slots de horários
  - Filtragem de eventos por médico (sem necessidade de calendários separados)

#### 6. **Token Monitor** 📊 (Novo!)
- **Arquivo**: `api_gateway/services/token_monitor.py`
- **Responsabilidades**:
  - Monitoramento de consumo de tokens do Gemini
  - Controle de custos da API
  - Logs de uso e estatísticas
  - Alertas de limites

#### 7. **Handoff Service** 👥
- **Arquivo**: `api_gateway/services/handoff_service.py`
- **Responsabilidades**:
  - Transferência para atendimento humano
  - Geração de links de confirmação
  - Notificação da secretaria
  - Compilação de resumo da conversa

#### 8. **Smart Scheduling Service** 🎯
- **Arquivo**: `api_gateway/services/smart_scheduling_service.py`
- **Responsabilidades**:
  - Lógica inteligente de agendamento
  - Otimização de horários
  - Validação de disponibilidade
  - Sugestões de horários alternativos

## 🚀 Funcionalidades

### ✅ Implementadas

#### 1. **Conversação Inteligente com IA** 🤖
   - ✅ Análise de intenções com Gemini AI 2.0 Flash
   - ✅ Extração automática de entidades (nome, telefone, especialidade, data)
   - ✅ Confirmação interativa de dados do paciente
   - ✅ Fluxo conversacional natural e contextual
   - ✅ Memória de contexto durante toda a sessão
   - ✅ Respostas personalizadas baseadas no histórico

#### 2. **Sistema de Agendamento Completo** 📅
   - ✅ Coleta inteligente de informações do paciente
   - ✅ Validação de dados (nome, telefone)
   - ✅ Seleção de médico por especialidade
   - ✅ Consulta de disponibilidade em tempo real no Google Calendar
   - ✅ Apresentação de horários disponíveis
   - ✅ Geração de links de confirmação
   - ✅ Pré-agendamento com validação da secretaria
   - ✅ Sincronização automática com calendário

#### 3. **Integração WhatsApp Business** 💬
   - ✅ Recebimento de mensagens via webhook
   - ✅ Envio de respostas automáticas
   - ✅ Suporte a diferentes tipos de mídia
   - ✅ Validação de webhook do WhatsApp
   - ✅ Tratamento de erros e retry automático

#### 4. **Persistência e Gerenciamento de Dados** 💾
   - ✅ Sessões de conversa persistentes no banco de dados
   - ✅ Histórico completo de mensagens (user, bot, system)
   - ✅ Cache inteligente de dados RAG
   - ✅ Estados de fluxo preservados entre mensagens
   - ✅ Timeout automático de sessões (24h)
   - ✅ Modelos Django: `ConversationSession`, `ConversationMessage`

#### 5. **Sistema RAG (Retrieval Augmented Generation)** 📚
   - ✅ Base de conhecimento estruturada da clínica
   - ✅ Informações sobre médicos (nome, especialidades, CRM)
   - ✅ Catálogo de especialidades disponíveis
   - ✅ Exames oferecidos pela clínica
   - ✅ Políticas de agendamento e cancelamento
   - ✅ Dados de contato, localização e horários
   - ✅ Atualização via Django Admin

#### 6. **Monitoramento e Observabilidade** 📊
   - ✅ Token Monitor para controle de custos Gemini
   - ✅ Logs estruturados por serviço
   - ✅ Rastreamento de intenções e entidades extraídas
   - ✅ Métricas de uso e performance
   - ✅ Scripts de verificação do banco de dados

#### 7. **Handoff para Atendimento Humano** 👥
   - ✅ Transferência inteligente para secretaria
   - ✅ Geração de links de confirmação via WhatsApp
   - ✅ Resumo completo da conversa para a secretaria
   - ✅ Contexto preservado durante transferência

### 🔄 Fluxo de Agendamento Detalhado

```
┌─────────────────────────────────────────────────────────────────┐
│                    📱 PACIENTE VIA WHATSAPP                      │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│  1️⃣ RECEPÇÃO E ANÁLISE                                          │
├─────────────────────────────────────────────────────────────────┤
│  • WhatsApp webhook envia mensagem para Django                   │
│  • Gemini AI analisa intenção e contexto                        │
│  • Extração automática de entidades (nome, telefone)            │
│  • Consulta/cria sessão persistente                             │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│  2️⃣ COLETA DE INFORMAÇÕES DO PACIENTE                           │
├─────────────────────────────────────────────────────────────────┤
│  • Estado: collecting_patient_info → confirming_name            │
│  • Validação de nome completo                                   │
│  • Confirmação interativa ("Seu nome é X, está correto?")       │
│  • Validação de telefone                                        │
│  • Persistência em ConversationSession                          │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│  3️⃣ SELEÇÃO DE ESPECIALIDADE                                   │
├─────────────────────────────────────────────────────────────────┤
│  • Consulta RAG para especialidades disponíveis                 │
│  • Análise da necessidade do paciente                           │
│  • Sugestão de especialidades relevantes                        │
│  • Estado: selecting_specialty                                  │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│  4️⃣ SELEÇÃO DE MÉDICO                                           │
├─────────────────────────────────────────────────────────────────┤
│  • Estado: selecting_doctor                                     │
│  • Filtragem de médicos por especialidade                       │
│  • Apresentação de opções (nome, especialidades, CRM)           │
│  • Seleção pelo paciente                                        │
│  • Armazenamento em session.selected_doctor                     │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│  5️⃣ CONSULTA DE DISPONIBILIDADE                                 │
├─────────────────────────────────────────────────────────────────┤
│  • Estado: choosing_schedule                                    │
│  • Integração com Google Calendar API                           │
│  • Busca de slots disponíveis em tempo real                     │
│  • Apresentação de horários formatados                          │
│  • Validação de regras de agendamento                           │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│  6️⃣ CONFIRMAÇÃO E HANDOFF                                       │
├─────────────────────────────────────────────────────────────────┤
│  • Estado: confirming                                           │
│  • Resumo completo do pré-agendamento                           │
│  • Geração de link de confirmação WhatsApp                      │
│  • Transferência para secretaria (Handoff Service)              ││                                                                 │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│  7️⃣ FINALIZAÇÃO                                                 │
├─────────────────────────────────────────────────────────────────┤
│  • Estado: retorna para idle                                    │
│  • Notificação de conclusão ao paciente                         │
│  • Mensagem de despedida personalizada                          │
│  • Sessão preservada para futuras interações                    │
└─────────────────────────────────────────────────────────────────┘
```

**Estados da Sessão:**
- `idle` → Aguardando nova interação
- `collecting_patient_info` → Coletando dados básicos
- `confirming_name` → Confirmando nome do paciente
- `selecting_specialty` → Escolhendo especialidade médica
- `selecting_doctor` → Escolhendo médico
- `choosing_schedule` → Selecionando data/horário
- `answering_questions` → Respondendo dúvidas do paciente
- `confirming` → Confirmando agendamento

### 🔄 Gerenciamento Dinâmico do Fluxo

O sistema conta com funções inteligentes no `conversation_service` para facilitar a dinâmica do chat:

```python
from api_gateway.services.conversation_service import conversation_service

# Verificar informações faltantes
missing_info = conversation_service.get_missing_appointment_info(phone_number)
# Retorna: {'missing_info': ['patient_name', 'selected_doctor'], 
#           'next_action': 'ask_name', 
#           'is_complete': False}

# Obter próxima pergunta automaticamente
next_question = conversation_service.get_next_question(phone_number)
# Retorna: "Para começar o agendamento, preciso saber seu nome completo. Qual é seu nome?"
```

**Fluxo Sequencial Inteligente:**
1. `ask_name` → Solicita nome do paciente
2. `ask_specialty` → Solicita especialidade desejada
3. `ask_doctor` → Solicita médico preferido
4. `ask_date` → Solicita data da consulta
5. `ask_time` → Solicita horário da consulta
6. `generate_handoff` → Gera link de confirmação

### 💡 Sistema de Pausar/Retomar para Dúvidas

O chatbot permite que o usuário tire dúvidas a qualquer momento, incluindo durante um agendamento:

```python
# Pausar agendamento para responder dúvida
conversation_service.pause_for_question(phone_number)
# Estado atual é salvo em previous_state

# Verificar se há agendamento pausado
has_paused = conversation_service.has_paused_appointment(phone_number)

# Retomar agendamento de onde parou
resume_result = conversation_service.resume_appointment(phone_number)
# Restaura o estado anterior e continua o fluxo
```

**Cenários de Uso:**
1. 👤 **Apenas Dúvidas**: Usuário tira dúvidas sem iniciar agendamento
2. 🔄 **Dúvidas Antes**: Usuário tira dúvidas e depois inicia agendamento
3. ⏸️ **Pausar Agendamento**: Usuário pausa agendamento para tirar dúvidas e depois retoma

**Palavras-chave para Retomar:**
- "continuar"
- "voltar"
- "retomar"
- "prosseguir"
- "seguir"
- "agendamento"

## 🛠️ Tecnologias Utilizadas

### Backend Framework
- **Django 5.2.6** - Framework web Python de alto nível
- **Django REST Framework 3.16.1** - Toolkit para construção de Web APIs
- **SQLite** - Banco de dados (desenvolvimento)
- **django-cors-headers 4.3.1** - Gerenciamento de CORS

### Inteligência Artificial
- **Google Gemini AI 2.0 Flash** - Motor principal de conversação
- **google-generativeai 0.8.3** - SDK oficial do Gemini
- **Sistema RAG** - Retrieval Augmented Generation customizado

### Integrações Externas
- **Google Calendar API** - Gerenciamento de agendamentos
  - `google-api-python-client 2.181.0`
  - `google-auth 2.40.3`
  - Service Account authentication
- **WhatsApp Business Cloud API** - Interface de mensagens
  - Webhooks para recebimento
  - API REST para envio

### Gerenciamento de Configuração
- **python-decouple 3.8** - Separação de configuração do código
- **Variáveis de ambiente** - Segurança de credenciais

### Dependências Principais
```txt
# Framework
Django==5.2.6
djangorestframework==3.16.1
django-cors-headers==4.3.1

# Google AI
google-generativeai==0.8.3
google-ai-generativelanguage==0.6.10

# Google Calendar
google-api-python-client==2.181.0
google-auth==2.40.3
google-auth-httplib2==0.2.0

# Utilities
python-decouple==3.8
requests==2.32.5
```

**Veja o arquivo completo:** [`requirements.txt`](requirements.txt)

## 📦 Instalação e Configuração

### 1. Pré-requisitos
- ✅ **Python 3.8+** (recomendado: 3.10+)
- ✅ **Conta Google Cloud Platform** (para Gemini AI e Calendar)
- ✅ **WhatsApp Business Account** (Meta Business)
- ✅ **Ngrok** ou similar (para desenvolvimento local com webhooks)
- ✅ **Git** para controle de versão

### 2. Configuração do Ambiente

```bash
# Clone o repositório
git clone <repository-url>
cd chatbot_ClinicaMedica

# Crie ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Instale dependências
pip install -r requirements.txt
```

### 3. Configuração de Variáveis de Ambiente

⚠️ **CRÍTICO - Segurança**: Todas as configurações sensíveis **DEVEM** estar no arquivo `.env` na raiz do projeto.

**📖 Documentação completa:** [`docs/02_setup_configuracao/CONFIGURACAO_ENV.md`](docs/02_setup_configuracao/CONFIGURACAO_ENV.md)

#### Variáveis Necessárias

```bash
# Crie o arquivo .env na raiz do projeto
touch .env  # Linux/Mac
# ou
New-Item .env -ItemType File  # Windows PowerShell

# Configure TODAS as variáveis abaixo:
# 
# 🤖 Google Gemini AI
# GEMINI_API_KEY=sua_chave_aqui
# 
# 💬 WhatsApp Business API
# WHATSAPP_ACCESS_TOKEN=seu_token
# WHATSAPP_PHONE_NUMBER_ID=seu_id
# WHATSAPP_VERIFY_TOKEN=seu_verify_token
# 
# 📅 Google Calendar
# GOOGLE_CALENDAR_ENABLED=True
# GOOGLE_SERVICE_ACCOUNT_FILE=service-account-key.json
# CLINIC_CALENDAR_ID=seu_calendar_id@group.calendar.google.com
# 
# 🏥 Clínica
# CLINIC_WHATSAPP_NUMBER=5500000000000
# CLINIC_DOMAIN=gmail.com
# 
# ⚙️ Django
# SECRET_KEY=sua_secret_key
# DEBUG=True
```

#### 🔐 Boas Práticas de Segurança

```bash
# ✅ SEMPRE FAÇA
✓ Mantenha .env no .gitignore (já configurado)
✓ Use valores diferentes para dev e produção
✓ Rotacione API keys periodicamente (90 dias)
✓ Consulte docs/CONFIGURACAO_ENV.md para obter credenciais

# ❌ NUNCA FAÇA
✗ Commitar arquivo .env com valores reais
✗ Expor API keys em código ou documentação
✗ Compartilhar .env por email/chat
✗ Usar mesmas credenciais em ambientes diferentes
```

**💡 Dica:** O sistema usa `python-decouple` para carregar variáveis do `.env` automaticamente no `core/settings.py`.

### 4. Configuração do Banco de Dados

```bash
# Execute migrações
python manage.py migrate

# Crie superusuário
python manage.py createsuperuser

# Popule dados iniciais
python scripts/criar_dados_pneumosono.py
```

### 5. Configuração do WhatsApp

1. Configure webhook no WhatsApp Business API
2. URL do webhook: `https://seu-ngrok-url.ngrok-free.app/api/whatsapp/webhook/`
3. Token de verificação: use o valor de `WHATSAPP_VERIFY_TOKEN`

### 6. Configuração do Google Calendar

#### Passos de Configuração

1. **Google Cloud Console**
   - Crie um projeto ou use existente
   - Ative a **Google Calendar API**
   
2. **Service Account**
   - Crie uma Service Account
   - Baixe o arquivo JSON de credenciais
   - Renomeie para `service-account-key.json`
   - Coloque na raiz do projeto
   
3. **Google Calendar**
   - Abra o calendário da clínica
   - Configurações > Compartilhar com pessoas específicas
   - Adicione o email da Service Account
   - Dê permissão "Fazer alterações nos eventos"
   - Copie o ID do calendário
   
4. **Arquivo .env**
   ```bash
   GOOGLE_CALENDAR_ENABLED=True
   GOOGLE_SERVICE_ACCOUNT_FILE=service-account-key.json
   CLINIC_CALENDAR_ID=seu_calendar_id@group.calendar.google.com
   ```

#### 📅 Calendário Único Compartilhado

O sistema suporta **um único calendário** compartilhado por todos os médicos:

- ✅ **Identificação Automática**: O sistema gera automaticamente padrões de busca para identificar eventos de cada médico
- ✅ **Baseado no Banco de Dados**: Busca médicos cadastrados em `rag_agent.models.Medico`
- ✅ **Sem Configuração Manual**: Não precisa adicionar médicos manualmente no código
- ℹ️ **Override Manual** (opcional): Use `DOCTOR_EVENT_PATTERNS` no `settings.py` apenas para casos especiais

**Formato de eventos no calendário:**
- "Dr. João - Consulta"
- "Consulta Cardiologia - João Carvalho"
- "Dr Gustavo - Retorno"

📖 **Documentação completa:** [`docs/02_setup_configuracao/GOOGLE_CALENDAR_SETUP.md`](docs/02_setup_configuracao/GOOGLE_CALENDAR_SETUP.md)

## 🧪 Testes

### Executar Testes
```bash
# Todos os testes
python manage.py test

# Testes específicos
python manage.py test tests.api_gateway.test_webhook_integration
python manage.py test tests.api_gateway.test_handoff
```

### Scripts de Teste
```bash
# Testar persistência
python scripts/testar_persistencia_completa.py

# Verificar banco de dados
python scripts/verificar_banco_dados.py

# Testar agendamento
python scripts/test_improved_logging.py
```

## 📊 Monitoramento e Logs

### Logs Disponíveis
- **Conversation Logger**: Logs de conversação
- **Gemini Logger**: Logs do Gemini AI
- **WhatsApp Logger**: Logs de integração WhatsApp
- **Calendar Logger**: Logs do Google Calendar

### Verificação de Estado
```bash
# Verificar sessões ativas
python scripts/verificar_sessao_cache.py

# Verificar dados da clínica
python scripts/verificar_banco_dados.py
```

## 🔧 Scripts Utilitários

A pasta `scripts/` contém diversos utilitários para desenvolvimento e manutenção:

### 📊 Gerenciamento de Dados
- **`criar_dados_pneumosono.py`** - Popula banco com dados da Clínica PneumoSono
  ```bash
  python scripts/criar_dados_pneumosono.py
  ```

- **`verificar_banco_dados.py`** - Verifica estado completo do banco de dados
  ```bash
  python scripts/verificar_banco_dados.py
  ```

- **`comandos_banco_dados.py`** - Comandos úteis para manipulação do banco

- **`deletar_dados_especificos.py`** - Remove dados específicos do banco

- **`quick_reset.py`** - Reset rápido do banco de dados

### 🧪 Scripts de Teste
- **`test_pre_agendamento_flow.py`** - Testa fluxo completo de pré-agendamento
- **`testar_persistencia_completa.py`** - Valida persistência de sessões
- **`test_improved_logging.py`** - Testa sistema de logs
- **`test_optimized_integration.py`** - Testa integração otimizada
- **`test_entity_processing.py`** - Testa extração de entidades
- **`test_date_normalization.py`** - Testa normalização de datas
- **`testar_regex_entidades.py`** - Testa expressões regulares

### ⚙️ Configuração e Setup
- **`criar_superuser.py`** - Cria superusuário Django
- **`setup_calendar_dev.py`** - Configura Google Calendar para desenvolvimento

### 📋 Verificação de Sistema
- **`verificar_sessao_cache.py`** - Verifica sessões ativas e cache
  ```bash
  python scripts/verificar_sessao_cache.py
  ```

### 📚 Exemplos
- **`exemplo_pratico_coleta.py`** - Exemplo de coleta de dados

## 💾 Modelos de Banco de Dados

### API Gateway (`api_gateway/models.py`)

#### ConversationSession
Armazena sessões completas de conversa com estado persistente:

```python
- phone_number (CharField, unique) - Identificador único do paciente
- patient_name (CharField) - Nome confirmado do paciente
- pending_name (CharField) - Nome aguardando confirmação
- name_confirmed (Boolean) - Status de confirmação do nome
- current_state (CharField) - Estado atual do fluxo
  • idle, collecting_patient_info, confirming_name,
  • collecting_info, selected_specialty, choosing_schedule, confirming
- selected_specialty (CharField) - Especialidade de interesse
- insurance_type (CharField) - Tipo de convênio
- preferred_date (DateField) - Data preferida
- preferred_time (TimeField) - Horário preferido
- selected_doctor (CharField) - Médico selecionado
- additional_notes (TextField) - Observações adicionais
- created_at, updated_at, last_activity (DateTimeField)
```

**Métodos:**
- `is_active()` - Verifica se sessão está ativa (< 24h)
- `update_activity()` - Atualiza timestamp

#### ConversationMessage
Registra todas as mensagens da conversa:

```python
- session (ForeignKey) - Relacionamento com ConversationSession
- message_type (CharField) - 'user', 'bot', 'system'
- content (TextField) - Conteúdo da mensagem
- intent (CharField) - Intenção identificada pelo Gemini
- confidence (FloatField) - Confiança da classificação
- entities (JSONField) - Entidades extraídas
- timestamp (DateTimeField) - Momento da mensagem
```

### RAG Agent (`rag_agent/models.py`)

#### ClinicaInfo
Informações gerais da clínica:
```python
- nome, endereco, telefone, whatsapp_contato
- email, horario_funcionamento
- politica_agendamento, politica_cancelamento
```

#### Medico
Cadastro de médicos:
```python
- nome_completo, crm, especialidades (ManyToMany)
- telefone, email, horario_atendimento
- dias_atendimento, tempo_consulta
```

#### Especialidade
Especialidades médicas oferecidas:
```python
- nome, descricao, tempo_medio_consulta
```

#### Exame
Exames disponíveis:
```python
- nome, descricao, tempo_estimado
- preparo_necessario, instrucoes_preparo
```

## 🔌 API Endpoints

### WhatsApp Webhook
```http
GET  /api/whatsapp/webhook/  # Verificação do webhook
POST /api/whatsapp/webhook/  # Recebimento de mensagens
```

### RAG Agent API (Django Admin)
```http
GET  /admin/  # Interface administrativa
GET  /admin/rag_agent/clinicainfo/
GET  /admin/rag_agent/medico/
GET  /admin/rag_agent/especialidade/
GET  /admin/rag_agent/exame/
```



## 📈 Próximos Passos e Roadmap

### 🎯 Melhorias Planejadas (Curto Prazo)

#### Interface e UX
1. **Dashboard Web para Secretaria** 💻
   - Visualização de agendamentos em tempo real
   - Gerenciamento de confirmações pendentes
   - Histórico de conversas
   - Estatísticas de atendimento

2. **Painel de Controle** 📊
   - Métricas de uso do chatbot
   - Taxa de conversão de agendamentos
   - Horários de maior demanda
   - Análise de satisfação

#### Funcionalidades
3. **Sistema de Notificações** 📧
   - Email automático de confirmação
   - SMS de lembretes (24h antes)
   - Notificações push para secretaria
   - Confirmações automáticas via WhatsApp

4. **Reagendamento e Cancelamento** 🔄
   - Permitir paciente reagendar via chatbot
   - Cancelamento com confirmação
   - Política de cancelamento automática
   - Lista de espera inteligente

5. **Multi-idioma** 🌍
   - Suporte a Inglês e Espanhol
   - Detecção automática de idioma
   - Respostas contextualizadas

### 🚀 Otimizações (Médio Prazo)

#### Performance e Escalabilidade
1. **Cache Redis** ⚡
   - Cache de sessões ativas
   - Cache de consultas RAG frequentes
   - Melhoria de performance em 50%

2. **PostgreSQL em Produção** 🗄️
   - Migração de SQLite para PostgreSQL
   - Melhor performance com queries complexas
   - Suporte a conexões concorrentes

3. **Containerização Docker** 🐳
   - Docker Compose para desenvolvimento
   - Imagens otimizadas
   - Deploy facilitado

4. **CI/CD Pipeline** 🔄
   - GitHub Actions para testes automatizados
   - Deploy automático em staging
   - Rollback automático em caso de erro

#### Inteligência Artificial
5. **Melhorias no Gemini** 🤖
   - Fine-tuning para contexto médico
   - Redução de consumo de tokens
   - Respostas mais precisas

6. **Análise de Sentimento** 😊
   - Detectar insatisfação do paciente
   - Priorização de casos urgentes
   - Handoff automático para humano

### 🔗 Integrações (Longo Prazo)

1. **CRM Médico** 📋
   - Sincronização com sistemas existentes
   - Prontuário eletrônico
   - Histórico completo do paciente

2. **Pagamentos Online** 💳
   - Integração com gateways de pagamento
   - Agendamento com pagamento antecipado
   - Parcelamento de consultas

3. **Telemedicina** 🎥
   - Videochamadas integradas
   - Compartilhamento de documentos
   - Prescrição digital

4. **Análise Preditiva** 📈
   - Previsão de demanda
   - Otimização de agenda
   - Sugestão de horários

### 🛡️ Segurança e Compliance

1. **LGPD / HIPAA Compliance** 🔐
   - Criptografia end-to-end
   - Anonimização de dados
   - Auditoria completa

2. **Backup Automatizado** 💾
   - Backup diário automático
   - Restore point recovery
   - Disaster recovery plan

3. **Monitoramento 24/7** 👁️
   - Alertas de sistema
   - Uptime monitoring
   - Log aggregation

## 🤝 Contribuição

Contribuições são bem-vindas! Siga estas etapas:

1. **Fork o projeto** no GitHub
2. **Crie uma branch** para sua feature
   ```bash
   git checkout -b feature/minha-nova-funcionalidade
   ```
3. **Commit suas mudanças** com mensagens descritivas
   ```bash
   git commit -m 'feat: Adiciona nova funcionalidade X'
   ```
4. **Push para a branch**
   ```bash
   git push origin feature/minha-nova-funcionalidade
   ```
5. **Abra um Pull Request** detalhado

### 📋 Padrões de Commit

Seguimos a convenção [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - Nova funcionalidade
- `fix:` - Correção de bug
- `docs:` - Alterações na documentação
- `style:` - Formatação, sem mudança de código
- `refactor:` - Refatoração de código
- `test:` - Adição ou correção de testes
- `chore:` - Tarefas de build, configurações, etc.


## 📚 Documentação Completa

A pasta `docs/` contém mais de 20 guias técnicos detalhados. Principais documentos:

### 🎯 Essenciais (Comece por aqui!)
- **[Configuração do .env](docs/02_setup_configuracao/CONFIGURACAO_ENV.md)** - ⚠️ **IMPORTANTE**: Configure suas variáveis de ambiente
- **[Guia de Desenvolvimento](docs/03_desenvolvimento/GUIA_DESENVOLVIMENTO.md)** - Como desenvolver no projeto
- **[Fluxo Completo do Projeto](docs/04_fluxos_processos/FLUXO_COMPLETO_PROJETO.md)** - Entenda o fluxo completo

### 🏗️ Arquitetura
- **[Arquitetura Atual](docs/01_arquitetura/ARQUITETURA_ATUAL.md)** - Visão geral da arquitetura
- **[Arquitetura Gemini Centralizada](docs/01_arquitetura/ARQUITETURA_GEMINI_CENTRALIZADA.md)** - Como o Gemini orquestra tudo

### 🔄 Fluxos e Lógica
- **[Lógica de Pré-agendamento](docs/04_fluxos_processos/LOGICA_PRE_AGENDAMENTO_ATUALIZADA.md)** - Detalhes do agendamento
- **[Fluxo Pré-agendamento Corrigido](docs/04_fluxos_processos/FLUXO_PRE_AGENDAMENTO_CORRIGIDO.md)** - Versão otimizada
- **[Análise de Estados de Conversação](docs/04_fluxos_processos/ANALISE_ESTADOS_CONVERSACAO.md)** - Estados e transições

### 🔌 Integrações
- **[Integração de APIs](docs/02_setup_configuracao/INTEGRACAO_APIS.md)** - Como as APIs se conectam
- **[Setup WhatsApp Webhook](docs/02_setup_configuracao/SETUP_WEBHOOK_WHATSAPP.md)** - Configure webhooks do WhatsApp
- **[WhatsApp Setup](docs/02_setup_configuracao/WHATSAPP_SETUP.md)** - Configuração completa do WhatsApp
- **[Google Calendar Setup](docs/02_setup_configuracao/GOOGLE_CALENDAR_SETUP.md)** - Configure o Google Calendar
- **[Setup Calendar Desenvolvimento](docs/02_setup_configuracao/SETUP_CALENDAR_DESENVOLVIMENTO.md)** - Calendar para dev
- **[Guia Secretaria Calendar](docs/02_setup_configuracao/GUIA_SECRETARIA_CALENDAR.md)** - Como a secretaria usa o Calendar

### ⚡ Otimizações e Performance
- **[Gestão de Memória e Otimização de Tokens](docs/05_otimizacoes/GESTAO_MEMORIA_TOKENS_ATUALIZADA.md)** - Reduza custos!
- **[Análise de Tokens Gemini](docs/05_otimizacoes/ANALISE_TOKENS_GEMINI.md)** - Entenda o consumo
- **[Monitoramento de Tokens](docs/05_otimizacoes/MONITORAMENTO_TOKENS_GEMINI.md)** - Como monitorar
- **[Refatoração Token Monitor](docs/05_otimizacoes/REFATORACAO_TOKEN_MONITOR.md)** - Melhorias implementadas
- **[Otimização Validação de Agendamento](docs/05_otimizacoes/OTIMIZACAO_VALIDACAO_AGENDAMENTO.md)** - Validações otimizadas

### 🐛 Correções e Debugging
- **[Correção de Erros nos Logs](docs/07_correcoes/CORRECAO_ERROS_LOGS.md)** - Problemas comuns
- **[Correção Salvamento no Banco](docs/07_correcoes/CORRECAO_SALVAMENTO_BANCO.md)** - Issues de persistência
- **[Validação de Formato de Mensagem](docs/04_fluxos_processos/VALIDACAO_FORMATO_MENSAGEM.md)** - Mensagens WhatsApp
- **[Plano Refatoração Entidades](docs/07_correcoes/PLANO_REFATORACAO_ENTIDADES.md)** - Correção da duplicação de responsabilidades entre `IntentDetector` e `EntityExtractor`


### 📖 Como Usar a Documentação

```bash
# Leia os documentos essenciais primeiro
1. docs/02_setup_configuracao/CONFIGURACAO_ENV.md
2. docs/01_arquitetura/ARQUITETURA_ATUAL.md
3. docs/04_fluxos_processos/FLUXO_COMPLETO_PROJETO.md

# Para desenvolvimento
4. docs/03_desenvolvimento/GUIA_DESENVOLVIMENTO.md
5. docs/02_setup_configuracao/SETUP_WEBHOOK_WHATSAPP.md
6. docs/02_setup_configuracao/GOOGLE_CALENDAR_SETUP.md

# Para otimização
7. docs/05_otimizacoes/GESTAO_MEMORIA_TOKENS_ATUALIZADA.md
```

## 📞 Suporte e Recursos

### 📚 Documentação
- **Guias Completos**: Consulte a pasta [`docs/`](docs/)
- **README Detalhado**: Este arquivo

### 🐛 Reportar Problemas
- **Issues no GitHub**: Para bugs e solicitações de funcionalidades
- **Discussions**: Para perguntas e discussões

### 💬 Comunidade
- Contribua com melhorias
- Compartilhe casos de uso
- Sugira novas funcionalidades

### 📧 Contato
Para questões relacionadas ao projeto, abra uma issue no GitHub.

---

## 🎯 Comandos Úteis de Desenvolvimento

### 🚀 Inicialização

```bash
# Ativar ambiente virtual
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Iniciar servidor de desenvolvimento
python manage.py runserver

# Criar superusuário
python manage.py createsuperuser

# Aplicar migrações
python manage.py migrate
```

### 🧪 Testes e Verificação

```bash
# Executar todos os testes
python manage.py test

# Verificar banco de dados
python scripts/verificar_banco_dados.py

# Testar persistência
python scripts/testar_persistencia_completa.py

# Verificar sessões ativas
python scripts/verificar_sessao_cache.py
```

### 🗄️ Gerenciamento de Dados

```bash
# Popular dados iniciais
python scripts/criar_dados_pneumosono.py

# Reset completo do banco
python scripts/quick_reset.py

# Acessar shell do Django
python manage.py shell

# Acessar shell do banco de dados
python manage.py dbshell
```

### 📊 Monitoramento

```bash
# Ver logs em tempo real (Linux/Mac)
tail -f logs/conversation.log

# Verificar migrações pendentes
python manage.py showmigrations

# Criar nova migração
python manage.py makemigrations

# Ver SQL de uma migração
python manage.py sqlmigrate api_gateway 0001
```

### 🌐 Desenvolvimento com Webhooks

```bash
# Iniciar ngrok (em outro terminal)
ngrok http 8000

# Copiar URL do ngrok e configurar no WhatsApp
# URL: https://SEU-NGROK-URL.ngrok-free.app/api/whatsapp/webhook/
```

---

## 📋 Status do Projeto

- **Versão**: 1.0.0
- **Status**: ✅ Desenvolvimento Ativo
- **Última Atualização**: 17 de Outubro de 2025
- **Python**: 3.8+ (recomendado 3.10+)
- **Django**: 5.2.6
- **Gemini AI**: 2.0 Flash
- **Arquitetura**: Multi-Componentes com Sistema RAG e Gemini AI distribuído

---

## ❓ Perguntas Frequentes (FAQ)

### Configuração e Setup

<details>
<summary><b>Por que as variáveis estão no .env e também no settings.py?</b></summary>

Isso é uma **melhor prática de programação** conhecida como **12-Factor App**:

1. **`.env`** - Contém os **valores reais** (não vai para git)
2. **`settings.py`** - **Carrega** as variáveis do `.env` (vai para git sem valores sensíveis)

```python
# settings.py (vai para git)
GEMINI_API_KEY = config('GEMINI_API_KEY', default='')

# .env (NÃO vai para git)
GEMINI_API_KEY=AIzaSy...valor_real...
```

**Vantagens:**
- ✅ Código sem credenciais (seguro para git)
- ✅ Fácil trocar entre dev/produção
- ✅ Centralizado em `settings.py`

📖 **Leia mais:** [`docs/02_setup_configuracao/CONFIGURACAO_ENV.md`](docs/02_setup_configuracao/CONFIGURACAO_ENV.md)
</details>

<details>
<summary><b>O que é DOCTOR_EVENT_PATTERNS e preciso configurá-lo?</b></summary>

**Não precisa configurar!** O sistema gera automaticamente.

`DOCTOR_EVENT_PATTERNS` identifica eventos de médicos no Google Calendar compartilhado:

- ✅ **Automático**: Busca médicos do banco e gera padrões
- ✅ **Dinâmico**: Adicionar médico no banco = funciona automaticamente
- ℹ️ **Opcional**: Use apenas para casos especiais (apelidos, abreviações)

**Deixe vazio (padrão):**
```python
DOCTOR_EVENT_PATTERNS = {}  # Sistema gera automaticamente
```
</details>

<details>
<summary><b>Como obtenho a GEMINI_API_KEY?</b></summary>

1. Acesse: https://aistudio.google.com/app/apikey
2. Faça login com Google
3. Clique em "Create API Key"
4. Copie e cole no `.env`

```bash
GEMINI_API_KEY=AIzaSy...sua_chave_aqui
```

📖 **Guia completo:** [`docs/02_setup_configuracao/CONFIGURACAO_ENV.md`](docs/02_setup_configuracao/CONFIGURACAO_ENV.md)
</details>

<details>
<summary><b>O calendário precisa ser separado por médico?</b></summary>

**Não!** O sistema suporta **um único calendário compartilhado**:

- ✅ Um calendário para toda a clínica
- ✅ Sistema identifica eventos de cada médico automaticamente
- ✅ Baseado em padrões do nome no título do evento

**Formato de eventos:**
- "Dr. João - Consulta" ✅
- "Consulta - Dr Gustavo" ✅
- "Cardiologia - João Carvalho" ✅
</details>

### Desenvolvimento

<details>
<summary><b>Como testo o chatbot localmente?</b></summary>

```bash
# 1. Inicie o servidor
python manage.py runserver

# 2. Em outro terminal, inicie o ngrok
ngrok http 8000

# 3. Configure webhook no WhatsApp com URL do ngrok
# https://SEU-NGROK.ngrok-free.app/api/whatsapp/webhook/

# 4. Envie mensagem no WhatsApp
```

📖 **Guia completo:** [`docs/02_setup_configuracao/SETUP_WEBHOOK_WHATSAPP.md`](docs/02_setup_configuracao/SETUP_WEBHOOK_WHATSAPP.md)
</details>

<details>
<summary><b>Como verifico se meu banco de dados está correto?</b></summary>

```bash
# Script de verificação completa
python scripts/verificar_banco_dados.py

# Verificar sessões ativas
python scripts/verificar_sessao_cache.py
```
</details>

### Produção

<details>
<summary><b>Como faço deploy em produção?</b></summary>

**Checklist de Produção:**

1. ✅ Configure variáveis de ambiente no servidor (não use `.env`)
2. ✅ Use PostgreSQL ao invés de SQLite
3. ✅ Defina `DEBUG=False`
4. ✅ Configure `ALLOWED_HOSTS`
5. ✅ Use HTTPS
6. ✅ Configure backup automático
7. ✅ Monitore uso de tokens Gemini

📖 **Documentação:** [`docs/04_fluxos_processos/FLUXO_COMPLETO_PROJETO.md`](docs/04_fluxos_processos/FLUXO_COMPLETO_PROJETO.md)
</details>

---

## 🏆 Destaques Técnicos

- 🤖 **IA Conversacional Avançada** com Gemini 2.0 Flash
- 💾 **Persistência Completa** de sessões e histórico
- 📚 **Sistema RAG** para contextualização inteligente
- 🔄 **Integração Multi-plataforma** (WhatsApp + Google Calendar)
- 📊 **Monitoramento de Tokens** para controle de custos
- 🔐 **Segurança** com variáveis de ambiente
- 🧪 **Testes Automatizados** e scripts de verificação
- 📖 **Documentação Completa** com 20+ guias técnicos

---

**Desenvolvido com ❤️ para Clínicas Médicas**

*Sistema de Chatbot Inteligente para Agendamento Médico*
