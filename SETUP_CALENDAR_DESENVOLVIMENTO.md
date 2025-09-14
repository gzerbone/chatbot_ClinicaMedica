# 📅 Setup Google Calendar - Desenvolvimento com Email Pessoal

Guia passo a passo para configurar o Google Calendar usando seu email pessoal `gzerbone@gmail.com` para testes de desenvolvimento.

## 🎯 **Objetivo**

Configurar um calendário de teste usando sua conta pessoal do Google para validar a integração antes de implementar na clínica real.

---

## 📋 **PASSO 1: Criar Calendário de Teste**

### **1.1 Acessar Google Calendar**
1. Abra [Google Calendar](https://calendar.google.com)
2. Faça login com `gzerbone@gmail.com`

### **1.2 Criar Novo Calendário**
1. No lado esquerdo, clique no **"+"** ao lado de "Outros calendários"
2. Selecione **"Criar novo calendário"**
3. Preencha:
   ```
   Nome: Agenda Clínica Teste
   Descrição: Calendário para testes do chatbot da clínica
   Fuso horário: (UTC-03:00) Brasília
   ```
4. Clique em **"Criar calendário"**

### **1.3 Encontrar o Calendar ID**
1. Após criar, vá em **"Configurações e compartilhamento"** do calendário
2. Role até **"Integrar calendário"**
3. Copie o **"ID do calendário"**
   ```
   Exemplo: c_1234567890abcdef@group.calendar.google.com
   ```
4. **ANOTE ESTE ID** - você precisará dele no `.env`

---

## 📋 **PASSO 2: Configurar Google Cloud Console**

### **2.1 Criar Projeto**
1. Acesse [Google Cloud Console](https://console.cloud.google.com)
2. Faça login com `gzerbone@gmail.com`
3. Clique em **"Selecionar projeto"** → **"Novo projeto"**
4. Nome: `chatbot-clinica-teste`
5. Clique em **"Criar"**

### **2.2 Habilitar Calendar API**
1. No menu lateral: **"APIs e serviços"** → **"Biblioteca"**
2. Busque: `Google Calendar API`
3. Clique na API e depois em **"Ativar"**

### **2.3 Criar Conta de Serviço**
1. Vá para **"APIs e serviços"** → **"Credenciais"**
2. Clique **"+ Criar credenciais"** → **"Conta de serviço"**
3. Preencha:
   ```
   Nome: chatbot-calendar-service
   ID: chatbot-calendar-service
   Descrição: Serviço para consultar calendário da clínica
   ```
4. Clique **"Criar e continuar"**
5. **Função:** Selecione `Visualizador` ou pule esta etapa
6. Clique **"Concluído"**

### **2.4 Gerar Chave JSON**
1. Na lista de contas de serviço, clique na conta criada
2. Vá para aba **"Chaves"**
3. Clique **"Adicionar chave"** → **"Criar nova chave"**
4. Selecione **"JSON"**
5. **Baixe o arquivo** (será algo como `chatbot-clinica-teste-abc123.json`)
6. **Renomeie para:** `service-account-key.json`
7. **Mova para a pasta do projeto:** `C:\Users\gabri\OneDrive\Área de Trabalho\ALL\Faculdade\TCC\chatbot_ClinicaMedica\`

---

## 📋 **PASSO 3: Compartilhar Calendário com Conta de Serviço**

### **3.1 Obter Email da Conta de Serviço**
1. Abra o arquivo `service-account-key.json` baixado
2. Procure o campo `"client_email"`
3. **Copie o email** (será algo como: `chatbot-calendar-service@chatbot-clinica-teste.iam.gserviceaccount.com`)

### **3.2 Compartilhar Calendário**
1. No Google Calendar, vá no calendário **"Agenda Clínica Teste"**
2. Clique nos **três pontos** → **"Configurações e compartilhamento"**
3. Em **"Compartilhar com pessoas específicas"**, clique **"+ Adicionar pessoas"**
4. **Cole o email da conta de serviço**
5. **Permissão:** Selecione **"Ver todos os detalhes do evento"**
6. Clique **"Enviar"**

---

## 📋 **PASSO 4: Configurar o Projeto Django**

### **4.1 Atualizar arquivo `.env`**
```env
# Configurações do Google Calendar API
GOOGLE_CALENDAR_ENABLED=True
GOOGLE_SERVICE_ACCOUNT_FILE=service-account-key.json
CLINIC_DOMAIN=gmail.com
CLINIC_CALENDAR_ID=c_1234567890abcdef@group.calendar.google.com
```

**⚠️ IMPORTANTE:** Substitua `c_1234567890abcdef@group.calendar.google.com` pelo ID real do seu calendário!

### **4.2 Instalar Dependências**
```bash
# Ativar ambiente virtual
venv\Scripts\activate

# Instalar dependências do Google Calendar
pip install google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2
```

---

## 📋 **PASSO 5: Criar Eventos de Teste**

### **5.1 Adicionar Eventos no Google Calendar**

Vá no seu calendário **"Agenda Clínica Teste"** e crie alguns eventos de exemplo:

#### **Segunda-feira (16/09/2025):**
```
09:00 - 09:30  │ Dr. João Carvalho - Consulta
14:00 - 14:30  │ Dr. João Carvalho - Retorno
15:30 - 16:00  │ Dra. Maria Santos - Consulta
```

#### **Terça-feira (17/09/2025):**
```
08:30 - 09:00  │ Dra. Maria Santos - Consulta
10:00 - 10:30  │ Dr. João Carvalho - Consulta
16:00 - 17:00  │ Dra. Maria Santos - Procedimento
```

### **5.2 Formato Obrigatório dos Eventos**
```
✅ CORRETO:
Título: Dr. João Carvalho - Consulta
Título: Dra. Maria Santos - Procedimento
Título: Dr. João - Retorno

❌ INCORRETO:
Título: João - Consulta        (sem "Dr.")
Título: Consulta Dr. João      (ordem errada)
Título: Paciente Maria Silva   (nome do paciente)
```

---

## 📋 **PASSO 6: Testar a Integração**

### **6.1 Testar Conexão**
```bash
# No terminal do projeto
python test_calendar.py
```

**Saída esperada:**
```
🧪 Testando Google Calendar Service...
Habilitado: True

📅 Testando disponibilidade do Dr. João...
Google Calendar conectado. Acesso ao calendário confirmado.
Encontrados 2 eventos para Dr. João Carvalho no calendário da clínica
Médico: Dr. João Carvalho
Período: 16/09/2025 a 20/09/2025
```

### **6.2 Testar via API**
```bash
# Testar conexão
curl http://localhost:8000/api/test/calendar/

# Consultar disponibilidade
curl "http://localhost:8000/api/test/availability/Dr.%20João%20Carvalho/?days=3"
```

### **6.3 Testar via Chatbot**
Envie mensagem no WhatsApp (se configurado):
```
👤: "Quero agendar com Dr. João"
🤖: [Mostrará horários reais baseados no seu calendário]
```

---

## 🔧 **CONFIGURAÇÃO COMPLETA DO .env**

Aqui está como seu arquivo `.env` deve ficar:

```env
# Configurações do Django
DEBUG=True
SECRET_KEY=django-insecure-le135!_9$^gz#fscc)$l_*)#476!r^uxn($+^!^hebdhp=^j7w
ALLOWED_HOSTS=localhost,127.0.0.1,sua-url-do-ngrok.ngrok-free.app

# Configurações do Gemini AI
GEMINI_API_KEY=sua_gemini_api_key_aqui
GEMINI_ENABLED=True
GEMINI_MODEL=gemini-1.5-flash
GEMINI_TEMPERATURE=0.7
GEMINI_MAX_TOKENS=1024

# Configurações do WhatsApp Business API
WHATSAPP_ACCESS_TOKEN=seu_whatsapp_access_token_aqui
WHATSAPP_VERIFY_TOKEN=meu_verify_token_123
WHATSAPP_PHONE_NUMBER_ID=seu_phone_number_id_aqui
WHATSAPP_API_URL=https://graph.facebook.com/v18.0

# Configurações do Google Calendar API
GOOGLE_CALENDAR_ENABLED=True
GOOGLE_SERVICE_ACCOUNT_FILE=service-account-key.json
CLINIC_DOMAIN=gmail.com
CLINIC_CALENDAR_ID=SEU_CALENDAR_ID_AQUI
```

**⚠️ Substitua `SEU_CALENDAR_ID_AQUI` pelo ID real do calendário que você criou!**

---

## 🔍 **Como Encontrar o Calendar ID**

### **Método 1: Via Interface do Google Calendar**
1. Vá no seu calendário **"Agenda Clínica Teste"**
2. Clique nos **três pontos** → **"Configurações e compartilhamento"**
3. Role até **"Integrar calendário"**
4. Copie o **"ID do calendário"**

### **Método 2: Via URL**
1. Clique no calendário para selecioná-lo
2. Observe a URL do navegador
3. O ID estará na URL após `/calendar/`

### **Exemplo de Calendar ID:**
```
c_1a2b3c4d5e6f7g8h9i0j@group.calendar.google.com
```

---

## 📱 **PASSO 7: Testar Fluxo Completo**

### **7.1 Criar Eventos de Teste**
No Google Calendar, crie:
```
Hoje + 1 dia:
09:00 - Dr. João Carvalho - Consulta
14:30 - Dra. Maria Santos - Consulta

Hoje + 2 dias:  
10:00 - Dr. João Carvalho - Retorno
15:00 - Dra. Maria Santos - Procedimento
```

### **7.2 Testar Chatbot**
```bash
# Executar servidor
python manage.py runserver

# Em outro terminal, testar
curl -X POST http://localhost:8000/api/test/intent/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Quero agendar com Dr. João",
    "phone_number": "test_user",
    "use_context": true
  }'
```

### **7.3 Verificar Logs**
No terminal do Django, você deve ver:
```
INFO: Google Calendar conectado. Acesso ao calendário confirmado.
INFO: Encontrados X eventos para Dr. João Carvalho no calendário da clínica
```

---

## 🚨 **Troubleshooting**

### **Erro: "Calendar not found"**
- ✅ Verifique se o Calendar ID está correto no `.env`
- ✅ Confirme se o calendário foi criado
- ✅ Teste copiar o ID novamente

### **Erro: "Permission denied"**
- ✅ Verifique se compartilhou o calendário com a conta de serviço
- ✅ Confirme se a permissão é "Ver todos os detalhes"
- ✅ Aguarde alguns minutos para a permissão propagar

### **Erro: "Service account not found"**
- ✅ Verifique se o arquivo `service-account-key.json` está na pasta correta
- ✅ Confirme se o caminho no `.env` está correto
- ✅ Teste recriar a chave se necessário

### **Eventos não são encontrados:**
- ✅ Verifique se os eventos seguem o padrão "Dr. Nome - Tipo"
- ✅ Confirme se os eventos estão no calendário correto
- ✅ Teste com nomes exatos dos médicos do banco de dados

---

## 📊 **Exemplo de Configuração Final**

### **Seu arquivo `.env` ficará assim:**
```env
# ... outras configurações ...

# Google Calendar (SEU SETUP DE TESTE)
GOOGLE_CALENDAR_ENABLED=True
GOOGLE_SERVICE_ACCOUNT_FILE=service-account-key.json
CLINIC_DOMAIN=gmail.com
CLINIC_CALENDAR_ID=c_abcd1234efgh5678@group.calendar.google.com
```

### **Estrutura de arquivos:**
```
chatbot_ClinicaMedica/
├── .env                          # Suas configurações
├── service-account-key.json      # Chave baixada do Google Cloud
├── manage.py
└── ...
```

### **Eventos de teste no seu calendário:**
```
📅 Agenda Clínica Teste (gzerbone@gmail.com)

Segunda (16/09):
🕐 09:00 - Dr. João Carvalho - Consulta
🕐 14:00 - Dr. João Carvalho - Retorno  
🕐 15:30 - Dra. Maria Santos - Consulta

Terça (17/09):
🕐 08:30 - Dra. Maria Santos - Consulta
🕐 10:00 - Dr. João Carvalho - Consulta
🕐 16:00 - Dra. Maria Santos - Procedimento
```

---

## 🧪 **Validação Final**

### **Teste 1: Conexão**
```bash
curl http://localhost:8000/api/test/calendar/
```

**Resposta esperada:**
```json
{
  "google_calendar_enabled": true,
  "connection_status": "connected", 
  "message": "Google Calendar funcionando"
}
```

### **Teste 2: Disponibilidade**
```bash
curl "http://localhost:8000/api/test/availability/Dr.%20João%20Carvalho/?days=3"
```

**Resposta esperada:**
```json
{
  "doctor": "Dr. João Carvalho",
  "availability": {
    "doctor_name": "Dr. João Carvalho",
    "days": [
      {
        "date": "16/09/2025",
        "weekday": "Segunda",
        "available_times": ["08:00", "08:30", "09:30", "10:00", ...],
        "occupied_times": ["09:00", "14:00"]
      }
    ]
  }
}
```

### **Teste 3: Chatbot Integrado**
```bash
curl -X POST http://localhost:8000/api/test/intent/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Quero agendar com Dr. João amanhã",
    "phone_number": "test_user",
    "use_context": true
  }'
```

---

## 🔄 **Fluxo de Desenvolvimento**

### **Ciclo de Teste:**
```
1. 📝 Criar evento no Google Calendar
   "Dr. João Carvalho - Consulta" (14:00-14:30)

2. 🧪 Testar API
   curl .../availability/Dr.%20João/

3. ✅ Verificar resposta
   Horário 14:00 deve aparecer como ocupado

4. 🤖 Testar chatbot
   "Quero Dr. João amanhã" → Deve mostrar horários livres

5. 🔄 Repetir com diferentes cenários
```

### **Cenários de Teste Sugeridos:**

#### **Cenário 1: Médico com poucos agendamentos**
```
Eventos: 1 consulta de manhã
Resultado: Muitos horários livres
```

#### **Cenário 2: Médico muito ocupado**
```
Eventos: 6-8 consultas no dia
Resultado: Poucos horários livres
```

#### **Cenário 3: Médico ausente**
```
Evento: "Dr. João - AUSENTE" (dia todo)
Resultado: Nenhum horário disponível
```

#### **Cenário 4: Fim de semana**
```
Eventos: Sábado/Domingo
Resultado: Sistema pula automaticamente
```

---

## 📞 **Suporte e Dúvidas**

### **Se algo não funcionar:**

1. **Verifique os logs do Django:**
   ```bash
   python manage.py runserver
   # Observe mensagens de erro no console
   ```

2. **Teste conexão básica:**
   ```bash
   python test_calendar.py
   ```

3. **Verifique arquivo de credenciais:**
   ```bash
   # Deve existir e ser válido JSON
   python -c "import json; print(json.load(open('service-account-key.json'))['client_email'])"
   ```

4. **Confirme permissões do calendário:**
   - Email da conta de serviço deve estar na lista de compartilhamento
   - Permissão deve ser "Ver todos os detalhes"

---

## 🎯 **Resultado Final**

Após seguir todos os passos, você terá:

✅ **Calendário de teste** funcionando  
✅ **Integração real** com Google Calendar API  
✅ **Eventos filtrados** por médico automaticamente  
✅ **Chatbot consultando** horários reais  
✅ **Sistema híbrido** - IA + controle humano  

### **Exemplo de conversa real:**
```
👤: "Dr. João tem horário amanhã?"
🤖: "Dr. João Carvalho disponível amanhã:
     🌅 Manhã: 08:00, 08:30, 10:00, 10:30
     🌆 Tarde: 15:00, 15:30, 17:00
     
     (Baseado na agenda real da clínica)
     Para agendar: (11) 99999-9999"
```

**Agora você tem um sistema real funcionando com seu Google Calendar pessoal para testes!** 📅✨🎯
