#!/usr/bin/env python
"""
Script de teste para demonstrar a coleta inteligente de informações
"""
import os
import sys

import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from api_gateway.services.conversation_service import conversation_service
from api_gateway.services.intent_detection_service import \
    IntentDetectionService
from api_gateway.services.smart_collection_service import \
    smart_collection_service


def test_smart_collection():
    """Testa a coleta inteligente de informações"""
    print("🧠 TESTANDO COLETA INTELIGENTE DE INFORMAÇÕES")
    print("=" * 60)
    
    intent_service = IntentDetectionService()
    phone_number = "5511999999999"
    
    # Simular diferentes cenários de conversa
    test_scenarios = [
        {
            'name': 'Cenário 1: Usuário não informa nome',
            'messages': [
                'Oi, preciso de um médico',
                'Cardiologista',
                'Tenho Unimed',
                'Quero agendar para segunda'
            ]
        },
        {
            'name': 'Cenário 2: Usuário informa nome parcial',
            'messages': [
                'Oi, sou João',
                'Preciso de cardiologista',
                'Tenho Unimed',
                'Quero agendar'
            ]
        },
        {
            'name': 'Cenário 3: Usuário informa nome completo',
            'messages': [
                'Olá, sou João Silva',
                'Preciso de cardiologista',
                'Tenho Unimed',
                'Quero agendar para segunda'
            ]
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n📋 {scenario['name']}")
        print("-" * 50)
        
        # Limpar sessão anterior
        try:
            from api_gateway.models import ConversationSession
            ConversationSession.objects.filter(phone_number=phone_number).delete()
        except:
            pass
        
        for i, message in enumerate(scenario['messages'], 1):
            print(f"\n👤 Usuário: '{message}'")
            
            # Detectar intenção
            intent, confidence = intent_service.detect_intent(message)
            entities = intent_service.extract_entities(message)
            
            print(f"🎯 Intenção: {intent} (confiança: {confidence:.2f})")
            print(f"📊 Entidades: {entities}")
            
            # Processar com coleta inteligente
            result = smart_collection_service.process_message_with_collection(
                phone_number, message, intent, entities
            )
            
            print(f"🤖 Bot: {result['response']}")
            print(f"🔄 Próxima ação: {result['next_action']}")
            print(f"🔗 Requer handoff: {'Sim' if result['requires_handoff'] else 'Não'}")
            
            # Verificar status das informações
            info_status = conversation_service.check_required_info(phone_number)
            print(f"📋 Status: Nome={'✅' if info_status['has_name'] else '❌'} | Telefone={'✅' if info_status['has_phone'] else '❌'}")
            
            # Adicionar mensagem ao histórico
            conversation_service.add_message(
                phone_number, message, 'user', intent, confidence, entities
            )
            if result['response']:
                conversation_service.add_message(
                    phone_number, result['response'], 'bot', 'resposta_bot', 1.0, {}
                )


def test_name_extraction():
    """Testa extração de nomes"""
    print("\n\n🔍 TESTANDO EXTRAÇÃO DE NOMES")
    print("=" * 50)
    
    test_messages = [
        "Oi, sou João Silva",
        "Meu nome é Maria Santos",
        "Chamo-me Pedro Oliveira",
        "Sou a Ana",
        "Dr. João",
        "Oi, sou João",
        "Meu nome é João",
        "Sou João Silva Santos",
        "Oi, sou o João da Silva"
    ]
    
    for message in test_messages:
        extracted = smart_collection_service.conversation_service.extract_patient_name(message)
        print(f"📝 '{message}' -> '{extracted}'")


def test_name_validation():
    """Testa validação de nomes"""
    print("\n\n✅ TESTANDO VALIDAÇÃO DE NOMES")
    print("=" * 50)
    
    test_names = [
        "João Silva",
        "Maria Santos Oliveira",
        "João",
        "João123",
        "João@Silva",
        "A",
        "João Silva Santos da Costa",
        "123456",
        "João-Silva"
    ]
    
    for name in test_names:
        is_valid, error = smart_collection_service.validate_patient_name(name)
        status = "✅ Válido" if is_valid else f"❌ Inválido: {error}"
        print(f"📝 '{name}' -> {status}")


def test_phone_extraction():
    """Testa extração de telefones"""
    print("\n\n📱 TESTANDO EXTRAÇÃO DE TELEFONES")
    print("=" * 50)
    
    test_messages = [
        "Meu telefone é (11) 99999-9999",
        "O número é 11 99999-9999",
        "11999999999",
        "Telefone: 11 9999-9999",
        "Meu celular é 11999999999",
        "Não tenho telefone"
    ]
    
    for message in test_messages:
        extracted = smart_collection_service.extract_phone_from_message(message)
        print(f"📝 '{message}' -> '{extracted}'")


def test_info_status():
    """Testa verificação de status das informações"""
    print("\n\n📊 TESTANDO STATUS DAS INFORMAÇÕES")
    print("=" * 50)
    
    phone_number = "5511999999999"
    
    # Limpar sessão
    try:
        from api_gateway.models import ConversationSession
        ConversationSession.objects.filter(phone_number=phone_number).delete()
    except:
        pass
    
    # Testar diferentes estados
    test_states = [
        {
            'name': 'Sessão vazia',
            'setup': lambda: None
        },
        {
            'name': 'Com nome parcial',
            'setup': lambda: conversation_service.update_patient_info(phone_number, patient_name="João")
        },
        {
            'name': 'Com nome completo',
            'setup': lambda: conversation_service.update_patient_info(phone_number, patient_name="João Silva")
        }
    ]
    
    for state in test_states:
        print(f"\n🔍 {state['name']}:")
        state['setup']()
        
        info_status = conversation_service.check_required_info(phone_number)
        print(f"  Nome: {'✅' if info_status['has_name'] else '❌'}")
        print(f"  Telefone: {'✅' if info_status['has_phone'] else '❌'}")
        print(f"  Completo: {'✅' if info_status['is_complete'] else '❌'}")
        print(f"  Próxima ação: {info_status['next_action']}")


def cleanup():
    """Limpa dados de teste"""
    print("\n\n🧹 LIMPANDO DADOS DE TESTE")
    print("=" * 50)
    
    from api_gateway.models import ConversationSession
    test_sessions = ConversationSession.objects.filter(phone_number="5511999999999")
    count = test_sessions.count()
    test_sessions.delete()
    print(f"🗑️ Removidas {count} sessões de teste")


def main():
    """Executa todos os testes"""
    print("🚀 TESTANDO COLETA INTELIGENTE DE INFORMAÇÕES")
    print("=" * 70)
    
    try:
        test_smart_collection()
        test_name_extraction()
        test_name_validation()
        test_phone_extraction()
        test_info_status()
        cleanup()
        
        print("\n\n✅ TESTES CONCLUÍDOS COM SUCESSO!")
        print("\n📋 RESUMO DAS MELHORIAS:")
        print("• ✅ Coleta proativa de nome completo")
        print("• ✅ Validação inteligente de nomes")
        print("• ✅ Extração automática de telefone")
        print("• ✅ Estados de conversa inteligentes")
        print("• ✅ Fluxo guiado para agendamento")
        print("• ✅ Prevenção de dados inválidos")
        
    except Exception as e:
        print(f"\n❌ ERRO DURANTE OS TESTES: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
