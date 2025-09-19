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

## 🔄 Diagrama de Fluxo de Dados Atualizado

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    FLUXO DE DADOS ATUALIZADO                               │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                             │
│  📱 PACIENTE                                                                                │
│     │                                                                                       │
│     │ "Olá, preciso agendar uma consulta com cardiologista"                                │
│     ▼                                                                                       │
│  🌐 WHATSAPP BUSINESS API                                                                    │
│     │                                                                                       │
│     │ HTTP POST Webhook                                                                     │
│     ▼                                                                                       │
│  🔧 DJANGO MIDDLEWARE                                                                       │
│     │ • CSRF Exemption                                                                      │
│     │ • Request Logging                                                                     │
│     ▼                                                                                       │
│  📥 API GATEWAY WEBHOOK                                                                     │
│     │                                                                                       │
│     │ process_message()                                                                     │
│     ▼                                                                                       │
│  🔍 INTENT DETECTION SERVICE                                                                │
│     │ • ContextManager.analyze_contextual_intent()                                          │
│     │ • BaseService.extract_entities()                                                      │
│     │ • Fallback para análise tradicional                                                   │
│     ▼                                                                                       │
│  🧠 SMART COLLECTION SERVICE                                                                │
│     │ • check_required_info()                                                               │
│     │ • process_message_with_collection()                                                   │
│     │ • Confirmação de nome (se necessário)                                                 │
│     ▼                                                                                       │
│  🏥 RAG SERVICE                                                                             │
│     │ • get_all_clinic_data()                                                               │
│     │ • Cache inteligente                                                                   │
│     │ • Dados de médicos e especialidades                                                   │
│     ▼                                                                                       │
│  🤖 GEMINI AI SERVICE                                                                       │
│     │ • generate_response()                                                                 │
│     │ • Prompt contextualizado                                                              │
│     │ • Lógica inteligente de contatos                                                      │
│     │ • Fallback robusto                                                                    │
│     ▼                                                                                       │
│  💾 CONVERSATION SERVICE                                                                    │
│     │ • add_message() (user)                                                                │
│     │ • add_message() (bot)                                                                 │
│     │ • update_patient_info()                                                               │
│     ▼                                                                                       │
│  📤 WHATSAPP SERVICE                                                                        │
│     │ • send_message()                                                                      │
│     │ • mark_message_as_read()                                                              │
│     ▼                                                                                       │
│  📱 PACIENTE RECEBE RESPOSTA                                                                │
│     │ "Olá! 😊 Que bom que você procurou nossa clínica! Para cardiologia, temos o Dr. João │
│     │  Carvalho (CRM 123456), um excelente cardiologista com grande experiência..."        │
│                                                                                             │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
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

### 4️⃣ **DETECÇÃO DE INTENÇÃO CONTEXTUAL**

**Arquivo:** `api_gateway/services/intent_detection_service.py`

```python
# Análise contextual da mensagem usando ContextManager
intent, confidence, entities = intent_service.detect_intent_with_context(
    from_number, text_content
)

# Resultado exemplo:
intent = "buscar_medico"
confidence = 0.85
entities = {
    "especialidades": ["cardiologista"],
    "doctors": [],
    "patient_name": [],
    "insurance": [],
    "dates": [],
    "times": []
}
```

**Lógica de detecção contextual avançada:**
1. **Análise de mensagem simples** (sim/não/ok) baseada no contexto
2. **Verificação de confirmações pendentes** (nome, agendamento, etc.)
3. **Detecção de continuação de conversa** (e, também, mais, etc.)
4. **Análise contextual com histórico** de mensagens anteriores
5. **Extração de entidades** usando BaseService consolidado
6. **Consciência contextual** via ContextManager com cache
7. **Fallback para análise tradicional** se contexto falhar

---

### 5️⃣ **PROCESSAMENTO COM COLETA INTELIGENTE**

**Arquivo:** `api_gateway/services/smart_collection_service.py`

```python
# Processamento inteligente com coleta de informações
collection_result = smart_collection_service.process_message_with_collection(
    from_number, text_content, intent, entities
)

# Verificação de informações essenciais
info_status = conversation_service.check_required_info(from_number)

# Resultado da coleta:
{
    "response": None,  # Será preenchido pelo Gemini se necessário
    "next_action": "proceed",  # ou "waiting_for_name", "waiting_for_info"
    "requires_handoff": False,
    "info_status": {
        "is_complete": True,
        "missing_info": [],
        "has_name": True,
        "has_phone": True,
        "current_state": "collecting_patient_info"
    }
}
```

**Funcionalidades da Coleta Inteligente:**
1. **Verificação de informações essenciais** (nome completo, telefone)
2. **Extração automática de nome** da mensagem usando BaseService
3. **Validação de nome** com confirmação obrigatória
4. **Atualização de informações** baseada nas entidades extraídas
5. **Lógica de handoff** para transferência para atendimento humano
6. **Mensagens personalizadas** baseadas no estado da conversa
7. **Integração com ContextManager** para consciência contextual

---

### 5.1️⃣ **CONFIRMAÇÃO DE NOME DO PACIENTE**

**Arquivo:** `api_gateway/services/conversation_service.py`

```python
# Processamento de confirmação de nome
if collection_result.get('next_action') == 'waiting_for_name':
    name_result = conversation_service.process_patient_name(from_number, text_content)
    
    # Estados possíveis:
    if name_result['status'] == 'confirmation_needed':
        # Nome extraído, aguardando confirmação
        response_text = f"Entendi que seu nome é \"{name_result['pending_name']}\". Este é realmente o nome do paciente que deseja ser atendido? (Responda \"sim\" para confirmar ou \"não\" para informar outro nome)"
        
    elif name_result['status'] == 'confirmed':
        # Nome confirmado com sucesso
        response_text = f"Perfeito! Seu nome \"{name_result['confirmed_name']}\" foi confirmado. Agora vamos continuar com o agendamento."
        
    elif name_result['status'] == 'rejected':
        # Nome rejeitado, solicitar novo
        response_text = "Entendi. Por favor, me informe novamente seu nome completo para que possamos continuar."
        
    elif name_result['status'] == 'unclear_response':
        # Resposta não clara, pedir esclarecimento
        response_text = f"Não entendi sua resposta. O nome \"{name_result['pending_name']}\" está correto? Responda \"sim\" para confirmar ou \"não\" para informar outro nome."
```

**Fluxo de Confirmação de Nome:**
1. **Extração automática** do nome da mensagem
2. **Validação** usando BaseService.validate_patient_name()
3. **Armazenamento pendente** na sessão (pending_name)
4. **Solicitação de confirmação** ao paciente
5. **Processamento da resposta** (sim/não/incorreto)
6. **Confirmação ou rejeição** do nome
7. **Atualização do estado** da sessão

### 6️⃣ **OBTENÇÃO DOS DADOS DA CLÍNICA (RAG)**

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
    ]
}
```

---

### 7️⃣ **GERAÇÃO DA RESPOSTA (Gemini AI)**

**Arquivo:** `flow_agent/services/gemini_service.py`

```python
# Obter histórico da conversa
conversation_history = conversation_service.get_conversation_history(from_number, limit=3)

# Construção do prompt contextualizado
response_text = gemini_service.generate_response(
    user_message="Olá, preciso agendar uma consulta com cardiologista",
    intent="buscar_medico",
    context={
        'entities': entities,
        'confidence': confidence,
        'message_id': message_id,
        'timestamp': timestamp,
        'conversation_history': conversation_history,
        'info_status': collection_result.get('info_status', {})
    },
    clinic_data=get_clinic_data()  # Todos os dados da clínica
)
```

**Melhorias do Gemini Service:**
1. **Prompt dinâmico** baseado no nome da clínica do banco de dados
2. **Instruções específicas** por intenção detectada
3. **Lógica inteligente de contatos** (quando mostrar telefone/WhatsApp)
4. **Histórico de conversa** integrado no prompt
5. **Fallback robusto** quando Gemini não está disponível
6. **Configurações otimizadas** (temperatura, max_tokens)
7. **Validação de conexão** com teste automático

**Prompt enviado para o Gemini:**
```
Você é um assistente virtual especializado da Clínica Saúde Total.
Seu papel é ajudar pacientes com informações sobre a clínica, agendamentos, médicos e exames.

IMPORTANTE:
- Seja sempre cordial, profissional e prestativo
- Use emojis moderadamente para tornar a conversa mais amigável
- NÃO mencione telefone ou WhatsApp a menos que o paciente peça especificamente
- Foque apenas no que o paciente perguntou

Informações da clínica:
{
  "clinica_info": {
    "nome": "Clínica Saúde Total",
    "endereco": "Rua das Flores, 123",
    "telefone": "(11) 99999-9999",
    "whatsapp_contato": "(11) 98888-8888"
  },
  "medicos": [...],
  "especialidades": [...]
}

Histórico recente da conversa:
1. Paciente: Olá, preciso agendar uma consulta com cardiologista
2. Assistente: Olá! 😊 Que bom que você procurou nossa clínica!

Instruções específicas para esta intenção (buscar_medico):
- Apresente os médicos disponíveis que atendem a especialidade perguntada
- Informe nome, especialidade, convênios aceitos e horários de atendimento
- NÃO mencione telefone/WhatsApp a menos que o paciente peça

Lógica de contatos:
- NÃO mencione telefone ou WhatsApp nesta resposta
- Foque apenas no que o paciente perguntou

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

### 8️⃣ **PERSISTÊNCIA DA CONVERSA**

**Arquivo:** `api_gateway/services/conversation_service.py`

```python
# Persistir mensagens no banco de dados
conversation_service.add_message(
    from_number, text_content, 'user', intent, confidence, entities
)
conversation_service.add_message(
    from_number, response_text, 'bot', 'resposta_bot', 1.0, {}
)

# Atualizar informações do paciente se necessário
if entities:
    conversation_service.update_patient_info(from_number, **extracted_info)
```

### 9️⃣ **ENVIO DA RESPOSTA (WhatsApp API)**

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

### 🔟 **RECEBIMENTO PELO PACIENTE**

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
- **models.py**: Persistência de conversas e agendamentos
- **views.py**: Recepção e processamento do webhook
- **middleware.py**: CSRF exemption e logging
- **services/base_service.py**: 🆕 Funções comuns consolidadas
- **services/whatsapp_service.py**: Comunicação com WhatsApp API
- **services/intent_detection_service.py**: Análise contextual de intenções
- **services/conversation_service.py**: 🆕 Gerenciamento persistente de conversas
- **services/smart_collection_service.py**: 🆕 Coleta inteligente de informações
- **services/context_manager.py**: 🆕 Consciência contextual
- **services/rag_service.py**: Acesso aos dados da clínica
- **services/handoff_service.py**: Transferência para atendimento humano

### **Flow Agent (`flow_agent/`)**
- **services/gemini_service.py**: Integração com Gemini AI
- Geração de respostas contextualizadas com histórico
- Lógica inteligente de contatos
- Fallbacks para quando Gemini não está disponível
- Prompts personalizados por intenção

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

3. 🔍 Intent Detection Service (Contextual)
   Intenção: "buscar_medico" | Confiança: 0.85 | Entidades extraídas
   + ContextManager para análise contextual avançada

4. 🧠 Smart Collection Service
   Verificação de informações essenciais do paciente
   + Confirmação de nome obrigatória
   + Validação usando BaseService

5. 🏥 RAG Service
   Busca: Médicos cardiologistas + dados da clínica
   + Cache inteligente para performance

6. 🤖 Gemini AI Service
   Prompt + Context + Histórico + Clinic Data → Resposta personalizada
   + Lógica inteligente de contatos
   + Fallback robusto

7. 💾 Conversation Service
   Persistência das mensagens no banco de dados
   + Gerenciamento de estados de sessão
   + Confirmação de nome do paciente

8. 📤 WhatsApp Service
   Envio da resposta formatada para o paciente
   + Marcação de mensagem como lida

9. 📱 Paciente recebe resposta contextualizada
   + Consciência contextual completa
   + Fluxo natural de conversa
```

---

## ⏱️ Tempo de Resposta Estimado

- **Recepção do webhook**: ~50ms
- **Processamento da mensagem**: ~100ms
- **Detecção contextual de intenção**: ~250ms
- **Coleta inteligente de informações**: ~100ms
- **Busca dados RAG**: ~150ms
- **Geração Gemini**: ~2-5 segundos
- **Persistência da conversa**: ~50ms
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

### **Funcionalidades Básicas**
- ✅ Busca de médicos por especialidade
- ✅ Informações sobre exames
- ✅ Dados da clínica (endereço, telefone, horários)
- ✅ Consulta de convênios aceitos
- ✅ Orientações para agendamento
- ✅ Respostas a saudações e despedidas
- ✅ Tratamento de mensagens não compreendidas

### **Funcionalidades Avançadas**
- ✅ **Coleta inteligente de informações** do paciente
- ✅ **Persistência de conversas** com histórico completo
- ✅ **Consciência contextual** para respostas mais naturais
- ✅ **Confirmação de nome** do paciente com validação
- ✅ **Estados de conversa** para fluxos estruturados
- ✅ **Handoff inteligente** para atendimento humano
- ✅ **Detecção contextual** de intenções com ContextManager
- ✅ **Lógica inteligente** de quando mostrar contatos
- ✅ **Fallbacks robustos** quando IA não está disponível
- ✅ **BaseService consolidado** com funções comuns
- ✅ **Cache de contexto** para performance otimizada
- ✅ **Análise de mensagens simples** (sim/não/ok)
- ✅ **Detecção de continuação** de conversa
- ✅ **Validação robusta** de nomes e telefones
- ✅ **Extração avançada** de entidades médicas

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
