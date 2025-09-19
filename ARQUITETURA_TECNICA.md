# 🏗️ Arquitetura Técnica do Chatbot - Versão Atualizada

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
│ • Smart      │                │ • Responses │                │ • Data      │
│   Collection │                │ • Handoff   │                │   Cache     │
│ • Context    │                │             │                │             │
│   Manager    │                │             │                │             │
│ • Handoff    │                │             │                │             │
│ • Persistence│                │             │                │             │
│ • Base       │                │             │                │             │
│   Service    │                │             │                │             │
└──────────────┘                └─────────────┘                └─────────────┘
```

## 🔧 Arquitetura de Serviços Consolidada

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CAMADA DE SERVIÇOS                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐        │
│  │  BASE SERVICE   │    │ CONTEXT MANAGER │    │ CONVERSATION    │        │
│  │                 │    │                 │    │ SERVICE         │        │
│  │ • extract_name  │◄──►│ • Context Cache │◄──►│ • Session Mgmt  │        │
│  │ • validate_name │    │ • Intent Analysis│    │ • Message Store │        │
│  │ • extract_phone │    │ • Conversation  │    │ • Patient Info  │        │
│  │ • extract_entities│  │   History       │    │ • State Mgmt    │        │
│  │ • should_handoff│    │ • Pending Conf  │    │ • Appointment   │        │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘        │
│           │                       │                       │                │
│           └───────────────────────┼───────────────────────┘                │
│                                   │                                        │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐        │
│  │ SMART COLLECTION│    │ INTENT DETECTION│    │ WHATSAPP SERVICE│        │
│  │ SERVICE         │    │ SERVICE         │    │                 │        │
│  │                 │    │                 │    │ • Send Message  │        │
│  │ • Info Gathering│◄──►│ • Pattern Match │◄──►│ • Mark Read     │        │
│  │ • Name Confirm  │    │ • Context Aware │    │ • Template Msg  │        │
│  │ • Validation    │    │ • Entity Extract│    │ • Webhook Valid │        │
│  │ • Handoff Logic │    │ • Confidence    │    │ • Profile Info  │        │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘        │
│           │                       │                       │                │
│           └───────────────────────┼───────────────────────┘                │
│                                   │                                        │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐        │
│  │   RAG SERVICE   │    │  HANDOFF SERVICE│    │ GEMINI SERVICE  │        │
│  │                 │    │                 │    │                 │        │
│  │ • Clinic Data   │◄──►│ • Link Generate │◄──►│ • AI Response   │        │
│  │ • Doctor Info   │    │ • Data Prepare  │    │ • Context Build │        │
│  │ • Specialties   │    │ • Confirmation  │    │ • Fallback Resp │        │
│  │ • Cache Mgmt    │    │ • Calendar Int  │    │ • Prompt Eng    │        │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 🔧 Componentes por Camada

### 1. **CAMADA DE COMUNICAÇÃO (API GATEWAY)**
```
┌─────────────────────────────────────────────────────────────┐
│                    API GATEWAY                              │
├─────────────────────────────────────────────────────────────┤
│ 📁 api_gateway/                                             │
│ ├── models.py             # Sessões, Mensagens, Agendamentos │
│ ├── views.py              # Webhook + Endpoints de teste    │
│ ├── middleware.py         # CSRF + Logging                 │
│ ├── urls.py               # URL routing                    │
│ └── services/                                              │
│     ├── base_service.py          # 🆕 Serviço base consolidado │
│     ├── whatsapp_service.py      # WhatsApp API client     │
│     ├── intent_detection_service.py # NLP contextual       │
│     ├── rag_service.py          # Acesso aos dados         │
│     ├── conversation_service.py # Gerenciamento persistente │
│     ├── smart_collection_service.py # Coleta inteligente   │
│     ├── context_manager.py      # Consciência contextual   │
│     ├── handoff_service.py      # Transferência para humano │
│     └── google_calendar_service.py # Integração calendário │
└─────────────────────────────────────────────────────────────┘
```

### 1.1. **BASE SERVICE - Funções Consolidadas**
```
┌─────────────────────────────────────────────────────────────┐
│                    BASE SERVICE                             │
├─────────────────────────────────────────────────────────────┤
│ 📁 api_gateway/services/base_service.py                    │
│                                                             │
│ 🔧 Funções Centralizadas:                                   │
│ • extract_patient_name()     # Extração de nomes           │
│ • validate_patient_name()    # Validação de nomes          │
│ • extract_phone_from_message() # Extração de telefones     │
│ • extract_entities_from_message() # Extração de entidades  │
│ • should_trigger_handoff()   # Lógica de handoff           │
│ • format_phone_number()      # Formatação de telefones     │
│                                                             │
│ 🎯 Benefícios:                                              │
│ • Elimina duplicação de código                             │
│ • Padroniza funções comuns                                 │
│ • Facilita manutenção                                      │
│ • Melhora testabilidade                                    │
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
│ • Respostas personalizadas por contexto                    │
│ • Lógica de contatos inteligente                           │
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
│ • ClinicaInfo    (nome, endereço, telefone, WhatsApp)      │
│ • Especialidade  (nome, descrição, ativa)                  │
│ • Medico         (nome, CRM, especialidades)               │
│ • Convenio       (nome, ativo)                             │
│ • Exame          (nome, descrição, preço)                  │
│ • HorarioTrabalho (médico, dia, horário)                   │
└─────────────────────────────────────────────────────────────┘
```

### 4. **CAMADA DE PERSISTÊNCIA (API GATEWAY)**
```
┌─────────────────────────────────────────────────────────────┐
│                    PERSISTÊNCIA                             │
├─────────────────────────────────────────────────────────────┤
│ 📁 api_gateway/models.py                                    │
│                                                             │
│ 🗄️ Modelos de Persistência:                                 │
│ • ConversationSession    # Sessões de conversa             │
│ • ConversationMessage    # Mensagens individuais           │
│ • AppointmentRequest     # Solicitações de agendamento     │
│ • RAGCache              # Cache de dados RAG               │
│                                                             │
│ 📊 Estados de Sessão:                                       │
│ • idle                   # Ocioso                          │
│ • collecting_patient_info # Coletando dados do paciente    │
│ • collecting_info       # Coletando informações gerais     │
│ • confirming_name       # Confirmando nome                 │
│ • selecting_doctor      # Selecionando médico              │
│ • choosing_schedule     # Escolhendo horário               │
│ • confirming           # Confirmando agendamento           │
│ • completed            # Concluído                         │
│ • cancelled            # Cancelado                         │
│                                                             │
│ 🔧 Campos Adicionais:                                       │
│ • pending_name          # Nome aguardando confirmação      │
│ • name_confirmed        # Flag de confirmação do nome      │
│ • last_activity         # Timestamp da última atividade    │
└─────────────────────────────────────────────────────────────┘
```

### 4.1. **CONTEXT MANAGER - Consciência Contextual**
```
┌─────────────────────────────────────────────────────────────┐
│                    CONTEXT MANAGER                          │
├─────────────────────────────────────────────────────────────┤
│ 📁 api_gateway/services/context_manager.py                  │
│                                                             │
│ 🧠 Funcionalidades:                                         │
│ • ConversationContext    # Contexto individual por usuário │
│ • Context Cache          # Cache de contextos ativos       │
│ • Intent Analysis        # Análise contextual de intenções │
│ • Pending Confirmation   # Gerenciamento de confirmações   │
│ • Conversation History   # Histórico de conversas          │
│ • Patient Info Tracking  # Rastreamento de informações     │
│                                                             │
│ 🎯 Estados de Contexto:                                     │
│ • idle                   # Ocioso                          │
│ • waiting_confirmation   # Aguardando confirmação          │
│ • collecting_info        # Coletando informações           │
│                                                             │
│ 🔄 Fluxo Contextual:                                        │
│ 1. Análise de mensagem simples (sim/não)                   │
│ 2. Verificação de confirmações pendentes                   │
│ 3. Detecção de continuação de conversa                     │
│ 4. Análise contextual com histórico                        │
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
    
    # Detectar intenção com contexto (usando ContextManager)
    intent, confidence, entities = intent_service.detect_intent_with_context(
        from_number, text_content
    )
    
    # Processar com coleta inteligente (usando SmartCollectionService)
    collection_result = smart_collection_service.process_message_with_collection(
        from_number, text_content, intent, entities
    )
    
    # Verificar se precisa de confirmação de nome
    if collection_result.get('next_action') == 'waiting_for_name':
        # Processar confirmação de nome
        name_result = conversation_service.process_patient_name(from_number, text_content)
        if name_result['status'] == 'confirmation_needed':
            response_text = name_result['message']
        else:
            response_text = collection_result['response']
    else:
        # Obter histórico da conversa
        conversation_history = conversation_service.get_conversation_history(from_number, limit=3)
        
        # Gerar resposta ou usar resposta específica da coleta
        if collection_result['response']:
            response_text = collection_result['response']
        elif collection_result['requires_handoff']:
            response_text = handle_appointment_confirmation(...)
        else:
            response_text = gemini_service.generate_response(
                user_message=text_content,
                intent=intent,
                context={
                    'entities': entities,
                    'confidence': confidence,
                    'conversation_history': conversation_history,
                    'info_status': collection_result.get('info_status', {})
                },
                clinic_data=get_clinic_data()
            )
    
    # Enviar resposta e persistir
    whatsapp_service.send_message(from_number, response_text)
    conversation_service.add_message(from_number, text_content, 'user', intent, confidence, entities)
    conversation_service.add_message(from_number, response_text, 'bot', 'resposta_bot', 1.0, {})
```

### **4. Detecção de Intenção Contextual**
```python
# api_gateway/services/intent_detection_service.py
class IntentDetectionService:
    def detect_intent_with_context(self, phone_number: str, message: str):
        # Usar ContextManager para análise contextual avançada
        intent, confidence, entities = context_manager.analyze_contextual_intent(phone_number, message)
        
        # Se não foi possível determinar com contexto, usar análise tradicional
        if intent == 'desconhecida' and confidence < 0.5:
            intent, confidence = self.detect_intent(message)
            entities = self.extract_entities(message)
        
        # Adicionar mensagem ao contexto
        context_manager.add_message_to_context(
            phone_number, message, intent, entities, confidence, is_user=True
        )
        
        return intent, confidence, entities
    
    def detect_intent(self, message: str):
        # Análise tradicional por padrões regex
        message_lower = message.lower().strip()
        intent_scores = {}
        
        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    score += 1
            intent_scores[intent] = score / len(patterns) if patterns else 0
        
        if intent_scores:
            best_intent = max(intent_scores.items(), key=lambda x: x[1])
            return best_intent if best_intent[1] >= 0.1 else ('desconhecida', 0.0)
        
        return 'desconhecida', 0.0
    
    def extract_entities(self, message: str):
        # Usar BaseService para extração consolidada
        return BaseService.extract_entities_from_message(message)
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
        # Verificar se Gemini está disponível
        if not self.enabled:
            return self._get_fallback_response(intent)
        
        # Construir prompt contextualizado
        prompt = self._build_prompt(user_message, intent, context, clinic_data)
        
        # Gerar resposta
        response = self.model.generate_content(
            prompt,
            generation_config=self.generation_config
        )
        
        return response.text.strip()
    
    def _build_prompt(self, user_message, intent, context, clinic_data):
        # Buscar nome da clínica dinamicamente
        clinic_name = clinic_data.get('nome', 'clínica médica') if clinic_data else 'clínica médica'
        
        system_prompt = f"""Você é um assistente virtual especializado da {clinic_name}.
        Seu papel é ajudar pacientes com informações sobre a clínica, agendamentos, médicos e exames.
        
        IMPORTANTE:
        - Seja sempre cordial, profissional e prestativo
        - Use emojis moderadamente para tornar a conversa mais amigável
        - NÃO mencione telefone ou WhatsApp a menos que o paciente peça especificamente
        - Foque apenas no que o paciente perguntou"""
        
        # Adicionar dados da clínica e contexto
        if clinic_data:
            system_prompt += f"\n\nInformações da clínica:\n{json.dumps(clinic_data, indent=2, ensure_ascii=False)}"
        
        if context and 'conversation_history' in context:
            # Adicionar histórico da conversa
            history = context['conversation_history']
            if history:
                system_prompt += "\n\nHistórico recente da conversa:"
                for i, msg in enumerate(history, 1):
                    role = "Paciente" if msg.get('is_user', True) else "Assistente"
                    content = msg.get('content', '')[:100]
                    system_prompt += f"\n{i}. {role}: {content}"
        
        # Instruções específicas por intenção
        intent_instructions = self._get_intent_instructions(intent)
        system_prompt += f"\n\nInstruções específicas para esta intenção ({intent}):\n{intent_instructions}"
        
        # Lógica de contatos inteligente
        contact_logic = self._get_contact_logic(intent, user_message)
        system_prompt += f"\n\nLógica de contatos:\n{contact_logic}"
        
        system_prompt += f"\n\nMensagem do paciente: {user_message}\n\nResposta:"
        
        return system_prompt
```

### **7. BaseService - Funções Consolidadas**
```python
# api_gateway/services/base_service.py
class BaseService:
    @staticmethod
    def extract_patient_name(message: str) -> Optional[str]:
        """Extrai nome completo do paciente da mensagem"""
        patterns = [
            r'sou\s+([A-Za-zÀ-ÿ\s]+)',
            r'meu\s+nome\s+é\s+([A-Za-zÀ-ÿ\s]+)',
            r'chamo-me\s+([A-Za-zÀ-ÿ\s]+)',
            r'nome\s+é\s+([A-Za-zÀ-ÿ\s]+)',
            r'me\s+chamo\s+([A-Za-zÀ-ÿ\s]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                words = name.split()
                if len(words) >= 2:
                    return name.title()
        
        # Fallback: extrair palavras maiúsculas consecutivas
        words = message.split()
        name_words = []
        for word in words:
            clean_word = word.strip('.,!?')
            if (clean_word.istitle() and len(clean_word) > 2 and 
                clean_word.isalpha() and clean_word.lower() not in 
                {'oi', 'olá', 'ola', 'bom', 'boa', 'dia', 'tarde', 'noite'}):
                name_words.append(clean_word)
        
        return ' '.join(name_words) if len(name_words) >= 2 else None
    
    @staticmethod
    def validate_patient_name(name: str) -> Tuple[bool, str]:
        """Valida se o nome fornecido é válido"""
        if not name or len(name.strip()) < 3:
            return False, "Nome muito curto. Por favor, informe seu nome completo."
        
        words = name.strip().split()
        if len(words) < 2:
            return False, "Por favor, informe seu nome e sobrenome. Exemplo: 'João Silva'"
        
        if any(char.isdigit() for char in name):
            return False, "Nome não deve conter números. Por favor, informe apenas letras."
        
        if not re.match(r'^[a-zA-ZÀ-ÿ\s]+$', name):
            return False, "Nome contém caracteres inválidos. Use apenas letras e espaços."
        
        return True, ""
    
    @staticmethod
    def extract_phone_from_message(message: str) -> Optional[str]:
        """Extrai número de telefone da mensagem"""
        patterns = [
            r'\(?(\d{2})\)?\s*(\d{4,5})-?(\d{4})',  # (11) 99999-9999
            r'(\d{2})\s*(\d{4,5})-?(\d{4})',        # 11 99999-9999
            r'(\d{10,11})',                          # 11999999999
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                groups = match.groups()
                if len(groups) == 3:
                    return f"({groups[0]}) {groups[1]}-{groups[2]}"
                elif len(groups) == 1:
                    phone = groups[0]
                    if len(phone) == 11:
                        return f"({phone[:2]}) {phone[2:7]}-{phone[7:]}"
                    elif len(phone) == 10:
                        return f"({phone[:2]}) {phone[2:6]}-{phone[6:]}"
        
        return None
    
    @staticmethod
    def extract_entities_from_message(message: str) -> Dict[str, List[str]]:
        """Extrai entidades básicas da mensagem"""
        entities = {
            'specialties': [],
            'doctors': [],
            'patient_name': [],
            'insurance': [],
            'dates': [],
            'times': []
        }
        
        # Extrair especialidades médicas
        specialties = [
            'cardiologia', 'dermatologia', 'pediatria', 'ginecologia', 
            'ortopedia', 'neurologia', 'psiquiatria', 'endocrinologia',
            'oftalmologia', 'urologia', 'gastroenterologia', 'pneumologia',
            'medicina do sono'
        ]
        
        for specialty in specialties:
            if specialty in message.lower():
                entities['specialties'].append(specialty)
        
        # Extrair médicos (Dr., Dra., Doutor, Doutora)
        doctor_patterns = [
            r'\b(?:Dr\.?|Dra\.?|Doutor|Doutora)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'\b([A-Z][a-z]+)\s+(?:Dr\.?|Dra\.?|Doutor|Doutora)'
        ]
        
        for pattern in doctor_patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            entities['doctors'].extend(matches)
        
        # Extrair datas (DD/MM/YYYY ou DD/MM)
        date_patterns = [
            r'\b(\d{1,2})/(\d{1,2})/(\d{2,4})\b',
            r'\b(\d{1,2})/(\d{1,2})\b'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, message)
            for match in matches:
                if len(match) == 3:  # DD/MM/YYYY
                    day, month, year = match
                    if len(year) == 2:
                        year = '20' + year
                    entities['dates'].append(f"{day}/{month}/{year}")
                elif len(match) == 2:  # DD/MM
                    day, month = match
                    entities['dates'].append(f"{day}/{month}")
        
        # Extrair horários (HH:MM)
        time_pattern = r'\b(\d{1,2}):(\d{2})\b'
        time_matches = re.findall(time_pattern, message)
        entities['times'] = [f"{hour}:{minute}" for hour, minute in time_matches]
        
        return entities
    
    @staticmethod
    def should_trigger_handoff(intent: str, message: str) -> bool:
        """Determina se deve acionar o handoff"""
        handoff_intents = ['confirmar_agendamento', 'agendar_consulta']
        handoff_keywords = ['confirmar', 'agendar', 'marcar', 'sim', 'ok', 'perfeito']
        
        if intent in handoff_intents:
            return True
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in handoff_keywords)
    
    @staticmethod
    def format_phone_number(phone: str) -> str:
        """Formata número de telefone para padrão brasileiro"""
        digits = re.sub(r'\D', '', phone)
        
        if len(digits) == 11:
            return f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"
        elif len(digits) == 10:
            return f"({digits[:2]}) {digits[2:6]}-{digits[6:]}"
        else:
            return phone
```

### **8. Envio via WhatsApp**
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

-- Sessões de Conversa (API Gateway)
CREATE TABLE api_gateway_conversationsession (
    id INTEGER PRIMARY KEY,
    phone_number VARCHAR(20) UNIQUE,
    patient_name VARCHAR(100),
    pending_name VARCHAR(100),
    name_confirmed BOOLEAN DEFAULT FALSE,
    current_state VARCHAR(50) DEFAULT 'idle',
    specialty_interest VARCHAR(100),
    insurance_type VARCHAR(50),
    preferred_date DATE,
    preferred_time TIME,
    selected_doctor VARCHAR(100),
    additional_notes TEXT,
    created_at DATETIME,
    updated_at DATETIME,
    last_activity DATETIME
);

-- Mensagens da Conversa
CREATE TABLE api_gateway_conversationmessage (
    id INTEGER PRIMARY KEY,
    session_id INTEGER REFERENCES api_gateway_conversationsession(id),
    message_type VARCHAR(10), -- 'user', 'bot', 'system'
    content TEXT,
    intent VARCHAR(50),
    confidence FLOAT,
    entities JSON,
    timestamp DATETIME
);

-- Solicitações de Agendamento
CREATE TABLE api_gateway_appointmentrequest (
    id INTEGER PRIMARY KEY,
    session_id INTEGER UNIQUE REFERENCES api_gateway_conversationsession(id),
    patient_name VARCHAR(100),
    phone_number VARCHAR(20),
    doctor_name VARCHAR(100),
    specialty VARCHAR(100),
    appointment_type VARCHAR(50),
    preferred_date DATE,
    preferred_time TIME,
    insurance VARCHAR(50),
    status VARCHAR(20) DEFAULT 'pending',
    handoff_link VARCHAR(500),
    confirmation_code VARCHAR(20),
    created_at DATETIME,
    updated_at DATETIME
);

-- Cache RAG
CREATE TABLE api_gateway_ragcache (
    id INTEGER PRIMARY KEY,
    cache_key VARCHAR(255) UNIQUE,
    data JSON,
    expires_at DATETIME,
    created_at DATETIME
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
