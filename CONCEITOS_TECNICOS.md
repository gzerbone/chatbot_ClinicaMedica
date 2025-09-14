# 📚 Conceitos Técnicos do Projeto - Chatbot Clínica Médica

Este documento explica todos os conceitos técnicos utilizados no desenvolvimento do chatbot, desde os mais básicos até os mais avançados, com exemplos práticos do nosso projeto.

---

## 🌐 **CONCEITOS DE REDE E WEB**

### **API (Application Programming Interface)**

**O que é:**
Uma API é um conjunto de regras e protocolos que permite que diferentes aplicações se comuniquem entre si. É como um "garçom" que leva pedidos de um cliente (aplicação) para a cozinha (servidor) e traz a resposta de volta.

**No nosso projeto:**
```python
# Exemplo: WhatsApp Business API
POST https://graph.facebook.com/v18.0/{phone_number_id}/messages
{
    "messaging_product": "whatsapp",
    "to": "5511999999999",
    "type": "text",
    "text": {"body": "Olá! Como posso ajudar?"}
}
```

**Características:**
- **Interface padronizada** para comunicação
- **Abstração** da complexidade interna
- **Reutilização** de funcionalidades
- **Interoperabilidade** entre sistemas diferentes

---

### **API REST (REpresentational State Transfer)**

**O que é:**
REST é um estilo arquitetural para APIs que usa HTTP de forma padronizada. Segue princípios específicos como stateless (sem estado), uso correto de verbos HTTP, e recursos identificados por URLs.

**Princípios REST:**
1. **Stateless**: Cada requisição é independente
2. **Client-Server**: Separação clara de responsabilidades
3. **Cacheable**: Respostas podem ser cacheadas
4. **Uniform Interface**: Interface consistente

**No nosso projeto:**
```python
# rag_agent/views.py - Endpoints REST
GET /rag/especialidades/     # Lista especialidades
GET /rag/medicos/           # Lista médicos  
GET /rag/medicos/1/         # Detalhes do médico ID 1
GET /rag/clinica/           # Informações da clínica

# Seguindo padrões REST:
# GET = Buscar dados
# POST = Criar dados
# PUT = Atualizar dados
# DELETE = Remover dados
```

**Vantagens:**
- **Simplicidade** e facilidade de uso
- **Escalabilidade** através do stateless
- **Padronização** reconhecida mundialmente
- **Cache** nativo do HTTP

---

### **Endpoint**

**O que é:**
Um endpoint é um ponto de acesso específico de uma API. É uma URL que aceita requisições e retorna dados ou executa ações. Cada endpoint tem uma função específica.

**Estrutura típica:**
```
[MÉTODO] [BASE_URL]/[RECURSO]/[PARÂMETROS]
GET https://api.clinica.com/medicos/1
```

**No nosso projeto:**
```python
# api_gateway/urls.py
urlpatterns = [
    # Webhook do WhatsApp
    path('webhook/whatsapp/', views.whatsapp_webhook, name='whatsapp_webhook'),
    
    # Endpoints de teste
    path('test/send-message/', views.send_test_message, name='send_test_message'),
    path('test/gemini/', views.test_gemini_connection, name='test_gemini'),
    path('test/intent/', views.test_intent_detection, name='test_intent'),
]

# rag_agent/urls.py  
urlpatterns = [
    path('especialidades/', EspecialidadeListView.as_view(), name='especialidades-list'),
    path('medicos/', MedicoViewSet.as_view({'get': 'list'}), name='medicos-list'),
    path('clinica/', ClinicaInfoView.as_view(), name='clinica-info'),
]
```

**Tipos de endpoints no projeto:**
- **Webhook**: Recebe dados externos (WhatsApp)
- **REST**: Fornece dados estruturados (médicos, especialidades)
- **Teste**: Valida funcionamento do sistema

---

## 🚪 **GATEWAY E MIDDLEWARE**

### **API Gateway**

**O que é:**
Um API Gateway é um ponto de entrada único que gerencia, roteia e processa todas as requisições para diferentes serviços de backend. Atua como um "porteiro" inteligente.

**Funções principais:**
- **Roteamento** de requisições
- **Autenticação** e autorização
- **Rate limiting** (controle de frequência)
- **Logging** e monitoramento
- **Transformação** de dados

**No nosso projeto:**
```python
# api_gateway/ - Nosso Gateway
├── views.py              # Processamento principal
├── middleware.py         # Interceptação de requisições  
├── services/            # Serviços especializados
│   ├── whatsapp_service.py    # Comunicação WhatsApp
│   ├── intent_detection_service.py  # Análise de intenções
│   └── rag_service.py         # Acesso aos dados
└── urls.py              # Roteamento

# Fluxo do Gateway:
WhatsApp → API Gateway → Flow Agent (Gemini) → RAG Agent (Dados) → Resposta
```

**Vantagens:**
- **Centralização** do controle de acesso
- **Abstração** da complexidade interna
- **Monitoramento** centralizado
- **Segurança** em camadas

---

### **Middleware**

**O que é:**
Middleware é um software que fica entre diferentes componentes, interceptando e processando requisições antes que cheguem ao destino final. É como uma "esteira de produção" onde cada middleware executa uma função específica.

**Como funciona:**
```
Requisição → Middleware 1 → Middleware 2 → Middleware 3 → View → Resposta
                ↑              ↑              ↑
            CORS         Autenticação    Logging
```

**No nosso projeto:**
```python
# core/settings.py
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',                    # 1. CORS
    'django.middleware.security.SecurityMiddleware',           # 2. Segurança
    'django.contrib.sessions.middleware.SessionMiddleware',    # 3. Sessões
    'django.middleware.common.CommonMiddleware',               # 4. Comum
    'api_gateway.middleware.WhatsAppWebhookCSRFExemptMiddleware', # 5. CSRF Custom
    'django.middleware.csrf.CsrfViewMiddleware',              # 6. CSRF
    'django.contrib.auth.middleware.AuthenticationMiddleware', # 7. Autenticação
    'django.contrib.messages.middleware.MessageMiddleware',    # 8. Mensagens
    'django.middleware.clickjacking.XFrameOptionsMiddleware',  # 9. Clickjacking
    'api_gateway.middleware.RequestLoggingMiddleware',         # 10. Logging Custom
]

# api_gateway/middleware.py - Nossos middlewares customizados
class WhatsAppWebhookCSRFExemptMiddleware(MiddlewareMixin):
    """Desabilita CSRF apenas para webhook do WhatsApp"""
    
    def process_request(self, request):
        if request.path.startswith('/api/webhook/whatsapp/'):
            setattr(request, '_dont_enforce_csrf_checks', True)
            logger.debug("CSRF check disabled for WhatsApp webhook")

class RequestLoggingMiddleware(MiddlewareMixin):
    """Registra logs de todas as requisições da API"""
    
    def process_request(self, request):
        if request.path.startswith('/api/'):
            logger.info(f"API Request: {request.method} {request.path}")
    
    def process_response(self, request, response):
        if request.path.startswith('/api/'):
            logger.info(f"API Response: {response.status_code}")
        return response
```

**Tipos de middleware:**
- **Segurança**: CSRF, XSS, autenticação
- **Logging**: Registro de atividades
- **CORS**: Controle de acesso cross-origin
- **Custom**: Funcionalidades específicas do projeto

---

## 🔗 **WEBHOOK**

**O que é:**
Um webhook é um mecanismo que permite que uma aplicação envie dados automaticamente para outra aplicação quando um evento específico ocorre. É como uma "campainha" que toca quando algo acontece.

**Diferença entre API e Webhook:**
```
API (Pull):     Cliente → Servidor (Cliente puxa dados)
Webhook (Push): Servidor → Cliente (Servidor empurra dados)
```

**No nosso projeto:**
```python
# WhatsApp → Nosso Webhook quando paciente envia mensagem
POST /api/webhook/whatsapp/
{
  "entry": [{
    "changes": [{
      "field": "messages",
      "value": {
        "messages": [{
          "id": "wamid.123",
          "from": "5511999999999",
          "text": {"body": "Olá, preciso de ajuda"}
        }]
      }
    }]
  }]
}

# api_gateway/views.py
@csrf_exempt  # Webhook não pode ter CSRF
@require_http_methods(["GET", "POST"])
def whatsapp_webhook(request):
    if request.method == 'GET':
        return verify_webhook(request)  # Verificação inicial
    elif request.method == 'POST':
        return handle_webhook(request)  # Processar mensagem
```

**Características:**
- **Tempo real**: Dados chegam imediatamente
- **Event-driven**: Baseado em eventos
- **Eficiiente**: Não há polling desnecessário
- **Assíncrono**: Não bloqueia outras operações

**Configuração no Meta (WhatsApp):**
```
Callback URL: https://sua-url.ngrok-free.app/api/webhook/whatsapp/
Verify Token: meu_verify_token_123
Events: messages (quando paciente envia mensagem)
```

---

## 📝 **LOGGING**

**O que é:**
Logging é o processo de registrar eventos, erros e informações importantes que ocorrem durante a execução de uma aplicação. É como um "diário" detalhado do sistema.

**Níveis de Log:**
```
DEBUG    → Informações detalhadas para debugging
INFO     → Informações gerais sobre o funcionamento
WARNING  → Algo inesperado, mas não crítico
ERROR    → Erro que impediu uma operação
CRITICAL → Erro grave que pode parar o sistema
```

**No nosso projeto:**
```python
# core/settings.py - Configuração do logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'api_gateway': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'flow_agent': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Uso nos arquivos Python
import logging
logger = logging.getLogger(__name__)

# Exemplos de uso:
logger.info(f"Mensagem recebida de {from_number}")
logger.debug(f"Intent detectado: {intent} (confiança: {confidence})")
logger.warning("GEMINI_API_KEY não configurada")
logger.error(f"Erro ao enviar mensagem: {e}")
```

**Saída dos logs:**
```
INFO api_gateway.views: Mensagem recebida de 5511999999999
DEBUG api_gateway.services.intent_detection: Intent: buscar_medico (0.85)
INFO api_gateway.services.whatsapp: Mensagem enviada com sucesso
```

**Benefícios:**
- **Debugging**: Identificar problemas
- **Monitoramento**: Acompanhar performance
- **Auditoria**: Rastrear atividades
- **Analytics**: Entender padrões de uso

---

## 🛠️ **SERVICES (CAMADA DE SERVIÇOS)**

**O que é:**
Services são classes que encapsulam lógica de negócio específica, mantendo o código organizado e reutilizável. É como ter "especialistas" para cada tipo de tarefa.

**Padrão Service:**
```
Controller (View) → Service → Model/External API → Response
```

**No nosso projeto:**
```python
# api_gateway/services/ - Nossos serviços

# 1. WhatsApp Service - Comunicação com WhatsApp API
class WhatsAppService:
    def send_message(self, to: str, message: str) -> bool:
        """Envia mensagem via WhatsApp Business API"""
        
    def mark_message_as_read(self, message_id: str) -> bool:
        """Marca mensagem como lida"""
        
    def validate_webhook(self, mode: str, token: str, challenge: str) -> str:
        """Valida webhook do WhatsApp"""

# 2. Intent Detection Service - Análise de intenções
class IntentDetectionService:
    def detect_intent(self, message: str) -> tuple:
        """Detecta intenção da mensagem do usuário"""
        
    def extract_entities(self, message: str) -> dict:
        """Extrai entidades (nomes, especialidades, etc.)"""

# 3. RAG Service - Acesso aos dados da clínica  
class RAGService:
    @staticmethod
    def get_all_clinic_data() -> dict:
        """Obtém todos os dados da clínica"""
        
    @staticmethod
    def get_medicos() -> list:
        """Busca médicos disponíveis"""

# flow_agent/services/
# 4. Gemini Service - Integração com IA
class GeminiService:
    def generate_response(self, user_message, intent, context, clinic_data):
        """Gera resposta usando Gemini AI"""
        
    def test_connection(self) -> bool:
        """Testa conexão com Gemini"""
```

**Vantagens dos Services:**
- **Separação de responsabilidades**
- **Reutilização** de código
- **Testabilidade** individual
- **Manutenibilidade** melhorada
- **Abstração** de complexidade

---

## 🏗️ **ARQUITETURA MVC/MVT**

**O que é:**
MVC (Model-View-Controller) ou MVT (Model-View-Template) no Django é um padrão arquitetural que separa a aplicação em três camadas distintas.

**Django MVT:**
```
Model    → Dados e lógica de negócio (models.py)
View     → Lógica de apresentação (views.py)  
Template → Interface do usuário (templates/)
```

**No nosso projeto:**
```python
# MODEL - rag_agent/models.py
class Medico(models.Model):
    nome = models.CharField(max_length=200)
    crm = models.CharField(max_length=20, unique=True)
    especialidades = models.ManyToManyField(Especialidade)

# VIEW - api_gateway/views.py  
def whatsapp_webhook(request):
    """Processa webhooks do WhatsApp"""
    if request.method == 'POST':
        return handle_webhook(request)

# SERIALIZER (equivalente ao Template para APIs)
class MedicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medico
        fields = ['id', 'nome', 'crm', 'especialidades']
```

**Fluxo MVT no projeto:**
```
WhatsApp → View (webhook) → Service → Model → Serializer → JSON Response
```

---

## 📊 **SERIALIZERS (DRF)**

**O que é:**
Serializers convertem dados complexos (como instâncias de modelo Django) em tipos nativos Python que podem ser facilmente renderizados em JSON, XML ou outros formatos.

**Funções:**
- **Serialização**: Model → JSON
- **Deserialização**: JSON → Model
- **Validação**: Dados de entrada
- **Transformação**: Formatação de dados

**No nosso projeto:**
```python
# rag_agent/serializers.py
class MedicoResumoSerializer(serializers.ModelSerializer):
    """Serializer resumido para listagem de médicos"""
    especialidades = serializers.StringRelatedField(many=True, read_only=True)
    
    class Meta:
        model = Medico
        fields = ['id', 'nome', 'crm', 'especialidades']

class MedicoSerializer(serializers.ModelSerializer):
    """Serializer completo com todos os detalhes"""
    especialidades = EspecialidadeSerializer(many=True, read_only=True)
    convenios = ConvenioSerializer(many=True, read_only=True)
    horarios_trabalho = HorarioTrabalhoSerializer(many=True, read_only=True)
    
    class Meta:
        model = Medico
        fields = '__all__'

# Uso nos Services:
medicos = Medico.objects.all()
serialized_data = MedicoResumoSerializer(medicos, many=True).data
# Resultado: [{"id": 1, "nome": "Dr. João", "crm": "123456", ...}]
```

**Vantagens:**
- **Automação** da conversão de dados
- **Validação** integrada
- **Flexibilidade** de campos
- **Consistência** na API

---

## 🔄 **DJANGO REST FRAMEWORK (DRF)**

**O que é:**
DRF é um toolkit poderoso e flexível para construir APIs REST no Django. Fornece componentes prontos para serialização, autenticação, permissões e muito mais.

**Componentes principais:**
```python
# 1. ViewSets - Conjuntos de views relacionadas
class MedicoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Medico.objects.all()
    serializer_class = MedicoSerializer

# 2. Generic Views - Views pré-construídas
class EspecialidadeListView(generics.ListAPIView):
    queryset = Especialidade.objects.filter(ativa=True)
    serializer_class = EspecialidadeSerializer

# 3. Function-based Views com decorators
@api_view(['GET'])
@permission_classes([AllowAny])
def test_gemini_connection(request):
    return Response({'status': 'OK'})

# 4. Routers - Roteamento automático
router = DefaultRouter()
router.register(r'medicos', MedicoViewSet)
urlpatterns = router.urls
```

**Features utilizadas no projeto:**
- **Serializers**: Conversão de dados
- **Generic Views**: Views padronizadas
- **Permissions**: Controle de acesso
- **Response**: Respostas HTTP estruturadas

---

## 🗄️ **ORM (Object-Relational Mapping)**

**O que é:**
ORM é uma técnica que permite manipular banco de dados usando programação orientada a objetos, sem escrever SQL diretamente.

**Django ORM:**
```python
# Sem ORM (SQL puro):
cursor.execute("SELECT * FROM medico WHERE especialidade = 'Cardiologia'")

# Com ORM Django:
medicos = Medico.objects.filter(especialidades__nome='Cardiologia')

# Exemplos do projeto:
# rag_agent/models.py
class Medico(models.Model):
    nome = models.CharField(max_length=200)
    crm = models.CharField(max_length=20, unique=True)
    especialidades = models.ManyToManyField(Especialidade)
    
    def __str__(self):
        return self.nome

# Queries complexas:
medicos_cardiologia = Medico.objects.filter(
    especialidades__nome='Cardiologia',
    especialidades__ativa=True
).prefetch_related('convenios', 'horarios_trabalho')

# Relacionamentos:
medico = Medico.objects.get(id=1)
especialidades = medico.especialidades.all()  # Many-to-Many
horarios = medico.horarios_trabalho.all()     # Foreign Key reversa
```

**Vantagens:**
- **Abstração** do SQL
- **Portabilidade** entre bancos
- **Segurança** contra SQL injection
- **Produtividade** no desenvolvimento

---

## 🔐 **CSRF (Cross-Site Request Forgery)**

**O que é:**
CSRF é um tipo de ataque onde um site malicioso executa ações não autorizadas em nome de um usuário autenticado em outro site.

**Como funciona:**
```
1. Usuário faz login no site A
2. Usuário visita site malicioso B  
3. Site B faz requisição para site A usando credenciais do usuário
4. Site A executa ação não autorizada
```

**Proteção no Django:**
```python
# Django adiciona token CSRF automaticamente
{% csrf_token %}  # Em templates

# Em views, o middleware verifica o token
'django.middleware.csrf.CsrfViewMiddleware'

# Para APIs externas (webhooks), desabilitamos:
@csrf_exempt
def whatsapp_webhook(request):
    # WhatsApp não pode enviar token CSRF
    pass

# Ou via middleware customizado:
class WhatsAppWebhookCSRFExemptMiddleware:
    def process_request(self, request):
        if request.path.startswith('/api/webhook/whatsapp/'):
            setattr(request, '_dont_enforce_csrf_checks', True)
```

---

## 🌍 **CORS (Cross-Origin Resource Sharing)**

**O que é:**
CORS é um mecanismo que permite que recursos de uma página web sejam acessados por outro domínio, protocolo ou porta.

**Problema sem CORS:**
```
Frontend (localhost:3000) → API (localhost:8000) = ❌ BLOQUEADO
```

**Solução com CORS:**
```python
# core/settings.py
INSTALLED_APPS = [
    'corsheaders',  # Instalar django-cors-headers
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Primeiro middleware
]

# Configuração para desenvolvimento
CORS_ALLOW_ALL_ORIGINS = True

# Configuração para produção
CORS_ALLOWED_ORIGINS = [
    "https://meusite.com",
    "https://app.meusite.com",
]
```

---

## 🔧 **ENVIRONMENT VARIABLES**

**O que é:**
Variáveis de ambiente são valores configuráveis externamente à aplicação, usadas para armazenar configurações sensíveis como chaves de API.

**No nosso projeto:**
```python
# .env (não vai para o Git)
DEBUG=True
SECRET_KEY=django-insecure-abc123
GEMINI_API_KEY=AIzaSyC-sua-chave-aqui
WHATSAPP_ACCESS_TOKEN=EAABs...token-longo
WHATSAPP_VERIFY_TOKEN=meu_verify_token_123

# core/settings.py
from decouple import config

DEBUG = config('DEBUG', default=False, cast=bool)
SECRET_KEY = config('SECRET_KEY')
GEMINI_API_KEY = config('GEMINI_API_KEY', default='')

# Uso nos services:
class GeminiService:
    def __init__(self):
        self.api_key = getattr(settings, 'GEMINI_API_KEY', '')
```

**Benefícios:**
- **Segurança**: Chaves não ficam no código
- **Flexibilidade**: Diferentes configs por ambiente
- **Praticidade**: Mudanças sem redeployment

---

## 🤖 **INTELIGÊNCIA ARTIFICIAL INTEGRADA**

### **LLM (Large Language Model)**

**O que é:**
LLMs são modelos de IA treinados em grandes volumes de texto para entender e gerar linguagem natural humana.

**Gemini AI no projeto:**
```python
# flow_agent/services/gemini_service.py
import google.generativeai as genai

class GeminiService:
    def __init__(self):
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def generate_response(self, user_message, intent, context, clinic_data):
        # Construir prompt contextualizado
        prompt = f"""
        Você é um assistente virtual de uma clínica médica.
        
        Dados da clínica: {clinic_data}
        Intenção do usuário: {intent}
        Mensagem: {user_message}
        
        Responda de forma profissional e útil.
        """
        
        response = self.model.generate_content(prompt)
        return response.text
```

### **RAG (Retrieval-Augmented Generation)**

**O que é:**
RAG combina recuperação de informações com geração de texto, permitindo que a IA acesse dados específicos para dar respostas mais precisas.

**No nosso projeto:**
```python
# 1. RETRIEVAL - Buscar dados relevantes
clinic_data = RAGService.get_all_clinic_data()
medicos_cardiologia = RAGService.get_medicos_por_especialidade('cardiologia')

# 2. AUGMENTATION - Enriquecer prompt com dados
prompt = f"""
Dados da clínica: {clinic_data}
Médicos disponíveis: {medicos_cardiologia}
Pergunta do usuário: {user_message}
"""

# 3. GENERATION - Gerar resposta contextualizada
response = gemini_service.generate_response(prompt)
```

### **NLP (Natural Language Processing)**

**O que é:**
NLP é a capacidade de computadores entenderem e processarem linguagem humana.

**No projeto:**
```python
# api_gateway/services/intent_detection_service.py
class IntentDetectionService:
    def __init__(self):
        self.intent_keywords = {
            'buscar_medico': ['médico', 'doutor', 'dr', 'dra'],
            'agendar_consulta': ['agendar', 'marcar', 'consulta'],
            'buscar_especialidade': ['especialidade', 'cardiologista', 'dermatologista'],
        }
    
    def detect_intent(self, message: str):
        message_lower = message.lower()
        
        for intent, keywords in self.intent_keywords.items():
            matches = sum(1 for keyword in keywords if keyword in message_lower)
            if matches > 0:
                confidence = min(matches / len(keywords) * 2, 1.0)
                return intent, confidence
        
        return 'desconhecida', 0.0
```

---

## 📈 **MONITORAMENTO E MÉTRICAS**

### **Health Check**

**O que é:**
Endpoints que verificam se o sistema está funcionando corretamente.

```python
# api_gateway/views.py
@api_view(['GET'])
def health_check(request):
    """Verifica saúde do sistema"""
    checks = {
        'database': test_database_connection(),
        'gemini': gemini_service.test_connection(),
        'whatsapp': test_whatsapp_connection(),
    }
    
    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 503
    
    return Response({
        'status': 'healthy' if all_healthy else 'unhealthy',
        'checks': checks,
        'timestamp': timezone.now()
    }, status=status_code)
```

### **Métricas de Performance**

```python
import time
from functools import wraps

def measure_time(func):
    """Decorator para medir tempo de execução"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        logger.info(f"{func.__name__} executado em {end_time - start_time:.2f}s")
        return result
    return wrapper

@measure_time
def generate_response(self, user_message, intent, context, clinic_data):
    # Função medida automaticamente
    pass
```

---

## 🔄 **PADRÕES DE DESIGN UTILIZADOS**

### **1. Service Layer Pattern**
```python
# Separação de responsabilidades
View → Service → Model
```

### **2. Repository Pattern**
```python
# RAGService atua como repository
class RAGService:
    @staticmethod
    def get_medicos():
        return Medico.objects.all()
```

### **3. Factory Pattern**
```python
# GeminiService cria instâncias configuradas
def create_gemini_service():
    return GeminiService(
        api_key=settings.GEMINI_API_KEY,
        model='gemini-1.5-flash'
    )
```

### **4. Observer Pattern**
```python
# Webhook é um observer de eventos do WhatsApp
WhatsApp Event → Webhook Notification → Process Message
```

---

## 🚀 **DEPLOYMENT E INFRAESTRUTURA**

### **Development vs Production**

**Development:**
```python
# Configurações de desenvolvimento
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '.ngrok-free.app']
DATABASE = SQLite
SERVER = Django Development Server
TUNNEL = ngrok
```

**Production (futuro):**
```python
# Configurações de produção  
DEBUG = False
ALLOWED_HOSTS = ['meusite.com']
DATABASE = PostgreSQL
SERVER = Gunicorn + Nginx
HTTPS = SSL Certificate
CACHE = Redis
QUEUE = Celery
MONITORING = Sentry
```

### **Docker (conceito para futuro)**
```dockerfile
# Dockerfile
FROM python:3.10
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "core.wsgi:application"]
```

---

## 📚 **RESUMO DOS CONCEITOS**

| Conceito | O que é | Onde está no projeto |
|----------|---------|---------------------|
| **API** | Interface de comunicação | WhatsApp Business API |
| **REST** | Estilo arquitetural para APIs | `rag_agent/views.py` |
| **Endpoint** | Ponto de acesso da API | `/api/webhook/whatsapp/` |
| **Gateway** | Ponto de entrada único | `api_gateway/` |
| **Middleware** | Interceptador de requisições | `api_gateway/middleware.py` |
| **Webhook** | Notificação automática | WhatsApp → Django |
| **Service** | Camada de lógica de negócio | `services/` |
| **Logging** | Registro de eventos | `settings.LOGGING` |
| **ORM** | Mapeamento objeto-relacional | Django Models |
| **Serializer** | Conversão de dados | DRF Serializers |
| **CSRF** | Proteção contra ataques | Django Middleware |
| **CORS** | Controle de acesso cross-origin | `django-cors-headers` |
| **Environment Variables** | Configurações externas | `.env` |
| **LLM** | Modelo de linguagem | Gemini AI |
| **RAG** | Geração aumentada por recuperação | RAGService + Gemini |
| **NLP** | Processamento de linguagem natural | Intent Detection |

---

**Esta documentação serve como referência completa para entender todos os conceitos técnicos utilizados no projeto do chatbot!** 🎓📚
