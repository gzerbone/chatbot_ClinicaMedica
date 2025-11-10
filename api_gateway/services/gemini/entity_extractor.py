"""
Entity Extractor - Extração de Entidades das Mensagens

Responsável por:
- Extrair entidades relevantes das mensagens
- Usar regex como fallback
- Normalizar e validar dados extraídos
"""

import json
import logging
import re
from typing import Dict, List, Optional

import google.generativeai as genai
from django.conf import settings

logger = logging.getLogger(__name__)



class EntityExtractor:
    """Extração de entidades das mensagens"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'GEMINI_API_KEY', '')
        self.model = None
        
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                model_name = getattr(settings, 'GEMINI_MODEL', 'gemini-2.5-flash-lite')
                self.model = genai.GenerativeModel(model_name)
            except Exception as e:
                logger.error(f"Erro ao configurar Gemini no EntityExtractor: {e}")
            
    # Método principal para extrair entidades da mensagem
    def extract_entities(self, message: str, session: Dict, conversation_history: List, clinic_data: Dict) -> Dict[str, str]:
        """
        Extrai entidades da mensagem (método principal)
        Usa Gemini como método primário e regex como fallback
        """
        try:
            # Tentar extração com Gemini primeiro
            if self.model:
                entities = self.extract_entities_with_gemini(message, session, conversation_history, clinic_data)
                if entities and any(entities.values()):
                    return self.validate_entities(entities)
            
            # Fallback para regex
            logger.info("Usando regex como fallback para extração de entidades")
            entities = self.extract_entities_with_regex(message)
            return self.validate_entities(entities)
            
        except Exception as e:
            logger.error(f"Erro na extração de entidades: {e}")
            return self.extract_entities_with_regex(message)
        
    # Método para extrair entidades com Gemini
    def extract_entities_with_gemini(self, message: str, session: Dict,
                                conversation_history: List, clinic_data: Dict) -> Dict[str, str]:
        """Extrai entidades usando Gemini"""
        try:
            prompt = self._build_entity_extraction_prompt(message, session, conversation_history, clinic_data)
            
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.5,
                    "top_p": 0.8,
                    "top_k": 20,
                    "max_output_tokens": 200
                }
            )
            
            # Monitorar tokens
            from ..token_monitor import token_monitor
            token_monitor.log_token_usage("EXTRAÇÃO_ENTIDADES", prompt, response.text, session.get('phone_number'))
            
            # Extrair JSON da resposta
            return self._extract_entities_from_response(response.text)
            
        except Exception as e:
            logger.error(f"Erro ao extrair entidades com Gemini: {e}")
            return {}
        
    # Método para construir o prompt de extração de entidades
    def _build_entity_extraction_prompt(self, message: str, session: Dict, conversation_history: List, clinic_data: Dict) -> str:
        """Constrói prompt para extração de entidades"""
        current_state = session.get('current_state', 'idle')
        patient_name = session.get('patient_name')
        selected_doctor = session.get('selected_doctor')
        selected_specialty = session.get('selected_specialty')
        preferred_date = session.get('preferred_date')
        preferred_time = session.get('preferred_time')
        
        prompt = f"""Você é um assistente especializado em extrair informações de mensagens de pacientes.

MENSAGEM: "{message}"

CONTEXTO:
- Estado: {current_state}
- Nome: {patient_name or 'Não informado'}
- Médico: {selected_doctor or 'Não selecionado'}
- Especialidade: {selected_specialty or 'Não selecionada'}
- Data: {preferred_date or 'Não informada'}
- Horário: {preferred_time or 'Não informado'}

EXTRAIA as seguintes entidades da mensagem (use null se não encontrar):
- nome_paciente: Nome completo do paciente
- medico: Nome do médico mencionado
- especialidade: Especialidade médica
- data: Data mencionada
- horario: Horário mencionado

IMPORTANTE:
- Se encontrar especialidade como "pneumologista", extraia como "pneumologia"
- Se a mensagem modifica informações já coletadas, extraia os novos valores
- Use o contexto para entender referências

Responda APENAS com JSON válido:
{{
    "nome_paciente": "nome_ou_null",
    "medico": "médico_ou_null",
    "especialidade": "especialidade_ou_null",
    "data": "data_ou_null",
    "horario": "horário_ou_null"
}}"""
        
        return prompt
            
    # Método para extrair entidades do JSON retornado pelo Gemini
    def _extract_entities_from_response(self, response_text: str) -> Dict[str, str]:
        """Extrai entidades do JSON retornado pelo Gemini"""
        try:
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            entities = json.loads(response_text.strip())
            
            # Remover valores null
            return {k: v for k, v in entities.items() if v and v != 'null'}
            
        except Exception as e:
            logger.error(f"Erro ao extrair entidades do JSON: {e}")
            logger.error(f"Resposta recebida: {response_text}")
            return {}


    def extract_entities_with_regex(self, message: str) -> Dict[str, str]:
        """
        Extrai entidades usando regex como fallback quando o Gemini falha
        
        Args:
            message: Mensagem do usuário
            
        Returns:
            Dict com entidades extraídas
        """
        entities = {}
        message_lower = message.lower()
        
        # Extrair nome do paciente
        name = self.extract_patient_name(message)
        if name:
            entities['nome_paciente'] = name
        
        # Extrair médico
        doctor = self.extract_doctor(message)
        if doctor:
            entities['medico'] = doctor
        
        # Extrair data
        date = self.extract_date(message)
        if date:
            entities['data'] = date
        
        # Extrair horário
        time = self.extract_time(message)
        if time:
            entities['horario'] = time
        
        return entities
    
    def extract_patient_name(self, message: str) -> Optional[str]:
        """
        Extrai nome do paciente da mensagem
        
        Args:
            message: Mensagem do usuário
            
        Returns:
            Nome do paciente ou None
        """
        name_patterns = [
            r'meu\s+nome\s+é\s+([A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+)*)',
            r'(?:eu\s+)?sou\s+(?:o\s+|a\s+)?([A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+)*)',
            r'chamo-me\s+([A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+)*)',
            r'nome\s+é\s+([A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+)*)',
            r'me\s+chamo\s+([A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+)*)'
        ]
        
        # Lista de palavras que não são nomes
        invalid_names = [
            'gostaria', 'queria', 'preciso', 'quero', 'desejo', 'solicito',
            'consulta', 'agendamento', 'marcar', 'agendar', 'uma', 'de',
            'para', 'com', 'em', 'no', 'na', 'do', 'da', 'por', 'pelo'
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                
                # Verificar se não é uma palavra inválida (palavras completas)
                name_words = name.lower().split()
                if any(word in invalid_names for word in name_words):
                    continue
                
                # Limitar a 3 palavras (nome + sobrenome + sobrenome)
                name_parts = name.split()[:3]
                if len(name_parts) >= 2:  # Pelo menos nome e sobrenome
                    # Verificar se as partes não são palavras inválidas
                    valid_parts = []
                    for part in name_parts:
                        if part.lower() not in invalid_names:
                            valid_parts.append(part)
                    
                    if len(valid_parts) >= 2:
                        return ' '.join(valid_parts).title()
        
        return None
    
    def extract_doctor(self, message: str) -> Optional[str]:
        """
        Extrai nome do médico da mensagem
        
        Args:
            message: Mensagem do usuário
            
        Returns:
            Nome do médico ou None
        """
        doctor_patterns = [
            r'dr\.?\s+([A-Za-zÀ-ÿ]+)',
            r'dra\.?\s+([A-Za-zÀ-ÿ]+)',
            r'doutor\s+([A-Za-zÀ-ÿ]+)',
            r'doutora\s+([A-Za-zÀ-ÿ]+)',
            r'com\s+([A-Za-zÀ-ÿ]+)'
        ]
        
        for pattern in doctor_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                doctor_name = match.group(0).strip()
                # Limitar a 3 palavras
                doctor_parts = doctor_name.split()[:3]
                return ' '.join(doctor_parts)
        
        return None
    
    def extract_date(self, message: str) -> Optional[str]:
        """
        Extrai data da mensagem
        
        Args:
            message: Mensagem do usuário
            
        Returns:
            Data extraída ou None
        """
        date_patterns = [
            r'(\d{1,2})/(\d{1,2})/(\d{2,4})',
            r'(\d{1,2})/(\d{1,2})',
            r'(segunda|terça|quarta|quinta|sexta|sábado|domingo)',
            r'(amanhã|hoje|depois)'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(0).strip()
        
        return None
    
    def extract_time(self, message: str) -> Optional[str]:
        """
        Extrai horário da mensagem
        
        Args:
            message: Mensagem do usuário
            
        Returns:
            Horário extraído ou None
        """
        time_patterns = [
            r'(\d{1,2}):(\d{2})',
            r'(\d{1,2})h(\d{2})?',
            r'(\d{1,2})\s+da\s+(manhã|tarde|noite)'
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(0).strip()
        
        return None
    
    def extract_specialty(self, message: str) -> Optional[str]:
        """
        Extrai especialidade médica da mensagem e valida contra o banco de dados
        
        Args:
            message: Mensagem do usuário
            
        Returns:
            Nome da especialidade se encontrada e registrada, None caso contrário
        """
        from ..rag_service import RAGService

        # Buscar especialidades ativas no banco de dados
        especialidades_ativas = RAGService.get_especialidades()
        
        # Converter a mensagem para minúsculas
        mensagem_usuario = message.lower()
        
        # Verificar se a especialidade no BD está na mensagem do usuário
        for especialidade in especialidades_ativas:
            nome_esp = especialidade.get('nome', ' ').lower()
            if nome_esp in mensagem_usuario:
                return especialidade.get('nome') # Retorna o nome da especialidade normalizado
        
        # Se não encontrar, retornar None
        logger.warning(f"Especialidade não encontrada na mensagem: {message}")
        return None
    
    def validate_specialty(self, specialty_name: str, especialidades_ativas: list[Dict]) -> bool:
        """
        Valida se a especialidade existe no banco de dados
        
        Args:
            specialty_name: Nome da especialidade
            especialidades_ativas: Lista de especialidades ativas
        """
        if not specialty_name or not especialidades_ativas:
            return False
        
        # Converter o nome da especialidade para minúsculas
        specialty_name = specialty_name.lower()
        
        # Verificar se a especialidade existe no banco de dados
        for especialidade in especialidades_ativas:
            if especialidade.get('nome', '').lower() == specialty_name:
                return True
        
        return False
    
    def get_available_specialties_message(self, especialidades_ativas: list[Dict] = None) -> str:
        """
        Gera mensagem com lista de especialidades disponíveis
        
        Returns:
            Mensagem com lista de especialidades disponíveis
        """
        from ..rag_service import RAGService

        # Buscar especialidades ativas no banco de dados
        if especialidades_ativas is None:
            especialidades_ativas = RAGService.get_especialidades()
        
        if not especialidades_ativas:
            return "No momento não temos nenhuma especialidade cadastrada"
        
        # Gerar mensagem com lista de especialidades
        lista = [f"- {especialidade.get('nome')}" for especialidade in especialidades_ativas]
        return "Nossas Especialidades disponíveis são:\n" + "\n".join(lista)

    

    
    def validate_entities(self, entities: Dict[str, str]) -> Dict[str, str]:
        """
        Valida e normaliza entidades extraídas
        
        Args:
            entities: Entidades extraídas
            
        Returns:
            Entidades validadas e normalizadas
        """
        validated = {}
        
        # Validar nome
        if entities.get('nome_paciente'):
            name = entities['nome_paciente'].strip()
            if len(name) >= 3 and ' ' in name:  # Nome e sobrenome mínimo
                validated['nome_paciente'] = name.title()
        
        # Validar médico
        if entities.get('medico'):
            doctor = entities['medico'].strip()
            if len(doctor) >= 3:
                validated['medico'] = doctor
        
        # Validar especialidade
        if entities.get('especialidade'):
            specialty = entities['especialidade'].strip()
            if len(specialty) >= 3:
                validated['especialidade'] = specialty.title()
        
        # Validar data
        if entities.get('data'):
            date = entities['data'].strip()
            if len(date) >= 1:
                validated['data'] = date
        
        # Validar horário
        if entities.get('horario'):
            time = entities['horario'].strip()
            if len(time) >= 1:
                validated['horario'] = time
        
        return validated


