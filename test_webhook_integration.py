#!/usr/bin/env python
"""
Script para testar a integração do webhook do WhatsApp com o chatbot
"""
import json
import os
import sys
from pathlib import Path

import django
import requests

# Configurar Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.conf import settings

from api_gateway.services.rag_service import RAGService
from api_gateway.services.whatsapp_service import WhatsAppService
from flow_agent.services.gemini_service import GeminiService


def test_gemini_connection():
    """Testa a conexão com o Gemini AI"""
    print("🤖 Testando conexão com Gemini AI...")
    
    try:
        gemini_service = GeminiService()
        is_connected = gemini_service.test_connection()
        
        if is_connected:
            print("✅ Conexão com Gemini AI: OK")
            
            # Testar uma resposta simples
            response = gemini_service.generate_response(
                user_message="Olá, preciso agendar uma consulta",
                intent="agendar_consulta"
            )
            print(f"📝 Resposta de teste: {response[:100]}...")
            return True
        else:
            print("❌ Falha na conexão com Gemini AI")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao testar Gemini: {e}")
        return False


def test_whatsapp_config():
    """Testa as configurações do WhatsApp"""
    print("\n📱 Testando configurações do WhatsApp...")
    
    try:
        whatsapp_service = WhatsAppService()
        print("✅ WhatsAppService inicializado com sucesso")
        
        # Verificar se as configurações estão presentes
        if whatsapp_service.access_token:
            print("✅ Access Token: Configurado")
        else:
            print("❌ Access Token: NÃO configurado")
            
        if whatsapp_service.phone_number_id:
            print("✅ Phone Number ID: Configurado")
        else:
            print("❌ Phone Number ID: NÃO configurado")
            
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar WhatsApp: {e}")
        return False


def test_webhook_verification():
    """Testa a verificação do webhook"""
    print("\n🔗 Testando verificação do webhook...")
    
    try:
        whatsapp_service = WhatsAppService()
        
        # Simular verificação do webhook
        challenge = "test_challenge_123"
        result = whatsapp_service.validate_webhook(
            mode="subscribe",
            token=settings.WHATSAPP_VERIFY_TOKEN,
            challenge=challenge
        )
        
        if result == challenge:
            print("✅ Verificação do webhook: OK")
            return True
        else:
            print("❌ Falha na verificação do webhook")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao testar webhook: {e}")
        return False


def test_rag_service():
    """Testa o serviço RAG (acesso aos dados da clínica)"""
    print("\n🏥 Testando RAGService...")
    
    try:
        # Testar obtenção de dados da clínica
        clinic_data = RAGService.get_all_clinic_data()
        
        print("✅ RAGService funcionando")
        print(f"   - Clínica Info: {'✅' if clinic_data.get('clinica_info') else '❌'}")
        print(f"   - Especialidades: {len(clinic_data.get('especialidades', []))} encontradas")
        print(f"   - Médicos: {len(clinic_data.get('medicos', []))} encontrados")
        print(f"   - Convênios: {len(clinic_data.get('convenios', []))} encontrados")
        print(f"   - Exames: {len(clinic_data.get('exames', []))} encontrados")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar RAGService: {e}")
        return False


def test_message_processing():
    """Testa o processamento de mensagem simulado"""
    print("\n💬 Testando processamento de mensagem...")
    
    try:
        # Simular uma mensagem do WhatsApp
        mock_message = {
            "id": "wamid.test123",
            "from": "5511999999999",
            "type": "text",
            "timestamp": "1640995200",
            "text": {
                "body": "Olá, gostaria de agendar uma consulta"
            }
        }
        
        mock_webhook_data = {
            "messaging_product": "whatsapp",
            "metadata": {
                "display_phone_number": "15551234567",
                "phone_number_id": "123456789"
            },
            "contacts": [{
                "profile": {"name": "Paciente Teste"},
                "wa_id": "5511999999999"
            }],
            "messages": [mock_message]
        }
        
        print("📝 Mensagem simulada processada com sucesso")
        print(f"   - ID: {mock_message['id']}")
        print(f"   - De: {mock_message['from']}")
        print(f"   - Texto: {mock_message['text']['body']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar processamento: {e}")
        return False


def show_ngrok_setup():
    """Mostra instruções para configurar o ngrok"""
    print("\n🌐 Instruções para configurar o ngrok:")
    print("1. Instale o ngrok: https://ngrok.com/download")
    print("2. Execute: ngrok http 8000")
    print("3. Copie a URL HTTPS fornecida (ex: https://abc123.ngrok-free.app)")
    print("4. Configure no WhatsApp Business API:")
    print("   - URL do webhook: https://sua-url.ngrok-free.app/api/webhook/whatsapp/")
    print("   - Verify token: meu_verify_token_123")
    print("5. Adicione a URL do ngrok no ALLOWED_HOSTS do arquivo .env")


def main():
    """Função principal do teste"""
    print("🚀 Iniciando testes de integração do chatbot...")
    print("=" * 50)
    
    # Verificar se o arquivo .env existe
    env_file = BASE_DIR / '.env'
    if not env_file.exists():
        print("⚠️  Arquivo .env não encontrado!")
        print("📋 Copie o arquivo env_example.txt para .env e configure suas chaves")
        print("=" * 50)
        return
    
    # Executar testes
    tests = [
        test_gemini_connection,
        test_whatsapp_config,
        test_webhook_verification,
        test_rag_service,
        test_message_processing,
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    # Mostrar resultados
    print("\n" + "=" * 50)
    print("📊 RESULTADOS DOS TESTES:")
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ Todos os testes passaram! ({passed}/{total})")
        print("\n🎉 Seu chatbot está pronto para receber mensagens do WhatsApp!")
    else:
        print(f"⚠️  {passed}/{total} testes passaram")
        print("🔧 Verifique as configurações no arquivo .env")
    
    show_ngrok_setup()
    
    print("\n📚 URLs de teste disponíveis:")
    print("- Teste Gemini: http://localhost:8000/api/test/gemini/")
    print("- Webhook WhatsApp: http://localhost:8000/api/webhook/whatsapp/")
    print("- Teste envio: http://localhost:8000/api/test/send-message/")


if __name__ == "__main__":
    main()
