# 👩‍💼 Guia da Secretária - Gerenciamento do Google Calendar

Este guia é específico para a **secretária da clínica** que será responsável por manter o calendário atualizado e organizado.

## 🎯 **Responsabilidades da Secretária**

- 📅 **Gerenciar calendário único** da clínica
- ✅ **Criar eventos** para agendamentos
- ❌ **Cancelar eventos** quando necessário  
- 🔄 **Atualizar horários** em tempo real
- 📝 **Manter nomenclatura** consistente
- 🤝 **Coordenar com médicos** sobre disponibilidade

---

## 📋 **Padrão Obrigatório de Eventos**

### **Formato Correto:**
```
[Dr./Dra. Nome Completo] - [Tipo de Atendimento]
```

### **Exemplos Práticos:**

#### **✅ Formatos CORRETOS:**
```
Dr. João Carvalho - Consulta
Dr. João Carvalho - Retorno
Dr. João Carvalho - Consulta Cardiologia
Dra. Maria Santos - Consulta
Dra. Maria Santos - Procedimento Dermatológico
Dr. Pedro Silva - Consulta Ortopedia
Dr. João Carvalho - Primeira Consulta
Dra. Maria Santos - Avaliação
```

#### **❌ Formatos INCORRETOS:**
```
❌ João - Consulta               (sem "Dr.")
❌ Consulta João                 (ordem errada)
❌ Dr João Carvalho - Consulta   (sem ponto)
❌ Paciente Maria Silva          (nome do paciente)
❌ Reunião médica                (não é atendimento)
❌ Consulta 14h                  (sem nome do médico)
❌ Dr. João                      (sem tipo de atendimento)
```

---

## 🕐 **Organização de Horários**

### **Grade de Horários Padrão:**

#### **Período da Manhã (08:00 - 12:00):**
```
08:00  08:30  09:00  09:30  10:00  10:30  11:00  11:30
```

#### **Período da Tarde (14:00 - 18:00):**
```
14:00  14:30  15:00  15:30  16:00  16:30  17:00  17:30
```

### **Duração por Tipo de Consulta:**

| Tipo de Atendimento | Duração | Horários Sugeridos |
|-------------------|---------|-------------------|
| **Consulta** | 30 min | Qualquer horário padrão |
| **Primeira Consulta** | 45 min | 08:00, 09:00, 14:00, 15:00 |
| **Retorno** | 20 min | Qualquer horário + 10 min |
| **Procedimento** | 60 min | 08:00, 10:00, 14:00, 16:00 |
| **Avaliação** | 30 min | Qualquer horário padrão |

---

## 📱 **Como o Chatbot Funciona**

### **O que o chatbot faz:**
1. **Consulta o calendário** em tempo real
2. **Filtra eventos** por nome do médico
3. **Calcula horários livres** baseado nos ocupados
4. **Informa paciente** sobre disponibilidade

### **Exemplo de consulta do chatbot:**

**Calendário atual:**
```
15/09 09:00 - Dr. João Carvalho - Consulta
15/09 14:00 - Dra. Maria Santos - Consulta  
15/09 15:30 - Dr. João Carvalho - Retorno
16/09 10:00 - Dr. João Carvalho - Consulta
```

**Paciente pergunta:** "Quero agendar com Dr. João"

**Chatbot responde:**
```
Dr. João Carvalho está disponível:

📅 Segunda (15/09):
• 08:00, 08:30, 10:00, 10:30, 11:00, 14:00, 14:30, 15:00, 16:00

📅 Terça (16/09):  
• 08:00, 08:30, 09:00, 09:30, 11:00, 14:00, 14:30, 15:00, 15:30

Qual horário prefere?
```

---

## 📋 **Rotina Diária da Secretária**

### **🌅 Início do Dia (08:00):**
1. **Verificar calendário** do dia
2. **Confirmar agendamentos** com pacientes
3. **Checar nomenclatura** dos eventos
4. **Atualizar faltas** ou cancelamentos

### **🕐 Durante o Dia:**
1. **Criar novos agendamentos** conforme solicitações
2. **Cancelar eventos** quando necessário
3. **Reagendar consultas** se houver conflitos
4. **Manter calendário atualizado** em tempo real

### **🌆 Final do Dia (18:00):**
1. **Revisar eventos** do dia seguinte
2. **Confirmar agenda** com cada médico
3. **Preparar lembretes** para pacientes
4. **Verificar consistência** do calendário

---

## 🔧 **Criando Eventos no Google Calendar**

### **Passo a Passo:**

1. **Abrir Google Calendar** da clínica
2. **Clicar no horário** desejado
3. **Preencher informações:**
   ```
   Título: Dr. João Carvalho - Consulta
   Data: 15/09/2025
   Horário: 14:00 - 14:30
   Descrição: Paciente: Maria Silva (opcional)
   ```
4. **Salvar evento**

### **Campos Importantes:**

#### **Título (Obrigatório):**
- Sempre seguir padrão: `Dr. Nome - Tipo`
- Usar nome completo do médico
- Especificar tipo de atendimento

#### **Horário (Obrigatório):**
- Início e fim precisos
- Respeitar grade de horários
- Considerar duração por tipo

#### **Descrição (Opcional):**
```
Paciente: João Silva
Telefone: (11) 99999-9999
Convênio: SulAmérica
Observações: Primeira consulta
```

---

## 🚨 **Situações Especiais**

### **Médico Ausente:**
```
Dr. João - AUSENTE
Dr. João - FÉRIAS
Dr. João - CONGRESSO
```
**Resultado:** Chatbot não mostra disponibilidade para o Dr. João

### **Horário Bloqueado:**
```
Dr. João - BLOQUEADO
Dr. João - RESERVADO
```
**Resultado:** Horário não aparece como disponível

### **Emergência/Encaixe:**
```
Dr. João - EMERGÊNCIA
Dr. João - ENCAIXE
```
**Resultado:** Horário ocupado, mas pode ser reorganizado

### **Procedimentos Longos:**
```
Dra. Maria - Procedimento Cirúrgico (2h)
```
**Resultado:** Bloqueia múltiplos slots de horário

---

## 📊 **Monitoramento e Relatórios**

### **Métricas que a Secretária Deve Acompanhar:**

#### **Diárias:**
- ✅ **Taxa de ocupação** por médico
- ✅ **Cancelamentos** do dia
- ✅ **Encaixes** realizados
- ✅ **Faltas** de pacientes

#### **Semanais:**
- 📈 **Horários mais procurados**
- 📊 **Médicos mais agendados**
- 📅 **Dias com maior demanda**
- 🔄 **Reagendamentos frequentes**

### **Relatório Semanal Sugerido:**
```
📊 RELATÓRIO SEMANAL - 09/09 a 15/09

👨‍⚕️ Dr. João Carvalho:
• Consultas agendadas: 25
• Taxa de ocupação: 85%
• Cancelamentos: 2
• Encaixes: 3

👩‍⚕️ Dra. Maria Santos:
• Consultas agendadas: 20
• Taxa de ocupação: 75%
• Cancelamentos: 1
• Encaixes: 1

🎯 INSIGHTS:
• Terça-feira é o dia mais procurado
• Horário 14:00 tem maior demanda
• Dr. João precisa de mais slots
```

---

## 💡 **Dicas Importantes**

### **Para Melhor Organização:**
1. **Use cores** diferentes para cada médico no Google Calendar
2. **Configure lembretes** automáticos
3. **Mantenha backup** de agendamentos importantes
4. **Sincronize** com agenda física se necessário

### **Para Evitar Conflitos:**
1. **Sempre confirme** com o médico antes de agendar
2. **Verifique disponibilidade** real antes de criar evento
3. **Comunique mudanças** imediatamente
4. **Mantenha margem** entre consultas

### **Para Melhor Atendimento:**
1. **Responda rapidamente** às solicitações do chatbot
2. **Mantenha calendário atualizado** em tempo real
3. **Use descrições** para informações importantes
4. **Monitore** horários de pico

---

## 🔄 **Fluxo de Trabalho Integrado**

### **Quando Paciente Consulta Chatbot:**
```
1. 👤 Paciente: "Quero agendar com Dr. João"
2. 🤖 Chatbot: Consulta Google Calendar
3. 📅 Sistema: Filtra eventos do Dr. João
4. 🧮 Sistema: Calcula horários livres
5. 💬 Chatbot: "Dr. João disponível: 14:00, 15:00..."
6. 👤 Paciente: "Quero 14:00"
7. 🤖 Chatbot: "Entre em contato para confirmar: (11) 99999-9999"
```

### **Quando Secretária Recebe Ligação:**
```
1. 📞 Paciente liga: "O chatbot disse que Dr. João tem 14:00 livre"
2. 👩‍💼 Secretária: Verifica Google Calendar
3. ✅ Secretária: Confirma disponibilidade
4. 📝 Secretária: Cria evento "Dr. João - Consulta"
5. 💬 Secretária: Confirma com paciente
```

---

## 🎓 **Treinamento da Equipe**

### **O que a Secretária Precisa Saber:**
- ✅ **Como usar Google Calendar** básico
- ✅ **Padrão de nomenclatura** obrigatório
- ✅ **Horários de cada médico**
- ✅ **Como o chatbot funciona**
- ✅ **Quando atualizar calendário**

### **Treinamento Sugerido (2 horas):**
1. **30 min**: Explicação do sistema integrado
2. **45 min**: Prática com Google Calendar
3. **30 min**: Simulação de agendamentos
4. **15 min**: Dúvidas e ajustes

---

**Com esta abordagem, a secretária tem controle total sobre os agendamentos, enquanto o chatbot fornece informações precisas e atualizadas aos pacientes!** 👩‍💼📅✨
