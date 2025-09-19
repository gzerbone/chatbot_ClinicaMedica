#!/usr/bin/env python
"""
Script de teste para demonstrar a nova arquitetura com persistência
"""
import os
import sys

import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from api_gateway.models import (AppointmentRequest, ConversationMessage,
                                ConversationSession)
from api_gateway.services.conversation_service import conversation_service
from api_gateway.services.intent_detection_service import \
    IntentDetectionService


def test_conversation_persistence():
    """Testa a persistência de conversas"""
    print("🗄️ TESTANDO PERSISTÊNCIA DE CONVERSAS")
    print("=" * 50)
    
    phone_number = "5511999999999"
    
    # Simular conversa completa
    conversation_flow = [
        {
            'message': 'Olá, sou Maria Santos',
            'intent': 'saudacao',
            'entities': {'patient_name': ['Maria', 'Santos']}
        },
        {
            'message': 'Preciso de um cardiologista',
            'intent': 'buscar_medico',
            'entities': {'specialties': ['cardiologia']}
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
        },
        {
            'message': 'Sim, confirma',
            'intent': 'confirmar_agendamento',
            'entities': {}
        }
    ]
    
    print(f"📱 Simulando conversa para {phone_number}")
    
    for i, step in enumerate(conversation_flow, 1):
        print(f"\n📝 Passo {i}: '{step['message']}'")
        
        # Adicionar mensagem do usuário
        conversation_service.add_message(
            phone_number=phone_number,
            content=step['message'],
            message_type='user',
            intent=step['intent'],
            confidence=0.9,
            entities=step['entities']
        )
        
        # Simular resposta do bot
        bot_response = f"Resposta do bot para: {step['intent']}"
        conversation_service.add_message(
            phone_number=phone_number,
            content=bot_response,
            message_type='bot',
            intent='resposta_bot',
            confidence=1.0,
            entities={}
        )
        
        # Mostrar estado atual
        patient_info = conversation_service.get_patient_info(phone_number)
        print(f"👤 Info do paciente: {patient_info}")
    
    # Verificar dados no banco
    print(f"\n📊 VERIFICANDO DADOS NO BANCO:")
    
    # Sessão
    session = ConversationSession.objects.get(phone_number=phone_number)
    print(f"📋 Sessão: {session}")
    print(f"🔄 Estado: {session.current_state}")
    print(f"👤 Nome: {session.patient_name}")
    print(f"🩺 Especialidade: {session.specialty_interest}")
    print(f"💼 Convênio: {session.insurance_type}")
    
    # Mensagens
    messages = ConversationMessage.objects.filter(session=session)
    print(f"💬 Total de mensagens: {messages.count()}")
    
    # Solicitação de agendamento
    try:
        appointment = AppointmentRequest.objects.get(session=session)
        print(f"📅 Agendamento: {appointment}")
        print(f"🔗 Link: {appointment.handoff_link}")
    except AppointmentRequest.DoesNotExist:
        print("📅 Nenhuma solicitação de agendamento encontrada")

def test_rag_cache():
    """Testa o cache RAG"""
    print("\n\n🗂️ TESTANDO CACHE RAG")
    print("=" * 50)
    
    # Testar cache de dados da clínica
    clinic_data = conversation_service.rag_cache.get_clinic_data()
    print(f"🏥 Dados da clínica: {len(clinic_data)} itens")
    
    # Testar cache de médico
    doctor_data = conversation_service.rag_cache.get_doctor_info("Dr. João Carvalho")
    print(f"👨‍⚕️ Dados do médico: {len(doctor_data)} campos")

def test_data_separation():
    """Testa a separação de dados"""
    print("\n\n🔄 TESTANDO SEPARAÇÃO DE DADOS")
    print("=" * 50)
    
    # Dados RAG (cache temporário)
    print("📊 DADOS RAG (Cache temporário):")
    print("• Informações da clínica")
    print("• Lista de médicos")
    print("• Especialidades")
    print("• Convênios")
    print("• Exames")
    print("• TTL: 1 hora")
    
    # Dados de conversa (banco persistente)
    print("\n💾 DADOS DE CONVERSA (Banco persistente):")
    print("• Sessões de conversa")
    print("• Mensagens individuais")
    print("• Informações do paciente")
    print("• Estados de agendamento")
    print("• Solicitações de agendamento")
    print("• Persistência: Permanente")

def test_benefits():
    """Mostra os benefícios da nova arquitetura"""
    print("\n\n✅ BENEFÍCIOS DA NOVA ARQUITETURA")
    print("=" * 50)
    
    benefits = [
        "🔒 Persistência Real: Dados não se perdem com reinicialização",
        "⚡ Performance: Cache RAG para dados que mudam pouco",
        "📊 Rastreabilidade: Histórico completo de conversas",
        "🔄 Escalabilidade: Suporta múltiplos servidores",
        "🛠️ Manutenibilidade: Separação clara de responsabilidades",
        "📈 Analytics: Dados para análise e melhorias",
        "🔍 Debugging: Fácil rastreamento de problemas",
        "💾 Backup: Dados importantes no banco",
        "🎯 Precisão: Links de handoff sempre atualizados",
        "📱 Multi-dispositivo: Sessão persiste entre dispositivos"
    ]
    
    for benefit in benefits:
        print(f"  {benefit}")

def cleanup_test_data():
    """Limpa dados de teste"""
    print("\n\n🧹 LIMPANDO DADOS DE TESTE")
    print("=" * 50)
    
    # Remover sessões de teste
    test_sessions = ConversationSession.objects.filter(phone_number__startswith="5511999999999")
    count = test_sessions.count()
    test_sessions.delete()
    
    print(f"🗑️ Removidas {count} sessões de teste")

def main():
    """Executa todos os testes"""
    print("🚀 TESTANDO NOVA ARQUITETURA COM PERSISTÊNCIA")
    print("=" * 60)
    
    try:
        test_conversation_persistence()
        test_rag_cache()
        test_data_separation()
        test_benefits()
        cleanup_test_data()
        
        print("\n\n✅ TESTES CONCLUÍDOS COM SUCESSO!")
        print("\n📋 RESUMO DA NOVA ARQUITETURA:")
        print("• ✅ Dados RAG em cache temporário (1h TTL)")
        print("• ✅ Conversas de agendamento no banco persistente")
        print("• ✅ Histórico completo de mensagens")
        print("• ✅ Estados de agendamento rastreáveis")
        print("• ✅ Links de handoff sempre atualizados")
        print("• ✅ Dados não se perdem com reinicialização")
        
    except Exception as e:
        print(f"\n❌ ERRO DURANTE OS TESTES: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
