#!/usr/bin/env python
"""
Script para auxiliar na configuração do Google Calendar para desenvolvimento
"""
import json
import os
from pathlib import Path


def check_service_account_file():
    """Verifica se o arquivo de conta de serviço existe"""
    service_file = Path('service-account-key.json')
    
    if not service_file.exists():
        print("❌ Arquivo service-account-key.json não encontrado!")
        print("\n📋 Para criar o arquivo:")
        print("1. Acesse https://console.cloud.google.com")
        print("2. Crie um projeto (ex: chatbot-clinica-teste)")
        print("3. Habilite Google Calendar API")
        print("4. Crie conta de serviço")
        print("5. Baixe chave JSON e renomeie para 'service-account-key.json'")
        print("6. Coloque na pasta do projeto")
        return False
    
    try:
        with open(service_file, 'r') as f:
            data = json.load(f)
        
        client_email = data.get('client_email', '')
        project_id = data.get('project_id', '')
        
        print("✅ Arquivo service-account-key.json encontrado!")
        print(f"   📧 Email da conta: {client_email}")
        print(f"   🏗️ Projeto: {project_id}")
        
        return True, client_email
        
    except Exception as e:
        print(f"❌ Erro ao ler arquivo: {e}")
        return False


def check_env_file():
    """Verifica configuração do arquivo .env"""
    env_file = Path('.env')
    
    if not env_file.exists():
        print("❌ Arquivo .env não encontrado!")
        print("📋 Copie env_example.txt para .env e configure")
        return False
    
    try:
        with open(env_file, 'r') as f:
            content = f.read()
        
        config_checks = {
            'GOOGLE_CALENDAR_ENABLED': 'GOOGLE_CALENDAR_ENABLED=True' in content,
            'CLINIC_CALENDAR_ID': 'CLINIC_CALENDAR_ID=' in content and 'seu_calendar_id_aqui' not in content,
            'SERVICE_ACCOUNT_FILE': 'GOOGLE_SERVICE_ACCOUNT_FILE=service-account-key.json' in content
        }
        
        print("📋 Verificação do arquivo .env:")
        for key, status in config_checks.items():
            status_icon = "✅" if status else "❌"
            print(f"   {status_icon} {key}: {'Configurado' if status else 'Precisa configurar'}")
        
        all_configured = all(config_checks.values())
        
        if not all_configured:
            print("\n🔧 Para corrigir:")
            if not config_checks['GOOGLE_CALENDAR_ENABLED']:
                print("   - Defina GOOGLE_CALENDAR_ENABLED=True")
            if not config_checks['CLINIC_CALENDAR_ID']:
                print("   - Configure CLINIC_CALENDAR_ID com o ID do seu calendário")
            if not config_checks['SERVICE_ACCOUNT_FILE']:
                print("   - Defina GOOGLE_SERVICE_ACCOUNT_FILE=service-account-key.json")
        
        return all_configured
        
    except Exception as e:
        print(f"❌ Erro ao ler .env: {e}")
        return False


def generate_calendar_instructions(client_email):
    """Gera instruções específicas para compartilhar calendário"""
    print("\n📅 INSTRUÇÕES PARA CONFIGURAR SEU CALENDÁRIO:")
    print("=" * 60)
    
    print("\n1️⃣ CRIAR CALENDÁRIO:")
    print("   • Acesse https://calendar.google.com")
    print("   • Faça login com gzerbone@gmail.com")
    print("   • Clique no '+' ao lado de 'Outros calendários'")
    print("   • Selecione 'Criar novo calendário'")
    print("   • Nome: 'Agenda Clínica Teste'")
    print("   • Clique 'Criar calendário'")
    
    print("\n2️⃣ OBTER CALENDAR ID:")
    print("   • No calendário criado, clique nos 3 pontos")
    print("   • Selecione 'Configurações e compartilhamento'")
    print("   • Role até 'Integrar calendário'")
    print("   • COPIE o 'ID do calendário'")
    print("   • Exemplo: c_1a2b3c4d@group.calendar.google.com")
    
    print("\n3️⃣ COMPARTILHAR COM CONTA DE SERVIÇO:")
    print("   • Na mesma tela, vá em 'Compartilhar com pessoas específicas'")
    print("   • Clique '+ Adicionar pessoas'")
    print(f"   • Email: {client_email}")
    print("   • Permissão: 'Ver todos os detalhes do evento'")
    print("   • Clique 'Enviar'")
    
    print("\n4️⃣ CONFIGURAR .env:")
    print("   • Abra o arquivo .env")
    print("   • Encontre CLINIC_CALENDAR_ID=")
    print("   • Substitua pelo ID copiado no passo 2")
    print("   • Salve o arquivo")
    
    print("\n5️⃣ CRIAR EVENTOS DE TESTE:")
    print("   • No Google Calendar, crie alguns eventos:")
    print("   • 'Dr. João Carvalho - Consulta' (amanhã 09:00)")
    print("   • 'Dr. João Carvalho - Retorno' (amanhã 14:00)")
    print("   • 'Dra. Maria Santos - Consulta' (amanhã 15:30)")


def main():
    """Função principal do script de setup"""
    print("🚀 CONFIGURAÇÃO DO GOOGLE CALENDAR PARA DESENVOLVIMENTO")
    print("=" * 65)
    print("📧 Usando email: gzerbone@gmail.com")
    print("📅 Calendário: Agenda Clínica Teste")
    print()
    
    # Verificar arquivo de conta de serviço
    service_result = check_service_account_file()
    if not service_result:
        return
    
    client_email = service_result[1] if isinstance(service_result, tuple) else None
    
    print()
    
    # Verificar arquivo .env
    env_configured = check_env_file()
    
    print()
    
    if client_email:
        generate_calendar_instructions(client_email)
    
    print("\n" + "=" * 65)
    
    if env_configured and client_email:
        print("🎉 CONFIGURAÇÃO COMPLETA!")
        print("✅ Execute: python test_calendar.py")
    else:
        print("🔧 CONFIGURAÇÃO INCOMPLETA")
        print("📋 Siga as instruções acima para finalizar")
    
    print("\n📚 Documentação completa: SETUP_CALENDAR_DESENVOLVIMENTO.md")


if __name__ == "__main__":
    main()
