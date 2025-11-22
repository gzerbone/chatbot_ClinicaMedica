# 📚 Índice - Fluxos e Processos do Chatbot

## 🎯 Visão Geral

Esta pasta contém documentação detalhada sobre os **fluxos de processos** do sistema de chatbot para clínica médica, incluindo estados da conversa, lógica de pré-agendamento, sistema de dúvidas e validações.

---

## 📋 Documentos Disponíveis

### **1. Visão Geral e Arquitetura**

#### 📄 [FLUXO_COMPLETO_PROJETO.md](./FLUXO_COMPLETO_PROJETO.md)
**Documento principal sobre a arquitetura e fluxo completo do sistema**

- 🏗️ Arquitetura modularizada (5 módulos Gemini)
- 🔄 Fluxo de dados completo (mensagem → resposta)
- 🤖 Módulos Gemini detalhados
- 📚 Serviços de apoio
- 📊 Persistência e sincronização
- 📈 Métricas e logs

**Quando usar:** Para entender a arquitetura completa do projeto e como todos os componentes se conectam.

**Última atualização:** Novembro 15, 2025 (v3.0 - Modularizada)

---

### **2. Estados e Máquina de Estados**

#### 📄 [ANALISE_ESTADOS_CONVERSACAO.md](./ANALISE_ESTADOS_CONVERSACAO.md)
**Documentação completa sobre os estados da conversa**

- 🔄 9 estados ativos implementados
- 📊 Máquina de estados e transições
- 🔧 Campos auxiliares (previous_state, pending_name)
- 📋 Sistema de pausar/retomar
- 📈 Estatísticas e consultas úteis
- 🎯 Boas práticas

**Quando usar:** Para entender como os estados da conversa funcionam e como o chatbot transita entre eles.

**Última atualização:** Novembro 15, 2025 (v3.0)

**Estados implementados:**
- `idle` - Ocioso
- `collecting_patient_info` - Coletando dados
- `answering_questions` - Respondendo dúvidas
- `confirming_name` - Confirmando nome
- `selecting_specialty` - Selecionando especialidade
- `selecting_doctor` - Selecionando médico
- `choosing_schedule` - Escolhendo horário
- `confirming` - Confirmando

---

### **3. Lógica de Pré-Agendamento**

#### 📄 [LOGICA_PRE_AGENDAMENTO_ATUALIZADA.md](./LOGICA_PRE_AGENDAMENTO_ATUALIZADA.md)
**Lógica completa do sistema de pré-agendamento com arquitetura modular**

- 📅 Fluxo completo de pré-agendamento (passo a passo)
- 🤖 Módulos Gemini e responsabilidades
- ✅ Validações em cada etapa
- 🔗 Geração de handoff
- 📊 Persistência de dados
- 🔧 Tratamento de erros

**Quando usar:** Para entender como funciona o processo completo de agendamento, desde a solicitação inicial até o handoff.

**Última atualização:** Novembro 15, 2025 (v3.0 - Modularizada)

**Etapas do agendamento:**
1. Solicitação inicial
2. Coleta de nome
3. Confirmação de nome
4. Seleção de especialidade
5. Seleção de médico
6. Escolha de data e horário
7. Confirmação final e handoff

---

#### 📄 [FLUXO_PRE_AGENDAMENTO_CORRIGIDO.md](./FLUXO_PRE_AGENDAMENTO_CORRIGIDO.md)
**Correção do problema de handoffs prematuros**

- 🎯 Problema identificado
- ✅ Solução implementada
- 🔍 Validação de informações obrigatórias
- 📋 Checklist de validação
- 🔄 Comparação: antes vs depois

**Quando usar:** Para entender como o sistema garante que todas as informações necessárias sejam coletadas antes de gerar o handoff.

**Última atualização:** Novembro 15, 2025 (v2.0)

**Informações obrigatórias validadas:**
- Nome do paciente (confirmado)
- Especialidade médica
- Médico selecionado
- Data da consulta
- Horário da consulta

---

### **4. Sistema de Pausar/Retomar**

#### 📄 [SISTEMA_DUVIDAS_PAUSAR_RETOMAR.md](./SISTEMA_DUVIDAS_PAUSAR_RETOMAR.md)
**Sistema inteligente de pausar agendamento para responder dúvidas**

- 💡 Três cenários de uso
- 🔧 Implementação técnica
- 📚 Funções principais (pause, resume, has_paused)
- 🔄 Integração com CoreService
- 📝 Exemplos de conversa real
- 🔍 Palavras-chave de retomada

**Quando usar:** Para entender como o sistema permite que usuários tirem dúvidas durante o agendamento sem perder progresso.

**Última atualização:** Novembro 15, 2025 (v2.0)

**Palavras-chave de retomada:**
- continuar
- retomar
- voltar
- prosseguir
- seguir
- agendamento

---

### **5. Validação e Segurança**

#### 📄 [VALIDACAO_FORMATO_MENSAGEM.md](./VALIDACAO_FORMATO_MENSAGEM.md)
**Validação robusta de formatos de mensagem**

- 📝 Validação de tipos de mensagem
- ✅ Tipos aceitos (apenas texto)
- ❌ Tipos rejeitados (mídia, interativos)
- 💬 Mensagens de erro personalizadas
- 📊 Logs e monitoramento
- 🧪 Cenários de teste

**Quando usar:** Para entender como o sistema valida e filtra mensagens recebidas do WhatsApp.

**Última atualização:** Novembro 15, 2025 (v2.0)

**Tipos rejeitados:**
- Imagens, áudios, vídeos
- Documentos, figurinhas
- Localizações, contatos
- Mensagens interativas

---

## 🗺️ Navegação Rápida

### **Por Tópico**

#### 🏗️ **Arquitetura**
- [Fluxo Completo do Projeto](./FLUXO_COMPLETO_PROJETO.md) - Visão geral da arquitetura
- [Análise de Estados](./ANALISE_ESTADOS_CONVERSACAO.md) - Máquina de estados

#### 📅 **Agendamento**
- [Lógica de Pré-Agendamento](./LOGICA_PRE_AGENDAMENTO_ATUALIZADA.md) - Fluxo completo
- [Correção de Handoffs](./FLUXO_PRE_AGENDAMENTO_CORRIGIDO.md) - Validações

#### 💬 **Interação**
- [Sistema de Dúvidas](./SISTEMA_DUVIDAS_PAUSAR_RETOMAR.md) - Pausar/retomar
- [Validação de Mensagens](./VALIDACAO_FORMATO_MENSAGEM.md) - Formatos aceitos

---

### **Por Módulo de Código**

#### 🤖 **CoreService** (`core_service.py`)
- [Fluxo Completo do Projeto](./FLUXO_COMPLETO_PROJETO.md#módulos-gemini)
- [Lógica de Pré-Agendamento](./LOGICA_PRE_AGENDAMENTO_ATUALIZADA.md#1-coreservice---orquestrador-principal)
- [Sistema de Dúvidas](./SISTEMA_DUVIDAS_PAUSAR_RETOMAR.md#integração-com-coreservice)

#### 📊 **SessionManager** (`session_manager.py`)
- [Fluxo Completo do Projeto](./FLUXO_COMPLETO_PROJETO.md#5-sessionmanager---gerenciamento-de-sessões)
- [Análise de Estados](./ANALISE_ESTADOS_CONVERSACAO.md#métodos-auxiliares)

#### 🔍 **IntentDetector** (`intent_detector.py`)
- [Fluxo Completo do Projeto](./FLUXO_COMPLETO_PROJETO.md#2-intentdetector---detecção-de-intenções)
- [Lógica de Pré-Agendamento](./LOGICA_PRE_AGENDAMENTO_ATUALIZADA.md#3-intentdetector---detecção-de-intenções)

#### 📦 **EntityExtractor** (`entity_extractor.py`)
- [Fluxo Completo do Projeto](./FLUXO_COMPLETO_PROJETO.md#3-entityextractor---extração-de-entidades)
- [Lógica de Pré-Agendamento](./LOGICA_PRE_AGENDAMENTO_ATUALIZADA.md#4-entityextractor---extração-de-entidades)

#### 💬 **ResponseGenerator** (`response_generator.py`)
- [Fluxo Completo do Projeto](./FLUXO_COMPLETO_PROJETO.md#4-responsegenerator---geração-de-respostas)
- [Lógica de Pré-Agendamento](./LOGICA_PRE_AGENDAMENTO_ATUALIZADA.md#5-responsegenerator---geração-de-respostas)

#### 📚 **ConversationService** (`conversation_service.py`)
- [Análise de Estados](./ANALISE_ESTADOS_CONVERSACAO.md#sistema-de-campos-auxiliares)
- [Sistema de Dúvidas](./SISTEMA_DUVIDAS_PAUSAR_RETOMAR.md#funções-principais)
- [Correção de Handoffs](./FLUXO_PRE_AGENDAMENTO_CORRIGIDO.md#validações-por-etapa)

#### 🌐 **Views** (`views.py`)
- [Validação de Mensagens](./VALIDACAO_FORMATO_MENSAGEM.md#implementação)

---

## 🚀 Começando

### **Para Novos Desenvolvedores**

Recomendamos ler na seguinte ordem:

1. **[FLUXO_COMPLETO_PROJETO.md](./FLUXO_COMPLETO_PROJETO.md)**
   - Entenda a arquitetura geral do sistema
   - Conheça os módulos principais
   - Veja o fluxo de dados completo

2. **[ANALISE_ESTADOS_CONVERSACAO.md](./ANALISE_ESTADOS_CONVERSACAO.md)**
   - Compreenda os estados da conversa
   - Aprenda sobre transições de estados
   - Veja como o sistema de pausar/retomar funciona

3. **[LOGICA_PRE_AGENDAMENTO_ATUALIZADA.md](./LOGICA_PRE_AGENDAMENTO_ATUALIZADA.md)**
   - Entenda o fluxo de agendamento completo
   - Veja as validações em cada etapa
   - Aprenda sobre geração de handoffs

4. **[SISTEMA_DUVIDAS_PAUSAR_RETOMAR.md](./SISTEMA_DUVIDAS_PAUSAR_RETOMAR.md)**
   - Entenda como funciona o sistema de dúvidas
   - Veja exemplos práticos
   - Aprenda a implementar funcionalidades similares

5. **[FLUXO_PRE_AGENDAMENTO_CORRIGIDO.md](./FLUXO_PRE_AGENDAMENTO_CORRIGIDO.md)**
   - Entenda validações específicas
   - Veja como prevenir handoffs prematuros

6. **[VALIDACAO_FORMATO_MENSAGEM.md](./VALIDACAO_FORMATO_MENSAGEM.md)**
   - Entenda filtros de mensagens
   - Veja como tratar diferentes tipos de mídia

---

### **Para Manutenção**

#### Adicionando novo estado:
1. Atualizar modelo em `models.py`
2. Criar migração
3. Atualizar [ANALISE_ESTADOS_CONVERSACAO.md](./ANALISE_ESTADOS_CONVERSACAO.md)
4. Atualizar [LOGICA_PRE_AGENDAMENTO_ATUALIZADA.md](./LOGICA_PRE_AGENDAMENTO_ATUALIZADA.md) se aplicável

#### Modificando fluxo de agendamento:
1. Atualizar código em `core_service.py`
2. Atualizar [LOGICA_PRE_AGENDAMENTO_ATUALIZADA.md](./LOGICA_PRE_AGENDAMENTO_ATUALIZADA.md)
3. Atualizar [FLUXO_COMPLETO_PROJETO.md](./FLUXO_COMPLETO_PROJETO.md)

#### Adicionando novo tipo de mensagem:
1. Atualizar `views.py`
2. Atualizar [VALIDACAO_FORMATO_MENSAGEM.md](./VALIDACAO_FORMATO_MENSAGEM.md)

---

## 📊 Resumo dos Documentos

| Documento | Tamanho | Última Atualização | Status |
|-----------|---------|-------------------|--------|
| FLUXO_COMPLETO_PROJETO.md | ~800 linhas | Nov 15, 2025 | ✅ Atualizado |
| ANALISE_ESTADOS_CONVERSACAO.md | ~350 linhas | Nov 15, 2025 | ✅ Atualizado |
| LOGICA_PRE_AGENDAMENTO_ATUALIZADA.md | ~700 linhas | Nov 15, 2025 | ✅ Atualizado |
| FLUXO_PRE_AGENDAMENTO_CORRIGIDO.md | ~400 linhas | Nov 15, 2025 | ✅ Atualizado |
| SISTEMA_DUVIDAS_PAUSAR_RETOMAR.md | ~450 linhas | Nov 15, 2025 | ✅ Atualizado |
| VALIDACAO_FORMATO_MENSAGEM.md | ~250 linhas | Nov 15, 2025 | ✅ Atualizado |

**Total:** ~2.950 linhas de documentação

---

## 🔗 Links Úteis

### **Documentação Relacionada**

- **01_arquitetura/**
  - [ARQUITETURA_ATUAL.md](../01_arquitetura/ARQUITETURA_ATUAL.md) - Arquitetura técnica
  - [ORGANIZACAO_BANCO_DADOS.md](../01_arquitetura/ORGANIZACAO_BANCO_DADOS.md) - Estrutura do banco

- **02_setup_configuracao/**
  - [GUIA_DESENVOLVIMENTO.md](../02_setup_configuracao/) - Setup e configuração

- **05_otimizacoes/**
  - [GESTAO_MEMORIA_TOKENS_ATUALIZADA.md](../05_otimizacoes/) - Otimizações

- **06_modularizacao/**
  - [MODULARIZACAO_GEMINI_COMPLETA.md](../06_modularizacao/) - Detalhes da modularização

---

## 🤝 Contribuindo

Ao atualizar documentos:

1. ✅ Mantenha o formato markdown consistente
2. ✅ Atualize a data "Última Atualização"
3. ✅ Incremente a versão se mudanças significativas
4. ✅ Atualize este INDEX.md se adicionar/remover documentos
5. ✅ Use exemplos práticos e diagramas visuais
6. ✅ Referencie linhas específicas do código quando possível

---

## 📞 Suporte

Para dúvidas sobre a documentação:

1. Verifique os exemplos de código nos documentos
2. Consulte os logs do sistema
3. Revise o código fonte referenciado
4. Entre em contato com a equipe de desenvolvimento

---

**📅 Última Atualização:** Novembro 15, 2025  
**📝 Versão:** 1.0  
**✅ Status:** Documentação completa e atualizada

