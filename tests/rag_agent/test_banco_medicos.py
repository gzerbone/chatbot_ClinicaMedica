#!/usr/bin/env python
"""
Teste para verificar médicos no banco e handoff
"""
import os
import sys
from pathlib import Path

import django

# Configurar Django
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from api_gateway.services.context_manager import context_manager
from api_gateway.services.handoff_service import handoff_service
from api_gateway.services.rag_service import RAGService


def main():
    print("🏥 MÉDICOS NO BANCO DE DADOS:")
    print("=" * 40)
    
    # Listar médicos
    medicos = RAGService.get_medicos()
    
    for i, medico in enumerate(medicos, 1):
        nome = medico.get('nome', 'N/A')
        crm = medico.get('crm', 'N/A')
        especialidades = medico.get('especialidades', [])
        convenios = medico.get('convenios', [])
        
        print(f"{i}. {nome} (CRM: {crm})")
        print(f"   Especialidades: {especialidades}")
        print(f"   Convênios: {convenios}")
        print()
    
    if medicos:
        # Testar com primeiro médico
        primeiro_medico = medicos[0]['nome']
        print(f"🧪 TESTANDO HANDOFF COM: {primeiro_medico}")
        print("=" * 40)
        
        # Testar busca específica
        medico_data = RAGService.get_medico_by_name(primeiro_medico)
        if medico_data:
            print("✅ Médico encontrado no banco!")
            print(f"   Nome: {medico_data.get('nome')}")
            print(f"   CRM: {medico_data.get('crm')}")
        else:
            print("❌ Médico não encontrado")
        
        # Testar especialidade
        specialty = RAGService.get_doctor_specialty(primeiro_medico)
        print(f"   Especialidade: {specialty}")
        
        # Testar convênios
        convenios = RAGService.get_doctor_insurances(primeiro_medico)
        print(f"   Convênios: {convenios}")
        
        # Testar handoff
        print("\n🔗 TESTANDO GERAÇÃO DE LINK:")
        link = handoff_service.generate_appointment_handoff_link(
            patient_name="Paciente Teste",
            doctor_name=primeiro_medico,
            date="15/09/2025",
            time="14:30"
        )
        
        print("✅ Link gerado com dados reais do banco!")
        print(f"Link: {link[:80]}...")
        
    else:
        print("❌ Nenhum médico encontrado no banco de dados")


if __name__ == "__main__":
    main()
