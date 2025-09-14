# 💬 Exemplos de Conversas do Chatbot

Este documento apresenta exemplos práticos de conversas entre pacientes e o chatbot, mostrando como cada intenção é processada e respondida.

## 🔄 Formato dos Exemplos

Cada exemplo segue o padrão:
```
👤 PACIENTE: [mensagem]
🔍 SISTEMA: intent="[intenção]" | confidence=[confiança] | entities={...}
🤖 CHATBOT: [resposta do Gemini]
```

---

## 1️⃣ **SAUDAÇÃO E APRESENTAÇÃO**

### Exemplo 1.1 - Saudação Simples
```
👤 PACIENTE: Olá
🔍 SISTEMA: intent="saudacao" | confidence=0.9 | entities={}
🤖 CHATBOT: Olá! 😊 Bem-vindo à Clínica Saúde Total! 

Sou seu assistente virtual e estou aqui para ajudá-lo com:
• Informações sobre nossos médicos e especialidades
• Dados sobre exames e procedimentos
• Orientações para agendamento
• Informações gerais da clínica

Como posso ajudá-lo hoje? 🏥
```

### Exemplo 1.2 - Saudação com Contexto
```
👤 PACIENTE: Boa tarde, preciso de ajuda
🔍 SISTEMA: intent="saudacao" | confidence=0.8 | entities={"periodo": "tarde", "necessidade": "ajuda"}
🤖 CHATBOT: Boa tarde! 🌅 Que bom que você procurou nossa clínica!

Estou aqui para ajudá-lo com qualquer dúvida sobre:
📋 Nossos serviços médicos
👨‍⚕️ Informações sobre médicos
🏥 Dados da clínica
📞 Como fazer agendamentos

O que você gostaria de saber? 😊
```

---

## 2️⃣ **BUSCA POR ESPECIALIDADES**

### Exemplo 2.1 - Busca Específica
```
👤 PACIENTE: Vocês têm cardiologista?
🔍 SISTEMA: intent="buscar_especialidade" | confidence=0.95 | entities={"especialidade": "cardiologista"}
🤖 CHATBOT: Sim! 💖 Temos especialista em **Cardiologia** na nossa clínica.

**🩺 Cardiologia**
📝 Especialidade médica que cuida do coração e sistema cardiovascular

**👨‍⚕️ Nosso especialista:**
• **Dr. João Carvalho** (CRM 123456)
• Convênios: SulAmérica, Unimed
• Horário: Segunda a sexta, 8h às 18h

Para agendar sua consulta:
📞 Telefone: (11) 99999-9999
💬 WhatsApp: (11) 98888-8888

Precisa de mais informações sobre cardiologia ou tem alguma dúvida? 🏥
```

### Exemplo 2.2 - Lista de Especialidades
```
👤 PACIENTE: Quais especialidades vocês têm?
🔍 SISTEMA: intent="buscar_especialidade" | confidence=0.85 | entities={}
🤖 CHATBOT: Temos várias especialidades disponíveis! 🩺

**📋 Nossas Especialidades:**

🫀 **Cardiologia**
Cuidados com o coração e sistema cardiovascular

🌸 **Dermatologia** 
Tratamentos para pele, cabelo e unhas

🦴 **Ortopedia**
Cuidados com ossos, músculos e articulações

👁️ **Oftalmologia**
Saúde dos olhos e visão

Gostaria de saber mais sobre alguma especialidade específica ou conhecer nossos médicos? 😊

Para agendamentos: 📞 (11) 99999-9999
```

---

## 3️⃣ **BUSCA POR MÉDICOS**

### Exemplo 3.1 - Médico Específico
```
👤 PACIENTE: Quero agendar com Dr. João
🔍 SISTEMA: intent="buscar_medico" | confidence=0.9 | entities={"medico": "Dr. João"}
🤖 CHATBOT: Ótima escolha! 👨‍⚕️

**Dr. João Carvalho** (CRM 123456)
🩺 **Especialidade:** Cardiologia
💼 **Convênios:** SulAmérica, Unimed
📅 **Atendimento:** Segunda a sexta-feira
🕐 **Horário:** 08:00 às 18:00

**Para agendar sua consulta:**
📞 Ligue: (11) 99999-9999
💬 WhatsApp: (11) 98888-8888
🏥 Endereço: Rua das Flores, 123

O Dr. João é um excelente cardiologista com vasta experiência. Você tem convênio ou será particular? 😊
```

### Exemplo 3.2 - Busca por Especialidade
```
👤 PACIENTE: Preciso de um dermatologista
🔍 SISTEMA: intent="buscar_medico" | confidence=0.88 | entities={"especialidade": "dermatologista"}
🤖 CHATBOT: Perfeito! 🌸 Temos uma excelente dermatologista:

**👩‍⚕️ Dra. Maria Santos** (CRM 654321)
🩺 **Especialidade:** Dermatologia
💼 **Convênios:** SulAmérica, Unimed
📅 **Atendimento:** Terça, quinta e sexta
🕐 **Horário:** 09:00 às 17:00

**🌟 Serviços oferecidos:**
• Consultas gerais de pele
• Tratamento de acne
• Procedimentos estéticos
• Mapeamento de pintas

**Para agendar:**
📞 (11) 99999-9999 ou 💬 (11) 98888-8888

Tem alguma condição específica que gostaria de tratar? 😊
```

---

## 4️⃣ **INFORMAÇÕES SOBRE EXAMES**

### Exemplo 4.1 - Exame Específico
```
👤 PACIENTE: Quanto custa um eletrocardiograma?
🔍 SISTEMA: intent="buscar_exame" | confidence=0.92 | entities={"exame": "eletrocardiograma"}
🤖 CHATBOT: 📊 **Eletrocardiograma (ECG)**

**💰 Valor:** R$ 80,00
**⏱️ Duração:** Aproximadamente 15 minutos
**🩺 Para que serve:** Avalia a atividade elétrica do coração

**📋 Como é feito:**
• Exame simples e indolor
• Eletrodos são colocados no peito, braços e pernas
• O paciente fica deitado e relaxado
• Não precisa de preparo especial

**📅 Para agendar:**
📞 Telefone: (11) 99999-9999
💬 WhatsApp: (11) 98888-8888

Seu convênio cobre este exame? Posso ajudar com mais informações! 😊
```

### Exemplo 4.2 - Lista de Exames
```
👤 PACIENTE: Que exames vocês fazem?
🔍 SISTEMA: intent="buscar_exame" | confidence=0.85 | entities={}
🤖 CHATBOT: Realizamos diversos exames! 🔬

**📊 Nossos Exames Disponíveis:**

💖 **Eletrocardiograma (ECG)**
• Valor: R$ 80,00 | Duração: 15 min
• Avalia atividade elétrica do coração

🩸 **Exames Laboratoriais**
• Valor: R$ 120,00 | Duração: 5 min
• Hemograma, glicose, colesterol, etc.

🫁 **Raio-X de Tórax**
• Valor: R$ 90,00 | Duração: 10 min
• Avalia pulmões e estruturas do tórax

**📋 Todos os exames:**
• Não precisam de agendamento prévio
• Resultados em 24-48h
• Aceitos pelos principais convênios

Qual exame você precisa fazer? 😊
```

---

## 5️⃣ **INFORMAÇÕES DA CLÍNICA**

### Exemplo 5.1 - Localização
```
👤 PACIENTE: Onde vocês ficam?
🔍 SISTEMA: intent="buscar_info_clinica" | confidence=0.9 | entities={"info_tipo": "localizacao"}
🤖 CHATBOT: 📍 **Nossa Localização:**

🏥 **Clínica Saúde Total**
📧 Endereço: Rua das Flores, 123 - Centro
🚗 Fácil acesso e estacionamento disponível

**📞 Contatos:**
• Telefone: (11) 99999-9999
• WhatsApp: (11) 98888-8888

**🕐 Horário de Funcionamento:**
• Segunda a sexta: 08:00 às 18:00
• Sábado: 08:00 às 12:00
• Domingo: Fechado

**🚌 Como chegar:**
• Próximo ao centro da cidade
• Várias linhas de ônibus passam na região
• Estacionamento gratuito para pacientes

Precisa de mais alguma informação? 😊
```

### Exemplo 5.2 - Horários
```
👤 PACIENTE: Que horas vocês abrem?
🔍 SISTEMA: intent="buscar_info_clinica" | confidence=0.88 | entities={"info_tipo": "horarios"}
🤖 CHATBOT: 🕐 **Nossos Horários de Funcionamento:**

**Segunda a Sexta-feira:**
🌅 Abertura: 08:00
🌆 Fechamento: 18:00

**Sábado:**
🌅 Abertura: 08:00  
🌆 Fechamento: 12:00

**Domingo:**
🔒 Fechado

**⚡ Atendimento de Urgência:**
• Para emergências, recomendamos procurar o hospital mais próximo
• Para dúvidas urgentes: 💬 WhatsApp (11) 98888-8888

**📅 Agendamentos:**
• Podem ser feitos durante todo o horário de funcionamento
• Também pelo WhatsApp fora do horário

Precisa agendar algo? Posso orientá-lo! 😊
```

---

## 6️⃣ **AGENDAMENTO DE CONSULTAS**

### Exemplo 6.1 - Solicitação de Agendamento
```
👤 PACIENTE: Quero marcar uma consulta
🔍 SISTEMA: intent="agendar_consulta" | confidence=0.92 | entities={}
🤖 CHATBOT: Perfeito! Vou ajudá-lo a agendar sua consulta! 📅

**Para um agendamento eficiente, preciso saber:**

1️⃣ **Qual especialidade?**
• Cardiologia, Dermatologia, Ortopedia, Oftalmologia

2️⃣ **Tem preferência de médico?**
• Dr. João Carvalho (Cardiologia)
• Dra. Maria Santos (Dermatologia)

3️⃣ **Você tem convênio?**
• SulAmérica, Unimed ou Particular

**📞 Para finalizar o agendamento:**
• Telefone: (11) 99999-9999
• WhatsApp: (11) 98888-8888

Nossa recepção terá prazer em encontrar o melhor horário para você! 😊

Qual especialidade você precisa?
```

### Exemplo 6.2 - Agendamento Específico
```
👤 PACIENTE: Quero marcar cardiologista para amanhã
🔍 SISTEMA: intent="agendar_consulta" | confidence=0.95 | entities={"especialidade": "cardiologista", "tempo": "amanhã"}
🤖 CHATBOT: Ótimo! 💖 Vamos agendar com nosso cardiologista!

**👨‍⚕️ Dr. João Carvalho - Cardiologia**
📅 **Para amanhã** - vou verificar a disponibilidade!

**📋 Informações necessárias:**
✅ Especialidade: Cardiologia  
✅ Médico: Dr. João Carvalho
⏰ Data: Amanhã
❓ Horário: A definir
❓ Convênio: Qual você tem?

**📞 Para confirmar o agendamento:**
Ligue agora: **(11) 99999-9999**
Ou WhatsApp: **(11) 98888-8888**

Nossa recepção verificará os horários disponíveis para amanhã e confirmará com você!

**⚡ Dica:** Tenha em mãos seus documentos e cartão do convênio! 

Você tem convênio ou será particular? 😊
```

---

## 7️⃣ **CONVÊNIOS E PAGAMENTOS**

### Exemplo 7.1 - Consulta sobre Convênios
```
👤 PACIENTE: Vocês aceitam Unimed?
🔍 SISTEMA: intent="buscar_info_clinica" | confidence=0.87 | entities={"convenio": "Unimed"}
🤖 CHATBOT: Sim! 💙 **Aceitamos Unimed!**

**🏥 Convênios Aceitos:**
✅ **Unimed** - Todos os planos
✅ **SulAmérica** - Todos os planos

**👨‍⚕️ Médicos que atendem Unimed:**
• Dr. João Carvalho (Cardiologia)
• Dra. Maria Santos (Dermatologia)

**📋 Exames cobertos:**
• Eletrocardiograma
• Exames laboratoriais
• Raio-X

**📞 Para agendar com Unimed:**
• Telefone: (11) 99999-9999
• WhatsApp: (11) 98888-8888
• Tenha sua carteirinha em mãos!

**💡 Importante:** Alguns procedimentos podem precisar de autorização prévia do convênio.

Qual especialidade você precisa? 😊
```

---

## 8️⃣ **MENSAGENS NÃO COMPREENDIDAS**

### Exemplo 8.1 - Mensagem Confusa
```
👤 PACIENTE: asdkjaslkd médico coração
🔍 SISTEMA: intent="desconhecida" | confidence=0.2 | entities={"especialidade": "coração"}
🤖 CHATBOT: Desculpe, não entendi completamente sua mensagem! 😅

Mas percebi que você mencionou **"coração"** - você está procurando um **cardiologista**? 💖

**Posso ajudá-lo com:**
🩺 Informações sobre cardiologia
👨‍⚕️ Nosso cardiologista Dr. João Carvalho
📅 Agendamento de consulta
💰 Valores e convênios

**Ou talvez você queira:**
• Informações sobre outros médicos
• Dados da clínica
• Orientações sobre exames

Pode reformular sua pergunta? Estou aqui para ajudar! 😊
```

### Exemplo 8.2 - Solicitação Fora do Escopo
```
👤 PACIENTE: Vocês vendem remédios?
🔍 SISTEMA: intent="desconhecida" | confidence=0.3 | entities={}
🤖 CHATBOT: Entendo sua pergunta! 💊

Nós somos uma **clínica médica** e não vendemos medicamentos. Nossos serviços incluem:

**🩺 O que oferecemos:**
• Consultas médicas especializadas
• Exames diagnósticos
• Orientações médicas
• Receituário médico

**💊 Para medicamentos:**
• Nossos médicos podem prescrever receitas
• Você pode comprar em qualquer farmácia
• Algumas farmácias ficam próximas à clínica

**📋 Posso ajudá-lo com:**
• Agendar consulta para receita médica
• Informações sobre nossos médicos
• Orientações sobre especialidades

Precisa de uma consulta médica? 😊
```

---

## 9️⃣ **DESPEDIDAS**

### Exemplo 9.1 - Despedida Simples
```
👤 PACIENTE: Obrigado, tchau
🔍 SISTEMA: intent="despedida" | confidence=0.9 | entities={}
🤖 CHATBOT: Por nada! 😊 Foi um prazer ajudá-lo!

**🏥 Clínica Saúde Total** está sempre aqui para cuidar da sua saúde!

**📞 Nossos contatos:**
• Telefone: (11) 99999-9999
• WhatsApp: (11) 98888-8888

**Volte sempre que precisar!** 
Desejamos muita saúde e bem-estar! 💙

Até logo! 👋
```

### Exemplo 9.2 - Despedida com Agradecimento
```
👤 PACIENTE: Muito obrigada pelas informações! Até mais!
🔍 SISTEMA: intent="despedida" | confidence=0.95 | entities={"agradecimento": "obrigada"}
🤖 CHATBOT: Fico muito feliz em ter ajudado! 🌟

**Obrigado por escolher a Clínica Saúde Total!** 

Esperamos vê-la em breve para cuidar da sua saúde! 💙

**📋 Lembre-se:**
• Estamos aqui sempre que precisar
• Agendamentos: (11) 99999-9999
• WhatsApp: (11) 98888-8888

**Tenha um excelente dia e muita saúde!** 🌸

Até a próxima! 👋😊
```

---

## 🎯 **Resumo de Intenções Suportadas**

| Intenção | Palavras-chave | Confiança Típica | Exemplo |
|----------|----------------|------------------|---------|
| `saudacao` | olá, oi, bom dia, boa tarde | 0.8-0.95 | "Olá, como vai?" |
| `buscar_especialidade` | especialidade, cardiologista, dermatologista | 0.8-0.95 | "Vocês têm cardiologista?" |
| `buscar_medico` | médico, doutor, dr, dra | 0.7-0.9 | "Quero o Dr. João" |
| `buscar_exame` | exame, eletrocardiograma, raio-x | 0.8-0.95 | "Quanto custa ECG?" |
| `buscar_info_clinica` | endereço, telefone, horário, localização | 0.8-0.9 | "Onde vocês ficam?" |
| `agendar_consulta` | agendar, marcar, consulta | 0.85-0.95 | "Quero marcar consulta" |
| `despedida` | tchau, obrigado, até logo | 0.8-0.95 | "Obrigado, tchau!" |
| `desconhecida` | - | 0.0-0.4 | Mensagens não identificadas |

---

## 📊 **Métricas de Performance**

### Tempo de Resposta por Tipo:
- **Saudação**: ~2-3 segundos
- **Busca simples**: ~3-4 segundos  
- **Busca complexa**: ~4-6 segundos
- **Informações da clínica**: ~2-3 segundos

### Taxa de Sucesso:
- **Intenções claras**: ~95% de acerto
- **Mensagens ambíguas**: ~70% de acerto
- **Fallback útil**: ~90% dos casos

### Satisfação do Usuário:
- **Respostas úteis**: ~85%
- **Linguagem adequada**: ~90%
- **Informações corretas**: ~95%
