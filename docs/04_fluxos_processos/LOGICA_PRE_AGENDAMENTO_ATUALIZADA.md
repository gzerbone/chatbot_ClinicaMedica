# 📅 Lógica de Pré-Agendamento - Arquitetura Modularizada

## 📋 Índice
- [Visão Geral](#visão-geral)
- [Arquitetura Modular](#arquitetura-modular)
- [Fluxo Completo de Pré-Agendamento](#fluxo-completo-de-pré-agendamento)
- [Módulos e Responsabilidades](#módulos-e-responsabilidades)
- [Estados da Conversa](#estados-da-conversa)
- [Validações e Confirmações](#validações-e-confirmações)
- [Handoff para Secretária](#handoff-para-secretária)

---

## Visão Geral

O sistema de **pré-agendamento** é responsável por conduzir o paciente através de um fluxo conversacional inteligente, coletando informações necessárias para o agendamento e gerando um link de **handoff** para confirmação final com a secretária.

### Objetivo Principal
Automatizar a **coleta de informações** e **validação inicial** de agendamentos, reduzindo carga de trabalho da secretária e melhorando experiência do paciente.

---

## Arquitetura Modular

### Estrutura de Módulos

```
┌────────────────────────────────────────────────────────────────┐
│                  SISTEMA DE PRÉ-AGENDAMENTO                     │
└────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  📱 WhatsApp → Webhook → views.py                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│         🤖 CORE SERVICE (Orquestrador)                      │
│         api_gateway/services/gemini/core_service.py         │
├─────────────────────────────────────────────────────────────┤
│  def process_message(phone_number, message):                │
│    1. Obter sessão                                          │
│    2. Detectar intenção                                     │
│    3. Extrair entidades                                     │
│    4. Gerar resposta                                        │
│    5. Validar agendamento                                   │
│    6. Gerar handoff (se completo)                           │
│    7. Atualizar sessão                                      │
│    8. Salvar histórico                                      │
└──────┬──────────────────┬──────────────────┬───────────────┘
       │                  │                  │
       ▼                  ▼                  ▼
┌─────────────┐  ┌─────────────────┐  ┌──────────────────┐
│ SESSION     │  │ INTENT          │  │ ENTITY           │
│ MANAGER     │  │ DETECTOR        │  │ EXTRACTOR        │
├─────────────┤  ├─────────────────┤  ├──────────────────┤
│ - Obtém     │  │ - Analisa com   │  │ - Extrai com     │
│   sessão    │  │   Gemini        │  │   Gemini         │
│ - Atualiza  │  │ - Detecta       │  │ - Fallback       │
│   estado    │  │   intenção      │  │   regex          │
│ - Salva     │  │ - Next state    │  │ - Valida         │
│   mensagens │  │                 │  │   entidades      │
└─────────────┘  └─────────────────┘  └──────────────────┘
       │                  
       ▼                  
┌─────────────────┐
│ RESPONSE        │
│ GENERATOR       │
├─────────────────┤
│ - Gera resposta │
│   contextual    │
│ - Formata       │
│   mensagem      │
└─────────────────┘

       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│              SERVIÇOS DE APOIO                              │
├─────────────────────────────────────────────────────────────┤
│  ConversationService  │ SmartSchedulingService             │
│  RAGService          │ HandoffService                      │
│  GoogleCalendarService│ TokenMonitor                       │
└─────────────────────────────────────────────────────────────┘
```

---

## Fluxo Completo de Pré-Agendamento

### Sequência de Etapas

```
┌─────────────────────────────────────────────────────────────┐
│ ETAPA 1: SOLICITAÇÃO INICIAL                                │
└─────────────────────────────────────────────────────────────┘

👤 Paciente: "Olá, gostaria de agendar uma consulta"

🤖 CoreService.process_message():
   │
   ├─ SessionManager.get_or_create_session(phone)
   │  └─ Estado inicial: 'idle'
   │
   ├─ IntentDetector.analyze_message()
   │  └─ Intent: 'agendar_consulta', Confidence: 0.95
   │
   └─ ResponseGenerator.generate_response()
      └─ "Olá! Para começar, qual é o seu nome completo?"

Estado atualizado: idle → collecting_patient_info


┌─────────────────────────────────────────────────────────────┐
│ ETAPA 2: COLETA DE NOME                                     │
└─────────────────────────────────────────────────────────────┘

👤 Paciente: "Meu nome é João Silva Santos"

🤖 CoreService.process_message():
   │
   ├─ IntentDetector.analyze_message()
   │  └─ Intent: 'fornecer_nome'
   │
   ├─ EntityExtractor.extract_entities()
   │  ├─ Gemini extrai: "João Silva Santos"
   │  └─ Validação: nome tem >= 2 palavras ✓
   │
   ├─ Armazena nome temporário:
   │  ├─ session.pending_name = "João Silva Santos"
   │  └─ session.name_confirmed = False
   │
   └─ ResponseGenerator.generate_response()
      └─ "Prazer! Seu nome é João Silva Santos? (Sim/Não)"

Estado atualizado: collecting_patient_info → confirming_name


┌─────────────────────────────────────────────────────────────┐
│ ETAPA 3: CONFIRMAÇÃO DE NOME                                │
└─────────────────────────────────────────────────────────────┘

👤 Paciente: "Sim"

🤖 CoreService._handle_patient_name_flow():
   │
   ├─ Detecta confirmação positiva
   │  └─ Palavras: ['sim', 'confirmo', 'correto', ...]
   │
   ├─ Confirma nome:
   │  ├─ session.patient_name = session.pending_name
   │  ├─ session.name_confirmed = True
   │  └─ session.pending_name = None
   │
   └─ ResponseGenerator.generate_response()
      └─ "Perfeito, João Silva Santos! 👏
          Qual especialidade médica você precisa?"

Estado atualizado: confirming_name → selecting_specialty


┌─────────────────────────────────────────────────────────────┐
│ ETAPA 4: SELEÇÃO DE ESPECIALIDADE                           │
└─────────────────────────────────────────────────────────────┘

👤 Paciente: "Pneumologia"

🤖 CoreService.process_message():
   │
   ├─ EntityExtractor.extract_entities()
   │  └─ Especialidade extraída: "Pneumologia"
   │
   ├─ Validação com banco de dados:
   │  └─ Especialidade.objects.filter(
   │       nome__icontains="pneumologia",
   │       ativa=True
   │     ).first()
   │     └─ ✓ Especialidade válida encontrada
   │
   ├─ Atualiza sessão:
   │  └─ session.selected_specialty = "Pneumologia"
   │
   └─ ResponseGenerator + RAGService:
      └─ Lista médicos de Pneumologia
         "Temos os seguintes médicos de Pneumologia:
          👨‍⚕️ Dr. Gustavo - R$ 150,00
          Com qual médico você gostaria?"

Estado atualizado: selecting_specialty → selecting_doctor


┌─────────────────────────────────────────────────────────────┐
│ ETAPA 5: SELEÇÃO DE MÉDICO                                  │
└─────────────────────────────────────────────────────────────┘

👤 Paciente: "Dr. Gustavo"

🤖 CoreService.process_message():
   │
   ├─ EntityExtractor.extract_entities()
   │  └─ Médico extraído: "Dr. Gustavo"
   │
   ├─ Validação com banco de dados:
   │  └─ Medico.objects.filter(
   │       nome__icontains="gustavo",
   │       especialidades__nome="Pneumologia"
   │     ).first()
   │     └─ ✓ Médico válido encontrado
   │
   ├─ SmartSchedulingService.analyze_scheduling_request():
   │  │
   │  └─ GoogleCalendarService.get_doctor_availability():
   │     ├─ Consulta Google Calendar API
   │     ├─ Próximos 7 dias
   │     └─ Retorna horários disponíveis
   │
   ├─ Atualiza sessão:
   │  └─ session.selected_doctor = "Dr. Gustavo"
   │
   └─ ResponseGenerator.generate_response():
      └─ "Excelente escolha! 👨‍⚕️
          
          Dr. Gustavo
          🩺 Pneumologia, Medicina do Sono
          💰 R$ 150,00
          
          📅 Horários disponíveis:
          Segunda-feira (14/10): 08:00, 09:00, 14:00, 15:00
          Quarta-feira (16/10): 08:00, 09:00
          
          Qual data e horário seria melhor para você?"

Estado atualizado: selecting_doctor → choosing_schedule


┌─────────────────────────────────────────────────────────────┐
│ ETAPA 6: ESCOLHA DE DATA E HORÁRIO                          │
└─────────────────────────────────────────────────────────────┘

👤 Paciente: "Segunda-feira às 14h"

🤖 CoreService.process_message():
   │
   ├─ EntityExtractor.extract_entities():
   │  ├─ Data extraída: "segunda-feira"
   │  │  └─ Normalizada: "2024-10-14" (próxima segunda)
   │  └─ Horário extraído: "14h"
   │     └─ Normalizado: "14:00"
   │
   ├─ Validação de disponibilidade:
   │  └─ GoogleCalendarService.check_availability():
   │     └─ ✓ Horário disponível confirmado
   │
   ├─ Atualiza sessão:
   │  ├─ session.preferred_date = "2024-10-14"
   │  └─ session.preferred_time = "14:00"
   │
   └─ _validate_appointment_info():
      ├─ ✓ patient_name: "João Silva Santos"
      ├─ ✓ selected_doctor: "Dr. Gustavo"
      ├─ ✓ preferred_date: "2024-10-14"
      ├─ ✓ preferred_time: "14:00"
      └─ is_complete: True

Estado atualizado: choosing_schedule → confirming


┌─────────────────────────────────────────────────────────────┐
│ ETAPA 7: CONFIRMAÇÃO FINAL E GERAÇÃO DE HANDOFF             │
└─────────────────────────────────────────────────────────────┘

🤖 CoreService._handle_appointment_confirmation():
   │
   ├─ Validação final das informações:
   │  └─ Todas as informações obrigatórias presentes ✓
   │
   ├─ HandoffService.generate_appointment_handoff_link():
   │  │
   │  ├─ Cria mensagem formatada:
   │  │  """
   │  │  Olá, gostaria de confirmar meu pré-agendamento:
   │  │  
   │  │  👤 Paciente: João Silva Santos
   │  │  👨‍⚕️ Médico: Dr. Gustavo
   │  │  📅 Data: 14/10/2024 (Segunda-feira)
   │  │  🕐 Horário: 14:00
   │  │  """
   │  │
   │  ├─ URL encode da mensagem
   │  │
   │  └─ Gera link WhatsApp:
   │     https://wa.me/5573988221003?text=Ol%C3%A1%2C%20gostaria...
   │
   └─ ResponseGenerator.generate_response():
      └─ "✅ Perfeito! Vamos confirmar seu pré-agendamento:
          
          📋 RESUMO:
          👤 Paciente: João Silva Santos
          👨‍⚕️ Médico: Dr. Gustavo
          📅 Data: Segunda-feira, 14/10/2024
          🕐 Horário: 14:00
          
          🔄 Para CONFIRMAR definitivamente:
          👩‍💼 Nossa secretária validará a disponibilidade.
          
          📞 Clique no link para falar com nossa equipe:
          https://wa.me/5573988221003?text=..."

Estado final: confirming

👤 Paciente clica no link → Conversa abre com secretária
```

---

## Módulos e Responsabilidades

### 1. CoreService - Orquestrador Principal
**Arquivo:** `api_gateway/services/gemini/core_service.py`

```python
class GeminiChatbotService:
    """Orquestrador Principal do Chatbot"""
    
    def process_message(self, phone_number: str, message: str) -> Dict[str, Any]:
        """
        Processa mensagem do usuário - Método Principal
        
        Fluxo:
        1. Obter/criar sessão
        2. Verificar agendamento pausado (pausar/retomar)
        3. Obter histórico e dados da clínica
        4. Detectar intenção
        5. Extrair entidades
        6. Tratar fluxo de nome (se aplicável)
        7. Detectar pausar para dúvidas
        8. Consultar disponibilidade (se agendamento)
        9. Gerar resposta
        10. Verificar confirmação de agendamento
        11. Atualizar sessão
        12. Salvar histórico
        13. Retornar resultado
        """
```

**Responsabilidades:**
- ✅ Coordena todos os módulos
- ✅ Gerencia fluxo completo
- ✅ Trata casos especiais
- ✅ Valida informações
- ✅ Gera handoff

---

### 2. SessionManager - Gerenciamento de Sessões
**Arquivo:** `api_gateway/services/gemini/session_manager.py`

```python
class SessionManager:
    """Gerenciamento de sessões e persistência"""
    
    def get_or_create_session(self, phone_number: str) -> Dict:
        """Obtém ou cria sessão do cache ou banco"""
        
    def update_session(self, phone_number: str, session: Dict,
                      analysis: Dict, response: Dict):
        """Atualiza sessão com novos dados"""
        
    def save_messages(self, phone_number: str, user_msg: str,
                     bot_response: str, analysis: Dict):
        """Salva mensagens no histórico do banco"""
        
    def get_conversation_history(self, phone_number: str, limit: int = 10) -> List:
        """Obtém histórico de mensagens"""
```

**Responsabilidades:**
- ✅ Gerencia sessões (cache + banco)
- ✅ Atualiza estados da conversa
- ✅ Persiste mensagens
- ✅ Sincroniza cache com banco
- ✅ Obtém histórico

---

### 3. IntentDetector - Detecção de Intenções
**Arquivo:** `api_gateway/services/gemini/intent_detector.py`

```python
class IntentDetector:
    """Detecção de intenções do usuário"""
    
    def analyze_message(self, message: str, session: Dict,
                       conversation_history: List, clinic_data: Dict) -> Dict[str, Any]:
        """
        Analisa mensagem com Gemini para identificar intenção
        
        Returns:
            {
                'intent': 'agendar_consulta',
                'next_state': 'collecting_patient_info',
                'confidence': 0.95,
                'reasoning': 'Usuário solicitou agendamento'
            }
        """
```

**Responsabilidades:**
- ✅ Detecta intenção com Gemini
- ✅ Determina próximo estado
- ✅ Calcula confiança
- ✅ Monitora tokens

**Intenções detectadas:**
- `saudacao` - Saudação inicial
- `agendar_consulta` - Solicitação de agendamento
- `fornecer_nome` - Fornecimento de nome
- `confirmar` - Confirmação
- `buscar_info` - Busca de informações
- `buscar_medico` - Busca médico específico
- `buscar_horarios` - Consulta horários
- `confirmar_agendamento` - Confirmação final
- `duvida` - Pergunta/dúvida

---

### 4. EntityExtractor - Extração de Entidades
**Arquivo:** `api_gateway/services/gemini/entity_extractor.py`

```python
class EntityExtractor:
    """Extração de entidades das mensagens"""
    
    def extract_entities(self, message: str, session: Dict,
                        conversation_history: List, clinic_data: Dict) -> Dict[str, str]:
        """
        Extrai entidades (Gemini primário, regex fallback)
        
        Returns:
            {
                'nome_paciente': 'João Silva Santos',
                'medico': 'Dr. Gustavo',
                'especialidade': 'Pneumologia',
                'data': '14/10/2024',
                'horario': '14:00'
            }
        """
    
    def extract_entities_with_gemini(self, ...) -> Dict:
        """Extrai entidades usando Gemini AI"""
        
    def extract_entities_with_regex(self, message: str) -> Dict:
        """Fallback com regex patterns"""
        
    def validate_entities(self, entities: Dict) -> Dict:
        """Valida e normaliza entidades"""
```

**Responsabilidades:**
- ✅ Extrai entidades com Gemini (primário)
- ✅ Fallback com regex
- ✅ Valida entidades
- ✅ Normaliza dados (datas, nomes)
- ✅ Monitora tokens

**Entidades extraídas:**
- `nome_paciente` - Nome completo
- `medico` - Nome do médico
- `especialidade` - Especialidade médica
- `data` - Data da consulta
- `horario` - Horário da consulta
- `convenio` - Convênio (opcional)

---

### 5. ResponseGenerator - Geração de Respostas
**Arquivo:** `api_gateway/services/gemini/response_generator.py`

```python
class ResponseGenerator:
    """Geração de respostas contextualizadas"""
    
    def generate_response(self, message: str, intent: str,
                         entities: Dict, session: Dict,
                         conversation_history: List, clinic_data: Dict) -> str:
        """
        Gera resposta apropriada usando Gemini
        
        Returns:
            Resposta formatada e contextualizada
        """
```

**Responsabilidades:**
- ✅ Gera respostas com Gemini
- ✅ Contextualiza com histórico
- ✅ Inclui dados relevantes
- ✅ Formata mensagem
- ✅ Monitora tokens

---

## Estados da Conversa

### Máquina de Estados

```
┌──────┐
│ idle │ ← Estado inicial
└───┬──┘
    │ Intenção: agendar_consulta
    ▼
┌──────────────────────┐
│collecting_patient_info│ ← Coleta nome
└──────────┬───────────┘
           │ Nome extraído
           ▼
┌─────────────────┐
│confirming_name  │ ← Confirma nome
└────────┬────────┘
         │ Nome confirmado
         ▼
┌────────────────────┐
│selecting_specialty │ ← Escolhe especialidade
└─────────┬──────────┘
          │ Especialidade válida
          ▼
┌──────────────────┐
│selecting_doctor  │ ← Escolhe médico
└────────┬─────────┘
         │ Médico válido
         ▼
┌─────────────────┐
│choosing_schedule│ ← Data + Hora
└────────┬────────┘
         │ Informações completas
         ▼
┌──────────────┐
│confirming    │ ← Validação final + Handoff
└──────────────┘
```

### Sistema de Pausar/Retomar

```
[Estado de agendamento]
         │
         │ Usuário faz pergunta
         ▼
┌────────────────────┐
│answering_questions │ ← Pausa agendamento
│previous_state=X    │   Salva estado anterior
└─────────┬──────────┘
          │ Usuário: "continuar"
          ▼
[Estado X restaurado] ← Retoma de onde parou
```

---

## Validações e Confirmações

### 1. Validação de Nome

```python
# core_service.py
def _handle_patient_name_flow(self, phone_number, session, message, analysis):
    """
    Fluxo dedicado para confirmação precoce do nome
    
    Estados: confirming_name
    
    Lógica:
    1. Extrai nome da mensagem
    2. Armazena em pending_name
    3. Solicita confirmação
    4. Se "sim": pending_name → patient_name, name_confirmed=True
    5. Se "não": limpa pending_name, volta a pedir
    """
```

### 2. Validação de Especialidade

```python
# entity_extractor.py
def _validate_specialty(self, specialty_name: str) -> Optional[str]:
    """
    Valida especialidade com banco de dados
    
    1. Busca exata (case-insensitive)
    2. Busca parcial (contém)
    3. Retorna nome correto ou None
    """
    # Query 1: Busca exata
    especialidade = Especialidade.objects.filter(
        nome__iexact=specialty_name,
        ativa=True
    ).first()
    
    if not especialidade:
        # Query 2: Busca parcial
        especialidade = Especialidade.objects.filter(
            nome__icontains=specialty_name,
            ativa=True
        ).first()
    
    return especialidade.nome if especialidade else None
```

### 3. Validação de Médico

```python
# entity_extractor.py
def _validate_doctor(self, doctor_name: str, specialty: str = None) -> Optional[str]:
    """
    Valida médico com banco de dados
    
    1. Busca por nome (case-insensitive)
    2. Filtra por especialidade se fornecida
    3. Retorna nome correto ou None
    """
    query = Medico.objects.filter(nome__icontains=doctor_name)
    
    if specialty:
        query = query.filter(especialidades__nome=specialty)
    
    medico = query.first()
    return medico.nome if medico else None
```

### 4. Validação de Agendamento Completo

```python
# core_service.py
def _validate_appointment_info(self, session: Dict, analysis: Dict) -> Dict[str, Any]:
    """
    Valida se todas as informações necessárias foram coletadas
    
    Informações obrigatórias:
    - patient_name
    - selected_doctor
    - preferred_date
    - preferred_time
    
    Returns:
        {
            'is_complete': True/False,
            'missing_info': [],
            'message': 'Mensagem para solicitar info faltante'
        }
    """
    required_info = {
        'nome_paciente': session.get('patient_name'),
        'medico': session.get('selected_doctor'),
        'data': session.get('preferred_date'),
        'horario': session.get('preferred_time')
    }
    
    missing = [k for k, v in required_info.items() if not v]
    
    return {
        'is_complete': len(missing) == 0,
        'missing_info': missing,
        'message': self._get_missing_info_message(missing[0]) if missing else None
    }
```

---

## Handoff para Secretária

### Geração de Link de Handoff

```python
# handoff_service.py
def generate_appointment_handoff_link(self, patient_name: str, 
                                     doctor_name: str,
                                     date: str, time: str,
                                     appointment_type: str = 'Consulta') -> str:
    """
    Gera link de handoff para WhatsApp da secretária
    
    Fluxo:
    1. Cria mensagem formatada
    2. URL encode da mensagem
    3. Gera link WhatsApp
    
    Returns:
        Link WhatsApp com mensagem pré-preenchida
    """
    # 1. Criar mensagem formatada
    base_message = f"""Olá, gostaria de confirmar meu pré-agendamento:

👤 Paciente: {patient_name}
👨‍⚕️ Médico: {doctor_name}
📅 Data: {date}
🕐 Horário: {time}
📋 Tipo: {appointment_type}"""
    
    # 2. URL encode
    import urllib.parse
    encoded_message = urllib.parse.quote(base_message)
    
    # 3. Gerar link
    clinic_whatsapp = settings.CLINIC_WHATSAPP_NUMBER
    handoff_link = f"https://wa.me/{clinic_whatsapp}?text={encoded_message}"
    
    return handoff_link
```

### Exemplo de Link Gerado

```
https://wa.me/5573988221003?text=Ol%C3%A1%2C%20gostaria%20de%20confirmar%20meu%20pr%C3%A9-agendamento%3A%0A%0A%F0%9F%91%A4%20Paciente%3A%20Jo%C3%A3o%20Silva%20Santos%0A%F0%9F%91%A8%E2%80%8D%E2%9A%95%EF%B8%8F%20M%C3%A9dico%3A%20Dr.%20Gustavo%0A%F0%9F%93%85%20Data%3A%2014%2F10%2F2024%0A%F0%9F%95%90%20Hor%C3%A1rio%3A%2014%3A00%0A%F0%9F%93%8B%20Tipo%3A%20Consulta
```

**Ao clicar no link:**
1. WhatsApp abre automaticamente
2. Conversa com secretária é iniciada
3. Mensagem pré-formatada já está digitada
4. Paciente só precisa enviar

---

## Persistência de Dados

### Sincronização Cache + Banco

```
┌────────────────┐
│     CACHE      │ ← Acesso rápido (< 1ms)
└───────┬────────┘
        │ Sincronização automática
        ▼
┌────────────────┐
│  BANCO DADOS   │ ← Persistência (SQLite/PostgreSQL)
└────────────────┘

Fluxo de atualização:
1. Leitura: Cache primeiro → Se não existe: Banco → Popula cache
2. Escrita: Atualiza cache + Sincroniza banco (assíncrono)
3. Mensagens: Grava direto no banco
```

**Campos da Sessão:**
```python
ConversationSession:
- phone_number (unique)
- patient_name
- pending_name (temporário)
- name_confirmed (flag)
- current_state
- previous_state (pausar/retomar)
- selected_specialty
- selected_doctor
- preferred_date
- preferred_time
- created_at
- updated_at
- last_activity
```

---

## Tratamento de Erros

### 1. Informações Faltantes

```python
# Se usuário pular etapas
if missing_info:
    next_action = _get_next_action(missing_info)
    return {
        'response': _get_missing_info_message(next_action),
        'state': current_state  # Mantém estado até coletar
    }
```

### 2. Médico Não Encontrado

```python
# Médico não existe ou não tem especialidade
if not medico:
    return {
        'response': f"❌ Não encontrei o médico '{doctor_name}' em {specialty}.
                    
                    Nossos médicos de {specialty} são:
                    {list_doctors_of_specialty(specialty)}
                    
                    Com qual deles você gostaria de agendar?",
        'state': 'selecting_doctor'
    }
```

### 3. Horário Indisponível

```python
# Horário solicitado não está livre
if not is_available:
    return {
        'response': f"❌ O horário {time} em {date} não está disponível.
                    
                    📅 Horários disponíveis:
                    {format_available_times(available_slots)}
                    
                    Qual desses horários seria melhor para você?",
        'state': 'choosing_schedule'
    }
```

---

## Conclusão

### Arquitetura Modularizada Implementada

O sistema de pré-agendamento foi refatorado com **5 módulos especializados**:

1. **CoreService** - Orquestrador principal
2. **SessionManager** - Gerencia sessões e persistência
3. **IntentDetector** - Detecta intenções
4. **EntityExtractor** - Extrai entidades (Gemini + regex)
5. **ResponseGenerator** - Gera respostas contextualizadas

### Fluxo Completo Implementado

```
WhatsApp → CoreService → {
    SessionManager,
    IntentDetector,
    EntityExtractor,
    ResponseGenerator
} → Validações → Handoff → Secretária
```

### Funcionalidades Principais

- ✅ **Coleta sequencial** de informações
- ✅ **Confirmação de nome** com pending_name
- ✅ **Validação** com banco de dados
- ✅ **Consulta de disponibilidade** real (Google Calendar)
- ✅ **Sistema pausar/retomar** para dúvidas
- ✅ **Handoff inteligente** para secretária
- ✅ **Persistência dual** (cache + banco)

---

**📅 Última Atualização:** Novembro 15, 2025  
**📝 Versão:** 3.0 (Modularizada)  
**✅ Status:** Documentação completa e atualizada
