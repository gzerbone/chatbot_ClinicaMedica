# Integração com Google Gemini AI

Este documento explica como a integração com o Google Gemini AI foi implementada no chatbot da clínica médica.

## 📋 Visão Geral

A integração com o Gemini AI permite que o chatbot gere respostas mais inteligentes, contextuais e naturais, mantendo a funcionalidade de fallback para os templates tradicionais.

## 🔧 Configuração

### 1. Dependências

Adicione a dependência no `requirements.txt`:
```
google-generativeai==0.8.3
```

### 2. Configurações do Django

No arquivo `core/settings.py`, configure:

```python
# Configurações do Gemini AI
GEMINI_API_KEY="sua_chave_api_aqui"
GEMINI_MODEL="gemini-1.5-flash"
GEMINI_TEMPERATURE=0.7
GEMINI_MAX_TOKENS=1024
GEMINI_ENABLED=True
```

### 3. Obter Chave da API

1. Acesse [Google AI Studio](https://aistudio.google.com/)
2. Crie um projeto
3. Gere uma chave de API
4. Adicione a chave nas configurações do Django

## 🏗️ Arquitetura

### Componentes Principais

1. **GeminiService** (`flow_agent/services/gemini_service.py`)
   - Gerencia a conexão com a API do Gemini
   - Gera respostas baseadas em prompts estruturados
   - Suporta respostas contextuais com histórico

2. **ResponseGenerator** (modificado)
   - Integra com o GeminiService
   - Mantém fallback para templates tradicionais
   - Fornece dados da clínica para o Gemini

3. **MessageProcessor** (modificado)
   - Usa o Gemini para gerar respostas inteligentes
   - Considera o histórico da conversa
   - Mantém compatibilidade com sistema existente

## 🚀 Funcionalidades

### Respostas Inteligentes

O Gemini gera respostas baseadas em:
- **Intenção detectada**: Saudação, agendamento, busca de informações, etc.
- **Contexto da conversa**: Histórico de mensagens anteriores
- **Dados da clínica**: Especialidades, médicos, exames, informações gerais
- **Instruções específicas**: Prompts personalizados para cada tipo de intenção

### Fallback Automático

Se o Gemini não estiver disponível ou falhar:
- Sistema automaticamente usa templates tradicionais
- Funcionalidade do chatbot mantida
- Logs de erro para debugging

### Respostas Contextuais

O sistema considera:
- Últimas 10 mensagens da conversa
- Estado atual do agendamento
- Preferências do usuário
- Dados específicos da clínica

## 📝 Exemplos de Uso

### 1. Teste Básico

```python
from flow_agent.services.gemini_service import GeminiService

gemini = GeminiService()
response = gemini.generate_response(
    user_message="Olá, quero agendar uma consulta",
    intent="agendar_consulta",
    context={'etapa': 'inicio'}
)
```

### 2. Resposta Contextual

```python
from flow_agent.services.response_generator import ResponseGenerator

generator = ResponseGenerator()
response = generator.generate_contextual_response(
    user_message="Sim, quero agendar",
    intent="agendar_consulta",
    conversation_history=[
        {'tipo': 'entrada', 'conteudo': 'Olá'},
        {'tipo': 'saida', 'conteudo': 'Como posso ajudar?'}
    ]
)
```

### 3. Via API

```bash
# Testar integração
curl -X POST http://localhost:8000/api/whatsapp/gemini-test/ \
  -H "Content-Type: application/json" \
  -d '{"message": "Quais especialidades vocês têm?"}'

# Verificar status
curl http://localhost:8000/api/whatsapp/status/
```

## 🧪 Testes

### Script de Teste Automatizado

Execute o script de teste:

```bash
python test_gemini_integration.py
```

O script testa:
- ✅ Conexão com Gemini AI
- ✅ Geração de respostas básicas
- ✅ Processamento de mensagens
- ✅ Respostas contextuais

### Testes Manuais

1. **Via API Gateway**:
   - `GET /api/whatsapp/status/` - Verificar status
   - `POST /api/whatsapp/gemini-test/` - Testar processamento

2. **Via WhatsApp**:
   - Envie mensagens para o webhook
   - Verifique respostas mais naturais e contextuais

## ⚙️ Configurações Avançadas

### Personalização de Prompts

Modifique o método `_get_intent_instructions()` no `GeminiService` para personalizar como o Gemini responde a cada intenção.

### Ajuste de Parâmetros

No `settings.py`, ajuste:
- `GEMINI_TEMPERATURE`: Criatividade (0.0 a 1.0)
- `GEMINI_MAX_TOKENS`: Tamanho máximo da resposta
- `GEMINI_MODEL`: Modelo do Gemini a usar

### Desabilitar Gemini

Para desabilitar temporariamente:
```python
GEMINI_ENABLED=False
```

## 🔍 Monitoramento

### Logs

O sistema gera logs para:
- Inicialização do Gemini
- Erros de conexão
- Fallbacks para templates
- Respostas geradas

### Métricas

Monitore:
- Taxa de sucesso do Gemini
- Tempo de resposta
- Qualidade das respostas
- Uso de fallbacks

## 🚨 Troubleshooting

### Problemas Comuns

1. **Erro de API Key**:
   - Verifique se a chave está correta
   - Confirme se a API está habilitada

2. **Respostas vazias**:
   - Verifique logs de erro
   - Confirme se o modelo está disponível

3. **Fallback constante**:
   - Verifique conectividade
   - Confirme configurações

### Debug

Ative logs detalhados:
```python
import logging
logging.getLogger('flow_agent.services.gemini_service').setLevel(logging.DEBUG)
```

## 📈 Benefícios

### Para Usuários
- Respostas mais naturais e humanas
- Melhor compreensão de contexto
- Interações mais fluidas

### Para Desenvolvedores
- Sistema de fallback robusto
- Fácil manutenção e configuração
- Logs detalhados para debugging

### Para a Clínica
- Atendimento mais personalizado
- Melhor experiência do paciente
- Redução de mal-entendidos

## 🔄 Próximos Passos

1. **Treinamento Personalizado**: Usar dados específicos da clínica para treinar prompts
2. **Análise de Sentimentos**: Detectar humor e urgência nas mensagens
3. **Multilíngue**: Suporte a outros idiomas
4. **Integração com CRM**: Conectar com sistemas de gestão da clínica

## 📚 Recursos Adicionais

- [Documentação do Gemini AI](https://ai.google.dev/docs)
- [Google AI Studio](https://aistudio.google.com/)
- [Django Settings](https://docs.djangoproject.com/en/stable/topics/settings/)
