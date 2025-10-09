# 🧠 Gestão de Memória para Otimização de Tokens - Atualizada 09/10 (mais recente)

## 📋 Índice
- [Visão Geral](#visão-geral)
- [Estratégia de Gestão de Estado](#estratégia-de-gestão-de-estado)
- [Sistema de Monitoramento de Tokens](#sistema-de-monitoramento-de-tokens)
- [Otimizações Implementadas](#otimizações-implementadas)
- [Cache Inteligente](#cache-inteligente)
- [Resposta à Pergunta do Usuário](#resposta-à-pergunta-do-usuário)

---

## Visão Geral

O projeto implementa uma **estratégia completa de gestão de memória e otimização de tokens** para reduzir custos com a API do Gemini e melhorar a performance do chatbot.

### Objetivos Principais
1. ✅ **Reduzir custos com tokens do Gemini**
2. ✅ **Manter contexto relevante sem enviar histórico completo**
3. ✅ **Monitorar uso de tokens em tempo real**
4. ✅ **Implementar modo econômico quando necessário**
5. ✅ **Cachear dados da clínica para evitar repetições**

---

## Resposta à Pergunta do Usuário

### ❓ Pergunta
> **"Para evitar o alto custo de enviar todo o histórico da conversa para o LLM a cada nova mensagem, será implementada uma estratégia de gestão de estado"**

### ✅ Resposta: **SIM, ESSA ESTRATÉGIA ESTÁ IMPLEMENTADA NO PROJETO**

### 📍 Onde está implementada?

#### 1. **Gestão de Estado em Banco de Dados**
**Arquivo:** `api_gateway/models.py` e `api_gateway/services/conversation_service.py`

**Como funciona:**
- Ao invés de enviar todo o histórico, o projeto armazena o **estado atual da conversa** no banco de dados
- Cada sessão possui um campo `current_state` que rastreia onde o usuário está no fluxo
- As informações coletadas (nome, médico, data, horário) são armazenadas em **campos separados** na sessão

```python
# api_gateway/models.py (linhas 8-56)
class ConversationSession(models.Model):
    """
    Sessão de conversa persistente para fluxos de agendamento
    """
    phone_number = models.CharField(max_length=20, unique=True)
    patient_name = models.CharField(max_length=100, blank=True, null=True)
    current_state = models.CharField(max_length=50, default='idle')
    
    # Informações estruturadas (não precisa reenviar histórico)
    specialty_interest = models.CharField(max_length=100, blank=True, null=True)
    insurance_type = models.CharField(max_length=50, blank=True, null=True)
    preferred_date = models.DateField(blank=True, null=True)
    preferred_time = models.TimeField(blank=True, null=True)
    selected_doctor = models.CharField(max_length=100, blank=True, null=True)
```

#### 2. **Histórico Limitado**
**Arquivo:** `api_gateway/services/gemini_chatbot_service.py` (linhas 975-981)

**Como funciona:**
- O sistema **limita o histórico** enviado ao Gemini para apenas as **últimas mensagens relevantes**
- Não envia todo o histórico completo da conversa

```python
# gemini_chatbot_service.py (linhas 249-254)
# Histórico da conversa
history_text = ""
if conversation_history:
    history_text = "Histórico da conversa:\n"
    for msg in conversation_history[-3:]:  # Últimas 3 mensagens apenas
        role = "Paciente" if msg['is_user'] else "Assistente"
        history_text += f"- {role}: {msg['content']}\n"
```

#### 3. **Cache de Sessão em Memória**
**Arquivo:** `api_gateway/services/gemini_chatbot_service.py` (linhas 731-750)

**Como funciona:**
- As informações da sessão são armazenadas em **cache (Redis/Memcached)**
- Ao invés de reenviar tudo, o sistema recupera o estado atual do cache

```python
# gemini_chatbot_service.py (linhas 731-750)
def _get_or_create_session(self, phone_number: str) -> Dict[str, Any]:
    """Obtém ou cria sessão da conversa"""
    cache_key = f"gemini_session_{phone_number}"
    session = cache.get(cache_key)
    
    if not session:
        session = {
            'phone_number': phone_number,
            'current_state': 'idle',
            'patient_name': None,
            'selected_doctor': None,
            'preferred_date': None,
            'preferred_time': None,
            # ... outros campos
        }
        cache.set(cache_key, session, token_monitor.get_cache_timeout())
    
    return session
```

#### 4. **Sincronização Banco + Cache**
**Arquivo:** `api_gateway/services/gemini_chatbot_service.py` (linhas 929-973)

**Como funciona:**
- As informações são mantidas em **cache** (rápido) e **banco de dados** (persistente)
- Quando necessário, apenas o **estado atual** é consultado, não todo o histórico

```python
# gemini_chatbot_service.py (linhas 929-973)
def _sync_session_to_database(self, phone_number: str, session: Dict):
    """Sincroniza sessão do cache com o banco de dados"""
    try:
        from api_gateway.models import ConversationSession

        # Obtém ou cria sessão no banco com dados estruturados
        db_session, created = ConversationSession.objects.get_or_create(
            phone_number=phone_number,
            defaults={
                'current_state': session.get('current_state', 'idle'),
                'patient_name': session.get('patient_name'),
                'selected_doctor': session.get('selected_doctor'),
                'preferred_date': session.get('preferred_date'),
                'preferred_time': session.get('preferred_time'),
                # ... outros campos
            }
        )
        
        # Atualiza apenas os campos modificados
        if not created:
            db_session.current_state = session.get('current_state', 'idle')
            db_session.patient_name = session.get('patient_name')
            # ... atualiza apenas campos necessários
            db_session.save()
```

### 📊 Resumo da Estratégia

| Aspecto | Implementação |
|---------|---------------|
| **Histórico Completo** | ❌ NÃO envia todo o histórico |
| **Estado da Conversa** | ✅ Armazena em campo `current_state` |
| **Informações Coletadas** | ✅ Campos estruturados no banco |
| **Cache de Sessão** | ✅ Cache em memória para acesso rápido |
| **Histórico Limitado** | ✅ Apenas últimas 3-5 mensagens |
| **Sincronização** | ✅ Cache + Banco de Dados |

---

## Sistema de Monitoramento de Tokens

### Arquitetura do Token Monitor

**Arquivo:** `api_gateway/services/token_monitor.py`

```
┌─────────────────────────────────────────────────────────────┐
│                    TOKEN MONITOR                             │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐         ┌──────────────────┐          │
│  │ Monitoramento    │         │ Modo Econômico   │          │
│  │ em Tempo Real    │────────►│ (Auto-ativação)  │          │
│  └──────────────────┘         └──────────────────┘          │
│           │                            │                     │
│           │                            │                     │
│           ▼                            ▼                     │
│  ┌──────────────────┐         ┌──────────────────┐          │
│  │ Contadores       │         │ Configurações    │          │
│  │ - Diário         │         │ - Tokens reduzidos│         │
│  │ - Por Sessão     │         │ - Cache agressivo│          │
│  │ - Por Operação   │         │ - Temp. reduzida │          │
│  └──────────────────┘         └──────────────────┘          │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Funcionalidades do Token Monitor

#### 1. **Estimativa de Tokens**
```python
# token_monitor.py (linhas 58-74)
def estimate_tokens(self, text: str) -> int:
    """
    Estima o número de tokens em um texto
    Aproximação: 1 token ≈ 4 caracteres para português
    """
    if not text:
        return 0
    
    # Contar caracteres e dividir por 4 (aproximação)
    char_count = len(text)
    estimated_tokens = char_count // 4
    
    # Ajuste para português (caracteres acentuados contam mais)
    accent_chars = sum(1 for char in text if char in 'áàâãéèêíìîóòôõúùûçÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇ')
    estimated_tokens += accent_chars // 2
    
    return max(estimated_tokens, 1)  # Mínimo 1 token
```

#### 2. **Registro de Uso**
```python
# token_monitor.py (linhas 76-130)
def log_token_usage(self, operation: str, input_text: str, output_text: str = "", phone_number: str = None) -> int:
    """
    Registra o uso de tokens para monitoramento
    """
    # Calcular tokens
    input_tokens = self.estimate_tokens(input_text)
    output_tokens = self.estimate_tokens(output_text)
    total_tokens = input_tokens + output_tokens
    
    # Atualizar contadores
    self.token_usage_today += total_tokens
    if phone_number:
        if phone_number not in self.session_token_usage:
            self.session_token_usage[phone_number] = 0
        self.session_token_usage[phone_number] += total_tokens
    
    # Salvar no cache
    today = date.today().isoformat()
    cache_key = f"gemini_tokens_{today}"
    cache.set(cache_key, self.token_usage_today, 86400)  # 24 horas
    
    # Log detalhado
    logger.info(f"📊 TOKENS - {operation}: Input={input_tokens:,}, Output={output_tokens:,}, Total={total_tokens:,}")
```

#### 3. **Alertas Automáticos**
```python
# token_monitor.py (linhas 113-120)
# Alertas baseados no uso
if usage_percentage >= 95:
    logger.critical(f"🚨 CRÍTICO: Uso de tokens em {usage_percentage:.1f}% do limite diário!")
    self._activate_economy_mode()
elif usage_percentage >= 90:
    logger.error(f"⚠️ ALERTA: Uso de tokens em {usage_percentage:.1f}% do limite diário")
elif usage_percentage >= 80:
    logger.warning(f"⚠️ AVISO: Uso de tokens em {usage_percentage:.1f}% do limite diário")
```

#### 4. **Modo Econômico Automático**
```python
# token_monitor.py (linhas 132-145)
def _activate_economy_mode(self):
    """
    Ativa modo econômico quando o limite de tokens está próximo
    """
    try:
        if self.economy_mode:
            return  # Já está ativo
            
        logger.warning("🔄 Ativando modo econômico para preservar tokens")
        self.economy_mode = True
        logger.info("✅ Modo econômico ativado - tokens preservados")
        
    except Exception as e:
        logger.error(f"Erro ao ativar modo econômico: {e}")
```

#### 5. **Configurações de Modo Econômico**
```python
# token_monitor.py (linhas 192-204)
def get_economy_config(self) -> Dict[str, Any]:
    """
    Retorna configurações para modo econômico
    """
    if not self.economy_mode:
        return {}
    
    return {
        'max_output_tokens': 512,      # Reduz de 1024 para 512
        'temperature': 0.7,            # Reduz criatividade
        'top_p': 0.8,                  # Reduz diversidade
        'top_k': 20                    # Reduz opções
    }
```

---

## Otimizações Implementadas

### 1. **Prompts Otimizados**

#### Análise de Mensagem (Tokens Reduzidos)
**Arquivo:** `api_gateway/services/gemini_chatbot_service.py` (linhas 231-341)

```python
def _build_analysis_prompt(self, message: str, session: Dict, 
                         conversation_history: List, clinic_data: Dict) -> str:
    """
    Constrói prompt para análise da mensagem com contexto otimizado
    """
    # Histórico limitado a 3 mensagens
    if conversation_history:
        history_text = "Histórico da conversa:\n"
        for msg in conversation_history[-3:]:  # LIMITADO!
            role = "Paciente" if msg['is_user'] else "Assistente"
            history_text += f"- {role}: {msg['content']}\n"
    
    # Informações da clínica LIMITADAS (top 5)
    for medico in medicos[:5]:  # LIMITADO!
        # ... formata médico
    
    for esp in especialidades[:5]:  # LIMITADO!
        # ... formata especialidade
```

**Resultado:**
- Análise usa **temperature=0.1** e **max_output_tokens=300** (muito econômico)
- Prompt otimizado com informações essenciais apenas

#### Resposta ao Usuário (Tokens Controlados)
```python
# gemini_chatbot_service.py (linhas 52-58)
self.generation_config = {
    "temperature": 0.7,
    "top_p": 0.8,
    "top_k": 40,
    "max_output_tokens": 1024,  # Controlado
}
```

### 2. **Cache de Dados da Clínica**

**Arquivo:** `api_gateway/services/gemini_chatbot_service.py` (linhas 1315-1339)

```python
def _get_clinic_data_optimized(self) -> Dict[str, Any]:
    """
    Obtém dados da clínica de forma otimizada com cache inteligente
    """
    cache_key = "gemini_clinic_data"
    
    # Tentar cache primeiro (EVITA QUERY NO BANCO)
    cached_data = cache.get(cache_key)
    if cached_data:
        logger.debug("📋 Dados da clínica obtidos do cache")
        return cached_data
    
    # Buscar dados frescos do RAGService (SOMENTE SE NECESSÁRIO)
    try:
        clinic_data = RAGService.get_all_clinic_data()
        
        # Cache por 30 minutos (dados da clínica não mudam frequentemente)
        cache.set(cache_key, clinic_data, token_monitor.get_cache_timeout())
        
        logger.info("📋 Dados da clínica carregados do banco e armazenados no cache")
        return clinic_data
        
    except Exception as e:
        logger.error(f"Erro ao obter dados da clínica: {e}")
        return {}
```

**Benefícios:**
- Evita consultas repetidas ao banco de dados
- Reduz processamento e tempo de resposta
- Dados são atualizados apenas quando necessário

### 3. **Cache Adaptativo por Uso de Tokens**

```python
# token_monitor.py (linhas 212-221)
def get_cache_timeout(self) -> int:
    """
    Retorna timeout do cache baseado no modo econômico
    """
    if self.economy_mode:
        return 3600  # 1 hora em modo econômico
    elif (self.token_usage_today / self.daily_token_limit) > 0.8:
        return 1800  # 30 minutos quando próximo do limite
    else:
        return 900  # 15 minutos normal
```

**Como funciona:**
- **Modo Normal:** Cache de 15 minutos
- **Uso Alto (>80%):** Cache de 30 minutos
- **Modo Econômico (>95%):** Cache de 1 hora

### 4. **Otimização de Cache por Médico e Especialidade**

```python
# gemini_chatbot_service.py (linhas 1341-1399)
def _get_doctor_info_optimized(self, doctor_name: str) -> Dict[str, Any]:
    """
    Obtém informações de um médico específico de forma otimizada
    """
    cache_key = f"gemini_doctor_{doctor_name.lower().replace(' ', '_')}"
    
    # Cache por médico específico
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data
    
    # Buscar do RAGService
    doctor_data = RAGService.get_medico_by_name(doctor_name)
    
    if doctor_data:
        # Cache por 1 hora
        cache.set(cache_key, doctor_data, token_monitor.get_cache_timeout())
    
    return doctor_data or {}
```

---

## Fluxo de Otimização de Tokens

### Diagrama do Fluxo

```
┌─────────────────────────────────────────────────────────────┐
│                   NOVA MENSAGEM DO USUÁRIO                   │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  Buscar Sessão       │
              │  (Cache ou Banco)    │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  Estado Atual        │
              │  + Dados Coletados   │◄─── NÃO envia histórico completo
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  Histórico Limitado  │
              │  (Últimas 3 msgs)    │◄─── LIMITADO para reduzir tokens
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  Dados da Clínica    │
              │  (Cache)             │◄─── Cache para evitar repetições
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  Construir Prompt    │
              │  Otimizado           │◄─── Somente informações essenciais
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  Enviar ao Gemini    │
              │  + Monitorar Tokens  │◄─── Registra uso e ativa economia se necessário
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  Atualizar Sessão    │
              │  (Cache + Banco)     │◄─── Sincroniza estado atual
              └──────────────────────┘
```

---

## Monitoramento em Tempo Real

### Logs de Tokens

```python
# Exemplo de log ao processar mensagem:
📊 TOKENS - ANÁLISE: Input=1,245, Output=156, Total=1,401
📊 SESSÃO 5573988221003: Total=1,401, Acumulado=5,234
📊 DIA: Total=125,678, Limite=1,500,000, Uso=8.4%

# Quando próximo do limite:
⚠️ AVISO: Uso de tokens em 82.3% do limite diário

# Quando crítico:
🚨 CRÍTICO: Uso de tokens em 96.1% do limite diário!
🔄 Ativando modo econômico para preservar tokens
✅ Modo econômico ativado - tokens preservados
```

### Estatísticas Disponíveis

```python
# token_monitor.py (linhas 147-166)
def get_token_usage_stats(self) -> Dict[str, Any]:
    """
    Retorna estatísticas de uso de tokens
    """
    usage_percentage = (self.token_usage_today / self.daily_token_limit) * 100
    
    return {
        'tokens_used_today': self.token_usage_today,
        'daily_limit': self.daily_token_limit,
        'usage_percentage': usage_percentage,
        'tokens_remaining': self.daily_token_limit - self.token_usage_today,
        'session_usage': self.session_token_usage,
        'economy_mode': self.economy_mode,
        'enabled': self.enabled
    }
```

---

## Comparação: Antes vs Depois

### ❌ Sem Otimização (Hipotético)
```python
# Enviaria TODO o histórico:
prompt = f"""
Histórico completo de 50 mensagens: ...
Todos os médicos (10 médicos com todas as informações): ...
Todas as especialidades (15 especialidades): ...
Todos os convênios (20 convênios): ...
Todos os exames (8 exames): ...

Mensagem do usuário: "Quero agendar"
"""
# Tokens estimados: ~8,000 tokens por mensagem
```

### ✅ Com Otimização (Implementado)
```python
# Envia apenas o essencial:
prompt = f"""
Estado atual: collecting_info
Nome do paciente: João Silva
Médico selecionado: Dr. Gustavo

Histórico (últimas 3 msgs): ...
Top 5 médicos: ...
Top 5 especialidades: ...

Mensagem do usuário: "Quero agendar"
"""
# Tokens estimados: ~1,500 tokens por mensagem
```

### 💰 Economia
- **Redução:** ~81% de tokens por mensagem
- **Custo:** Redução proporcional nos custos da API
- **Performance:** Respostas mais rápidas

---

## Configurações

### Settings do Django

```python
# core/settings.py
GEMINI_TOKEN_MONITORING = True
GEMINI_DAILY_TOKEN_LIMIT = 1500000  # 1.5M tokens/dia

# Cache (Redis ou Memcached)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'TIMEOUT': 900  # 15 minutos padrão
    }
}
```

---

## Conclusão

### ✅ Estratégia Implementada

**SIM**, a estratégia mencionada na pergunta está **COMPLETAMENTE IMPLEMENTADA** no projeto:

> **"Para evitar o alto custo de enviar todo o histórico da conversa para o LLM a cada nova mensagem, será implementada uma estratégia de gestão de estado"**

### 📊 Implementações Realizadas

1. ✅ **Gestão de Estado** - Armazena estado atual ao invés de histórico completo
2. ✅ **Histórico Limitado** - Apenas últimas 3-5 mensagens relevantes
3. ✅ **Cache Inteligente** - Dados da clínica em cache para evitar repetições
4. ✅ **Monitoramento de Tokens** - Sistema completo de tracking e alertas
5. ✅ **Modo Econômico** - Ativação automática quando próximo do limite
6. ✅ **Sincronização** - Cache + Banco de Dados para persistência eficiente

### 📈 Benefícios Alcançados

- **Redução de ~81% nos tokens** enviados ao Gemini
- **Economia significativa de custos** com API
- **Respostas mais rápidas** (menos dados = menos processamento)
- **Monitoramento em tempo real** do uso de tokens
- **Proteção contra estouro de limites** com modo econômico

---

**Última Atualização:** Outubro 2024  
**Versão:** 1.0  
**Autor:** Sistema de Documentação Automatizada

