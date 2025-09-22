# 🤖 Chatbot Clínica Médica - Sistema Inteligente de Agendamento

## 📋 Visão Geral

Sistema de chatbot inteligente desenvolvido em Django REST Framework para automatizar o agendamento de consultas médicas na Clínica PneumoSono. O sistema utiliza Google Gemini AI como motor principal de conversação, integração com WhatsApp Business API e Google Calendar para gerenciamento de agendamentos.

## 🏗️ Arquitetura Atual

### Estrutura do Projeto

```
chatbot_ClinicaMedica/
├── api_gateway/                 # Gateway principal da API
│   ├── models.py                # Modelos de dados (sessões, mensagens, agendamentos)
│   ├── services/                # Serviços de negócio
│   │   ├── conversation_service.py      # Gerenciamento de conversas
│   │   ├── gemini_chatbot_service.py    # Motor principal Gemini AI
│   │   ├── whatsapp_service.py          # Integração WhatsApp
│   │   ├── google_calendar_service.py   # Integração Google Calendar
│   │   ├── handoff_service.py           # Transferência para secretaria
│   │   ├── rag_service.py              # Sistema RAG (Retrieval Augmented Generation)
│   │   └── smart_scheduling_service.py  # Agendamento inteligente
│   ├── views.py                # Endpoints da API
│   └── urls.py                 # Roteamento
├── rag_agent/                  # Agente de conhecimento
│   ├── models.py               # Modelos de dados da clínica
│   └── knowledge_base/         # Base de conhecimento
├── core/                       # Configurações Django
├── scripts/                    # Scripts utilitários
└── tests/                      # Testes automatizados
```

### Componentes Principais

#### 1. **Gemini Chatbot Service** (Protagonista Principal)
- **Arquivo**: `api_gateway/services/gemini_chatbot_service.py`
- **Responsabilidades**:
  - Gerenciamento completo do fluxo de conversação
  - Análise de intenções e extração de entidades
  - Geração de respostas contextuais
  - Coordenação com outros serviços

#### 2. **Conversation Service**
- **Arquivo**: `api_gateway/services/conversation_service.py`
- **Responsabilidades**:
  - Persistência de sessões de conversa
  - Gerenciamento de estado do fluxo
  - Cache de dados RAG
  - Histórico de mensagens

#### 3. **RAG Agent**
- **Arquivo**: `rag_agent/models.py`
- **Responsabilidades**:
  - Base de conhecimento da clínica
  - Informações sobre médicos, especialidades, exames
  - Dados de contato e políticas

#### 4. **WhatsApp Service**
- **Arquivo**: `api_gateway/services/whatsapp_service.py`
- **Responsabilidades**:
  - Integração com WhatsApp Business API
  - Envio e recebimento de mensagens
  - Processamento de webhooks

#### 5. **Google Calendar Service**
- **Arquivo**: `api_gateway/services/google_calendar_service.py`
- **Responsabilidades**:
  - Consulta de disponibilidade
  - Criação de eventos
  - Sincronização de agendamentos

## 🚀 Funcionalidades

### ✅ Implementadas

1. **Conversação Inteligente**
   - Análise de intenções com Gemini AI
   - Extração automática de entidades (nome, telefone, especialidade)
   - Confirmação de dados do paciente
   - Fluxo conversacional natural

2. **Sistema de Agendamento**
   - Coleta inteligente de informações do paciente
   - Seleção de médico e especialidade
   - Consulta de disponibilidade em tempo real
   - Geração de links de confirmação

3. **Integração WhatsApp**
   - Recebimento de mensagens via webhook
   - Envio de respostas automáticas
   - Suporte a mídias (texto, imagens, áudio)

4. **Persistência de Dados**
   - Sessões de conversa persistentes
   - Histórico completo de mensagens
   - Cache inteligente de dados RAG
   - Estados de fluxo preservados

5. **Sistema RAG**
   - Base de conhecimento da clínica
   - Informações sobre médicos e especialidades
   - Políticas de agendamento
   - Dados de contato e localização

### 🔄 Fluxo de Agendamento

1. **Recepção da Mensagem**
   - WhatsApp recebe mensagem do paciente
   - Webhook envia para Django
   - Gemini analisa intenção e contexto

2. **Coleta de Informações**
   - Extração automática de dados (nome, telefone)
   - Confirmação de informações
   - Seleção de especialidade desejada

3. **Seleção de Médico**
   - Consulta base de dados de médicos
   - Filtragem por especialidade
   - Apresentação de opções ao paciente

4. **Agendamento**
   - Consulta disponibilidade no Google Calendar
   - Apresentação de horários disponíveis
   - Confirmação de agendamento

5. **Finalização**
   - Geração de link de confirmação
   - Transferência para secretaria (handoff)
   - Notificação de conclusão

## 🛠️ Tecnologias Utilizadas

### Backend
- **Django 5.2.6** - Framework web
- **Django REST Framework 3.16.1** - API REST
- **SQLite** - Banco de dados (desenvolvimento)

### IA e Integração
- **Google Gemini AI 2.0 Flash** - Motor de conversação
- **Google Calendar API** - Gerenciamento de agendamentos
- **WhatsApp Business API** - Interface de mensagens

### Dependências Principais
```
google-generativeai==0.8.3
google-api-python-client==2.181.0
djangorestframework==3.16.1
python-decouple==3.8
```

## 📦 Instalação e Configuração

### 1. Pré-requisitos
- Python 3.8+
- Conta Google Cloud Platform
- WhatsApp Business Account
- Ngrok (para desenvolvimento)

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

### 3. Configuração de Variáveis

Crie arquivo `.env` na raiz do projeto:

```env
# Django
SECRET_KEY=sua-secret-key-aqui
DEBUG=True

# Gemini AI
GEMINI_API_KEY=sua-gemini-api-key
GEMINI_ENABLED=True
GEMINI_MODEL=gemini-2.0-flash

# WhatsApp
WHATSAPP_TOKEN=seu-whatsapp-token
WHATSAPP_VERIFY_TOKEN=seu-verify-token
WHATSAPP_PHONE_NUMBER_ID=seu-phone-number-id

# Google Calendar
GOOGLE_CALENDAR_CREDENTIALS_FILE=service-account-key.json
GOOGLE_CALENDAR_ID=id-do-calendario-principal
```

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

1. Crie projeto no Google Cloud Console
2. Ative Google Calendar API
3. Crie service account e baixe JSON
4. Renomeie para `service-account-key.json`
5. Configure calendário principal no admin Django

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

### Scripts Disponíveis
- `criar_dados_pneumosono.py` - Popula dados iniciais
- `quick_reset.py` - Reset rápido do banco
- `testar_persistencia_completa.py` - Testa persistência
- `verificar_banco_dados.py` - Verifica estado do banco

## 📈 Próximos Passos

### Melhorias Planejadas
1. **Interface Web** - Dashboard para secretaria
2. **Notificações** - SMS e email automáticos
3. **Relatórios** - Analytics de agendamentos
4. **Multi-idioma** - Suporte a outros idiomas
5. **Integração CRM** - Sincronização com sistemas existentes

### Otimizações
1. **Cache Redis** - Melhor performance
2. **PostgreSQL** - Banco de produção
3. **Docker** - Containerização
4. **CI/CD** - Deploy automatizado

## 🤝 Contribuição

1. Fork o projeto
2. Crie branch para feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para branch (`git push origin feature/nova-funcionalidade`)
5. Abra Pull Request

## 📄 Licença

Este projeto está sob licença MIT. Veja o arquivo `LICENSE` para detalhes.

## 📞 Suporte

Para dúvidas ou suporte:
- **Email**: suporte@clinica.com
- **WhatsApp**: +55 (11) 99999-9999
- **Documentação**: Consulte os arquivos `.md` específicos

---

**Desenvolvido com ❤️ para a Clínica PneumoSono**
