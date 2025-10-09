# 📅 Configuração do Google Calendar - Guia Completo

Este guia explica como configurar a integração com Google Calendar para consultar disponibilidade de horários dos médicos da clínica.

## 🎯 **Objetivo**

Permitir que o chatbot consulte um **calendário único da clínica** no Google Calendar para informar:
- ✅ **Dias disponíveis** para agendamento de cada médico
- ✅ **Horários livres** baseados em eventos existentes
- ✅ **Disponibilidade em tempo real** controlada pela secretária
- ✅ **Gestão centralizada** com controle humano

---

## 🚀 **Configuração Rápida (Mais Simples)**

### **Opção 1: Usar Dados Simulados (Recomendado para Testes)**

1. **No arquivo `.env`:**
```env
GOOGLE_CALENDAR_ENABLED=False
```

2. **Resultado:**
- Sistema usa horários simulados
- Funciona imediatamente
- Ideal para desenvolvimento e testes
- Horários: 09:00, 10:00, 14:00, 15:00, 16:00

---

## 🔧 **Configuração Completa (Google Calendar Real)**

### **Passo 1: Criar Projeto no Google Cloud Console**

1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um novo projeto ou selecione um existente
3. Nome sugerido: "Chatbot-Clinica-Medica"

### **Passo 2: Habilitar Google Calendar API**

1. No menu lateral: **APIs e Serviços** → **Biblioteca**
2. Busque por "Google Calendar API"
3. Clique em **Habilitar**

### **Passo 3: Criar Conta de Serviço**

1. Vá para **APIs e Serviços** → **Credenciais**
2. Clique em **+ Criar Credenciais** → **Conta de Serviço**
3. Preencha:
   - **Nome:** `chatbot-calendar-service`
   - **Descrição:** `Serviço para consultar calendários dos médicos`
4. Clique em **Criar e Continuar**
5. **Função:** Selecione `Visualizador` (ou crie uma função personalizada)
6. Clique em **Concluído**

### **Passo 4: Gerar Chave da Conta de Serviço**

1. Na lista de contas de serviço, clique na conta criada
2. Vá para a aba **Chaves**
3. Clique em **Adicionar Chave** → **Criar Nova Chave**
4. Selecione **JSON**
5. **Baixe o arquivo** (ex: `service-account-key.json`)
6. **Coloque o arquivo** na raiz do projeto Django

### **Passo 5: Configurar Calendário Único da Clínica (Recomendado)**

#### **📅 Calendário Único Controlado pela Secretária**

1. **Criar calendário principal da clínica:**
   - Nome: "Agenda Clínica Saúde Total"
   - Email: `agenda@clinica.com` (ou similar)

2. **Padrão de nomenclatura de eventos:**
   ```
   Dr. João - Consulta Cardiologia
   Dra. Maria - Consulta Dermatologia  
   Dr. João - Retorno
   Dra. Maria - Procedimento
   ```

3. **Compartilhar com a conta de serviço:**
   - Adicionar email da conta de serviço
   - Permissão: **Ver todos os detalhes do evento**

4. **Responsabilidades da secretária:**
   - ✅ Criar/editar/cancelar eventos
   - ✅ Manter nomenclatura consistente
   - ✅ Gerenciar conflitos de horário
   - ✅ Atualizar disponibilidade em tempo real

### **Passo 6: Configurar o Django**

1. **No arquivo `.env`:**
```env
GOOGLE_CALENDAR_ENABLED=True
GOOGLE_SERVICE_ACCOUNT_FILE=service-account-key.json
CLINIC_DOMAIN=clinica.com
CLINIC_CALENDAR_ID=agenda@clinica.com
```

2. **Instalar dependências:**
```bash
pip install -r requirements.txt
```

---

## 👩‍💼 **Guia para a Secretária - Gerenciamento do Calendário**

### **📝 Padrão de Nomenclatura de Eventos**

#### **Formato Obrigatório:**
```
[Nome do Médico] - [Tipo de Atendimento]
```

#### **Exemplos Corretos:**
```
✅ Dr. João - Consulta
✅ Dr. João - Retorno  
✅ Dr. João - Consulta Cardiologia
✅ Dra. Maria - Consulta
✅ Dra. Maria - Procedimento Dermatológico
✅ Dr. Pedro - Consulta Ortopedia
```

#### **Exemplos Incorretos:**
```
❌ Consulta João (nome incompleto)
❌ Paciente João Silva (sem nome do médico)
❌ Reunião (não é atendimento)
❌ João - 14h (sem "Dr.")
```

### **🕐 Organização de Horários**

#### **Horários Padrão Sugeridos:**
```
Manhã:   08:00, 08:30, 09:00, 09:30, 10:00, 10:30, 11:00, 11:30
Tarde:   14:00, 14:30, 15:00, 15:30, 16:00, 16:30, 17:00, 17:30
```

#### **Duração de Consultas:**
- **Consulta normal**: 30 minutos
- **Primeira consulta**: 45 minutos  
- **Retorno**: 20 minutos
- **Procedimento**: 60 minutos

### **📋 Checklist para Secretária**

#### **Ao criar evento:**
- ✅ Nome do médico completo (Dr./Dra.)
- ✅ Tipo de atendimento claro
- ✅ Horário correto
- ✅ Duração adequada
- ✅ Informações do paciente na descrição (opcional)

#### **Ao cancelar evento:**
- ✅ Deletar evento completamente
- ✅ Verificar se não há conflitos
- ✅ Comunicar mudanças ao médico

#### **Manutenção semanal:**
- ✅ Revisar eventos da semana
- ✅ Verificar nomenclatura consistente
- ✅ Confirmar horários com médicos
- ✅ Atualizar indisponibilidades

---

## 🧪 **Testando a Configuração**

### **1. Teste via API:**
```bash
# Testar conexão
curl http://localhost:8000/api/test/calendar/

# Consultar disponibilidade
curl http://localhost:8000/api/test/availability/Dr.%20João/?days=7
```

### **2. Resposta Esperada:**
```json
{
  "google_calendar_enabled": true,
  "connection_status": "connected",
  "message": "Google Calendar funcionando"
}
```

### **3. Disponibilidade de Médico:**
```json
{
  "doctor": "Dr. João",
  "availability": {
    "doctor_name": "Dr. João Carvalho",
    "period": "15/09/2025 a 22/09/2025",
    "days": [
      {
        "date": "16/09/2025",
        "weekday": "Segunda",
        "available_times": ["09:00", "10:00", "14:00", "15:00"]
      },
      {
        "date": "17/09/2025", 
        "weekday": "Terça",
        "available_times": ["09:30", "10:30", "14:30", "15:30"]
      }
    ]
  }
}
```

---

## 📊 **Como Funciona**

### **Fluxo de Consulta:**
```
1. 👤 Paciente: "Quero agendar com Dr. João"
2. 🤖 Sistema: Consulta Google Calendar do Dr. João
3. 📅 Calendar: Retorna eventos ocupados
4. 🧠 Sistema: Calcula horários livres
5. 💬 Chatbot: "Dr. João tem horários disponíveis: Segunda 09:00, 10:00..."
```

### **Lógica de Disponibilidade:**
```python
# Horários padrão do médico
horarios_trabalho = ['08:00', '08:30', '09:00', '09:30', '10:00', ...]

# Eventos ocupados no Google Calendar
eventos_ocupados = ['09:00', '14:00', '15:30']

# Horários disponíveis = Horários trabalho - Eventos ocupados
horarios_disponiveis = ['08:00', '08:30', '10:00', '10:30', ...]
```

---

## ⚙️ **Configurações Avançadas**

### **Personalizar Horários por Médico:**
```python
# Em settings.py ou banco de dados
DOCTOR_WORKING_HOURS = {
    'dr. joao carvalho': {
        'morning': ['08:00', '08:30', '09:00', '09:30', '10:00'],
        'afternoon': ['14:00', '14:30', '15:00', '15:30', '16:00']
    },
    'dra. maria santos': {
        'morning': ['09:00', '09:30', '10:00', '10:30', '11:00'],
        'afternoon': ['13:00', '13:30', '14:00', '14:30', '15:00']
    }
}
```

### **Configurar Dias de Trabalho:**
```python
# Excluir fins de semana, feriados, etc.
DOCTOR_WORKING_DAYS = {
    'dr. joao carvalho': [0, 1, 2, 3, 4],  # Segunda a Sexta
    'dra. maria santos': [1, 3, 4],        # Terça, Quinta, Sexta
}
```

---

## 🔒 **Segurança e Permissões**

### **Princípio do Menor Privilégio:**
- Conta de serviço tem apenas permissão de **leitura**
- Acesso apenas aos calendários específicos
- Não pode criar, editar ou deletar eventos

### **Arquivo de Credenciais:**
```bash
# Adicionar ao .gitignore
echo "service-account-key.json" >> .gitignore

# Permissões restritivas
chmod 600 service-account-key.json
```

---

## 🚨 **Troubleshooting**

### **Erro: "Credentials not found"**
```bash
# Verificar se arquivo existe
ls -la service-account-key.json

# Verificar configuração no .env
cat .env | grep GOOGLE_SERVICE_ACCOUNT_FILE
```

### **Erro: "Calendar not found"**
1. Verificar se calendar ID está correto
2. Verificar se conta de serviço tem acesso ao calendar
3. Testar com email da conta de serviço

### **Erro: "403 Forbidden"**
1. Verificar se Google Calendar API está habilitada
2. Verificar permissões da conta de serviço
3. Verificar se calendar foi compartilhado corretamente

### **Usando Dados Simulados:**
Se houver qualquer problema, o sistema automaticamente usa dados simulados:
```json
{
  "mock_data": true,
  "message": "Usando horários simulados - Google Calendar não disponível"
}
```

---

## 📈 **Vantagens da Integração**

### **Para a Clínica:**
✅ **Sincronização automática** - Horários sempre atualizados  
✅ **Redução de conflitos** - Evita agendamentos duplos  
✅ **Gestão centralizada** - Médicos gerenciam próprios calendários  
✅ **Flexibilidade** - Fácil alteração de horários  

### **Para os Pacientes:**
✅ **Informação em tempo real** - Disponibilidade atualizada  
✅ **Múltiplas opções** - Vários horários e médicos  
✅ **Conveniência** - Consulta via WhatsApp  
✅ **Transparência** - Horários claros e organizados  

### **Para o Sistema:**
✅ **Escalabilidade** - Suporta muitos médicos  
✅ **Confiabilidade** - Fallback para dados simulados  
✅ **Performance** - Cache inteligente  
✅ **Manutenibilidade** - Configuração simples  

---

## 🔮 **Próximos Passos (Futuro)**

### **Funcionalidades Avançadas:**
- **Agendamento direto** - Criar eventos no calendar
- **Notificações** - Lembretes automáticos
- **Sincronização bidirecional** - Atualizar banco de dados
- **Analytics** - Relatórios de ocupação

### **Integrações Adicionais:**
- **Outlook Calendar** - Para médicos que usam Microsoft
- **Apple Calendar** - Integração com iCloud
- **Sistema próprio** - API da clínica

---

## 📚 **Recursos Úteis**

- [Google Calendar API Docs](https://developers.google.com/calendar/api)
- [Service Account Guide](https://cloud.google.com/iam/docs/service-accounts)
- [Python Client Library](https://github.com/googleapis/google-api-python-client)

---

**Com esta configuração, seu chatbot terá acesso em tempo real à disponibilidade dos médicos, tornando o processo de agendamento muito mais eficiente e confiável!** 📅✨
