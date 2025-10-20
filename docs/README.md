# 📚 Documentação do Projeto - Chatbot Clínica Médica

## 📋 Índice de Documentações

Este README serve como índice para toda a documentação do projeto, organizada por categorias temáticas.

---

## 📁 Estrutura da Documentação

### 🏗️ **01_arquitetura/**
Documentos sobre a estrutura e design do sistema:
- [`ARQUITETURA_ATUAL.md`](./01_arquitetura/ARQUITETURA_ATUAL.md) - Arquitetura atual do sistema
- [`ARQUITETURA_GEMINI_CENTRALIZADA.md`](./01_arquitetura/ARQUITETURA_GEMINI_CENTRALIZADA.md) - Arquitetura centralizada no Gemini
- [`ORGANIZACAO_BANCO_DADOS.md`](./01_arquitetura/ORGANIZACAO_BANCO_DADOS.md) - Estrutura do banco de dados

### ⚙️ **02_setup_configuracao/**
Guias de instalação e configuração:
- [`CONFIGURACAO_ENV.md`](./02_setup_configuracao/CONFIGURACAO_ENV.md) - Configuração de variáveis de ambiente
- [`WHATSAPP_SETUP.md`](./02_setup_configuracao/WHATSAPP_SETUP.md) - Setup do WhatsApp Business API
- [`SETUP_WEBHOOK_WHATSAPP.md`](./02_setup_configuracao/SETUP_WEBHOOK_WHATSAPP.md) - Configuração de webhooks
- [`GOOGLE_CALENDAR_SETUP.md`](./02_setup_configuracao/GOOGLE_CALENDAR_SETUP.md) - Integração com Google Calendar
- [`SETUP_CALENDAR_DESENVOLVIMENTO.md`](./02_setup_configuracao/SETUP_CALENDAR_DESENVOLVIMENTO.md) - Setup para desenvolvimento
- [`GUIA_SECRETARIA_CALENDAR.md`](./02_setup_configuracao/GUIA_SECRETARIA_CALENDAR.md) - Guia para secretária
- [`INTEGRACAO_APIS.md`](./02_setup_configuracao/INTEGRACAO_APIS.md) - Integração com APIs externas

### 💻 **03_desenvolvimento/**
Guias e dicas para desenvolvimento:
- [`GUIA_DESENVOLVIMENTO.md`](./03_desenvolvimento/GUIA_DESENVOLVIMENTO.md) - Guia completo de desenvolvimento
- [`DICAS_MODULARIZACAO.md`](./03_desenvolvimento/DICAS_MODULARIZACAO.md) - Dicas de modularização
- [`EXEMPLO_MODULARIZACAO.md`](./03_desenvolvimento/EXEMPLO_MODULARIZACAO.md) - Exemplos práticos

### 🔄 **04_fluxos_processos/**
Documentação de fluxos de negócio:
- [`FLUXO_COMPLETO_PROJETO.md`](./04_fluxos_processos/FLUXO_COMPLETO_PROJETO.md) - Fluxo completo do projeto
- [`FLUXO_PRE_AGENDAMENTO_CORRIGIDO.md`](./04_fluxos_processos/FLUXO_PRE_AGENDAMENTO_CORRIGIDO.md) - Fluxo de pré-agendamento
- [`LOGICA_PRE_AGENDAMENTO_ATUALIZADA.md`](./04_fluxos_processos/LOGICA_PRE_AGENDAMENTO_ATUALIZADA.md) - Lógica de agendamento
- [`ANALISE_ESTADOS_CONVERSACAO.md`](./04_fluxos_processos/ANALISE_ESTADOS_CONVERSACAO.md) - Análise de estados
- [`SISTEMA_DUVIDAS_PAUSAR_RETOMAR.md`](./04_fluxos_processos/SISTEMA_DUVIDAS_PAUSAR_RETOMAR.md) - Sistema de dúvidas
- [`VALIDACAO_FORMATO_MENSAGEM.md`](./04_fluxos_processos/VALIDACAO_FORMATO_MENSAGEM.md) - Validação de mensagens

### ⚡ **05_otimizacoes/**
Documentos sobre gestão de recursos e performance:
- [`GESTAO_MEMORIA_TOKENS_ATUALIZADA.md`](./05_otimizacoes/GESTAO_MEMORIA_TOKENS_ATUALIZADA.md) - Gestão de memória e tokens
- [`ANALISE_TOKENS_GEMINI.md`](./05_otimizacoes/ANALISE_TOKENS_GEMINI.md) - Análise de tokens do Gemini
- [`MONITORAMENTO_TOKENS_GEMINI.md`](./05_otimizacoes/MONITORAMENTO_TOKENS_GEMINI.md) - Monitoramento de tokens
- [`REFATORACAO_TOKEN_MONITOR.md`](./05_otimizacoes/REFATORACAO_TOKEN_MONITOR.md) - Refatoração do monitor
- [`OTIMIZACAO_VALIDACAO_AGENDAMENTO.md`](./05_otimizacoes/OTIMIZACAO_VALIDACAO_AGENDAMENTO.md) - Otimização de validação
- [`OTIMIZACOES_CODIGO_DUPLICADO.md`](./05_otimizacoes/OTIMIZACOES_CODIGO_DUPLICADO.md) - Otimizações de código

### 🧩 **06_modularizacao/**
Documentos sobre refatoração e organização do código:
- [`MODULARIZACAO_GEMINI_COMPLETA.md`](./06_modularizacao/MODULARIZACAO_GEMINI_COMPLETA.md) - Modularização do Gemini
- [`PLANO_MODULARIZACAO.md`](./06_modularizacao/PLANO_MODULARIZACAO.md) - Plano de modularização

### 🔧 **07_correcoes/**
Histórico de correções implementadas:
- [`CORREÇÕES_IMPLEMENTADAS.md`](./07_correcoes/CORREÇÕES_IMPLEMENTADAS.md) - Resumo das correções
- [`CORRECAO_ERROS_CONFIRMACAO.md`](./07_correcoes/CORRECAO_ERROS_CONFIRMACAO.md) - Correção de erros de confirmação
- [`CORRECAO_ERROS_LOGS.md`](./07_correcoes/CORRECAO_ERROS_LOGS.md) - Correção de erros de logs
- [`CORRECAO_REPETICAO_PERGUNTAS.md`](./07_correcoes/CORRECAO_REPETICAO_PERGUNTAS.md) - Correção de repetição de perguntas
- [`CORRECAO_SALVAMENTO_BANCO.md`](./07_correcoes/CORRECAO_SALVAMENTO_BANCO.md) - Correção de salvamento no banco
- [`PLANO_REFATORACAO_ENTIDADES.md`](./07_correcoes/PLANO_REFATORACAO_ENTIDADES.md) - Correção da duplicação de responsabilidades entre `IntentDetector` e `EntityExtractor`
---

## 📖 Documentações Principais (Outubro 2024)

### 1️⃣ **Organização do Banco de Dados**

**Arquivo:** [`01_arquitetura/ORGANIZACAO_BANCO_DADOS.md`](./01_arquitetura/ORGANIZACAO_BANCO_DADOS.md)

### 📊 O que contém:
- ✅ Estrutura completa do banco de dados (SQLite3)
- ✅ Modelos de dados detalhados (api_gateway e rag_agent)
- ✅ Relacionamentos entre tabelas
- ✅ Histórico de migrações
- ✅ Estratégias de otimização
- ✅ Exemplos de queries

### 🎯 Principais Modelos:

#### **api_gateway:**
- `ConversationSession` - Sessões de conversa
- `ConversationMessage` - Mensagens individuais

#### **rag_agent:**
- `ClinicaInfo` - Informações da clínica
- `Especialidade` - Especialidades médicas
- `Convenio` - Convênios aceitos
- `Medico` - Médicos da clínica
- `HorarioTrabalho` - Horários de atendimento
- `Exame` - Exames disponíveis

---

## 2️⃣ **Gestão de Memória para Otimização de Tokens**

**Arquivo:** [`05_otimizacoes/GESTAO_MEMORIA_TOKENS_ATUALIZADA.md`](./05_otimizacoes/GESTAO_MEMORIA_TOKENS_ATUALIZADA.md)

### 🧠 O que contém:
- ✅ Estratégia de gestão de estado (respondida a pergunta do usuário)
- ✅ Sistema de monitoramento de tokens (TokenMonitor)
- ✅ Otimizações implementadas
- ✅ Cache inteligente
- ✅ Modo econômico automático

### ❓ Resposta à Pergunta:

> **"Para evitar o alto custo de enviar todo o histórico da conversa para o LLM a cada nova mensagem, será implementada uma estratégia de gestão de estado"**

**✅ RESPOSTA: SIM, ESTA ESTRATÉGIA ESTÁ IMPLEMENTADA**

#### 📍 Onde está:
1. **Gestão de Estado** - `ConversationSession` armazena estado atual (não histórico completo)
2. **Histórico Limitado** - Apenas últimas 3-5 mensagens enviadas ao Gemini
3. **Cache de Sessão** - Dados estruturados em cache (evita reenvio)
4. **Sincronização** - Cache + Banco de Dados

#### 💰 Resultados:
- **Redução de ~81% nos tokens** enviados ao Gemini
- **Economia significativa** com custos da API
- **Respostas mais rápidas**

---

## 3️⃣ **Implementação da Lógica de Pré-Agendamento**

**Arquivo:** [`04_fluxos_processos/LOGICA_PRE_AGENDAMENTO_ATUALIZADA.md`](./04_fluxos_processos/LOGICA_PRE_AGENDAMENTO_ATUALIZADA.md)

### 📅 O que contém:
- ✅ Arquitetura do sistema de pré-agendamento
- ✅ Fluxo completo (respondida a pergunta do usuário)
- ✅ Módulos e serviços
- ✅ Estados da conversa
- ✅ Validações e confirmações
- ✅ Integração com Google Calendar
- ✅ Handoff para secretária

### ❓ Resposta à Pergunta:

> **"Este módulo será responsável por orquestrar todo o fluxo de agendamento, desde a solicitação inicial até a confirmação do usuário."**

**✅ RESPOSTA: SIM, ESTE MÓDULO ORQUESTRADOR ESTÁ IMPLEMENTADO**

#### 📍 Onde está:
- **Orquestrador Principal:** `GeminiChatbotService.process_message()`
- **Serviços de Apoio:**
  - `ConversationService` - Gerencia sessões
  - `SmartSchedulingService` - Consulta horários
  - `RAGService` - Dados da clínica
  - `GoogleCalendarService` - Disponibilidade real
  - `HandoffService` - Link de transferência

#### 🎯 Fluxo Completo:
```
Saudação → Coleta de Nome → Confirmação → Seleção de Médico →
Consulta de Horários → Escolha de Data/Hora → Validação →
Confirmação → Handoff para Secretária
```

#### 🚀 Diferenciais:
- **IA com Gemini** - Análise inteligente de intenções
- **Estados Progressivos** - Máquina de estados bem definida
- **Validações Robustas** - Verifica informações antes do handoff
- **Integração Google Calendar** - Horários reais
- **Handoff Inteligente** - Link formatado para WhatsApp

---

## 📊 Resumo Geral

### ✅ Perguntas Respondidas

| Pergunta | Resposta | Documentação |
|----------|----------|--------------|
| **Estratégia de gestão de estado para evitar envio de histórico completo?** | ✅ **SIM, IMPLEMENTADA** | [05_otimizacoes/GESTAO_MEMORIA_TOKENS_ATUALIZADA.md](./05_otimizacoes/GESTAO_MEMORIA_TOKENS_ATUALIZADA.md) |
| **Módulo orquestrador de fluxo de agendamento completo?** | ✅ **SIM, IMPLEMENTADO** | [04_fluxos_processos/LOGICA_PRE_AGENDAMENTO_ATUALIZADA.md](./04_fluxos_processos/LOGICA_PRE_AGENDAMENTO_ATUALIZADA.md) |

### 📈 Estrutura Documentada

```
📁 docs/
├── 📄 README.md (índice principal)
├── 📁 01_arquitetura/
│   ├── ARQUITETURA_ATUAL.md
│   ├── ARQUITETURA_GEMINI_CENTRALIZADA.md
│   └── ORGANIZACAO_BANCO_DADOS.md
├── 📁 02_setup_configuracao/
│   ├── CONFIGURACAO_ENV.md
│   ├── WHATSAPP_SETUP.md
│   ├── GOOGLE_CALENDAR_SETUP.md
│   └── ... (7 arquivos total)
├── 📁 03_desenvolvimento/
│   ├── GUIA_DESENVOLVIMENTO.md
│   ├── DICAS_MODULARIZACAO.md
│   └── EXEMPLO_MODULARIZACAO.md
├── 📁 04_fluxos_processos/
│   ├── FLUXO_COMPLETO_PROJETO.md
│   ├── LOGICA_PRE_AGENDAMENTO_ATUALIZADA.md
│   └── ... (6 arquivos total)
├── 📁 05_otimizacoes/
│   ├── GESTAO_MEMORIA_TOKENS_ATUALIZADA.md
│   ├── ANALISE_TOKENS_GEMINI.md
│   └── ... (6 arquivos total)
├── 📁 06_modularizacao/
│   ├── MODULARIZACAO_GEMINI_COMPLETA.md
│   └── PLANO_MODULARIZACAO.md
└── 📁 07_correcoes/
    ├── CORREÇÕES_IMPLEMENTADAS.md
    ├── CORRECAO_ERROS_CONFIRMACAO.md
    └── ... (6 arquivos total)
```

---

## 🎯 Como Usar as Documentações

### Para Desenvolvedores:
1. **Setup** - Comece com `02_setup_configuracao/` para configurar o ambiente
2. **Arquitetura** - Entenda a estrutura em `01_arquitetura/`
3. **Desenvolvimento** - Use `03_desenvolvimento/` para guias práticos
4. **Fluxos** - Compreenda os processos em `04_fluxos_processos/`

### Para Product Owners:
1. **Arquitetura** - Entenda a estrutura do sistema
2. **Fluxos** - Visualize a jornada do paciente
3. **Otimizações** - Veja como economizamos recursos
4. **Correções** - Acompanhe melhorias implementadas

### Para Novos Membros:
- **Ordem recomendada**: Setup → Arquitetura → Desenvolvimento → Fluxos
- **Consulte os diagramas** para visualizar
- **Veja os exemplos práticos** em desenvolvimento
- **Entenda as correções** para evitar problemas conhecidos

### Para Manutenção:
- **Adicione novos documentos** na pasta apropriada
- **Use prefixos numéricos** para manter ordem lógica
- **Documentos obsoletos** vão para `_obsoletos/`


