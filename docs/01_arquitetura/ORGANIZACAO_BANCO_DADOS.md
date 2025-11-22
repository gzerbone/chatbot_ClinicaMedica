# 📊 Organização e Estrutura do Banco de Dados - Atualizada 10/11/2025 (mais recente)

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
      • answering_questions: Respondendo dúvidas do paciente
      • confirming_name: Confirmando nome do paciente
      • selecting_specialty: Selecionando especialidade médica
      • selecting_doctor: Selecionando médico
      • choosing_schedule: Escolhendo horário
      • confirming: Confirmando agendamento

- previous_state: CharField(max_length=50, blank=True, null=True)
  └─ Estado anterior antes de pausar para responder dúvidas
  └─ Usado no sistema de pausar/retomar agendamento
  └─ Permite que o chatbot retome o fluxo de agendamento após responder dúvidas

- insurance_type: CharField(max_length=50, blank=True, null=True)
  └─ Tipo de convênio (ou "Particular")

- selected_specialty: CharField(max_length=100, blank=True, null=True)
  └─ Especialidade médica selecionada pelo paciente
  └─ Adicionado para melhor rastreamento de preferências

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
- is_active(): bool
  └─ Verifica se a sessão está ativa (< 24h de inatividade)
  └─ Retorna True se last_activity foi há menos de 86400 segundos (24 horas)
  
- update_activity(): None
  └─ Atualiza o timestamp da última atividade para timezone.now()
  └─ Salva apenas o campo last_activity (otimizado)
  
- __str__(): str
  └─ Retorna representação em string: "{phone_number} - {patient_name} ({current_state})"
```

**Meta:**
```python
- ordering = ['-last_activity']  # Sessões mais recentes primeiro
- verbose_name = 'Sessão de Conversa'
- verbose_name_plural = 'Sessões de Conversa'
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
  └─ Entidades extraídas da mensagem (JSON) pelo EntityExtractor do Gemini
  └─ Exemplos de entidades possíveis:
      {
        "nome_paciente": "João Silva",
        "nome_confirmado": true,
        "medico": "Dr. Gustavo",
        "especialidade": "Pneumologia",
        "data": "15/10/2024",
        "data_normalizada": "2024-10-15",
        "horario": "14:30",
        "convenio": "Unimed",
        "confianca_extracao": 0.95
      }
  └─ As entidades são extraídas primariamente pelo Gemini AI
  └─ Regex é usado como fallback para datas e horários

- timestamp: DateTimeField(auto_now_add=True)
  └─ Data/hora da mensagem
```

**Métodos:**
```python
- __str__(): str
  └─ Retorna: "{message_type_display}: {content[:50]}..."
  └─ Exemplo: "Usuário: Olá, gostaria de agendar uma consulta..."
```

**Meta:**
```python
- ordering = ['timestamp']  # Ordenação cronológica
- verbose_name = 'Mensagem da Conversa'
- verbose_name_plural = 'Mensagens da Conversa'
```

**Constantes:**
```python
MESSAGE_TYPES = [
    ('user', 'Usuário'),
    ('bot', 'Bot'),
    ('system', 'Sistema')
]
```

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
- get_especialidades_display(): str
  └─ Retorna especialidades ativas como string formatada
  └─ Formato: "Especialidade1, Especialidade2, Especialidade3"
  └─ Filtra apenas especialidades com ativa=True
  └─ Exemplo: "Pneumologia, Medicina do Sono"
  
- __str__(): str
  └─ Retorna: "{nome}"
```

**Meta:**
```python
- ordering não especificado (padrão do Django: por ID)
- verbose_name = 'Médico'
- verbose_name_plural = 'Médicos'
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

**Métodos:**
```python
- __str__(): str
  └─ Retorna: "{medico.nome} - {dia_da_semana_display}: {hora_inicio} às {hora_fim}"
  └─ Exemplo: "Dr. Gustavo - Segunda-feira: 08:00 às 12:00"
```

**Meta:**
```python
- constraints = [
    UniqueConstraint(
      fields=['medico', 'dia_da_semana', 'hora_inicio'], 
      name='unique_medico_horario'
    )
  ]
  └─ Garante que não haja horários duplicados para o mesmo médico no mesmo dia/hora
```

**Constantes:**
```python
DIA_DA_SEMANA_CHOICES = [
    (1, "Segunda-feira"),
    (2, "Terça-feira"),
    (3, "Quarta-feira"),
    (4, "Quinta-feira"),
    (5, "Sexta-feira"),
    (6, "Sábado"),
    (7, "Domingo"),
]
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

**Métodos:**
```python
- __str__(): str
  └─ Retorna: "{nome}"
  └─ Exemplo: "Polissonografia"
```

**Meta:**
```python
- ordering não especificado (padrão do Django: por ID)
- verbose_name = 'Exame'
- verbose_name_plural = 'Exames'
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

0006_alter_conversationsession_current_state.py
├─ Altera novamente as opções de current_state

0007_conversationsession_selected_specialty_and_more.py
├─ Adiciona campo selected_specialty
└─ Ajustes adicionais em campos relacionados

0008_remove_conversationsession_specialty_interest.py
├─ Remove campo specialty_interest (redundante com selected_specialty)

0009_add_question_handling.py
├─ Adiciona campo previous_state
└─ Adiciona estado 'answering_questions' ao current_state
└─ Sistema de pausar/retomar para responder dúvidas durante agendamento

0010_add_confirmed_state.py
└─ Adiciona estado 'confirming' ao current_state
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

### 1. **Índices Automáticos**
```python
# Índices criados automaticamente pelo Django:

# ConversationSession
- phone_number → UNIQUE INDEX (para busca rápida por telefone)
- last_activity → INDEX (para queries de sessões ativas)

# ConversationMessage
- session_id → INDEX (chave estrangeira)
- timestamp → INDEX (ordenação cronológica)

# Medico
- crm → UNIQUE INDEX (identificação única do médico)

# Especialidade
- nome → UNIQUE INDEX (busca rápida por nome)

# Convenio
- nome → UNIQUE INDEX (busca rápida por nome)

# HorarioTrabalho
- medico_id → INDEX (chave estrangeira)
- [medico, dia_da_semana, hora_inicio] → UNIQUE CONSTRAINT
```

### 2. **Índices Recomendados para Produção**
```python
# Adicionar via migration para melhor performance:

# ConversationSession
class Meta:
    indexes = [
        models.Index(fields=['current_state', '-last_activity']),
        models.Index(fields=['patient_name']),
        models.Index(fields=['-created_at']),
    ]

# ConversationMessage
class Meta:
    indexes = [
        models.Index(fields=['session', 'message_type']),
        models.Index(fields=['intent', '-timestamp']),
    ]
```

### 3. **Ordenação Padrão**
```python
# ConversationSession
ordering = ['-last_activity']  # Mais recentes primeiro

# ConversationMessage
ordering = ['timestamp']  # Cronológica

# Especialidade
ordering = ['nome']  # Alfabética
```

### 4. **Campos com Valores Padrão**
- Reduz necessidade de validações adicionais
- Melhora integridade dos dados
- Facilita criação de novos registros

### 5. **Relacionamentos Otimizados**
```python
# Uso de related_name para queries reversas eficientes
session.messages.all()  # Todas as mensagens da sessão
medico.horarios_trabalho.all()  # Todos os horários do médico
especialidade.medicos.all()  # Todos os médicos da especialidade
```

### 6. **Limpeza Automática de Sessões Antigas**
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

## Sistema de Cache e Performance

### Cache Inteligente
O sistema utiliza o **Django Cache Framework** para otimizar consultas frequentes:

```python
# Cache de dados da clínica (30 minutos)
CACHE_TIMEOUT_RAG = 1800  # 30 minutos

# Tipos de cache utilizados:
1. RAG_CACHE: Dados da clínica (médicos, especialidades, convênios, exames)
2. SESSION_CACHE: Sessões ativas de conversação
3. DOCTOR_CACHE: Informações de médicos específicos
4. TOKEN_CACHE: Monitoramento de uso de tokens do Gemini
```

### Estratégia de Cache
```python
# Exemplo de uso no RAGService
def get_medicos(self):
    """Obtém lista de médicos com cache"""
    cache_key = 'rag_medicos'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return cached_data
    
    # Se não está em cache, busca do banco
    medicos = Medico.objects.prefetch_related(
        'especialidades', 'convenios', 'horarios_trabalho'
    ).all()
    
    # Serializa e armazena em cache
    medicos_data = [self._serialize_medico(m) for m in medicos]
    cache.set(cache_key, medicos_data, timeout=1800)
    
    return medicos_data
```

---

## Sistema de Pausar/Retomar (Question Handling)

### Conceito
O sistema permite que o paciente **pause o agendamento** para fazer perguntas sobre a clínica, médicos ou procedimentos, e depois **retome** o agendamento de onde parou.

### Campos Envolvidos
```python
# ConversationSession
- current_state: Estado atual ('answering_questions' quando pausado)
- previous_state: Estado anterior antes de pausar (ex: 'selecting_doctor')
```

### Fluxo
```
1. Paciente está agendando (ex: current_state='selecting_doctor')
2. Paciente faz uma pergunta (ex: "Quais os horários do Dr. Gustavo?")
3. Sistema detecta intenção 'buscar_info' ou 'duvida'
4. Sistema PAUSA o agendamento:
   - previous_state = 'selecting_doctor'
   - current_state = 'answering_questions'
5. Sistema responde a pergunta
6. Paciente diz "continuar", "retomar" ou "voltar"
7. Sistema RETOMA o agendamento:
   - current_state = previous_state
   - previous_state = None
```

### Implementação
```python
# conversation_service.py

def pause_for_question(self, phone_number: str) -> bool:
    """Pausa agendamento para responder dúvida"""
    session = self.get_or_create_session(phone_number)
    
    if session.current_state not in ['idle', 'answering_questions']:
        session.previous_state = session.current_state
        session.current_state = 'answering_questions'
        session.save()
        return True
    return False

def resume_appointment(self, phone_number: str) -> bool:
    """Retoma agendamento após responder dúvida"""
    session = self.get_or_create_session(phone_number)
    
    if session.previous_state and session.current_state == 'answering_questions':
        session.current_state = session.previous_state
        session.previous_state = None
        session.save()
        return True
    return False

def has_paused_appointment(self, phone_number: str) -> bool:
    """Verifica se há agendamento pausado"""
    session = self.get_or_create_session(phone_number)
    return bool(session.previous_state)
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

## Exemplos Práticos de Uso

### 1. Criar Nova Sessão de Conversa
```python
from api_gateway.models import ConversationSession
from django.utils import timezone

# Criar nova sessão
session = ConversationSession.objects.create(
    phone_number='5573988221003',
    current_state='idle'
)

# Ou obter/criar
session, created = ConversationSession.objects.get_or_create(
    phone_number='5573988221003',
    defaults={'current_state': 'idle'}
)
```

### 2. Adicionar Mensagens à Conversa
```python
from api_gateway.models import ConversationMessage

# Mensagem do usuário
user_msg = ConversationMessage.objects.create(
    session=session,
    message_type='user',
    content='Olá, gostaria de agendar uma consulta com pneumologista',
    intent='agendar_consulta',
    confidence=0.95,
    entities={
        'especialidade': 'Pneumologia',
        'confianca_extracao': 0.95
    }
)

# Resposta do bot
bot_msg = ConversationMessage.objects.create(
    session=session,
    message_type='bot',
    content='Claro! Temos o Dr. Gustavo disponível. Qual seria seu nome?',
    intent='collecting_patient_info'
)
```

### 3. Atualizar Informações da Sessão
```python
# Atualizar dados do paciente
session.patient_name = 'João Silva'
session.name_confirmed = True
session.selected_specialty = 'Pneumologia'
session.selected_doctor = 'Dr. Gustavo'
session.preferred_date = '2024-11-15'
session.preferred_time = '14:30'
session.current_state = 'confirming'
session.save()

# Ou usar update para múltiplos campos
ConversationSession.objects.filter(
    phone_number='5573988221003'
).update(
    patient_name='João Silva',
    name_confirmed=True,
    current_state='confirming'
)
```

### 4. Consultar Histórico de Conversas
```python
# Obter últimas 10 mensagens
messages = ConversationMessage.objects.filter(
    session__phone_number='5573988221003'
).order_by('-timestamp')[:10]

# Obter apenas mensagens do usuário
user_messages = ConversationMessage.objects.filter(
    session__phone_number='5573988221003',
    message_type='user'
)

# Obter mensagens com intenção específica
agendamento_msgs = ConversationMessage.objects.filter(
    session__phone_number='5573988221003',
    intent='agendar_consulta'
)
```

### 5. Pausar e Retomar Agendamento
```python
from api_gateway.services.conversation_service import conversation_service

# Pausar para responder dúvida
conversation_service.pause_for_question('5573988221003')
# current_state muda para 'answering_questions'
# previous_state armazena o estado anterior

# Verificar se há agendamento pausado
has_paused = conversation_service.has_paused_appointment('5573988221003')

# Retomar agendamento
conversation_service.resume_appointment('5573988221003')
# current_state volta ao previous_state
# previous_state volta a None
```

### 6. Consultar Médicos por Especialidade
```python
from rag_agent.models import Medico

# Buscar médicos de uma especialidade
pneumologistas = Medico.objects.filter(
    especialidades__nome='Pneumologia',
    especialidades__ativa=True
).prefetch_related('convenios', 'horarios_trabalho')

for medico in pneumologistas:
    print(f"{medico.nome} - {medico.get_especialidades_display()}")
    print(f"Convênios: {', '.join([c.nome for c in medico.convenios.all()])}")
    print(f"Preço particular: R$ {medico.preco_particular}")
```

### 7. Verificar Horários de Trabalho
```python
from rag_agent.models import HorarioTrabalho

# Obter horários de um médico
horarios = HorarioTrabalho.objects.filter(
    medico__nome='Dr. Gustavo'
).order_by('dia_da_semana', 'hora_inicio')

for horario in horarios:
    print(horario)  # Dr. Gustavo - Segunda-feira: 08:00 às 12:00
```

### 8. Limpar Sessões Antigas
```python
from django.utils import timezone
from datetime import timedelta
from api_gateway.models import ConversationSession

# Deletar sessões inativas há mais de 7 dias
cutoff_date = timezone.now() - timedelta(days=7)
old_sessions = ConversationSession.objects.filter(
    last_activity__lt=cutoff_date
)

count = old_sessions.count()
old_sessions.delete()
print(f"{count} sessões antigas removidas")
```

### 9. Estatísticas de Conversas
```python
from django.db.models import Count, Q
from api_gateway.models import ConversationMessage

# Contar mensagens por tipo
stats = ConversationMessage.objects.values('message_type').annotate(
    total=Count('id')
)

# Contar intenções mais comuns
intents = ConversationMessage.objects.filter(
    message_type='user',
    intent__isnull=False
).values('intent').annotate(
    total=Count('id')
).order_by('-total')[:10]

# Sessões ativas hoje
from datetime import date
today = date.today()
active_today = ConversationSession.objects.filter(
    last_activity__date=today
).count()
```

### 10. Validar Especialidade Extraída
```python
from rag_agent.models import Especialidade

def validar_especialidade(nome_extraido):
    """Valida se especialidade extraída existe no banco"""
    # Busca case-insensitive
    especialidade = Especialidade.objects.filter(
        nome__iexact=nome_extraido,
        ativa=True
    ).first()
    
    if especialidade:
        return especialidade.nome  # Retorna nome correto
    
    # Busca parcial (contém)
    especialidade = Especialidade.objects.filter(
        nome__icontains=nome_extraido,
        ativa=True
    ).first()
    
    return especialidade.nome if especialidade else None

# Uso
especialidade_validada = validar_especialidade("pneumo")
# Retorna: "Pneumologia"
```

---

## Diagramas Detalhados

### Diagrama de Estados da Conversa

```
┌─────────────────────────────────────────────────────────────────┐
│                   FLUXO DE ESTADOS DA SESSÃO                    │
└─────────────────────────────────────────────────────────────────┘

                           ┌──────┐
                           │ idle │ ◄─── Estado inicial
                           └───┬──┘
                               │
                    Intenção: agendar_consulta
                               │
                               ▼
                ┌──────────────────────────┐
                │ collecting_patient_info  │ ◄─── Coleta nome
                └──────────┬───────────────┘
                           │
                    Nome extraído
                           │
                           ▼
                ┌─────────────────┐
                │ confirming_name │ ◄─── Confirma nome
                └────────┬────────┘
                         │
                  Nome confirmado
                         │
                         ▼
              ┌────────────────────┐
              │ selecting_specialty│ ◄─── Escolhe especialidade
              └─────────┬──────────┘
                        │
              Especialidade selecionada
                        │
                        ▼
              ┌──────────────────┐
              │ selecting_doctor │ ◄─── Escolhe médico
              └────────┬─────────┘
                       │
             ┌─────────┴─────────┐
             │                   │
       Médico selecionado    Pergunta/Dúvida
             │                   │
             ▼                   ▼
    ┌─────────────────┐  ┌────────────────────┐
    │ choosing_schedule│  │ answering_questions│◄─── Pausa agendamento
    └────────┬────────┘  └─────────┬──────────┘
             │                      │
    Data/hora escolhida      "continuar"/"retomar"
             │                      │
             │                      │
             └──────────┬───────────┘
                        │
                        ▼
                ┌──────────────┐
                │ confirming   │ ◄─── Confirma tudo
                └──────────────┘
```

### Diagrama Entidade-Relacionamento Detalhado

```
┌────────────────────────────────────────────────────────────────┐
│                  MODELO DE DADOS COMPLETO                      │
└────────────────────────────────────────────────────────────────┘

┌──────────────────────────┐
│   ConversationSession    │
├──────────────────────────┤
│ PK  phone_number         │
│     patient_name         │
│     pending_name         │
│     name_confirmed       │
│     current_state        │◄──┐
│     previous_state       │   │ Sistema pausar/retomar
│     insurance_type       │   │
│     preferred_date       │   │
│     preferred_time       │   │
│     selected_doctor      │   │
│     selected_specialty   │   │
│     additional_notes     │   │
│     created_at           │   │
│     updated_at           │   │
│     last_activity        │   │
└──────────┬───────────────┘   │
           │ 1                 │
           │                   │
           │ N                 │
           ▼                   │
┌──────────────────────────┐   │
│   ConversationMessage    │   │
├──────────────────────────┤   │
│ PK  id                   │   │
│ FK  session_id           │───┘
│     message_type         │
│     content              │
│     intent               │
│     confidence           │
│     entities (JSON)      │
│     timestamp            │
└──────────────────────────┘


┌──────────────────────┐        ┌──────────────────────┐
│   Especialidade      │   N:M  │      Medico          │
├──────────────────────┤◄───────┤──────────────────────┤
│ PK  id               │        │ PK  id               │
│     nome (unique)    │        │     nome             │
│     descricao        │        │     crm (unique)     │
│     ativa            │        │     bio              │
└──────────────────────┘        │     preco_particular │
                                │     formas_pagamento │
                                │     retorno_info     │
                                └──────────┬───────────┘
                                           │ 1
                                           │
                   ┌───────────────────────┼───────────────────────┐
                   │ N                     │ N                     │ 1
                   ▼                       ▼                       ▼
        ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
        │    Convenio      │   │  HorarioTrabalho │   │   ClinicaInfo    │
        ├──────────────────┤   ├──────────────────┤   ├──────────────────┤
        │ PK  id           │   │ PK  id           │   │ PK  id           │
        │     nome (unique)│   │ FK  medico_id    │   │     nome         │
        │     descricao    │   │     dia_da_semana│   │     objetivo_geral│
        └──────────────────┘   │     hora_inicio  │   │     secretaria   │
                               │     hora_fim     │   │     telefone     │
                               └──────────────────┘   │     whatsapp     │
                                                      │     email        │
                                                      │     endereco     │
                                                      │     referencia   │
                                                      │     politica     │
                                                      │     calendar_id  │
                                                      └──────────────────┘

        ┌──────────────────┐
        │      Exame       │
        ├──────────────────┤
        │ PK  id           │
        │     nome         │
        │     o_que_e      │
        │     como_funciona│
        │     preparacao   │
        │     vantagem     │
        │     preco        │
        │     duracao      │
        └──────────────────┘
```

---

**Última Atualização:** Novembro 10, 2025  
**Versão:** 2.0  
**Autor:** Sistema de Documentação Automatizada  
**Status:** ✅ Atualizado e Validado com o Código Atual

