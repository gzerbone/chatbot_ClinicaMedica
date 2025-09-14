# 🤖 Fluxo Completo do Chatbot - Clínica Médica

Este documento detalha todo o processo que ocorre desde o momento em que um paciente envia uma mensagem via WhatsApp até receber a resposta formatada pelo Gemini AI.

## 📋 Visão Geral da Arquitetura

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   PACIENTE      │    │   WHATSAPP       │    │   CHATBOT       │
│   (WhatsApp)    │◄──►│   BUSINESS API   │◄──►│   (Django)      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                        │
                       ┌─────────────────────────────────┼─────────────────────────────────┐
                       │                                 │                                 │
                ┌──────▼──────┐                 ┌────────▼────────┐                ┌─────▼─────┐
                │ API GATEWAY │                 │  FLOW AGENT     │                │ RAG AGENT │
                │ (Webhook)   │                 │ (Gemini AI)     │                │ (Dados)   │
                └─────────────┘                 └─────────────────┘                └───────────┘
```

## 🔄 Fluxo Detalhado do Processo

### 1️⃣ **ENVIO DA MENSAGEM PELO PACIENTE**

```
📱 Paciente digita: "Olá, preciso agendar uma consulta com cardiologista"
```

**O que acontece:**
- Paciente envia mensagem através do WhatsApp
- WhatsApp Business API recebe a mensagem
- Meta (Facebook) encaminha via webhook HTTP POST para o servidor Django

---

### 2️⃣ **RECEPÇÃO DO WEBHOOK (API Gateway)**

**Arquivo:** `api_gateway/views.py` → `whatsapp_webhook()`

```python
# Middleware processa primeiro
WhatsAppWebhookCSRFExemptMiddleware  # Desabilita CSRF para webhook
RequestLoggingMiddleware             # Registra logs da requisição
```

**Estrutura da mensagem recebida:**
```json
{
  "entry": [{
    "changes": [{
      "field": "messages",
      "value": {
        "messaging_product": "whatsapp",
        "metadata": {
          "display_phone_number": "15551234567",
          "phone_number_id": "123456789"
        },
        "contacts": [{
          "profile": {"name": "João Silva"},
          "wa_id": "5511999999999"
        }],
        "messages": [{
          "id": "wamid.HBgNNTUxMTk5OTk5OTk5ORUCABIYFjNBMDJBN0Y5RjBEMzA3RjdEMzQ1AA==",
          "from": "5511999999999",
          "timestamp": "1640995200",
          "type": "text",
          "text": {
            "body": "Olá, preciso agendar uma consulta com cardiologista"
          }
        }]
      }
    }]
  }]
}
```

---

### 3️⃣ **PROCESSAMENTO DA MENSAGEM**

**Função:** `handle_webhook()` → `process_message()`

```python
# 1. Extração dos dados da mensagem
message_id = "wamid.HBgNNTUxMTk5OTk5OTk5ORUCABIYFjNBMDJBN0Y5RjBEMzA3RjdEMzQ1AA=="
from_number = "5511999999999"
message_type = "text"
text_content = "Olá, preciso agendar uma consulta com cardiologista"
timestamp = "1640995200"

# 2. Marcar mensagem como lida
whatsapp_service.mark_message_as_read(message_id)
```

---

### 4️⃣ **DETECÇÃO DE INTENÇÃO**

**Arquivo:** `api_gateway/services/intent_detection_service.py`

```python
# Análise da mensagem
intent, confidence = intent_service.detect_intent(text_content)
entities = intent_service.extract_entities(text_content)

# Resultado exemplo:
intent = "buscar_medico"
confidence = 0.85
entities = {
    "especialidade": "cardiologista",
    "acao": "agendar",
    "tipo_consulta": "consulta"
}
```

**Lógica de detecção:**
- Palavras-chave para intenções (regex e matching)
- Extração de entidades (especialidades, nomes, datas)
- Cálculo de confiança baseado em matches

---

### 5️⃣ **OBTENÇÃO DOS DADOS DA CLÍNICA (RAG)**

**Arquivo:** `api_gateway/services/rag_service.py`

```python
# Busca todos os dados da clínica
clinic_data = get_clinic_data()  # Chama RAGService.get_all_clinic_data()

# Resultado:
{
    "clinica_info": {
        "nome": "Clínica Saúde Total",
        "endereco": "Rua das Flores, 123",
        "telefone": "(11) 99999-9999",
        "horario_funcionamento": "08:00 às 18:00",
        "whatsapp_contato": "(11) 98888-8888"
    },
    "especialidades": [
        {
            "id": 1,
            "nome": "Cardiologia",
            "descricao": "Especialidade médica que cuida do coração",
            "ativa": True
        },
        {
            "id": 2,
            "nome": "Dermatologia", 
            "descricao": "Especialidade médica que cuida da pele",
            "ativa": True
        }
    ],
    "medicos": [
        {
            "id": 1,
            "nome": "Dr. João Carvalho",
            "crm": "123456",
            "especialidades": ["Cardiologia"],
            "convenios": ["SulAmérica", "Unimed"]
        }
    ],
    "convenios": [
        {"id": 1, "nome": "SulAmérica"},
        {"id": 2, "nome": "Unimed"}
    ],
    "exames": [
        {
            "id": 1,
            "nome": "Eletrocardiograma",
            "descricao": "Exame do coração",
            "preco": 80.00
        }
    ]
}
```

---

### 6️⃣ **GERAÇÃO DA RESPOSTA (Gemini AI)**

**Arquivo:** `flow_agent/services/gemini_service.py`

```python
# Construção do prompt contextualizado
response_text = gemini_service.generate_response(
    user_message="Olá, preciso agendar uma consulta com cardiologista",
    intent="buscar_medico",
    context={
        'entities': {"especialidade": "cardiologista"},
        'confidence': 0.85,
        'message_id': "wamid.HBgN...",
        'timestamp': "1640995200"
    },
    clinic_data=get_clinic_data()  # Todos os dados da clínica
)
```

**Prompt enviado para o Gemini:**
```
Você é um assistente virtual especializado de uma clínica médica. 
Seu papel é ajudar pacientes com informações sobre a clínica, agendamentos, médicos e exames.

IMPORTANTE:
- Seja sempre cordial, profissional e prestativo
- Use emojis moderadamente para tornar a conversa mais amigável
- Mantenha respostas concisas mas informativas
- Se não souber algo específico, oriente o paciente a entrar em contato
- Sempre mantenha o foco em saúde e bem-estar
- Use linguagem clara e acessível

Contexto da clínica:

Informações da clínica:
{
  "nome": "Clínica Saúde Total",
  "endereco": "Rua das Flores, 123",
  "telefone": "(11) 99999-9999",
  "medicos": [...],
  "especialidades": [...]
}

Contexto da conversa:
{
  "entities": {"especialidade": "cardiologista"},
  "confidence": 0.85,
  "message_id": "wamid.HBgN...",
  "timestamp": "1640995200"
}

Instruções específicas para esta intenção (buscar_medico):
- Apresente os médicos disponíveis
- Inclua especialidades, experiência e formas de pagamento
- Destaque pontos fortes de cada médico
- Facilite o processo de escolha

Mensagem do paciente: Olá, preciso agendar uma consulta com cardiologista

Resposta:
```

**Resposta gerada pelo Gemini:**
```
Olá! 😊 Que bom que você procurou nossa clínica!

Para cardiologia, temos o **Dr. João Carvalho** (CRM 123456), um excelente cardiologista com grande experiência.

📋 **Informações do médico:**
• Especialidade: Cardiologia
• Convênios aceitos: SulAmérica, Unimed
• Atendimento: Segunda a sexta, 8h às 18h

Para agendar sua consulta, você pode:
📞 Ligar: (11) 99999-9999
💬 WhatsApp: (11) 98888-8888

Precisa de mais alguma informação sobre o Dr. João ou tem alguma dúvida sobre o agendamento? 🏥
```

---

### 7️⃣ **ENVIO DA RESPOSTA (WhatsApp API)**

**Arquivo:** `api_gateway/services/whatsapp_service.py`

```python
# Envio via WhatsApp Business API
success = whatsapp_service.send_message(from_number, response_text)

# Requisição HTTP POST para Meta:
POST https://graph.facebook.com/v18.0/{phone_number_id}/messages
Headers: {
    "Authorization": "Bearer {access_token}",
    "Content-Type": "application/json"
}
Body: {
    "messaging_product": "whatsapp",
    "to": "5511999999999",
    "type": "text",
    "text": {
        "body": "Olá! 😊 Que bom que você procurou nossa clínica!..."
    }
}
```

---

### 8️⃣ **RECEBIMENTO PELO PACIENTE**

```
📱 Paciente recebe no WhatsApp:
"Olá! 😊 Que bom que você procurou nossa clínica!

Para cardiologia, temos o **Dr. João Carvalho** (CRM 123456), 
um excelente cardiologista com grande experiência.

📋 Informações do médico:
• Especialidade: Cardiologia  
• Convênios aceitos: SulAmérica, Unimed
• Atendimento: Segunda a sexta, 8h às 18h

Para agendar sua consulta, você pode:
📞 Ligar: (11) 99999-9999
💬 WhatsApp: (11) 98888-8888

Precisa de mais alguma informação sobre o Dr. João ou 
tem alguma dúvida sobre o agendamento? 🏥"
```

---

## 🔧 Componentes Técnicos Envolvidos

### **API Gateway (`api_gateway/`)**
- **views.py**: Recepção e processamento do webhook
- **middleware.py**: CSRF exemption e logging
- **services/whatsapp_service.py**: Comunicação com WhatsApp API
- **services/intent_detection_service.py**: Análise de intenções
- **services/rag_service.py**: Acesso aos dados da clínica

### **Flow Agent (`flow_agent/`)**
- **services/gemini_service.py**: Integração com Gemini AI
- Geração de respostas contextualizadas
- Fallbacks para quando Gemini não está disponível

### **RAG Agent (`rag_agent/`)**
- **models.py**: Modelos de dados (Médico, Especialidade, etc.)
- **serializers.py**: Serialização para JSON
- **views.py**: APIs REST para dados da clínica

### **Core (`core/`)**
- **settings.py**: Configurações do Django e variáveis de ambiente
- **urls.py**: Roteamento principal
- **middleware**: Logging e tratamento de requisições

---

## 📊 Fluxo de Dados Resumido

```
1. 📱 Paciente → WhatsApp Business API
   Mensagem: "Olá, preciso agendar uma consulta com cardiologista"

2. 🌐 WhatsApp API → Django Webhook
   POST /api/webhook/whatsapp/

3. 🔍 Intent Detection Service
   Intenção: "buscar_medico" | Confiança: 0.85

4. 🏥 RAG Service
   Busca: Médicos cardiologistas + dados da clínica

5. 🤖 Gemini AI Service
   Prompt + Context + Clinic Data → Resposta personalizada

6. 📤 WhatsApp Service
   Envio da resposta formatada para o paciente

7. 📱 Paciente recebe resposta contextualizada
```

---

## ⏱️ Tempo de Resposta Estimado

- **Recepção do webhook**: ~50ms
- **Processamento da mensagem**: ~100ms
- **Detecção de intenção**: ~200ms
- **Busca dados RAG**: ~150ms
- **Geração Gemini**: ~2-5 segundos
- **Envio WhatsApp**: ~300ms

**Total: ~3-6 segundos** ⚡

---

## 🔒 Segurança e Validação

1. **Verificação do Webhook**: Token de verificação do Meta
2. **CSRF Protection**: Desabilitado apenas para webhook
3. **Rate Limiting**: Controle de frequência de mensagens
4. **Logs Detalhados**: Monitoramento de todas as operações
5. **Tratamento de Erros**: Fallbacks em cada etapa

---

## 🎯 Casos de Uso Suportados

- ✅ Busca de médicos por especialidade
- ✅ Informações sobre exames
- ✅ Dados da clínica (endereço, telefone, horários)
- ✅ Consulta de convênios aceitos
- ✅ Orientações para agendamento
- ✅ Respostas a saudações e despedidas
- ✅ Tratamento de mensagens não compreendidas

---

## 📈 Métricas e Monitoramento

O sistema registra:
- Volume de mensagens por dia
- Intenções mais detectadas
- Tempo de resposta do Gemini
- Taxa de sucesso de envio
- Erros e exceções

**Logs disponíveis em:**
- Console do Django (desenvolvimento)
- Arquivos de log (produção)
- Monitoramento via middleware customizado
