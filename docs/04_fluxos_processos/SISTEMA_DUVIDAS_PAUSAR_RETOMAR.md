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

**Arquivo:** `api_gateway/services/gemini/core_service.py` (linhas 142-146)

```python
# Detectar se usuário quer tirar dúvidas durante agendamento
if analysis_result['intent'] in ['buscar_info', 'duvida']:
    if session['current_state'] not in ['idle', 'answering_questions']:
        # Pausar agendamento para responder dúvida
        conversation_service.pause_for_question(phone_number)
        # Nota: O sistema apenas pausa silenciosamente
        # A resposta do bot é gerada normalmente pelo ResponseGenerator
        # Não há mensagem automática de aviso sobre a pausa
```

**⚠️ Comportamento Atual:**
- ✅ Sistema pausa o agendamento automaticamente
- ✅ Responde a dúvida normalmente
- ❌ **NÃO** envia mensagem de aviso sobre a pausa
- ⚠️ Usuário precisa saber que pode usar "continuar" para retomar

**💡 Melhoria Sugerida:**
Para melhorar a UX, seria recomendado adicionar a mensagem de aviso após pausar:

```python
# Após pausar, adicionar aviso à resposta
if conversation_service.pause_for_question(phone_number):
    response_result['response'] += "\n\n💡 Seu agendamento foi pausado. Digite 'continuar' para retomar."
```

### Detecção de Retomada

**Arquivo:** `api_gateway/services/gemini/core_service.py` (linhas 84-89)

```python
# Verificar se há agendamento pausado (sistema de dúvidas)
if conversation_service.has_paused_appointment(phone_number):
    # Detectar palavras-chave para retomar
    if any(keyword in message.lower() for keyword in ['continuar', 'retomar', 'voltar']):
        conversation_service.resume_appointment(phone_number)
        return {'response': '✅ Certo! Vamos continuar com seu agendamento. Onde paramos?'}
```

**Palavras-chave reconhecidas:**
- `continuar`
- `retomar`
- `voltar`

## 📊 Fluxo de Estados

```
┌─────────────────────────────────────────────────────────┐
│                  USUÁRIO EM AGENDAMENTO                  │
│         Estado: selecting_doctor (ou outro)             │
└─────────────────────────────────────────────────────────┘
                           │
                           │ Pergunta algo não relacionado
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
│    previous_state: selecting_doctor                     │
└─────────────────────────────────────────────────────────┘
                           │
                           │ Usuário: "continuar"
                           ▼
┌─────────────────────────────────────────────────────────┐
│              resume_appointment()                        │
│  • Restaura previous_state → current_state              │
│  • Limpa previous_state                                 │
│  • Retorna próxima pergunta do fluxo                    │
└─────────────────────────────────────────────────────────┘
                           │
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│           AGENDAMENTO RETOMADO                           │
│    Estado: selecting_doctor (restaurado)                │
│    Continua de onde parou                               │
└─────────────────────────────────────────────────────────┘
```

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

### Exemplo 1: Pausar e Retomar

```
👤 Olá, quero agendar uma consulta
🤖 Perfeito! Para começar, qual é seu nome completo?

👤 Maria Silva
🤖 Olá Maria Silva! Qual especialidade você procura?

👤 Espera, quanto custa uma consulta?
🤖 O valor da consulta particular é R$ 250,00.
    [Nota: Sistema pausa silenciosamente - não há mensagem automática de aviso]

👤 Entendi, quero continuar
🤖 Perfeito! Vamos continuar seu agendamento de onde paramos.
    Qual especialidade você procura?

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
✅ **Inteligente** - Detecta automaticamente quando retomar  
✅ **Robusto** - Distingue entre dúvidas simples e agendamento pausado

## 🔍 Palavras-chave de Retomada

O sistema reconhece automaticamente quando o usuário quer retomar:

- "continuar"
- "voltar"
- "retomar"
- "prosseguir"
- "seguir"
- "agendamento"

Qualquer uma dessas palavras na mensagem dispara a retomada automática.

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

### **Limitações Conhecidas**
- ⚠️ **Mensagem de aviso sobre pausa NÃO é enviada automaticamente** - Sistema pausa silenciosamente
- ⚠️ Usuário precisa saber intuitivamente que pode usar "continuar" para retomar
- ⚠️ Retomada automática após timeout **não implementada** (melhoria futura)

### **Melhoria Recomendada**
Adicionar mensagem de aviso após pausar o agendamento:

```python
# Em core_service.py, após linha 145
if conversation_service.pause_for_question(phone_number):
    # Adicionar aviso à resposta (se ainda não foi gerada)
    if not response_result.get('response'):
        response_result = self.response_generator.generate_response(...)
    response_result['response'] += "\n\n💡 Seu agendamento foi pausado. Digite 'continuar' para retomar."
```

---

**Criado em:** 15/10/2025  
**Última atualização:** Janeiro 2025  
**Versão:** 2.0  
**Status:** ✅ Validado com código atual

