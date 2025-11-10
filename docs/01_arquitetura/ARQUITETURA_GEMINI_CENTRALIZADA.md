# Arquitetura Gemini Centralizada - Chatbot Clínica Médica - Atualizada 10/11/2025

## Visão Geral

A arquitetura atual mantém o **Google Gemini AI** como cérebro central do chatbot, mas agora estruturado em um conjunto de módulos especializados dentro de `api_gateway/services/gemini/`. O `GeminiChatbotService` continua responsável pelo fluxo completo de mensagens, porém delega tarefas específicas (detecção de intenção, extração de entidades, geração de respostas e gerenciamento de sessão) para componentes dedicados. Isso garante inteligência centralizada com código mais organizado e fácil de manter.

## Arquitetura Centralizada e Modular

### Serviços Principais

1. **`GeminiChatbotService`** (`api_gateway/services/gemini/core_service.py`)
   - Orquestra o pipeline de conversação
   - Coordena os módulos `IntentDetector`, `EntityExtractor`, `ResponseGenerator` e `SessionManager`
   - Integra com `RAGService`, `ConversationService`, `SmartSchedulingService` e `HandoffService`
   - Aplica lógica de pausa/retomada e confirmações de agendamento

2. **`IntentDetector`** (`api_gateway/services/gemini/intent_detector.py`)
   - Analisa mensagens com Gemini
   - Retorna intenção, próximo estado e confiança
   - Possui fallbacks por palavras-chave

3. **`EntityExtractor`** (`api_gateway/services/gemini/entity_extractor.py`)
   - Extrai entidades com Gemini + regex de apoio
   - Normaliza dados de pacientes, médicos, datas e horários
   - Valida especialidades contra a base persistida

4. **`ResponseGenerator`** (`api_gateway/services/gemini/response_generator.py`)
   - Monta prompts estruturados por intenção
   - Ajusta parâmetros conforme modo econômico do `TokenMonitor`
   - Utiliza contexto histórico e dados do RAG

5. **`SessionManager`** (`api_gateway/services/gemini/session_manager.py`)
   - Sincroniza cache e banco de dados
   - Mantém histórico recente da conversa
   - Persiste estados, entidades confirmadas e mensagens

6. **`RAGService`** (`api_gateway/services/rag_service.py`)
   - Consolida informações da clínica com cache inteligente
   - Exponibiliza dados para o Gemini responder com precisão

7. **`ConversationService`** (`api_gateway/services/conversation_service.py`)
   - Controla sessões, mensagens e estados persistentes
   - Dá suporte ao sistema de pausa/retomada de dúvidas

8. **`WhatsAppService`** (`api_gateway/services/whatsapp_service.py`)
   - Recebe e envia mensagens via WhatsApp Business API
   - Garante validação de webhook e suporte a templates

9. **`SmartSchedulingService`** (`api_gateway/services/smart_scheduling_service.py`)
   - Consulta horários em tempo real via Google Calendar
   - Consolida disponibilidade para o Gemini

10. **`GoogleCalendarService`** (`api_gateway/services/google_calendar_service.py`)
    - Integra com a agenda oficial da clínica
    - Cria e sincroniza eventos confirmados

11. **`HandoffService`** (`api_gateway/services/handoff_service.py`)
    - Gera links e mensagens para repasse à secretária
    - Valida dados do agendamento antes de concluir

12. **`TokenMonitor`** (`api_gateway/services/token_monitor.py`)
    - Monitora consumo de tokens do Gemini
    - Aciona modo econômico e registra uso diário

## Fluxo de Conversação

```
WhatsApp → WhatsAppService → GeminiChatbotService
                                    ↓
                       SessionManager + ConversationService
                                    ↓
                   IntentDetector → EntityExtractor
                                    ↓
 RAGService + SmartSchedulingService + HandoffService (quando necessário)
                                    ↓
                        ResponseGenerator → WhatsAppService
```

## Pipeline do Gemini

1. **Análise da mensagem**  
   - Intenção detectada por `IntentDetector`
   - Entidades extraídas por `EntityExtractor`
2. **Atualização de contexto**  
   - `SessionManager` sincroniza estados e histórico
   - `ConversationService` registra mensagens
3. **Respostas inteligentes**  
   - `ResponseGenerator` usa dados do RAG e do agendamento
   - `TokenMonitor` ajusta parâmetros em modo econômico
4. **Pós-processamento**  
   - Handoff e confirmações via `HandoffService`
   - Disponibilidade validada pelo `SmartSchedulingService`

## Intenções Suportadas

- `saudacao`
- `buscar_info`
- `agendar_consulta`
- `confirmar_agendamento`
- `buscar_medico`
- `buscar_exame`
- `buscar_horarios`
- `despedida`
- `duvida`

## Estados da Conversa Persistidos

- `idle`
- `collecting_patient_info`
- `collecting_info`
- `answering_questions`
- `confirming_name`
- `selecting_specialty`
- `selecting_doctor`
- `choosing_schedule`
- `confirming`

## Arquivos Substituídos na Refatoração

- `api_gateway/services/gemini_chatbot_service.py` ➜ dividido em `api_gateway/services/gemini/`
- `flow_agent/`, `base_service.py`, `intent_detection_service.py`, `smart_collection_service.py` ➜ removidos
- Novos módulos centralizados expostos em `api_gateway/services/gemini/__init__.py`

## Como Usar

### Processamento de Mensagem
```python
from api_gateway.services.gemini import GeminiChatbotService

gemini_chatbot_service = GeminiChatbotService()
result = gemini_chatbot_service.process_message(phone_number, message)

response = result['response']
intent = result.get('intent')
confidence = result.get('confidence')
handoff_link = result.get('handoff_link')
```

### Teste de Conexão
```python
status = gemini_chatbot_service.test_connection()
print(status['message'])
```

### Monitoramento de Tokens
```python
from api_gateway.services.token_monitor import token_monitor

stats = token_monitor.get_token_usage_stats()
print(f"Tokens usados hoje: {stats['tokens_used_today']}")
print(f"Limite diário: {stats['daily_limit']}")
print(f"Modo econômico ativo: {stats['economy_mode_active']}")
```

## Configuração Essencial

- Variáveis sensíveis no `.env` (ver `.env.example`)
- Apps habilitados em `core/settings.py` (`rag_agent`, `api_gateway`)
- Chaves necessárias: `GEMINI_API_KEY`, credenciais WhatsApp, Google Calendar, etc.

## Endpoints de Teste (prefixo `/api/`)

- `GET /api/test/gemini/` – valida conexão com Gemini
- `POST /api/test/chatbot/` – executa `process_message`
- `POST /api/test/intent-analysis/` – roda apenas o `IntentDetector`
- `POST /api/test/entity-extraction/` – testa o `EntityExtractor`
- `POST /api/test/handoff/` – gera handoff com dados simulados
- `GET /api/test/check-data/` – verifica dados persistidos
- `GET /api/monitor/tokens/` – estatísticas do `TokenMonitor`
- `POST /api/monitor/tokens/reset/` – zera contadores de tokens
- `GET /api/test/calendar/` – checa integração com Google Calendar
- `GET /api/test/availability/<doctor_name>/` – horários de um médico

## Persistência e Cache

- `ConversationSession` e `ConversationMessage` armazenam estado completo
- Cache em camadas: sessões ativas, dados RAG, tokens e disponibilidade
- Limpeza automática de sessões antigas via `ConversationService`

## Logs e Monitoramento

- Logs estruturados para intents, entidades e respostas
- Auditoria de consumo de tokens
- Histórico de agendamentos e handoffs gerado automaticamente

## Próximos Passos Recomendados

1. Garantir credenciais válidas (Gemini, WhatsApp, Google)
2. Executar endpoints de teste após cada ajuste
3. Monitorar métricas de tokens em produção
4. Ajustar prompts do `ResponseGenerator` conforme novas intenções
5. Expandir base RAG sempre que novos serviços forem adicionados
