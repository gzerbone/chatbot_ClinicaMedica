"""
Entity Extractor - Extração de Entidades das Mensagens

Responsável por:
- Extrair entidades relevantes das mensagens
- Usar regex como fallback
- Normalizar e validar dados extraídos
"""

import logging
import re
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class EntityExtractor:
    """Extração de entidades das mensagens"""
    
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
        Extrai especialidade médica da mensagem
        
        Args:
            message: Mensagem do usuário
            
        Returns:
            Especialidade extraída ou None
        """
        # Lista de especialidades comuns
        specialties = [
            'pneumologia', 'cardiologia', 'dermatologia', 'ortopedia',
            'pediatria', 'ginecologia', 'neurologia', 'psiquiatria',
            'oftalmologia', 'otorrinolaringologia', 'urologia', 'oncologia'
        ]
        
        message_lower = message.lower()
        for specialty in specialties:
            if specialty in message_lower:
                return specialty.title()
        
        return None
    
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


