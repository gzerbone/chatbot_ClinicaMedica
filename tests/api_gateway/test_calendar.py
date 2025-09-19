#!/usr/bin/env python
"""
Script para testar a integração com Google Calendar
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

from api_gateway.services.google_calendar_service import \
    google_calendar_service
from api_gateway.services.rag_service import RAGService


def test_calendar_integration():
    """Testa integração com Google Calendar"""
    print("🧪 Testando Google Calendar Service...")
    print(f"Habilitado: {google_calendar_service.enabled}")
    
    # Testar disponibilidade simulada
    print("\n📅 Testando disponibilidade do Dr. João...")
    availability = RAGService.get_doctor_availability("Dr. João Silva", 5)
    
    print(f"Médico: {availability.get('doctor_name', 'N/A')}")
    print(f"Período: {availability.get('period', 'N/A')}")
    print(f"Dados simulados: {availability.get('mock_data', False)}")
    
    if availability.get('days'):
        print(f"Dias disponíveis: {len(availability['days'])}")
        for day in availability['days'][:2]:  # Mostrar apenas 2 primeiros dias
            print(f"  📆 {day['date']} ({day['weekday']}): {day['available_times']}")
    
    print("\n📊 Testando disponibilidade de todos os médicos...")
    all_availability = RAGService.get_all_doctors_availability(3)
    
    if 'doctors' in all_availability:
        print(f"Total de médicos: {len(all_availability['doctors'])}")
        for doctor_data in all_availability['doctors'][:2]:
            doctor_name = doctor_data.get('doctor_name', 'N/A')
            days_count = len(doctor_data.get('days', []))
            print(f"  👨‍⚕️ {doctor_name}: {days_count} dias disponíveis")
    
    print("\n✅ Teste concluído!")


if __name__ == "__main__":
    test_calendar_integration()
