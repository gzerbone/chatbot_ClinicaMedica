# 💡 Sistema de Pausar/Retomar Agendamento para Dúvidas

## 📋 Visão Geral

O chatbot agora possui um sistema inteligente que permite ao usuário tirar dúvidas a qualquer momento, incluindo durante o processo de agendamento. O sistema salva o progresso e permite retomar de onde parou.

## 🎯 Funcionalidades

### 1. **Três Cenários de Uso**

#### Cenário A: Apenas Tirar Dúvidas
```
Usuário → "Quais convênios vocês aceitam?"
Bot → Responde sobre convênios
Usuário → "Qual o horário de funcionamento?"
Bot → Responde sobre horários
Usuário → "Obrigado!"
```

#### Cenário B: Dúvidas Antes do Agendamento
```
Usuário → "Quanto custa uma consulta?"
Bot → Responde sobre valores
Usuário → "Quero agendar uma consulta"
Bot → Inicia fluxo de agendamento
```

#### Cenário C: Pausar Agendamento para Dúvidas
```
[Usuário está no meio do agendamento]
Usuário → "Momento, quanto custa?"
Bot → ⏸️ Pausa agendamento e responde
Usuário → "Entendi, quero continuar"
Bot → ▶️ Retoma agendamento de onde parou
```

## 🔧 Implementação Técnica

### Novo Campo no Modelo

```python
class ConversationSession(models.Model):
    # ... campos existentes ...
    
    current_state = models.CharField(
        max_length=50,
        choices=[
            # ... outros estados ...
            ('answering_questions', 'Respondendo Dúvidas'),
        ]
    )
    
    previous_state = models.CharField(
        max_length=50, 
        blank=True, 
        null=True,
        help_text="Estado anterior antes de pausar para dúvidas"
    )
```

### Funções Principais

#### 1. `pause_for_question(phone_number)`
Pausa o fluxo de agendamento para responder dúvidas.

```python
conversation_service.pause_for_question(phone_number)
# Salva o estado atual em previous_state
# Muda current_state para 'answering_questions'
```

**Comportamento:**
- ✅ Salva o estado atual (ex: `selecting_doctor`)
- ✅ Muda para estado `answering_questions`
- ✅ Preserva todas as informações já coletadas
- ✅ Retorna `True` se pausou com sucesso

#### 2. `resume_appointment(phone_number)`
Retoma o agendamento de onde parou.

```python
resume_result = conversation_service.resume_appointment(phone_number)
# Retorna:
{
    'resumed': True,
    'restored_state': 'selecting_doctor',
    'next_question': 'Qual médico você prefere?',
    'message': 'Perfeito! Vamos continuar...'
}
```

**Comportamento:**
- ✅ Restaura o estado anterior
- ✅ Limpa `previous_state`
- ✅ Retorna a próxima pergunta do fluxo
- ✅ Fornece mensagem de retomada

#### 3. `is_in_question_mode(phone_number)`
Verifica se o usuário está no modo de dúvidas.

```python
is_questioning = conversation_service.is_in_question_mode(phone_number)
# Retorna: True ou False
```

#### 4. `has_paused_appointment(phone_number)`
Verifica se há um agendamento pausado.

```python
has_paused = conversation_service.has_paused_appointment(phone_number)
# Retorna: True se tem agendamento pausado
#          False se está apenas tirando dúvidas
```

## 🔄 Integração com Gemini

### Detecção Automática de Dúvidas

**Arquivo:** `api_gateway/services/gemini/core_service.py` (linhas 142-165)

```python
# Detectar se usuário quer tirar dúvidas durante agendamento
if analysis_result['intent'] in ['buscar_info', 'duvida']:
    if session['current_state'] not in ['idle', 'answering_questions']:
        # IMPORTANTE: Salvar o estado anterior ANTES de pausar
        # (porque pause_for_question já muda o current_state no banco)
        previous_state_before_pause = session['current_state']
        
        # Pausar agendamento para responder dúvida
        paused = conversation_service.pause_for_question(phone_number)
        if paused:
            # Atualizar variável session em memória para refletir a mudança
            session['previous_state'] = previous_state_before_pause
            session['current_state'] = 'answering_questions'
```

**Comportamento:**
- ✅ Sistema pausa o agendamento automaticamente quando detecta dúvida
- ✅ Salva o estado anterior corretamente antes de pausar
- ✅ Responde a dúvida normalmente
- ✅ Preserva todas as informações já coletadas

### Retomada Automática Inteligente

**Arquivo:** `api_gateway/services/gemini/core_service.py` (linhas 843-879)

O sistema possui uma **retomada automática inteligente** que detecta quando o usuário fornece informações de agendamento durante o estado `answering_questions`, mesmo que a intenção seja `buscar_info` ou `duvida`.

```python
# 10.5. Retomar automaticamente se usuário fornecer informações de agendamento
# IMPORTANTE: Isso é feito DEPOIS da geração da resposta para garantir 
# que dúvidas sejam respondidas primeiro
if session.get('current_state') == 'answering_questions' and session.get('previous_state'):
    entities = analysis_result.get('entities', {})
    
    # Verificar se há entidades NOVAS de agendamento sendo fornecidas
    has_new_appointment_entities = any([
        entities.get('medico') and entities.get('medico') != session.get('selected_doctor'),
        entities.get('especialidade') and entities.get('especialidade') != session.get('selected_specialty'),
        entities.get('data'),
        entities.get('horario')
    ])
    
    intent = analysis_result.get('intent', '')
    
    # LÓGICA DE RETOMADA:
    # 1. Se há entidades NOVAS de agendamento (data, horário, médico, especialidade), 
    #    retomar SEMPRE, mesmo que a intenção seja buscar_info ou duvida
    #    (porque o usuário está fornecendo informações, não apenas perguntando)
    # 2. Se a intenção é explicitamente de agendamento, retomar
    # 3. NÃO retomar se é apenas uma pergunta sem entidades de agendamento
    should_resume = False
    
    if has_new_appointment_entities:
        # Se há entidades de agendamento, retomar independente da intenção
        should_resume = True
    elif intent in ['agendar_consulta', 'confirmar_agendamento', 'selecionar_especialidade', 'confirming_name']:
        # Se a intenção é explicitamente de agendamento, retomar
        should_resume = True
    
    if should_resume:
        restored_state = session.get('previous_state')
        session['current_state'] = restored_state
        session['previous_state'] = None
        # Atualizar no banco também
        db_session = conversation_service.get_or_create_session(phone_number)
        db_session.current_state = restored_state
        db_session.previous_state = None
        db_session.save()
```

**Lógica de Retomada Automática:**
- ✅ **Retoma automaticamente** quando o usuário fornece informações de agendamento (data, horário, médico, especialidade)
- ✅ Funciona **mesmo que a intenção seja `buscar_info` ou `duvida`** (porque o usuário está fornecendo informações, não apenas perguntando)
- ✅ **NÃO retoma** se é apenas uma pergunta sem entidades de agendamento
- ✅ A retomada acontece **DEPOIS da geração da resposta**, garantindo que dúvidas sejam respondidas primeiro
- ✅ O fluxo continua **naturalmente**, sem exigir que o usuário diga "continuar"

**Exemplo de Retomada Automática:**
```
👤 Usuário: "Quanto custa uma consulta?"
🤖 Bot: "O valor da consulta particular é R$ 250,00."
     [Estado: answering_questions, previous_state: selecting_specialty]

👤 Usuário: "Pneumologia"  ← Forneceu especialidade (entidade de agendamento)
🤖 Bot: [Responde sobre Pneumologia e continua automaticamente]
     [Estado: selecting_doctor] ← Retomado automaticamente!
```

### Retomada Manual (Palavras-chave)

O sistema também reconhece palavras-chave para retomada manual quando o usuário não fornece informações de agendamento:

**Palavras-chave reconhecidas:**
- `continuar`
- `retomar`
- `voltar`
- `prosseguir`
- `seguir`
- `agendamento`

## 📊 Fluxo de Estados

### Fluxo Completo com Retomada Automática

```
┌─────────────────────────────────────────────────────────┐
│                  USUÁRIO EM AGENDAMENTO                  │
│         Estado: selecting_specialty (ou outro)          │
└─────────────────────────────────────────────────────────┘
                           │
                           │ Pergunta algo não relacionado
                           │ (intent: buscar_info ou duvida)
                           ▼
┌─────────────────────────────────────────────────────────┐
│               pause_for_question()                       │
│  • Salva current_state → previous_state                 │
│  • Muda para 'answering_questions'                      │
│  • Preserva todas as informações                        │
└─────────────────────────────────────────────────────────┘
                           │
                           │ Bot responde dúvidas
                           ▼
┌─────────────────────────────────────────────────────────┐
│            USUÁRIO TIRANDO DÚVIDAS                       │
│         Estado: answering_questions                     │
│    previous_state: selecting_specialty                  │
└─────────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┴──────────────────┐
        │                                      │
        │ Fornece informações                  │ Usuário: "continuar"
        │ (especialidade, médico,              │ ou palavras-chave
        │  data, horário)                       │
        ▼                                      ▼
┌───────────────────────────────┐  ┌───────────────────────────────┐
│   RETOMADA AUTOMÁTICA         │  │   RETOMADA MANUAL              │
│   (Detecta entidades)         │  │   (Palavras-chave)             │
│                               │  │                               │
│   • Detecta entidades de     │  │   • Detecta palavras-chave     │
│     agendamento               │  │   • Chama resume_appointment()│
│   • Retoma automaticamente   │  │   • Retorna próxima pergunta   │
│   • Fluxo continua fluido     │  │                                │
└───────────────────────────────┘  └───────────────────────────────┘
        │                                      │
        └──────────────────┬──────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│           AGENDAMENTO RETOMADO                           │
│    Estado: selecting_specialty (restaurado)             │
│    Continua de onde parou                               │
│    Fluxo natural e fluido                               │
└─────────────────────────────────────────────────────────┘
```

### Comparação: Retomada Automática vs Manual

| Situação | Comportamento | Exemplo |
|----------|---------------|---------|
| **Usuário fornece informações** | Retoma automaticamente | "Pneumologia" → retoma para `selecting_doctor` |
| **Usuário apenas pergunta** | Permanece em `answering_questions` | "Qual o preço?" → continua respondendo |
| **Usuário diz "continuar"** | Retoma manualmente | "continuar" → retoma para estado anterior |

## 🧪 Testando o Sistema

Execute o script de teste:

```bash
python scripts/test_question_flow.py
```

O teste cobre todos os cenários:
1. ✅ Iniciar agendamento
2. ✅ Pausar para tirar dúvida
3. ✅ Responder dúvida
4. ✅ Retomar agendamento
5. ✅ Completar agendamento
6. ✅ Apenas tirar dúvidas (sem agendamento)

## 📝 Exemplo de Conversa Real

### Exemplo 1: Pausar e Retomar com Retomada Automática

```
👤 Olá, quero agendar uma consulta
🤖 Perfeito! Para começar, qual é seu nome completo?

👤 Maria Silva
🤖 Olá Maria Silva! Qual especialidade você procura?

👤 Espera, quanto custa uma consulta?
🤖 O valor da consulta particular é R$ 250,00.
    [Estado: answering_questions, previous_state: selecting_specialty]

👤 Pneumologia  ← Forneceu especialidade (entidade de agendamento)
🤖 Com a especialidade de Pneumologia escolhida, temos o Dr. Gustavo Magno...
    [Estado: selecting_doctor] ← RETOMADO AUTOMATICAMENTE!
    [Nota: Sistema detectou entidade "especialidade" e retomou automaticamente]

👤 Dr. Gustavo
🤖 Com o Dr. Gustavo Magno selecionado, em qual data e horário você gostaria de agendar?
    [Estado: choosing_schedule]
```

### Exemplo 2: Pausar e Retomar Manualmente

```
👤 Olá, quero agendar uma consulta
🤖 Perfeito! Para começar, qual é seu nome completo?

👤 Maria Silva
🤖 Olá Maria Silva! Qual especialidade você procura?

👤 Espera, quanto custa uma consulta?
🤖 O valor da consulta particular é R$ 250,00.
    [Estado: answering_questions, previous_state: selecting_specialty]

👤 Vocês aceitam Unimed?
🤖 Sim! Aceitamos os seguintes convênios: Unimed, SulAmérica, Amil...
    [Estado: answering_questions] ← Continua respondendo (sem entidades de agendamento)

👤 Entendi, quero continuar  ← Palavra-chave de retomada
🤖 Perfeito! Vamos continuar seu agendamento de onde paramos.
    Qual especialidade você procura?
    [Estado: selecting_specialty] ← RETOMADO MANUALMENTE!

👤 Cardiologia
🤖 Temos médicos disponíveis em Cardiologia...
```

### Exemplo 2: Apenas Dúvidas

```
👤 Vocês aceitam Unimed?
🤖 Sim! Aceitamos os seguintes convênios: Unimed, SulAmérica, Amil...

👤 E o horário de funcionamento?
🤖 Nosso horário de funcionamento é de segunda a sexta, das 8h às 18h.

👤 Obrigada!
🤖 De nada! Estou à disposição quando precisar.
```

## 🎯 Benefícios

✅ **Flexibilidade** - Usuário pode tirar dúvidas a qualquer momento  
✅ **Não Perde Progresso** - Todas as informações são preservadas  
✅ **Natural** - Fluxo de conversa mais humano e natural  
✅ **Inteligente** - Detecta automaticamente quando retomar baseado em entidades de agendamento  
✅ **Fluido** - Retomada automática quando usuário fornece informações, sem precisar dizer "continuar"  
✅ **Robusto** - Distingue entre dúvidas simples e agendamento pausado  
✅ **Eficiente** - Usuário não precisa ficar dizendo "continuar" a cada etapa após tirar dúvidas

## 🔍 Formas de Retomada

### 1. Retomada Automática (Recomendada)

O sistema retoma **automaticamente** quando detecta que o usuário está fornecendo informações de agendamento:

- ✅ Usuário fornece **especialidade** → retoma para `selecting_doctor`
- ✅ Usuário fornece **médico** → retoma para `choosing_schedule`
- ✅ Usuário fornece **data** → retoma para `choosing_schedule` (se já tem médico)
- ✅ Usuário fornece **horário** → retoma para `confirming` (se já tem data)

**Vantagem:** Fluxo natural e fluido, sem necessidade de palavras-chave.

### 2. Retomada Manual (Palavras-chave)

O sistema também reconhece palavras-chave para retomada manual quando o usuário não fornece informações:

- "continuar"
- "voltar"
- "retomar"
- "prosseguir"
- "seguir"
- "agendamento"

**Uso:** Quando o usuário quer retomar mas não está fornecendo informações de agendamento.

## 📚 Código de Referência

### Uso Básico

```python
from api_gateway.services.conversation_service import conversation_service

phone = "5511999999999"

# Pausar agendamento
conversation_service.pause_for_question(phone)

# Verificar status
if conversation_service.has_paused_appointment(phone):
    print("Há agendamento pausado")

# Retomar
result = conversation_service.resume_appointment(phone)
if result['resumed']:
    print(f"Agendamento retomado: {result['message']}")
```

## 🚀 Melhorias Futuras

- [ ] Adicionar tempo limite para retomada automática (ex: 10 minutos)
- [ ] Permitir múltiplas pausas/retomadas
- [ ] Histórico de pausas para análise
- [ ] Notificação proativa se demorar para retomar

---

---

## 📝 Notas de Implementação

### **Status Atual**
- ✅ Sistema de pausar/retomar **implementado e funcional**
- ✅ Integração com `core_service.py` **completa**
- ✅ Validações **funcionando corretamente**
- ✅ Múltiplas pausas **suportadas** (sistema permite várias dúvidas)
- ✅ **Retomada automática inteligente** implementada e funcional
- ✅ Sistema detecta entidades de agendamento e retoma automaticamente
- ✅ Fluxo fluido sem necessidade de palavras-chave quando usuário fornece informações

### **Comportamento da Retomada Automática**

A retomada automática funciona da seguinte forma:

1. **Durante `answering_questions`**, o sistema verifica se há entidades de agendamento nas mensagens do usuário
2. **Se detectar entidades novas** (especialidade, médico, data, horário), retoma automaticamente
3. **Funciona mesmo com intent `buscar_info` ou `duvida`** (porque o usuário está fornecendo informações)
4. **A retomada acontece DEPOIS da geração da resposta**, garantindo que dúvidas sejam respondidas primeiro
5. **O prompt do Gemini é ajustado** para continuar o agendamento fluidamente quando há entidades de agendamento

### **Exemplo de Fluxo com Retomada Automática**

```
Estado: selecting_specialty
Usuário: "Quanto custa uma consulta?"
→ Sistema pausa: answering_questions (previous_state: selecting_specialty)
→ Sistema responde sobre preço

Usuário: "Pneumologia"  ← Forneceu especialidade
→ Sistema detecta entidade "especialidade"
→ Sistema retoma automaticamente: selecting_doctor
→ Fluxo continua naturalmente, sem precisar dizer "continuar"
```

---

**Criado em:** 15/10/2025  
**Última atualização:** Novembro 2025  
**Versão:** 3.0  
**Status:** ✅ Validado com código atual - Retomada Automática Inteligente Implementada

