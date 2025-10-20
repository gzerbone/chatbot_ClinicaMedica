# 📝 Validação de Formato de Mensagem

## 🎯 Objetivo

Implementar validação robusta para garantir que o chatbot aceite apenas mensagens de texto válidas e rejeite todos os outros tipos de mídia com mensagens de erro apropriadas.

## ✅ Implementação

### **1. Validação de Mensagens de Texto**

```python
# Verificar se é mensagem de texto válida
if message_type == 'text':
    text_content = message.get('text', {}).get('body', '')

    # Validar se o conteúdo de texto não está vazio e tem tamanho mínimo
    if text_content and len(text_content.strip()) > 0:
        # Processar mensagem válida
        logger.info(f"👤 USUÁRIO ({from_number}): {text_content}")
        # ... processamento normal
    else:
        # Mensagem de texto vazia ou inválida
        logger.warning(f"⚠️ Mensagem de texto vazia ou inválida de {from_number}")
        response_text = "❌ Desculpe, não consegui processar sua mensagem. Por favor, envie uma mensagem de texto válida."
        whatsapp_service.send_message(from_number, response_text)
        logger.info(f"💬 ERRO TEXTO: {response_text}")
```

### **2. Rejeição de Outros Tipos de Mídia**

```python
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
```

## 📊 Tipos de Mensagem Suportados

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

## 🧪 Testes Implementados

### **Cenários de Teste:**

1. **✅ Texto Válido**: "Olá, quero agendar uma consulta"
2. **❌ Texto Vazio**: ""
3. **❌ Texto com Espaços**: "   "
4. **❌ Imagem**: Arquivo JPEG/PNG
5. **❌ Áudio**: Arquivo MP3/OGG
6. **❌ Vídeo**: Arquivo MP4/AVI
7. **❌ Documento**: Arquivo PDF/DOC
8. **❌ Figurinha**: Sticker
9. **❌ Localização**: Coordenadas GPS
10. **❌ Contato**: Informações de contato
11. **❌ Interativo**: Botões/Listas

### **Script de Teste:**
```bash
python scripts/test_message_validation.py
```

## 🎯 Resultado Final

A validação de formato garante que:

- ✅ **Apenas mensagens de texto válidas** são processadas
- ✅ **Todos os outros tipos** são rejeitados com mensagens claras
- ✅ **Logs detalhados** para monitoramento
- ✅ **Experiência consistente** para o usuário
- ✅ **Segurança** contra mídia maliciosa
- ✅ **Performance otimizada** do sistema

**Resultado**: Chatbot robusto que aceita apenas texto válido e orienta usuários sobre formatos suportados! 🚀
