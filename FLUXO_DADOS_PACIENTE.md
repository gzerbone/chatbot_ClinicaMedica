# 🔄 Fluxo de Dados do Paciente - Diagrama Visual

## 📊 **Diagrama do Fluxo Completo**

```
                           📱 PACIENTE ENVIA MENSAGEM
                                        │
                                        ▼
                           ┌─────────────────────────────┐
                           │    INTENT DETECTION         │
                           │  extract_entities()         │
                           │                             │
                           │ ✅ Extrai:                  │
                           │ • Nome (João Silva)         │
                           │ • Especialidade (cardio)    │
                           │ • Data/Hora (15/09 14:30)   │
                           │ • Convênio (Unimed)         │
                           └─────────────┬───────────────┘
                                        │
                                        ▼
                           ┌─────────────────────────────┐
                           │   CONVERSATION CONTEXT      │
                           │  _update_patient_info()     │
                           │                             │
                           │ 💾 Armazena em:             │
                           │ • patient_info{}            │
                           │ • last_entities{}           │
                           │ • messages[]                │
                           └─────────────┬───────────────┘
                                        │
                                        ▼
                           ┌─────────────────────────────┐
                           │     DJANGO CACHE            │
                           │   _save_context()           │
                           │                             │
                           │ 🗄️ Persiste por 24h:       │
                           │ • Contexto completo         │
                           │ • Histórico de mensagens    │
                           │ • Informações do paciente   │
                           └─────────────┬───────────────┘
                                        │
                                        ▼
                           ┌─────────────────────────────┐
                           │   USUÁRIO CONFIRMA          │
                           │ "Sim, confirmo!"            │
                           └─────────────┬───────────────┘
                                        │
                                        ▼
                           ┌─────────────────────────────┐
                           │  HANDLE APPOINTMENT         │
                           │  CONFIRMATION               │
                           │                             │
                           │ 🔍 Busca no histórico:      │
                           │ • Nome do médico            │
                           │ • Data e horário            │
                           │ • Tipo de consulta          │
                           └─────────────┬───────────────┘
                                        │
                                        ▼
                           ┌─────────────────────────────┐
                           │   PREPARE HANDOFF DATA      │
                           │ context_manager.prepare()   │
                           │                             │
                           │ 🧠 Combina:                 │
                           │ • Dados do contexto         │
                           │ • Informações do banco      │
                           │ • Entidades extraídas       │
                           └─────────────┬───────────────┘
                                        │
                                        ▼
                           ┌─────────────────────────────┐
                           │      RAG SERVICE            │
                           │ get_doctor_specialty()      │
                           │                             │
                           │ 🗄️ Busca no banco:          │
                           │ • Especialidade do médico   │
                           │ • Convênios aceitos         │
                           │ • CRM do médico             │
                           └─────────────┬───────────────┘
                                        │
                                        ▼
                           ┌─────────────────────────────┐
                           │    HANDOFF SERVICE          │
                           │ generate_appointment_       │
                           │ handoff_link()              │
                           │                             │
                           │ 🔗 Gera link com:           │
                           │ • URL do WhatsApp           │
                           │ • Número da clínica         │
                           │ • Mensagem codificada       │
                           └─────────────┬───────────────┘
                                        │
                                        ▼
                           ┌─────────────────────────────┐
                           │   RESPOSTA AO PACIENTE      │
                           │                             │
                           │ 📱 Envia:                   │
                           │ • Resumo do agendamento     │
                           │ • Link clicável             │
                           │ • Instruções               │
                           └─────────────────────────────┘
```

---

## 📍 **LOCALIZAÇÃO EXATA DAS INFORMAÇÕES**

### **1. 👤 Nome Completo do Paciente**

#### **Extração:**
```python
# api_gateway/services/intent_detection_service.py - Linha 220-233
# api_gateway/services/handoff_service.py - Linha 210-215

for word in content.split():
    if word.istitle() and len(word) > 2 and word not in ['Dr', 'Dra']:
        patient_info['patient_name'] = word  # ← ARMAZENADO AQUI
```

#### **Armazenamento:**
```python
# api_gateway/services/context_manager.py - Linha 28
self.patient_info: Dict = {}  # ← ARMAZENADO AQUI

# Estrutura:
patient_info['patient_name'] = "João Silva"
```

### **2. 👨‍⚕️ Médico Solicitado**

#### **Extração:**
```python
# api_gateway/views.py - Linha 66-77
if 'dr.' in msg_content or 'dra.' in msg_content:
    # Extrai nome completo do médico
    doctor_name = f"Dr. João Carvalho"  # ← EXTRAÍDO AQUI
```

#### **Validação no Banco:**
```python
# api_gateway/services/rag_service.py - Linha 224-252
def get_medico_by_name(doctor_name: str):
    medico = Medico.objects.filter(nome__icontains=normalized_name).first()
    # ← VALIDADO CONTRA BANCO AQUI
```

### **3. 🩺 Tipo de Consulta**

#### **Detecção:**
```python
# api_gateway/services/context_manager.py - Linha 57-73
# Palavras-chave: "consulta", "retorno", "exame"
# Padrão: "Consulta" se não especificado
```

#### **Armazenamento:**
```python
patient_info['appointment_type'] = "Consulta"  # ou "Retorno", "Exame"
```

### **4. 💼 Plano de Saúde**

#### **Extração de Convênios:**
```python
# api_gateway/services/handoff_service.py - Linha 192-204
valid_insurances = self._get_valid_insurances()  # ← Do banco via RAGService

for insurance in valid_insurances:
    if insurance.lower() in content:
        patient_info['insurance'] = insurance  # ← ARMAZENADO AQUI
```

#### **Validação Automática:**
```python
# api_gateway/services/rag_service.py - Linha 284-306
def get_doctor_insurances(doctor_name: str):
    # Verifica se médico aceita o convênio mencionado
    # Se não aceitar → "Particular"
```

### **5. 📅 Data de Interesse**

#### **Extração:**
```python
# api_gateway/services/intent_detection_service.py - Linha 212-213
dates = re.findall(r'\b\d{1,2}/\d{1,2}(?:/\d{2,4})?\b', message)
entities['dates'] = dates  # ← EXTRAÍDO AQUI
```

#### **Armazenamento:**
```python
# api_gateway/services/context_manager.py - Linha 65-66
if 'dates' in entities and entities['dates']:
    self.patient_info['preferred_date'] = entities['dates'][0]  # ← ARMAZENADO AQUI
```

### **6. 🕐 Hora de Interesse**

#### **Extração:**
```python
# api_gateway/services/intent_detection_service.py - Linha 215-216
times = re.findall(r'\b\d{1,2}:\d{2}\b', message)
entities['times'] = times  # ← EXTRAÍDO AQUI
```

#### **Armazenamento:**
```python
# api_gateway/services/context_manager.py - Linha 62-63
if 'times' in entities and entities['times']:
    self.patient_info['preferred_time'] = entities['times'][0]  # ← ARMAZENADO AQUI
```

---

## 🔗 **ONDE É GERADO O LINK**

### **🎯 Localização Exata:**

**Arquivo:** `api_gateway/views.py`  
**Função:** `handle_appointment_confirmation()`  
**Linhas:** 91-103

```python
# Gerar link de handoff
whatsapp_link = handoff_service.generate_appointment_handoff_link(
    patient_name=handoff_data['patient_name'],     # ← Do contexto
    doctor_name=handoff_data['doctor_name'],       # ← Do histórico
    specialty=handoff_data['specialty'],           # ← Do banco (RAGService)
    appointment_type=handoff_data['appointment_type'], # ← Do contexto
    date=handoff_data['date'],                     # ← Do histórico
    time=handoff_data['time'],                     # ← Do histórico
    additional_info={
        'telefone_paciente': phone_number,         # ← Do WhatsApp
        'convenio': handoff_data.get('insurance')  # ← Do contexto
    }
)
```

### **📱 Onde o Usuário Recebe o Link:**

**Arquivo:** `api_gateway/views.py`  
**Linhas:** 113-125

```python
final_message = f"""{confirmation_message}

🔗 **CLIQUE AQUI PARA CONFIRMAR:**
{whatsapp_link}                          # ← LINK ENVIADO AQUI

💡 **Como funciona:**
1️⃣ Clique no link acima
2️⃣ Será direcionado para WhatsApp da clínica
3️⃣ Mensagem será preenchida automaticamente
4️⃣ Nossa secretária confirmará seu agendamento"""

# Esta mensagem é enviada via WhatsApp para o paciente
```

---

## 🎯 **RESUMO EXECUTIVO**

### **📍 ARMAZENAMENTO:**
- **Contexto Individual:** `ConversationContext.patient_info` (memória)
- **Cache Persistente:** Django Cache (24h)
- **Dados do Médico:** Banco de dados via RAGService

### **📍 GERAÇÃO DO LINK:**
- **Trigger:** Intent "confirmar_agendar_consulta"
- **Localização:** `api_gateway/views.py` - `handle_appointment_confirmation()`
- **Serviço:** `HandoffService.generate_appointment_handoff_link()`

### **📍 ENTREGA AO USUÁRIO:**
- **Via:** WhatsApp (mesmo canal da conversa)
- **Formato:** Mensagem com link clicável
- **Destino:** WhatsApp da clínica com dados pré-preenchidos

**O sistema coleta TUDO automaticamente durante a conversa natural e gera o link no momento exato da confirmação!** 🎯✅📱
