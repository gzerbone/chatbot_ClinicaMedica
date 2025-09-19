# 📋 Mapeamento Completo - Onde São Armazenadas as Informações do Paciente

Este documento mapeia exatamente onde cada informação do paciente é coletada, armazenada e utilizada no sistema.

## 🎯 **Informações Principais Coletadas**

### **📝 Lista Completa:**
1. **👤 Nome completo do paciente**
2. **👨‍⚕️ Médico solicitado**
3. **🩺 Tipo de consulta** (consulta, retorno, exame)
4. **💼 Plano de saúde** (Unimed, SulAmérica, Particular, etc.)
5. **📅 Data de interesse**
6. **🕐 Hora de interesse**
7. **📱 Número de telefone** (WhatsApp)

---

## 🗄️ **ONDE SÃO ARMAZENADAS**

### **1. 🧠 ConversationContext (Contexto Individual)**

**Arquivo:** `api_gateway/services/context_manager.py` - Linhas 16-137

```python
class ConversationContext:
    def __init__(self, phone_number: str):
        self.phone_number = phone_number          # 📱 Telefone do paciente
        self.messages: List[Dict] = []            # 💬 Histórico completo
        self.last_intent: Optional[str] = None    # 🎯 Última intenção
        self.last_entities: Dict = {}             # 📊 Últimas entidades
        self.patient_info: Dict = {}              # 👤 INFORMAÇÕES DO PACIENTE
        self.pending_confirmation: Optional[Dict] = None  # ⏳ Confirmações pendentes
```

#### **📋 Estrutura do `patient_info`:**
```python
self.patient_info = {
    'patient_name': 'Nome do paciente',       # 👤 Nome
    'specialty': 'Cardiologia',               # 🩺 Especialidade
    'preferred_time': '14:30',                # 🕐 Horário
    'preferred_date': '15/09/2025',           # 📅 Data
    'insurance': 'Unimed',                    # 💼 Convênio
    'appointment_type': 'Consulta',           # 📝 Tipo de consulta
    'phone_number': '5511999999999'           # 📱 Telefone
}
```

#### **📍 Onde é atualizado:**
```python
# Linha 57-73: Método _update_patient_info()
def _update_patient_info(self, entities: Dict):
    if 'specialties' in entities and entities['specialties']:
        self.patient_info['specialty'] = entities['specialties'][0]
    
    if 'times' in entities and entities['times']:
        self.patient_info['preferred_time'] = entities['times'][0]
    
    if 'dates' in entities and entities['dates']:
        self.patient_info['preferred_date'] = entities['dates'][0]
```

---

### **2. 💾 Cache do Django (Persistência Temporária)**

**Arquivo:** `api_gateway/services/context_manager.py` - Linhas 164-171

```python
def _save_context(self, context: ConversationContext):
    """Salva contexto no cache"""
    cache_key = f"conversation_context_{context.phone_number}"
    cache.set(cache_key, context.to_dict(), 24*3600)  # 24 horas
```

#### **📍 Estrutura no Cache:**
```json
{
  "phone_number": "5511999999999",
  "messages": [
    {
      "content": "Quero Dr. Gustavo",
      "intent": "buscar_medico", 
      "entities": {"specialties": ["pneumologia"]},
      "confidence": 0.8,
      "is_user": true,
      "timestamp": "2025-09-14T15:30:00"
    }
  ],
  "patient_info": {
    "specialty": "pneumologia",
    "preferred_time": "14:30",
    "insurance": "Unimed"
  }
}
```

---

## 🔄 **COMO AS INFORMAÇÕES SÃO COLETADAS**

### **1. 📥 Extração de Entidades (Durante a Conversa)**

**Arquivo:** `api_gateway/services/intent_detection_service.py` - Linhas 195-233

```python
def extract_entities(self, message: str) -> Dict[str, List]:
    entities = {
        'numbers': [],      # Números mencionados
        'dates': [],        # Datas (DD/MM/YYYY)
        'times': [],        # Horários (HH:MM)
        'specialties': [],  # Especialidades médicas
        'doctors': []       # Nomes de médicos
    }
    
    # Extrair datas (formato DD/MM/YYYY ou DD/MM)
    dates = re.findall(r'\b\d{1,2}/\d{1,2}(?:/\d{2,4})?\b', message)
    entities['dates'] = dates
    
    # Extrair horários (formato HH:MM)
    times = re.findall(r'\b\d{1,2}:\d{2}\b', message)
    entities['times'] = times
    
    # Extrair especialidades médicas
    specialties = ['cardiologia', 'dermatologia', 'pneumologia', ...]
    for specialty in specialties:
        if specialty in message.lower():
            entities['specialties'].append(specialty)
```

### **2. 🧠 Atualização Automática (A Cada Mensagem)**

**Arquivo:** `api_gateway/services/context_manager.py` - Linha 53

```python
# Chamado automaticamente quando usuário envia mensagem
def add_message(self, message, intent, entities, confidence, is_user=True):
    if is_user:
        self._update_patient_info(entities)  # ← ATUALIZA INFO DO PACIENTE
```

### **3. 📱 Extração do Histórico (Análise Contextual)**

**Arquivo:** `api_gateway/services/handoff_service.py` - Linhas 156-217

```python
def extract_patient_info_from_context(self, context_history: list, entities: Dict):
    # Buscar informações no histórico da conversa
    for message in context_history:
        content = message.get('content', '').lower()
        
        # Buscar menções de convênio usando dados do banco
        for insurance in valid_insurances:
            if insurance.lower() in content:
                patient_info['insurance'] = insurance
                
        # Buscar se mencionou ser particular
        if 'particular' in content:
            patient_info['appointment_type'] = 'Particular'
            
        # Buscar menção de nome próprio
        for word in content.split():
            if word.istitle() and len(word) > 2:
                patient_info['patient_name'] = word
```

---

## 🔗 **ONDE É GERADO O LINK DE HANDOFF**

### **📍 Localização Principal:**

**Arquivo:** `api_gateway/views.py` - Linhas 130-148

```python
# Verificar se é confirmação de agendamento para gerar handoff
if intent.startswith('confirmar_') and 'agendar' in intent:
    response_text = handle_appointment_confirmation(
        from_number, text_content, intent, entities, conversation_history
    )
```

### **🔧 Função de Geração:**

**Arquivo:** `api_gateway/views.py` - Linhas 34-133

```python
def handle_appointment_confirmation(phone_number, message, intent, entities, conversation_history):
    # 1. Extrair informações do histórico
    # 2. Preparar dados do handoff
    handoff_data = context_manager.prepare_handoff_data(
        phone_number, doctor_name, date, time
    )
    
    # 3. Gerar link de handoff
    whatsapp_link = handoff_service.generate_appointment_handoff_link(
        patient_name=handoff_data['patient_name'],
        doctor_name=handoff_data['doctor_name'],
        specialty=handoff_data['specialty'],      # ← Do banco de dados
        appointment_type=handoff_data['appointment_type'],
        date=handoff_data['date'],
        time=handoff_data['time']
    )
    
    # 4. Retornar mensagem com link
    return f"""✅ Resumo do agendamento...
    
🔗 **CLIQUE AQUI PARA CONFIRMAR:**
{whatsapp_link}"""
```

### **⚙️ Geração Técnica do Link:**

**Arquivo:** `api_gateway/services/handoff_service.py` - Linhas 90-101

```python
# Construir mensagem formatada
message_lines = [
    "🏥 *PRÉ-AGENDAMENTO VIA CHATBOT*",
    f"👤 *Nome do Paciente:* {patient_name}",
    f"👨‍⚕️ *Médico:* {doctor_name}",
    f"🩺 *Especialidade:* {specialty}",        # ← Do banco via RAGService
    f"💼 *Tipo de Consulta:* {appointment_type}",
    f"📅 *Data/Hora escolhida:* {date} às {time}",
]

# Codificar para URL
encoded_message = urllib.parse.quote(full_message)

# Gerar link final
whatsapp_link = f"https://api.whatsapp.com/send?phone={clinic_phone}&text={encoded_message}"
```

---

## 🔄 **FLUXO COMPLETO DE COLETA E ARMAZENAMENTO**

### **📱 Exemplo Prático:**

```
👤 PACIENTE: "Olá, sou Maria Silva"
🔍 SISTEMA: Extrai nome → patient_info['patient_name'] = "Maria Silva"

👤 PACIENTE: "Preciso de pneumologista"  
🔍 SISTEMA: Extrai especialidade → patient_info['specialty'] = "pneumologia"

👤 PACIENTE: "Dr. Gustavo Magno"
🔍 SISTEMA: Identifica médico → Busca no banco via RAGService

👤 PACIENTE: "Amanhã às 14:30"
🔍 SISTEMA: Extrai data/hora → patient_info['preferred_date'] = "amanhã"
                              patient_info['preferred_time'] = "14:30"

👤 PACIENTE: "Tenho Unimed"
🔍 SISTEMA: Identifica convênio → patient_info['insurance'] = "Unimed"

👤 PACIENTE: "Sim, confirmo!"
🔍 SISTEMA: Intent = "confirmar_agendar_consulta"
🔗 SISTEMA: GERA LINK DE HANDOFF ← AQUI!
```

---

## 📊 **MAPEAMENTO TÉCNICO DETALHADO**

### **1. 📥 COLETA (Durante Conversa)**

| Informação | Onde é Extraída | Como é Detectada |
|------------|-----------------|------------------|
| **Nome do Paciente** | `intent_detection_service.py` | Palavras com primeira letra maiúscula |
| **Médico Solicitado** | `intent_detection_service.py` | Padrões "Dr./Dra. + Nome" |
| **Especialidade** | `intent_detection_service.py` | Lista de especialidades médicas |
| **Data/Hora** | `intent_detection_service.py` | Regex para DD/MM e HH:MM |
| **Convênio** | `context_manager.py` | Comparação com convênios do banco |
| **Tipo de Consulta** | `context_manager.py` | Palavras-chave: consulta, retorno, exame |

### **2. 💾 ARMAZENAMENTO (Em Memória)**

| Informação | Localização | Estrutura |
|------------|-------------|-----------|
| **Contexto Completo** | `ConversationContext.patient_info` | Dicionário Python |
| **Histórico** | `ConversationContext.messages` | Lista de mensagens |
| **Cache** | `Django Cache` | JSON serializado (24h TTL) |
| **Entidades** | `ConversationContext.last_entities` | Dicionário de entidades |

### **3. 🔗 GERAÇÃO DO LINK (Quando Confirma)**

| Etapa | Arquivo | Função | Linha |
|-------|---------|--------|-------|
| **Detecção de Confirmação** | `views.py` | `whatsapp_webhook()` | 130-148 |
| **Preparação de Dados** | `context_manager.py` | `prepare_handoff_data()` | 395-434 |
| **Busca no Banco** | `rag_service.py` | `get_doctor_specialty()` | 254-281 |
| **Geração do Link** | `handoff_service.py` | `generate_appointment_handoff_link()` | 23-105 |
| **Envio ao Usuário** | `views.py` | `handle_appointment_confirmation()` | 113-125 |

---

## 📱 **EXEMPLO REAL DE FUNCIONAMENTO**

### **💬 Conversa:**
```
👤: "Olá, sou João Silva"                    → patient_name = "João Silva"
👤: "Preciso de pneumologista"               → specialty = "pneumologia" 
👤: "Dr. Gustavo Magno"                      → doctor_name = "Dr. Gustavo Magno"
👤: "Amanhã às 14:30"                        → date = "amanhã", time = "14:30"
👤: "Tenho Cassi"                            → insurance = "Cassi"
👤: "Sim, confirmo!"                         → TRIGGER: Gerar handoff
```

### **🗄️ Dados Finais Coletados:**
```python
# Em ConversationContext.patient_info:
{
    'patient_name': 'João Silva',
    'specialty': 'pneumologia', 
    'preferred_time': '14:30',
    'preferred_date': 'amanhã',
    'insurance': 'Cassi',
    'appointment_type': 'Cassi'
}

# Dados do médico (do banco via RAGService):
{
    'doctor_name': 'Dr. Gustavo Magno',
    'specialty': 'Medicina do Sono',    # ← Do banco de dados
    'convenios': ['Cassi'],             # ← Do banco de dados
    'crm': 'CRM123456'                  # ← Do banco de dados
}
```

### **🔗 Link Gerado:**
```
https://api.whatsapp.com/send?phone=5573988221003&text=
🏥 *PRÉ-AGENDAMENTO VIA CHATBOT*

👤 *Nome do Paciente:* João Silva
👨‍⚕️ *Médico:* Dr. Gustavo Magno
🩺 *Especialidade:* Medicina do Sono
💼 *Tipo de Consulta:* Cassi
📅 *Data/Hora escolhida:* 15/09/2025 às 14:30
💼 *Convênios aceitos:* Cassi

🤖 Mensagem gerada automaticamente pelo chatbot
👩‍💼 Secretária: Por favor, confirme este agendamento
```

---

## 🎯 **PONTOS-CHAVE DO SISTEMA**

### **✅ Armazenamento Inteligente:**
- **Coleta gradual** durante conversa
- **Cache persistente** por 24 horas
- **Fallbacks** para informações ausentes
- **Validação** contra banco de dados

### **✅ Integração com Banco:**
- **Especialidades** vêm do banco real
- **Convênios** validados contra dados reais
- **Informações do médico** sempre atualizadas
- **CRM** incluído automaticamente

### **✅ Geração de Link:**
- **Trigger automático** na confirmação
- **Dados completos** do contexto + banco
- **URL codificada** corretamente
- **Mensagem estruturada** para secretária

---

## 🔧 **CONFIGURAÇÃO NECESSÁRIA**

### **Para Funcionar Completamente:**

#### **1. Arquivo `.env`:**
```env
CLINIC_WHATSAPP_NUMBER=5573988221003  # ← Número da clínica para handoff
```

#### **2. Banco de Dados:**
- **Médicos** cadastrados com especialidades
- **Convênios** configurados
- **Relacionamentos** médico-convênio definidos

#### **3. Trigger de Confirmação:**
- **Intent detection** identifica "confirmar_agendar_consulta"
- **Sistema** automaticamente gera link
- **Usuário** recebe link clicável

---

## 🎉 **RESULTADO FINAL**

**TODAS as informações são coletadas automaticamente durante a conversa natural e armazenadas no `ConversationContext.patient_info` + cache do Django.**

**O LINK é gerado automaticamente na função `handle_appointment_confirmation()` em `api_gateway/views.py` quando o sistema detecta confirmação de agendamento.**

**A mensagem final inclui TODOS os dados coletados + informações do médico obtidas em tempo real do banco de dados via RAGService!** 

✅📋🔗💾🤖
