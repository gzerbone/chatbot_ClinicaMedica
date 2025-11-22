# 🔗 Integração com APIs Externas - Chatbot Clínica Médica

## 📱 WhatsApp Business API

### **Configuração Inicial**

#### **1. Criar Conta WhatsApp Business**
1. Acesse [WhatsApp Business API](https://business.whatsapp.com/)
2. Crie conta empresarial
3. Configure número de telefone
4. Obtenha tokens de acesso

#### **2. Configuração de Webhook**
```python
# api_gateway/views.py
@csrf_exempt
def whatsapp_webhook(request):
    if request.method == 'GET':
        # Verificação do webhook
        verify_token = settings.WHATSAPP_VERIFY_TOKEN
        if request.GET.get('hub.verify_token') == verify_token:
            return HttpResponse(request.GET.get('hub.challenge'))
        return HttpResponse('Error', status=400)
    
    elif request.method == 'POST':
        # Processamento de mensagens
        data = json.loads(request.body)
        # Lógica de processamento
        return HttpResponse('OK')
```

#### **3. Variáveis de Ambiente**
```env
# WhatsApp Business
WHATSAPP_TOKEN=seu-token-aqui
WHATSAPP_VERIFY_TOKEN=seu-verify-token
WHATSAPP_PHONE_NUMBER_ID=seu-phone-number-id
```

### **Envio de Mensagens**

#### **Serviço WhatsApp**
```python
# api_gateway/services/whatsapp_service.py
class WhatsAppService:
    def __init__(self):
        self.token = settings.WHATSAPP_TOKEN
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        self.base_url = f"https://graph.facebook.com/v18.0/{self.phone_number_id}/messages"
    
    def send_message(self, to, message):
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'messaging_product': 'whatsapp',
            'to': to,
            'type': 'text',
            'text': {'body': message}
        }
        
        response = requests.post(self.base_url, headers=headers, json=data)
        return response.json()
```

### **Recebimento de Mensagens**

#### **Processamento de Webhook**
```python
def process_whatsapp_message(data):
    """
    Processa mensagem recebida do WhatsApp
    """
    for entry in data.get('entry', []):
        for change in entry.get('changes', []):
            if change.get('field') == 'messages':
                for message in change.get('value', {}).get('messages', []):
                    phone_number = message.get('from')
                    message_text = message.get('text', {}).get('body', '')
                    
                    # Processar com Gemini
                    response = gemini_service.process_message(message_text, phone_number)
                    
                    # Enviar resposta
                    whatsapp_service.send_message(phone_number, response)
```

## 🤖 Google Gemini AI

### **Configuração Inicial**

#### **1. Criar Projeto Google Cloud**
1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Crie novo projeto
3. Ative Gemini AI API
4. Gere chave de API

#### **2. Configuração do Serviço**
```python
# api_gateway/services/gemini/core_service.py (modularizado - antes era gemini_chatbot_service.py)
import google.generativeai as genai

class GeminiChatbotService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
    
    def process_message(self, message, phone_number):
        """
        Processa mensagem com Gemini AI
        """
        # Obter contexto da sessão
        session = conversation_service.get_or_create_session(phone_number)
        
        # Obter dados RAG
        rag_data = rag_service.get_clinic_info()
        
        # Prompt contextualizado
        prompt = self.build_contextual_prompt(message, session, rag_data)
        
        # Gerar resposta
        response = self.model.generate_content(prompt)
        
        return response.text
```

### **Sistema RAG (Retrieval Augmented Generation)**

#### **Integração com Base de Conhecimento**
```python
# api_gateway/services/rag_service.py
class RAGService:
    def get_clinic_info(self):
        """
        Obtém informações da clínica para contexto
        """
        cache_key = "clinic_info"
        cached_data = cache.get(cache_key)
        
        if not cached_data:
            # Buscar dados do banco
            clinic = ClinicaInfo.objects.first()
            doctors = Medico.objects.all()
            specialties = Especialidade.objects.filter(ativa=True)
            
            cached_data = {
                'clinic': {
                    'nome': clinic.nome,
                    'endereco': clinic.endereco,
                    'telefone': clinic.telefone_contato,
                    'whatsapp': clinic.whatsapp_contato
                },
                'doctors': [{'nome': d.nome, 'especialidades': d.get_especialidades_display()} for d in doctors],
                'specialties': [s.nome for s in specialties]
            }
            
            cache.set(cache_key, cached_data, 3600)  # 1 hora
        
        return cached_data
```

### **Prompt Engineering**

#### **Template de Prompt**
```python
def build_contextual_prompt(self, message, session, rag_data):
    """
    Constrói prompt contextualizado para Gemini
    """
    prompt = f"""
    Você é o assistente virtual da {rag_data['clinic']['nome']}.
    
    INFORMAÇÕES DA CLÍNICA:
    - Nome: {rag_data['clinic']['nome']}
    - Endereço: {rag_data['clinic']['endereco']}
    - WhatsApp: {rag_data['clinic']['whatsapp']}
    
    MÉDICOS DISPONÍVEIS:
    {self.format_doctors(rag_data['doctors'])}
    
    ESPECIALIDADES:
    {', '.join(rag_data['specialties'])}
    
    ESTADO ATUAL DA CONVERSA:
    - Paciente: {session.patient_name or 'Não informado'}
    - Estado: {session.current_state}
    - Especialidade de interesse: {session.selected_specialty or 'Não definida'}
    
    MENSAGEM DO PACIENTE: {message}
    
    Responda de forma natural e útil, ajudando com agendamento de consultas.
    """
    
    return prompt
```

## 📅 Google Calendar API

### **Configuração Inicial**

#### **1. Ativar Calendar API**
1. No Google Cloud Console
2. Ative Google Calendar API
3. Crie credenciais (Service Account)
4. Baixe arquivo JSON

#### **2. Configuração do Serviço**
```python
# api_gateway/services/google_calendar_service.py
from google.oauth2 import service_account
from googleapiclient.discovery import build

class GoogleCalendarService:
    def __init__(self):
        self.credentials_file = settings.GOOGLE_CALENDAR_CREDENTIALS_FILE
        self.calendar_id = settings.GOOGLE_CALENDAR_ID
        
        # Configurar credenciais
        credentials = service_account.Credentials.from_service_account_file(
            self.credentials_file,
            scopes=['https://www.googleapis.com/auth/calendar']
        )
        
        self.service = build('calendar', 'v3', credentials=credentials)
```

### **Consultar Disponibilidade**

#### **Verificar Horários Livres**
```python
def get_availability(self, date, doctor_name=None):
    """
    Consulta disponibilidade no Google Calendar
    """
    # Definir período de consulta
    start_time = f"{date}T00:00:00-03:00"
    end_time = f"{date}T23:59:59-03:00"
    
    # Consultar eventos
    events_result = self.service.events().list(
        calendarId=self.calendar_id,
        timeMin=start_time,
        timeMax=end_time,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    
    events = events_result.get('items', [])
    
    # Processar horários disponíveis
    available_slots = self.calculate_available_slots(events, date)
    
    return available_slots
```

### **Criar Evento**

#### **Agendar Consulta**
```python
def create_appointment(self, patient_name, doctor_name, date, time, duration=60):
    """
    Cria evento no Google Calendar
    """
    event = {
        'summary': f'Consulta - {patient_name}',
        'description': f'Paciente: {patient_name}\nMédico: {doctor_name}',
        'start': {
            'dateTime': f"{date}T{time}:00-03:00",
            'timeZone': 'America/Sao_Paulo',
        },
        'end': {
            'dateTime': f"{date}T{time + duration}:00-03:00",
            'timeZone': 'America/Sao_Paulo',
        },
        'attendees': [
            {'email': 'clinica@email.com'},
        ],
    }
    
    created_event = self.service.events().insert(
        calendarId=self.calendar_id,
        body=event
    ).execute()
    
    return created_event
```

## 🔧 Configuração de Desenvolvimento

### **Ngrok para Webhook Local**

#### **Instalação**
```bash
# Download ngrok
# https://ngrok.com/download

# Configurar token
ngrok config add-authtoken seu-token-ngrok
```

#### **Executar Túnel**
```bash
# Túnel para porta 8000
ngrok http 8000

# URL será: https://abc123.ngrok-free.app
```

#### **Configurar Webhook**
```
URL: https://abc123.ngrok-free.app/api/whatsapp/webhook/
Token: seu-verify-token
```

### **Variáveis de Ambiente Completas**

#### **Arquivo .env**
```env
# Django
SECRET_KEY=sua-secret-key
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

## 🧪 Testes de Integração

### **Teste WhatsApp**
```python
# tests/api_gateway/test_webhook_integration.py
def test_whatsapp_webhook(self):
    """
    Testa recebimento de webhook WhatsApp
    """
    webhook_data = {
        'entry': [{
            'changes': [{
                'value': {
                    'messages': [{
                        'from': '5511999999999',
                        'text': {'body': 'Olá, quero agendar consulta'}
                    }]
                }
            }]
        }]
    }
    
    response = self.client.post('/api/whatsapp/webhook/', 
                               json.dumps(webhook_data),
                               content_type='application/json')
    
    self.assertEqual(response.status_code, 200)
```

### **Teste Gemini AI**
```python
def test_gemini_response(self):
    """
    Testa resposta do Gemini AI
    """
    service = GeminiChatbotService()
    response = service.process_message("Olá", "5511999999999")
    
    self.assertIsNotNone(response)
    self.assertIsInstance(response, str)
```

### **Teste Google Calendar**
```python
def test_calendar_availability(self):
    """
    Testa consulta de disponibilidade
    """
    service = GoogleCalendarService()
    availability = service.get_availability('2024-01-15')
    
    self.assertIsNotNone(availability)
    self.assertIsInstance(availability, list)
```

## 🚨 Tratamento de Erros

### **WhatsApp API**
```python
def send_message_with_retry(self, to, message, max_retries=3):
    """
    Envia mensagem com retry automático
    """
    for attempt in range(max_retries):
        try:
            response = self.send_message(to, message)
            if response.get('error'):
                raise Exception(f"WhatsApp API Error: {response['error']}")
            return response
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"Falha ao enviar mensagem após {max_retries} tentativas: {e}")
                raise
            time.sleep(2 ** attempt)  # Backoff exponencial
```

### **Gemini AI**
```python
def process_message_with_fallback(self, message, phone_number):
    """
    Processa mensagem com fallback
    """
    try:
        return self.gemini_service.process_message(message, phone_number)
    except Exception as e:
        logger.error(f"Erro no Gemini AI: {e}")
        return "Desculpe, estou com dificuldades técnicas. Tente novamente em alguns minutos."
```

### **Google Calendar**
```python
def get_availability_with_fallback(self, date):
    """
    Consulta disponibilidade com fallback
    """
    try:
        return self.calendar_service.get_availability(date)
    except Exception as e:
        logger.error(f"Erro no Google Calendar: {e}")
        return self.get_default_availability(date)
```

## 📊 Monitoramento

### **Métricas de API**
- **Taxa de sucesso** WhatsApp
- **Latência** Gemini AI
- **Disponibilidade** Google Calendar
- **Erros** por integração

### **Logs Estruturados**
```python
import logging

# Logger específico para integrações
integration_logger = logging.getLogger('integration')

def log_api_call(service, endpoint, status, duration):
    integration_logger.info({
        'service': service,
        'endpoint': endpoint,
        'status': status,
        'duration_ms': duration,
        'timestamp': timezone.now().isoformat()
    })
```

---

**Este guia fornece todas as informações necessárias para configurar e manter as integrações com APIs externas.**
