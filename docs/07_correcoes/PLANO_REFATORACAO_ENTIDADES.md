# 📋 PLANO COMPLETO: Refatoração da Arquitetura de Extração de Entidades

## 🎯 **Objetivo**
Corrigir a duplicação de responsabilidades entre `IntentDetector` e `EntityExtractor`, fazendo com que cada módulo tenha uma responsabilidade única e bem definida, mantendo a lógica do projeto intacta.

## 🔍 **Problema Atual**
- `IntentDetector` está extraindo entidades via Gemini (responsabilidade do `EntityExtractor`)
- `EntityExtractor` só é usado como fallback quando Gemini falha
- Duplicação de lógica de extração de entidades
- Arquitetura inconsistente com princípio de responsabilidade única

## 📊 **Arquitetura Proposta**

```
ANTES (Atual):
IntentDetector → [Detecta Intenção + Extrai Entidades] → Core Service
EntityExtractor → [Apenas Fallback Regex] → Core Service

DEPOIS (Proposta):
IntentDetector → [Detecta Apenas Intenção] → Core Service
EntityExtractor → [Extrai Entidades via Gemini + Regex] → Core Service
```

## 🛠️ **Mudanças Detalhadas**

### **1. EntityExtractor - Adicionar Extração via Gemini**

**Arquivo**: `api_gateway/services/gemini/entity_extractor.py`

**Mudanças**:
- Adicionar método `extract_entities_with_gemini(message, session, conversation_history, clinic_data)`
- Adicionar método `extract_entities(message, session, conversation_history, clinic_data)` (método principal)
- Mover lógica de prompt de extração do `IntentDetector` para cá
- Manter métodos regex existentes como fallback
- Adicionar configuração do modelo Gemini (similar ao IntentDetector)

**Novos métodos**:
```python
def extract_entities_with_gemini(self, message: str, session: Dict, 
                                conversation_history: List, clinic_data: Dict) -> Dict[str, str]

def extract_entities(self, message: str, session: Dict, 
                    conversation_history: List, clinic_data: Dict) -> Dict[str, str]

def _build_entity_extraction_prompt(self, message: str, session: Dict, 
                                   conversation_history: List, clinic_data: Dict) -> str
```

### **2. IntentDetector - Remover Extração de Entidades**

**Arquivo**: `api_gateway/services/gemini/intent_detector.py`

**Mudanças**:
- Remover seção de extração de entidades do prompt (linhas 179-200)
- Simplificar prompt para focar apenas em detecção de intenção
- Remover campo `entities` do JSON de resposta
- Manter apenas: `intent`, `next_state`, `confidence`, `reasoning`
- Atualizar método `_extract_analysis_from_response()` para não processar entidades

**Prompt simplificado**:
```python
# REMOVER esta seção do prompt:
# 3. ENTIDADES EXTRAÍDAS (EXTRAIA SEMPRE QUE POSSÍVEL):
#    - nome_paciente: Nome completo do paciente
#    - medico: Nome do médico mencionado
#    - especialidade: Especialidade médica
#    - data: Data em formato DD/MM/YYYY ou texto
#    - horario: Horário em formato HH:MM ou texto

# MANTER apenas:
# 1. INTENÇÃO PRINCIPAL
# 2. PRÓXIMO ESTADO DA CONVERSA  
# 3. CONFIANÇA
```

### **3. Core Service - Atualizar Orquestração**

**Arquivo**: `api_gateway/services/gemini/core_service.py`

**Mudanças**:
- Linha 96-98: Separar chamadas para IntentDetector e EntityExtractor
- Linha 104-109: Usar EntityExtractor como método principal, não fallback
- Atualizar lógica de processamento para usar entidades do EntityExtractor
- Manter validação de especialidade existente

**Fluxo atualizado**:
```python
# 4. Detectar intenção (sem entidades)
intent_result = self.intent_detector.analyze_message(
    message, session, conversation_history, clinic_data
)

# 5. Extrair entidades (método principal)
entities_result = self.entity_extractor.extract_entities(
    message, session, conversation_history, clinic_data
)

# 6. Combinar resultados
analysis_result = {
    'intent': intent_result['intent'],
    'next_state': intent_result['next_state'],
    'confidence': intent_result['confidence'],
    'entities': entities_result,
    'reasoning': intent_result.get('reasoning', '')
}
```

### **4. Session Manager - Manter Compatibilidade**

**Arquivo**: `api_gateway/services/gemini/session_manager.py`

**Mudanças**:
- Nenhuma mudança necessária
- Manter lógica de atualização de sessão existente
- Entidades continuam vindo do `analysis_result['entities']`

## 🔄 **Fluxo de Execução Atualizado**

```
1. Core Service recebe mensagem
2. IntentDetector → Detecta intenção (agendar_consulta, buscar_info, etc.)
3. EntityExtractor → Extrai entidades (nome, médico, data, etc.)
4. Core Service → Combina resultados
5. Core Service → Valida especialidades (mantém lógica existente)
6. Core Service → Processa agendamento/confirmação
7. Response Generator → Gera resposta
8. Session Manager → Atualiza sessão
```

## ✅ **Critérios de Sucesso**

1. **Funcionalidade**: Todas as funcionalidades existentes continuam funcionando
2. **Performance**: Não degradar performance (mesmo número de chamadas Gemini)
3. **Logs**: Manter logs informativos existentes
4. **Testes**: Todos os testes existentes devem passar
5. **Modularidade**: Cada módulo tem responsabilidade única e bem definida

## 🧪 **Testes de Validação**

**Cenários a testar**:
1. Extração de nome do paciente
2. Extração de médico
3. Extração de especialidade
4. Extração de data/horário
5. Detecção de intenções
6. Fallback para regex quando Gemini falha
7. Validação de especialidades
8. Fluxo completo de agendamento

## 📝 **Ordem de Implementação**

1. **Fase 1**: Adicionar métodos no EntityExtractor
2. **Fase 2**: Simplificar IntentDetector
3. **Fase 3**: Atualizar Core Service
4. **Fase 4**: Testes e validação
5. **Fase 5**: Limpeza e documentação

## 🚨 **Pontos de Atenção**

1. **Manter compatibilidade**: Não quebrar interface existente
2. **Preservar logs**: Manter logs informativos para debug
3. **Token monitoring**: Continuar monitorando uso de tokens
4. **Error handling**: Manter tratamento de erros robusto
5. **Fallback**: Garantir que regex continue funcionando como fallback

## 📋 **Checklist de Implementação**

- [ ] Adicionar `extract_entities_with_gemini()` no EntityExtractor
- [ ] Adicionar `extract_entities()` (método principal) no EntityExtractor
- [ ] Remover extração de entidades do prompt do IntentDetector
- [ ] Simplificar JSON de resposta do IntentDetector
- [ ] Atualizar Core Service para usar ambos os módulos
- [ ] Testar extração de entidades
- [ ] Testar detecção de intenções
- [ ] Testar fluxo completo de agendamento
- [ ] Validar logs e monitoramento
- [ ] Executar testes existentes

## 🔧 **Detalhes Técnicos**

### **Prompt do EntityExtractor (novo)**
```python
prompt = f"""Você é um assistente especializado em extrair informações de mensagens de pacientes.

MENSAGEM: "{message}"

CONTEXTO:
- Estado: {current_state}
- Nome: {patient_name or 'Não informado'}
- Médico: {selected_doctor or 'Não selecionado'}
- Especialidade: {selected_specialty or 'Não selecionada'}
- Data: {preferred_date or 'Não informada'}
- Horário: {preferred_time or 'Não informado'}

EXTRAIA as seguintes entidades da mensagem:
- nome_paciente: Nome completo do paciente
- medico: Nome do médico mencionado
- especialidade: Especialidade médica
- data: Data mencionada
- horario: Horário mencionado

Responda APENAS com JSON:
{{
    "nome_paciente": "nome_ou_null",
    "medico": "médico_ou_null", 
    "especialidade": "especialidade_ou_null",
    "data": "data_ou_null",
    "horario": "horário_ou_null"
}}"""
```

### **Prompt do IntentDetector (simplificado)**
```python
prompt = f"""Você é um assistente virtual da {clinic_info.get('nome', 'clínica médica')}.

MENSAGEM: "{message}"

CONTEXTO:
- Estado: {current_state}
- Nome: {patient_name or 'Não informado'}

DETECTE a intenção principal:
- saudacao: Cumprimentos
- buscar_info: Perguntas sobre clínica
- agendar_consulta: Quero agendar/marcar consulta
- confirmar_agendamento: Confirmar dados
- despedida: Tchau, obrigado
- duvida: Não entendi, ajuda

DETERMINE o próximo estado:
- idle: Estado inicial
- collecting_patient_info: Coletando nome
- selecting_doctor: Escolhendo médico
- selecting_specialty: Escolhendo especialidade
- choosing_schedule: Escolhendo data/horário
- confirming: Confirmando dados
- answering_questions: Respondendo dúvidas

Responda APENAS com JSON:
{{
    "intent": "intenção_detectada",
    "next_state": "próximo_estado",
    "confidence": 0.95,
    "reasoning": "Explicação breve"
}}"""
```

---

**Este plano garante que a refatoração seja feita de forma segura, mantendo toda a funcionalidade existente enquanto corrige a arquitetura para seguir o princípio de responsabilidade única.**
