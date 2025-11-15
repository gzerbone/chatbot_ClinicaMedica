# 🧪 Cenários de Teste - Conversas entre Usuário e Chatbot

## 📋 Visão Geral

Este documento contém **cenários completos de conversas** entre usuários e o chatbot para validação e documentação do sistema. Cada cenário demonstra um fluxo específico do chatbot.

---

## 🎯 Cenário 1: Agendamento Completo - Fluxo Ideal

### **Descrição**
Usuário realiza um agendamento completo do início ao fim, seguindo todas as etapas sequencialmente.

### **Conversa Completa**

```
👤 USUÁRIO: Olá, bom dia!

🤖 BOT: Olá! Bom dia! 😊 Sou a assistente virtual da Clínica PneumoSono.
       Como posso ajudá-lo hoje?
       
       [Estado: idle → collecting_patient_info]
       [Intent: saudacao]

─────────────────────────────────────────────────────────────

👤 USUÁRIO: Quero agendar uma consulta

🤖 BOT: Perfeito! Para começar o agendamento, preciso saber seu nome completo.
       Qual é seu nome?
       
       [Estado: collecting_patient_info]
       [Intent: agendar_consulta]

─────────────────────────────────────────────────────────────

👤 USUÁRIO: Meu nome é João Silva Santos

🤖 BOT: Entendi. Confirma se seu nome completo é João Silva Santos?
       Se estiver correto, responda com 'sim'. Caso contrário, digite novamente seu nome completo.
       
       [Estado: confirming_name]
       [Intent: fornecer_nome]
       [Entidades: nome_paciente="João Silva Santos"]
       [Sessão: pending_name="João Silva Santos"]

─────────────────────────────────────────────────────────────

👤 USUÁRIO: Sim

🤖 BOT: Perfeito, João Silva Santos! Para continuarmos, qual especialidade você deseja consultar?
       
       [Estado: collecting_info]
       [Intent: confirmar_nome]
       [Sessão: patient_name="João Silva Santos", name_confirmed=True]

─────────────────────────────────────────────────────────────

👤 USUÁRIO: Pneumologia

🤖 BOT: Perfeito! 🫁 Pneumologia
       
       Agora, com qual médico você gostaria de agendar?
       
       Médicos de Pneumologia:
       • Dr. Gustavo (Medicina do Sono, Pneumologia)
       
       Qual médico você prefere?
       
       [Estado: selecting_doctor]
       [Intent: selecionar_especialidade]
       [Entidades: especialidade="Pneumologia"]
       [Sessão: selected_specialty="Pneumologia"]

─────────────────────────────────────────────────────────────

👤 USUÁRIO: Dr. Gustavo

🤖 BOT: Excelente escolha! 👨‍⚕️
       
       Dr. Gustavo
       🩺 Medicina do Sono, Pneumologia
       💰 Consulta particular: R$ 150,00
       
       📅 Horários disponíveis:
       
       Segunda-feira (14/10/2024):
       ✅ 08:00, 09:00, 10:00, 14:00, 15:00, 16:00
       
       Quarta-feira (16/10/2024):
       ✅ 08:00, 09:00, 14:00
       
       Qual data e horário seria melhor para você?
       
       [Estado: choosing_schedule]
       [Intent: selecionar_medico]
       [Entidades: medico="Dr. Gustavo"]
       [Sessão: selected_doctor="Dr. Gustavo"]

─────────────────────────────────────────────────────────────

👤 USUÁRIO: Segunda-feira às 14h

🤖 BOT: Perfeito! Vamos confirmar seu pré-agendamento:
       
       📋 RESUMO:
       👤 Paciente: João Silva Santos
       👨‍⚕️ Médico: Dr. Gustavo
       📅 Data: Segunda-feira, 14/10/2024
       🕐 Horário: 14:00
       
       Está tudo correto? (Sim/Não)
       
       [Estado: choosing_schedule]
       [Intent: fornecer_data_horario]
       [Entidades: data="Segunda-feira", horario="14h"]
       [Sessão: preferred_date="2024-10-14", preferred_time="14:00"]

─────────────────────────────────────────────────────────────

👤 USUÁRIO: Sim, está correto

🤖 BOT: ✅ Perfeito! Vamos confirmar seu pré-agendamento:
       
       📋 RESUMO:
       👤 Paciente: João Silva Santos
       👨‍⚕️ Médico: Dr. Gustavo
       📅 Data: Segunda-feira, 14/10/2024
       🕐 Horário: 14:00
       
       🔄 Para CONFIRMAR definitivamente:
       👩‍💼 Nossa secretária validará a disponibilidade e confirmará seu agendamento.
       
       📞 Clique no link abaixo para falar diretamente com nossa equipe:
       https://wa.me/5573988221003?text=Ol%C3%A1%2C%20gostaria%20de%20confirmar...
       
       [Estado: confirming]
       [Intent: confirmar_agendamento]
       [Handoff gerado ✅]

```

### **Validações do Cenário**
- ✅ Nome coletado e confirmado
- ✅ Especialidade selecionada
- ✅ Médico escolhido
- ✅ Data e horário informados
- ✅ Handoff gerado com sucesso
- ✅ Estado final: `confirming`

---

## 🎯 Cenário 2: Pausar Agendamento para Dúvidas

### **Descrição**
Usuário está no meio do agendamento e faz uma pergunta. O sistema pausa o agendamento, responde a dúvida e permite retomar.

### **Conversa Completa**

```
👤 USUÁRIO: Olá, quero agendar uma consulta

🤖 BOT: Perfeito! Para começar o agendamento, preciso saber seu nome completo.
       Qual é seu nome?
       
       [Estado: collecting_patient_info]

─────────────────────────────────────────────────────────────

👤 USUÁRIO: Maria Silva

🤖 BOT: Entendi. Confirma se seu nome completo é Maria Silva?
       
       [Estado: confirming_name]
       [Sessão: pending_name="Maria Silva"]

─────────────────────────────────────────────────────────────

👤 USUÁRIO: Sim

🤖 BOT: Perfeito, Maria Silva! Para continuarmos, qual especialidade você deseja consultar?
       
       [Estado: collecting_info]
       [Sessão: patient_name="Maria Silva", name_confirmed=True]

─────────────────────────────────────────────────────────────

👤 USUÁRIO: Espera, quanto custa uma consulta?

🤖 BOT: O valor da consulta particular é R$ 150,00.
       
       [Estado: answering_questions]
       [Previous State: collecting_info]
       [Intent: buscar_info]
       [Sessão: previous_state="collecting_info"]
       [Nota: Sistema pausa silenciosamente - não há mensagem de aviso automática]

─────────────────────────────────────────────────────────────

👤 USUÁRIO: Vocês aceitam convênio?

🤖 BOT: Sim! Aceitamos os seguintes convênios:
       • Unimed
       • SulAmérica
       • Amil
       
       [Estado: answering_questions]
       [Intent: buscar_info]

─────────────────────────────────────────────────────────────

👤 USUÁRIO: Entendi, quero continuar

🤖 BOT: ✅ Certo! Vamos continuar com seu agendamento. Onde paramos?
       
       Para continuarmos, qual especialidade você deseja consultar?
       
       [Estado: collecting_info]
       [Previous State: None]
       [Intent: resume_appointment]
       [Sessão: previous_state=None]

─────────────────────────────────────────────────────────────

👤 USUÁRIO: Cardiologia

🤖 BOT: Perfeito! 🫀 Cardiologia
       
       Agora, com qual médico você gostaria de agendar?
       ...
       
       [Estado: selecting_doctor]
       [Sessão: selected_specialty="Cardiologia"]

```

### **Validações do Cenário**
- ✅ Agendamento pausado quando usuário faz pergunta
- ✅ Estado anterior salvo em `previous_state`
- ✅ Dúvidas respondidas corretamente
- ⚠️ **NÃO há mensagem automática** informando sobre a pausa
- ✅ Retomada do agendamento com "continuar"
- ✅ Estado restaurado corretamente

---

## 🎯 Cenário 3: Apenas Tirar Dúvidas (Sem Agendamento)

### **Descrição**
Usuário apenas quer informações sobre a clínica, sem interesse em agendar.

### **Conversa Completa**

```
👤 USUÁRIO: Olá

🤖 BOT: Olá! Bom dia! 😊 Sou a assistente virtual da Clínica PneumoSono.
       Como posso ajudá-lo hoje?
       
       [Estado: idle → answering_questions]
       [Intent: saudacao]

─────────────────────────────────────────────────────────────

👤 USUÁRIO: Quais convênios vocês aceitam?

🤖 BOT: Aceitamos os seguintes convênios:
       • Unimed
       • SulAmérica
       • Amil
       
       [Estado: answering_questions]
       [Intent: buscar_info]

─────────────────────────────────────────────────────────────

👤 USUÁRIO: Qual o horário de funcionamento?

🤖 BOT: Nosso horário de funcionamento é de segunda a sexta, das 8h às 18h.
       
       [Estado: answering_questions]
       [Intent: buscar_info]

─────────────────────────────────────────────────────────────

👤 USUÁRIO: Obrigada!

🤖 BOT: De nada! Estou à disposição quando precisar. 😊
       
       [Estado: answering_questions → idle]
       [Intent: despedida]

```

### **Validações do Cenário**
- ✅ Sistema não inicia agendamento
- ✅ Responde dúvidas diretamente
- ✅ Estado permanece em `answering_questions` ou volta para `idle`
- ✅ Não solicita informações de agendamento

---

## 🎯 Cenário 4: Confirmação Duplicada (Prevenção de Handoff Duplicado)

### **Descrição**
Usuário confirma o agendamento duas vezes. Sistema deve evitar gerar handoff duplicado.

### **Conversa Completa**

```
[... agendamento completo até confirmação ...]

👤 USUÁRIO: Sim, está correto

🤖 BOT: ✅ Perfeito! Vamos confirmar seu pré-agendamento:
       
       📋 RESUMO:
       👤 Paciente: João Silva Santos
       👨‍⚕️ Médico: Dr. Gustavo
       📅 Data: Segunda-feira, 14/10/2024
       🕐 Horário: 14:00
       
       🔄 Para CONFIRMAR definitivamente:
       👩‍💼 Nossa secretária validará a disponibilidade...
       
       📞 Clique no link abaixo...
       https://wa.me/5573988221003?text=...
       
       [Estado: confirming]
       [Handoff gerado ✅]

─────────────────────────────────────────────────────────────

👤 USUÁRIO: Sim, confirma

🤖 BOT: ✅ Seu agendamento já foi confirmado anteriormente!
       
       📋 Dados do seu agendamento:
       👤 Paciente: João Silva Santos
       🏥 Especialidade: Pneumologia
       👨‍⚕️ Médico: Dr. Gustavo
       📅 Data: 14/10/2024
       ⏰ Horário: 14:00
       
       Nossa secretaria entrará em contato em breve para finalizar seu agendamento.
       
       🔗 Link de confirmação: https://wa.me/5573988221003?text=...
       
       Há algo mais em que posso ajudar? 😊
       
       [Estado: confirming]
       [Handoff NÃO gerado novamente ✅]
       [Mensagem de confirmação duplicada]

```

### **Validações do Cenário**
- ✅ Sistema detecta que já está em `confirming`
- ✅ Não gera handoff duplicado
- ✅ Mostra resumo do agendamento confirmado
- ✅ Inclui link do handoff anterior se disponível

---

## 🎯 Cenário 5: Informações Faltantes - Solicitação Sequencial

### **Descrição**
Usuário tenta confirmar agendamento sem todas as informações. Sistema solicita informações faltantes sequencialmente.

### **Conversa Completa**

```
👤 USUÁRIO: Quero agendar uma consulta

🤖 BOT: Perfeito! Para começar o agendamento, preciso saber seu nome completo.
       Qual é seu nome?
       
       [Estado: collecting_patient_info]

─────────────────────────────────────────────────────────────

👤 USUÁRIO: João Silva

🤖 BOT: Entendi. Confirma se seu nome completo é João Silva?
       
       [Estado: confirming_name]

─────────────────────────────────────────────────────────────

👤 USUÁRIO: Sim

🤖 BOT: Perfeito, João Silva! Para continuarmos, qual especialidade você deseja consultar?
       
       [Estado: collecting_info]

─────────────────────────────────────────────────────────────

👤 USUÁRIO: Quero confirmar o agendamento

🤖 BOT: Para prosseguir com o agendamento, preciso de algumas informações adicionais.
       
       Qual especialidade médica você procura?
       
       [Estado: collecting_info]
       [Intent: confirmar_agendamento]
       [Validação: Faltam especialidade, médico, data, horário]
       [Handoff NÃO gerado ❌]

─────────────────────────────────────────────────────────────

👤 USUÁRIO: Pneumologia

🤖 BOT: Perfeito! 🫁 Pneumologia
       
       Agora, com qual médico você gostaria de agendar?
       ...
       
       [Estado: selecting_doctor]
       [Sessão: selected_specialty="Pneumologia"]

─────────────────────────────────────────────────────────────

👤 USUÁRIO: Confirma

🤖 BOT: Para prosseguir com o agendamento, preciso de algumas informações adicionais.
       
       Com qual médico você gostaria de agendar?
       
       [Estado: selecting_doctor]
       [Validação: Faltam médico, data, horário]
       [Handoff NÃO gerado ❌]

```

### **Validações do Cenário**
- ✅ Sistema valida informações antes de gerar handoff
- ✅ Solicita informações faltantes sequencialmente
- ✅ Não gera handoff incompleto
- ✅ Mantém informações já coletadas

---

## 🎯 Cenário 6: Confirmação por Pronome

### **Descrição**
Usuário confirma médico usando pronome ("ele", "com ele") após o sistema sugerir médicos.

### **Conversa Completa**

```
[... até seleção de especialidade ...]

👤 USUÁRIO: Pneumologia

🤖 BOT: Perfeito! 🫁 Pneumologia
       
       Agora, com qual médico você gostaria de agendar?
       
       Médicos de Pneumologia:
       • Dr. Gustavo (Medicina do Sono, Pneumologia)
       
       Qual médico você prefere?
       
       [Estado: selecting_doctor]
       [Sessão: last_suggested_doctor="Dr. Gustavo"]
       [Sessão: last_suggested_doctors=["Dr. Gustavo"]]

─────────────────────────────────────────────────────────────

👤 USUÁRIO: Com ele

🤖 BOT: Excelente escolha! 👨‍⚕️
       
       Dr. Gustavo
       🩺 Medicina do Sono, Pneumologia
       💰 Consulta particular: R$ 150,00
       
       📅 Horários disponíveis:
       ...
       
       [Estado: choosing_schedule]
       [Intent: selecionar_medico]
       [Entidades: medico="Dr. Gustavo"] (resolvido do contexto)
       [Sessão: selected_doctor="Dr. Gustavo"]

```

### **Validações do Cenário**
- ✅ Sistema resolve pronome "ele" para médico sugerido
- ✅ Usa contexto de médicos sugeridos anteriormente
- ✅ Confirmação funciona corretamente

---

## 🎯 Cenário 7: Especialidade Não Encontrada

### **Descrição**
Usuário menciona especialidade que não existe na clínica. Sistema informa e lista especialidades disponíveis.

### **Conversa Completa**

```
👤 USUÁRIO: Quero agendar com um dermatologista

🤖 BOT: Desculpe, não temos a especialidade "Dermatologia" disponível na clínica.
       
       Nossas especialidades disponíveis são:
       • Medicina do Sono
       • Pneumologia
       • Endocrinologia
       • Cardiologia
       
       Qual dessas especialidades você gostaria de consultar?
       
       [Estado: collecting_info]
       [Intent: agendar_consulta]
       [Validação: Especialidade não encontrada]
       [Lista especialidades disponíveis]

```

### **Validações do Cenário**
- ✅ Sistema valida especialidade contra banco de dados
- ✅ Informa que especialidade não está disponível
- ✅ Lista especialidades disponíveis
- ✅ Permite usuário escolher outra especialidade

---

## 🎯 Cenário 8: Múltiplas Dúvidas Durante Agendamento

### **Descrição**
Usuário faz várias perguntas durante o agendamento. Sistema pausa, responde todas e permite retomar.

### **Conversa Completa**

```
[... agendamento em andamento, estado: selecting_doctor ...]

👤 USUÁRIO: Quanto custa uma consulta?

🤖 BOT: O valor da consulta particular é R$ 150,00.
       
       [Estado: answering_questions]
       [Previous State: selecting_doctor]
       [Nota: Sistema pausa silenciosamente - usuário precisa saber que pode usar "continuar"]

─────────────────────────────────────────────────────────────

👤 USUÁRIO: E vocês aceitam Unimed?

🤖 BOT: Sim! Aceitamos Unimed e outros convênios.
       
       [Estado: answering_questions]

─────────────────────────────────────────────────────────────

👤 USUÁRIO: Qual o horário de funcionamento?

🤖 BOT: Nosso horário de funcionamento é de segunda a sexta, das 8h às 18h.
       
       [Estado: answering_questions]

─────────────────────────────────────────────────────────────

👤 USUÁRIO: Continuar

🤖 BOT: ✅ Certo! Vamos continuar com seu agendamento. Onde paramos?
       
       Com qual médico você gostaria de agendar?
       
       [Estado: selecting_doctor]
       [Previous State: None]
       [Agendamento retomado ✅]

```

### **Validações do Cenário**
- ✅ Sistema permite múltiplas dúvidas durante pausa
- ✅ Mantém estado anterior salvo
- ✅ Retoma corretamente após "continuar"
- ✅ Preserva informações já coletadas

---

## 📊 Resumo dos Cenários

| Cenário | Estados Envolvidos | Funcionalidades Testadas |
|---------|-------------------|-------------------------|
| 1. Agendamento Completo | idle → collecting_patient_info → confirming_name → collecting_info → selecting_doctor → choosing_schedule → confirming | Fluxo completo, handoff |
| 2. Pausar para Dúvidas | collecting_info → answering_questions → collecting_info | Pausar, retomar |
| 3. Apenas Dúvidas | idle → answering_questions → idle | Resposta direta, sem agendamento |
| 4. Confirmação Duplicada | confirming → confirming | Prevenção handoff duplicado |
| 5. Informações Faltantes | collecting_info → selecting_doctor | Validação, solicitação sequencial |
| 6. Confirmação por Pronome | selecting_doctor → choosing_schedule | Resolução de pronome |
| 7. Especialidade Inválida | collecting_info | Validação especialidade |
| 8. Múltiplas Dúvidas | selecting_doctor → answering_questions → selecting_doctor | Múltiplas pausas |

---

## ✅ Checklist de Validação

Para cada cenário, validar:

- [ ] Estados transicionam corretamente
- [ ] Entidades são extraídas corretamente
- [ ] Informações são salvas na sessão
- [ ] Respostas são contextualizadas
- [ ] Handoff é gerado apenas quando completo
- [ ] Sistema de pausar/retomar funciona
- [ ] Validações funcionam corretamente
- [ ] Mensagens são salvas no histórico
- [ ] Cache e banco sincronizam corretamente

---

**Última Atualização:** Janeiro 2025  
**Versão:** 1.0

