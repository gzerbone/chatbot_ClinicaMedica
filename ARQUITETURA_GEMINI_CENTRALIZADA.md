# Arquitetura Gemini Centralizada - Chatbot Simplificado

## Visão Geral

O projeto foi refatorado para usar o **Google Gemini AI** como protagonista principal do chatbot, responsável por gerenciar todo o fluxo de conversação e responder pacientes com base nas informações do RAG (Retrieval-Augmented Generation).

## Arquitetura Simplificada

### Serviços Principais

1. **`gemini_chatbot_service.py`** - **PROTAGONISTA PRINCIPAL**
   - Gerencia todo o fluxo de conversação
   - Identifica intenções e estados da conversa
   - Responde pacientes com base nas informações do RAG
   - Coordena pré-agendamentos e informações da clínica

2. **`rag_service.py`** - **Base de Conhecimento**
   - Acessa dados da clínica (médicos, especialidades, exames, preços)
   - Serializa informações para o Gemini
   - Integra com Google Calendar para disponibilidade

3. **`conversation_service.py`** - **Persistência**
   - Salva mensagens e histórico de conversas
   - Gerencia sessões de conversa

4. **`whatsapp_service.py`** - **Integração WhatsApp**
   - Processa webhooks do WhatsApp
   - Envia mensagens para pacientes

5. **`handoff_service.py`** - **Transferência para Secretária**
   - Gera links de handoff para agendamentos
   - Cria mensagens de confirmação

6. **`google_calendar_service.py`** - **Agenda**
   - Consulta disponibilidade de médicos
   - Integra com Google Calendar

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
- **cancelar_agendamento**: Cancelamento
- **despedida**: Encerramento de conversa
- **duvida**: Quando não entende a mensagem

## Estados da Conversa

- **idle**: Estado inicial
- **coletando_nome**: Coletando nome do paciente
- **confirmando_nome**: Confirmando nome extraído
- **selecionando_medico**: Escolhendo médico
- **escolhendo_horario**: Escolhendo data/horário
- **confirmando_agendamento**: Confirmando dados finais
- **agendamento_concluido**: Processo finalizado
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
```

### Teste de Conexão
```python
is_connected = gemini_chatbot_service.test_connection()
```

## Configuração

### Variáveis de Ambiente
```bash
GEMINI_API_KEY=sua_chave_aqui
GEMINI_ENABLED=True
GEMINI_MODEL=gemini-1.5-flash
GEMINI_TEMPERATURE=0.7
GEMINI_MAX_TOKENS=1024
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
- `POST /test-handoff-generation/` - Testa geração de handoff

## Logs e Monitoramento

O sistema gera logs detalhados para monitoramento:
- Análise de intenções com confiança
- Estados da conversa
- Respostas geradas
- Erros e fallbacks

## Próximos Passos

1. Configurar API key do Gemini
2. Testar conexão
3. Ajustar prompts se necessário
4. Monitorar logs de conversação
5. Expandir intenções conforme necessário
