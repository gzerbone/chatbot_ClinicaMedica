# Correção de Erros no Fluxo de Confirmação

## 📋 Resumo dos Problemas

Durante testes reais, foram identificados **2 erros críticos** no fluxo de agendamento:

### Erro 1: "Olá, None!"
**Problema**: O bot não coletava o nome no início da conversa e, ao tentar confirmar, exibia "Olá, None!".

### Erro 2: Mensagem de Confirmação Duplicada
**Problema**: Após o usuário informar o nome, o bot enviava a mesma mensagem de confirmação **duas vezes seguidas**.

---

## 🔍 Análise das Causas

### Erro 1: Valor `None` não tratado

**Localização**: `api_gateway/services/gemini_chatbot_service.py`, linha 1295

**Código Original**:
```python
patient_name = session.get('patient_name', 'Paciente')
```

**Problema**:
- Se `session['patient_name']` existir mas for `None`, o valor retornado é `None` (não o default `'Paciente'`)
- Isso acontece porque `get()` só usa o default quando a chave **não existe**, não quando o valor é `None`
- Resultado: `"Olá, None! Para prosseguir..."`

**Solução**:
```python
# Garantir que patient_name nunca seja None
patient_name = session.get('patient_name') or 'Paciente'
```

O operador `or` retorna o segundo valor se o primeiro for `None`, `''`, `0`, etc.

---

### Erro 2: Confirmação Processada Múltiplas Vezes

**Localização**: `api_gateway/services/gemini_chatbot_service.py`, linhas 154-169

**Problema**:

1. **Falta de verificação de estado**: O código processava `confirmar_agendamento` toda vez que o intent era detectado, sem verificar se já estava em processo de confirmação.

2. **Instruções ambíguas para o Gemini**: O prompt não deixava claro que a confirmação só deveria ser solicitada UMA VEZ.

3. **Loop de confirmação**:
   ```
   Bot: "Deseja confirmar o agendamento de pneumologia...?"
   Usuário: "sim"
   Bot processa como confirmar_agendamento
   Bot: "Deseja confirmar o agendamento de pneumologia...?" (NOVAMENTE)
   Usuário: "confirmado"
   Bot processa como confirmar_agendamento (DE NOVO)
   ```

**Soluções Implementadas**:

#### Solução 1: Verificação de Estado
```python
# Verificar se é confirmação de agendamento e gerar handoff
if analysis_result['intent'] == 'confirmar_agendamento':
    # Verificar se já não está no estado de confirmação (evita duplicação)
    if session.get('current_state') == 'confirming':
        # Já está no processo de confirmação - não processar novamente
        logger.warning(f"⚠️ Ignorando confirmação duplicada para {phone_number}")
    else:
        # ... processar confirmação ...
        if missing_info_result['is_complete']:
            # ... gerar handoff ...
            # Marcar como já confirmado
            session['current_state'] = 'confirming'
```

**Benefícios**:
- ✅ Evita processar a mesma confirmação múltiplas vezes
- ✅ Usa o estado da sessão para rastrear se já está confirmando
- ✅ Log de warning para debug

#### Solução 2: Melhorias no Prompt

**Mudanças em `'agendar_consulta'`**:
```python
'agendar_consulta': """
...
- **IMPORTANTE**: NÃO peça confirmação se ainda faltam informações. Colete tudo ANTES de confirmar.
""",
```

**Mudanças em `'confirmar_agendamento'`**:
```python
'confirmar_agendamento': """
- VERIFIQUE primeiro se tem TODAS as informações na seção "INFORMAÇÕES JÁ COLETADAS":
  * Nome completo do paciente
  * Médico escolhido
  * Especialidade escolhida
  * Data da consulta
  * Horário da consulta
- Se FALTAR alguma informação, NÃO confirme. Diga "Ainda preciso de [informação faltante]"
- Se tiver TODAS as informações, faça um resumo claro e pergunte UMA VEZ APENAS: "Deseja confirmar o agendamento?"
- NÃO repita a mesma pergunta de confirmação se o usuário já respondeu "sim" ou "confirmado"
- Após a primeira confirmação positiva, agradeça e informe próximos passos
- **NUNCA pergunte confirmação duas vezes seguidas**
""",
```

**Benefícios**:
- ✅ Instrui explicitamente a NÃO repetir confirmações
- ✅ Deixa claro que só deve confirmar quando tiver TODAS as informações
- ✅ Orienta a verificar a seção "INFORMAÇÕES JÁ COLETADAS"

---

## 🧪 Como Testar

### Teste 1: Verificar que "None" não aparece mais

```bash
# Iniciar conversa sem dar nome logo de cara
Usuário: "Quero agendar uma consulta de pneumologia"
Bot: [deve pedir o nome, não mostrar "Olá, None!"]
```

### Teste 2: Verificar que não há confirmação duplicada

```bash
# Seguir o fluxo completo
Usuário: "Quero marcar consulta"
Bot: "Qual seu nome?"
Usuário: "João Silva"
Bot: "Qual especialidade?"
Usuário: "Pneumologia"
Bot: "Qual médico?"
Usuário: "Dr. Gustavo"
Bot: "Qual data?"
Usuário: "15 de maio"
Bot: "Qual horário?"
Usuário: "10:00"
Bot: "Deseja confirmar o agendamento...?" [PRIMEIRA VEZ]
Usuário: "sim"
Bot: [NÃO deve perguntar novamente, deve gerar handoff]
```

---

## 📊 Impacto das Correções

### Antes:
- ❌ Nome exibido como "None"
- ❌ Confirmação solicitada múltiplas vezes
- ❌ Experiência frustrante para o usuário
- ❌ Perda de confiança no chatbot

### Depois:
- ✅ Nome sempre tem fallback ("Paciente")
- ✅ Confirmação solicitada UMA ÚNICA VEZ
- ✅ Fluxo mais limpo e profissional
- ✅ Melhor experiência do usuário

---

## 📝 Arquivos Modificados

1. **`api_gateway/services/gemini_chatbot_service.py`**:
   - Linha 1296: Tratamento de `None` em `patient_name`
   - Linhas 155-176: Verificação de estado para evitar duplicação
   - Linhas 537, 551: Melhorias nas instruções do prompt

---

## 🔄 Próximos Passos

1. **Testes Extensivos**: Realizar testes com diferentes fluxos de conversa
2. **Monitoramento**: Observar logs para confirmar que não há mais duplicações
3. **Feedback**: Coletar feedback dos usuários sobre a experiência

---

## 🔧 Correção 3: Contexto Incompleto no Intent Detector (16/10/2025)

### Problema Identificado

Durante a análise do código, foi identificado que o prompt do `intent_detector.py` estava **incompleto** - apenas incluía `selected_doctor` e `patient_name`, mas faltavam campos importantes da sessão:

- `selected_specialty` (especialidade escolhida)
- `preferred_date` (data preferida) 
- `preferred_time` (horário preferido)
- `insurance_type` (tipo de convênio)

### Impacto do Problema

O Gemini não recebia contexto completo da sessão, resultando em:
- Perguntas repetidas sobre informações já coletadas
- Falha em entender referências como "na data que falei"
- Não detectar correções de informações anteriores
- Análise de intenções menos precisa

### Solução Implementada

**Arquivo**: `api_gateway/services/gemini/intent_detector.py`

**Antes** (contexto incompleto):
```python
# Apenas 2 campos no prompt
current_state = session.get('current_state', 'idle')
patient_name = session.get('patient_name' or 'Nome do paciente não informado')
selected_doctor = session.get('selected_doctor' or 'Médico não selecionado')

# No prompt:
CONTEXTO ATUAL:
- Estado da conversa: {current_state}
- Nome do paciente: {patient_name or 'Não informado'}
- Médico selecionado: {selected_doctor or 'Não selecionado'}
```

**Depois** (contexto completo):
```python
# Todos os campos importantes
current_state = session.get('current_state', 'idle')
patient_name = session.get('patient_name')
selected_doctor = session.get('selected_doctor')
selected_specialty = session.get('selected_specialty')  # ✅ ADICIONADO
preferred_date = session.get('preferred_date')          # ✅ ADICIONADO
preferred_time = session.get('preferred_time')          # ✅ ADICIONADO
insurance_type = session.get('insurance_type')          # ✅ ADICIONADO

# No prompt:
CONTEXTO ATUAL:
- Estado da conversa: {current_state}
- Nome do paciente: {patient_name or 'Não informado'}
- Médico selecionado: {selected_doctor or 'Não selecionado'}
- Especialidade escolhida: {selected_specialty or 'Não selecionada'}  # ✅ NOVO
- Data preferida: {preferred_date or 'Não informada'}                  # ✅ NOVO
- Horário preferido: {preferred_time or 'Não informado'}               # ✅ NOVO
- Tipo de convênio: {insurance_type or 'Não informado'}                # ✅ NOVO
```

**Instruções melhoradas**:
```python
IMPORTANTE: 
- Se a mensagem contém informações como nome do paciente, médico, especialidade, data ou horário, EXTRAIA essas informações mesmo que já estejam na sessão anterior. O paciente pode estar corrigindo ou confirmando dados.
- Use o CONTEXTO ATUAL para entender referências como "na data que falei", "o médico que escolhi", "mudar o horário", etc.
- Se o paciente mencionar "mudar", "alterar", "corrigir", considere que está modificando informações já coletadas.
```

### Benefícios

- ✅ **Contexto completo**: Gemini tem visão total da sessão
- ✅ **Melhor detecção**: Entende referências e correções
- ✅ **Menos repetições**: Não pergunta dados já coletados
- ✅ **Análise mais precisa**: Intent detection mais inteligente

### Arquivos Modificados

- `api_gateway/services/gemini/intent_detector.py`:
  - Linhas 118-124: Adicionados todos os campos da sessão
  - Linhas 139-146: Prompt com contexto completo
  - Linhas 184-187: Instruções melhoradas para usar contexto

---

## 📚 Documentação Relacionada

- [Gestão de Memória e Tokens](./GESTAO_MEMORIA_TOKENS_ATUALIZADA.md)
- [Correção de Repetição de Perguntas](./CORRECAO_REPETICAO_PERGUNTAS.md)
- [Sistema de Dúvidas Pausar/Retomar](./SISTEMA_DUVIDAS_PAUSAR_RETOMAR.md)
- [Análise de Estados de Conversação](./ANALISE_ESTADOS_CONVERSACAO.md)

---

**Data**: 16 de outubro de 2025  
**Status**: ✅ Correções Implementadas e Testadas

