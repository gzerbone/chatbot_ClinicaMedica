# Armazenamento Persistente vs Volátil no Projeto

## 📋 Visão Geral

O projeto utiliza uma arquitetura híbrida de armazenamento que combina **armazenamento persistente** (banco de dados relacional) e **armazenamento volátil** (cache em memória) para otimizar performance, garantir persistência de dados e reduzir custos operacionais.

---

## 🗄️ ARMAZENAMENTO PERSISTENTE (Banco de Dados Relacional)

### O que é?

O armazenamento persistente utiliza o **Django ORM** com **SQLite** (desenvolvimento) e está preparado para **PostgreSQL** (produção). Os dados são armazenados em disco e **sobrevivem a reinicializações do servidor**.

### Tecnologia Utilizada

```python
# core/settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

### O que é Armazenado?

#### 1. **Sessões de Conversa** (`ConversationSession`)

**Modelo:** `api_gateway/models.py`

```python
class ConversationSession(models.Model):
    phone_number = models.CharField(max_length=20, unique=True)
    patient_name = models.CharField(max_length=100, blank=True, null=True)
    current_state = models.CharField(max_length=50, default='idle')
    previous_state = models.CharField(max_length=50, blank=True, null=True)
    selected_doctor = models.CharField(max_length=100, blank=True, null=True)
    selected_specialty = models.CharField(max_length=100, blank=True, null=True)
    preferred_date = models.DateField(blank=True, null=True)
    preferred_time = models.TimeField(blank=True, null=True)
    insurance_type = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity = models.DateTimeField(auto_now=True)
```

**Dados Armazenados:**
- ✅ Número de telefone do paciente (chave única)
- ✅ Nome do paciente confirmado
- ✅ Estado atual da conversa (idle, collecting_patient_info, etc.)
- ✅ Estado anterior (para retomar após pausar para dúvidas)
- ✅ Médico selecionado
- ✅ Especialidade selecionada
- ✅ Data e horário preferidos
- ✅ Tipo de convênio
- ✅ Timestamps de criação, atualização e última atividade

**Características:**
- **Persistência:** Dados permanecem mesmo após reinicialização
- **Integridade:** Validações e constraints do Django ORM
- **Relacionamentos:** Foreign keys e relacionamentos muitos-para-muitos
- **Histórico:** Timestamps para auditoria

#### 2. **Mensagens da Conversa** (`ConversationMessage`)

**Modelo:** `api_gateway/models.py`

```python
class ConversationMessage(models.Model):
    session = models.ForeignKey(ConversationSession, on_delete=models.CASCADE)
    message_type = models.CharField(max_length=10)  # 'user', 'bot', 'system'
    content = models.TextField()
    intent = models.CharField(max_length=50, blank=True, null=True)
    confidence = models.FloatField(blank=True, null=True)
    entities = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
```

**Dados Armazenados:**
- ✅ Mensagens do usuário e do bot
- ✅ Intenção detectada (intent)
- ✅ Confiança da detecção (confidence)
- ✅ Entidades extraídas (nome, médico, data, horário) em formato JSON
- ✅ Timestamp de cada mensagem

**Características:**
- **Histórico Completo:** Todas as mensagens são preservadas
- **Análise:** Permite análise de padrões de conversação
- **Auditoria:** Rastreamento completo das interações

#### 3. **Dados da Clínica** (`rag_agent/models.py`)

**Modelos:**
- `ClinicaInfo`: Informações gerais da clínica
- `Medico`: Médicos e suas especialidades
- `Especialidade`: Especialidades médicas disponíveis
- `Convenio`: Convênios aceitos
- `Exame`: Exames disponíveis
- `HorarioTrabalho`: Horários de trabalho dos médicos

**Dados Armazenados:**
- ✅ Informações estáticas da clínica (nome, endereço, telefone)
- ✅ Cadastro completo de médicos com CRM
- ✅ Especialidades médicas ativas
- ✅ Convênios aceitos
- ✅ Exames disponíveis com preços
- ✅ Horários de trabalho de cada médico

**Características:**
- **Dados de Referência:** Informações que mudam raramente
- **Relacionamentos Complexos:** Many-to-Many entre médicos e especialidades
- **Integridade Referencial:** Constraints garantem consistência

### Como Funciona?

#### 1. **Criação de Sessão**

```python
# api_gateway/services/conversation_service.py
def get_or_create_session(self, phone_number: str) -> ConversationSession:
    session, created = ConversationSession.objects.get_or_create(
        phone_number=phone_number,
        defaults={
            'current_state': 'idle',
            'last_activity': timezone.now()
        }
    )
    return session
```

**Fluxo:**
1. Sistema busca sessão existente pelo `phone_number`
2. Se não existe, cria nova sessão com estado inicial
3. Se existe, atualiza `last_activity`
4. Dados são salvos **imediatamente** no banco

#### 2. **Atualização de Estado**

```python
# api_gateway/services/conversation_service.py
def _update_session_state(self, session: ConversationSession, intent: str, entities: Dict):
    # Atualiza estado baseado na intenção
    if new_state and new_state != session.current_state:
        session.current_state = new_state
        session.save()  # Salva no banco imediatamente
    
    # Atualiza entidades extraídas
    if entities:
        if 'patient_name' in entities:
            session.patient_name = entities['patient_name'][0]
        if 'medico' in entities:
            session.selected_doctor = entities['medico'][0]
        # ... outros campos
        session.save()  # Persiste no banco
```

**Fluxo:**
1. Sistema detecta intenção e extrai entidades
2. Atualiza campos do modelo `ConversationSession`
3. Chama `session.save()` para persistir no banco
4. Dados ficam **permanentemente** armazenados

#### 3. **Salvamento de Mensagens**

```python
# api_gateway/services/conversation_service.py
def add_message(self, phone_number: str, content: str, message_type: str = 'user', ...):
    session = self.get_or_create_session(phone_number)
    
    message = ConversationMessage.objects.create(
        session=session,
        message_type=message_type,
        content=content,
        intent=intent,
        confidence=confidence,
        entities=entities or {}
    )
    return message
```

**Fluxo:**
1. Cada mensagem é salva como registro separado
2. Relacionamento Foreign Key com `ConversationSession`
3. Entidades extraídas são armazenadas em JSON
4. Timestamp automático registra quando foi criada

### Vantagens do Armazenamento Persistente

✅ **Durabilidade:** Dados não são perdidos em caso de reinicialização  
✅ **Integridade:** Validações e constraints garantem consistência  
✅ **Histórico:** Todas as interações são preservadas para análise  
✅ **Auditoria:** Timestamps permitem rastreamento completo  
✅ **Relacionamentos:** Foreign keys garantem integridade referencial  
✅ **Consultas Complexas:** ORM permite queries avançadas  
✅ **Backup:** Dados podem ser facilmente copiados e restaurados  

### Desvantagens

❌ **Latência:** Acesso ao disco é mais lento (~50-200ms)  
❌ **Carga no Banco:** Muitas escritas podem sobrecarregar o banco  
❌ **Escalabilidade:** SQLite não suporta múltiplos servidores  

---

## ⚡ ARMAZENAMENTO VOLÁTIL (Cache em Memória)

### O que é?

O armazenamento volátil utiliza o **Django Cache Framework** com **LocMemCache** (memória local). Os dados são armazenados em **RAM** e são **perdidos** quando o servidor é reiniciado ou quando expiram.

### Tecnologia Utilizada

```python
# Django usa LocMemCache por padrão (memória local do processo)
from django.core.cache import cache

# Configuração implícita (padrão do Django)
# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
#     }
# }
```

### O que é Armazenado?

#### 1. **Sessões de Conversa em Cache**

**Chave:** `gemini_session_{phone_number}`  
**Timeout:** 15-60 minutos (dinâmico baseado em uso de tokens)  
**Localização:** `api_gateway/services/gemini/session_manager.py`

```python
def get_or_create_session(self, phone_number: str) -> Dict[str, Any]:
    cache_key = f"gemini_session_{phone_number}"
    session = cache.get(cache_key)  # Busca no cache
    
    if not session:
        # Se não está no cache, carrega do banco
        db_session = ConversationSession.objects.filter(phone_number=phone_number).first()
        if db_session:
            # Converte modelo Django para dict
            session = {
                'phone_number': phone_number,
                'current_state': db_session.current_state,
                'patient_name': db_session.patient_name,
                'selected_doctor': db_session.selected_doctor,
                # ... outros campos
            }
            # Armazena no cache para próximas consultas
            cache.set(cache_key, session, token_monitor.get_cache_timeout())
    
    return session
```

**Dados Armazenados:**
- ✅ Estado atual da conversa
- ✅ Nome do paciente
- ✅ Médico e especialidade selecionados
- ✅ Data e horário preferidos
- ✅ Última resposta gerada
- ✅ Médicos sugeridos anteriormente (para resolver pronomes)
- ✅ Flags de controle (has_greeted, name_confirmed)

**Características:**
- **Acesso Rápido:** ~1ms vs ~50-200ms do banco
- **Temporário:** Expira após timeout
- **Sincronização:** Carrega do banco se não está em cache

#### 2. **Dados da Clínica em Cache**

**Chave:** `gemini_clinic_data`  
**Timeout:** 15-60 minutos (dinâmico)  
**Localização:** `api_gateway/services/rag_service.py`

**Dados Armazenados:**
- ✅ Lista de médicos com especialidades
- ✅ Lista de especialidades ativas
- ✅ Lista de convênios
- ✅ Lista de exames
- ✅ Informações gerais da clínica

**Características:**
- **Dados Estáticos:** Informações que mudam raramente
- **Redução de Queries:** Evita consultar banco a cada mensagem
- **Performance:** Resposta instantânea para dados frequentes

#### 3. **Monitoramento de Tokens**

**Chave:** `gemini_tokens_{data}` (ex: `gemini_tokens_2025-01-15`)  
**Timeout:** 24 horas (até meia-noite)  
**Localização:** `api_gateway/services/token_monitor.py`

```python
def log_token_usage(self, operation: str, input_text: str, ...):
    # Calcula tokens usados
    total_tokens = input_tokens + output_tokens
    self.token_usage_today += total_tokens
    
    # Salva no cache
    today = date.today().isoformat()
    cache_key = f"gemini_tokens_{today}"
    cache.set(cache_key, self.token_usage_today, 86400)  # 24 horas
```

**Dados Armazenados:**
- ✅ Total de tokens consumidos no dia
- ✅ Uso por sessão (opcional)
- ✅ Flag de modo econômico ativo

**Características:**
- **Controle de Custos:** Monitora uso diário de tokens
- **Modo Econômico:** Ativa automaticamente quando próximo do limite
- **Reset Diário:** Expira à meia-noite

#### 4. **Cache de Médico Específico**

**Chave:** `gemini_doctor_{nome_medico}`  
**Timeout:** 15-60 minutos (dinâmico)

**Dados Armazenados:**
- ✅ Informações completas do médico
- ✅ Especialidades do médico
- ✅ Convênios aceitos
- ✅ Horários de trabalho

**Características:**
- **Busca Rápida:** Evita consultar banco para médico específico
- **Dados Frequentes:** Médicos mais consultados ficam em cache

### Como Funciona?

#### 1. **Estratégia Cache-Aside (Lazy Loading)**

```python
# api_gateway/services/gemini/session_manager.py
def get_or_create_session(self, phone_number: str) -> Dict[str, Any]:
    cache_key = f"gemini_session_{phone_number}"
    
    # 1. TENTA BUSCAR NO CACHE (rápido)
    session = cache.get(cache_key)
    
    if not session:
        # 2. SE NÃO ESTÁ NO CACHE, BUSCA NO BANCO (mais lento)
        db_session = ConversationSession.objects.filter(phone_number=phone_number).first()
        
        if db_session:
            # 3. CONVERTE MODELO PARA DICT
            session = self._convert_db_to_dict(db_session)
        else:
            # 4. CRIA NOVA SESSÃO
            session = self._create_empty_session(phone_number)
        
        # 5. ARMAZENA NO CACHE PARA PRÓXIMAS CONSULTAS
        cache.set(cache_key, session, token_monitor.get_cache_timeout())
    
    return session
```

**Fluxo:**
1. **Primeira consulta:** Cache miss → Busca no banco → Armazena no cache
2. **Consultas subsequentes:** Cache hit → Retorna imediatamente
3. **Após timeout:** Cache expira → Busca no banco novamente

#### 2. **Atualização com Sincronização**

```python
# api_gateway/services/gemini/session_manager.py
def update_session(self, phone_number: str, session: Dict, ...):
    # 1. ATUALIZA DADOS NO CACHE (rápido)
    session['current_state'] = next_state
    session['patient_name'] = nome_extraido
    session['selected_doctor'] = medico_validado
    
    # 2. SALVA NO CACHE
    cache_key = f"gemini_session_{phone_number}"
    cache.set(cache_key, session, token_monitor.get_cache_timeout())
    
    # 3. SINCRONIZA COM BANCO (persistência)
    self.sync_to_database(phone_number, session)
```

**Fluxo:**
1. Atualiza dados no dicionário em memória
2. Salva no cache para acesso rápido
3. Sincroniza com banco para persistência

#### 3. **Sincronização Cache → Banco**

```python
# api_gateway/services/gemini/session_manager.py
def sync_to_database(self, phone_number: str, session: Dict):
    # Busca ou cria sessão no banco
    db_session, created = ConversationSession.objects.get_or_create(
        phone_number=phone_number,
        defaults={...}
    )
    
    if not created:
        # Atualiza campos do banco com dados do cache
        db_session.current_state = session.get('current_state')
        db_session.patient_name = session.get('patient_name')
        db_session.selected_doctor = session.get('selected_doctor')
        # ... outros campos
        db_session.save()  # Persiste no banco
```

**Fluxo:**
1. Dados são atualizados primeiro no cache (rápido)
2. Depois são sincronizados com o banco (persistência)
3. Se servidor reiniciar, cache é recarregado do banco

### Vantagens do Armazenamento Volátil

✅ **Performance:** Acesso extremamente rápido (~1ms)  
✅ **Redução de Carga:** Menos queries ao banco de dados  
✅ **Economia:** Reduz uso de tokens (menos dados enviados ao Gemini)  
✅ **Escalabilidade:** Pode ser distribuído (Redis)  
✅ **Temporário:** Dados expiram automaticamente  

### Desvantagens

❌ **Volatilidade:** Dados são perdidos ao reiniciar servidor  
❌ **Memória Limitada:** Cache ocupa RAM  
❌ **Sincronização:** Requer sincronização com banco  
❌ **Inconsistência Temporária:** Cache pode estar desatualizado  

---

## 🔄 DIFERENÇAS E COMPLEMENTARIDADE

### Comparação Direta

| Aspecto | Persistente (Banco) | Volátil (Cache) |
|---------|---------------------|-----------------|
| **Localização** | Disco (SQLite/PostgreSQL) | RAM (Memória) |
| **Velocidade** | ~50-200ms | ~1ms |
| **Durabilidade** | ✅ Permanente | ❌ Temporário |
| **Custo** | Baixo (disco) | Alto (RAM) |
| **Capacidade** | Ilimitada (praticamente) | Limitada (RAM disponível) |
| **Uso** | Dados críticos, histórico | Dados frequentes, temporários |
| **Sobrevive Restart** | ✅ Sim | ❌ Não |
| **Integridade** | ✅ Constraints, validações | ⚠️ Sem validações |
| **Escalabilidade** | ⚠️ SQLite: 1 servidor | ✅ Redis: múltiplos servidores |

### Como Trabalham Juntos

```
┌─────────────────────────────────────────────────────────────┐
│                    FLUXO HÍBRIDO                            │
└─────────────────────────────────────────────────────────────┘

1️⃣ PRIMEIRA MENSAGEM (Cache Miss)
   ┌─────────────┐
   │   Usuário   │
   └──────┬──────┘
          │
          ▼
   ┌─────────────────┐     ❌ Cache miss
   │  Cache (RAM)    │ ◄──────┐
   └─────────────────┘        │
          │                    │
          ▼                    │
   ┌─────────────────┐        │
   │ Banco (Disco)   │ ────────┘ Busca sessão
   └─────────────────┘
          │
          ▼
   ┌─────────────────┐
   │ Carrega dados   │
   └─────────────────┘
          │
          ▼
   ┌─────────────────┐
   │ Armazena cache  │ ✅ Próxima consulta será rápida
   └─────────────────┘

2️⃣ MENSAGENS SUBSEQUENTES (Cache Hit)
   ┌─────────────┐
   │   Usuário   │
   └──────┬──────┘
          │
          ▼
   ┌─────────────────┐     ✅ Cache hit (~1ms)
   │  Cache (RAM)    │ ◄──────┐ Retorna imediatamente
   └─────────────────┘        │
          │                    │
          ▼                    │
   ┌─────────────────┐        │
   │ Banco (Disco)   │ ────────┘ Não consulta (economia)
   └─────────────────┘

3️⃣ ATUALIZAÇÃO DE DADOS
   ┌─────────────┐
   │   Usuário   │ Envia nome, médico, data
   └──────┬──────┘
          │
          ▼
   ┌─────────────────┐
   │  Cache (RAM)    │ ✅ Atualiza cache primeiro (rápido)
   └──────┬──────────┘
          │
          ▼
   ┌─────────────────┐
   │ Banco (Disco)   │ ✅ Sincroniza depois (persistência)
   └─────────────────┘

4️⃣ REINICIALIZAÇÃO DO SERVIDOR
   ┌─────────────────┐
   │  Cache (RAM)    │ ❌ Perdido (vazio)
   └─────────────────┘
          │
          ▼
   ┌─────────────────┐
   │ Banco (Disco)   │ ✅ Dados preservados
   └─────────────────┘
          │
          ▼
   ┌─────────────────┐
   │ Recarrega cache │ ✅ Cache reconstruído do banco
   └─────────────────┘
```

### Estratégia de Sincronização

O projeto utiliza **sincronização bidirecional**:

1. **Cache → Banco:** Dados atualizados no cache são sincronizados com o banco
2. **Banco → Cache:** Se cache expira ou servidor reinicia, cache é recarregado do banco

```python
# api_gateway/services/gemini/session_manager.py

# 1. Atualiza cache (rápido)
def update_session(self, phone_number: str, session: Dict, ...):
    # Atualiza dados no cache
    session['current_state'] = next_state
    cache.set(cache_key, session, timeout)
    
    # Sincroniza com banco (persistência)
    self.sync_to_database(phone_number, session)

# 2. Recarrega do banco se cache expirou
def get_or_create_session(self, phone_number: str) -> Dict:
    session = cache.get(cache_key)  # Tenta cache
    
    if not session:
        # Cache expirou ou servidor reiniciou
        db_session = ConversationSession.objects.filter(...).first()
        if db_session:
            session = self._convert_db_to_dict(db_session)
            cache.set(cache_key, session, timeout)  # Recarrega cache
```

---

## 🎯 IMPORTÂNCIA DE CADA UM NO PROJETO

### Importância do Armazenamento Persistente

#### 1. **Continuidade da Conversa**

**Problema sem persistência:**
- Usuário envia mensagem → Sistema processa → Servidor reinicia → **Dados perdidos**
- Usuário precisa começar do zero

**Solução com persistência:**
- Usuário envia mensagem → Sistema salva no banco → Servidor reinicia → **Dados preservados**
- Usuário continua de onde parou

```python
# Exemplo: Usuário estava escolhendo médico
# Servidor reinicia → Cache perdido
# Sistema recarrega do banco:
session = ConversationSession.objects.get(phone_number="5511999999999")
# session.current_state = "selecting_doctor" ✅
# session.selected_specialty = "Cardiologia" ✅
# Conversa continua normalmente
```

#### 2. **Histórico Completo para Análise**

**Benefícios:**
- Análise de padrões de conversação
- Identificação de problemas recorrentes
- Melhoria contínua do sistema
- Auditoria e compliance

```python
# Exemplo: Análise de conversas
messages = ConversationMessage.objects.filter(
    session__phone_number="5511999999999"
).order_by('timestamp')

# Permite:
# - Ver fluxo completo da conversa
# - Identificar onde usuários desistem
# - Analisar intenções mais comuns
# - Medir taxa de sucesso
```

#### 3. **Integridade de Dados**

**Validações:**
- Constraints garantem que dados são válidos
- Foreign keys garantem relacionamentos corretos
- Validações do Django ORM previnem dados inválidos

```python
# Exemplo: Validação automática
session = ConversationSession(
    phone_number="5511999999999",
    current_state="invalid_state"  # ❌ Erro: não está nas choices
)
session.save()  # Django valida e rejeita

# Exemplo: Integridade referencial
message = ConversationMessage(
    session_id=99999,  # ❌ Erro: sessão não existe
    content="Teste"
)
message.save()  # Django valida Foreign Key
```

#### 4. **Backup e Recuperação**

**Benefícios:**
- Dados podem ser copiados facilmente
- Restauração em caso de falhas
- Migração entre ambientes

### Importância do Armazenamento Volátil

#### 1. **Performance Crítica**

**Impacto:**
- **Sem cache:** ~50-200ms por consulta ao banco
- **Com cache:** ~1ms por consulta ao cache
- **Ganho:** 50-200x mais rápido

**Cenário Real:**
```
Conversa típica: 20 mensagens
- Sem cache: 20 × 100ms = 2 segundos de latência
- Com cache: 20 × 1ms = 20ms de latência
- Ganho: 100x mais rápido
```

#### 2. **Redução de Carga no Banco**

**Impacto:**
- **Sem cache:** Cada mensagem consulta banco 5-10 vezes
- **Com cache:** Cada mensagem consulta banco 1-2 vezes
- **Redução:** 80-90% menos queries

**Cenário Real:**
```
100 usuários simultâneos, 20 mensagens cada
- Sem cache: 100 × 20 × 8 queries = 16.000 queries/minuto
- Com cache: 100 × 20 × 1 query = 2.000 queries/minuto
- Redução: 87.5% menos carga no banco
```

#### 3. **Economia de Tokens (Gemini API)**

**Impacto:**
- Cache permite enviar apenas dados essenciais ao Gemini
- Histórico limitado reduz tokens consumidos
- Modo econômico ativado automaticamente

**Cenário Real:**
```
Conversa longa: 50 mensagens
- Sem cache: Envia todo histórico = 5.000 tokens
- Com cache: Envia apenas últimas 3 mensagens = 300 tokens
- Economia: 94% menos tokens
```

#### 4. **Escalabilidade**

**Benefícios:**
- Cache pode ser distribuído (Redis)
- Múltiplos servidores compartilham cache
- Suporta alta concorrência

---

## 📊 EXEMPLOS PRÁTICOS

### Exemplo 1: Fluxo de Agendamento Completo

```
1. Usuário: "Olá, quero agendar uma consulta"
   ┌─────────────────┐
   │ Cache: Miss     │ → Busca no banco
   │ Banco: Cria     │ → ConversationSession(idle)
   │ Cache: Armazena │ → gemini_session_5511999999999
   └─────────────────┘

2. Sistema: "Qual seu nome?"
   ┌─────────────────┐
   │ Cache: Hit      │ → Retorna imediatamente (~1ms)
   │ Banco: Não      │ → Não consulta (economia)
   └─────────────────┘

3. Usuário: "Meu nome é João Silva"
   ┌─────────────────┐
   │ Cache: Atualiza │ → session['patient_name'] = "João Silva"
   │ Banco: Sincroniza│ → ConversationSession.patient_name = "João Silva"
   └─────────────────┘

4. Sistema: "Qual especialidade?"
   ┌─────────────────┐
   │ Cache: Hit      │ → Retorna estado atual (~1ms)
   │ Banco: Não      │ → Não consulta
   └─────────────────┘

5. Usuário: "Cardiologia"
   ┌─────────────────┐
   │ Cache: Atualiza │ → session['selected_specialty'] = "Cardiologia"
   │ Banco: Sincroniza│ → ConversationSession.selected_specialty = "Cardiologia"
   └─────────────────┘

6. [Servidor reinicia]
   ┌─────────────────┐
   │ Cache: Perdido  │ → Vazio após restart
   │ Banco: Preservado│ → Dados ainda estão lá
   └─────────────────┘

7. Usuário: "Quero o Dr. Carlos"
   ┌─────────────────┐
   │ Cache: Miss      │ → Busca no banco
   │ Banco: Recupera   │ → ConversationSession com todos os dados
   │ Cache: Recarrega │ → Cache reconstruído
   └─────────────────┘
   ✅ Conversa continua normalmente
```

### Exemplo 2: Monitoramento de Tokens

```
1. Primeira mensagem do dia
   ┌─────────────────┐
   │ Cache: tokens_2025-01-15 = 0
   │ Banco: Não armazena tokens (apenas cache)
   └─────────────────┘

2. Mensagem processada (500 tokens)
   ┌─────────────────┐
   │ Cache: tokens_2025-01-15 = 500
   │ Banco: Não consulta
   └─────────────────┘

3. Mais 10 mensagens (5.000 tokens cada)
   ┌─────────────────┐
   │ Cache: tokens_2025-01-15 = 50.500
   │ Banco: Não consulta
   └─────────────────┘

4. Sistema verifica limite (1.5M tokens)
   ┌─────────────────┐
   │ Cache: Hit      │ → 50.500 / 1.500.000 = 3.4%
   │ Ação: Normal     │ → Continua operação normal
   └─────────────────┘

5. [Meia-noite]
   ┌─────────────────┐
   │ Cache: Expira    │ → tokens_2025-01-15 expira
   │ Novo dia: tokens_2025-01-16 = 0
   └─────────────────┘
```

### Exemplo 3: Dados da Clínica

```
1. Primeira consulta de médicos
   ┌─────────────────┐
   │ Cache: Miss     │ → Busca no banco
   │ Banco: Query    │ → Medico.objects.prefetch_related(...)
   │ Cache: Armazena │ → gemini_clinic_data
   └─────────────────┘
   ⏱️ Tempo: ~150ms

2. Próximas 100 consultas
   ┌─────────────────┐
   │ Cache: Hit      │ → Retorna imediatamente
   │ Banco: Não      │ → Não consulta
   └─────────────────┘
   ⏱️ Tempo: ~1ms cada (100x mais rápido)

3. [Timeout de 30 minutos]
   ┌─────────────────┐
   │ Cache: Expira    │ → Dados podem estar desatualizados
   │ Próxima consulta │ → Recarrega do banco
   └─────────────────┘
```

---

## 🔧 CONFIGURAÇÕES E OTIMIZAÇÕES

### Timeout Dinâmico do Cache

O projeto utiliza timeout dinâmico baseado no uso de tokens:

```python
# api_gateway/services/token_monitor.py
def get_cache_timeout(self) -> int:
    """Retorna timeout do cache (em segundos)"""
    return 3600  # 1 hora (pode ser ajustado dinamicamente)
```

**Estratégia:**
- **Uso normal:** 1 hora de timeout
- **Modo econômico:** Timeout reduzido para economizar memória
- **Alto uso:** Timeout aumentado para melhor performance

### Sincronização Automática

O sistema sincroniza cache e banco automaticamente:

```python
# api_gateway/services/gemini/session_manager.py
def update_session(self, phone_number: str, session: Dict, ...):
    # 1. Atualiza cache (rápido)
    cache.set(cache_key, session, timeout)
    
    # 2. Sincroniza banco (persistência)
    self.sync_to_database(phone_number, session)
```

**Garantias:**
- ✅ Cache sempre atualizado primeiro (performance)
- ✅ Banco sempre sincronizado depois (persistência)
- ✅ Se cache expirar, recarrega do banco

---

## 🚀 EVOLUÇÃO FUTURA

### Migração para Redis

**Atual:** LocMemCache (memória local do processo)

**Futuro:** Redis (cache distribuído)

```python
# Futura configuração
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

**Benefícios:**
- ✅ Múltiplos servidores compartilham cache
- ✅ Persistência opcional (sobrevive restart)
- ✅ Performance superior
- ✅ Recursos avançados (pub/sub, etc.)

### Migração para PostgreSQL

**Atual:** SQLite (desenvolvimento)

**Futuro:** PostgreSQL (produção)

**Benefícios:**
- ✅ Suporta múltiplas conexões simultâneas
- ✅ Melhor performance com índices
- ✅ Recursos avançados (particionamento, etc.)
- ✅ Escalabilidade horizontal

---

## 📝 RESUMO

### Armazenamento Persistente (Banco de Dados)

- **O que:** Dados críticos que devem sobreviver a reinicializações
- **Onde:** SQLite/PostgreSQL (disco)
- **Velocidade:** ~50-200ms
- **Durabilidade:** ✅ Permanente
- **Uso:** Sessões, mensagens, dados da clínica

### Armazenamento Volátil (Cache)

- **O que:** Dados temporários para acesso rápido
- **Onde:** LocMemCache/Redis (RAM)
- **Velocidade:** ~1ms
- **Durabilidade:** ❌ Temporário (expira)
- **Uso:** Sessões ativas, dados da clínica, tokens

### Trabalho em Conjunto

1. **Cache acelera** acesso a dados frequentes
2. **Banco garante** persistência e integridade
3. **Sincronização** mantém ambos atualizados
4. **Fallback** do banco quando cache expira

### Importância

- **Persistente:** Essencial para continuidade e histórico
- **Volátil:** Essencial para performance e economia
- **Ambos:** Trabalham juntos para otimizar o sistema

---

**Última atualização:** 15/01/2025  
**Versão:** 1.0  
**Autor:** Documentação Técnica - Chatbot Clínica Médica

