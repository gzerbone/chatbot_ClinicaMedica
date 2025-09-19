#!/usr/bin/env python
"""
Debug para investigar por que especialidades e convênios estão vazios
"""
import os
import sys

import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from rag_agent.models import Convenio, Especialidade, Medico
from rag_agent.serializers import MedicoResumoSerializer, MedicoSerializer


def debug_medicos():
    print("🔍 DEBUG - INVESTIGANDO MÉDICOS, ESPECIALIDADES E CONVÊNIOS")
    print("=" * 60)
    
    # 1. Verificar médicos
    print("\n1. MÉDICOS NO BANCO:")
    medicos = Medico.objects.all()
    print(f"Total de médicos: {medicos.count()}")
    
    for medico in medicos:
        print(f"\n- {medico.nome} (CRM: {medico.crm})")
        print(f"  Especialidades relacionadas: {medico.especialidades.count()}")
        print(f"  Convênios relacionados: {medico.convenios.count()}")
        
        # Verificar especialidades específicas
        especialidades = medico.especialidades.all()
        print(f"  Especialidades: {[esp.nome for esp in especialidades]}")
        
        # Verificar convênios específicos
        convenios = medico.convenios.all()
        print(f"  Convênios: {[conv.nome for conv in convenios]}")
    
    # 2. Verificar especialidades
    print("\n2. ESPECIALIDADES NO BANCO:")
    especialidades = Especialidade.objects.all()
    print(f"Total de especialidades: {especialidades.count()}")
    
    for esp in especialidades:
        print(f"- {esp.nome} (Ativa: {esp.ativa})")
        print(f"  Médicos com esta especialidade: {esp.medicos.count()}")
    
    # 3. Verificar convênios
    print("\n3. CONVÊNIOS NO BANCO:")
    convenios = Convenio.objects.all()
    print(f"Total de convênios: {convenios.count()}")
    
    for conv in convenios:
        print(f"- {conv.nome}")
        print(f"  Médicos com este convênio: {conv.medicos.count()}")
    
    # 4. Testar serializer completo
    print("\n4. TESTANDO SERIALIZER COMPLETO:")
    if medicos.exists():
        medico = medicos.first()
        serializer_completo = MedicoSerializer(medico)
        print("Dados do serializer completo:")
        print(f"  Especialidades: {serializer_completo.data.get('especialidades', [])}")
        print(f"  Convênios: {serializer_completo.data.get('convenios', [])}")
    
    # 5. Testar serializer resumo
    print("\n5. TESTANDO SERIALIZER RESUMO:")
    if medicos.exists():
        medico = medicos.first()
        serializer_resumo = MedicoResumoSerializer(medico)
        print("Dados do serializer resumo:")
        print(f"  Campos disponíveis: {list(serializer_resumo.data.keys())}")
        print(f"  Especialidades display: {serializer_resumo.data.get('especialidades_display', 'N/A')}")
    
    # 6. Testar RAGService
    print("\n6. TESTANDO RAGService.get_medicos():")
    from api_gateway.services.rag_service import RAGService
    medicos_rag = RAGService.get_medicos()
    print(f"Total retornado pelo RAGService: {len(medicos_rag)}")
    
    if medicos_rag:
        primeiro = medicos_rag[0]
        print(f"Primeiro médico do RAGService:")
        print(f"  Nome: {primeiro.get('nome')}")
        print(f"  CRM: {primeiro.get('crm')}")
        print(f"  Campos disponíveis: {list(primeiro.keys())}")
        print(f"  Especialidades display: {primeiro.get('especialidades_display', 'N/A')}")

if __name__ == "__main__":
    debug_medicos()
