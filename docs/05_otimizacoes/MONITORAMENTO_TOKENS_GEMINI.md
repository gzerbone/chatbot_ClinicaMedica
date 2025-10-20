# 📊 Sistema de Monitoramento de Tokens - Gemini API

## 🎯 Visão Geral

Sistema completo de monitoramento de tokens implementado no chatbot da clínica médica para controlar o uso da API do Gemini e evitar exceder limites diários.

## 🔧 Funcionalidades Implementadas

### 1. **Monitoramento Automático**
- ✅ **Contagem de tokens** por operação (análise e resposta)
- ✅ **Contadores por sessão** (por número de telefone)
- ✅ **Contador diário** com persistência em cache
- ✅ **Estimativa inteligente** de tokens (otimizada para português)

### 2. **Alertas Automáticos**
- 🟡 **80% do limite**: Aviso de uso moderado
- 🟠 **90% do limite**: Alerta de uso alto
- 🔴 **95% do limite**: Crítico + modo econômico automático

### 3. **Modo Econômico**
- ✅ **Ativação automática** em 95% do limite
- ✅ **Redução de max_output_tokens** para 512
- ✅ **Preservação da funcionalidade** do chatbot

### 4. **Logs Detalhados**
- 📊 **Por operação**: Input, output e total de tokens
- 📊 **Por sessão**: Acumulado por paciente
- 📊 **Por dia**: Total diário e percentual
- 📊 **Prompts grandes**: Alertas para prompts >2000 tokens

## 🚀 Como Usar

### **1. Monitoramento via Logs**

Os logs mostram informações detalhadas em tempo real:

```
📊 TOKENS - ANÁLISE: Input=2,500, Output=200, Total=2,700
📊 SESSÃO 11999999999: Total=2,700, Acumulado=5,400
📊 DIA: Total=15,000, Limite=1,500,000, Uso=1.0%
⚠️ AVISO: Uso de tokens em 80.0% do limite diário
```

### **2. Endpoints de API**

#### **Obter Estatísticas**
```bash
GET /api_gateway/monitor/tokens/
```

**Resposta:**
```json
{
  "success": true,
  "data": {
    "tokens_used_today": 15000,
    "daily_limit": 1500000,
    "usage_percentage": 1.0,
    "tokens_remaining": 1485000,
    "session_usage": {
      "11999999999": 5400,
      "11999999998": 9600
    },
    "economy_mode": false,
    "monitoring_enabled": true,
    "status": {
      "level": "NORMAL",
      "message": "Uso normal de tokens",
      "percentage": 1.0
    }
  }
}
```

#### **Resetar Contador (Cuidado!)**
```bash
POST /api_gateway/monitor/tokens/reset/
```

### **3. Configurações**

Adicione no `settings.py`:

```python
# Configurações de monitoramento de tokens
GEMINI_TOKEN_MONITORING = True  # Habilitar monitoramento
GEMINI_DAILY_TOKEN_LIMIT = 1500000  # Limite diário (1.5M tokens)
```

## 📈 Análise de Consumo

### **Consumo por Mensagem**
- **Análise**: ~2,500-3,500 tokens input + ~150-300 tokens output
- **Resposta**: ~2,500-3,500 tokens input + ~200-500 tokens output
- **TOTAL**: ~5,350-7,800 tokens por mensagem

### **Fatores que Influenciam o Consumo**
1. **Dados da clínica**: ~1,100-1,700 tokens (médicos, especialidades, exames)
2. **Histórico da conversa**: ~200-400 tokens (últimas 3 mensagens)
3. **Prompts detalhados**: ~1,900-3,000 tokens (instruções e exemplos)

### **Estratégias de Otimização**
- ✅ **Cache inteligente**: 30 minutos para dados da clínica
- ✅ **Prompts otimizados**: Informações específicas e relevantes
- ✅ **Modo econômico**: Redução automática quando necessário

## 🚨 Alertas e Ações

### **Níveis de Alerta**

| Percentual | Nível | Ação |
|------------|-------|------|
| < 80% | 🟢 NORMAL | Monitoramento contínuo |
| 80-89% | 🟡 CAUTION | Aviso - monitorar uso |
| 90-94% | 🟠 WARNING | Alerta - atenção necessária |
| ≥ 95% | 🔴 CRITICAL | Crítico - modo econômico ativado |

### **Ações Automáticas**
- **80%**: Log de aviso
- **90%**: Log de alerta
- **95%**: Log crítico + modo econômico + redução de tokens

## 🔍 Monitoramento em Tempo Real

### **1. Logs do Sistema**
```bash
# Acompanhar logs em tempo real
tail -f logs/django.log | grep "TOKENS"
```

### **2. Dashboard via API**
```python
import requests

# Obter estatísticas
response = requests.get('http://localhost:8000/api/monitor/tokens/')
stats = response.json()

print(f"Uso: {stats['data']['usage_percentage']:.1f}%")
print(f"Tokens restantes: {stats['data']['tokens_remaining']:,}")
```

### **3. Script de Monitoramento**
```bash
# Executar script de teste
python scripts/test_token_monitoring.py
```

## 📊 Métricas Importantes

### **Por Sessão**
- Tokens utilizados por paciente
- Média de tokens por mensagem
- Duração da sessão

### **Por Dia**
- Total de tokens utilizados
- Percentual do limite diário
- Horários de maior uso
- Picos de consumo

### **Por Operação**
- Análise vs Resposta
- Prompts grandes (>2000 tokens)
- Eficiência por tipo de pergunta

## 🛡️ Proteções Implementadas

### **1. Modo Econômico Automático**
- Ativação em 95% do limite
- Redução de max_output_tokens para 512
- Preservação da funcionalidade

### **2. Cache Inteligente**
- Dados da clínica: 30 minutos
- Médicos específicos: 1 hora
- Especialidades: 1 hora

### **3. Alertas Proativos**
- Logs detalhados em tempo real
- Alertas baseados em percentuais
- Avisos para prompts grandes

## 🎯 Recomendações

### **1. Monitoramento Contínuo**
- Acompanhar logs diariamente
- Configurar alertas em 80% do limite
- Monitorar picos de uso

### **2. Otimizações**
- Manter cache de dados da clínica
- Monitorar prompts grandes
- Usar modo econômico quando necessário

### **3. Backup de Segurança**
- Sistema de fallback para emergências
- Reset manual do contador (com cuidado)
- Monitoramento de limites da API

## 📞 Suporte

Para dúvidas sobre o sistema de monitoramento:

1. **Logs**: Verificar logs do Django
2. **API**: Usar endpoints de monitoramento
3. **Scripts**: Executar scripts de teste
4. **Documentação**: Consultar este documento

## 🔄 Atualizações

O sistema de monitoramento é **automático** e **não requer intervenção manual**. Ele:

- ✅ Monitora tokens em tempo real
- ✅ Ativa alertas automaticamente
- ✅ Preserva funcionalidade do chatbot
- ✅ Fornece visibilidade completa do uso

**Resultado**: Controle total sobre o consumo de tokens sem comprometer a qualidade do chatbot!
