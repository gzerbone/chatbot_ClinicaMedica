# 📅 Implementação da Lógica de Pré-Agendamento - Atualizada 09/10 (mais recente)

## 📋 Índice
- [Visão Geral](#visão-geral)
- [Resposta à Pergunta do Usuário](#resposta-à-pergunta-do-usuário)
- [Arquitetura do Sistema](#arquitetura-do-sistema)
- [Fluxo Completo de Pré-Agendamento](#fluxo-completo-de-pré-agendamento)
- [Módulos e Serviços](#módulos-e-serviços)
- [Estados da Conversa](#estados-da-conversa)
- [Validações e Confirmações](#validações-e-confirmações)
- [Integração com Google Calendar](#integração-com-google-calendar)
- [Handoff para Secretária](#handoff-para-secretária)

---

## Visão Geral

O sistema de **pré-agendamento** é responsável por conduzir o paciente através de um fluxo conversacional inteligente, coletando informações necessárias para o agendamento e gerando um link de **handoff** para confirmação final com a secretária.

### Objetivo Principal
Automatizar a **coleta de informações** e **validação inicial** de agendamentos, reduzindo carga de trabalho da secretária e melhorando experiência do paciente.

---

## Resposta à Pergunta do Usuário

### ❓ Pergunta
> **"Este módulo será responsável por orquestrar todo o fluxo de agendamento, desde a solicitação inicial até a confirmação do usuário."**

### ✅ Resposta: **SIM, ESTE MÓDULO ORQUESTRADOR ESTÁ IMPLEMENTADO NO PROJETO**

### 📍 Onde está implementado?

#### 1. **Módulo Orquestrador Principal**

**Arquivo:** `api_gateway/services/gemini_chatbot_service.py`

**Classe:** `GeminiChatbotService`

**Descrição:** Este serviço é o **protagonista principal do chatbot** e **orquestra todo o fluxo de agendamento** conforme descrito na pergunta.

```python
# gemini_chatbot_service.py (linhas 21-29)
class GeminiChatbotService:
    """
    Serviço Gemini Centralizado - Protagonista Principal do Chatbot
    
    Este serviço é responsável por:
    1. Gerenciar todo o fluxo de conversação
    2. Identificar intenções e estados da conversa
    3. Responder pacientes com base nas informações do RAG
    4. Coordenar pré-agendamentos e informações da clínica
    """
```

#### 2. **Método Principal de Orquestração**

**Arquivo:** `api_gateway/services/gemini_chatbot_service.py` (linhas 84-163)

```python
def process_message(self, phone_number: str, message: str) -> Dict[str, Any]:
    """
    Processa mensagem do usuário usando o Gemini como protagonista principal
    
    ORQUESTRA TODO O FLUXO:
    1. Obtém sessão da conversa
    2. Obtém dados da clínica
    3. Obtém histórico da conversa
    4. Verifica se é solicitação de horários
    5. Analisa mensagem com Gemini
    6. Gera resposta com Gemini
    7. Verifica confirmação de agendamento
    8. Valida informações completas
    9. Gera handoff se tudo estiver OK
    10. Atualiza sessão
    11. Salva mensagens no histórico
    """
    try:
        # 1. Obter sessão da conversa
        session = self._get_or_create_session(phone_number)
        
        # 2. Obter dados da clínica de forma otimizada
        clinic_data = self._get_clinic_data_optimized()
        
        # 3. Obter histórico da conversa
        conversation_history = self._get_conversation_history(phone_number)
        
        # 4. Verificar se é solicitação de horários
        if self._is_scheduling_request(message):
            scheduling_result = smart_scheduling_service.analyze_scheduling_request(message, session)
            # ... processa solicitação de horários
        else:
            # 5. Análise com Gemini
            analysis_result = self._analyze_message_with_gemini(
                message, session, conversation_history, clinic_data
            )

            # 6. Gerar resposta com Gemini
            response_result = self._generate_response_with_gemini(
                message, analysis_result, session, conversation_history, clinic_data
            )
        
        # 7. Verificar se é confirmação de agendamento
        if analysis_result['intent'] == 'confirmar_agendamento':
            # 8. Validar informações de agendamento
            validation_result = self._validate_appointment_info(session, analysis_result)
            
            if validation_result['is_complete']:
                # 9. GERAR HANDOFF - Todas as informações presentes
                handoff_result = self._handle_appointment_confirmation(phone_number, session, analysis_result)
                if handoff_result:
                    response_result['response'] = handoff_result['message']
                    response_result['handoff_link'] = handoff_result['handoff_link']
            else:
                # Informações faltantes - solicitar
                response_result['response'] = validation_result['message']
        
        # 10. Atualizar sessão
        self._update_session(phone_number, session, analysis_result, response_result)
        
        # 11. Salvar mensagens no histórico
        self._save_conversation_messages(phone_number, message, response_result['response'], analysis_result)
```

#### 3. **Serviços de Apoio**

##### **a) ConversationService** - Gerenciamento de Sessões
**Arquivo:** `api_gateway/services/conversation_service.py`

```python
# conversation_service.py (linhas 24-427)
class ConversationService:
    """
    Serviço para gerenciar conversas de agendamento com persistência
    """
    
    # Métodos principais:
    - get_or_create_session()      # Obtém ou cria sessão
    - add_message()                 # Adiciona mensagem ao histórico
    - get_conversation_history()    # Obtém histórico
    - update_patient_info()         # Atualiza informações do paciente
    - get_patient_info()            # Obtém informações do paciente
    - check_required_info()         # Verifica informações obrigatórias
    - process_patient_name()        # Processa nome com confirmação
    - confirm_patient_name()        # Confirma nome do paciente
    - finalize_session()            # Finaliza sessão
```

##### **b) SmartSchedulingService** - Consulta de Horários
**Arquivo:** `api_gateway/services/smart_scheduling_service.py`

```python
# smart_scheduling_service.py (linhas 17-586)
class SmartSchedulingService:
    """
    Serviço de Consulta de Horários
    
    Responsável por:
    1. Consultar disponibilidade real no Google Calendar
    2. Informar horários disponíveis para o médico escolhido
    3. Otimizar fluxo de conversa para evitar repetições
    4. Fornecer informações claras sobre agenda do médico
    """
    
    # Métodos principais:
    - analyze_scheduling_request()       # Analisa solicitação de horários
    - _validate_doctor()                 # Valida se médico existe
    - _get_doctor_availability()         # Consulta disponibilidade
    - _check_real_availability()         # Verifica horário específico
    - _handle_appointment_confirmation() # Processa confirmação e gera handoff
```

### 📊 Resumo: Módulo Orquestrador

| Aspecto | Implementação |
|---------|---------------|
| **Orquestração do Fluxo** | ✅ GeminiChatbotService.process_message() |
| **Solicitação Inicial** | ✅ Detecta intenção de agendamento |
| **Coleta de Informações** | ✅ Estados progressivos (nome → médico → data → horário) |
| **Validação** | ✅ _validate_appointment_info() |
| **Confirmação** | ✅ _handle_appointment_confirmation() |
| **Handoff** | ✅ handoff_service.generate_appointment_handoff_link() |

**Conclusão:** O módulo orquestrador está **COMPLETO E FUNCIONAL**, gerenciando todo o ciclo desde a solicitação até a confirmação.

---

## Arquitetura do Sistema

### **Módulos Responsáveis**

A orquestração do fluxo de agendamento é distribuída entre **4 serviços principais**:

```
┌─────────────────────────────────────────────────────────┐
│         GEMINI CHATBOT SERVICE                          │
│         (Orquestrador Principal)                        │
│                                                         │
│  • Recebe mensagem do usuário                          │
│  • Analisa intenção e extrai entidades                 │
│  • Coordena fluxo de agendamento                       │
│  • Valida informações coletadas                        │
│  • Aciona handoff quando completo                      │
└───────┬──────────────────────┬──────────────────────────┘
        │                      │
        │                      │
┌───────▼──────────┐  ┌────────▼──────────────┐
│ CONVERSATION     │  │ SMART SCHEDULING      │
│ SERVICE          │  │ SERVICE               │
│                  │  │                       │
│ • Persistência   │  │ • Consulta horários   │
│ • Sessões        │  │ • Google Calendar     │
│ • Histórico      │  │ • Validação médicos   │
└──────────────────┘  └───────────────────────┘
        │
        │
┌───────▼──────────┐
│ HANDOFF          │
│ SERVICE          │
│                  │
│ • Gera links     │
│ • Transferência  │
│ • WhatsApp       │
└──────────────────┘
```

### Diagrama de Componentes

```
┌────────────────────────────────────────────────────────────────┐
│                    SISTEMA DE PRÉ-AGENDAMENTO                   │
├────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐   │
│  │         ORQUESTRADOR PRINCIPAL                          │   │
│  │      GeminiChatbotService.process_message()             │   │
│  └─────────────┬──────────────────────────────────────────┘   │
│                │                                                │
│                ├──► ConversationService (Gerencia Sessões)      │
│                │                                                │
│                ├──► SmartSchedulingService (Horários)           │
│                │                                                │
│                ├──► RAGService (Dados da Clínica)               │
│                │                                                │
│                ├──► GoogleCalendarService (Disponibilidade)     │
│                │                                                │
│                ├──► HandoffService (Link de Transferência)      │
│                │                                                │
│                └──► TokenMonitor (Otimização de Tokens)         │
│                                                                  │
└────────────────────────────────────────────────────────────────┘
```

---

## Fluxo Completo de Pré-Agendamento

### Visão Geral do Fluxo

```
┌────────────────────────────────────────────────────────────────┐
│                    FLUXO DE PRÉ-AGENDAMENTO                     │
└────────────────────────────────────────────────────────────────┘

┌─────────────┐
│ 1. SAUDAÇÃO │
└──────┬──────┘
       │ "Olá, bom dia!"
       ▼
┌─────────────────┐
│ 2. COLETAR NOME │ ◄─── Estado: collecting_patient_info
└──────┬──────────┘       "Qual é o seu nome completo?"
       │ "João Silva"
       ▼
┌──────────────────────┐
│ 3. CONFIRMAR NOME    │ ◄─── Estado: confirming_name
└──────┬───────────────┘       "Confirma que seu nome é João Silva?"
       │ "Sim"
       ▼
┌──────────────────────┐
│ 4. SELECIONAR MÉDICO │ ◄─── Estado: selecting_doctor
└──────┬───────────────┘       "Com qual médico deseja agendar?"
       │ "Dr. Gustavo"
       ▼
┌──────────────────────┐
│ 5. CONSULTAR HORÁRIOS│ ◄─── SmartSchedulingService
└──────┬───────────────┘       Consulta Google Calendar
       │                        Mostra horários disponíveis
       ▼
┌──────────────────────┐
│ 6. ESCOLHER DATA     │ ◄─── Estado: choosing_schedule
└──────┬───────────────┘       "Qual data prefere?"
       │ "15/10/2024"
       ▼
┌──────────────────────┐
│ 7. ESCOLHER HORÁRIO  │ ◄─── Estado: choosing_schedule
└──────┬───────────────┘       "Qual horário?"
       │ "14:30"
       ▼
┌──────────────────────┐
│ 8. VALIDAR COMPLETO  │ ◄─── _validate_appointment_info()
└──────┬───────────────┘       Verifica: nome ✓ médico ✓ data ✓ hora ✓
       │
       ▼
┌──────────────────────┐
│ 9. GERAR HANDOFF     │ ◄─── Estado: confirming
└──────┬───────────────┘       handoff_service.generate_link()
       │
       ▼
┌──────────────────────┐
│ 10. ENVIAR LINK      │ ◄─── Paciente clica e vai para WhatsApp da secretária
└──────────────────────┘       Secretária confirma agendamento final
```

---

## Estados da Conversa

### Máquina de Estados

**Arquivo:** `api_gateway/models.py` (linhas 16-27)

```python
current_state = models.CharField(
    max_length=50,
    choices=[
        ('idle', 'Ocioso'),                                    # Estado inicial
        ('collecting_patient_info', 'Coletando Dados do Paciente'),
        ('collecting_info', 'Coletando Informações'),
        ('confirming_name', 'Confirmando Nome do Paciente'),
        ('selecting_doctor', 'Selecionando Médico'),
        ('choosing_schedule', 'Escolhendo Horário'),
        ('confirming', 'Confirmando')                          # Estado final
    ],
    default='idle'
)
```

### Transições de Estado

```
┌──────┐
│ idle │ ◄──────────────────────────┐
└───┬──┘                             │
    │                                │
    │ Saudação                       │
    ▼                                │
┌─────────────────────┐              │
│collecting_patient_  │              │
│      info           │              │
└────────┬────────────┘              │
         │                           │
         │ Nome extraído             │
         ▼                           │
┌─────────────────────┐              │
│  confirming_name    │              │
└────────┬────────────┘              │
         │                           │
         │ Nome confirmado           │
         ▼                           │
┌─────────────────────┐              │
│ selecting_doctor    │              │
└────────┬────────────┘              │
         │                           │
         │ Médico selecionado        │
         ▼                           │
┌─────────────────────┐              │
│ choosing_schedule   │              │
└────────┬────────────┘              │
         │                           │
         │ Data + Horário escolhidos │
         ▼                           │
┌─────────────────────┐              │
│    confirming       │              │
└────────┬────────────┘              │
         │                           │
         │ Handoff enviado           │
         └───────────────────────────┘
```

### Gerenciamento de Estados

**Arquivo:** `api_gateway/services/gemini_chatbot_service.py` (linhas 752-856)

```python
def _update_session(self, phone_number: str, session: Dict, 
                   analysis_result: Dict, response_result: Dict):
    """
    Atualiza sessão com base na análise e resposta
    """
    # Atualizar estado
    session['current_state'] = analysis_result['next_state']
    session['last_activity'] = timezone.now().isoformat()
    
    # Atualizar entidades extraídas
    entities = analysis_result['entities']
    
    # Atualizar nome do paciente
    if entities.get('nome_paciente'):
        session['patient_name'] = entities['nome_paciente']
        logger.info(f"✅ Nome atualizado: {entities['nome_paciente']}")
    
    # Atualizar médico selecionado
    if entities.get('medico'):
        session['selected_doctor'] = entities['medico']
        logger.info(f"✅ Médico atualizado: {entities['medico']}")
    
    # Atualizar data preferida
    if entities.get('data'):
        normalized_date = self._normalize_date_for_database(entities['data'])
        if normalized_date:
            session['preferred_date'] = normalized_date
            logger.info(f"✅ Data atualizada: {normalized_date}")
    
    # Atualizar horário preferido
    if entities.get('horario'):
        session['preferred_time'] = entities['horario']
        logger.info(f"✅ Horário atualizado: {entities['horario']}")
    
    # Salvar sessão em cache
    cache_key = f"gemini_session_{phone_number}"
    cache.set(cache_key, session, token_monitor.get_cache_timeout())
    
    # Sincronizar com banco de dados
    self._sync_session_to_database(phone_number, session)
```

---

## Validações e Confirmações

### 1. **Validação de Informações Completas**

**Arquivo:** `api_gateway/services/gemini_chatbot_service.py` (linhas 1190-1254)

```python
def _validate_appointment_info(self, session: Dict, analysis_result: Dict) -> Dict[str, Any]:
    """
    Valida informações de agendamento e retorna status completo
    
    VERIFICA SE TEM:
    - Nome do paciente
    - Médico selecionado
    - Data preferida
    - Horário preferido
    """
    entities = analysis_result.get('entities', {})
    patient_name = session.get('patient_name', 'Paciente')
    
    # Mapear informações obrigatórias
    required_info = {
        'nome_paciente': {
            'entity_key': 'nome_paciente',
            'session_key': 'patient_name',
            'message': f"Olá, {patient_name}! Para prosseguir com o agendamento, preciso confirmar seu nome completo."
        },
        'medico': {
            'entity_key': 'medico',
            'session_key': 'selected_doctor',
            'message': f"Perfeito, {patient_name}! Agora preciso saber com qual médico você gostaria de agendar."
        },
        'data': {
            'entity_key': 'data',
            'session_key': 'preferred_date',
            'message': f"Ótimo! Agora preciso saber quando você gostaria de agendar."
        },
        'horario': {
            'entity_key': 'horario',
            'session_key': 'preferred_time',
            'message': f"Perfeito! E qual horário seria mais conveniente para você?"
        }
    }
    
    # Verificar cada informação obrigatória
    missing_info = []
    for info_key, info_config in required_info.items():
        has_info = bool(
            entities.get(info_config['entity_key']) or 
            session.get(info_config['session_key'])
        )
        if not has_info:
            missing_info.append(info_key)
    
    # Retornar status completo
    is_complete = len(missing_info) == 0
    
    if is_complete:
        return {
            'is_complete': True,
            'missing_info': [],
            'message': None
        }
    else:
        # Retornar mensagem para a primeira informação faltante
        first_missing = missing_info[0]
        return {
            'is_complete': False,
            'missing_info': missing_info,
            'message': required_info[first_missing]['message']
        }
```

### 2. **Confirmação de Nome do Paciente**

**Arquivo:** `api_gateway/services/conversation_service.py` (linhas 331-407)

```python
def process_patient_name(self, phone_number: str, message: str) -> Dict[str, Any]:
    """
    Processa nome do paciente com confirmação
    """
    session = self.get_or_create_session(phone_number)
    
    # Extrair nome da mensagem
    extracted_name = self.extract_patient_name(message)
    
    if extracted_name:
        # Armazenar nome pendente de confirmação
        session.pending_name = extracted_name
        session.save()
        
        return {
            'status': 'confirmation_needed',
            'message': f'Confirma se seu nome é {extracted_name}?',
            'extracted_name': extracted_name
        }

def confirm_patient_name(self, phone_number: str, confirmation: str) -> Dict[str, Any]:
    """
    Confirma ou rejeita o nome do paciente
    """
    session = self.get_or_create_session(phone_number)
    
    # Verificar confirmação
    confirmation_lower = confirmation.lower()
    if any(word in confirmation_lower for word in ['sim', 's', 'yes', 'confirmo']):
        # Confirmar nome
        session.patient_name = session.pending_name
        session.name_confirmed = True
        session.pending_name = None
        session.save()
        
        return {
            'status': 'confirmed',
            'message': f'Perfeito, {session.patient_name}! Como posso ajudá-lo hoje?',
            'patient_name': session.patient_name
        }
    else:
        # Rejeitar nome
        session.pending_name = None
        session.save()
        
        return {
            'status': 'rejected',
            'message': 'Entendi. Por favor, digite seu nome completo novamente.'
        }
```

---

## Integração com Google Calendar

### Consulta de Disponibilidade

**Arquivo:** `api_gateway/services/smart_scheduling_service.py` (linhas 273-314)

```python
def _get_doctor_availability(self, doctor_name: str, date_filter: str = None) -> Dict[str, Any]:
    """
    Consulta disponibilidade do médico no Google Calendar
    """
    try:
        # Consultar disponibilidade para os próximos 7 dias
        availability = self.calendar_service.get_doctor_availability(
            doctor_name=doctor_name,
            days_ahead=7
        )
        
        if not availability:
            return {
                'available': False,
                'reason': 'calendar_error',
                'message': 'Erro ao consultar agenda'
            }
        
        # Filtrar por data se especificada
        days_info = availability.get('days', [])
        if date_filter:
            target_date = self._parse_date(date_filter)
            if target_date:
                # Filtrar apenas o dia solicitado
                filtered_days = [day for day in days_info 
                               if datetime.strptime(day['date'], '%d/%m/%Y').date() == target_date]
                days_info = filtered_days
        
        return {
            'available': len(days_info) > 0,
            'doctor': doctor_name,
            'days': days_info,
            'total_days': len(days_info)
        }
        
    except Exception as e:
        logger.error(f"Erro ao consultar disponibilidade: {e}")
        return {
            'available': False,
            'reason': 'error',
            'message': 'Erro ao consultar disponibilidade'
        }
```

### Exemplo de Resposta ao Paciente

```
👨‍⚕️ Dr. Gustavo
🩺 Medicina do Sono, Pneumologia
💰 Consulta particular: R$ 150,00

📅 Horários disponíveis:

Segunda-feira (14/10/2024):
✅ Disponíveis: 08:00, 09:00, 10:00, 14:00, 15:00, 16:00

Quarta-feira (16/10/2024):
✅ Disponíveis: 08:00, 09:00, 14:00, 15:00

📞 Para agendar:
(73) 3613-5380 | (73) 98822-1003
```

---

## Handoff para Secretária

### Geração de Link de Handoff

**Arquivo:** `api_gateway/services/gemini_chatbot_service.py` (linhas 1256-1313)

```python
def _handle_appointment_confirmation(self, phone_number: str, session: Dict, analysis_result: Dict) -> Optional[Dict]:
    """
    Processa confirmação de agendamento e gera handoff
    """
    try:
        # Obter informações da sessão e entidades
        entities = analysis_result.get('entities', {})
        
        # Extrair informações com fallbacks
        patient_name = entities.get('nome_paciente') or session.get('patient_name') or 'Paciente'
        doctor_name = entities.get('medico') or session.get('selected_doctor') or 'Médico'
        date_mentioned = entities.get('data') or session.get('preferred_date') or 'Data a definir'
        time_mentioned = entities.get('horario') or session.get('preferred_time') or 'Horário a definir'
        
        # Gerar link de handoff
        from .handoff_service import handoff_service
        
        handoff_link = handoff_service.generate_appointment_handoff_link(
            patient_name=patient_name,
            doctor_name=doctor_name,
            date=date_mentioned,
            time=time_mentioned,
            appointment_type='Consulta'
        )
        
        # Criar mensagem de confirmação
        patient_info = {
            'patient_name': patient_name,
            'appointment_type': 'Consulta'
        }
        
        confirmation_message = handoff_service.create_confirmation_message(
            doctor_name=doctor_name,
            date=str(date_mentioned),
            time=str(time_mentioned),
            patient_info=patient_info
        )
        
        # Adicionar o link de handoff à mensagem
        confirmation_message += f"\n{handoff_link}"
        
        return {
            'message': confirmation_message,
            'handoff_link': handoff_link
        }
        
    except Exception as e:
        logger.error(f"Erro ao gerar handoff: {e}")
        return None
```

### Exemplo de Mensagem de Handoff

```
✅ Perfeito! Vamos confirmar seu pré-agendamento:

📋 RESUMO:
👤 Paciente: João Silva
👨‍⚕️ Médico: Dr. Gustavo
📅 Data: 15/10/2024
🕐 Horário: 14:30

🔄 Para CONFIRMAR definitivamente:
👩‍💼 Nossa secretária validará a disponibilidade e confirmará seu agendamento.

📞 Clique no link abaixo para falar diretamente com nossa equipe:
https://wa.me/5573988221003?text=Ol%C3%A1%2C%20gostaria%20de%20confirmar%20meu%20pr%C3%A9-agendamento%3A%0A%0A%F0%9F%91%A4%20Paciente%3A%20Jo%C3%A3o%20Silva%0A%F0%9F%91%A8%E2%80%8D%E2%9A%95%EF%B8%8F%20M%C3%A9dico%3A%20Dr.%20Gustavo%0A%F0%9F%93%85%20Data%3A%2015%2F10%2F2024%0A%F0%9F%95%90%20Hor%C3%A1rio%3A%2014%3A30
```

---

## Extração de Entidades

### Análise Inteligente com Gemini

**Arquivo:** `api_gateway/services/gemini_chatbot_service.py` (linhas 165-198)

```python
def _analyze_message_with_gemini(self, message: str, session: Dict, 
                               conversation_history: List, clinic_data: Dict) -> Dict[str, Any]:
    """
    Analisa mensagem usando Gemini para identificar intenção e estado da conversa
    """
    # Construir prompt de análise
    analysis_prompt = self._build_analysis_prompt(
        message, session, conversation_history, clinic_data
    )
    
    # Gerar análise com Gemini
    response = self.model.generate_content(
        analysis_prompt,
        generation_config={
            "temperature": 0.1,  # Baixa temperatura para análise determinística
            "top_p": 0.8,
            "top_k": 20,
            "max_output_tokens": 300
        }
    )
    
    # Extrair análise da resposta
    analysis_result = self._extract_analysis_from_response(response.text)
    
    return analysis_result
```

### Exemplo de Análise JSON

```json
{
  "intent": "agendar_consulta",
  "next_state": "choosing_schedule",
  "entities": {
    "nome_paciente": "João Silva",
    "medico": "Dr. Gustavo",
    "data": "15/10/2024",
    "horario": "14:30"
  },
  "confidence": 0.95,
  "reasoning": "Paciente quer agendar consulta com Dr. Gustavo para 15/10 às 14:30"
}
```

### Fallback com Regex

**Arquivo:** `api_gateway/services/gemini_chatbot_service.py` (linhas 1018-1091)

```python
def _extract_entities_with_regex(self, message: str) -> Dict[str, str]:
    """
    Extrai entidades usando regex como fallback quando o Gemini falha
    """
    import re
    entities = {}
    
    # Extrair nome do paciente
    name_patterns = [
        r'meu\s+nome\s+é\s+([A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+)*)',
        r'sou\s+([A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+)*)',
        # ... mais padrões
    ]
    
    # Extrair médico
    doctor_patterns = [
        r'dr\.?\s+([A-Za-zÀ-ÿ]+)',
        r'dra\.?\s+([A-Za-zÀ-ÿ]+)',
        # ... mais padrões
    ]
    
    # Extrair data
    date_patterns = [
        r'(\d{1,2})/(\d{1,2})/(\d{2,4})',
        r'(segunda|terça|quarta|quinta|sexta)',
        # ... mais padrões
    ]
    
    # Extrair horário
    time_patterns = [
        r'(\d{1,2}):(\d{2})',
        r'(\d{1,2})h(\d{2})?',
        # ... mais padrões
    ]
    
    return entities
```

---

## Fluxo de Mensagens Completo

### Exemplo Real de Conversa

```
┌─────────────────────────────────────────────────────────────┐
│ CONVERSA DE PRÉ-AGENDAMENTO                                  │
└─────────────────────────────────────────────────────────────┘

👤 PACIENTE: Olá, bom dia!

🤖 BOT: Olá! Bom dia! 😊 Sou o assistente virtual da Clínica PneumoSono.
        Como posso ajudá-lo hoje?
        
        [Estado: idle → collecting_patient_info]

─────────────────────────────────────────────────────────────

👤 PACIENTE: Quero agendar uma consulta

🤖 BOT: Ótimo! Para iniciar o agendamento, preciso de algumas informações.
        Primeiro, qual é o seu nome completo?
        
        [Estado: collecting_patient_info]

─────────────────────────────────────────────────────────────

👤 PACIENTE: Meu nome é João Silva

🤖 BOT: Confirma que seu nome é João Silva?
        
        [Estado: confirming_name]
        [Entidades: nome_paciente="João Silva" (pendente)]

─────────────────────────────────────────────────────────────

👤 PACIENTE: Sim

🤖 BOT: Perfeito, João Silva! 👏
        Com qual médico você gostaria de agendar?
        
        Nossos médicos:
        👨‍⚕️ Dr. Gustavo - Medicina do Sono, Pneumologia
        👨‍⚕️ Dr. Gleyton Porto - Endocrinologia
        
        [Estado: selecting_doctor]
        [Sessão: patient_name="João Silva", name_confirmed=True]

─────────────────────────────────────────────────────────────

👤 PACIENTE: Dr. Gustavo

🤖 BOT: Excelente escolha! 👨‍⚕️
        
        Dr. Gustavo
        🩺 Medicina do Sono, Pneumologia
        💰 Consulta particular: R$ 150,00
        
        📅 Horários disponíveis:
        
        Segunda-feira (14/10/2024):
        ✅ 08:00, 09:00, 10:00, 14:00, 15:00, 16:00
        
        Quarta-feira (16/10/2024):
        ✅ 08:00, 09:00, 14:00, 15:00
        
        Qual data seria melhor para você?
        
        [Estado: choosing_schedule]
        [Sessão: selected_doctor="Dr. Gustavo"]

─────────────────────────────────────────────────────────────

👤 PACIENTE: Segunda às 14h

🤖 BOT: ✅ Perfeito! Vamos confirmar seu pré-agendamento:
        
        📋 RESUMO:
        👤 Paciente: João Silva
        👨‍⚕️ Médico: Dr. Gustavo
        📅 Data: 14/10/2024
        🕐 Horário: 14:00
        
        🔄 Para CONFIRMAR definitivamente:
        👩‍💼 Nossa secretária validará a disponibilidade e confirmará.
        
        📞 Clique no link para falar com nossa equipe:
        https://wa.me/5573988221003?text=...
        
        [Estado: confirming]
        [Sessão: preferred_date="14/10/2024", preferred_time="14:00"]
        [HANDOFF GERADO ✅]

```

---

## Tratamento de Erros

### 1. **Informações Faltantes**

```python
# Se o paciente pular etapas:
👤 PACIENTE: Quero agendar para segunda-feira

# O sistema detecta que falta o médico:
🤖 BOT: Para agendar, preciso saber com qual médico você deseja consultar.
        
        Nossos médicos disponíveis são:
        • Dr. Gustavo - Medicina do Sono, Pneumologia
        • Dr. Gleyton Porto - Endocrinologia
        
        Com qual deles você gostaria de agendar?
```

### 2. **Médico Não Encontrado**

```python
# Se o paciente mencionar médico inexistente:
👤 PACIENTE: Quero agendar com Dr. Paulo

🤖 BOT: ❌ Não encontrei o médico "Dr. Paulo".
        
        Nossos médicos disponíveis são:
        • Dr. Gustavo (Medicina do Sono, Pneumologia)
        • Dr. Gleyton Porto (Endocrinologia)
        
        Para qual médico gostaria de consultar os horários?
```

### 3. **Horário Indisponível**

```python
# Se horário não estiver disponível:
🤖 BOT: ❌ Não há horários disponíveis para a data solicitada.
        
        📅 Mas temos horários disponíveis em outros dias:
        
        Segunda-feira (14/10/2024): 08:00, 09:00, 14:00, 15:00
        Quarta-feira (16/10/2024): 08:00, 09:00
        
        Qual desses horários seria melhor para você?
```

---

## Persistência de Dados

### Sincronização Cache + Banco

```python
# gemini_chatbot_service.py (linhas 929-973)

┌────────────────┐
│     CACHE      │ ◄─── Acesso rápido (sessão em memória)
└───────┬────────┘
        │
        │ Sincronização
        ▼
┌────────────────┐
│  BANCO DADOS   │ ◄─── Persistência (sessão no PostgreSQL/SQLite)
└────────────────┘

# A cada atualização de sessão:
1. Atualiza cache (rápido)
2. Sincroniza com banco (persistente)
3. Log de sucesso
```

### Exemplo de Log

```
✅ Nome atualizado: João Silva
✅ Médico atualizado: Dr. Gustavo
✅ Data atualizada (normalizada): 2024-10-14
✅ Horário atualizado: 14:00
📋 Status das informações: {'nome': True, 'medico': True, 'data': True, 'horario': True}
📋 Sessão atualizada - Estado: confirming, Nome: João Silva, Médico: Dr. Gustavo
💾 Sessão sincronizada com banco - ID: 42, Nome: João Silva, Data: 2024-10-14
```

---

## Métricas e Monitoramento

### Logs de Acompanhamento

```python
# Logs durante o fluxo:

🔍 Entidades extraídas: {'nome_paciente': 'João Silva', 'medico': 'Dr. Gustavo'}
✅ Nome atualizado: João Silva
✅ Médico atualizado: Dr. Gustavo
📋 Status das informações: {'nome': True, 'medico': True, 'data': False, 'horario': False}
🤖 [AGENDAR_CONSULTA] 0.95 - Perfeito, João Silva! Com qual médico você gostaria...
💾 Mensagem do usuário salva no banco com ID: 123
💾 Resposta do bot salva no banco com ID: 124
📊 TOKENS - ANÁLISE: Input=1,245, Output=156, Total=1,401
```

---

## Conclusão

### ✅ Módulo Orquestrador Implementado

**SIM**, o módulo orquestrador completo está implementado no projeto:

> **"Este módulo será responsável por orquestrar todo o fluxo de agendamento, desde a solicitação inicial até a confirmação do usuário."**

### 📊 Implementações Completas

| Funcionalidade | Status | Arquivo Principal |
|----------------|--------|-------------------|
| **Orquestração Completa** | ✅ | `gemini_chatbot_service.py` |
| **Solicitação Inicial** | ✅ | `process_message()` |
| **Coleta de Nome** | ✅ | `conversation_service.py` |
| **Seleção de Médico** | ✅ | `smart_scheduling_service.py` |
| **Consulta de Horários** | ✅ | `google_calendar_service.py` |
| **Escolha de Data/Hora** | ✅ | Estados progressivos |
| **Validação Completa** | ✅ | `_validate_appointment_info()` |
| **Confirmação Final** | ✅ | `_handle_appointment_confirmation()` |
| **Handoff para Secretária** | ✅ | `handoff_service.py` |
| **Persistência** | ✅ | Cache + Banco de Dados |
| **Monitoramento** | ✅ | Logs detalhados |

### 🎯 Fluxo Completo

```
Solicitação → Coleta de Nome → Confirmação → Seleção de Médico →
Consulta de Horários → Escolha de Data/Hora → Validação →
Confirmação → Handoff → Secretária Confirma
```

### 🚀 Diferenciais

1. **Inteligência Artificial** - Gemini analisa intenções e extrai entidades
2. **Estados Progressivos** - Máquina de estados bem definida
3. **Validações Robustas** - Verifica informações antes de gerar handoff
4. **Fallbacks** - Regex como backup quando Gemini falha
5. **Integração Google Calendar** - Horários reais e disponibilidade
6. **Handoff Inteligente** - Link formatado para WhatsApp da secretária
7. **Persistência Dual** - Cache (rápido) + Banco (persistente)
8. **Monitoramento Completo** - Logs detalhados de todo o fluxo

---

**Última Atualização:** Outubro 2024  
**Versão:** 1.0  
**Autor:** Sistema de Documentação Automatizada

