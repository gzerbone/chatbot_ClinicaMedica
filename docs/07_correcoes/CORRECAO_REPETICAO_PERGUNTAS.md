# 🔧 Correção: Bot Perguntando Repetidamente Informações Já Coletadas

## 📋 Problema Identificado

O chatbot estava perguntando repetidamente informações que já haviam sido coletadas e armazenadas no banco de dados, como:
- Nome do paciente
- Especialidade médica
- Médico escolhido
- Data da consulta
- Horário da consulta

### Exemplo do Problema

```
Bot: "Qual seu nome?"
Usuário: "Gabriela Zerbone"
Bot: "Qual especialidade?"
Usuário: "Pneumologia"
Bot: "Qual médico?"
Usuário: "Dr. Gustavo"
Bot: "Qual a data?" ❌ (Já foi informada anteriormente)
Usuário: "21/10 às 08:00"
Bot: "Qual a data você gostaria?" ❌ (Pergunta de novo!)
```

## 🔍 Causa Raiz do Problema

### 1. Cache Expirando e Não Recarregando do Banco

A função `_get_or_create_session()` criava uma sessão vazia quando o cache expirava, **sem buscar os dados do banco de dados**.

#### ❌ Código Anterior

```python
def _get_or_create_session(self, phone_number: str) -> Dict[str, Any]:
    cache_key = f"gemini_session_{phone_number}"
    session = cache.get(cache_key)
    
    if not session:
        # ❌ Criava sessão vazia sem carregar do banco
        session = {
            'phone_number': phone_number,
            'current_state': 'idle',
            'patient_name': None,  # ❌ Perdido!
            'selected_doctor': None,  # ❌ Perdido!
            # ...
        }
        cache.set(cache_key, session, timeout)
    
    return session
```

### 2. Campo `selected_specialty` Não Sendo Sincronizado

O campo `selected_specialty` existia no banco mas não estava sendo:
- Carregado para o cache
- Atualizado quando extraído
- Verificado nas validações

### 3. Prompt Não Informava Dados Já Coletados

O prompt do Gemini não recebia informações sobre quais dados já haviam sido coletados, fazendo com que o bot perguntasse tudo de novo.

### 4. Contexto Incompleto no Intent Detector

**Problema Identificado**: O prompt do `intent_detector.py` estava **incompleto** - apenas incluía `selected_doctor` e `patient_name`, mas faltavam campos importantes como:
- `selected_specialty` (especialidade escolhida)
- `preferred_date` (data preferida) 
- `preferred_time` (horário preferido)
- `insurance_type` (tipo de convênio)

**Impacto**: O Gemini não sabia que o usuário já havia escolhido uma especialidade, data ou horário, então:
- Perguntava novamente informações já coletadas
- Não entendia referências como "na data que falei"
- Não detectava correções de informações anteriores
- Análise de intenções menos precisa

---

## ✅ Soluções Implementadas

### Solução 1: Carregar Dados do Banco ao Criar Sessão

Agora a função `_get_or_create_session()` **sempre verifica o banco** antes de criar uma sessão vazia.

#### ✅ Código Corrigido

```python
def _get_or_create_session(self, phone_number: str) -> Dict[str, Any]:
    cache_key = f"gemini_session_{phone_number}"
    session = cache.get(cache_key)
    
    if not session:
        # ✅ Tenta carregar do banco primeiro
        try:
            from api_gateway.models import ConversationSession
            db_session = ConversationSession.objects.filter(
                phone_number=phone_number
            ).first()
            
            if db_session:
                # ✅ Carrega todos os dados do banco
                session = {
                    'phone_number': phone_number,
                    'current_state': db_session.current_state,
                    'patient_name': db_session.patient_name,  # ✅ Recuperado!
                    'selected_doctor': db_session.selected_doctor,  # ✅ Recuperado!
                    'selected_specialty': db_session.selected_specialty,  # ✅ Recuperado!
                    'preferred_date': db_session.preferred_date.isoformat() if db_session.preferred_date else None,
                    'preferred_time': db_session.preferred_time.isoformat() if db_session.preferred_time else None,
                    'insurance_type': db_session.insurance_type,
                    'created_at': db_session.created_at.isoformat(),
                    'last_activity': timezone.now().isoformat()
                }
                logger.info(f"📥 Sessão carregada do banco - Nome: {db_session.patient_name}")
            else:
                # Só cria vazia se realmente não existir no banco
                session = { ... }
                logger.info(f"🆕 Nova sessão criada")
        except Exception as e:
            logger.error(f"Erro ao carregar sessão: {e}")
            session = { ... }  # Fallback
        
        cache.set(cache_key, session, timeout)
    
    return session
```

**Benefícios:**
- ✅ Dados nunca são perdidos
- ✅ Cache funciona como otimização, não como fonte única
- ✅ Sessão persiste entre reinicializações
- ✅ Informações coletadas são sempre recuperadas

### Solução 2: Atualizar `selected_specialty` na Sessão

Adicionado código para atualizar a especialidade escolhida:

```python
# Atualizar especialidade selecionada
if entities.get('especialidade') and entities['especialidade'] != 'null':
    session['selected_specialty'] = entities['especialidade']
    logger.info(f"✅ Especialidade atualizada: {entities['especialidade']}")
```

### Solução 3: Validação Melhorada de Informações Faltantes

Agora a validação considera **tanto as entidades extraídas quanto a sessão salva**:

```python
# Verificar cada informação obrigatória  
missing_info = []
for info_key, info_config in required_info.items():
    entity_value = entities.get(info_config['entity_key'])
    session_value = session.get(info_config['session_key'])
    
    # ✅ Considerar informação presente se:
    # 1. Está nas entidades extraídas OU
    # 2. Está salva na sessão (do banco ou cache)
    has_info = bool(entity_value or session_value)
    
    if not has_info:
        missing_info.append(info_key)
        logger.info(f"❌ Informação faltante: {info_key}")
    else:
        logger.info(f"✅ Informação presente: {info_key} = {entity_value or session_value}")
```

### Solução 4: Prompt Melhorado com Informações Coletadas

O prompt do Gemini agora recebe **explicitamente** quais informações já foram coletadas:

### Solução 5: Contexto Completo no Intent Detector

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

**Benefícios**:
- ✅ **Contexto completo**: Gemini tem visão total da sessão
- ✅ **Melhor detecção**: Entende referências e correções
- ✅ **Menos repetições**: Não pergunta dados já coletados
- ✅ **Análise mais precisa**: Intent detection mais inteligente

```python
# Criar lista de informações já coletadas
collected_info = []
if patient_name:
    collected_info.append(f"✅ Nome do paciente: {patient_name}")
if selected_specialty:
    collected_info.append(f"✅ Especialidade escolhida: {selected_specialty}")
if selected_doctor:
    collected_info.append(f"✅ Médico escolhido: {selected_doctor}")
if preferred_date:
    collected_info.append(f"✅ Data preferida: {preferred_date}")
if preferred_time:
    collected_info.append(f"✅ Horário preferido: {preferred_time}")

collected_info_str = "\n".join(collected_info) if collected_info else "Nenhuma informação coletada ainda"

prompt = f"""...

INFORMAÇÕES JÁ COLETADAS (NÃO PERGUNTE NOVAMENTE):
{collected_info_str}

...

REGRAS IMPORTANTES:
...
11. **MUITO IMPORTANTE**: NÃO pergunte informações que já foram coletadas (veja seção "INFORMAÇÕES JÁ COLETADAS")
12. Se já tiver nome, especialidade, médico, data e horário, pergunte se o paciente deseja confirmar o agendamento
"""
```

---

## 📊 Resultado Esperado

### Antes (Com Problema)

```
Bot: "Qual seu nome?"
Usuário: "Gabriela Zerbone"
Bot: "Qual especialidade?"
Usuário: "Pneumologia"
Bot: "Qual médico?"
Usuário: "Dr. Gustavo"
Bot: "Qual data?"
Usuário: "21/10 às 08:00"
Bot: "Qual data você gostaria?" ❌ PERGUNTA DE NOVO
Usuário: "21/10" ❌ TEM QUE REPETIR
Bot: "Qual horário?" ❌ JÁ FOI INFORMADO
```

### Depois (Corrigido)

```
Bot: "Qual seu nome?"
Usuário: "Gabriela Zerbone"
Bot: "Qual especialidade?"
Usuário: "Pneumologia"
Bot: "Qual médico?"
Usuário: "Dr. Gustavo"
Bot: "Qual data?"
Usuário: "21/10 às 08:00"
Bot: "Perfeito! Resumindo: ✅ TODAS AS INFORMAÇÕES COLETADAS
     - Nome: Gabriela Zerbone
     - Especialidade: Pneumologia
     - Médico: Dr. Gustavo
     - Data: 21/10/2025
     - Horário: 08:00
     
     Deseja confirmar o agendamento?"
```

---

## 🧪 Como Testar

### Teste 1: Sessão Persistente

```bash
# 1. Inicie uma conversa
Usuário: "Olá"
Bot: "Olá! Qual seu nome?"
Usuário: "João Silva"

# 2. Espere o cache expirar ou reinicie o servidor

# 3. Continue a conversa
Usuário: "Quero agendar uma consulta"
Bot: "Olá João Silva! Qual especialidade?" ✅ LEMBRA DO NOME
```

### Teste 2: Informações Completas

```bash
Usuário: "Olá, sou Maria"
Bot: "Olá Maria! Como posso ajudar?"
Usuário: "Quero consulta de cardiologia"
Bot: "Temos Dr. João. Deseja agendar?"
Usuário: "Sim, dia 20/10 às 14h"
Bot: "Perfeito! Confirma o agendamento com todas as informações?" ✅ NÃO PERGUNTA DE NOVO
```

---

## 📈 Melhorias Implementadas

### Performance
- ✅ Cache funciona como primeira camada
- ✅ Banco como fonte de verdade
- ✅ Menos chamadas ao Gemini (não repete perguntas)

### Experiência do Usuário
- ✅ Não precisa repetir informações
- ✅ Conversa mais natural e fluida
- ✅ Menos frustração

### Confiabilidade
- ✅ Dados nunca são perdidos
- ✅ Sessão persiste corretamente
- ✅ Validação robusta

### Logs Melhorados
- ✅ `📥 Sessão carregada do banco`
- ✅ `🆕 Nova sessão criada`
- ✅ `✅ Informação presente: nome = João Silva`
- ✅ `❌ Informação faltante: data`

---

## 🔍 Monitoramento

### Logs para Verificar

```
# Sessão carregada do banco
📥 Sessão carregada do banco - Nome: Gabriela Zerbone, Médico: Dr. Gustavo

# Nova sessão criada
🆕 Nova sessão criada para 5573999999999

# Informações presentes
✅ Informação presente: nome_paciente = Gabriela Zerbone
✅ Informação presente: medico = Dr. Gustavo
✅ Informação presente: data = 2025-10-21
✅ Informação presente: horario = 08:00:00

# Informações faltantes
❌ Informação faltante: selected_specialty
```

---

## 📝 Checklist de Correções

- ✅ `_get_or_create_session()` carrega do banco
- ✅ `selected_specialty` sendo atualizado
- ✅ Validação considera sessão E entidades
- ✅ Prompt informa dados já coletados
- ✅ Logs melhorados para debug
- ✅ Testes validados
- ✅ Documentação atualizada

---

## 🚀 Próximos Passos

### Recomendações Futuras

1. **Cache Inteligente**
   - Implementar TTL baseado em atividade
   - Cache mais longo para sessões ativas

2. **Validação Proativa**
   - Verificar integridade antes de perguntar
   - Sugerir completar informações faltantes

3. **Confirmação Explícita**
   - Sempre mostrar resumo antes de confirmar
   - Permitir correção de qualquer campo

---

**Data:** 16/10/2025  
**Versão:** 1.0  
**Status:** ✅ Implementado e Testado

