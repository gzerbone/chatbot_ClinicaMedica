# 📊 Análise Detalhada do Consumo de Tokens - Gemini API - Atualizada 05/10

## 🎯 Objetivo
Este documento analisa o fluxo de entrada e saída de tokens do Gemini API no chatbot da clínica médica, fornecendo insights sobre consumo e estratégias de otimização.

## 🔍 Fluxo Atual de Tokens

### 1. **Processamento de Mensagem Completo**

#### **Entrada (Input Tokens):**
```
📝 MENSAGEM DO PACIENTE: "Quero agendar com Dr. João"
```

#### **Prompt de Análise (Análise de Intenção):**
```
Você é um assistente virtual especializado da Clínica Médica.

ANÁLISE DA MENSAGEM:
Mensagem do paciente: "Quero agendar com Dr. João"

CONTEXTO ATUAL:
- Estado da conversa: idle
- Nome do paciente: Não informado
- Médico selecionado: Não selecionado

INFORMAÇÕES DETALHADAS DA CLÍNICA:
🏥 Nome: Clínica Médica
📍 Endereço: Rua das Flores, 123
📞 Telefone: (11) 99999-9999
💬 WhatsApp: (11) 99999-9999
🕒 Horário de funcionamento: Segunda a Sexta, 8h às 18h

👨‍⚕️ MÉDICOS DISPONÍVEIS:
• Dr. João Silva (CRM: 123456)
  - Especialidades: Cardiologia, Clínica Geral
  - Convênios aceitos: Unimed, Bradesco, Particular
  - Preço particular: R$ 150,00

• Dr. Maria Santos (CRM: 789012)
  - Especialidades: Dermatologia, Estética
  - Convênios aceitos: Amil, SulAmérica, Particular
  - Preço particular: R$ 120,00

[... mais médicos ...]

🏥 ESPECIALIDADES ATENDIDAS:
• Cardiologia: Tratamento de doenças do coração
• Dermatologia: Cuidados com a pele
• Clínica Geral: Consultas gerais

🏥 CONVÊNIOS ACEITOS:
• Unimed
• Bradesco
• Amil
• SulAmérica
• Particular

🔬 EXAMES DISPONÍVEIS:
• Hemograma: R$ 25,00 (30 minutos)
• Raio-X: R$ 50,00 (15 minutos)
• Ultrassom: R$ 80,00 (45 minutos)

ANÁLISE NECESSÁRIA:
Analise a mensagem e determine:

1. INTENÇÃO PRINCIPAL (uma das opções abaixo):
   - saudacao: Cumprimentos, oi, olá, bom dia
   - buscar_info: Perguntas sobre clínica, médicos, exames, preços, endereço
   - agendar_consulta: Quero agendar, marcar consulta, agendamento
   - confirmar_agendamento: Confirmar dados, sim, está correto
   - cancelar_agendamento: Cancelar, desmarcar, não posso mais
   - buscar_medico: Quais médicos, médico específico, especialidade
   - buscar_exame: Exames disponíveis, procedimentos
   - buscar_horarios: Horários disponíveis, quando atende
   - despedida: Tchau, obrigado, até logo
   - duvida: Não entendi, pode repetir, ajuda

2. PRÓXIMO ESTADO DA CONVERSA:
   - idle: Estado inicial
   - coletando_nome: Coletando nome do paciente
   - confirmando_nome: Confirmando nome extraído
   - selecionando_medico: Escolhendo médico
   - escolhendo_horario: Escolhendo data/horário
   - confirmando_agendamento: Confirmando dados finais
   - agendamento_concluido: Processo finalizado
   - fornecendo_info: Fornecendo informações solicitadas

3. ENTIDADES EXTRAÍDAS (EXTRAIA SEMPRE QUE POSSÍVEL):
   - nome_paciente: Nome completo do paciente
   - medico: Nome do médico mencionado
   - especialidade: Especialidade médica
   - data: Data em formato DD/MM/YYYY ou texto
   - horario: Horário em formato HH:MM ou texto
   - exame: Nome do exame mencionado

4. CONFIANÇA: Nível de confiança na análise (0.0 a 1.0)

Responda APENAS com um JSON válido no formato:
{
    "intent": "intenção_detectada",
    "next_state": "próximo_estado",
    "entities": {
        "nome_paciente": "nome_extraído_ou_null",
        "medico": "médico_extraído_ou_null",
        "especialidade": "especialidade_extraída_ou_null",
        "data": "data_extraída_ou_null",
        "horario": "horário_extraído_ou_null",
        "exame": "exame_extraído_ou_null"
    },
    "confidence": 0.95,
    "reasoning": "Explicação breve da análise"
}
```

**📊 ESTIMATIVA DE TOKENS - ANÁLISE:**
- **Input**: ~2,500-3,500 tokens (dependendo do tamanho dos dados da clínica)
- **Output**: ~150-300 tokens (resposta JSON)

#### **Prompt de Resposta (Geração de Resposta):**
```
Você é um assistente virtual especializado da Clínica Médica.

CONTEXTO DA CONVERSA:
- Estado atual: idle
- Próximo estado: selecionando_medico
- Intenção detectada: agendar_consulta
- Nome do paciente: Não informado
- Médico selecionado: Não selecionado

MENSAGEM DO PACIENTE: "Quero agendar com Dr. João"

INFORMAÇÕES DA CLÍNICA:
🏥 Nome: Clínica Médica
📍 Endereço: Rua das Flores, 123
📞 Telefone: (11) 99999-9999
💬 WhatsApp: (11) 99999-9999
🕒 Horário de funcionamento: Segunda a Sexta, 8h às 18h

MÉDICOS DISPONÍVEIS:
👨‍⚕️ Dr. João Silva (CRM: 123456)
   📋 Especialidades: Cardiologia, Clínica Geral
   🏥 Convênios aceitos: Unimed, Bradesco, Particular
   💰 Preço particular: R$ 150,00

👨‍⚕️ Dr. Maria Santos (CRM: 789012)
   📋 Especialidades: Dermatologia, Estética
   🏥 Convênios aceitos: Amil, SulAmérica, Particular
   💰 Preço particular: R$ 120,00

[... mais médicos ...]

ESPECIALIDADES ATENDIDAS:
🏥 Cardiologia: Tratamento de doenças do coração
🏥 Dermatologia: Cuidados com a pele
🏥 Clínica Geral: Consultas gerais

CONVÊNIOS ACEITOS:
🏥 Unimed
🏥 Bradesco
🏥 Amil
🏥 SulAmérica
🏥 Particular

EXAMES DISPONÍVEIS:
🔬 Hemograma: R$ 25,00 (30 minutos)
   📝 Exame de sangue completo
🔬 Raio-X: R$ 50,00 (15 minutos)
   📝 Imagem radiológica
🔬 Ultrassom: R$ 80,00 (45 minutos)
   📝 Exame por ultrassom

INSTRUÇÕES ESPECÍFICAS PARA INTENÇÃO "agendar_consulta":
- Guie o paciente através do processo de agendamento
- Se não tiver o nome, solicite o nome completo primeiro
- Se tiver o nome, prossiga para seleção de médico
- Seja claro sobre as etapas necessárias
- Mantenha o processo organizado e fácil

REGRAS IMPORTANTES:
1. Seja sempre cordial, profissional e prestativo
2. Use emojis moderadamente para tornar a conversa mais amigável
3. Mantenha respostas concisas e diretas
4. NÃO mencione telefone ou WhatsApp a menos que o paciente peça especificamente
5. Foque apenas no que o paciente perguntou
6. Se não souber algo específico, oriente o paciente a entrar em contato
7. Use linguagem clara e acessível
8. Mantenha o foco em saúde e bem-estar
9. Para perguntas sobre médicos, forneça informações específicas sobre especialidades e convênios aceitos
10. Para perguntas sobre exames, explique o que é o exame e como funciona

Gere uma resposta apropriada para a intenção "agendar_consulta" considerando o contexto atual da conversa.
```

**📊 ESTIMATIVA DE TOKENS - RESPOSTA:**
- **Input**: ~2,500-3,500 tokens (dependendo do tamanho dos dados da clínica)
- **Output**: ~200-500 tokens (resposta do assistente)

## 📈 Análise de Consumo por Conversa

### **Conversa Simples (1 mensagem):**
- **Análise**: ~2,500-3,500 tokens input + ~150-300 tokens output
- **Resposta**: ~2,500-3,500 tokens input + ~200-500 tokens output
- **TOTAL**: ~5,350-7,800 tokens por mensagem

### **Conversa Completa (5 mensagens):**
- **TOTAL**: ~26,750-39,000 tokens

### **Conversa Longa (10 mensagens):**
- **TOTAL**: ~53,500-78,000 tokens

## 🚨 Pontos de Alto Consumo

### 1. **Dados da Clínica (Maior Consumidor)**
- **Médicos**: ~500-800 tokens (5 médicos com detalhes)
- **Especialidades**: ~200-300 tokens (5 especialidades)
- **Convênios**: ~100-150 tokens (5 convênios)
- **Exames**: ~200-300 tokens (3 exames)
- **Informações básicas**: ~100-150 tokens
- **TOTAL DADOS**: ~1,100-1,700 tokens por prompt

### 2. **Histórico da Conversa**
- **Últimas 3 mensagens**: ~200-400 tokens
- **Crescimento linear**: +100-200 tokens por mensagem

### 3. **Prompts Detalhados**
- **Instruções de análise**: ~800-1,200 tokens
- **Instruções de resposta**: ~600-1,000 tokens
- **Exemplos e regras**: ~500-800 tokens

## 💡 Estratégias de Otimização (Sem Alterar Lógica)

### 1. **Cache Inteligente**
- ✅ **Implementado**: Cache de 30 minutos para dados da clínica
- ✅ **Benefício**: Reduz consultas ao banco, mas mantém dados atualizados

### 2. **Monitoramento de Tokens**
- ✅ **Implementado**: Sistema de monitoramento detalhado
- ✅ **Benefício**: Visibilidade completa do consumo

### 3. **Alertas Inteligentes**
- ✅ **Implementado**: Alertas em 80%, 90% e 95% do limite
- ✅ **Benefício**: Prevenção de exceder limites

### 4. **Modo Econômico Automático**
- ✅ **Implementado**: Ativação automática em 95% do limite
- ✅ **Benefício**: Preserva tokens sem quebrar funcionalidade

## 📊 Limites e Recomendações

### **Limites do Gemini API:**
- **Free Tier**: 15 requests/minuto, 1M tokens/dia
- **Paid Tier**: 1M tokens/dia (padrão)
- **Enterprise**: Limites customizados

### **Recomendações:**
1. **Monitoramento Contínuo**: Acompanhar logs de tokens
2. **Cache Estratégico**: Manter cache de dados da clínica
3. **Alertas Proativos**: Configurar alertas em 80% do limite
4. **Backup de Fallback**: Sistema de fallback para emergências

## 🔧 Implementação do Monitoramento

O sistema de monitoramento foi implementado com:

1. **Contadores de Tokens**: Por sessão, por dia, por operação
2. **Logs Detalhados**: Input, output e total por operação
3. **Alertas Automáticos**: Baseados em percentuais de uso
4. **Modo Econômico**: Ativação automática quando necessário
5. **Estatísticas**: Dashboard de uso de tokens

## 📈 Métricas de Monitoramento

### **Por Sessão:**
- Tokens utilizados por paciente
- Média de tokens por mensagem
- Pico de uso por sessão

### **Por Dia:**
- Total de tokens utilizados
- Percentual do limite diário
- Horários de maior uso

### **Por Operação:**
- Análise vs Resposta
- Prompts grandes (>2000 tokens)
- Eficiência por tipo de pergunta

## 🎯 Conclusão

O sistema atual está **otimizado** para:
- ✅ **Qualidade**: Mantém contexto completo para respostas precisas
- ✅ **Eficiência**: Cache inteligente reduz consultas desnecessárias
- ✅ **Monitoramento**: Visibilidade completa do consumo
- ✅ **Proteção**: Alertas e modo econômico automático

**Recomendação**: Manter a lógica atual e monitorar o consumo através dos logs implementados.
