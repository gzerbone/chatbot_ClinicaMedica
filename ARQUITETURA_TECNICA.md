# 🏗️ Arquitetura Técnica do Chatbot

## 📐 Diagrama de Arquitetura Detalhada

```
                                    🌐 INTERNET
                                        │
                              ┌─────────▼─────────┐
                              │  WHATSAPP BUSINESS │
                              │       API          │
                              │   (Meta/Facebook)  │
                              └─────────┬─────────┘
                                        │ HTTP POST Webhook
                                        │
                              ┌─────────▼─────────┐
                              │      NGROK        │
                              │   (Túnel Local)   │
                              └─────────┬─────────┘
                                        │
                              ┌─────────▼─────────┐
                              │   DJANGO SERVER   │
                              │   (Port 8000)     │
                              └─────────┬─────────┘
                                        │
        ┌───────────────────────────────┼───────────────────────────────┐
        │                               │                               │
┌───────▼──────┐                ┌──────▼──────┐                ┌──────▼──────┐
│ API GATEWAY  │                │ FLOW AGENT  │                │ RAG AGENT   │
│              │                │             │                │             │
│ • Webhook    │                │ • Gemini AI │                │ • Models    │
│ • WhatsApp   │◄──────────────►│ • Prompts   │◄──────────────►│ • Database  │
│ • Intent     │                │ • Context   │                │ • Serializers│
│ • Middleware │                │ • Fallbacks │                │ • APIs      │
└──────────────┘                └─────────────┘                └─────────────┘
```

## 🔧 Componentes por Camada

### 1. **CAMADA DE COMUNICAÇÃO**
```
┌─────────────────────────────────────────────────────────────┐
│                    API GATEWAY                              │
├─────────────────────────────────────────────────────────────┤
│ 📁 api_gateway/                                             │
│ ├── views.py              # Webhook endpoints              │
│ ├── middleware.py         # CSRF + Logging                 │
│ ├── urls.py               # URL routing                    │
│ └── services/                                              │
│     ├── whatsapp_service.py    # WhatsApp API client       │
│     ├── intent_detection_service.py # NLP básico           │
│     └── rag_service.py          # Acesso aos dados         │
└─────────────────────────────────────────────────────────────┘
```

### 2. **CAMADA DE INTELIGÊNCIA**
```
┌─────────────────────────────────────────────────────────────┐
│                    FLOW AGENT                               │
├─────────────────────────────────────────────────────────────┤
│ 📁 flow_agent/                                              │
│ ├── models.py             # Modelos de conversa            │
│ ├── admin.py              # Interface administrativa       │
│ └── services/                                              │
│     └── gemini_service.py      # Integração Gemini AI      │
│                                                             │
│ 🤖 Responsabilidades:                                       │
│ • Geração de respostas contextualizadas                    │
│ • Prompts inteligentes baseados em intenção                │
│ • Fallbacks quando IA não está disponível                  │
│ • Histórico de conversas                                    │
└─────────────────────────────────────────────────────────────┘
```

### 3. **CAMADA DE DADOS**
```
┌─────────────────────────────────────────────────────────────┐
│                    RAG AGENT                                │
├─────────────────────────────────────────────────────────────┤
│ 📁 rag_agent/                                               │
│ ├── models.py             # Médicos, Especialidades, etc.  │
│ ├── serializers.py        # JSON serialization             │
│ ├── views.py              # REST API endpoints             │
│ ├── urls.py               # API routing                    │
│ └── migrations/           # Database schema                │
│                                                             │
│ 🗄️ Modelos de Dados:                                        │
│ • ClinicaInfo    (nome, endereço, telefone)                │
│ • Especialidade  (nome, descrição, ativa)                  │
│ • Medico         (nome, CRM, especialidades)               │
│ • Convenio       (nome, ativo)                             │
│ • Exame          (nome, descrição, preço)                  │
│ • HorarioTrabalho (médico, dia, horário)                   │
└─────────────────────────────────────────────────────────────┘
```

## 🔄 Fluxo de Execução por Arquivo

### **1. Recepção da Mensagem**
```python
# api_gateway/views.py
@csrf_exempt
@require_http_methods(["GET", "POST"])
def whatsapp_webhook(request):
    if request.method == 'GET':
        return verify_webhook(request)  # Verificação inicial
    elif request.method == 'POST':
        return handle_webhook(request)  # Processar mensagem
```

### **2. Middleware de Processamento**
```python
# api_gateway/middleware.py
class WhatsAppWebhookCSRFExemptMiddleware:
    def process_request(self, request):
        if request.path.startswith('/api/webhook/whatsapp/'):
            setattr(request, '_dont_enforce_csrf_checks', True)

class RequestLoggingMiddleware:
    def process_request(self, request):
        logger.info(f"API Request: {request.method} {request.path}")
```

### **3. Processamento da Mensagem**
```python
# api_gateway/views.py
def process_message(message, webhook_data):
    # Extrair dados
    message_id = message.get('id')
    from_number = message.get('from')
    text_content = message.get('text', {}).get('body', '')
    
    # Marcar como lida
    whatsapp_service.mark_message_as_read(message_id)
    
    # Detectar intenção
    intent, confidence = intent_service.detect_intent(text_content)
    entities = intent_service.extract_entities(text_content)
    
    # Gerar resposta
    response_text = gemini_service.generate_response(
        user_message=text_content,
        intent=intent,
        context={...},
        clinic_data=get_clinic_data()
    )
    
    # Enviar resposta
    whatsapp_service.send_message(from_number, response_text)
```

### **4. Detecção de Intenção**
```python
# api_gateway/services/intent_detection_service.py
class IntentDetectionService:
    def detect_intent(self, message: str):
        # Análise por palavras-chave
        for intent, keywords in self.intent_keywords.items():
            if any(keyword in message.lower() for keyword in keywords):
                confidence = self._calculate_confidence(message, keywords)
                return intent, confidence
        
        return 'desconhecida', 0.0
    
    def extract_entities(self, message: str):
        # Extração de entidades específicas
        entities = {}
        
        # Especialidades médicas
        for especialidade in self.especialidades:
            if especialidade.lower() in message.lower():
                entities['especialidade'] = especialidade
        
        return entities
```

### **5. Acesso aos Dados da Clínica**
```python
# api_gateway/services/rag_service.py
class RAGService:
    @staticmethod
    def get_all_clinic_data():
        return {
            'clinica_info': RAGService.get_clinic_info(),
            'especialidades': RAGService.get_especialidades(),
            'convenios': RAGService.get_convenios(),
            'medicos': RAGService.get_medicos(),
            'exames': RAGService.get_exames()
        }
    
    @staticmethod
    def get_medicos():
        medicos = Medico.objects.prefetch_related('especialidades', 'convenios')
        return MedicoResumoSerializer(medicos, many=True).data
```

### **6. Geração da Resposta com Gemini**
```python
# flow_agent/services/gemini_service.py
class GeminiService:
    def generate_response(self, user_message, intent, context=None, clinic_data=None):
        # Construir prompt contextualizado
        prompt = self._build_prompt(user_message, intent, context, clinic_data)
        
        # Gerar resposta
        response = self.model.generate_content(
            prompt,
            generation_config=self.generation_config
        )
        
        return response.text.strip()
    
    def _build_prompt(self, user_message, intent, context, clinic_data):
        system_prompt = """Você é um assistente virtual especializado..."""
        
        if clinic_data:
            system_prompt += f"\n\nInformações da clínica:\n{json.dumps(clinic_data, indent=2)}"
        
        intent_instructions = self._get_intent_instructions(intent)
        system_prompt += f"\n\nInstruções específicas: {intent_instructions}"
        system_prompt += f"\n\nMensagem do paciente: {user_message}\n\nResposta:"
        
        return system_prompt
```

### **7. Envio via WhatsApp**
```python
# api_gateway/services/whatsapp_service.py
class WhatsAppService:
    def send_message(self, to: str, message: str):
        url = f"{self.api_url}/{self.phone_number_id}/messages"
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        data = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": message}
        }
        
        response = requests.post(url, headers=headers, json=data)
        return response.status_code == 200
```

## 🗄️ Estrutura do Banco de Dados

```sql
-- Informações da Clínica
CREATE TABLE rag_agent_clinicainfo (
    id INTEGER PRIMARY KEY,
    nome VARCHAR(200),
    endereco TEXT,
    telefone VARCHAR(20),
    email VARCHAR(254),
    horario_funcionamento TEXT,
    whatsapp_contato VARCHAR(20)
);

-- Especialidades Médicas
CREATE TABLE rag_agent_especialidade (
    id INTEGER PRIMARY KEY,
    nome VARCHAR(100) UNIQUE,
    descricao TEXT,
    ativa BOOLEAN DEFAULT TRUE
);

-- Médicos
CREATE TABLE rag_agent_medico (
    id INTEGER PRIMARY KEY,
    nome VARCHAR(200),
    crm VARCHAR(20) UNIQUE,
    telefone VARCHAR(20),
    email VARCHAR(254)
);

-- Relação Médico-Especialidade (Many-to-Many)
CREATE TABLE rag_agent_medico_especialidades (
    id INTEGER PRIMARY KEY,
    medico_id INTEGER REFERENCES rag_agent_medico(id),
    especialidade_id INTEGER REFERENCES rag_agent_especialidade(id)
);

-- Convênios
CREATE TABLE rag_agent_convenio (
    id INTEGER PRIMARY KEY,
    nome VARCHAR(100) UNIQUE
);

-- Exames
CREATE TABLE rag_agent_exame (
    id INTEGER PRIMARY KEY,
    nome VARCHAR(200),
    descricao TEXT,
    preco DECIMAL(10,2),
    duracao_minutos INTEGER
);

-- Horários de Trabalho
CREATE TABLE rag_agent_horariotrabalho (
    id INTEGER PRIMARY KEY,
    medico_id INTEGER REFERENCES rag_agent_medico(id),
    dia_semana INTEGER,  -- 0=Segunda, 6=Domingo
    hora_inicio TIME,
    hora_fim TIME
);
```

## ⚡ Configurações de Performance

### **Django Settings**
```python
# core/settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Cache para consultas frequentes
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Logging detalhado
LOGGING = {
    'version': 1,
    'loggers': {
        'api_gateway': {'level': 'DEBUG'},
        'flow_agent': {'level': 'DEBUG'},
    }
}
```

### **Gemini Configuration**
```python
# Configurações otimizadas
GEMINI_MODEL = 'gemini-1.5-flash'  # Modelo mais rápido
GEMINI_TEMPERATURE = 0.7           # Criatividade moderada
GEMINI_MAX_TOKENS = 1024           # Respostas concisas
```

## 🔐 Segurança Implementada

1. **Webhook Verification**: Token de verificação do Meta
2. **CSRF Exemption**: Apenas para endpoint específico
3. **Environment Variables**: Chaves sensíveis no .env
4. **Input Sanitization**: Validação de dados de entrada
5. **Rate Limiting**: Controle de frequência (futuro)
6. **Error Handling**: Logs detalhados sem exposição de dados

## 📊 Monitoramento e Logs

```python
# Logs estruturados
logger.info(f"Mensagem recebida de {from_number}: {text_content[:50]}...")
logger.info(f"Intenção detectada: {intent} (confiança: {confidence})")
logger.info(f"Resposta enviada com sucesso para {from_number}")
logger.error(f"Erro ao processar mensagem: {e}")
```

## 🚀 Deployment e Escalabilidade

### **Desenvolvimento**
- Django Development Server (port 8000)
- ngrok para túnel público
- SQLite database
- Logs no console

### **Produção (Futuro)**
- Gunicorn + Nginx
- PostgreSQL database
- Redis cache
- Celery para tasks assíncronas
- Docker containers
- Load balancer
