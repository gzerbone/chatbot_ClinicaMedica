# 📚 Documentação de Fluxos e Processos

## 📋 Índice de Documentos

Esta pasta contém a documentação completa dos fluxos e processos do sistema de chatbot da clínica médica.

---

## 📄 Documentos Disponíveis

### 1. **CENARIOS_TESTE_CONVERSAS.md** ⭐ NOVO
**Cenários completos de conversas entre usuário e chatbot**

- ✅ 8 cenários detalhados de teste
- ✅ Conversas completas passo a passo
- ✅ Validações e estados documentados
- ✅ Casos de uso reais

**Use para:** Testes, validação, exemplos de uso

---

### 2. **ANALISE_ESTADOS_CONVERSACAO.md**
**Análise completa dos estados da conversação**

- ✅ 9 estados implementados documentados
- ✅ Transições entre estados
- ✅ Sistema de pausar/retomar
- ✅ Campos auxiliares (`previous_state`, `pending_name`)

**Use para:** Entender máquina de estados, debug de fluxos

---

### 3. **SISTEMA_DUVIDAS_PAUSAR_RETOMAR.md**
**Sistema de pausar agendamento para responder dúvidas**

- ✅ Como funciona o sistema de pausar/retomar
- ✅ Três cenários de uso
- ✅ Implementação técnica completa
- ✅ Integração com código atual

**Use para:** Entender sistema de dúvidas, implementar melhorias

---

### 4. **VALIDACAO_FORMATO_MENSAGEM.md**
**Validação de formatos de mensagem aceitos**

- ✅ Tipos de mensagem suportados
- ✅ Mensagens de erro personalizadas
- ✅ Validações implementadas

**Use para:** Entender validações, mensagens de erro

---

### 5. **FLUXO_PRE_AGENDAMENTO_CORRIGIDO.md**
**Fluxo corrigido de pré-agendamento**

- ✅ Verificação de informações obrigatórias
- ✅ Identificação de informações faltantes
- ✅ Solicitação sequencial de dados

**Use para:** Entender fluxo de agendamento, validações

---

### 6. **LOGICA_PRE_AGENDAMENTO_ATUALIZADA.md**
**Lógica completa de pré-agendamento (documento extenso)**

- ✅ Arquitetura do sistema
- ✅ Módulos e serviços
- ✅ Fluxo completo passo a passo
- ✅ Integração com Google Calendar
- ✅ Handoff para secretária

**Use para:** Referência completa, arquitetura detalhada

---

### 7. **FLUXO_COMPLETO_PROJETO.md**
**Fluxo completo do projeto (documento extenso)**

- ✅ Arquitetura macro do sistema
- ✅ Fluxo de dados completo
- ✅ Diagramas visuais
- ✅ Configuração e deploy
- ✅ Métricas e performance

**Use para:** Visão geral completa, deploy, monitoramento

---

## 🎯 Guia Rápido de Uso

### **Para Desenvolvedores Novos:**
1. Comece com **CENARIOS_TESTE_CONVERSAS.md** - Veja exemplos reais
2. Leia **ANALISE_ESTADOS_CONVERSACAO.md** - Entenda os estados
3. Consulte **SISTEMA_DUVIDAS_PAUSAR_RETOMAR.md** - Entenda sistema de dúvidas

### **Para Debug:**
1. **ANALISE_ESTADOS_CONVERSACAO.md** - Verificar transições de estado
2. **CENARIOS_TESTE_CONVERSAS.md** - Comparar com cenários esperados
3. **FLUXO_PRE_AGENDAMENTO_CORRIGIDO.md** - Verificar validações

### **Para Implementar Funcionalidades:**
1. **LOGICA_PRE_AGENDAMENTO_ATUALIZADA.md** - Arquitetura completa
2. **FLUXO_COMPLETO_PROJETO.md** - Integrações e serviços
3. **SISTEMA_DUVIDAS_PAUSAR_RETOMAR.md** - Sistema de pausar/retomar

---

## ⚠️ Documentos Obsoletos ou Desatualizados

### **Removidos:**
- ❌ Nenhum documento foi removido

### **Atualizados em Janeiro 2025:**
- ✅ **ANALISE_ESTADOS_CONVERSACAO.md** - Removidos estados obsoletos (`completed`, `cancelled`)
- ✅ **SISTEMA_DUVIDAS_PAUSAR_RETOMAR.md** - Atualizado com código atual
- ✅ **CENARIOS_TESTE_CONVERSAS.md** - Criado novo documento com testes

---

## 📊 Estados do Sistema (Resumo)

### **Estados Ativos (8):**
1. `idle` - Ocioso
2. `collecting_patient_info` - Coletando dados do paciente
3. `answering_questions` - Respondendo dúvidas
4. `confirming_name` - Confirmando nome
5. `selecting_specialty` - Selecionando especialidade
6. `selecting_doctor` - Selecionando médico
7. `choosing_schedule` - Escolhendo horário
8. `confirming` - Confirmando agendamento

### **Estados Removidos:**
- ❌ `completed` - Nunca utilizado
- ❌ `cancelled` - Nunca utilizado

---

## 🔄 Fluxo Principal

```
idle → collecting_patient_info → confirming_name → 
selecting_specialty → selecting_doctor → choosing_schedule → 
confirming
```

**Com sistema de pausar/retomar:**
```
[qualquer estado] → answering_questions → [estado anterior]
```

---

## 📝 Convenções de Documentação

### **Ícones Utilizados:**
- ✅ = Implementado/Funcional
- ❌ = Não implementado/Removido
- ⚠️ = Atenção/Limitação
- 📋 = Informação/Documentação
- 🔧 = Implementação técnica
- 🎯 = Objetivo/Finalidade

### **Formato de Código:**
- Código Python usa blocos de código com referências de arquivo
- Estados são escritos em `snake_case`
- Intents são escritos em `snake_case`

---

## 🚀 Próximos Passos

### **Melhorias Sugeridas:**
- [ ] Adicionar mais cenários de teste
- [ ] Documentar tratamento de erros
- [ ] Criar diagramas de sequência atualizados
- [ ] Documentar APIs e endpoints

---

**📅 Última Atualização:** Janeiro 2025  
**📝 Versão:** 1.0  
**✅ Status:** Documentação atualizada e validada

