# 💻 Implementação Técnica do Agent Router

## 📑 Índice

1. [Arquitetura de Código](#arquitetura-de-código)
2. [Classe GeminiChatbotService](#classe-geminichatbotservice)
3. [Fluxo de Processamento Detalhado](#fluxo-de-processamento-detalhado)
4. [Implementação das Decisões de Roteamento](#implementação-das-decisões-de-roteamento)
5. [Integração com Serviços](#integração-com-serviços)
6. [Configurações e Parâmetros](#configurações-e-parâmetros)
7. [Testes e Validação](#testes-e-validação)
8. [Boas Práticas](#boas-práticas)

---

## 🏗️ Arquitetura de Código

### Estrutura de Diretórios

```
api_gateway/
└── services/
    ├── gemini/                          # Módulos do Gemini
    │   ├── __init__.py                  # Exports dos módulos
    │   ├── core_service.py              # ⭐ AGENT ROUTER (Principal)
    │   ├── intent_detector.py           # Detecção de intenções
    │   ├── entity_extractor.py          # Extração de entidades
    │   ├── response_generator.py        # Geração de respostas
    │   └── session_manager.py           # Gerenciamento de sessões
    │
    ├── conversation_service.py          # Serviço de conversas
    ├── whatsapp_service.py              # Integração WhatsApp
    ├── rag_service.py                   # Base de conhecimento
    ├── smart_scheduling_service.py      # Agendamento inteligente
    ├── google_calendar_service.py       # Integração Google Calendar
    ├── handoff_service.py               # Transferência para secretaria
    └── token_monitor.py                 # Monitoramento de tokens
```

### Diagrama de Dependências

```
┌─────────────────────────────────────────────────────────────┐
│                   GeminiChatbotService                      │
│                    (Agent Router)                           │
└──────┬──────────────────┬──────────────────┬───────────────┘
       │                  │                  │
       │ usa              │ usa              │ usa
       │                  │                  │
┌──────▼──────┐    ┌──────▼──────┐   ┌──────▼──────┐
│   Intent    │    │   Entity    │   │  Response   │
│  Detector   │    │  Extractor  │   │  Generator  │
└─────────────┘    └─────────────┘   └─────────────┘
       │                  │                  │
       │ usa              │ usa              │ usa
       │                  │                  │
┌──────▼──────────────────▼──────────────────▼───────────┐
│              Serviços Especializados                    │
│  • RAGService                                           │
│  • SmartSchedulingService                               │
│  • HandoffService                                       │
│  • ConversationService                                  │
│  • GoogleCalendarService                                │
└─────────────────────────────────────────────────────────┘
```

---

## 🎯 Classe GeminiChatbotService

### Estrutura Completa

```python
# api_gateway/services/gemini/core_service.py

class GeminiChatbotService:
    """
    Agent Router Principal - Orquestrador de todo o sistema
    
    Responsável por:
    1. Receber mensagens do usuário
    2. Coordenar análise de intenção
    3. Decidir roteamento para serviços
    4. Gerar respostas contextualizadas
    5. Persistir estado da conversa
    """
    
    def __init__(self):
        """Inicializa todos os módulos especializados"""
        self.api_key = settings.GEMINI_API_KEY
        self.enabled = settings.GEMINI_ENABLED
        
        # Módulos principais do Gemini
        self.intent_detector = IntentDetector()
        self.entity_extractor = EntityExtractor()
        self.response_generator = ResponseGenerator()
        self.session_manager = SessionManager()
        
        # Serviços externos
        self.rag_service = RAGService()
    
    def process_message(self, phone_number: str, message: str) -> Dict[str, Any]:
        """
        ⭐ MÉTODO PRINCIPAL - NÚCLEO DO AGENT ROUTER
        
        Este método implementa toda a lógica de roteamento:
        1. Análise de intenção
        2. Extração de entidades
        3. Decisão de roteamento
        4. Execução do serviço adequado
        5. Geração de resposta
        6. Persistência de estado
        """
        pass  # Implementação detalhada abaixo
```

### Método process_message (Coração do Router)

```python
def process_message(self, phone_number: str, message: str) -> Dict[str, Any]:
    """
    Método principal do Agent Router
    """
    try:
        # ═══════════════════════════════════════════════════════
        # ETAPA 1: PREPARAÇÃO E CONTEXTO
        # ═══════════════════════════════════════════════════════
        
        # 1.1. Obter ou criar sessão do usuário
        session = self.session_manager.get_or_create_session(phone_number)
        logger.info(f"📱 Processando: {phone_number}")
        logger.info(f"📊 Estado atual: {session.get('current_state')}")
        
        # 1.2. Verificar sistema de pausa/retomada
        if conversation_service.has_paused_appointment(phone_number):
            # Usuário pausou para tirar dúvida
            if any(kw in message.lower() for kw in ['continuar', 'retomar', 'voltar']):
                conversation_service.resume_appointment(phone_number)
                return {'response': '✅ Vamos continuar com seu agendamento!'}
        
        # 1.3. Obter contexto histórico
        conversation_history = self.session_manager.get_conversation_history(phone_number)
        clinic_data = self._get_clinic_data_optimized()
        
        # ═══════════════════════════════════════════════════════
        # ETAPA 2: ANÁLISE DA MENSAGEM
        # ═══════════════════════════════════════════════════════
        
        # 2.1. Detectar intenção com Gemini AI
        intent_result = self.intent_detector.analyze_message(
            message, session, conversation_history, clinic_data
        )
        logger.info(f"🔍 Intent: {intent_result['intent']}")
        logger.info(f"📊 Confiança: {intent_result['confidence']}")
        
        # 2.2. Extrair entidades da mensagem
        entities_result = self.entity_extractor.extract_entities(
            message, session, conversation_history, clinic_data
        )
        logger.info(f"📦 Entidades: {entities_result}")
        
        # 2.3. Combinar resultados da análise
        analysis_result = {
            'intent': intent_result['intent'],
            'next_state': intent_result['next_state'],
            'confidence': intent_result['confidence'],
            'entities': entities_result,
            'reasoning': intent_result.get('reasoning', ''),
            'raw_message': message
        }

        # 2.4. Fluxo dedicado para confirmação precoce do nome
        manual_name_response = self._handle_patient_name_flow(
            phone_number=phone_number,
            session=session,
            message=message,
            analysis_result=analysis_result
        )
        if manual_name_response:
            response_result = manual_name_response
            self.session_manager.update_session(
                phone_number, session, analysis_result, response_result
            )
            self.session_manager.save_messages(
                phone_number, message, response_result['response'], analysis_result
            )
            return response_result

        # ═══════════════════════════════════════════════════════
        # ETAPA 3: DECISÃO DE ROTEAMENTO
        # ═══════════════════════════════════════════════════════
        
        # 3.1. Detectar se usuário quer tirar dúvidas durante agendamento
        if analysis_result['intent'] in ['buscar_info', 'duvida']:
            if session['current_state'] not in ['idle', 'answering_questions']:
                # Pausar agendamento para responder dúvida
                conversation_service.pause_for_question(phone_number)
        
        # 3.2. Roteamento para agendar_consulta
        if analysis_result['intent'] == 'agendar_consulta':
            # Verificar disponibilidade real no Google Calendar
            scheduling_analysis = self._handle_scheduling_request(
                message, session, analysis_result
            )
            if scheduling_analysis.get('has_availability_info'):
                analysis_result['scheduling_info'] = scheduling_analysis
        
        # 3.3. Roteamento para confirmar_agendamento
        response_result = {}
        if analysis_result['intent'] == 'confirmar_agendamento':
            missing_info_result = conversation_service.get_missing_appointment_info(
                phone_number
            )
            
            if missing_info_result['is_complete']:
                # Todas informações coletadas - gerar handoff
                if session.get('current_state') != 'confirming':
                    handoff_result = self._handle_appointment_confirmation(
                        phone_number, session, analysis_result
                    )
                    if handoff_result:
                        response_result['response'] = handoff_result['message']
                        response_result['handoff_link'] = handoff_result['handoff_link']
                        session['current_state'] = 'confirming'
                        analysis_result['next_state'] = 'confirming'
            else:
                # Informações faltando - continuar coletando
                logger.info(f"🔄 Faltam: {missing_info_result['missing_info']}")
                analysis_result['intent'] = 'agendar_consulta'
                analysis_result['missing_info'] = missing_info_result['missing_info']
        
        # ═══════════════════════════════════════════════════════
        # ETAPA 4: GERAÇÃO DE RESPOSTA
        # ═══════════════════════════════════════════════════════
        
        if not response_result.get('response'):
            response_result = self.response_generator.generate_response(
                message, analysis_result, session, conversation_history, clinic_data
            )
        
        # ═══════════════════════════════════════════════════════
        # ETAPA 5: PERSISTÊNCIA
        # ═══════════════════════════════════════════════════════
        
        # 5.1. Atualizar sessão no banco de dados
        self.session_manager.update_session(
            phone_number, session, analysis_result, response_result
        )
        
        # 5.2. Salvar mensagens no histórico
        self.session_manager.save_messages(
            phone_number, message, response_result['response'], analysis_result
        )
        
        logger.info(f"✅ Resposta gerada com sucesso")
        
        return response_result
        
    except Exception as e:
        logger.error(f"❌ Erro ao processar mensagem: {e}")
        return self._get_fallback_response(message)
```

Após combinar os resultados, o router executa um **fluxo especializado de confirmação do nome**:

- Chama `_handle_patient_name_flow(...)`, responsável por interpretar respostas como "me chamo Gabriela" ou confirmações curtas ("sim", "isso") quando já existe um `pending_name`.
- O nome é extraído diretamente pelo `EntityExtractor` (que usa Gemini AI) e armazenado em `pending_name` na sessão.
- O fluxo utiliza o `ConversationService.confirm_patient_name()` apenas para confirmar ou rejeitar o nome pendente, armazenando os campos `pending_name`, `patient_name` e `name_confirmed` na sessão e no banco.
- Caso a confirmação seja concluída, o método retorna imediatamente uma resposta amigável e atualiza o estado para a próxima informação necessária (especialidade, médico, data ou horário). Assim, o LLM não segue adiante até que o nome esteja oficialmente confirmado.

Somente quando o fluxo de nome não retorna uma resposta (ou seja, já temos um nome confirmado) o processamento continua para as etapas seguintes de roteamento.

---

## 🔄 Fluxo de Processamento Detalhado

### Diagrama de Fluxo de Código

```
┌─────────────────────────────────────────────────────────────────┐
│              GeminiChatbotService.process_message()             │
└─────────────────────────────────────────────────────────────────┘
                             │
                             │
    ┌────────────────────────▼────────────────────────┐
    │  ETAPA 1: PREPARAÇÃO                            │
    │  ─────────────────────                          │
    │  • SessionManager.get_or_create_session()       │
    │  • Verificar sistema pausa/retomada             │
    │  • Obter histórico e dados da clínica           │
    └────────────────────────┬────────────────────────┘
                             │
    ┌────────────────────────▼────────────────────────┐
    │  ETAPA 2: ANÁLISE                               │
    │  ────────────────                               │
    │  • IntentDetector.analyze_message()             │
    │      └─> Gemini AI analisa intenção             │
    │  • EntityExtractor.extract_entities()           │
    │      └─> Gemini AI extrai entidades             │
    │  • Combinar resultados                          │
    └────────────────────────┬────────────────────────┘
                             │
    ┌────────────────────────▼────────────────────────┐
    │  ETAPA 3: DECISÃO DE ROTEAMENTO                 │
    │  ──────────────────────────────                 │
    │                                                 │
    │  IF intent == 'buscar_info':                    │
    │      └─> Verificar se está em meio a agend.    │
    │          └─> SIM: pause_for_question()         │
    │      └─> RAGService.buscar_informacao()        │
    │                                                 │
    │  IF intent == 'agendar_consulta':               │
    │      └─> SmartSchedulingService                │
    │          └─> GoogleCalendarService              │
    │                                                 │
    │  IF intent == 'confirmar_agendamento':          │
    │      └─> Verificar informações completas       │
    │          └─> SIM: HandoffService               │
    │          └─> NÃO: Solicitar faltantes          │
    └────────────────────────┬────────────────────────┘
                             │
    ┌────────────────────────▼────────────────────────┐
    │  ETAPA 4: GERAÇÃO DE RESPOSTA                   │
    │  ────────────────────────────                   │
    │  • ResponseGenerator.generate_response()        │
    │      └─> Monta prompt contextualizado           │
    │      └─> Gemini AI gera resposta natural       │
    │      └─> Aplica modo econômico se necessário   │
    └────────────────────────┬────────────────────────┘
                             │
    ┌────────────────────────▼────────────────────────┐
    │  ETAPA 5: PERSISTÊNCIA                          │
    │  ─────────────────────                          │
    │  • SessionManager.update_session()              │
    │      └─> Atualiza estado no banco               │
    │      └─> Sincroniza cache                       │
    │  • SessionManager.save_messages()               │
    │      └─> Salva histórico de mensagens           │
    └────────────────────────┬────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │  RETURN RESULT  │
                    └─────────────────┘
```

---

## 🎯 Implementação das Decisões de Roteamento

### Switch de Intenções (Código Real)

```python
def _route_by_intent(self, analysis_result: Dict, session: Dict) -> str:
    """
    Determina qual serviço chamar baseado na intenção
    
    Este é o "switch statement" do Agent Router
    """
    intent = analysis_result['intent']
    
    # ═══════════════════════════════════════════════════════
    # ROTA 1: BUSCAR INFORMAÇÃO
    # ═══════════════════════════════════════════════════════
    if intent == 'buscar_info':
        # Verificar se está em meio a um agendamento
        if session['current_state'] not in ['idle', 'answering_questions']:
            # PAUSAR agendamento para responder dúvida
            conversation_service.pause_for_question(session['phone_number'])
        
        # Rotear para RAGService (base de conhecimento)
        return 'rag_service'
    
    # ═══════════════════════════════════════════════════════
    # ROTA 2: AGENDAR CONSULTA
    # ═══════════════════════════════════════════════════════
    elif intent == 'agendar_consulta':
        # Rotear para SmartSchedulingService
        # Este serviço consultará o Google Calendar
        return 'smart_scheduling_service'
    
    # ═══════════════════════════════════════════════════════
    # ROTA 3: CONFIRMAR AGENDAMENTO
    # ═══════════════════════════════════════════════════════
    elif intent == 'confirmar_agendamento':
        # Verificar se todas as informações foram coletadas
        missing_info = conversation_service.get_missing_appointment_info(
            session['phone_number']
        )
        
        if missing_info['is_complete']:
            # Rotear para HandoffService (gerar link para secretaria)
            return 'handoff_service'
        else:
            # Faltam informações - continuar coletando
            return 'continue_collecting'
    
    # ═══════════════════════════════════════════════════════
    # ROTA 4: SAUDAÇÃO
    # ═══════════════════════════════════════════════════════
    elif intent == 'saudacao':
        # Apenas gerar resposta amigável
        return 'response_generator'
    
    # ═══════════════════════════════════════════════════════
    # ROTA 5: DÚVIDA
    # ═══════════════════════════════════════════════════════
    elif intent == 'duvida':
        # Esclarecer dúvida e manter estado atual
        return 'response_generator'
    
    # ═══════════════════════════════════════════════════════
    # ROTA 6: DESPEDIDA
    # ═══════════════════════════════════════════════════════
    elif intent == 'despedida':
        # Mensagem de encerramento
        return 'response_generator'
    
    # ═══════════════════════════════════════════════════════
    # ROTA PADRÃO (fallback)
    # ═══════════════════════════════════════════════════════
    else:
        logger.warning(f"⚠️ Intent desconhecido: {intent}")
        return 'response_generator'
```

### Implementação dos Handlers (Manipuladores de Rota)

#### Handler para Agendamento

```python
def _handle_scheduling_request(
    self, 
    message: str, 
    session: Dict, 
    analysis_result: Dict
) -> Dict:
    """
    Handler para intent: 'agendar_consulta'
    
    Responsável por:
    1. Analisar solicitação de agendamento
    2. Consultar Google Calendar
    3. Retornar disponibilidade
    """
    try:
        logger.info("🗓️ Processando solicitação de agendamento")
        
        # 1. Usar SmartSchedulingService para analisar
        scheduling_analysis = smart_scheduling_service.analyze_scheduling_request(
            message, session
        )
        
        logger.info(f"📊 Tipo: {scheduling_analysis.get('response_type')}")
        
        # 2. Se temos informações suficientes, consultar disponibilidade
        if scheduling_analysis.get('response_type') == 'availability_info':
            doctor_info = scheduling_analysis.get('doctor_info')
            
            if doctor_info and doctor_info.get('nome'):
                doctor_name = doctor_info['nome']
                logger.info(f"👨‍⚕️ Consultando: {doctor_name}")
                
                # 3. Consultar horários no Google Calendar
                availability = smart_scheduling_service.get_doctor_availability(
                    doctor_name=doctor_name,
                    days_ahead=7  # Próximos 7 dias
                )
                
                if availability.get('has_availability'):
                    scheduling_analysis['calendar_availability'] = availability
                    scheduling_analysis['has_availability_info'] = True
                    logger.info(f"✅ {availability['available_slots']} horários disponíveis")
                else:
                    logger.warning(f"⚠️ Nenhum horário disponível para {doctor_name}")
                    scheduling_analysis['has_availability_info'] = False
        
        return scheduling_analysis
        
    except Exception as e:
        logger.error(f"❌ Erro ao processar agendamento: {e}")
        return {
            'response_type': 'error',
            'message': 'Desculpe, erro ao consultar disponibilidade.',
            'has_availability_info': False
        }
```

#### Handler para Confirmação Antecipada do Nome

```python
def _handle_patient_name_flow(
    self,
    phone_number: str,
    session: Dict,
    message: str,
    analysis_result: Dict
) -> Optional[Dict[str, Any]]:
    """Gerencia a extração e confirmação do nome antes de seguir o fluxo."""
```

**Responsabilidades principais:**

- Detectar quando ainda não temos `patient_name` confirmado ou quando um `pending_name` precisa ser validado.
- Usar o nome já extraído pelo `EntityExtractor` (que utiliza Gemini AI) ao invés de processar novamente.
- Se há `pending_name`, chamar `ConversationService.confirm_patient_name()` para confirmar ou rejeitar o nome.
- Persistir `pending_name`, `patient_name` e `name_confirmed` na sessão e no banco (via `SessionManager`).
- Construir respostas manuais ("Confirma se seu nome completo é…") sem chamar o LLM novamente, garantindo baixo consumo de tokens.
- Após a confirmação, direcionar imediatamente para a próxima informação necessária (especialidade, médico, data ou horário), consultando `get_missing_appointment_info()` para definir o follow-up.

**Fluxo de processamento:**

1. Se há `pending_name`: chama `confirm_patient_name()` para validar confirmação/rejeição do usuário.
2. Se não há nome confirmado: usa o nome extraído pelo `EntityExtractor` (já presente em `analysis_result['entities']['nome_paciente']`), salva em `pending_name` e solicita confirmação.
3. Se o `EntityExtractor` não extraiu nome: solicita novamente ao usuário.

> Esse handler é chamado antes das decisões de roteamento. Se ele devolver uma resposta, o método `process_message()` encerra ali mesmo, evitando que o Gemini formule prompts complexos enquanto o nome não estiver validado.

#### Handler para Confirmação

```python
def _handle_appointment_confirmation(
    self, 
    phone_number: str, 
    session: Dict, 
    analysis_result: Dict
) -> Dict:
    """
    Handler para intent: 'confirmar_agendamento'
    
    Responsável por:
    1. Coletar informações do agendamento
    2. Gerar link de handoff
    3. Criar mensagem de confirmação
    """
    try:
        # 1. Coletar informações da sessão
        patient_name = session.get('patient_name', 'Paciente')
        doctor = session.get('selected_doctor', 'Médico a definir')
        specialty = session.get('selected_specialty', 'Especialidade a definir')
        date = session.get('preferred_date', 'Data a definir')
        time = session.get('preferred_time', 'Horário a definir')
        
        # 2. Gerar link de handoff para secretaria
        handoff_link = handoff_service.generate_appointment_handoff_link(
            patient_name=patient_name,
            doctor_name=doctor,
            specialty=specialty,
            date=date,
            time=time
        )
        
        # 3. Criar mensagem de confirmação
        confirmation_message = handoff_service.create_confirmation_message(
            doctor_name=doctor,
            specialty=specialty,
            date=date,
            time=time,
            patient_info={'patient_name': patient_name}
        )
        
        # 4. Combinar mensagem + link
        full_message = f"{confirmation_message}\n{handoff_link}"
        
        logger.info(f"✅ Handoff gerado para {phone_number}")
        logger.info(f"🔗 Link: {handoff_link}")
        
        return {
            'message': full_message,
            'handoff_link': handoff_link
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao processar confirmação: {e}")
        return None
```

---

## 🔗 Integração com Serviços

### Como o Router Interage com os Serviços

```python
class GeminiChatbotService:
    """Agent Router com todas as dependências"""
    
    def __init__(self):
        # ═══════════════════════════════════════════════════════
        # MÓDULOS PRINCIPAIS (fazem parte do Router)
        # ═══════════════════════════════════════════════════════
        self.intent_detector = IntentDetector()
        self.entity_extractor = EntityExtractor()
        self.response_generator = ResponseGenerator()
        self.session_manager = SessionManager()
        
        # ═══════════════════════════════════════════════════════
        # SERVIÇOS EXTERNOS (chamados pelo Router)
        # ═══════════════════════════════════════════════════════
        self.rag_service = RAGService()
        # smart_scheduling_service é importado como singleton
        # handoff_service é importado como singleton
        # conversation_service é importado como singleton
```

### Padrão de Chamada de Serviços

```python
# ═══════════════════════════════════════════════════════
# PADRÃO 1: Serviços como Singletons (mais comum)
# ═══════════════════════════════════════════════════════

from ..smart_scheduling_service import smart_scheduling_service
from ..handoff_service import handoff_service
from ..conversation_service import conversation_service

# Uso direto
result = smart_scheduling_service.analyze_scheduling_request(...)
link = handoff_service.generate_appointment_handoff_link(...)
info = conversation_service.get_missing_appointment_info(...)


# ═══════════════════════════════════════════════════════
# PADRÃO 2: Serviços Instanciados (RAGService)
# ═══════════════════════════════════════════════════════

self.rag_service = RAGService()

# Uso via self
medicos = self.rag_service.get_medicos()
especialidades = self.rag_service.get_especialidades()
```

---

## ⚙️ Configurações e Parâmetros

### Variáveis de Ambiente

```python
# core/settings.py

# ═══════════════════════════════════════════════════════
# CONFIGURAÇÕES DO GEMINI AI (Agent Router)
# ═══════════════════════════════════════════════════════

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')
GEMINI_ENABLED = os.getenv('GEMINI_ENABLED', 'true').lower() == 'true'

# ═══════════════════════════════════════════════════════
# PARÂMETROS DE GERAÇÃO (usados no Router)
# ═══════════════════════════════════════════════════════

# IntentDetector parameters
INTENT_TEMPERATURE = 0.7  # Mais determinístico
INTENT_TOP_P = 0.8
INTENT_TOP_K = 20
INTENT_MAX_TOKENS = 300

# ResponseGenerator parameters
RESPONSE_TEMPERATURE = 0.9  # Mais criativo
RESPONSE_TOP_P = 0.95
RESPONSE_TOP_K = 40
RESPONSE_MAX_TOKENS = 800

# ═══════════════════════════════════════════════════════
# CONFIGURAÇÕES DE CACHE E PERFORMANCE
# ═══════════════════════════════════════════════════════

# Nota: O sistema Django usa cache padrão para sessões e dados
# Não há configurações específicas de timeout de cache definidas no settings.py
# O cache é gerenciado automaticamente pelo Django Cache Framework

# ═══════════════════════════════════════════════════════
# LIMITES E QUOTAS (Token Monitor)
# ═══════════════════════════════════════════════════════

# Configurações do TokenMonitor para controle de custos da API Gemini
DAILY_TOKEN_LIMIT = 150000  # Limite diário de tokens
ECONOMY_MODE_THRESHOLD = 0.8  # Ativa modo econômico aos 80% do limite
```

### Arquivo .env

```bash
# .env

# Gemini AI (obrigatório)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash-lite
GEMINI_ENABLED=true

# WhatsApp Business API (obrigatório)
WHATSAPP_API_URL=https://graph.facebook.com/v17.0
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_TOKEN=your_whatsapp_token
WHATSAPP_VERIFY_TOKEN=your_verify_token

# Google Calendar API (obrigatório para agendamento)
GOOGLE_CALENDAR_ID=your_calendar_id@group.calendar.google.com
GOOGLE_SERVICE_ACCOUNT_FILE=path/to/credentials.json
```

---

## 🧪 Testes e Validação

### Endpoints de Teste

O projeto possui endpoints para testar cada parte do Agent Router:

```python
# api_gateway/urls.py

urlpatterns = [
    # ════════════════════════════════════════════════════════
    # TESTE COMPLETO DO AGENT ROUTER
    # ════════════════════════════════════════════════════════
    path('test/chatbot/', views.test_chatbot_service, name='test_chatbot'),
    # POST: {"phone_number": "+5511999999999", "message": "Olá"}
    
    # ════════════════════════════════════════════════════════
    # TESTE DE COMPONENTES INDIVIDUAIS
    # ════════════════════════════════════════════════════════
    
    # IntentDetector
    path('test/intent-analysis/', views.test_intent_analysis),
    # POST: {"message": "Quero agendar consulta", "phone_number": "+5511999999999"}
    
    # EntityExtractor
    path('test/entity-extraction/', views.test_entity_extraction),
    # POST: {"message": "Meu nome é João", "phone_number": "+5511999999999"}
    
    # HandoffService
    path('test/handoff/', views.test_handoff_generation),
    # POST: dados de agendamento simulados
    
    # ════════════════════════════════════════════════════════
    # MONITORAMENTO
    # ════════════════════════════════════════════════════════
    path('monitor/tokens/', views.token_usage_stats),
    # GET: Estatísticas de uso de tokens
]
```

### Exemplos de Teste com cURL

```bash
# ═══════════════════════════════════════════════════════
# TESTE 1: Fluxo Completo (Agent Router)
# ═══════════════════════════════════════════════════════
curl -X POST http://localhost:8000/api/test/chatbot/ \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+5511999999999",
    "message": "Olá, quero agendar uma consulta"
  }'

# Resposta esperada:
# {
#   "response": "Olá! Para começar, qual é o seu nome completo?",
#   "intent": "agendar_consulta",
#   "confidence": 0.95,
#   "next_state": "collecting_patient_info"
# }


# ═══════════════════════════════════════════════════════
# TESTE 2: Apenas Detecção de Intenção
# ═══════════════════════════════════════════════════════
curl -X POST http://localhost:8000/api/test/intent-analysis/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Quais médicos cardiologistas vocês têm?",
    "phone_number": "+5511999999999"
  }'

# Resposta esperada:
# {
#   "intent": "buscar_info",
#   "next_state": "answering_questions",
#   "confidence": 0.92,
#   "reasoning": "Usuário está buscando informações sobre médicos"
# }


# ═══════════════════════════════════════════════════════
# TESTE 3: Extração de Entidades
# ═══════════════════════════════════════════════════════
curl -X POST http://localhost:8000/api/test/entity-extraction/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Meu nome é João Silva e quero agendar para amanhã às 14h",
    "phone_number": "+5511999999999"
  }'

# Resposta esperada:
# {
#   "patient_name": "João Silva",
#   "preferred_date": "2025-11-11",
#   "preferred_time": "14:00"
# }


# ═══════════════════════════════════════════════════════
# TESTE 4: Monitoramento de Tokens
# ═══════════════════════════════════════════════════════
curl http://localhost:8000/api/monitor/tokens/

# Resposta esperada:
# {
#   "tokens_used_today": 12450,
#   "daily_limit": 150000,
#   "percentage_used": 8.3,
#   "economy_mode_active": false,
#   "estimated_cost": 0.37
# }
```

---

## ✅ Boas Práticas

### 1. Logging Estruturado

```python
import logging

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════
# BOM: Logs informativos e estruturados
# ═══════════════════════════════════════════════════════
logger.info(f"📱 Processando mensagem de {phone_number}: '{message[:50]}...'")
logger.info(f"🔍 Intent detectado: {intent}, Confiança: {confidence}")
logger.info(f"✅ Resposta gerada com sucesso para {phone_number}")

# ═══════════════════════════════════════════════════════
# BOM: Logs de erro com contexto
# ═══════════════════════════════════════════════════════
logger.error(f"❌ Erro ao processar mensagem de {phone_number}: {e}")
logger.warning(f"⚠️ Intent desconhecido: {intent} - usando fallback")
```

### 2. Tratamento de Erros

```python
# ═══════════════════════════════════════════════════════
# BOM: Try-catch específico com fallback
# ═══════════════════════════════════════════════════════
try:
    intent_result = self.intent_detector.analyze_message(...)
except GeminiAPIError as e:
    logger.error(f"Erro na API do Gemini: {e}")
    intent_result = self._get_fallback_analysis(message, session)
except Exception as e:
    logger.error(f"Erro inesperado: {e}")
    return self._get_fallback_response(message)
```

### 3. Validação de Entrada

```python
def process_message(self, phone_number: str, message: str) -> Dict[str, Any]:
    # ═══════════════════════════════════════════════════════
    # BOM: Validar entrada antes de processar
    # ═══════════════════════════════════════════════════════
    if not phone_number or not message:
        raise ValueError("phone_number e message são obrigatórios")
    
    if not phone_number.startswith('+'):
        raise ValueError("phone_number deve estar no formato internacional (+55...)")
    
    if len(message) > 4096:
        raise ValueError("Mensagem muito longa (max: 4096 caracteres)")
```

### 4. Cache Inteligente

```python
# ═══════════════════════════════════════════════════════
# BOM: Usar cache para dados que não mudam frequentemente
# ═══════════════════════════════════════════════════════
def _get_clinic_data_optimized(self) -> Dict:
    """Obtém dados da clínica com cache"""
    try:
        return {
            'clinica_info': self.rag_service.get_clinica_info(),  # Cached 30min
            'medicos': self.rag_service.get_medicos(),  # Cached 30min
            'especialidades': self.rag_service.get_especialidades(),  # Cached 30min
            'convenios': self.rag_service.get_convenios(),  # Cached 30min
        }
    except Exception as e:
        logger.error(f"Erro ao obter dados da clínica: {e}")
        return {}
```

### 5. Monitoramento de Performance

```python
import time

# ═══════════════════════════════════════════════════════
# BOM: Medir tempo de execução de operações críticas
# ═══════════════════════════════════════════════════════
def process_message(self, phone_number: str, message: str) -> Dict[str, Any]:
    start_time = time.time()
    
    try:
        # ... processamento ...
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        logger.info(f"⏱️ Tempo de processamento: {elapsed:.2f}s")
        
        if elapsed > 5.0:
            logger.warning(f"⚠️ Processamento lento: {elapsed:.2f}s")
        
        return response_result
        
    except Exception as e:
        logger.error(f"❌ Erro após {time.time() - start_time:.2f}s: {e}")
        raise
```

---

## 📝 Checklist de Implementação

Se você for criar um novo serviço ou modificar o Agent Router, siga este checklist:

- [ ] Definir nova intenção em `IntentDetector._build_analysis_prompt()`
- [ ] Adicionar caso no switch de roteamento em `GeminiChatbotService.process_message()`
- [ ] Criar handler específico (ex: `_handle_new_feature_request()`)
- [ ] Integrar com serviço externo se necessário
- [ ] Adicionar logs estruturados
- [ ] Implementar tratamento de erros e fallback
- [ ] Criar testes unitários
- [ ] Adicionar endpoint de teste em `urls.py`
- [ ] Documentar no `AGENT_ROUTER_COMPLETO.md`
- [ ] Atualizar diagrama de arquitetura se necessário
- [ ] Testar fluxo completo end-to-end
- [ ] Monitorar uso de tokens após deploy

---

## 🔚 Conclusão

O Agent Router implementado no `GeminiChatbotService` é o **coração do sistema**, responsável por:

✅ Analisar mensagens com IA  
✅ Tomar decisões inteligentes de roteamento  
✅ Coordenar múltiplos serviços especializados  
✅ Garantir robustez com múltiplos fallbacks  
✅ Persistir estado da conversa  
✅ Monitorar performance e custos  

Esta implementação segue os padrões de **Agent Router** descritos na literatura, combinando **roteamento baseado em intenção** com **chamadas de função via LLM**, resultando em um sistema flexível, escalável e manutenível.

---

## 🚀 Trabalhos Futuros e Melhorias

### Estado Atual (TCC)
A implementação atual é **adequada para o escopo de TCC**:
- ✅ Demonstra conceito de Agent Router
- ✅ Sistema funcional end-to-end
- ✅ Performance aceitável para testes
- ✅ Arquitetura modular bem documentada

### Melhorias Recomendadas para Produção

#### 1. Sistema de Cache
**Atual:** LocMemCache (memória local)
- ✅ Funciona para 1 servidor
- ⚠️ Não escala para múltiplos servidores

**Melhoria:** Migrar para Redis
```python
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```
**Benefícios:**
- Compartilhado entre múltiplos servidores
- Persistente (não perde ao reiniciar)
- Performance superior

#### 2. Cache no RAGService
**Atual:** Consulta banco de dados a cada mensagem

**Melhoria:** Implementar cache de dados estáticos
```python
@staticmethod
def get_medicos() -> List[Dict]:
    cache_key = 'rag_medicos'
    medicos = cache.get(cache_key)
    if not medicos:
        medicos = Medico.objects.prefetch_related(...)
        cache.set(cache_key, medicos, 86400)  # 24h
    return medicos
```

#### 3. Timeouts Configuráveis
**Atual:** Timeout fixo de 1 hora

**Melhoria:** Timeouts diferenciados por tipo de dado
```python
CACHE_TIMEOUTS = {
    'session': 7200,      # 2 horas
    'rag_data': 86400,    # 24 horas
    'tokens': 'midnight'  # Até meia-noite
}
```

#### 4. Banco de Dados
**Atual:** SQLite (desenvolvimento)

**Melhoria:** PostgreSQL (produção)
- Suporta mais conexões simultâneas
- Melhor performance com múltiplos servidores
- Recursos avançados (índices, particionamento)

#### 5. Monitoramento
**Melhoria:** Implementar métricas detalhadas
- Dashboard de cache (hits/misses)
- Alertas de performance
- Logs estruturados com ELK Stack

#### 6. Escalabilidade
**Melhoria:** Preparar para múltiplos servidores
- Load Balancer (Nginx/AWS ALB)
- Session Affinity (sticky sessions)
- Horizontal scaling

---

**Última atualização:** 10/11/2025  
**Versão:** 1.0  
**Autor:** Documentação Técnica - Chatbot Clínica Médica

