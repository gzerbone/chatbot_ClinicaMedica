# ⚡ Guia Rápido - Agent Router

> Referência rápida para desenvolvedores trabalhando com o Agent Router

---

## 🎯 O que é?

**Agent Router** = `GeminiChatbotService` = Cérebro que decide para onde enviar cada mensagem

```
Mensagem → Análise → Roteamento → Serviço Específico → Resposta
```

---

## 📍 Localização Principal

```
api_gateway/services/gemini/core_service.py
    ↓
GeminiChatbotService (Agent Router)
```

---

## 🔀 Fluxo em 6 Passos

```python
def process_message(phone_number, message):
    # 1️⃣ PREPARAR
    session = get_session(phone_number)
    
    # 2️⃣ ANALISAR
    intent = IntentDetector.analyze(message)
    entities = EntityExtractor.extract(message)

    # 3️⃣ CONFIRMAR NOME (novo fluxo antecipado)
    manual_name_response = Router.handle_patient_name(phone_number, session, message, intent, entities)
    if manual_name_response:
        return manual_name_response

    # 4️⃣ ROTEAR
    if intent == 'buscar_info':
        result = RAGService.buscar()
    elif intent == 'agendar_consulta':
        result = SmartSchedulingService.agendar()
    elif intent == 'confirmar_agendamento':
        result = HandoffService.confirmar()

    # 5️⃣ RESPONDER
    response = ResponseGenerator.generate(result)

    # 6️⃣ SALVAR
    SessionManager.save(session, response)
    
    return response
```

---

## 🎯 Intenções Suportadas

| Intent | Descrição | Roteia para |
|--------|-----------|-------------|
| `saudacao` | Oi, olá | ResponseGenerator |
| `buscar_info` | Perguntas | RAGService |
| `agendar_consulta` | Agendar | SmartSchedulingService |
| `confirmar_agendamento` | Confirmar | HandoffService |
| `duvida` | Não entendi | ResponseGenerator |
| `despedida` | Tchau | ResponseGenerator |

---

## 📦 Módulos Principais

```
GeminiChatbotService (Router)
    ├── IntentDetector      → Detecta intenção
    ├── EntityExtractor     → Extrai dados
    ├── ResponseGenerator   → Gera resposta
    └── SessionManager      → Salva estado
```

---

## 🔄 Serviços Externos

```
Router chama:
    ├── RAGService               → Base de conhecimento
    ├── SmartSchedulingService   → Agendamento + Calendar
    ├── HandoffService           → Links para secretaria
    ├── ConversationService      → Persistência + confirmação de nome
    └── GoogleCalendarService    → Horários reais
```

---

## 🔧 Como Adicionar Nova Intenção

### Passo 1: Definir no IntentDetector

```python
# api_gateway/services/gemini/intent_detector.py

def _build_analysis_prompt(...):
    prompt = f"""
    ...
    1. INTENÇÃO PRINCIPAL:
       - saudacao
       - buscar_info
       - agendar_consulta
       - nova_intencao  ← ADICIONAR AQUI
    ...
    """
```

### Passo 2: Adicionar Roteamento

```python
# api_gateway/services/gemini/core_service.py

def process_message(...):
    ...
    # Adicionar novo caso
    if analysis_result['intent'] == 'nova_intencao':
        result = self._handle_nova_feature(message, session)
    ...
```

### Passo 3: Criar Handler

```python
def _handle_nova_feature(self, message: str, session: Dict) -> Dict:
    """Handler para nova funcionalidade"""
    try:
        # Implementar lógica
        result = novo_service.processar(message)
        return result
    except Exception as e:
        logger.error(f"Erro: {e}")
        return fallback_response
```

---

## 🧪 Como Testar

### Teste Rápido via cURL

```bash
# Teste completo do Router
curl -X POST http://localhost:8000/api/test/chatbot/ \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+5511999999999",
    "message": "Olá"
  }'
```

### Teste apenas Intent

```bash
curl -X POST http://localhost:8000/api/test/intent-analysis/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Quero agendar consulta",
    "phone_number": "+5511999999999"
  }'
```

### Teste apenas Entidades

```bash
curl -X POST http://localhost:8000/api/test/entity-extraction/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Meu nome é João Silva",
    "phone_number": "+5511999999999"
  }'
```

---

## 📊 Estados da Conversa

```
idle
  → collecting_patient_info
    → confirming_name
      → selecting_specialty
        → selecting_doctor
          → choosing_schedule
            → confirming (FIM)

[dúvida] → answering_questions → [volta ao anterior]
```

---

## ⚙️ Configurações Importantes

```python
# .env
GEMINI_API_KEY=sua_chave_aqui
GEMINI_MODEL=gemini-2.0-flash
GEMINI_ENABLED=true

# Parâmetros
INTENT_TEMPERATURE=0.7    # Mais determinístico
RESPONSE_TEMPERATURE=0.9  # Mais criativo
DAILY_TOKEN_LIMIT=150000
```

---

## 🛡️ Sistema de Fallback

```
1. TENTA: Gemini AI
   ↓ [erro]
2. TENTA: Palavras-chave
   ↓ [erro]
3. USA: Intent padrão ('duvida')
   ↓ [erro crítico]
4. RETORNA: Mensagem de erro amigável
```

---

## 🔍 Debugging

### Logs a Observar

```python
# Indica início do processamento
📱 Processando mensagem de +5511999999999

# Mostra estado atual
📊 Estado atual da sessão: selecting_doctor

# Intent detectado
🔍 Intent detectado: agendar_consulta, Confiança: 0.95

# Entidades extraídas
📦 Entidades extraídas: {'patient_name': 'João', ...}

# Sucesso
✅ Resposta gerada com sucesso
```

### Logs de Erro

```python
# Erro na API do Gemini
❌ Erro ao processar mensagem: API Error

# Intent desconhecido
⚠️ Intent desconhecido: xyz

# Processamento lento
⚠️ Processamento lento: 6.3s
```

---

## 🚨 Troubleshooting Rápido

| Problema | Causa Provável | Solução |
|----------|---------------|---------|
| Intent errado | Prompt desatualizado | Revisar `_build_analysis_prompt()` |
| Entidades não extraídas | Regex falhou | Verificar `EntityExtractor` |
| Resposta genérica | Fallback acionado | Verificar logs do Gemini |
| Timeout | Gemini lento | Verificar API status |
| Estado errado | Sessão não salva | Verificar `SessionManager` |

---

## 💡 Dicas Rápidas

### ✅ Boas Práticas

```python
# BOM: Logs informativos
logger.info(f"🔍 Intent: {intent}")

# BOM: Try-catch específico
try:
    result = gemini.analyze()
except GeminiAPIError:
    result = fallback_analysis()

# BOM: Validar entrada
if not phone_number:
    raise ValueError("phone_number obrigatório")
```

### ❌ Evitar

```python
# RUIM: Sem tratamento de erro
result = gemini.analyze()  # E se falhar?

# RUIM: Log genérico
logger.info("Processando")  # Processando o quê?

# RUIM: Sem validação
process_message(None, "")  # Vai dar erro
```

---

## 📈 Monitoramento

```bash
# Ver uso de tokens
curl http://localhost:8000/api/monitor/tokens/

# Resposta:
{
  "tokens_used_today": 12450,
  "daily_limit": 150000,
  "percentage_used": 8.3%,
  "economy_mode_active": false
}
```

---

## 🔗 Links Úteis

- 📄 Documentação Completa: `AGENT_ROUTER_COMPLETO.md`
- 💻 Implementação Técnica: `IMPLEMENTACAO_TECNICA_ROUTER.md`
- 🏗️ Arquitetura: `docs/01_arquitetura/ARQUITETURA_ATUAL.md`
- 🔄 Fluxos: `docs/04_fluxos_processos/FLUXO_COMPLETO_PROJETO.md`

---

## 📝 Checklist Rápido para Nova Feature

- [ ] Definir intent no prompt
- [ ] Adicionar caso no roteamento
- [ ] Criar handler específico
- [ ] Adicionar logs
- [ ] Tratamento de erros
- [ ] Criar teste
- [ ] Testar end-to-end
- [ ] Documentar

---

## 🎓 Resumo Ultra-Rápido

```
Agent Router = GeminiChatbotService

Mensagem → Intent → Roteamento → Serviço → Resposta

6 intents: saudacao, buscar_info, agendar_consulta, 
           confirmar_agendamento, duvida, despedida

Fallback: Gemini → Keywords → Padrão → Erro
```

---

**Guia rápido criado em:** 10/11/2025  
**Para dúvidas:** Consulte `AGENT_ROUTER_COMPLETO.md`

