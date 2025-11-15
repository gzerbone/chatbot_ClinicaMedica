#!/usr/bin/env python
"""
Teste específico para verificar formato do link de handoff
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

from api_gateway.services.handoff_service import handoff_service


def test_link_format():
    """Testa se o link está no formato correto especificado"""
    
    print("🔗 TESTANDO FORMATO DO LINK DE HANDOFF")
    print("=" * 60)
    
    # Dados de teste
    patient_name = "Maria Silva"
    doctor_name = "Dr. Gustavo Magno"
    specialty = "Pneumologia"
    date = "27/08/2025"
    time = "10h"
    
    # Gerar link
    link = handoff_service.generate_appointment_handoff_link(
        patient_name=patient_name,
        doctor_name=doctor_name,
        specialty=specialty,
        date=date,
        time=time
    )
    
    print("📋 DADOS DE ENTRADA:")
    print(f"   👤 Nome do Paciente: {patient_name}")
    print(f"   👨‍⚕️ Médico: {doctor_name}")
    print(f"   🩺 Especialidade: {specialty}")
    print(f"   📅 Data/Hora: {date} às {time}")
    
    print(f"\n🔗 LINK GERADO:")
    print(f"{link}")
    
    # Verificações específicas
    print(f"\n✅ VERIFICAÇÕES:")
    
    checks = {
        'Base URL': link.startswith('https://api.whatsapp.com/send?phone='),
        'Phone parameter': 'phone=' in link,
        'Text parameter': 'text=' in link,
        'Nome do paciente': 'Maria' in link or 'Silva' in link,
        'Nome do médico': 'Gustavo' in link or 'Magno' in link,
        'Especialidade': 'Pneumologia' in link,
        'Data': '27' in link and '2025' in link
    }
    
    all_passed = True
    for check_name, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {check_name}: {'OK' if passed else 'FALHOU'}")
        if not passed:
            all_passed = False
    
    # Decodificar para mostrar resultado final
    import urllib.parse
    text_param = link.split('text=')[1] if 'text=' in link else ''
    decoded_message = urllib.parse.unquote(text_param)
    
    print(f"\n📝 MENSAGEM DECODIFICADA (que a secretária vê):")
    print("-" * 50)
    print(decoded_message)
    print("-" * 50)
    
    expected_lines = [
        "Agendamento via Chatbot:",
        f"Paciente: {patient_name}",
        f"Médico: {doctor_name.replace('Dr. ', '').replace('Dra. ', '')}",
        f"Especialidade: {specialty}",
        f"Data/Horário: {date} às {time}"
    ]
    
    for expected_line in expected_lines:
        if expected_line not in decoded_message:
            all_passed = False
            print(f"   ❌ Linha ausente: {expected_line}")
    
    if all_passed:
        print("\n🎉 FORMATO CORRETO! Link está no padrão especificado.")
    else:
        print("\n⚠️ Formato precisa de ajustes.")
    
    return all_passed


if __name__ == "__main__":
    test_link_format()
