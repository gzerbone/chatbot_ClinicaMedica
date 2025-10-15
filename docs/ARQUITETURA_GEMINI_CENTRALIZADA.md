# Arquitetura Gemini Centralizada - Chatbot Clínica Médica - Atualizada 05/09 (mais recente)

## Visão Geral

O projeto foi completamente refatorado para usar o **Google Gemini AI** como protagonista principal do chatbot, responsável por gerenciar todo o fluxo de conversação e responder pacientes com base nas informações do RAG (Retrieval-Augmented Generation). Esta arquitetura centralizada elimina a fragmentação anterior e simplifica drasticamente o fluxo de dados.

## Arquitetura Simplificada

### Serviços Principais

1. **`gemini_chatbot_service.py`** - **PROTAGONISTA PRINCIPAL**
   - Gerencia todo o fluxo de conversação
   - Identifica intenções e estados da conversa
   - Responde pacientes com base nas informações do RAG
   - Coordena pré-agendamentos e informações da clínica
   - Extrai entidades (nome, médico, data, horário) usando IA
   - Valida informações de agendamento
   - Gera handoff quando necessário

2. **`rag_service.py`** - **Base de Conhecimento**
   - Acessa dados da clínica (médicos, especialidades, exames, preços)
   - Serializa informações para o Gemini
   - Integra com Google Calendar para disponibilidade
   - Fornece dados otimizados com cache inteligente

3. **`conversation_service.py`** - **Persistência**
   - Salva mensagens e histórico de conversas
   - Gerencia sessões de conversa
   - Processa confirmação de nomes de pacientes
   - Limpa sessões antigas automaticamente

4. **`whatsapp_service.py`** - **Integração WhatsApp**
   - Processa webhooks do WhatsApp
   - Envia mensagens para pacientes
   - Suporta templates e mensagens personalizadas
   - Valida webhooks do WhatsApp

5. **`handoff_service.py`** - **Transferência para Secretária**
   - Gera links de handoff para agendamentos
   - Cria mensagens de confirmação
   - Valida informações do médico no banco de dados
   - Formata mensagens para WhatsApp

6. **`smart_scheduling_service.py`** - **Consulta de Horários**
   - Consulta disponibilidade no Google Calendar
   - Analisa solicitações de agendamento
   - Valida médicos no banco de dados
   - Gera informações de disponibilidade

7. **`google_calendar_service.py`** - **Agenda**
   - Consulta disponibilidade de médicos
   - Integra com Google Calendar
   - Sincroniza eventos

8. **`token_monitor.py`** - **Monitoramento de Tokens**
   - Monitora uso de tokens do Gemini
   - Aplica modo econômico quando necessário
   - Otimiza configurações automaticamente

## Fluxo de Conversação

```
Mensagem do WhatsApp → Gemini Chatbot Service → Análise + Resposta → WhatsApp
                                    ↓
                            RAG Service (Dados da Clínica)
                                    ↓
                            Conversation Service (Histórico)
```

## Como o Gemini Funciona

### 1. Análise da Mensagem
- Identifica intenção (saudacao, agendar_consulta, buscar_info, etc.)
- Extrai entidades (nome, médico, data, horário)
- Determina próximo estado da conversa
- Calcula nível de confiança

### 2. Geração de Resposta
- Usa informações da clínica do RAG
- Considera histórico da conversa
- Segue instruções específicas por intenção
- Gera resposta contextualizada

### 3. Gerenciamento de Estado
- Mantém sessão da conversa
- Atualiza informações do paciente
- Controla fluxo de agendamento

## Intenções Suportadas

- **saudacao**: Cumprimentos e início de conversa
- **buscar_info**: Informações sobre clínica, endereço, telefone
- **agendar_consulta**: Processo de agendamento
- **confirmar_agendamento**: Confirmação de dados
- **buscar_medico**: Informações sobre médicos
- **buscar_exame**: Informações sobre exames
- **buscar_horarios**: Horários disponíveis
- **despedida**: Encerramento de conversa
- **duvida**: Quando não entende a mensagem

## Estados da Conversa

- **idle**: Estado inicial
- **collecting_patient_info**: Coletando dados do paciente
- **collecting_info**: Coletando informações
- **confirming_name**: Confirmando nome do paciente
- **selecting_doctor**: Selecionando médico
- **choosing_schedule**: Escolhendo horário
- **confirming**: Confirmando
- **fornecendo_info**: Fornecendo informações solicitadas

## Arquivos Removidos (Simplificação)

- `chatbot_service.py` - Substituído por `gemini_chatbot_service.py`
- `flow_agent.py` - Funcionalidades migradas para Gemini
- `intent_detection_service.py` - Gemini faz detecção de intenções
- `smart_collection_service.py` - Depreciado
- `context_manager.py` - Gemini gerencia contexto
- `base_service.py` - Gemini acessa RAG diretamente
- `flow_agent/` (diretório inteiro) - Não mais necessário

## Vantagens da Nova Arquitetura

1. **Simplicidade**: Apenas um serviço principal (Gemini)
2. **Inteligência**: Gemini entende contexto e intenções
3. **Flexibilidade**: Fácil de expandir e modificar
4. **Manutenção**: Menos código para manter
5. **Performance**: Menos camadas de processamento
6. **Consistência**: Respostas mais coerentes

## Como Usar

### Processamento de Mensagem
```python
from api_gateway.services.gemini_chatbot_service import gemini_chatbot_service

result = gemini_chatbot_service.process_message(phone_number, message)
response = result['response']
intent = result['intent']
confidence = result['confidence']
state = result['state']
session_data = result['session_data']
```

### Teste de Conexão
```python
is_connected = gemini_chatbot_service.test_connection()
```

### Monitoramento de Tokens
```python
from api_gateway.services.token_monitor import token_monitor

stats = token_monitor.get_token_usage_stats()
print(f"Tokens usados hoje: {stats['tokens_used_today']}")
print(f"Limite diário: {stats['daily_limit']}")
print(f"Modo econômico: {stats['economy_mode_active']}")
```

## Configuração

### Variáveis de Ambiente
Todas as configurações sensíveis são gerenciadas pelo arquivo `.env` na raiz do projeto.

**Importante:** Nunca exponha valores reais de API keys ou tokens. Use o arquivo `.env.example` como referência para as variáveis necessárias.

```bash
# Ver arquivo .env.example para lista completa
# Variáveis principais incluem:
# - GEMINI_API_KEY
# - WHATSAPP_ACCESS_TOKEN
# - WHATSAPP_VERIFY_TOKEN
# - GOOGLE_CALENDAR_ID
# - E outras...
```

### Django Settings
```python
INSTALLED_APPS = [
    'rag_agent',
    'api_gateway',
]
```

## Endpoints de Teste

- `GET /test-gemini-connection/` - Testa conexão com Gemini
- `POST /test-chatbot-service/` - Testa processamento de mensagem
- `POST /test-intent-analysis/` - Testa análise de intenção
- `POST /test-entity-extraction/` - Testa extração de entidades
- `POST /test-handoff-generation/` - Testa geração de handoff
- `GET /check-stored-data/` - Verifica dados armazenados
- `GET /token-usage-stats/` - Monitora uso de tokens
- `POST /reset-token-usage/` - Reseta contador de tokens

## Logs e Monitoramento

O sistema gera logs detalhados para monitoramento:
- Análise de intenções com confiança
- Estados da conversa
- Respostas geradas
- Erros e fallbacks
- Uso de tokens do Gemini
- Entidades extraídas
- Sessões de conversa
- Handoffs gerados

## Persistência de Dados

### Modelos Principais
- **ConversationSession**: Sessões de conversa persistentes
- **ConversationMessage**: Mensagens individuais com entidades
- **ClinicaInfo**: Informações da clínica
- **Medico**: Dados dos médicos
- **Especialidade**: Especialidades médicas
- **Convenio**: Convênios aceitos
- **Exame**: Exames disponíveis

### Cache Inteligente
- Cache de dados da clínica (30 minutos)
- Cache de sessões de conversa
- Cache de médicos específicos
- Cache de especialidades

## Próximos Passos

1. Configurar API key do Gemini
2. Testar conexão
3. Ajustar prompts se necessário
4. Monitorar logs de conversação
5. Expandir intenções conforme necessário
6. Configurar Google Calendar
7. Testar handoff com secretária
