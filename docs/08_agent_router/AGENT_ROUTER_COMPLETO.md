# 🎯 Agent Router - Sistema de Roteamento de Agentes

## 📚 Índice

1. [O que é um Agent Router?](#o-que-é-um-agent-router)
2. [Por que implementamos um Agent Router?](#por-que-implementamos-um-agent-router)
3. [Tipos de Roteamento](#tipos-de-roteamento)
4. [Arquitetura do Agent Router no Projeto](#arquitetura-do-agent-router-no-projeto)
5. [Fluxo Detalhado de Roteamento](#fluxo-detalhado-de-roteamento)
6. [Componentes do Sistema](#componentes-do-sistema)
7. [Intenções Suportadas](#intenções-suportadas)
8. [Estados da Conversa](#estados-da-conversa)
9. [Exemplos Práticos](#exemplos-práticos)
10. [Decisões de Roteamento](#decisões-de-roteamento)
11. [Tratamento de Erros e Fallbacks](#tratamento-de-erros-e-fallbacks)
12. [Monitoramento e Performance](#monitoramento-e-performance)

---

## 🎯 O que é um Agent Router?

Um **Agent Router** (Roteador de Agentes) é um componente arquitetural que funciona como um "direcionador inteligente" de mensagens. Pense nele como um operador de telemarketing que decide para qual departamento encaminhar sua ligação, mas de forma automatizada e inteligente.

### Analogia Simples

Imagine um hospital onde você chega na recepção:

```
Você: "Preciso marcar uma consulta com cardiologista"
Recepcionista (Router): Analisa sua necessidade → Encaminha para o Setor de Agendamento

Você: "Quais médicos atendem aqui?"
Recepcionista (Router): Analisa sua necessidade → Encaminha para o Setor de Informações

Você: "Quero confirmar minha consulta"
Recepcionista (Router): Analisa sua necessidade → Encaminha para o Setor de Confirmações
```

O **Agent Router** faz exatamente isso, mas de forma automática e inteligente com mensagens de WhatsApp!

---

## 🤔 Por que implementamos um Agent Router?

Nosso projeto atende **todos os critérios** que justificam a implementação de um Agent Router:

### ✅ Critérios Atendidos

| Critério | Como Atendemos |
|----------|----------------|
| **Múltiplas Integrações** | WhatsApp API, Google Calendar API, Gemini AI, Banco de Dados SQLite |
| **Diversos Tipos de Entrada** | Perguntas, comandos, agendamentos, confirmações, dúvidas |
| **Arquitetura Modular** | 4 módulos especializados + 8 serviços independentes |
| **Tratamento de Erros Sofisticado** | Sistema de fallback, modo econômico, contingências múltiplas |
| **Sistema Não-Determinístico** | Usa LLM (Gemini) para decisões contextuais e flexíveis |

---

## 🔀 Tipos de Roteamento

Nosso projeto utiliza uma **abordagem híbrida** que combina duas técnicas:

### 1. Roteamento Baseado em Intenção (Principal) 🎯

**O que é:** Identifica a intenção do usuário e mapeia para ações específicas.

**Como funciona:**
```
Mensagem do Usuário → Análise de Intenção → Roteamento para Serviço Específico
```

**Vantagens:**
- ✅ Separação clara entre entrada e processamento
- ✅ Fácil de depurar e escalar
- ✅ Extensível para novas intenções
- ✅ Lógica de roteamento organizada

**Desvantagens:**
- ⚠️ Requer mapeamento explícito de intenções
- ⚠️ Pode ter dificuldades com intenções muito ambíguas

### 2. Chamada de Funções com LLM (Complementar) 🤖

**O que é:** Usa o Gemini AI para determinar qual função/serviço chamar.

**Como funciona:**
```
Mensagem → Gemini AI → Decisão Contextual → Seleção de Função/Serviço
```

**Vantagens:**
- ✅ Processamento dinâmico e flexível
- ✅ Lida bem com entradas complexas
- ✅ Contexto histórico considerado
- ✅ Aprendizado de padrões

**Desvantagens:**
- ⚠️ Maior latência (chamada LLM)
- ⚠️ Custo de tokens
- ⚠️ Necessita monitoramento

---

## 🏗️ Arquitetura do Agent Router no Projeto

### Diagrama Geral da Arquitetura

```
                    ┌─────────────────────────────────┐
                    │   📱 WhatsApp Business API      │
                    │   (Entrada de Mensagens)        │
                    └────────────┬────────────────────┘
                                 │
                                 │ Mensagem do Usuário
                                 │
                    ┌────────────▼────────────────────┐
                    │   🌐 Django Webhook Handler     │
                    │   (api_gateway/views.py)        │
                    └────────────┬────────────────────┘
                                 │
                                 │
                    ┌────────────▼────────────────────┐
                    │   🎯 AGENT ROUTER               │
                    │   GeminiChatbotService          │
                    │   (Orquestrador Principal)      │
                    │                                 │
                    │   📂 core_service.py            │
                    └────────────┬────────────────────┘
                                 │
                                 │ process_message()
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        │         ETAPA 1: ANÁLISE DE INTENÇÃO           │
        │                        │                        │
        │           ┌────────────▼────────────┐           │
        │           │   🔍 IntentDetector     │           │
        │           │   intent_detector.py    │           │
        │           │                         │           │
        │           │   - Gemini AI           │           │
        │           │   - Análise Contextual  │           │
        │           │   - Fallback Keywords   │           │
        │           └────────────┬────────────┘           │
        │                        │                        │
        │           Retorna: intent, confidence           │
        │                        │                        │
        └────────────────────────┼────────────────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        │         ETAPA 2: EXTRAÇÃO DE ENTIDADES         │
        │                        │                        │
        │           ┌────────────▼────────────┐           │
        │           │   📦 EntityExtractor    │           │
        │           │   entity_extractor.py   │           │
        │           │                         │           │
        │           │   - Gemini AI           │           │
        │           │   - Regex Fallback      │           │
        │           │   - Validação BD        │           │
        │           └────────────┬────────────┘           │
        │                        │                        │
        │    Retorna: nome, especialidade, médico, etc   │
        │                        │                        │
        └────────────────────────┼────────────────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        │         ETAPA 3: DECISÃO DE ROTEAMENTO         │
        │                        │                        │
        │           ┌────────────▼────────────┐           │
        │           │   🧭 ROTEADOR PRINCIPAL │           │
        │           │   (switch de intenções) │           │
        │           └────────────┬────────────┘           │
        │                        │                        │
        └────────────────────────┼────────────────────────┘
                                 │
                ┌────────────────┼────────────────┐
                │                │                │
                │    ROTEAMENTO PARA SERVIÇOS    │
                │                │                │
     ┌──────────▼─────┐  ┌──────▼──────┐  ┌─────▼────────┐
     │  📚 RAGService │  │ 📅 Smart    │  │ 🔗 Handoff   │
     │                │  │  Scheduling │  │   Service    │
     │  - Base de     │  │             │  │              │
     │    Conhecimento│  │  - Google   │  │  - Geração   │
     │  - Médicos     │  │    Calendar │  │    de Links  │
     │  - Especialid. │  │  - Horários │  │  - Confirmação│
     │  - Convênios   │  │  - Datas    │  │              │
     └────────┬───────┘  └──────┬──────┘  └──────┬───────┘
          │                     │                 │
          │    (intent: buscar_info)             │
          │    (intent: agendar_consulta)        │
          │    (intent: confirmar_agendamento)   │
          │                     │                 │
          └─────────────────────┼─────────────────┘
                                │
                   ┌────────────▼────────────┐
                   │  💬 ResponseGenerator   │
                   │  response_generator.py  │
                   │                         │
                   │  - Monta Resposta       │
                   │  - Contexto Histórico   │
                   │  - Modo Econômico       │
                   └────────────┬────────────┘
                                │
                   ┌────────────▼────────────┐
                   │  💾 SessionManager      │
                   │  session_manager.py     │
                   │                         │
                   │  - Salva Estado         │
                   │  - Persiste Dados       │
                   │  - Cache + BD           │
                   └────────────┬────────────┘
                                │
                   ┌────────────▼────────────┐
                   │  📱 WhatsApp Response   │
                   │  (Resposta ao Usuário)  │
                   └─────────────────────────┘
```

### 📖 Explicação do Diagrama

1. **Entrada**: Mensagem chega via WhatsApp Business API
2. **Webhook**: Django recebe e encaminha para o Agent Router
3. **Agent Router (GeminiChatbotService)**: O cérebro do sistema
4. **IntentDetector**: Identifica o que o usuário quer (intenção)
5. **EntityExtractor**: Extrai informações específicas (nome, data, médico)
6. **Decisão de Roteamento**: Com base na intenção, roteia para o serviço adequado
7. **Serviços Especializados**: Cada um cuida de uma responsabilidade
8. **ResponseGenerator**: Monta a resposta final
9. **SessionManager**: Salva tudo no banco de dados
10. **Saída**: Resposta enviada de volta ao WhatsApp

---

## 🔄 Fluxo Detalhado de Roteamento

### Diagrama de Sequência Completo

```
┌─────────┐   ┌──────────┐   ┌────────────┐   ┌──────────────┐   ┌────────────┐
│ Usuário │   │ WhatsApp │   │   Agent    │   │    Intent    │   │  Serviços  │
│         │   │   API    │   │   Router   │   │   Detector   │   │ Especialis.│
└────┬────┘   └────┬─────┘   └─────┬──────┘   └──────┬───────┘   └─────┬──────┘
     │             │                │                 │                  │
     │ 1. Envia    │                │                 │                  │
     │ Mensagem    │                │                 │                  │
     │────────────>│                │                 │                  │
     │             │                │                 │                  │
     │             │ 2. POST        │                 │                  │
     │             │   Webhook      │                 │                  │
     │             │───────────────>│                 │                  │
     │             │                │                 │                  │
     │             │                │ 3. Obter        │                  │
     │             │                │    Sessão       │                  │
     │             │                │    (SessionMgr) │                  │
     │             │                │────┐            │                  │
     │             │                │<───┘            │                  │
     │             │                │                 │                  │
     │             │                │ 4. Analisar     │                  │
     │             │                │    Intenção     │                  │
     │             │                │────────────────>│                  │
     │             │                │                 │                  │
     │             │                │                 │ 5. Gemini AI    │
     │             │                │                 │    Análise      │
     │             │                │                 │────┐            │
     │             │                │                 │<───┘            │
     │             │                │                 │                  │
     │             │                │ 6. Retorna      │                  │
     │             │                │<─── Intent      │                  │
     │             │                │                 │                  │
     │             │                │ 7. Decisão de   │                  │
     │             │                │    Roteamento   │                  │
     │             │                │────┐            │                  │
     │             │                │<───┘            │                  │
     │             │                │                 │                  │
     │             │                │ 8. Chama Serviço│                  │
     │             │                │    Específico   │                  │
     │             │                │─────────────────────────────────>│
     │             │                │                 │                  │
     │             │                │                 │  9. Processa    │
     │             │                │                 │     Lógica      │
     │             │                │                 │     Específica  │
     │             │                │                 │     ────┐       │
     │             │                │                 │     <───┘       │
     │             │                │                 │                  │
     │             │                │ 10. Retorna     │                  │
     │             │                │<─────────────── Resultado ─────────│
     │             │                │                 │                  │
     │             │                │ 11. Gerar       │                  │
     │             │                │     Resposta    │                  │
     │             │                │────┐            │                  │
     │             │                │<───┘            │                  │
     │             │                │                 │                  │
     │             │                │ 12. Salvar      │                  │
     │             │                │     Estado      │                  │
     │             │                │────┐            │                  │
     │             │                │<───┘            │                  │
     │             │                │                 │                  │
     │             │ 13. Retorna    │                 │                  │
     │             │<─── Resposta ──│                 │                  │
     │             │                │                 │                  │
     │ 14. Recebe  │                │                 │                  │
     │<── Resposta │                │                 │                  │
     │             │                │                 │                  │
```

### 📖 Explicação do Fluxo Sequencial

Vamos entender cada passo:

1. **Usuário envia mensagem**: "Quero agendar uma consulta"
2. **WhatsApp API recebe**: Encaminha para nosso servidor Django
3. **Router obtém sessão**: Busca ou cria sessão do usuário no banco de dados
4. **Solicita análise**: Envia mensagem para o IntentDetector
5. **Gemini AI analisa**: IA processa e identifica intenção = "agendar_consulta"
6. **Retorna intent**: Intenção + confiança volta para o Router
7. **Confirmação antecipada do nome**: Antes de rotear para outros serviços, o router chama `_handle_patient_name_flow()` que utiliza o nome já extraído pelo `EntityExtractor` (via Gemini AI) e valida usando `ConversationService.confirm_patient_name()`. Se o nome ainda não estiver confirmado, o fluxo interrompe aqui para pedir confirmação (sem acionar o LLM novamente).
8. **Decisão de roteamento**: Router decide qual serviço chamar
9. **Chama serviço específico**: No caso, SmartSchedulingService
10. **Serviço processa**: Busca médicos, horários, etc.
11. **Retorna resultado**: Dados processados voltam para o Router
12. **Gera resposta**: ResponseGenerator monta mensagem amigável
13. **Salva estado**: SessionManager persiste no banco de dados
14. **Retorna para WhatsApp**: Resposta vai para a API do WhatsApp
15. **Usuário recebe**: Mensagem chega no celular do usuário

---

## 🧩 Componentes do Sistema

### 1. GeminiChatbotService (Agent Router Principal)

**Localização:** `api_gateway/services/gemini/core_service.py`

**Responsabilidades:**
- 🎯 Orquestrar todo o fluxo de processamento
- 🔀 Decidir para qual serviço rotear
- 🔄 Coordenar módulos especializados
- 💾 Gerenciar estado da conversa
- 🔗 Integrar com serviços externos
- 🧾 Garantir que o nome do paciente seja coletado e confirmado antes de avançar para especialidade/médico

**Código Simplificado:**
```python
class GeminiChatbotService:
    def process_message(self, phone_number, message):
        # 1. Obter sessão
        session = self.session_manager.get_or_create_session(phone_number)
        
        # 2. Detectar intenção
        intent_result = self.intent_detector.analyze_message(message, session)
        
        # 3. Extrair entidades
        entities = self.entity_extractor.extract_entities(message, session)

        analysis_result = {
            'intent': intent_result['intent'],
            'entities': entities,
            'next_state': intent_result['next_state'],
            'confidence': intent_result['confidence']
        }

        # 3.1. Confirmar nome antes de roteamentos complexos
        manual_name_response = self._handle_patient_name_flow(phone_number, session, message, analysis_result)
        if manual_name_response:
            return manual_name_response
        
        # 4. DECISÃO DE ROTEAMENTO
        if intent_result['intent'] == 'buscar_info':
            # Rotear para RAG Service
            response = self._handle_info_request(...)
            
        elif intent_result['intent'] == 'agendar_consulta':
            # Rotear para Scheduling Service
            response = self._handle_scheduling_request(...)
            
        elif intent_result['intent'] == 'confirmar_agendamento':
            # Rotear para Handoff Service
            response = self._handle_appointment_confirmation(...)
        
        # 5. Gerar resposta final
        final_response = self.response_generator.generate_response(...)
        
        # 6. Salvar estado
        self.session_manager.update_session(...)
        
        return final_response
```

### 2. IntentDetector (Analisador de Intenções)

**Localização:** `api_gateway/services/gemini/intent_detector.py`

**Responsabilidades:**
- 🔍 Analisar mensagem do usuário
- 🎯 Identificar intenção principal
- 📊 Calcular confiança da análise
- 🔄 Determinar próximo estado
- 🛡️ Fallback com palavras-chave

**Como Funciona:**

```
┌─────────────────────────────────────────────┐
│        IntentDetector.analyze_message()     │
└─────────────────┬───────────────────────────┘
                  │
    ┌─────────────▼─────────────┐
    │  Monta Prompt Contextual  │
    │  - Mensagem do usuário    │
    │  - Histórico conversa     │
    │  - Estado atual           │
    │  - Dados da clínica       │
    └─────────────┬─────────────┘
                  │
    ┌─────────────▼─────────────┐
    │  Envia para Gemini AI     │
    │  - Temperature: 0.7       │
    │  - Top_p: 0.8            │
    │  - Max tokens: 300        │
    └─────────────┬─────────────┘
                  │
    ┌─────────────▼─────────────┐
    │  Gemini processa e        │
    │  retorna JSON:            │
    │  {                        │
    │    "intent": "agendar",   │
    │    "next_state": "...",   │
    │    "confidence": 0.95     │
    │  }                        │
    └─────────────┬─────────────┘
                  │
    ┌─────────────▼─────────────┐
    │  Valida resposta          │
    │  - Parse JSON             │
    │  - Verifica campos        │
    │  - Aplica correções       │
    └─────────────┬─────────────┘
                  │
    ┌─────────────▼─────────────┐
    │  Retorna análise para     │
    │  o Agent Router           │
    └───────────────────────────┘
```

### 3. EntityExtractor (Extrator de Entidades)

**Localização:** `api_gateway/services/gemini/entity_extractor.py`

**Responsabilidades:**
- 📦 Extrair informações específicas
- ✅ Validar dados contra banco
- 🔄 Normalizar informações
- 🛡️ Fallback com regex

**Entidades Extraídas:**
- 👤 Nome do paciente
- 🏥 Especialidade médica
- 👨‍⚕️ Nome do médico
- 📅 Data preferida
- ⏰ Horário preferido
- 💳 Tipo de convênio

### 4. ResponseGenerator (Gerador de Respostas)

**Localização:** `api_gateway/services/gemini/response_generator.py`

**Responsabilidades:**
- 💬 Gerar respostas contextualizadas
- 📝 Usar prompts estruturados
- 🎨 Formatar mensagens amigáveis
- 💰 Aplicar modo econômico

### 5. SessionManager (Gerenciador de Sessões)

**Localização:** `api_gateway/services/gemini/session_manager.py`

**Responsabilidades:**
- 💾 Persistir dados no banco
- 🔄 Sincronizar cache
- 📚 Gerenciar histórico
- 🕐 Controlar timeouts
- 🧾 Guardar `pending_name`, `patient_name` e `name_confirmed` para o fluxo de confirmação antecipada

---

## 🎯 Intenções Suportadas

O sistema reconhece **6 intenções principais**:

### Tabela de Intenções

| Intenção | Descrição | Palavras-chave | Exemplo |
|----------|-----------|----------------|---------|
| **saudacao** | Cumprimentos iniciais | oi, olá, bom dia, boa tarde | "Olá, boa tarde!" |
| **buscar_info** | Perguntas sobre a clínica | quais, quem, que, tem | "Quais médicos atendem aqui?" |
| **agendar_consulta** | Solicitar agendamento | agendar, marcar, consulta | "Quero agendar uma consulta" |
| **confirmar_agendamento** | Confirmar dados | sim, confirmar, correto | "Sim, está tudo certo" |
| **despedida** | Encerramento | tchau, obrigado, até logo | "Obrigado, até logo!" |
| **duvida** | Não compreendeu | não entendi, ajuda, repetir | "Não entendi, pode repetir?" |

### Diagrama de Intenções

```
                    ┌──────────────────┐
                    │  Mensagem User   │
                    └────────┬─────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
     ┌──────▼──────┐  ┌──────▼──────┐  ┌─────▼──────┐
     │  saudacao   │  │ buscar_info │  │  agendar   │
     │             │  │             │  │  _consulta │
     │ oi, olá     │  │ quais, quem │  │            │
     │ bom dia     │  │ tem, info   │  │ marcar,    │
     │             │  │             │  │ agendar    │
     └──────┬──────┘  └──────┬──────┘  └─────┬──────┘
            │                │                │
            │        ┌───────▼────────┐       │
            │        │ EntityExtractor│       │
            │        │ (se necessário)│       │
            │        └───────┬────────┘       │
            │                │                │
            └────────────────┼────────────────┘
                             │
                    ┌────────▼─────────┐
                    │  ROTEAMENTO      │
                    │  para Serviço    │
                    └──────────────────┘
```

### 🔍 Distinção Importante: buscar_info vs agendar_consulta

Esta é uma distinção **crítica** no sistema:

#### buscar_info (Apenas Informação)
```
❌ NÃO quer agendar, APENAS perguntar

Exemplos:
- "Quais médicos trabalham aqui?"
- "Que especialidades vocês têm?"
- "Quem é o cardiologista?"
- "Tem ortopedista?"

Roteamento → RAGService (busca na base de conhecimento)
```

#### agendar_consulta (Quer Marcar)
```
✅ Quer AGENDAR + menciona médico/especialidade

Exemplos:
- "Quero agendar com cardiologista"
- "Marcar consulta com Dr. João"
- "Preciso agendar"
- "Consulta com ortopedista"

Roteamento → SmartSchedulingService (inicia processo de agendamento)
```

---

## 🔄 Estados da Conversa

O sistema mantém um **estado** para cada conversa, controlando em que etapa do fluxo o usuário está.

### Diagrama de Máquina de Estados

```
                        ┌──────────┐
                   ┌───>│   idle   │<────┐
                   │    └────┬─────┘     │
                   │         │           │
                   │   [saudacao]        │
                   │         │           │
                   │    ┌────▼─────────────────┐
                   │    │ collecting_patient   │
                   │    │      _info           │
                   │    └────┬─────────────────┘
                   │         │
                   │   [nome extraído]
                   │         │
                   │    ┌────▼─────────────┐
                   │    │ confirming_name  │
                   │    └────┬─────────────┘
                   │         │
                   │   [nome confirmado]
                   │         │
        [dúvida]   │    ┌────▼──────────────┐
          ┌────────┤    │ selecting_        │
          │        │    │   specialty       │
          │        │    └────┬──────────────┘
          │        │         │
          │        │   [especialidade escolhida]
          │        │         │
          │        │    ┌────▼──────────────┐
          │        │    │ selecting_        │
          │        │    │   doctor          │
          │        │    └────┬──────────────┘
          │        │         │
          │        │   [médico escolhido]
          │        │         │
          │        │    ┌────▼──────────────┐
          │        │    │ choosing_         │
          │        │    │   schedule        │
          │        │    └────┬──────────────┘
          │        │         │
          │        │   [data e hora escolhidos]
          │        │         │
          │        │    ┌────▼──────────────┐
          │        │    │  confirming       │
          │        │    └────┬──────────────┘
          │        │         │
          │        │   [confirmação final]
          │        │         │
          │        └─────────┴────────> FIM
          │
          │    ┌────────────────────┐
          └───>│ answering_         │
               │   questions        │
               └────────────────────┘
                  [continuar/retomar]
                         │
                    volta ao estado
                      anterior
```

### Tabela de Estados

| Estado | Descrição | Próximo Passo |
|--------|-----------|---------------|
| **idle** | Conversa iniciando | Identificar intenção |
| **collecting_patient_info** | Perguntando e extraindo o nome completo (armazenando `pending_name`) | Confirmar nome |
| **confirming_name** | Fluxo dedicado para validar `pending_name` com o paciente antes de seguir | Escolher especialidade |
| **selecting_specialty** | Escolhendo especialidade | Escolher médico |
| **selecting_doctor** | Escolhendo médico | Escolher data/hora |
| **choosing_schedule** | Escolhendo data e horário | Confirmar agendamento |
| **confirming** | Confirmando dados finais | Gerar handoff |
| **answering_questions** | Respondendo dúvidas | Retomar ou continuar |

### 🔄 Sistema de Pausa/Retomada

O sistema permite que o usuário **pause** o agendamento para tirar dúvidas:

```
Usuário está em: selecting_doctor
                      ↓
Usuário: "Quais médicos tem disponível?"
                      ↓
Sistema detecta: intent = 'buscar_info'
                      ↓
Sistema PAUSA o agendamento
   - Salva estado atual: previous_state = 'selecting_doctor'
   - Muda para: current_state = 'answering_questions'
                      ↓
Sistema responde a dúvida
                      ↓
Usuário: "Continuar"
                      ↓
Sistema RETOMA o agendamento
   - Restaura: current_state = 'selecting_doctor'
   - Limpa: previous_state = null
                      ↓
Continua de onde parou!
```

---

## 📝 Exemplos Práticos

Vamos ver exemplos reais de como o roteamento funciona:

### Exemplo 1: Buscar Informação

```
👤 Usuário: "Quais médicos ortopedistas vocês têm?"

🤖 Sistema:
  1. IntentDetector analisa → intent: 'buscar_info'
  2. EntityExtractor extrai → specialty: 'Ortopedia'
  3. Router decide → RAGService.get_medicos_by_specialty('Ortopedia')
  4. ResponseGenerator monta resposta
  
📱 Resposta: "Temos 2 ortopedistas:
   • Dr. Carlos Silva
   • Dra. Ana Costa
   
   Gostaria de agendar com algum deles?"
```

**Fluxo Visual:**
```
Mensagem → IntentDetector → [buscar_info]
                ↓
         RAGService
                ↓
    Busca no banco de dados
                ↓
    Retorna lista de médicos
                ↓
      ResponseGenerator
                ↓
    "Temos 2 ortopedistas..."
```

### Exemplo 2: Agendar Consulta

```
👤 Usuário: "Quero agendar uma consulta com cardiologista"

🤖 Sistema:
  1. IntentDetector analisa → intent: 'agendar_consulta'
  2. EntityExtractor extrai → specialty: 'Cardiologia'
  3. Router decide → SmartSchedulingService
  4. Verifica médicos cardiologistas disponíveis
  5. Consulta Google Calendar para horários
  6. ResponseGenerator monta resposta com disponibilidade
  
📱 Resposta: "Certo! Para agendar com cardiologista, preciso de algumas informações.
   
   Primeiro, qual é o seu nome completo?"
```

**Fluxo Visual:**
```
Mensagem → IntentDetector → [agendar_consulta]
                ↓
    EntityExtractor → [specialty: Cardiologia]
                ↓
    SmartSchedulingService
                ↓
    GoogleCalendarService (verifica disponibilidade)
                ↓
    SessionManager (salva: selecting_specialty)
                ↓
    ResponseGenerator
                ↓
    "Certo! Para agendar..."
```

### Exemplo 3: Dúvida Durante Agendamento

```
👤 Usuário iniciou agendamento (estado: selecting_doctor)
👤 Usuário: "Quanto custa a consulta?"

🤖 Sistema:
  1. IntentDetector analisa → intent: 'buscar_info'
  2. Sistema detecta: usuário está em meio a agendamento
  3. ConversationService.pause_for_question()
     - Salva: previous_state = 'selecting_doctor'
     - Muda: current_state = 'answering_questions'
  4. Router → RAGService (busca informação de preços)
  5. Responde a dúvida
  
📱 Resposta: "A consulta com convênio é coberta pelo seu plano.
   Consulta particular: R$ 200,00
   
   Deseja continuar com o agendamento? Digite 'continuar'"
   
👤 Usuário: "continuar"

🤖 Sistema:
  1. Detecta palavra-chave "continuar"
  2. ConversationService.resume_appointment()
     - Restaura: current_state = 'selecting_doctor'
  3. Continua de onde parou
  
📱 Resposta: "Ótimo! Então, qual médico você prefere?"
```

**Fluxo Visual:**
```
Estado: selecting_doctor
         ↓
Mensagem: "Quanto custa?"
         ↓
IntentDetector → [buscar_info]
         ↓
Sistema detecta: em meio a agendamento
         ↓
PAUSA: previous_state = selecting_doctor
       current_state = answering_questions
         ↓
RAGService (busca preço)
         ↓
Responde dúvida
         ↓
Mensagem: "continuar"
         ↓
RETOMA: current_state = selecting_doctor
         ↓
Continua agendamento!
```

### Exemplo 4: Confirmação de Agendamento

```
👤 Usuário completou todas as informações
👤 Usuário: "Sim, confirmar"

🤖 Sistema:
  1. IntentDetector analisa → intent: 'confirmar_agendamento'
  2. ConversationService verifica informações completas:
     ✅ Nome: João Silva
     ✅ Especialidade: Cardiologia
     ✅ Médico: Dr. Pedro Santos
     ✅ Data: 15/11/2025
     ✅ Horário: 14:00
  3. Router decide → HandoffService
  4. Gera link de handoff para secretaria
  5. Muda estado para: 'confirming'
  
📱 Resposta: "✅ Perfeito! Seu pré-agendamento foi registrado:

   👤 Paciente: João Silva
   🏥 Especialidade: Cardiologia
   👨‍⚕️ Médico: Dr. Pedro Santos
   📅 Data: 15/11/2025
   ⏰ Horário: 14:00
   
   🔗 Link para secretaria confirmar:
   https://wa.me/5511999999?text=..."
```

**Fluxo Visual:**
```
Mensagem: "Sim, confirmar"
         ↓
IntentDetector → [confirmar_agendamento]
         ↓
ConversationService.get_missing_info()
         ↓
Verifica: todas informações completas ✅
         ↓
HandoffService
         ↓
Gera link de handoff
         ↓
SessionManager (salva: confirming)
         ↓
ResponseGenerator
         ↓
"✅ Perfeito! Seu pré-agendamento..."
```

---

## 🧭 Decisões de Roteamento

O Agent Router toma decisões baseadas em **múltiplos fatores**:

### Matriz de Decisão

```
┌────────────────────────────────────────────────────────────────────┐
│                    MATRIZ DE DECISÃO DO ROUTER                     │
└────────────────────────────────────────────────────────────────────┘

ENTRADA: intent, estado_atual, entidades, histórico
                            ↓
┌───────────────────────────────────────────────────────────────────┐
│                                                                   │
│  IF intent == 'saudacao':                                         │
│      IF estado == 'idle':                                         │
│          → ResponseGenerator (saudação inicial)                   │
│          → Próximo: collecting_patient_info                       │
│                                                                   │
│  IF intent == 'buscar_info':                                      │
│      IF estado NOT IN ['idle', 'answering_questions']:            │
│          → ConversationService.pause_for_question()              │
│          → Salva previous_state                                   │
│      → RAGService.buscar_informacao()                            │
│      → ResponseGenerator (resposta informativa)                   │
│                                                                   │
│  IF intent == 'agendar_consulta':                                │
│      IF entities['specialty']:                                    │
│          → SmartSchedulingService.analyze_request()              │
│          → GoogleCalendarService.get_availability()              │
│      IF entities['doctor']:                                       │
│          → Valida médico no banco                                │
│      → ResponseGenerator (próxima pergunta)                       │
│      → Avança estado do fluxo                                     │
│                                                                   │
│  IF intent == 'confirmar_agendamento':                            │
│      → ConversationService.get_missing_info()                    │
│      IF todas_informacoes_completas:                              │
│          → HandoffService.generate_handoff_link()                │
│          → Estado: confirming                                     │
│      ELSE:                                                        │
│          → Muda intent para 'agendar_consulta'                   │
│          → Solicita informação faltante                           │
│                                                                   │
│  IF intent == 'duvida':                                           │
│      → ResponseGenerator (esclarecimento)                         │
│      → Mantém estado atual                                        │
│                                                                   │
│  IF intent == 'despedida':                                        │
│      → ResponseGenerator (mensagem de encerramento)              │
│      → Estado: idle                                               │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

### Fatores de Decisão

O Router considera:

1. **Intenção Detectada** (peso: 40%)
   - Qual é o objetivo principal do usuário?

2. **Estado Atual da Conversa** (peso: 30%)
   - Em que etapa do fluxo estamos?

3. **Entidades Extraídas** (peso: 20%)
   - Quais informações já temos?

4. **Histórico da Conversa** (peso: 10%)
   - O que foi dito anteriormente?

### Diagrama de Decisão Simplificado

```
                    ┌─────────────┐
                    │  Intent     │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
         ┌────▼───┐   ┌───▼────┐  ┌───▼─────┐
         │buscar_ │   │agendar_│  │confirmar│
         │ info   │   │consulta│  │_agend.  │
         └────┬───┘   └───┬────┘  └───┬─────┘
              │           │           │
              │           │           │
         ┌────▼────┐ ┌───▼─────┐ ┌──▼──────┐
         │   RAG   │ │ Smart   │ │Handoff  │
         │ Service │ │Scheduling│ │Service  │
         └─────────┘ └─────────┘ └─────────┘
```

---

## 🛡️ Tratamento de Erros e Fallbacks

O sistema possui **múltiplas camadas de fallback** para garantir robustez:

### Hierarquia de Fallbacks

```
┌────────────────────────────────────────────────────┐
│           HIERARQUIA DE FALLBACKS                  │
└────────────────────────────────────────────────────┘

NÍVEL 1: Gemini AI (Método Principal)
   ↓
   [ERRO: API indisponível ou resposta inválida]
   ↓
NÍVEL 2: Análise por Palavras-chave (IntentDetector)
   ↓
   [ERRO: Não encontrou palavras-chave]
   ↓
NÍVEL 3: Intent Padrão (duvida)
   ↓
   [ERRO: Sistema completamente fora do ar]
   ↓
NÍVEL 4: Mensagem de Erro Amigável
```

### Exemplo de Fallback em Ação

```python
# 1. TENTA: Análise com Gemini
try:
    response = gemini.generate_content(prompt)
    intent = parse_json(response.text)
    
# 2. FALLBACK: Palavras-chave
except GeminiAPIError:
    if 'agendar' in message:
        intent = 'agendar_consulta'
    elif 'quais' in message:
        intent = 'buscar_info'
    
# 3. FALLBACK: Intent padrão
    else:
        intent = 'duvida'
        
# 4. FALLBACK: Mensagem de erro
except CriticalSystemError:
    return "Desculpe, estou com dificuldades técnicas..."
```

### Estratégias de Recuperação

| Tipo de Erro | Estratégia | Fallback |
|--------------|-----------|----------|
| **Gemini API down** | Usar análise por keywords | Intent padrão |
| **JSON inválido** | Parse manual da resposta | Extração de texto |
| **Banco de dados offline** | Usar cache em memória | Mensagem de erro |
| **Entidade não encontrada** | Regex como fallback | Solicitar novamente |
| **Timeout** | Retry com backoff | Resposta simplificada |

---

## 📊 Monitoramento e Performance

O sistema monitora constantemente o desempenho do Agent Router:

### Métricas Coletadas

1. **Uso de Tokens (Gemini AI)**
   ```
   - Tokens por análise de intent
   - Tokens por extração de entidades
   - Tokens por geração de resposta
   - Total diário
   - Modo econômico ativado?
   ```

2. **Latência de Roteamento**
   ```
   - Tempo de análise de intent
   - Tempo de extração de entidades
   - Tempo total de processamento
   - Tempo de resposta ao usuário
   ```

3. **Taxa de Sucesso**
   ```
   - % de intents detectados com sucesso
   - % de entidades extraídas corretamente
   - % de agendamentos completados
   - % de fallbacks acionados
   ```

4. **Roteamento**
   ```
   - Distribuição de intents (qual mais comum)
   - Serviços mais acionados
   - Estados mais frequentes
   - Tempo médio por estado
   ```

### Dashboard de Monitoramento

```
┌─────────────────────────────────────────────────────────┐
│              AGENT ROUTER - DASHBOARD                   │
└─────────────────────────────────────────────────────────┘

📊 DISTRIBUIÇÃO DE INTENTS (Hoje)
┌──────────────────────────┐
│ agendar_consulta  45% ████████████████
│ buscar_info       30% ██████████
│ saudacao          15% █████
│ confirmar_agend.  08% ███
│ outros            02% █
└──────────────────────────┘

⚡ PERFORMANCE
┌──────────────────────────┐
│ Tempo médio resposta: 1.8s
│ Taxa de sucesso: 97.3%
│ Fallbacks acionados: 2.7%
│ Uptime: 99.9%
└──────────────────────────┘

🤖 USO DE TOKENS (Gemini)
┌──────────────────────────┐
│ Tokens hoje: 45,230 / 150,000
│ Modo econômico: ❌ Desativado
│ Custo estimado: $1.35
│ Limite atingido em: ~3 dias
└──────────────────────────┘

🎯 TAXA DE CONVERSÃO
┌──────────────────────────┐
│ Conversas iniciadas: 127
│ Agendamentos iniciados: 89 (70%)
│ Agendamentos completos: 67 (75% dos iniciados)
│ Taxa abandono: 25%
└──────────────────────────┘
```

### Alertas Configurados

```
⚠️ ALERTAS ATIVOS

1. Tokens > 80% do limite diário
   → Ativa modo econômico automaticamente

2. Taxa de fallback > 10%
   → Notifica equipe técnica

3. Latência > 5 segundos
   → Investiga gargalos

4. Taxa de sucesso < 90%
   → Revisa prompts do Gemini

5. Gemini API offline
   → Ativa fallback completo + notifica
```

---

## 🎓 Resumo Executivo

### O que é o Agent Router neste projeto?

O **Agent Router** é o **GeminiChatbotService**, que funciona como o cérebro central do chatbot. Ele:

1. **Recebe** mensagens do WhatsApp
2. **Analisa** a intenção com Gemini AI
3. **Decide** para qual serviço especializado encaminhar
4. **Coordena** a execução e resposta
5. **Persiste** o estado da conversa

### Como ele funciona?

```
Mensagem → Análise de Intenção → Decisão de Roteamento → Serviço Específico → Resposta
```

### Por que é importante?

- ✅ **Organização**: Cada serviço tem uma responsabilidade clara
- ✅ **Escalabilidade**: Fácil adicionar novas funcionalidades
- ✅ **Manutenibilidade**: Código modular e testável
- ✅ **Inteligência**: Usa IA para decisões contextuais
- ✅ **Robustez**: Múltiplas camadas de fallback

### Benefícios Obtidos

1. **Separação de Responsabilidades**: Cada módulo faz uma coisa bem
2. **Extensibilidade**: Novas intenções = novos casos no switch
3. **Testabilidade**: Componentes isolados = testes mais fáceis
4. **Performance**: Roteamento eficiente para o serviço certo
5. **Experiência do Usuário**: Respostas rápidas e precisas

---

## 📖 Glossário

- **Agent Router**: Componente que direciona mensagens para serviços específicos
- **Intent (Intenção)**: O que o usuário quer fazer (agendar, perguntar, etc.)
- **Entity (Entidade)**: Informação específica extraída (nome, data, médico)
- **Estado**: Etapa atual do fluxo de conversa
- **Fallback**: Método alternativo usado quando o principal falha
- **LLM**: Large Language Model (Modelo de Linguagem Grande) - ex: Gemini
- **Roteamento**: Processo de decidir qual serviço deve processar a mensagem
- **Handoff**: Transferência de atendimento para a secretaria

---

## 📚 Referências

- Documentação oficial do projeto em `docs/`
- `ARQUITETURA_ATUAL.md` - Arquitetura completa do sistema
- `FLUXO_COMPLETO_PROJETO.md` - Fluxos de processamento
- `MODULARIZACAO_GEMINI_COMPLETA.md` - Detalhes da modularização

---

**Última atualização:** 10/11/2025  
**Versão:** 1.0  
**Autor:** Documentação Técnica - Chatbot Clínica Médica

