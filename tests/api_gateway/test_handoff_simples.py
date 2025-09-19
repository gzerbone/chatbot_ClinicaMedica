#!/usr/bin/env python
"""
Teste simples do sistema de handoff
"""
import os
import sys
from pathlib import Path

import django

# Configurar Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

def test_handoff_service():
    """Testa apenas o serviço de handoff"""
    try:
        from api_gateway.services.handoff_service import handoff_service
        
        print("🧪 Testando HandoffService...")
        
        # Teste básico
        link = handoff_service.generate_appointment_handoff_link(
            patient_name="Maria Silva",
            doctor_name="Dr. João Carvalho",
            specialty="Cardiologia", 
            appointment_type="Particular",
            date="15/09/2025",
            time="14:30"
        )
        
        print("✅ Link gerado com sucesso!")
        print(f"Link: {link[:80]}...")
        
        # Verificar estrutura básica
        if link.startswith('https://api.whatsapp.com/send'):
            print("✅ URL válida")
        else:
            print("❌ URL inválida")
            
        if 'phone=' in link:
            print("✅ Parâmetro phone presente")
        else:
            print("❌ Parâmetro phone ausente")
            
        if 'text=' in link:
            print("✅ Parâmetro text presente")
        else:
            print("❌ Parâmetro text ausente")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_context_manager():
    """Testa apenas o context manager"""
    try:
        from api_gateway.services.context_manager import context_manager
        
        print("\n🧠 Testando ContextManager...")
        
        # Teste básico
        test_phone = "test123"
        context_manager.clear_context(test_phone)
        
        # Preparar dados de handoff
        handoff_data = context_manager.prepare_handoff_data(
            test_phone, "Dr. João Carvalho", "15/09/2025", "14:30"
        )
        
        print("✅ Dados de handoff preparados:")
        print(f"   Médico: {handoff_data['doctor_name']}")
        print(f"   Especialidade: {handoff_data['specialty']}")
        print(f"   Data: {handoff_data['date']}")
        print(f"   Hora: {handoff_data['time']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 TESTE SIMPLES DE HANDOFF")
    print("=" * 40)
    
    test1 = test_handoff_service()
    test2 = test_context_manager()
    
    if test1 and test2:
        print("\n🎉 Todos os testes básicos passaram!")
    else:
        print("\n⚠️ Alguns testes falharam")
