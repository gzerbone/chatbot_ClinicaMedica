# 🤖 Configuração do Webhook WhatsApp + Gemini

Este guia explica como configurar o webhook do WhatsApp Business API para funcionar com seu chatbot Django usando Gemini AI.

## 📋 Pré-requisitos

1. **WhatsApp Business API** configurado no Meta for Developers
2. **Google Gemini API Key** obtida no Google AI Studio
3. **ngrok** instalado para exposição local
4. **Python 3.8+** e **Django** configurados

## 🚀 Passo a Passo

### 1. Configurar Variáveis de Ambiente

Copie o arquivo `env_example.txt` para `.env` na raiz do projeto:

```bash
cp env_example.txt .env
```

Edite o arquivo `.env` com suas credenciais:

```env
# Configurações do Django
DEBUG=True
SECRET_KEY=sua_secret_key_aqui
ALLOWED_HOSTS=localhost,127.0.0.1,sua-url-do-ngrok.ngrok-free.app

# Configurações do Gemini AI
GEMINI_API_KEY=sua_gemini_api_key_aqui
GEMINI_ENABLED=True
GEMINI_MODEL=gemini-1.5-flash
GEMINI_TEMPERATURE=0.7
GEMINI_MAX_TOKENS=1024

# Configurações do WhatsApp Business API
WHATSAPP_ACCESS_TOKEN=seu_whatsapp_access_token_aqui
WHATSAPP_VERIFY_TOKEN=meu_verify_token_123
WHATSAPP_PHONE_NUMBER_ID=seu_phone_number_id_aqui
WHATSAPP_API_URL=https://graph.facebook.com/v18.0
```

### 2. Obter Credenciais do WhatsApp Business API

#### No Meta for Developers:

1. Acesse https://developers.facebook.com/
2. Vá para **Meus Apps** → **Criar App** → **Business**
3. Adicione o produto **WhatsApp Business API**
4. Nas configurações do WhatsApp:
   - **Access Token**: Copie o token temporário ou gere um permanente
   - **Phone Number ID**: Encontre na seção "From" do número de teste
   - **Verify Token**: Defina um token personalizado (ex: `meu_verify_token_123`)

### 3. Obter API Key do Gemini

1. Acesse https://aistudio.google.com/
2. Faça login com sua conta Google
3. Vá em **Get API Key** → **Create API Key**
4. Copie a chave gerada

### 4. Configurar ngrok

Instale e configure o ngrok:

```bash
# Instalar ngrok (Windows/Mac/Linux)
# Baixe de: https://ngrok.com/download

# Executar ngrok na porta 8000
ngrok http 8000
```

Copie a URL HTTPS fornecida (ex: `https://abc123.ngrok-free.app`)

### 5. Configurar Webhook no WhatsApp

No Meta for Developers:

1. Vá para **WhatsApp** → **Configuration** → **Webhook**
2. Configure:
   - **Callback URL**: `https://sua-url-ngrok.ngrok-free.app/api/webhook/whatsapp/`
   - **Verify Token**: `meu_verify_token_123` (mesmo do .env)
3. Clique em **Verify and Save**
4. Inscreva-se nos eventos: `messages`

### 6. Testar a Configuração

Execute o script de teste:

```bash
# Ativar ambiente virtual
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Executar teste
python test_webhook_integration.py
```

### 7. Iniciar o Servidor Django

```bash
# Aplicar migrações
python manage.py migrate

# Iniciar servidor
python manage.py runserver 0.0.0.0:8000
```

## 🧪 Testando a Integração

### Teste Manual via WhatsApp

1. Envie uma mensagem para o número de teste do WhatsApp
2. Verifique os logs do Django para ver o processamento
3. O bot deve responder usando o Gemini AI

### Testes Automatizados

Execute os endpoints de teste:

```bash
# Testar Gemini
curl http://localhost:8000/api/test/gemini/

# Testar detecção de intenção
curl -X POST http://localhost:8000/api/test/intent/ \
  -H "Content-Type: application/json" \
  -d '{"message": "Olá, preciso agendar uma consulta"}'

# Testar envio de mensagem (apenas desenvolvimento)
curl -X POST http://localhost:8000/api/test/send-message/ \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "5511999999999", "message": "Teste do bot!"}'
```

## 🔧 Troubleshooting

### Erro: "GEMINI_API_KEY não configurada"
- Verifique se o arquivo `.env` existe
- Confirme se a API key está correta
- Teste a key no Google AI Studio

### Erro: "Webhook verification failed"
- Confirme se o verify token no .env é igual ao configurado no Meta
- Verifique se a URL do ngrok está correta
- Teste manualmente: `GET https://sua-url.ngrok-free.app/api/webhook/whatsapp/?hub.mode=subscribe&hub.verify_token=meu_verify_token_123&hub.challenge=test`

### Erro: "WhatsApp API 403 Forbidden"
- Verifique se o access token está válido
- Confirme se o phone number ID está correto
- Teste com o número de telefone verificado

### Mensagens não chegam
- Verifique se o webhook está inscrito no evento `messages`
- Confirme se o ngrok está rodando
- Teste enviar mensagem para o número de teste primeiro

## 📱 Fluxo de Funcionamento

1. **Usuário envia mensagem** via WhatsApp
2. **Meta encaminha** para seu webhook Django
3. **Django processa** a mensagem e detecta intenção
4. **Gemini AI gera** resposta contextualizada
5. **Django envia** resposta de volta via WhatsApp API
6. **Usuário recebe** a resposta no WhatsApp

## 🔒 Segurança

- Mantenha o arquivo `.env` fora do controle de versão
- Use HTTPS sempre (ngrok fornece automaticamente)
- Valide sempre o verify token do webhook
- Monitore logs para tentativas de acesso não autorizadas

## 📞 Suporte

Se encontrar problemas:

1. Verifique os logs do Django
2. Execute o script de teste
3. Confirme todas as configurações no Meta for Developers
4. Teste a conectividade com ngrok

## 🎯 Próximos Passos

- Implementar persistência de conversas
- Adicionar mais intenções e respostas
- Integrar com sistema de agendamentos
- Configurar ambiente de produção
