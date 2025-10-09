# 📊 Organização e Estrutura do Banco de Dados - Atualizada 09/10 (mais recente)

## 📋 Índice
- [Visão Geral](#visão-geral)
- [Arquitetura do Banco de Dados](#arquitetura-do-banco-de-dados)
- [Modelos de Dados](#modelos-de-dados)
- [Relacionamentos](#relacionamentos)
- [Migrações](#migrações)
- [Estratégias de Otimização](#estratégias-de-otimização)

---

## Visão Geral

O projeto utiliza **SQLite3** como banco de dados principal, organizado através do ORM do Django. A estrutura está dividida em **dois aplicativos (apps)** principais:

### 1. **api_gateway** 
Gerencia conversas e sessões de agendamento

### 2. **rag_agent** 
Armazena informações da clínica (médicos, exames, especialidades, convênios)

---

## Arquitetura do Banco de Dados

### Diagrama de Estrutura

```
┌─────────────────────────────────────────────────────────────┐
│                      BANCO DE DADOS                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────┐        ┌─────────────────────┐    │
│  │    api_gateway      │        │     rag_agent       │    │
│  ├─────────────────────┤        ├─────────────────────┤    │
│  │ ConversationSession │        │  ClinicaInfo        │    │
│  │ ConversationMessage │        │  Especialidade      │    │
│  └─────────────────────┘        │  Convenio           │    │
│                                  │  Medico             │    │
│                                  │  HorarioTrabalho    │    │
│                                  │  Exame              │    │
│                                  └─────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## Modelos de Dados

### 📱 App: `api_gateway`

#### 1. **ConversationSession** (Sessão de Conversa)
Armazena o estado da conversa de cada paciente.

**Campos:**
```python
- phone_number: CharField(max_length=20, unique=True)
  └─ Número do telefone do paciente (chave única)

- patient_name: CharField(max_length=100, blank=True, null=True)
  └─ Nome completo do paciente após confirmação

- pending_name: CharField(max_length=100, blank=True, null=True)
  └─ Nome extraído aguardando confirmação do paciente

- name_confirmed: BooleanField(default=False)
  └─ Flag indicando se o nome foi confirmado pelo paciente

- current_state: CharField(max_length=50, default='idle')
  └─ Estado atual da conversa
  └─ Opções:
      • idle: Ocioso (estado inicial)
      • collecting_patient_info: Coletando dados do paciente
      • collecting_info: Coletando informações gerais
      • confirming_name: Confirmando nome do paciente
      • selecting_doctor: Selecionando médico
      • choosing_schedule: Escolhendo horário
      • confirming: Confirmando agendamento

- specialty_interest: CharField(max_length=100, blank=True, null=True)
  └─ Especialidade de interesse do paciente

- insurance_type: CharField(max_length=50, blank=True, null=True)
  └─ Tipo de convênio (ou "Particular")

- preferred_date: DateField(blank=True, null=True)
  └─ Data preferida para consulta

- preferred_time: TimeField(blank=True, null=True)
  └─ Horário preferido para consulta

- selected_doctor: CharField(max_length=100, blank=True, null=True)
  └─ Médico selecionado pelo paciente

- additional_notes: TextField(blank=True, null=True)
  └─ Notas adicionais sobre o agendamento

- created_at: DateTimeField(auto_now_add=True)
  └─ Data/hora de criação da sessão

- updated_at: DateTimeField(auto_now=True)
  └─ Data/hora da última atualização

- last_activity: DateTimeField(auto_now=True)
  └─ Data/hora da última atividade (usada para limpeza de sessões antigas)
```

**Métodos:**
```python
- is_active(): Verifica se a sessão está ativa (< 24h de inatividade)
- update_activity(): Atualiza o timestamp da última atividade
```

---

#### 2. **ConversationMessage** (Mensagem da Conversa)
Armazena cada mensagem individual da conversa.

**Campos:**
```python
- session: ForeignKey(ConversationSession, on_delete=CASCADE, related_name='messages')
  └─ Relacionamento com a sessão de conversa

- message_type: CharField(max_length=10)
  └─ Tipo da mensagem
  └─ Opções:
      • user: Mensagem do usuário/paciente
      • bot: Resposta do chatbot
      • system: Mensagem do sistema

- content: TextField()
  └─ Conteúdo da mensagem

- intent: CharField(max_length=50, blank=True, null=True)
  └─ Intenção identificada pelo Gemini
  └─ Exemplos: saudacao, agendar_consulta, buscar_medico

- confidence: FloatField(blank=True, null=True)
  └─ Confiança da análise de intenção (0.0 a 1.0)

- entities: JSONField(default=dict, blank=True)
  └─ Entidades extraídas da mensagem (JSON)
  └─ Exemplos:
      {
        "nome_paciente": "João Silva",
        "medico": "Dr. Gustavo",
        "data": "15/10/2024",
        "horario": "14:30"
      }

- timestamp: DateTimeField(auto_now_add=True)
  └─ Data/hora da mensagem
```

**Ordenação:**
- As mensagens são ordenadas por `timestamp` (cronológica)

---

### 🏥 App: `rag_agent`

#### 1. **ClinicaInfo** (Informações da Clínica)
Armazena informações gerais da clínica (apenas 1 registro).

**Campos:**
```python
- nome: CharField(max_length=100, default="Clínica PneumoSono")
  └─ Nome da clínica

- objetivo_geral: TextField()
  └─ Objetivo e missão da clínica

- secretaria_nome: CharField(max_length=100, default="Raro")
  └─ Nome da secretária/recepcionista

- telefone_contato: CharField(max_length=20, blank=True, null=True)
  └─ Telefone fixo de contato

- whatsapp_contato: CharField(max_length=20)
  └─ Número do WhatsApp da clínica

- email_contato: EmailField(blank=True, null=True)
  └─ E-mail de contato

- endereco: TextField()
  └─ Endereço completo da clínica

- referencia_localizacao: CharField(max_length=200)
  └─ Referência para facilitar localização

- politica_agendamento: TextField()
  └─ Política de agendamento e horários

- google_calendar_id: CharField(max_length=255, blank=True, null=True)
  └─ ID da agenda principal do Google Calendar
```

---

#### 2. **Especialidade** (Especialidades Médicas)
Especialidades atendidas pela clínica.

**Campos:**
```python
- nome: CharField(max_length=100, unique=True)
  └─ Nome da especialidade (ex: "Cardiologia", "Pneumologia")

- descricao: TextField(blank=True, null=True)
  └─ Descrição da especialidade

- ativa: BooleanField(default=True)
  └─ Se a especialidade está ativa para seleção
```

**Relacionamentos:**
- Um médico pode ter múltiplas especialidades (ManyToMany)

---

#### 3. **Convenio** (Convênios Aceitos)
Convênios médicos aceitos pela clínica.

**Campos:**
```python
- nome: CharField(max_length=100, unique=True)
  └─ Nome do convênio (ex: "Unimed", "Bradesco Saúde")

- descricao: TextField(blank=True, null=True)
  └─ Descrição e informações do convênio
```

**Relacionamentos:**
- Vários médicos podem aceitar vários convênios (ManyToMany)

---

#### 4. **Medico** (Médicos da Clínica)
Informações dos médicos que atendem na clínica.

**Campos:**
```python
- nome: CharField(max_length=100)
  └─ Nome completo do médico

- crm: CharField(max_length=100, unique=True, null=True, blank=True)
  └─ Número do CRM do médico

- especialidades: ManyToManyField(Especialidade, related_name='medicos')
  └─ Especialidades do médico

- bio: TextField()
  └─ Biografia e informações do médico

- convenios: ManyToManyField(Convenio, blank=True, related_name="medicos")
  └─ Convênios aceitos pelo médico

- preco_particular: DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
  └─ Preço da consulta particular

- formas_pagamento: CharField(max_length=200)
  └─ Formas de pagamento aceitas

- retorno_info: CharField(max_length=100, default="Consulta de retorno em até 30 dias incluído no valor.")
  └─ Informações sobre consulta de retorno
```

**Métodos:**
```python
- get_especialidades_display(): Retorna especialidades como string formatada
```

---

#### 5. **HorarioTrabalho** (Horários de Trabalho)
Horários de atendimento de cada médico por dia da semana.

**Campos:**
```python
- medico: ForeignKey(Medico, on_delete=CASCADE, related_name="horarios_trabalho")
  └─ Médico relacionado

- dia_da_semana: IntegerField(choices=DIA_DA_SEMANA_CHOICES)
  └─ Dia da semana (1=Segunda, 2=Terça, ..., 7=Domingo)

- hora_inicio: TimeField()
  └─ Hora de início do atendimento

- hora_fim: TimeField()
  └─ Hora de término do atendimento
```

**Constraints:**
```python
- UniqueConstraint: ['medico', 'dia_da_semana', 'hora_inicio']
  └─ Garante que não haja horários duplicados para o mesmo médico
```

---

#### 6. **Exame** (Exames Disponíveis)
Exames e procedimentos oferecidos pela clínica.

**Campos:**
```python
- nome: CharField(max_length=100)
  └─ Nome do exame

- o_que_e: TextField()
  └─ Descrição do que é o exame

- como_funciona: TextField()
  └─ Como o exame funciona

- preparacao: TextField(blank=True, null=True)
  └─ Preparação necessária para o exame

- vantagem: TextField(blank=True, null=True)
  └─ Vantagens do exame

- preco: DecimalField(max_digits=8, decimal_places=2)
  └─ Preço do exame

- duracao_estimada: DurationField(blank=True, null=True)
  └─ Duração estimada do exame (ex: 00:30:00 para 30 min)
```

---

## Relacionamentos

### Diagrama de Relacionamentos

```
┌─────────────────────┐
│ ConversationSession │
│                     │
│ - phone_number (PK) │
└──────────┬──────────┘
           │
           │ 1:N (One-to-Many)
           │
           ▼
┌─────────────────────┐
│ ConversationMessage │
│                     │
│ - session (FK)      │
│ - content           │
│ - entities (JSON)   │
└─────────────────────┘


┌──────────────┐         N:M          ┌──────────────┐
│ Especialidade├─────────────────────►│   Medico     │
└──────────────┘                      └──────┬───────┘
                                             │
                                             │ N:M
                                             │
┌──────────────┐                      ┌──────▼───────┐
│   Convenio   ├──────────────────────┤   Medico     │
└──────────────┘                      └──────┬───────┘
                                             │
                                             │ 1:N
                                             │
                                      ┌──────▼────────┐
                                      │HorarioTrabalho│
                                      └───────────────┘
```

### Descrição dos Relacionamentos

1. **ConversationSession → ConversationMessage** (1:N)
   - Uma sessão pode ter múltiplas mensagens
   - Quando uma sessão é deletada, todas as mensagens são deletadas (CASCADE)

2. **Medico ↔ Especialidade** (N:M)
   - Um médico pode ter múltiplas especialidades
   - Uma especialidade pode ter múltiplos médicos

3. **Medico ↔ Convenio** (N:M)
   - Um médico pode aceitar múltiplos convênios
   - Um convênio pode ser aceito por múltiplos médicos

4. **Medico → HorarioTrabalho** (1:N)
   - Um médico pode ter múltiplos horários de trabalho
   - Cada horário pertence a um único médico

---

## Migrações

### Histórico de Migrações

#### **api_gateway**

```python
0001_initial.py
├─ Cria ConversationSession e ConversationMessage iniciais

0002_alter_conversationsession_current_state.py
├─ Altera opções de current_state

0003_conversationsession_name_confirmed_and_more.py
├─ Adiciona campos:
│  ├─ name_confirmed
│  └─ pending_name

0004_delete_ragcache.py
├─ Remove modelo RAGCache (não mais necessário)

0005_delete_appointmentrequest.py
├─ Remove modelo AppointmentRequest (substituído por ConversationSession)

0006_remove_completed_cancelled_states.py
├─ Remove estados 'completed' e 'cancelled' de current_state
└─ Mantém apenas estados relevantes ao fluxo de conversação
```

#### **rag_agent**

```python
0001_initial.py
├─ Cria modelos iniciais:
│  ├─ ClinicaInfo
│  ├─ Especialidade
│  ├─ Convenio
│  ├─ Medico
│  ├─ HorarioTrabalho
│  └─ Exame

0002_clinicainfo_whatsapp_contato_and_more.py
├─ Adiciona campo whatsapp_contato à ClinicaInfo
└─ Ajustes em outros campos

0003_medico_crm.py
└─ Adiciona campo crm ao modelo Medico
```

---

## Estratégias de Otimização

### 1. **Índices**
```python
# Índices automáticos do Django:
- phone_number (ConversationSession) → UNIQUE INDEX
- crm (Medico) → UNIQUE INDEX
- nome (Especialidade) → UNIQUE INDEX
- nome (Convenio) → UNIQUE INDEX
```

### 2. **Ordenação Padrão**
```python
# ConversationSession
ordering = ['-last_activity']  # Mais recentes primeiro

# ConversationMessage
ordering = ['timestamp']  # Cronológica

# Especialidade
ordering = ['nome']  # Alfabética
```

### 3. **Campos com Valores Padrão**
- Reduz necessidade de validações adicionais
- Melhora integridade dos dados
- Facilita criação de novos registros

### 4. **Relacionamentos Otimizados**
```python
# Uso de related_name para queries reversas eficientes
session.messages.all()  # Todas as mensagens da sessão
medico.horarios_trabalho.all()  # Todos os horários do médico
especialidade.medicos.all()  # Todos os médicos da especialidade
```

### 5. **Limpeza Automática de Sessões Antigas**
```python
# conversation_service.py
def cleanup_old_sessions(days_old=7):
    """
    Remove sessões com mais de 7 dias de inatividade
    """
    cutoff_date = timezone.now() - timedelta(days=days_old)
    old_sessions = ConversationSession.objects.filter(
        last_activity__lt=cutoff_date
    )
    old_sessions.delete()
```

---

## Consultas Comuns

### Exemplos de Queries Otimizadas

```python
# 1. Obter sessão com todas as mensagens
session = ConversationSession.objects.prefetch_related('messages').get(
    phone_number='5573988221003'
)

# 2. Buscar médicos por especialidade
medicos = Medico.objects.filter(
    especialidades__nome='Cardiologia'
).prefetch_related('convenios', 'especialidades')

# 3. Obter horários de um médico específico
horarios = HorarioTrabalho.objects.filter(
    medico__nome='Dr. Gustavo'
).select_related('medico')

# 4. Sessões ativas (últimas 24h)
from django.utils import timezone
from datetime import timedelta

cutoff = timezone.now() - timedelta(hours=24)
active_sessions = ConversationSession.objects.filter(
    last_activity__gte=cutoff
)

# 5. Médicos que atendem por convênio específico
medicos = Medico.objects.filter(
    convenios__nome='Unimed'
).distinct()
```

---

## Backup e Manutenção

### Comandos Úteis

```bash
# Criar backup do banco
python manage.py dumpdata > backup.json

# Restaurar backup
python manage.py loaddata backup.json

# Criar backup de app específico
python manage.py dumpdata api_gateway > api_gateway_backup.json
python manage.py dumpdata rag_agent > rag_agent_backup.json

# Visualizar estrutura do banco
python manage.py dbshell
.schema

# Verificar migrações pendentes
python manage.py showmigrations

# Criar nova migração
python manage.py makemigrations

# Aplicar migrações
python manage.py migrate
```

---

## Considerações Finais

### ✅ Pontos Fortes
- **Separação clara de responsabilidades** entre api_gateway e rag_agent
- **Relacionamentos bem definidos** com uso adequado de ForeignKey e ManyToMany
- **Histórico completo de conversas** para análise e melhoria
- **Estrutura escalável** que suporta múltiplos médicos, especialidades e convênios
- **Validações no nível do modelo** (unique constraints, choices)

### 🔄 Possíveis Melhorias Futuras
- Migração para PostgreSQL para maior performance em produção
- Implementação de cache em Redis para consultas frequentes
- Índices compostos para queries mais complexas
- Soft delete para sessões antigas (ao invés de deletar completamente)
- Auditoria completa com django-simple-history

---

**Última Atualização:** Outubro 2024  
**Versão:** 1.0  
**Autor:** Sistema de Documentação Automatizada

