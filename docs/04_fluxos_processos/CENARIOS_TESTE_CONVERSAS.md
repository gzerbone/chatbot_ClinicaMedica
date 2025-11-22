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
       
       [Estado: selecting_specialty]
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
       
       [Estado: selecting_specialty]
       [Sessão: patient_name="Maria Silva", name_confirmed=True]

─────────────────────────────────────────────────────────────

👤 USUÁRIO: Espera, quanto custa uma consulta?

🤖 BOT: O valor da consulta particular é R$ 150,00.
       
       [Estado: answering_questions]
       [Previous State: selecting_specialty]
       [Intent: buscar_info]
       [Sessão: previous_state="selecting_specialty"]
       [Nota: Sistema pausa silenciosamente - não há mensagem de aviso automática]

─────────────────────────────────────────────────────────────

👤 USUÁRIO: Vocês aceitam convênio?

🤖 BOT: Sim! Aceitamos os seguintes convênios:
       • Unimed
       • SulAmérica
       • Amil
       
       [Estado: answering_questions]
       [Intent: buscar_info]
       [Nota: Continua respondendo dúvidas - sem entidades de agendamento]

─────────────────────────────────────────────────────────────

OPÇÃO 1: RETOMADA AUTOMÁTICA (Recomendada)
─────────────────────────────────────────────────────────────
👤 USUÁRIO: Pneumologia  ← FORNECEU ESPECIALIDADE (entidade de agendamento)

🤖 BOT: Com a especialidade de Pneumologia escolhida, temos o Dr. Gustavo Magno...
       
       [Estado: selecting_doctor] ← RETOMADO AUTOMATICAMENTE! ✅
       [Previous State: None]
       [Intent: agendar_consulta]
       [Nota: Sistema detectou entidade "especialidade" e retomou automaticamente]

OPÇÃO 2: RETOMADA MANUAL (Palavras-chave)
─────────────────────────────────────────────────────────────
👤 USUÁRIO: Entendi, quero continuar  ← Palavra-chave de retomada

🤖 BOT: ✅ Certo! Vamos continuar com seu agendamento. Onde paramos?
       
       Para continuarmos, qual especialidade você deseja consultar?
       
       [Estado: selecting_specialty]
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
       
       [Estado: selecting_specialty]

─────────────────────────────────────────────────────────────

👤 USUÁRIO: Quero confirmar o agendamento

🤖 BOT: Para prosseguir com o agendamento, preciso de algumas informações adicionais.
       
       Qual especialidade médica você procura?
       
       [Estado: selecting_specialty]
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
       
       Qual dessas especialidades você gostaria de consultar?
       
       [Estado: selecting_specialty]
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

## 🎯 Cenário 8: Múltiplas Dúvidas Durante Agendamento (com Retomada Automática)

### **Descrição**
Usuário faz várias perguntas durante o agendamento. Sistema pausa, responde todas e **retoma automaticamente** quando o usuário fornece informações de agendamento, sem necessidade de dizer "continuar" a cada etapa.

### **Conversa Completa**

```
[... agendamento em andamento, estado: selecting_specialty ...]

👤 USUÁRIO: você aceitam convenio do bradesco?

🤖 BOT: Sim, aceitamos o convênio Bradesco.
       
       Para qual especialidade você gostaria de agendar? Temos disponíveis:
       • Endocrinologia
       • Medicina do Sono
       • Pneumologia
       
       [Estado: answering_questions]
       [Previous State: selecting_specialty]
       [Nota: Sistema pausa silenciosamente para responder dúvida]

─────────────────────────────────────────────────────────────

👤 USUÁRIO: qual a localização da clinica?

🤖 BOT: A Clínica PneumoSono está localizada na Rua Miguel Calmon, 225 - Centro, Itabuna/BA.
       
       Para qual especialidade você gostaria de agendar sua consulta? Temos:
       • Endocrinologia
       • Medicina do Sono
       • Pneumologia
       
       [Estado: answering_questions]
       [Nota: Continua respondendo dúvidas - sem entidades de agendamento]

─────────────────────────────────────────────────────────────

👤 USUÁRIO: pneumologia  ← FORNECEU ESPECIALIDADE (entidade de agendamento)

🤖 BOT: Com a especialidade de Pneumologia escolhida, temos o Dr. Gustavo Magno disponível para consulta.
       Com qual desses médicos você gostaria de agendar?
       
       [Estado: selecting_doctor] ← RETOMADO AUTOMATICAMENTE! ✅
       [Previous State: None]
       [Nota: Sistema detectou entidade "especialidade" e retomou automaticamente]

─────────────────────────────────────────────────────────────

👤 USUÁRIO: dr gustavo  ← FORNECEU MÉDICO (entidade de agendamento)

🤖 BOT: Com o Dr. Gustavo Magno selecionado, em qual data e horário você gostaria de agendar sua consulta? 🗓️⏰
       
       [Estado: choosing_schedule] ← AVANÇOU AUTOMATICAMENTE! ✅
       [Nota: Sistema detectou entidade "médico" e avançou automaticamente]

─────────────────────────────────────────────────────────────

👤 USUÁRIO: 24/11 as 08:00  ← FORNECEU DATA E HORÁRIO (entidades de agendamento)

🤖 BOT: Para confirmar, o agendamento seria para 24 de novembro de 2025 às 08:00 com Dr. Gustavo Magno...
       
       [Estado: choosing_schedule → confirming] ← AVANÇOU AUTOMATICAMENTE! ✅
       [Nota: Sistema detectou entidades "data" e "horário" e avançou automaticamente]

```

### **Validações do Cenário**
- ✅ Sistema permite múltiplas dúvidas durante pausa
- ✅ Mantém estado anterior salvo em `previous_state`
- ✅ **Retoma automaticamente quando usuário fornece informações de agendamento** (especialidade, médico, data, horário)
- ✅ **Fluxo fluido e natural**, sem necessidade de dizer "continuar" a cada etapa
- ✅ Preserva informações já coletadas
- ✅ Funciona mesmo quando a intenção é `buscar_info` ou `duvida` mas há entidades de agendamento

---

## 🎯 Cenário 9: Consulta de Preço e Mudança de Especialidade

### **Descrição**
Usuário pergunta sobre preço de uma especialidade (Endocrinologia), mas depois escolhe outra especialidade (Pneumologia) e completa o agendamento. Demonstra a flexibilidade do sistema em lidar com mudanças de escolha e coleta de informações fora da ordem tradicional.

### **Conversa Completa**

```
👤 USUÁRIO: boa tarde, gostaria de saber quanto custa a consulta com o endocrinologista?

🤖 BOT: O valor da consulta com o Dr. Gleyton Porto, especialista em Endocrinologia, é de R$ 300,00.

Com qual desses médicos você gostaria de agendar?
• Dr. Gleyton Porto (Endocrinologia)

       [Estado: idle → selecting_doctor]
       [Intent: buscar_info]
       [Entidades: especialidade="Endocrinologia"]
       [Sessão: selected_specialty="Endocrinologia"]
       [Nota: Sistema extraiu especialidade da pergunta e já salvou na sessão]

─────────────────────────────────────────────────────────────

👤 USUÁRIO: gostaria de uma consulta pneumologica

🤖 BOT: Com qual desses médicos você gostaria de agendar?

*   **Dr. Gustavo Magno** (Medicina do Sono, Pneumologia) - Consulta particular: R$ 350,00

       [Estado: selecting_doctor]
       [Intent: agendar_consulta]
       [Entidades: especialidade="Pneumologia"]
       [Sessão: selected_specialty="Pneumologia"]
       [Nota: Sistema substituiu especialidade anterior pela nova escolha]

─────────────────────────────────────────────────────────────

👤 USUÁRIO: dr gustavo

🤖 BOT: Para agendar sua consulta com o Dr. Gustavo Magno, qual seria a sua data e horário de preferência?

       [Estado: selecting_doctor → choosing_schedule]
       [Intent: agendar_consulta]
       [Entidades: medico="Dr. Gustavo Magno", especialidade="Pneumologia"]
       [Sessão: selected_doctor="Dr. Gustavo Magno", selected_specialty="Pneumologia"]

─────────────────────────────────────────────────────────────

👤 USUÁRIO: segunda as 09

🤖 BOT: Para confirmar, o agendamento seria para 24 de novembro de 2025 às 09:00 com Dr. Gustavo Magno, especialista em Pneumologia. Tudo certo?

       [Estado: choosing_schedule]
       [Intent: agendar_consulta]
       [Entidades: data="segunda", horario="09:00"]
       [Sessão: preferred_date="2025-11-24", preferred_time="09:00:00"]
       [Validação: Horário 09:00 disponível ✅]

─────────────────────────────────────────────────────────────

👤 USUÁRIO: sim

🤖 BOT: Para agendarmos sua consulta com o Dr. Gustavo Magno na especialidade de Pneumologia para o dia 24 de novembro de 2025 às 09:00, preciso do seu nome completo, por favor.

       [Estado: choosing_schedule → collecting_patient_info]
       [Intent: confirmar_agendamento]
       [Validação: Faltam informações - patient_name]
       [Nota: Sistema detectou que falta nome e solicita antes de gerar handoff]

─────────────────────────────────────────────────────────────

👤 USUÁRIO: joao da silva

🤖 BOT: Entendi. Confirma se seu nome completo é Joao Da Silva? Se estiver correto, responda com 'sim'. Caso contrário, digite novamente seu nome completo.

       [Estado: collecting_patient_info → confirming_name]
       [Intent: confirmar_agendamento]
       [Entidades: nome_paciente="Joao Da Silva"]
       [Sessão: pending_name="Joao Da Silva"]

─────────────────────────────────────────────────────────────

👤 USUÁRIO: sim

🤖 BOT: ✅ *Perfeito! Vamos confirmar seu pré-agendamento:*

📋 *RESUMO:*
👤 Paciente: Joao Da Silva
👨‍⚕️ Médico: Dr. Gustavo Magno
🧠 Especialidade: Pneumologia
📅 Data: 2025-11-24
🕐 Horário: 09:00:00

*📞 Clique no link abaixo para falar diretamente com nossa equipe:*
https://api.whatsapp.com/send?phone=5573988221003&text=Agendamento%20via%20Chatbot%3A%0APaciente%3A%20Joao%20Da%20Silva%0AM%C3%A9dico%3A%20Gustavo%20Magno%0AEspecialidade%3A%20Pneumologia%0AData/Hor%C3%A1rio%3A%202025-11-24%20%C3%A0s%2009%3A00%3A00

       [Estado: confirming_name → confirming]
       [Intent: confirmar_agendamento]
       [Sessão: patient_name="Joao Da Silva", name_confirmed=True]
       [Handoff gerado ✅]
       [Validação: Todas as informações completas - handoff gerado com sucesso]

```

### **Validações do Cenário**
- ✅ Sistema responde pergunta sobre preço corretamente
- ✅ Extrai especialidade da pergunta sobre preço e salva na sessão
- ✅ Permite mudança de especialidade (Endocrinologia → Pneumologia)
- ✅ Substitui especialidade anterior pela nova escolha
- ✅ Coleta informações fora da ordem tradicional (especialidade/médico/data/horário antes do nome)
- ✅ Valida informações antes de gerar handoff
- ✅ Solicita nome quando falta, mesmo após confirmar agendamento
- ✅ Confirma nome antes de gerar handoff final
- ✅ Handoff gerado com todas as informações corretas
- ✅ Estados transicionam corretamente: idle → selecting_doctor → choosing_schedule → collecting_patient_info → confirming_name → confirming

### **Pontos de Destaque**
1. **Flexibilidade na Ordem de Coleta**: O sistema permite que o usuário forneça informações em ordem diferente da tradicional (especialidade/médico/data/horário antes do nome).

2. **Mudança de Escolha**: Sistema lida naturalmente com mudança de especialidade, substituindo a anterior pela nova escolha.

3. **Validação Inteligente**: Mesmo após o usuário confirmar o agendamento, o sistema detecta que falta o nome e solicita antes de gerar o handoff.

4. **Extração de Entidades em Perguntas**: Sistema extrai especialidade mesmo quando o usuário apenas pergunta sobre preço, demonstrando capacidade de entender contexto.

---

## 📊 Resumo dos Cenários

| Cenário | Estados Envolvidos | Funcionalidades Testadas |
|---------|-------------------|-------------------------|
| 1. Agendamento Completo | idle → collecting_patient_info → confirming_name → selecting_specialty → selecting_doctor → choosing_schedule → confirming | Fluxo completo, handoff |
| 2. Pausar para Dúvidas | selecting_specialty → answering_questions → selecting_specialty | Pausar, retomar |
| 3. Apenas Dúvidas | idle → answering_questions → idle | Resposta direta, sem agendamento |
| 4. Confirmação Duplicada | confirming → confirming | Prevenção handoff duplicado |
| 5. Informações Faltantes | selecting_specialty → selecting_doctor | Validação, solicitação sequencial |
| 6. Confirmação por Pronome | selecting_doctor → choosing_schedule | Resolução de pronome |
| 7. Especialidade Inválida | selecting_specialty | Validação especialidade |
| 8. Múltiplas Dúvidas | selecting_doctor → answering_questions → selecting_doctor | Múltiplas pausas |
| 9. Consulta de Preço e Mudança de Especialidade | idle → selecting_doctor → choosing_schedule → collecting_patient_info → confirming_name → confirming | Mudança de escolha, coleta fora de ordem, validação inteligente |

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

**Última Atualização:** Novembro 2025  
**Versão:** 1.1

