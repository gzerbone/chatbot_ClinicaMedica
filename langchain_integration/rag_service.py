"""
LangChain RAG Service - Fase 1
Serviço RAG otimizado usando LangChain
"""
import json
import logging
import os
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.core.cache import cache
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.vectorstores import VectorStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from rag_agent.models import (ClinicaInfo, Convenio, Especialidade, Exame,
                              Medico)

from .config import LANGCHAIN_CONFIG, RAG_CONFIG

logger = logging.getLogger(__name__)


class LangChainRAGService:
    """
    Serviço RAG otimizado usando LangChain
    
    Responsabilidades:
    1. Criar e gerenciar vector store
    2. Indexar dados da clínica
    3. Realizar buscas semânticas
    4. Cache inteligente
    """
    
    def __init__(self):
        self.embeddings = None
        self.vectorstore = None
        self._initialize_embeddings()
        self._load_or_create_vectorstore()
    
    def _initialize_embeddings(self):
        """Inicializa embeddings do Google"""
        try:
            self.embeddings = GoogleGenerativeAIEmbeddings(
                model=LANGCHAIN_CONFIG['EMBEDDING_MODEL'],
                google_api_key=LANGCHAIN_CONFIG['GEMINI_API_KEY']
            )
            logger.info("✅ Embeddings Google inicializados com sucesso")
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar embeddings: {e}")
            self.embeddings = None
    
    def _load_or_create_vectorstore(self):
        """Carrega ou cria vector store"""
        try:
            vectorstore_path = LANGCHAIN_CONFIG['VECTOR_STORE_PATH']
            
            # Criar diretório se não existir
            os.makedirs(vectorstore_path, exist_ok=True)
            
            # Tentar carregar vector store existente
            if os.path.exists(os.path.join(vectorstore_path, "index.faiss")):
                self.vectorstore = FAISS.load_local(
                    vectorstore_path, 
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                logger.info("✅ Vector store carregado com sucesso")
            else:
                # Criar novo vector store
                self._create_vectorstore()
                
        except Exception as e:
            logger.error(f"❌ Erro ao carregar/criar vector store: {e}")
            self.vectorstore = None
    
    def _create_vectorstore(self):
        """Cria novo vector store com dados da clínica"""
        try:
            # Coletar todos os dados da clínica
            documents = self._collect_clinic_documents()
            
            if not documents:
                logger.warning("⚠️ Nenhum documento encontrado para criar vector store")
                return
            
            # Criar vector store
            self.vectorstore = FAISS.from_documents(
                documents, 
                self.embeddings
            )
            
            # Salvar vector store
            vectorstore_path = LANGCHAIN_CONFIG['VECTOR_STORE_PATH']
            self.vectorstore.save_local(vectorstore_path)
            
            logger.info(f"✅ Vector store criado com {len(documents)} documentos")
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar vector store: {e}")
            self.vectorstore = None
    
    def _collect_clinic_documents(self) -> List[Document]:
        """Coleta todos os dados da clínica em formato Document"""
        documents = []
        
        try:
            # Informações da clínica
            clinica = ClinicaInfo.objects.first()
            if clinica:
                doc = Document(
                    page_content=f"""
                    Informações da Clínica:
                    Nome: {clinica.nome}
                    Secretária: {clinica.secretaria_nome}
                    Endereço: {clinica.endereco}
                    Telefone: {clinica.telefone_contato}
                    WhatsApp: {clinica.whatsapp_contato}
                    Horário de Funcionamento: {clinica.horario_funcionamento}
                    Objetivo Geral da Clínica: {clinica.objetivo_geral}
                    """,
                    metadata={
                        "type": "clinica_info",
                        "id": clinica.id,
                        "source": "clinica"
                    }
                )
                documents.append(doc)
            
            # Médicos
            medicos = Medico.objects.prefetch_related('especialidades', 'convenios')
            for medico in medicos:
                especialidades = ", ".join([esp.nome for esp in medico.especialidades.all()])
                convenios = ", ".join([conv.nome for conv in medico.convenios.all()])
                
                doc = Document(
                    page_content=f"""
                    Médico: {medico.nome}
                    CRM do {medico.nome}: {medico.crm}
                    Especialidades de {medico.nome}: {especialidades}
                    Convênios Aceito por {medico.nome}: {convenios}
                    Preço Particular: R$ {medico.preco_particular}
                    Formas de Pagamento: {medico.formas_pagamento}
                    Retorno Info: {medico.retorno_info}
                    Descrição do {medico.nome}: {medico.bio}
                    """,
                    metadata={
                        "type": "medico",
                        "id": medico.id,
                        "nome": medico.nome,
                        "crm": medico.crm,
                        "especialidades": [esp.nome for esp in medico.especialidades.all()],
                        "source": "medicos"
                    }
                )
                documents.append(doc)
            
            # Especialidades
            especialidades = Especialidade.objects.filter(ativa=True)
            for esp in especialidades:
                doc = Document(
                    page_content=f"""
                    Especialidade: {esp.nome}
                    Descrição: {esp.descricao}
                    Ativa: {esp.ativa}
                    """,
                    metadata={
                        "type": "especialidade",
                        "id": esp.id,
                        "nome": esp.nome,
                        "source": "especialidades"
                    }
                )
                documents.append(doc)
            
            # Exames
            exames = Exame.objects.all()
            for exame in exames:
                doc = Document(
                    page_content=f"""
                    Exame: {exame.nome}
                    Descrição: {exame.o_que_e}
                    Como Funciona: {exame.como_funciona}
                    Preço: R$ {exame.preco}
                    Duração: {exame.duracao_estimada}
                    Preparação: {exame.preparacao}
                    Vantagem: {exame.vantagem}
                    """,
                    metadata={
                        "type": "exame",
                        "id": exame.id,
                        "nome": exame.nome,
                        "preco": str(exame.preco),
                        "source": "exames"
                    }
                )
                documents.append(doc)
            
            # Convênios
            convenios = Convenio.objects.all()
            for convenio in convenios:
                doc = Document(
                    page_content=f"""
                    Convênio: {convenio.nome}
                    Descrição: {convenio.descricao}
                    """,
                    metadata={
                        "type": "convenio",
                        "id": convenio.id,
                        "nome": convenio.nome,
                        "source": "convenios"
                    }
                )
                documents.append(doc)
            
            logger.info(f"📚 Coletados {len(documents)} documentos da clínica")
            
        except Exception as e:
            logger.error(f"❌ Erro ao coletar documentos: {e}")
        
        return documents
    
    def search(self, query: str, k: int = None) -> List[Dict[str, Any]]:
        """
        Busca semântica no vector store
        
        Args:
            query: Consulta de busca
            k: Número de resultados (padrão: RAG_CONFIG['K_RETRIEVAL'])
            
        Returns:
            Lista de documentos relevantes
        """
        if not self.vectorstore:
            logger.warning("⚠️ Vector store não disponível")
            return []
        
        try:
            k = k or RAG_CONFIG['K_RETRIEVAL']
            
            # Buscar documentos similares
            docs = self.vectorstore.similarity_search_with_score(
                query, 
                k=k
            )
            
            # Filtrar por threshold de similaridade
            threshold = RAG_CONFIG['SIMILARITY_THRESHOLD']
            filtered_docs = [
                {
                    'content': doc.page_content,
                    'metadata': doc.metadata,
                    'score': score,
                    'relevance': 'high' if score > 0.8 else 'medium' if score > 0.6 else 'low'
                }
                for doc, score in docs
                if score >= threshold
            ]
            
            logger.info(f"🔍 Busca '{query}' retornou {len(filtered_docs)} resultados")
            return filtered_docs
            
        except Exception as e:
            logger.error(f"❌ Erro na busca: {e}")
            return []
    
    def get_clinic_info(self, query: str = None) -> Dict[str, Any]:
        """
        Obtém informações da clínica
        
        Args:
            query: Consulta específica (opcional)
            
        Returns:
            Informações da clínica
        """
        cache_key = f"langchain_clinic_info_{query or 'all'}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            if query:
                # Busca semântica
                results = self.search(query, k=3)
                clinic_docs = [r for r in results if r['metadata'].get('type') == 'clinica_info']
                
                if clinic_docs:
                    return {
                        'content': clinic_docs[0]['content'],
                        'metadata': clinic_docs[0]['metadata'],
                        'relevance': clinic_docs[0]['relevance']
                    }
            
            # Fallback: dados diretos do banco
            clinica = ClinicaInfo.objects.first()
            if clinica:
                from rag_agent.serializers import ClinicaInfoSerializer
                data = ClinicaInfoSerializer(clinica).data
                cache.set(cache_key, data, LANGCHAIN_CONFIG['CACHE_TTL'])
                return data
            
            return {}
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter informações da clínica: {e}")
            return {}
    
    def get_doctors(self, query: str = None, specialty: str = None) -> List[Dict[str, Any]]:
        """
        Obtém médicos com busca semântica
        
        Args:
            query: Consulta de busca
            specialty: Especialidade específica
            
        Returns:
            Lista de médicos
        """
        cache_key = f"langchain_doctors_{query or 'all'}_{specialty or 'all'}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            if query:
                # Busca semântica
                results = self.search(query, k=5)
                doctor_docs = [r for r in results if r['metadata'].get('type') == 'medico']
                
                if doctor_docs:
                    doctors = []
                    for doc in doctor_docs:
                        doctors.append({
                            'content': doc['content'],
                            'metadata': doc['metadata'],
                            'relevance': doc['relevance']
                        })
                    
                    cache.set(cache_key, doctors, LANGCHAIN_CONFIG['CACHE_TTL'])
                    return doctors
            
            # Fallback: dados diretos do banco
            medicos = Medico.objects.prefetch_related('especialidades', 'convenios')
            if specialty:
                medicos = medicos.filter(especialidades__nome__icontains=specialty)
            
            from rag_agent.serializers import MedicoResumoSerializer
            data = MedicoResumoSerializer(medicos, many=True).data
            cache.set(cache_key, data, LANGCHAIN_CONFIG['CACHE_TTL'])
            return data
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter médicos: {e}")
            return []
    
    def get_exams(self, query: str = None) -> List[Dict[str, Any]]:
        """
        Obtém exames com busca semântica
        
        Args:
            query: Consulta de busca
            
        Returns:
            Lista de exames
        """
        cache_key = f"langchain_exams_{query or 'all'}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            if query:
                # Busca semântica
                results = self.search(query, k=5)
                exam_docs = [r for r in results if r['metadata'].get('type') == 'exame']
                
                if exam_docs:
                    exams = []
                    for doc in exam_docs:
                        exams.append({
                            'content': doc['content'],
                            'metadata': doc['metadata'],
                            'relevance': doc['relevance']
                        })
                    
                    cache.set(cache_key, exams, LANGCHAIN_CONFIG['CACHE_TTL'])
                    return exams
            
            # Fallback: dados diretos do banco
            from rag_agent.serializers import ExameSerializer
            exames = Exame.objects.all()
            data = ExameSerializer(exames, many=True).data
            cache.set(cache_key, data, LANGCHAIN_CONFIG['CACHE_TTL'])
            return data
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter exames: {e}")
            return []
    
    def get_specialties(self, query: str = None) -> List[Dict[str, Any]]:
        """
        Obtém especialidades com busca semântica
        
        Args:
            query: Consulta de busca
            
        Returns:
            Lista de especialidades
        """
        cache_key = f"langchain_specialties_{query or 'all'}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            if query:
                # Busca semântica
                results = self.search(query, k=5)
                specialty_docs = [r for r in results if r['metadata'].get('type') == 'especialidade']
                
                if specialty_docs:
                    specialties = []
                    for doc in specialty_docs:
                        specialties.append({
                            'content': doc['content'],
                            'metadata': doc['metadata'],
                            'relevance': doc['relevance']
                        })
                    
                    cache.set(cache_key, specialties, LANGCHAIN_CONFIG['CACHE_TTL'])
                    return specialties
            
            # Fallback: dados diretos do banco
            from rag_agent.serializers import EspecialidadeSerializer
            especialidades = Especialidade.objects.filter(ativa=True)
            data = EspecialidadeSerializer(especialidades, many=True).data
            cache.set(cache_key, data, LANGCHAIN_CONFIG['CACHE_TTL'])
            return data
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter especialidades: {e}")
            return []
    
    def refresh_vectorstore(self):
        """Atualiza o vector store com dados mais recentes"""
        try:
            logger.info("🔄 Atualizando vector store...")
            self._create_vectorstore()
            logger.info("✅ Vector store atualizado com sucesso")
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar vector store: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do vector store"""
        try:
            if not self.vectorstore:
                return {'status': 'not_initialized'}
            
            # Contar documentos por tipo
            stats = {
                'total_documents': self.vectorstore.index.ntotal,
                'embedding_dimension': self.vectorstore.index.d,
                'status': 'active'
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter estatísticas: {e}")
            return {'status': 'error', 'error': str(e)}


# Instância global do serviço
langchain_rag_service = LangChainRAGService()
