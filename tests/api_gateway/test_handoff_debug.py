#!/usr/bin/env python
"""
Script de debug para testar o handoff
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
from api_gateway.views import handle_appointment_confirmation


def test_intent_detection():
    """Testa detecção de intenções para agendamento"""
    print("🔍 TESTANDO DETECÇÃO DE INTENÇÕES")
    print("=" * 50)
    
    intent_service = IntentDetectionService()
    
    test_messages = [
        "Quero agendar consulta",
        "Preciso marcar uma consulta",
        "Sim, confirma o agendamento",
        "Confirmar consulta",
        "Quero o Dr. João",
        "Segunda às 14h"
    ]
    
    for message in test_messages:
        intent, confidence = intent_service.detect_intent(message)
        entities = intent_service.extract_entities(message)
        
        print(f"\n📝 Mensagem: '{message}'")
        print(f"🎯 Intenção: {intent} (confiança: {confidence:.2f})")
        print(f"📊 Entidades: {entities}")
        
        # Verificar se seria detectado para handoff
        would_trigger_handoff = (
            intent in ['confirmar_agendamento', 'agendar_consulta'] or 
            'confirmar' in intent
        )
        print(f"🔗 Geraria handoff: {'✅ SIM' if would_trigger_handoff else '❌ NÃO'}")

def test_handoff_flow():
    """Testa o fluxo completo de handoff"""
    print("\n\n🔗 TESTANDO FLUXO DE HANDOFF")
    print("=" * 50)
    
    intent_service = IntentDetectionService()
    phone_number = "5511999999999"
    
    # Simular conversa de agendamento
    conversation_steps = [
        {
            'message': 'Olá, sou João Silva',
            'intent': 'saudacao',
            'entities': {'patient_name': ['João', 'Silva']}
        },
        {
            'message': 'Preciso de um cardiologista',
            'intent': 'buscar_medico',
            'entities': {'specialties': ['cardiologia']}
        },
        {
            'message': 'Quero o Dr. João Carvalho',
            'intent': 'buscar_medico',
            'entities': {'doctors': ['João Carvalho']}
        },
        {
            'message': 'Tenho Unimed',
            'intent': 'buscar_info_clinica',
            'entities': {'insurance': 'Unimed'}
        },
        {
            'message': 'Quero agendar para segunda às 14h',
            'intent': 'agendar_consulta',
            'entities': {'dates': ['segunda'], 'times': ['14:00']}
        }
    ]
    
    print(f"📱 Simulando conversa para {phone_number}")
    
    # Adicionar mensagens à conversa
    for step in conversation_steps:
        conversation_service.add_message(
            phone_number=phone_number,
            content=step['message'],
            message_type='user',
            intent=step['intent'],
            confidence=0.9,
            entities=step['entities']
        )
        print(f"✅ Adicionada: '{step['message']}' -> {step['intent']}")
    
    # Verificar informações do paciente
    patient_info = conversation_service.get_patient_info(phone_number)
    print(f"\n👤 Informações do paciente: {patient_info}")
    
    # Testar handoff
    print(f"\n🔗 TESTANDO HANDOFF:")
    
    try:
        # Simular confirmação
        confirmation_message = "Sim, confirma o agendamento"
        intent, confidence = intent_service.detect_intent(confirmation_message)
        entities = intent_service.extract_entities(confirmation_message)
        
        print(f"📝 Mensagem de confirmação: '{confirmation_message}'")
        print(f"🎯 Intenção detectada: {intent}")
        
        # Verificar se seria detectado
        would_trigger = (
            intent in ['confirmar_agendamento', 'agendar_consulta'] or 
            'confirmar' in intent
        )
        print(f"🔗 Seria detectado para handoff: {'✅ SIM' if would_trigger else '❌ NÃO'}")
        
        if would_trigger:
            # Obter histórico
            conversation_history = conversation_service.get_conversation_history(phone_number, limit=5)
            
            # Chamar função de handoff
            response = handle_appointment_confirmation(
                phone_number, confirmation_message, intent, entities, conversation_history
            )
            
            print(f"\n🤖 Resposta gerada:")
            print(f"{response}")
            
            # Verificar se contém link
            if "https://api.whatsapp.com" in response:
                print("✅ Link de handoff gerado com sucesso!")
            else:
                print("❌ Link de handoff NÃO foi gerado!")
        else:
            print("❌ Intenção não foi detectada corretamente para handoff")
            
    except Exception as e:
        print(f"❌ Erro durante teste de handoff: {e}")
        import traceback
        traceback.print_exc()

def test_condition_logic():
    """Testa a lógica de condição"""
    print("\n\n🧪 TESTANDO LÓGICA DE CONDIÇÃO")
    print("=" * 50)
    
    test_cases = [
        ('confirmar_agendamento', True),
        ('agendar_consulta', True),
        ('confirmar_consulta', True),
        ('buscar_medico', False),
        ('saudacao', False),
        ('confirmar', True),  # Deveria ser True
    ]
    
    for intent, expected in test_cases:
        result = (
            intent in ['confirmar_agendamento', 'agendar_consulta'] or 
            'confirmar' in intent
        )
        
        status = "✅" if result == expected else "❌"
        print(f"{status} {intent}: {result} (esperado: {expected})")

def cleanup():
    """Limpa dados de teste"""
    from api_gateway.models import ConversationSession
    test_sessions = ConversationSession.objects.filter(phone_number="5511999999999")
    count = test_sessions.count()
    test_sessions.delete()
    print(f"\n🧹 Removidas {count} sessões de teste")

def main():
    """Executa todos os testes"""
    print("🐛 DEBUG DO HANDOFF")
    print("=" * 60)
    
    try:
        test_intent_detection()
        test_condition_logic()
        test_handoff_flow()
        cleanup()
        
    except Exception as e:
        print(f"\n❌ ERRO DURANTE OS TESTES: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
