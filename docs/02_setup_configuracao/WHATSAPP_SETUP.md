# Configuração do WhatsApp API para Chatbot da Clínica Médica

## Visão Geral

Este documento explica como configurar e testar a integração do WhatsApp Business API com o chatbot da clínica médica usando Django REST Framework e Google Gemini AI.

## Pré-requisitos

1. **Conta do WhatsApp Business** configurada
2. **Acesso ao WhatsApp Business API** (via Meta for Developers)
3. **API Key do Google Gemini** configurada
4. **Servidor público** para receber webhooks (pode usar ngrok para desenvolvimento)

## Configuração

### 1. Configurar Variáveis de Ambiente

Edite o arquivo `core/settings.py` e configure as seguintes variáveis:

```python
# Configurações do Gemini AI
GEMINI_API_KEY = 'sua_api_key_do_gemini_aqui'
GEMINI_ENABLED = True
GEMINI_MODEL = 'gemini-1.5-flash'
GEMINI_TEMPERATURE = 0.7
GEMINI_MAX_TOKENS = 1024

# Configurações do WhatsApp API
WHATSAPP_ACCESS_TOKEN = 'seu_access_token_do_whatsapp_aqui'
WHATSAPP_VERIFY_TOKEN = 'seu_verify_token_personalizado_aqui'
WHATSAPP_PHONE_NUMBER_ID = 'seu_phone_number_id_aqui'
WHATSAPP_API_URL = 'https://graph.facebook.com/v18.0'
```

### 2. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 3. Configurar WhatsApp Business API

#### No Meta for Developers:

1. Acesse [developers.facebook.com](https://developers.facebook.com)
2. Crie uma aplicação do tipo "Business"
3. Adicione o produto "WhatsApp Business API"
4. Configure o webhook:
   - **URL do Webhook**: `https://seu-dominio.com/api/webhook/whatsapp/`
   - **Verify Token**: Use o mesmo valor configurado em `WHATSAPP_VERIFY_TOKEN`
   - **Campos de Webhook**: Selecione `messages`

#### Obter Credenciais:

- **Access Token**: Token de acesso permanente
- **Phone Number ID**: ID do número de telefone do WhatsApp Business
- **Verify Token**: Token personalizado para verificação do webhook

### 4. Executar o Servidor

```bash
python manage.py runserver
```

### 5. Expor o Servidor para Webhooks (Desenvolvimento)

Para desenvolvimento, use ngrok para expor seu servidor local:

```bash
# Instalar ngrok
# Windows: baixar de https://ngrok.com/
# Linux/Mac: npm install -g ngrok

# Expor porta 8000
ngrok http 8000
```

Use a URL do ngrok (ex: `https://abc123.ngrok.io`) como URL do webhook no Meta for Developers.

## Endpoints Disponíveis

### 1. Webhook do WhatsApp
- **URL**: `/api/webhook/whatsapp/`
- **Métodos**: GET (verificação), POST (receber mensagens)
- **Descrição**: Endpoint principal para receber mensagens do WhatsApp

### 2. Testes (Desenvolvimento)

#### Testar Conexão com Gemini
```bash
GET /api/test/gemini/
```

#### Testar Detecção de Intenções
```bash
POST /api/test/intent/
Content-Type: application/json

{
    "message": "Olá, quero agendar uma consulta"
}
```

#### Testar Envio de Mensagem
```bash
POST /api/test/send-message/
Content-Type: application/json

{
    "phone_number": "5511999999999",
    "message": "Teste do chatbot!"
}
```

## Fluxo de Funcionamento

1. **Usuário envia mensagem** via WhatsApp
2. **WhatsApp API** envia webhook para `/api/webhook/whatsapp/`
3. **Sistema detecta intenção** da mensagem usando regex patterns
4. **Gemini AI** gera resposta contextual baseada na intenção
5. **Sistema envia resposta** via WhatsApp API
6. **Usuário recebe resposta** no WhatsApp

## Intenções Suportadas

O sistema detecta automaticamente as seguintes intenções:

- **saudacao**: Cumprimentos e saudações
- **buscar_especialidade**: Consulta sobre especialidades médicas
- **buscar_medico**: Informações sobre médicos
- **buscar_exame**: Informações sobre exames e procedimentos
- **buscar_info_clinica**: Informações gerais da clínica
- **agendar_consulta**: Processo de agendamento
- **confirmar_agendamento**: Confirmação de agendamentos
- **horarios_disponiveis**: Consulta de horários
- **despedida**: Despedidas e agradecimentos
- **ajuda**: Solicitações de ajuda
- **desconhecida**: Mensagens não reconhecidas

## Exemplos de Uso

### Mensagens que o Bot Entende:

```
Usuário: "Olá, bom dia!"
Bot: "Olá! Bom dia! 😊 Bem-vindo à nossa clínica! Como posso ajudá-lo hoje?"

Usuário: "Quero agendar uma consulta"
Bot: "Ótimo! Vou ajudá-lo a agendar sua consulta. Qual especialidade você precisa?"

Usuário: "Quais especialidades vocês têm?"
Bot: "Temos as seguintes especialidades disponíveis: [lista das especialidades]"

Usuário: "Qual o endereço da clínica?"
Bot: "Nossa clínica está localizada em [endereço]. [informações adicionais]"
```

## Logs e Debugging

O sistema gera logs detalhados para facilitar o debugging:

```python
# Logs são salvos em:
logger.info(f"Webhook recebido: {json.dumps(body, indent=2)}")
logger.info(f"Intenção detectada: {intent} (confiança: {confidence})")
logger.info(f"Resposta enviada com sucesso para {from_number}")
```

## Troubleshooting

### Problemas Comuns:

1. **Webhook não é verificado**:
   - Verifique se o `WHATSAPP_VERIFY_TOKEN` está correto
   - Confirme se a URL está acessível publicamente

2. **Mensagens não são recebidas**:
   - Verifique se o webhook está configurado corretamente no Meta for Developers
   - Confirme se o `WHATSAPP_ACCESS_TOKEN` é válido

3. **Gemini não responde**:
   - Verifique se a `GEMINI_API_KEY` está configurada corretamente
   - Teste a conexão usando `/api/test/gemini/`

4. **Erro de CORS**:
   - Verifique se `django-cors-headers` está instalado
   - Confirme se o middleware está configurado corretamente

### Verificar Status:

```bash
# Testar conexão com Gemini
curl http://localhost:8000/api/test/gemini/

# Testar detecção de intenção
curl -X POST http://localhost:8000/api/test/intent/ \
  -H "Content-Type: application/json" \
  -d '{"message": "Olá, quero agendar uma consulta"}'
```

## Próximos Passos

1. **Configurar dados da clínica** no RAG Agent
2. **Implementar persistência** de conversas
3. **Adicionar templates** de mensagem do WhatsApp
4. **Implementar agendamento** real
5. **Adicionar validações** de dados
6. **Configurar monitoramento** e métricas

## Segurança

⚠️ **Importante para Produção**:

1. Use variáveis de ambiente para credenciais
2. Configure HTTPS obrigatório
3. Implemente rate limiting
4. Adicione autenticação para endpoints de teste
5. Configure logs de auditoria
6. Use firewall para proteger endpoints sensíveis
