# 🛠️ Guia de Desenvolvimento - Chatbot Clínica Médica

## 🚀 Configuração do Ambiente de Desenvolvimento

### 1. **Pré-requisitos**

#### **Software Necessário**
- Python 3.8+
- Git
- Ngrok (para webhook local)
- Conta Google Cloud Platform
- WhatsApp Business Account

#### **Contas e APIs**
- **Google Cloud Platform**: Para Gemini AI e Calendar API
- **WhatsApp Business**: Para integração de mensagens
- **Ngrok**: Para túnel local (desenvolvimento)

### 2. **Configuração Inicial**

#### **Clone e Setup**
```bash
# Clone o repositório
git clone <repository-url>
cd chatbot_ClinicaMedica

# Crie ambiente virtual
python -m venv venv

# Ative ambiente virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instale dependências
pip install -r requirements.txt
```

#### **Configuração de Variáveis**
Crie arquivo `.env` na raiz:

```env
# Django
SECRET_KEY=sua-secret-key-aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,.ngrok-free.app

# Gemini AI
GEMINI_API_KEY=sua-gemini-api-key
GEMINI_ENABLED=True
GEMINI_MODEL=gemini-2.0-flash

# WhatsApp Business
WHATSAPP_TOKEN=seu-whatsapp-token
WHATSAPP_VERIFY_TOKEN=seu-verify-token
WHATSAPP_PHONE_NUMBER_ID=seu-phone-number-id

# Google Calendar
GOOGLE_CALENDAR_CREDENTIALS_FILE=service-account-key.json
GOOGLE_CALENDAR_ID=id-do-calendario-principal
```

### 3. **Configuração do Banco de Dados**

#### **Migrações**
```bash
# Execute migrações
python manage.py migrate

# Crie superusuário
python manage.py createsuperuser

# Popule dados iniciais
python scripts/criar_dados_pneumosono.py
```

#### **Verificação**
```bash
# Verifique o banco
python scripts/verificar_banco_dados.py

# Teste persistência
python scripts/testar_persistencia_completa.py
```

## 🔧 Desenvolvimento

### **Estrutura de Desenvolvimento**

#### **1. Serviços Principais**
```python
# api_gateway/services/
├── gemini_chatbot_service.py    # Motor principal
├── conversation_service.py       # Gerenciamento de conversas
├── whatsapp_service.py          # Integração WhatsApp
├── google_calendar_service.py   # Integração Calendar
├── handoff_service.py           # Transferência secretaria
├── rag_service.py              # Sistema RAG
└── smart_scheduling_service.py  # Agendamento inteligente
```

#### **2. Modelos de Dados**
```python
# api_gateway/models.py
- ConversationSession    # Sessões de conversa
- ConversationMessage    # Mensagens
- AppointmentRequest     # Solicitações


# rag_agent/models.py
- ClinicaInfo           # Info da clínica
- Medico                # Médicos
- Especialidade         # Especialidades
- Convenio              # Convênios
- HorarioTrabalho       # Horários
- Exame                 # Exames
```

### **Fluxo de Desenvolvimento**

#### **1. Adicionar Nova Funcionalidade**

```python
# 1. Crie o serviço
# api_gateway/services/novo_service.py
class NovoService:
    def __init__(self):
        pass
    
    def processar(self, dados):
        # Lógica aqui
        pass

# 2. Integre com Gemini
# api_gateway/services/gemini_chatbot_service.py
def process_message(self, message, phone_number):
    # Adicione nova funcionalidade
    if intent == 'nova_funcionalidade':
        return self.novo_service.processar(dados)
```

#### **2. Modificar Fluxo de Conversa**

```python
# api_gateway/services/conversation_service.py
def update_session_state(self, session, new_state, **kwargs):
    """
    Atualiza estado da sessão
    """
    session.current_state = new_state
    # Adicione lógica específica
    session.save()
```

#### **3. Adicionar Novo Modelo**

```python
# api_gateway/models.py
class NovoModelo(models.Model):
    campo1 = models.CharField(max_length=100)
    campo2 = models.TextField()
    
    class Meta:
        verbose_name = 'Novo Modelo'
        verbose_name_plural = 'Novos Modelos'
```

```bash
# Gere migração
python manage.py makemigrations
python manage.py migrate
```

### **Testes**

#### **Estrutura de Testes**
```
tests/
├── api_gateway/
│   ├── test_webhook_integration.py
│   ├── test_handoff.py
│   ├── test_calendar.py
│   └── test_chatbot_improvements.py
└── rag_agent/
    └── test_banco_medicos.py
```

#### **Executar Testes**
```bash
# Todos os testes
python manage.py test

# Teste específico
python manage.py test tests.api_gateway.test_handoff

# Com verbose
python manage.py test --verbosity=2
```

#### **Criar Novo Teste**
```python
# tests/api_gateway/test_nova_funcionalidade.py
from django.test import TestCase
from api_gateway.services.novo_service import NovoService

class TestNovaFuncionalidade(TestCase):
    def setUp(self):
        self.service = NovoService()
    
    def test_processar_dados(self):
        resultado = self.service.processar({'teste': 'dados'})
        self.assertIsNotNone(resultado)
```

### **Scripts de Desenvolvimento**

#### **Scripts Disponíveis**
```bash
# População de dados
python scripts/criar_dados_pneumosono.py

# Reset rápido
python scripts/quick_reset.py

# Teste de persistência
python scripts/testar_persistencia_completa.py

# Verificação de banco
python scripts/verificar_banco_dados.py

# Verificação de sessão
python scripts/verificar_sessao_cache.py
```

#### **Criar Novo Script**
```python
# scripts/novo_script.py
import os
import django

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from api_gateway.models import ConversationSession

def main():
    # Lógica do script
    sessions = ConversationSession.objects.all()
    print(f"Total de sessões: {sessions.count()}")

if __name__ == '__main__':
    main()
```

## 🔍 Debugging

### **Logs e Monitoramento**

#### **Configuração de Logs**
```python
# core/settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
        },
    },
    'loggers': {
        'conversation': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

#### **Logs Específicos**
```python
# Em qualquer serviço
import logging
logger = logging.getLogger('conversation')

def processar_mensagem(self, mensagem):
    logger.info(f"Processando mensagem: {mensagem}")
    # Lógica aqui
    logger.debug(f"Resultado: {resultado}")
```

### **Debugging de Conversas**

#### **Verificar Sessão Ativa**
```bash
python scripts/verificar_sessao_cache.py
```

#### **Verificar Banco de Dados**
```bash
python scripts/verificar_banco_dados.py
```

#### **Testar Persistência**
```bash
python scripts/testar_persistencia_completa.py
```

### **Debugging de Integrações**

#### **WhatsApp Webhook**
```python
# Adicione logs no webhook
def whatsapp_webhook(request):
    logger.info(f"Webhook recebido: {request.body}")
    # Processamento
    logger.info(f"Resposta enviada: {response}")
```

#### **Google Calendar**
```python
# Teste de disponibilidade
from api_gateway.services.google_calendar_service import GoogleCalendarService

service = GoogleCalendarService()
disponibilidade = service.get_availability('2024-01-15')
print(f"Disponibilidade: {disponibilidade}")
```

## 🚀 Deploy

### **Configuração de Produção**

#### **Variáveis de Ambiente**
```env
# Produção
DEBUG=False
SECRET_KEY=chave-super-secreta
ALLOWED_HOSTS=seu-dominio.com

# Banco de produção
DATABASE_URL=postgresql://user:pass@host:port/db

# APIs
GEMINI_API_KEY=chave-producao
WHATSAPP_TOKEN=token-producao
```

#### **Configuração de Servidor**
```python
# core/settings.py
if not DEBUG:
    # Configurações de produção
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'chatbot_prod',
            'USER': 'postgres',
            'PASSWORD': 'senha',
            'HOST': 'localhost',
            'PORT': '5432',
        }
    }
```

### **Docker (Planejado)**

#### **Dockerfile**
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

#### **docker-compose.yml**
```yaml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEBUG=False
    volumes:
      - .:/app
```

## 📊 Monitoramento

### **Métricas Importantes**
- **Tempo de resposta** do Gemini AI
- **Taxa de sucesso** de agendamentos
- **Número de sessões** ativas
- **Erros** de integração

### **Alertas (Planejado)**
- **Falha** no webhook WhatsApp
- **Erro** na API Gemini
- **Problema** no Google Calendar
- **Alta** latência de resposta

## 🔧 Manutenção

### **Backup**
```bash
# Backup do banco
python manage.py dumpdata > backup.json

# Restore
python manage.py loaddata backup.json
```

### **Limpeza**
```bash
# Limpar sessões antigas
python scripts/limpar_sessoes_antigas.py

# Limpar cache
python manage.py clear_cache
```

### **Atualizações**
```bash
# Atualizar dependências
pip install -r requirements.txt --upgrade

# Executar migrações
python manage.py migrate

# Coletar estáticos
python manage.py collectstatic
```

---

**Este guia fornece todas as informações necessárias para desenvolvimento, debugging e manutenção do sistema.**
