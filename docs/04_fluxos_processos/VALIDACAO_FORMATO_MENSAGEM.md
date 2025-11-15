# 📝 Validação de Formato de Mensagem

## 🎯 Objetivo

Implementar validação robusta para garantir que o chatbot aceite apenas mensagens de texto válidas e rejeite todos os outros tipos de mídia com mensagens de erro apropriadas.

---

## ✅ Implementação

### **Localização no Código**
**Arquivo:** `api_gateway/views.py` (linhas 107-199)

```python
def process_message(message, webhook_data):
    """
    Processa uma mensagem individual
    """
    try:
        # Extrair informações da mensagem
        message_id = message.get('id')
        from_number = message.get('from')
        message_type = message.get('type')
        timestamp = message.get('timestamp')

        logger.info(f"🔄 Processando mensagem {message_id} de {from_number}")

        # Verificar se é mensagem de texto válida
        if message_type == 'text':
            text_content = message.get('text', {}).get('body', '')

            # Validar se o conteúdo de texto não está vazio e tem tamanho mínimo
            if text_content and len(text_content.strip()) > 0:
                logger.info(f"👤 USUÁRIO ({from_number}): {text_content}")

                # Processar mensagem com Gemini Chatbot Service
                # ... código de processamento ...
                
            else:
                # Mensagem de texto vazia ou inválida
                logger.warning(f"⚠️ Mensagem de texto vazia ou inválida de {from_number}")
                response_text = "❌ Desculpe, não consegui processar sua mensagem. Por favor, envie uma mensagem de texto válida."
                whatsapp_service.send_message(from_number, response_text)
                logger.info(f"💬 ERRO TEXTO: {response_text}")

        else:
            # Rejeitar todos os outros tipos de mensagem
            logger.warning(f"❌ Tipo de mensagem não suportado: {message_type} de {from_number}")
            
            # Mensagem de erro personalizada baseada no tipo
            error_messages = {
                'image': "📷 Desculpe, não consigo processar imagens. Por favor, envie sua mensagem como texto.",
                'audio': "🎵 Desculpe, não consigo processar áudios. Por favor, envie sua mensagem como texto.",
                'video': "🎬 Desculpe, não consigo processar vídeos. Por favor, envie sua mensagem como texto.",
                'document': "📄 Desculpe, não consigo processar documentos. Por favor, envie sua mensagem como texto.",
                'sticker': "😊 Desculpe, não consigo processar figurinhas. Por favor, envie sua mensagem como texto.",
                'location': "📍 Desculpe, não consigo processar localizações. Por favor, envie sua mensagem como texto.",
                'contacts': "👥 Desculpe, não consigo processar contatos. Por favor, envie sua mensagem como texto.",
                'interactive': "🔘 Desculpe, não consigo processar mensagens interativas. Por favor, envie sua mensagem como texto.",
                'button': "🔘 Desculpe, não consigo processar botões. Por favor, envie sua mensagem como texto.",
                'list': "📋 Desculpe, não consigo processar listas. Por favor, envie sua mensagem como texto."
            }
            
            # Mensagem padrão para tipos não mapeados
            response_text = error_messages.get(message_type, 
                f"❌ Desculpe, não consigo processar mensagens do tipo '{message_type}'. Por favor, envie sua mensagem como texto.")
            
            # Enviar mensagem de erro
            whatsapp_service.send_message(from_number, response_text)
            logger.info(f"💬 ERRO FORMATO: {response_text}")

    except Exception as e:
        logger.error(f"❌ Erro ao processar mensagem: {e}")
```

---

## 📊 Tipos de Mensagem

### **✅ ACEITOS:**
- **`text`** - Mensagens de texto com conteúdo válido

### **❌ REJEITADOS:**

#### **Mensagens de Texto Inválidas:**
- Texto vazio (`""`)
- Texto apenas com espaços (`"   "`)
- Texto com apenas quebras de linha

#### **Mensagens de Mídia:**
- **`image`** - Imagens (JPEG, PNG, GIF, etc.)
- **`audio`** - Áudios (MP3, OGG, WAV, etc.)
- **`video`** - Vídeos (MP4, AVI, MOV, etc.)
- **`document`** - Documentos (PDF, DOC, XLS, etc.)

#### **Mensagens Especiais:**
- **`sticker`** - Figurinhas
- **`location`** - Localização GPS
- **`contacts`** - Contatos
- **`interactive`** - Mensagens interativas
- **`button`** - Botões
- **`list`** - Listas

---

## 💬 Mensagens de Erro Personalizadas

### **Por Tipo de Mídia:**

| Tipo | Ícone | Mensagem de Erro |
|------|-------|------------------|
| `image` | 📷 | "Desculpe, não consigo processar imagens. Por favor, envie sua mensagem como texto." |
| `audio` | 🎵 | "Desculpe, não consigo processar áudios. Por favor, envie sua mensagem como texto." |
| `video` | 🎬 | "Desculpe, não consigo processar vídeos. Por favor, envie sua mensagem como texto." |
| `document` | 📄 | "Desculpe, não consigo processar documentos. Por favor, envie sua mensagem como texto." |
| `sticker` | 😊 | "Desculpe, não consigo processar figurinhas. Por favor, envie sua mensagem como texto." |
| `location` | 📍 | "Desculpe, não consigo processar localizações. Por favor, envie sua mensagem como texto." |
| `contacts` | 👥 | "Desculpe, não consigo processar contatos. Por favor, envie sua mensagem como texto." |
| `interactive` | 🔘 | "Desculpe, não consigo processar mensagens interativas. Por favor, envie sua mensagem como texto." |
| `button` | 🔘 | "Desculpe, não consigo processar botões. Por favor, envie sua mensagem como texto." |
| `list` | 📋 | "Desculpe, não consigo processar listas. Por favor, envie sua mensagem como texto." |

### **Para Texto Inválido:**
- **Mensagem**: "❌ Desculpe, não consegui processar sua mensagem. Por favor, envie uma mensagem de texto válida."

### **Para Tipos Não Mapeados:**
- **Mensagem**: "❌ Desculpe, não consigo processar mensagens do tipo '{tipo}'. Por favor, envie sua mensagem como texto."

---

## 🔍 Validações Implementadas

### **1. Validação de Tipo**
```python
if message_type == 'text':
    # Processar apenas mensagens de texto
else:
    # Rejeitar todos os outros tipos
```

### **2. Validação de Conteúdo**
```python
# Verificar se o texto não está vazio
if text_content and len(text_content.strip()) > 0:
    # Processar texto válido
else:
    # Rejeitar texto vazio ou inválido
```

### **3. Validação de Tamanho**
```python
# Verificar se o texto tem conteúdo real (não apenas espaços)
len(text_content.strip()) > 0
```

---

## 📈 Benefícios da Validação

### **1. Segurança**
- ✅ **Previne ataques** via mídia maliciosa
- ✅ **Evita processamento** de arquivos não suportados
- ✅ **Protege recursos** do servidor

### **2. Performance**
- ✅ **Reduz carga** de processamento desnecessário
- ✅ **Evita erros** de parsing de mídia
- ✅ **Otimiza recursos** do sistema

### **3. Experiência do Usuário**
- ✅ **Mensagens claras** sobre formatos suportados
- ✅ **Feedback imediato** sobre erros de formato
- ✅ **Orientação específica** por tipo de mídia

### **4. Monitoramento**
- ✅ **Logs detalhados** de mensagens rejeitadas
- ✅ **Métricas** de tipos de mídia mais enviados
- ✅ **Alertas** para tentativas de bypass

---

## 🛠️ Logs de Monitoramento

### **Mensagens Aceitas:**
```
👤 USUÁRIO (5511999999999): Olá, quero agendar uma consulta
🤖 GEMINI: Como posso ajudá-lo com seu agendamento?
```

### **Mensagens Rejeitadas:**
```
⚠️ Mensagem de texto vazia ou inválida de 5511999999999
💬 ERRO TEXTO: ❌ Desculpe, não consegui processar sua mensagem...

❌ Tipo de mensagem não suportado: image de 5511999999999
💬 ERRO FORMATO: 📷 Desculpe, não consigo processar imagens...
```

---

## 🧪 Cenários de Teste

### **Cenários Implementados:**

1. **✅ Texto Válido**: "Olá, quero agendar uma consulta"
   - **Resultado**: Processado normalmente

2. **❌ Texto Vazio**: ""
   - **Resultado**: "Desculpe, não consegui processar sua mensagem..."

3. **❌ Texto com Espaços**: "   "
   - **Resultado**: "Desculpe, não consegui processar sua mensagem..."

4. **❌ Imagem**: Arquivo JPEG/PNG
   - **Resultado**: "📷 Desculpe, não consigo processar imagens..."

5. **❌ Áudio**: Arquivo MP3/OGG
   - **Resultado**: "🎵 Desculpe, não consigo processar áudios..."

6. **❌ Vídeo**: Arquivo MP4/AVI
   - **Resultado**: "🎬 Desculpe, não consigo processar vídeos..."

7. **❌ Documento**: Arquivo PDF/DOC
   - **Resultado**: "📄 Desculpe, não consigo processar documentos..."

8. **❌ Figurinha**: Sticker
   - **Resultado**: "😊 Desculpe, não consigo processar figurinhas..."

9. **❌ Localização**: Coordenadas GPS
   - **Resultado**: "📍 Desculpe, não consigo processar localizações..."

10. **❌ Contato**: Informações de contato
    - **Resultado**: "👥 Desculpe, não consigo processar contatos..."

11. **❌ Interativo**: Botões/Listas
    - **Resultado**: "🔘 Desculpe, não consigo processar mensagens interativas..."

---

## 📊 Estrutura do Webhook WhatsApp

### **Formato da Mensagem de Texto:**
```json
{
  "entry": [{
    "changes": [{
      "value": {
        "messages": [{
          "from": "5511999999999",
          "id": "wamid.xxx",
          "timestamp": "1699876543",
          "type": "text",
          "text": {
            "body": "Olá, quero agendar"
          }
        }]
      }
    }]
  }]
}
```

### **Formato de Mensagem de Imagem:**
```json
{
  "entry": [{
    "changes": [{
      "value": {
        "messages": [{
          "from": "5511999999999",
          "id": "wamid.xxx",
          "timestamp": "1699876543",
          "type": "image",
          "image": {
            "id": "image_id",
            "mime_type": "image/jpeg"
          }
        }]
      }
    }]
  }]
}
```

---

## 🔧 Fluxo de Validação

```
┌──────────────────────┐
│ Webhook recebe msg   │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Extrai message_type  │
└──────────┬───────────┘
           │
           ├─ type == 'text'? ─────► SIM ──┐
           │                                │
           └─ NÃO ──────────────────────────┤
                                            │
                                            ▼
                                  ┌──────────────────┐
                                  │ Valida conteúdo  │
                                  └────────┬─────────┘
                                           │
                                           ├─ Texto válido? ─► SIM ──┐
                                           │                          │
                                           └─ NÃO ──────────────┐    │
                                                                │    │
                                                                ▼    ▼
                                                      ┌──────────────────────┐
                                                      │ Processa com Gemini  │
                                                      └──────────────────────┘

┌──────────────────────┐
│ Tipo não text        │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Busca msg de erro    │
│ personalizada        │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Envia msg de erro    │
│ via WhatsApp         │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Loga erro            │
└──────────────────────┘
```

---

## 📈 Estatísticas de Rejeição

### **Consultas Úteis:**

```python
# No Django shell ou análise de logs

# Contar mensagens rejeitadas por tipo
from collections import Counter
import re

# Ler logs
with open('logs/django.log', 'r') as f:
    logs = f.readlines()

# Extrair tipos rejeitados
rejected_types = []
for line in logs:
    if 'Tipo de mensagem não suportado' in line:
        match = re.search(r'não suportado: (\w+)', line)
        if match:
            rejected_types.append(match.group(1))

# Contar por tipo
type_counts = Counter(rejected_types)
print(type_counts)
# {'image': 45, 'audio': 23, 'video': 12, 'document': 8, ...}
```

---

## ✅ Conclusão

### **Sistema de Validação Implementado**

A validação de formato de mensagem está:

- ✅ **Implementada** em `views.py` (linhas 107-199)
- ✅ **Funcionando** em produção
- ✅ **Testada** com todos os tipos de mídia
- ✅ **Documentada** completamente

### **Garantias do Sistema**

- ✅ **Apenas mensagens de texto válidas** são processadas
- ✅ **Todos os outros tipos** são rejeitados com mensagens claras
- ✅ **Logs detalhados** para monitoramento
- ✅ **Experiência consistente** para o usuário
- ✅ **Segurança** contra mídia maliciosa
- ✅ **Performance otimizada** do sistema

### **Fluxo de Validação**

```
WhatsApp → Webhook → Validação de Tipo → Validação de Conteúdo → 
{
  ✅ Válido: Processa com CoreService
  ❌ Inválido: Envia mensagem de erro apropriada
}
```

---

**📅 Última Atualização:** Novembro 15, 2025  
**📝 Versão:** 2.0 (Validado com código atual)  
**✅ Status:** Implementado e funcionando corretamente
