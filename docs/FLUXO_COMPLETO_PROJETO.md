# 📋 Fluxo Completo do Projeto - Chatbot Clínica Médica

## 🎯 Visão Geral

Este documento descreve o fluxo completo do sistema de chatbot para clínica médica, desde a recepção de mensagens do WhatsApp até a geração de handoffs para a secretária.

## 🏗️ Arquitetura do Sistema

### Componentes Principais

1. **WhatsApp Business API** - Interface de comunicação
2. **Django Server** - Backend principal
3. **Google Gemini AI** - Motor de IA centralizado
4. **Google Calendar** - Sistema de agendamento
5. **Banco de Dados** - Persistência de dados
6. **Cache** - Otimização de performance

## 🔄 Fluxo Detalhado

### 1. **Recepção de Mensagem**

```
📱 Paciente envia mensagem no WhatsApp
    ↓
🌐 WhatsApp Business API recebe mensagem
    ↓
🔗 Webhook envia para Django Server
    ↓
📨 Django processa webhook em views.py
```

**Código responsável:**
- `api_gateway/views.py` - `whatsapp_webhook()`
- `api_gateway/views.py` - `process_message()`

### 2. **Processamento com Gemini AI**

```
🤖 Gemini Chatbot Service recebe mensagem
    ↓
🧠 Análise de intenção e extração de entidades
    ↓
📊 Consulta dados da clínica via RAG Service
    ↓
💾 Atualiza sessão de conversa
    ↓
🎯 Gera resposta contextualizada
```

**Código responsável:**
- `api_gateway/services/gemini_chatbot_service.py` - `process_message()`
- `api_gateway/services/rag_service.py` - Dados da clínica
- `api_gateway/services/conversation_service.py` - Persistência

### 3. **Análise de Intenção**

O Gemini AI identifica automaticamente:

#### **Intenções Suportadas:**
- `saudacao` - Cumprimentos e início de conversa
- `buscar_info` - Informações sobre clínica, endereço, telefone
- `agendar_consulta` - Processo de agendamento
- `confirmar_agendamento` - Confirmação de dados
- `buscar_medico` - Informações sobre médicos
- `buscar_exame` - Informações sobre exames
- `buscar_horarios` - Horários disponíveis
- `cancelar_agendamento` - Cancelamento
- `despedida` - Encerramento de conversa
- `duvida` - Quando não entende a mensagem

#### **Entidades Extraídas:**
- `nome_paciente` - Nome completo do paciente
- `medico` - Nome do médico mencionado
- `especialidade` - Especialidade médica
- `data` - Data da consulta
- `horario` - Horário da consulta
- `exame` - Nome do exame mencionado

### 4. **Estados da Conversa**

```
idle → collecting_patient_info → selecting_doctor → choosing_schedule → confirming
```

#### **Estados Detalhados:**
- `idle` - Estado inicial
- `collecting_patient_info` - Coletando dados do paciente
- `collecting_info` - Coletando informações
- `confirming_name` - Confirmando nome do paciente
- `selecting_doctor` - Selecionando médico
- `choosing_schedule` - Escolhendo horário
- `confirming` - Confirmando dados finais
- `fornecendo_info` - Fornecendo informações solicitadas

### 5. **Fluxo de Agendamento**

#### **Etapa 1: Coleta do Nome**
```
👤 Paciente: "Olá, gostaria de agendar uma consulta"
🤖 Bot: "Olá! Como posso ajudá-lo? Primeiro, preciso do seu nome completo."
👤 Paciente: "Meu nome é João Silva"
🤖 Bot: "Perfeito, João! Com qual médico gostaria de agendar?"
```

#### **Etapa 2: Seleção do Médico**
```
👤 Paciente: "Com Dr. João Carvalho"
🤖 Bot: "Ótimo! Dr. João Carvalho atende Cardiologia. Qual data seria melhor?"
```

#### **Etapa 3: Escolha de Data/Horário**
```
👤 Paciente: "Segunda-feira às 14h"
🤖 Bot: "Perfeito! Vamos confirmar: João Silva, Dr. João Carvalho, Segunda-feira às 14h. Está correto?"
```

#### **Etapa 4: Confirmação e Handoff**
```
👤 Paciente: "Sim, está correto"
🤖 Bot: "✅ Perfeito! Vamos confirmar seu pré-agendamento:

📋 RESUMO:
👤 Paciente: João Silva
👨‍⚕️ Médico: Dr. João Carvalho
📅 Data: Segunda-feira
🕐 Horário: 14h

🔄 Para CONFIRMAR definitivamente:
👩‍💼 Nossa secretária validará a disponibilidade e confirmará seu agendamento.

📞 Clique no link abaixo para falar diretamente com nossa equipe:
[LINK DE HANDOFF]"
```

### 6. **Geração de Handoff**

Quando o paciente confirma o agendamento:

```
🔗 Handoff Service gera link personalizado
    ↓
📝 Cria mensagem formatada com dados do paciente
    ↓
📱 Link direciona para WhatsApp da secretária
    ↓
👩‍💼 Secretária recebe informações completas
```

**Código responsável:**
- `api_gateway/services/handoff_service.py` - `generate_appointment_handoff_link()`

### 7. **Consulta de Horários**

Para solicitações de horários:

```
📅 Smart Scheduling Service analisa solicitação
    ↓
🔍 Valida médico no banco de dados
    ↓
📊 Consulta Google Calendar
    ↓
📋 Retorna horários disponíveis
```

**Código responsável:**
- `api_gateway/services/smart_scheduling_service.py` - `analyze_scheduling_request()`

## 🗄️ Persistência de Dados

### **Modelos Principais**

#### **ConversationSession**
```python
class ConversationSession(models.Model):
    phone_number = models.CharField(max_length=20, unique=True)
    patient_name = models.CharField(max_length=100, blank=True, null=True)
    current_state = models.CharField(max_length=50, default='idle')
    selected_doctor = models.CharField(max_length=100, blank=True, null=True)
    preferred_date = models.DateField(blank=True, null=True)
    preferred_time = models.TimeField(blank=True, null=True)
    # ... outros campos
```

#### **ConversationMessage**
```python
class ConversationMessage(models.Model):
    session = models.ForeignKey(ConversationSession, on_delete=models.CASCADE)
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES)
    content = models.TextField()
    intent = models.CharField(max_length=50, blank=True, null=True)
    confidence = models.FloatField(blank=True, null=True)
    entities = models.JSONField(default=dict, blank=True)
    # ... outros campos
```

### **Dados da Clínica (RAG Agent)**

#### **ClinicaInfo**
- Nome da clínica
- Endereço e contatos
- Horário de funcionamento
- Política de agendamento

#### **Medico**
- Nome e CRM
- Especialidades
- Convênios aceitos
- Preço particular
- Horários de trabalho

#### **Especialidade**
- Nome da especialidade
- Descrição
- Status ativo

#### **Convenio**
- Nome do convênio
- Descrição

#### **Exame**
- Nome do exame
- Descrição e preparação
- Preço e duração

## 🔧 Configuração e Deploy

### **Variáveis de Ambiente**

Todas as configurações sensíveis são gerenciadas pelo arquivo `.env` na raiz do projeto.

**Importante:** 
- Nunca exponha valores reais de API keys ou tokens na documentação
- Use o arquivo `.env.example` como referência
- O arquivo `.env` deve estar no `.gitignore`

```bash
# Copiar o arquivo de exemplo
cp .env.example .env

# Editar com suas credenciais reais
nano .env

# Variáveis principais configuradas no .env:
# - GEMINI_API_KEY
# - WHATSAPP_ACCESS_TOKEN
# - WHATSAPP_PHONE_NUMBER_ID
# - WHATSAPP_VERIFY_TOKEN
# - WHATSAPP_API_URL
# - GOOGLE_CALENDAR_ENABLED
# - GOOGLE_SERVICE_ACCOUNT_FILE
# - CLINIC_DOMAIN
# - CLINIC_CALENDAR_ID
# - CLINIC_WHATSAPP_NUMBER
```

### **Django Settings**

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rag_agent',
    'api_gateway',
]

# Configurações de cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}
```

## 📊 Monitoramento e Logs

### **Logs Estruturados**

O sistema gera logs detalhados para monitoramento:

```
🤖 [AGENDAR_CONSULTA] State: collecting_patient_info | Conf: 0.95 | Agent: gemini
🔍 Entidades extraídas: {'nome_paciente': 'João Silva', 'medico': 'Dr. João'}
✅ Nome atualizado: João Silva
✅ Médico atualizado: Dr. João
📋 Status das informações: {'nome': True, 'medico': True, 'data': False, 'horario': False}
💾 Sessão sincronizada com banco - ID: 123, Nome: João Silva, Data: None
```

### **Monitoramento de Tokens**

```python
# Estatísticas de uso
stats = token_monitor.get_token_usage_stats()
print(f"Tokens usados hoje: {stats['tokens_used_today']}")
print(f"Limite diário: {stats['daily_limit']}")
print(f"Modo econômico: {stats['economy_mode_active']}")
```

## 🧪 Endpoints de Teste

### **Teste de Conexão**
```bash
GET /test-gemini-connection/
```

### **Teste de Processamento**
```bash
POST /test-chatbot-service/
{
    "phone_number": "5511999999999",
    "message": "Olá, gostaria de agendar uma consulta"
}
```

### **Teste de Análise de Intenção**
```bash
POST /test-intent-analysis/
{
    "message": "Quais médicos vocês têm?",
    "phone_number": "5511999999999"
}
```

### **Teste de Extração de Entidades**
```bash
POST /test-entity-extraction/
{
    "message": "Meu nome é João Silva, quero agendar com Dr. João Carvalho para segunda-feira às 14h",
    "phone_number": "5511999999999"
}
```

### **Teste de Handoff**
```bash
POST /test-handoff-generation/
{
    "patient_name": "João Silva",
    "doctor_name": "Dr. João Carvalho",
    "date": "15/09/2025",
    "time": "14:30"
}
```

### **Verificação de Dados**
```bash
GET /check-stored-data/?phone_number=5511999999999
```

### **Estatísticas de Tokens**
```bash
GET /token-usage-stats/
```

## 🚀 Fluxo de Deploy

### **1. Preparação do Ambiente**

```bash
# Clonar repositório
git clone <repository_url>
cd chatbot_ClinicaMedica

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
# IMPORTANTE: Crie um arquivo .env na raiz do projeto com todas as variáveis necessárias
# Referência: Use o .env.example como template (se disponível)
# O arquivo .env NÃO deve ser commitado no git
```

### **2. Configuração do Banco**

```bash
# Aplicar migrações
python manage.py migrate

# Criar superusuário
python manage.py createsuperuser

# Carregar dados iniciais
python scripts/criar_dados_pneumosono.py
```

### **3. Configuração de Serviços**

```bash
# Configurar Google Calendar
python scripts/setup_calendar_dev.py

# Testar conexões
python manage.py runserver
# Acessar: http://localhost:8000/test-gemini-connection/
```

### **4. Configuração do WhatsApp**

```bash
# Configurar webhook
# URL: https://seu-dominio.com/webhook/
# Token: seu_verify_token
```

## 🔍 Troubleshooting

### **Problemas Comuns**

#### **1. Gemini não responde**
```bash
# Verificar API key
GET /test-gemini-connection/

# Verificar logs
tail -f logs/gemini.log
```

#### **2. WhatsApp não envia mensagens**
```bash
# Verificar se variáveis estão configuradas
python manage.py shell
>>> from django.conf import settings
>>> print(settings.WHATSAPP_ACCESS_TOKEN is not None)
>>> print(settings.WHATSAPP_PHONE_NUMBER_ID is not None)

# Testar envio
POST /send-test-message/
```

#### **3. Banco de dados não persiste**
```bash
# Verificar migrações
python manage.py showmigrations

# Verificar dados
GET /check-stored-data/
```

#### **4. Tokens esgotados**
```bash
# Verificar estatísticas
GET /token-usage-stats/

# Resetar contador (cuidado!)
POST /reset-token-usage/
```

## 📈 Métricas de Performance

### **Tempos de Resposta**
- **Análise de intenção**: < 500ms
- **Geração de resposta**: < 1s
- **Consulta de horários**: < 2s
- **Geração de handoff**: < 200ms

### **Limites do Sistema**
- **Tokens diários**: 1,000,000 (configurável)
- **Sessões ativas**: 1,000 (cache)
- **Mensagens por minuto**: 100+
- **Disponibilidade**: 99.9%

## 🔐 Segurança

### **Autenticação**
- **WhatsApp Verify Token** para webhooks
- **Google Service Account** para Calendar API
- **Gemini API Key** para IA

### **Validação**
- **Sanitização** de inputs
- **Validação** de dados
- **Rate limiting** (planejado)

### **Gestão de Configurações Sensíveis**

#### **Arquivo .env**
```bash
# ✅ FAZER
- Manter .env fora do controle de versão (.gitignore)
- Usar valores diferentes para dev/produção
- Rotacionar chaves periodicamente
- Criar .env.example com valores de exemplo

# ❌ NUNCA FAZER
- Commitar arquivo .env com valores reais
- Expor API keys em código ou documentação
- Usar mesmas credenciais em dev e produção
- Compartilhar arquivo .env por email/chat
```

#### **Variáveis Configuradas no .env**
Todas as credenciais sensíveis estão configuradas em:
- `WHATSAPP_VERIFY_TOKEN`
- `WHATSAPP_ACCESS_TOKEN`
- `WHATSAPP_PHONE_NUMBER_ID`
- `GEMINI_API_KEY`
- `WHATSAPP_API_URL`
- `GOOGLE_CALENDAR_ENABLED`
- `GOOGLE_SERVICE_ACCOUNT_FILE`
- `CLINIC_DOMAIN`
- `CLINIC_CALENDAR_ID`
- `CLINIC_WHATSAPP_NUMBER`

### **Dados Sensíveis**
- **Nomes de pacientes** armazenados com segurança
- **Números de telefone** mascarados em logs
- **Tokens e API Keys** carregados via .env
- **Mensagens** persistidas apenas necessárias

## 📚 Próximos Passos

### **Melhorias Planejadas**
1. **Processamento assíncrono** para melhor performance
2. **Rate limiting** para proteção contra spam
3. **Métricas avançadas** com Grafana
4. **Backup automático** de dados
5. **Integração com CRM** da clínica

### **Expansões Futuras**
1. **Múltiplas clínicas** em uma instância
2. **Agendamento automático** via Google Calendar
3. **Notificações push** para pacientes
4. **Relatórios analíticos** de conversas
5. **Integração com sistemas de pagamento**

---

**Esta documentação representa o estado atual do sistema após a refatoração completa para centralização no Gemini AI.**
