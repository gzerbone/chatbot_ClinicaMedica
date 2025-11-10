# 📚 Documentação do Agent Router

Esta pasta contém toda a documentação sobre o **Agent Router** implementado no projeto Chatbot Clínica Médica.

---

## 📖 Sobre o Agent Router

O **Agent Router** é o componente central do sistema, responsável por analisar mensagens dos usuários e direcioná-las para os serviços especializados apropriados. Implementado na classe `GeminiChatbotService`, ele funciona como o "cérebro" do chatbot.

---

## 📂 Documentos Disponíveis

### 1. 📘 AGENT_ROUTER_COMPLETO.md
**Documentação Completa e Didática**

**Para quem:**
- Desenvolvedores novos no projeto
- Quem quer entender o conceito de Agent Router
- Documentação para apresentações/TCC
- Referência geral do sistema

**Conteúdo:**
- ✅ O que é um Agent Router (conceito e analogias)
- ✅ Por que implementamos um
- ✅ Tipos de roteamento utilizados
- ✅ Arquitetura completa com diagramas
- ✅ Fluxos detalhados explicados de forma simples
- ✅ Intenções e estados suportados
- ✅ Exemplos práticos passo a passo
- ✅ Sistema de fallbacks
- ✅ Monitoramento e performance
- ✅ Glossário e referências

**Tempo de leitura:** ~30-40 minutos

---

### 2. 💻 IMPLEMENTACAO_TECNICA_ROUTER.md
**Guia Técnico de Implementação**

**Para quem:**
- Desenvolvedores implementando features
- Manutenção e debugging
- Code review
- Compreensão técnica profunda

**Conteúdo:**
- ✅ Arquitetura de código detalhada
- ✅ Estrutura da classe GeminiChatbotService
- ✅ Fluxo de processamento no código
- ✅ Implementação das decisões de roteamento
- ✅ Integração com serviços
- ✅ Configurações e parâmetros
- ✅ Testes e validação
- ✅ Boas práticas de código

**Tempo de leitura:** ~25-35 minutos

---

### 3. ⚡ GUIA_RAPIDO_ROUTER.md
**Referência Rápida (Cheat Sheet)**

**Para quem:**
- Desenvolvedores experientes no projeto
- Consultas rápidas durante desenvolvimento
- Troubleshooting
- Lembretes de comandos e endpoints

**Conteúdo:**
- ✅ Resumo ultra-compacto
- ✅ Fluxo em 5 passos
- ✅ Tabelas de referência
- ✅ Como adicionar nova intenção
- ✅ Comandos de teste (cURL)
- ✅ Troubleshooting rápido
- ✅ Checklist de implementação

**Tempo de leitura:** ~5-10 minutos

---

## 🎯 Qual documento ler?

### Fluxograma de Decisão

```
┌─────────────────────────────────────┐
│  Você é novo no projeto?            │
│                                     │
│  SIM → AGENT_ROUTER_COMPLETO.md    │
│  NÃO → Continue abaixo ↓            │
└─────────────────────────────────────┘
                │
┌───────────────▼─────────────────────┐
│  Você vai implementar algo novo?    │
│                                     │
│  SIM → IMPLEMENTACAO_TECNICA.md    │
│  NÃO → Continue abaixo ↓            │
└─────────────────────────────────────┘
                │
┌───────────────▼─────────────────────┐
│  Você precisa de uma referência     │
│  rápida ou comandos de teste?      │
│                                     │
│  SIM → GUIA_RAPIDO_ROUTER.md       │
└─────────────────────────────────────┘
```

### Por Perfil

#### 👨‍🎓 Estudante / Pesquisador / TCC
→ **Comece com:** `AGENT_ROUTER_COMPLETO.md`  
→ **Depois veja:** `IMPLEMENTACAO_TECNICA_ROUTER.md`

Este documento tem toda a explicação didática com diagramas e analogias, perfeito para apresentações e compreensão conceitual.

---

#### 👨‍💻 Desenvolvedor Novo no Projeto
→ **Comece com:** `AGENT_ROUTER_COMPLETO.md`  
→ **Depois veja:** `IMPLEMENTACAO_TECNICA_ROUTER.md`  
→ **Tenha à mão:** `GUIA_RAPIDO_ROUTER.md`

Leia os dois primeiros na ordem para entender conceito e implementação, depois use o guia rápido como referência.

---

#### 🔧 Desenvolvedor Experiente no Projeto
→ **Use:** `GUIA_RAPIDO_ROUTER.md` (referência rápida)  
→ **Consulte quando necessário:** `IMPLEMENTACAO_TECNICA_ROUTER.md`

Você já conhece o sistema, use o guia rápido para consultas e troubleshooting.

---

#### 📊 Gerente de Projeto / Tech Lead
→ **Leia:** `AGENT_ROUTER_COMPLETO.md` (seções de Arquitetura e Decisões)

Foque nas seções de arquitetura, benefícios obtidos e monitoramento.

---

#### 🐛 Debugging / Suporte
→ **Use:** `GUIA_RAPIDO_ROUTER.md` (seção Troubleshooting)  
→ **Se necessário:** `IMPLEMENTACAO_TECNICA_ROUTER.md` (seção Testes)

Para resolver problemas rapidamente.

---

## 🗂️ Estrutura Recomendada de Leitura

### Primeira Vez (Leitura Completa)

```
Dia 1: AGENT_ROUTER_COMPLETO.md
   ↓
   - Entender conceito
   - Ver diagramas
   - Compreender fluxos

Dia 2: IMPLEMENTACAO_TECNICA_ROUTER.md
   ↓
   - Código detalhado
   - Como funciona
   - Boas práticas

Dia 3: Prática
   ↓
   - Usar GUIA_RAPIDO_ROUTER.md
   - Testar endpoints
   - Implementar pequena mudança
```

### Consulta Rápida (Uso Diário)

```
Preciso adicionar feature?
   → GUIA_RAPIDO_ROUTER.md (Como Adicionar Nova Intenção)
   → IMPLEMENTACAO_TECNICA_ROUTER.md (Checklist)

Algo não funciona?
   → GUIA_RAPIDO_ROUTER.md (Troubleshooting)
   → Logs do sistema

Dúvida sobre arquitetura?
   → AGENT_ROUTER_COMPLETO.md (Arquitetura)
   → IMPLEMENTACAO_TECNICA_ROUTER.md (Código)
```

---

## 🔗 Documentação Relacionada

Estes documentos fazem parte do ecossistema de documentação do projeto:

### Arquitetura Geral
- `docs/01_arquitetura/ARQUITETURA_ATUAL.md` - Visão completa do sistema
- `docs/01_arquitetura/ARQUITETURA_GEMINI_CENTRALIZADA.md` - Foco no Gemini

### Fluxos e Processos
- `docs/04_fluxos_processos/FLUXO_COMPLETO_PROJETO.md` - Todos os fluxos

### Modularização
- `docs/06_modularizacao/MODULARIZACAO_GEMINI_COMPLETA.md` - Como foi modularizado
- `docs/06_modularizacao/PLANO_MODULARIZACAO.md` - Planejamento

### Correções
- `docs/07_correcoes/` - Histórico de correções implementadas

---

## 📝 Contribuindo com a Documentação

Se você identificar algo que precisa ser melhorado:

1. **Conceitos mal explicados** → Atualizar `AGENT_ROUTER_COMPLETO.md`
2. **Código desatualizado** → Atualizar `IMPLEMENTACAO_TECNICA_ROUTER.md`
3. **Referência faltando** → Atualizar `GUIA_RAPIDO_ROUTER.md`
4. **Novo documento necessário** → Criar e atualizar este README

---

## 📊 Métricas da Documentação

| Documento | Linhas | Diagramas | Exemplos | Complexidade |
|-----------|--------|-----------|----------|--------------|
| AGENT_ROUTER_COMPLETO.md | ~1400 | 12 | 4 | ⭐⭐ Média |
| IMPLEMENTACAO_TECNICA_ROUTER.md | ~1000 | 6 | 8 | ⭐⭐⭐ Alta |
| GUIA_RAPIDO_ROUTER.md | ~350 | 2 | 6 | ⭐ Baixa |

---

## 🎓 Conceitos-Chave

Antes de ler qualquer documento, tenha em mente:

### Agent Router
> Componente que analisa mensagens e decide para qual serviço especializado direcioná-las

### Intent (Intenção)
> O que o usuário quer fazer (ex: agendar, perguntar, confirmar)

### Entity (Entidade)
> Informação específica extraída da mensagem (ex: nome, data, médico)

### Roteamento
> Processo de decidir qual serviço deve processar a mensagem

### Estado
> Etapa atual do fluxo de conversa (ex: coletando_nome, escolhendo_medico)

---

## 💡 Dicas de Estudo

1. **Não pule os diagramas**: Eles são essenciais para entender o fluxo
2. **Execute os exemplos**: Use os comandos cURL para ver na prática
3. **Compare com o código**: Abra os arquivos mencionados enquanto lê
4. **Faça anotações**: Anote dúvidas e volte depois de praticar
5. **Teste incrementalmente**: Implemente pequenas mudanças para consolidar

---

## ❓ FAQ

### Preciso ler tudo?
Não. Use o fluxograma de decisão acima para escolher o que ler.

### Qual ordem devo ler?
Se é sua primeira vez: Completo → Técnico → Rápido

### Quanto tempo vou levar?
- Leitura completa: 1h-1h30
- Leitura técnica: 30min-45min
- Referência rápida: 5min-10min

### Posso começar pelo código?
Sim, mas recomendamos ler pelo menos o `AGENT_ROUTER_COMPLETO.md` antes.

### Como sei se entendi?
Tente explicar o fluxo de roteamento para alguém ou implemente uma nova intenção.

---

## 📞 Suporte

Se após ler toda a documentação você ainda tiver dúvidas:

1. Revise os logs do sistema (`api_gateway/logs/`)
2. Teste os endpoints de debug
3. Consulte a documentação geral em `docs/`
4. Revise o código fonte comentado

---

## 🏆 Objetivo desta Documentação

Garantir que qualquer desenvolvedor, independente do nível de experiência, consiga:

✅ **Entender** o que é e como funciona o Agent Router  
✅ **Implementar** novas funcionalidades com confiança  
✅ **Debugar** problemas de forma eficiente  
✅ **Manter** o sistema com qualidade  
✅ **Escalar** o projeto sem perder organização  

---

**Última atualização:** 10/11/2025  
**Versão:** 1.0  
**Mantenedores:** Equipe de Desenvolvimento Chatbot Clínica Médica

---

**🚀 Comece agora:** Abra o `AGENT_ROUTER_COMPLETO.md` e boa leitura!

