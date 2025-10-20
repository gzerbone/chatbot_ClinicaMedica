# 🔧 Configuração do Arquivo .env - Atualizada 09/10 (mais recente)

## 📋 Visão Geral

Este documento explica como configurar o arquivo `.env` que contém todas as variáveis de ambiente e credenciais necessárias para o funcionamento do chatbot.

## ⚠️ IMPORTANTE - Segurança

### ✅ FAZER
- Manter `.env` fora do controle de versão (já está no `.gitignore`)
- Usar valores diferentes para desenvolvimento e produção
- Rotacionar chaves e tokens periodicamente
- Criar backup seguro do `.env` em local protegido
- Usar variáveis de ambiente do servidor em produção

### ❌ NUNCA FAZER
- Commitar arquivo `.env` com valores reais no git
- Expor API keys em código, documentação ou screenshots
- Usar mesmas credenciais em dev e produção
- Compartilhar arquivo `.env` por email, chat ou redes sociais
- Deixar valores padrão em produção

## 📝 Como Criar o Arquivo .env

### Passo 1: Criar o Arquivo

```bash
# Na raiz do projeto
touch .env

# Ou no Windows (PowerShell)
New-Item .env -ItemType File
```

### Passo 2: Adicionar as Variáveis

Copie o template abaixo e preencha com seus valores reais:

```bash
# ============================================
# GEMINI AI - Google AI Studio
# ============================================
GEMINI_API_KEY=sua_chave_gemini_aqui
GEMINI_ENABLED=True
GEMINI_MODEL=gemini-2.0-flash
GEMINI_TEMPERATURE=0.7
GEMINI_MAX_TOKENS=1024

# ============================================
# WHATSAPP BUSINESS API - Meta/Facebook
# ============================================
WHATSAPP_ACCESS_TOKEN=seu_token_de_acesso_aqui
WHATSAPP_PHONE_NUMBER_ID=seu_phone_number_id_aqui
WHATSAPP_VERIFY_TOKEN=seu_verify_token_aqui
WHATSAPP_API_URL=https://graph.facebook.com/v18.0

# ============================================
# GOOGLE CALENDAR - Agendamento
# ============================================
GOOGLE_CALENDAR_ENABLED=True
GOOGLE_SERVICE_ACCOUNT_FILE=service-account-key.json
CLINIC_CALENDAR_ID=seu_calendar_id@group.calendar.google.com
CLINIC_DOMAIN=gmail.com

# ============================================
# CLÍNICA - Informações de Contato
# ============================================
CLINIC_WHATSAPP_NUMBER=5500000000000

# ============================================
# DJANGO - Configurações do Framework
# ============================================
DEBUG=True
SECRET_KEY=sua-chave-secreta-django-aqui
ALLOWED_HOSTS=localhost,127.0.0.1
```

## 🔑 Como Obter as Credenciais

### 1. GEMINI_API_KEY

1. Acesse: https://aistudio.google.com/app/apikey
2. Faça login com sua conta Google
3. Clique em "Create API Key"
4. Copie a chave gerada
5. Cole no `.env`

**Formato:** `GEMINI_API_KEY=AIzaSy...`

### 2. WHATSAPP (Meta/Facebook)

1. Acesse: https://developers.facebook.com/apps
2. Crie um app ou use existente
3. Adicione o produto "WhatsApp"
4. Na seção "API Setup":
   - `WHATSAPP_ACCESS_TOKEN`: Token de acesso temporário ou permanente
   - `WHATSAPP_PHONE_NUMBER_ID`: ID do número de telefone de teste
5. Crie um token de verificação personalizado:
   - `WHATSAPP_VERIFY_TOKEN`: Qualquer string secreta (ex: `meu_token_secreto_123`)

**Formato:**
```bash
WHATSAPP_ACCESS_TOKEN=EAABsb...
WHATSAPP_PHONE_NUMBER_ID=123456789012345
WHATSAPP_VERIFY_TOKEN=meu_token_secreto_123
```

### 3. GOOGLE CALENDAR

1. Acesse: https://console.cloud.google.com
2. Crie um projeto ou use existente
3. Ative a API do Google Calendar
4. Crie uma Service Account:
   - IAM & Admin > Service Accounts > Create Service Account
   - Baixe o arquivo JSON de credenciais
   - Renomeie para `service-account-key.json`
   - Coloque na raiz do projeto
5. No Google Calendar:
   - Abra o calendário da clínica
   - Configurações > Compartilhar com pessoas específicas
   - Adicione o email da Service Account com permissão "Fazer alterações nos eventos"
   - Copie o ID do calendário (Configurações > Integrar calendário)

**Formato:**
```bash
GOOGLE_SERVICE_ACCOUNT_FILE=service-account-key.json
CLINIC_CALENDAR_ID=abc123...@group.calendar.google.com
```

### 4. CLINIC_WHATSAPP_NUMBER

Número do WhatsApp da clínica para handoff (transferência para secretária).

**Formato:** Código do país + DDD + Número (sem espaços ou caracteres especiais)
```bash
CLINIC_WHATSAPP_NUMBER=5573988221003
# 55 = Brasil
# 73 = DDD
# 988221003 = Número
```

### 5. SECRET_KEY (Django)

Gere uma chave secreta aleatória:

```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

Copie a saída e cole no `.env`:
```bash
SECRET_KEY=django-insecure-a1b2c3d4e5f6g7h8i9j0...
```

## ✅ Verificação da Configuração

Após criar o `.env`, verifique se está tudo correto:

### 1. Verificar se o arquivo existe e está no .gitignore

```bash
# Verificar se existe
ls -la .env

# Verificar se está no .gitignore
cat .gitignore | grep .env
```

### 2. Verificar se as variáveis estão sendo carregadas

```bash
python manage.py shell
```

```python
from django.conf import settings

# Verificar Gemini
print("GEMINI_API_KEY:", settings.GEMINI_API_KEY is not None)

# Verificar WhatsApp
print("WHATSAPP_ACCESS_TOKEN:", settings.WHATSAPP_ACCESS_TOKEN is not None)
print("WHATSAPP_PHONE_NUMBER_ID:", settings.WHATSAPP_PHONE_NUMBER_ID is not None)

# Verificar Google Calendar
print("CLINIC_CALENDAR_ID:", settings.CLINIC_CALENDAR_ID is not None)

# Sair
exit()
```

### 3. Testar as conexões

```bash
# Iniciar servidor
python manage.py runserver

# Em outro terminal, testar Gemini
curl http://localhost:8000/test-gemini-connection/

# Verificar estatísticas de tokens
curl http://localhost:8000/token-usage-stats/
```

## 🐛 Troubleshooting

### Erro: "No module named 'dotenv'"

```bash
pip install python-dotenv
```

### Erro: "GEMINI_API_KEY not found"

1. Verifique se o arquivo `.env` está na raiz do projeto
2. Verifique se não há espaços antes/depois do `=`
3. Verifique se a chave está correta (sem aspas)

Correto:
```bash
GEMINI_API_KEY=AIzaSy...
```

Incorreto:
```bash
GEMINI_API_KEY = "AIzaSy..."
```

### Erro: "WhatsApp webhook verification failed"

1. Verifique se `WHATSAPP_VERIFY_TOKEN` está correto
2. Use o mesmo token nas configurações do webhook no Facebook
3. Não use caracteres especiais no token

### Erro: "Google Calendar permission denied"

1. Verifique se a Service Account tem permissão no calendário
2. Verifique se o ID do calendário está correto
3. Verifique se o arquivo `service-account-key.json` está na raiz

## 📊 Exemplo de Valores para Desenvolvimento

```bash
# Valores de exemplo APENAS para desenvolvimento local
# NUNCA use estes valores em produção!

GEMINI_API_KEY=AIzaSyABC123...
GEMINI_ENABLED=True
GEMINI_MODEL=gemini-2.0-flash

WHATSAPP_ACCESS_TOKEN=EAABsbCS...
WHATSAPP_PHONE_NUMBER_ID=123456789012345
WHATSAPP_VERIFY_TOKEN=meu_token_dev_123
WHATSAPP_API_URL=https://graph.facebook.com/v18.0

GOOGLE_CALENDAR_ENABLED=True
GOOGLE_SERVICE_ACCOUNT_FILE=service-account-key.json
CLINIC_CALENDAR_ID=abc123@group.calendar.google.com
CLINIC_DOMAIN=gmail.com

CLINIC_WHATSAPP_NUMBER=5500000000000

DEBUG=True
SECRET_KEY=django-insecure-dev-key-change-me
ALLOWED_HOSTS=localhost,127.0.0.1
```

## 🔒 Segurança em Produção

### Usar Variáveis de Ambiente do Servidor

Em produção, ao invés de usar arquivo `.env`, configure as variáveis diretamente no servidor:

**Heroku:**
```bash
heroku config:set GEMINI_API_KEY=sua_chave
```

**AWS Elastic Beanstalk:**
Configurar via Console > Environment Properties

**Docker:**
```bash
docker run -e GEMINI_API_KEY=sua_chave ...
```

**Linux (systemd):**
```bash
# /etc/systemd/system/chatbot.service
[Service]
Environment="GEMINI_API_KEY=sua_chave"
```

### Rotação de Credenciais

Recomendado trocar periodicamente:
- **API Keys**: A cada 90 dias
- **Tokens WhatsApp**: A cada 60 dias
- **Secret Key Django**: Nunca (a menos que comprometida)

---

**Para mais informações, consulte a documentação completa em `docs/FLUXO_COMPLETO_PROJETO.md`**

