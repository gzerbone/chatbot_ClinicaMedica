"""
Serviço Base Consolidado
Contém funções comuns utilizadas por todos os serviços
"""
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class BaseService:
    """
    Classe base com funções comuns para todos os serviços
    """
    
    @staticmethod
    def extract_patient_name(message: str) -> Optional[str]:
        """
        Extrai nome completo do paciente da mensagem
        
        Args:
            message: Mensagem do usuário
            
        Returns:
            Nome extraído ou None se não encontrado
        """
        try:
            # Padrões para extrair nomes
            patterns = [
                r'sou\s+([A-Za-zÀ-ÿ\s]+)',
                r'meu\s+nome\s+é\s+([A-Za-zÀ-ÿ\s]+)',
                r'chamo-me\s+([A-Za-zÀ-ÿ\s]+)',
                r'nome\s+é\s+([A-Za-zÀ-ÿ\s]+)',
                r'me\s+chamo\s+([A-Za-zÀ-ÿ\s]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    name = match.group(1).strip()
                    # Validar se tem pelo menos 2 palavras
                    words = name.split()
                    if len(words) >= 2:
                        return name.title()
            
            # Fallback: extrair palavras maiúsculas consecutivas
            words = message.split()
            name_words = []
            
            for word in words:
                clean_word = word.strip('.,!?')
                if (clean_word.istitle() and 
                    len(clean_word) > 2 and 
                    clean_word.isalpha() and
                    clean_word.lower() not in {'oi', 'olá', 'ola', 'bom', 'boa', 'dia', 'tarde', 'noite'}):
                    name_words.append(clean_word)
            
            # Se encontrou 2 ou mais palavras válidas, considerar como nome
            if len(name_words) >= 2:
                return ' '.join(name_words)
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao extrair nome: {e}")
            return None
    
    @staticmethod
    def validate_patient_name(name: str) -> Tuple[bool, str]:
        """
        Valida se o nome fornecido é válido
        
        Args:
            name: Nome a ser validado
            
        Returns:
            Tuple (is_valid, error_message)
        """
        if not name or len(name.strip()) < 3:
            return False, "Nome muito curto. Por favor, informe seu nome completo."
        
        # Verificar se tem pelo menos 2 palavras
        words = name.strip().split()
        if len(words) < 2:
            return False, "Por favor, informe seu nome e sobrenome. Exemplo: 'João Silva'"
        
        # Verificar se não contém números
        if any(char.isdigit() for char in name):
            return False, "Nome não deve conter números. Por favor, informe apenas letras."
        
        # Verificar se não contém caracteres especiais
        if not re.match(r'^[a-zA-ZÀ-ÿ\s]+$', name):
            return False, "Nome contém caracteres inválidos. Use apenas letras e espaços."
        
        return True, ""
    
    @staticmethod
    def extract_phone_from_message(message: str) -> Optional[str]:
        """
        Extrai número de telefone da mensagem
        
        Args:
            message: Mensagem do usuário
            
        Returns:
            Telefone formatado ou None se não encontrado
        """
        try:
            # Padrões para números de telefone brasileiros
            patterns = [
                r'\(?(\d{2})\)?\s*(\d{4,5})-?(\d{4})',  # (11) 99999-9999
                r'(\d{2})\s*(\d{4,5})-?(\d{4})',        # 11 99999-9999
                r'(\d{10,11})',                          # 11999999999
            ]
            
            for pattern in patterns:
                match = re.search(pattern, message)
                if match:
                    groups = match.groups()
                    if len(groups) == 3:
                        return f"({groups[0]}) {groups[1]}-{groups[2]}"
                    elif len(groups) == 1:
                        phone = groups[0]
                        if len(phone) == 11:
                            return f"({phone[:2]}) {phone[2:7]}-{phone[7:]}"
                        elif len(phone) == 10:
                            return f"({phone[:2]}) {phone[2:6]}-{phone[6:]}"
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao extrair telefone: {e}")
            return None
    
    @staticmethod
    def extract_entities_from_message(message: str) -> Dict[str, List[str]]:
        """
        Extrai entidades básicas da mensagem
        
        Args:
            message: Mensagem do usuário
            
        Returns:
            Dicionário com entidades extraídas
        """
        entities = {
            'specialties': [],
            'doctors': [],
            'patient_name': [],
            'insurance': [],
            'dates': [],
            'times': []
        }
        
        try:
            # Extrair especialidades médicas
            specialties = [
                'cardiologia', 'dermatologia', 'pediatria', 'ginecologia', 
                'ortopedia', 'neurologia', 'psiquiatria', 'endocrinologia',
                'oftalmologia', 'urologia', 'gastroenterologia', 'pneumologia',
                'medicina do sono'
            ]
            
            found_specialties = []
            for specialty in specialties:
                if specialty in message.lower():
                    found_specialties.append(specialty)
            
            entities['specialties'] = found_specialties
            
            # Extrair médicos (Dr., Dra., Doutor, Doutora)
            doctor_patterns = [
                r'\b(?:Dr\.?|Dra\.?|Doutor|Doutora)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                r'\b([A-Z][a-z]+)\s+(?:Dr\.?|Dra\.?|Doutor|Doutora)'
            ]
            
            found_doctors = []
            for pattern in doctor_patterns:
                matches = re.findall(pattern, message, re.IGNORECASE)
                found_doctors.extend(matches)
            
            entities['doctors'] = found_doctors
            
            # Extrair possíveis nomes de pacientes
            excluded_words = {
                'dr', 'dra', 'doutor', 'doutora', 'medico', 'medica', 'cardiologia',
                'dermatologia', 'pediatria', 'ginecologia', 'ortopedia', 'neurologia',
                'psiquiatria', 'endocrinologia', 'oftalmologia', 'urologia',
                'gastroenterologia', 'consulta', 'exame', 'agendamento', 'clínica',
                'clinica', 'telefone', 'whatsapp', 'endereco', 'endereço'
            }
            
            words = re.findall(r'\b[A-Z][a-z]+\b', message)
            patient_names = []
            for word in words:
                if (len(word) > 2 and 
                    word.lower() not in excluded_words and
                    not word.isdigit()):
                    patient_names.append(word)
            
            entities['patient_name'] = patient_names
            
            # Extrair datas (formato DD/MM/YYYY ou DD/MM/YY)
            date_patterns = [
                r'\b(\d{1,2})/(\d{1,2})/(\d{2,4})\b',
                r'\b(\d{1,2})/(\d{1,2})\b'
            ]
            
            found_dates = []
            for pattern in date_patterns:
                matches = re.findall(pattern, message)
                for match in matches:
                    if len(match) == 3:  # DD/MM/YYYY
                        day, month, year = match
                        if len(year) == 2:
                            year = '20' + year
                        found_dates.append(f"{day}/{month}/{year}")
                    elif len(match) == 2:  # DD/MM
                        day, month = match
                        found_dates.append(f"{day}/{month}")
            
            entities['dates'] = found_dates
            
            # Extrair horários (formato HH:MM)
            time_pattern = r'\b(\d{1,2}):(\d{2})\b'
            time_matches = re.findall(time_pattern, message)
            found_times = [f"{hour}:{minute}" for hour, minute in time_matches]
            entities['times'] = found_times
            
            return entities
            
        except Exception as e:
            logger.error(f"Erro ao extrair entidades: {e}")
            return entities
    
    @staticmethod
    def should_trigger_handoff(intent: str, message: str) -> bool:
        """
        Determina se deve acionar o handoff
        
        Args:
            intent: Intenção detectada
            message: Mensagem do usuário
            
        Returns:
            True se deve acionar handoff
        """
        handoff_intents = ['confirmar_agendamento', 'agendar_consulta']
        handoff_keywords = ['confirmar', 'agendar', 'marcar', 'sim', 'ok', 'perfeito']
        
        # Verificar intenção
        if intent in handoff_intents:
            return True
        
        # Verificar palavras-chave na mensagem
        message_lower = message.lower()
        if any(keyword in message_lower for keyword in handoff_keywords):
            return True
        
        return False
    
    @staticmethod
    def format_phone_number(phone: str) -> str:
        """
        Formata número de telefone para padrão brasileiro
        
        Args:
            phone: Número de telefone
            
        Returns:
            Telefone formatado
        """
        try:
            # Remover caracteres não numéricos
            digits = re.sub(r'\D', '', phone)
            
            # Se tem 11 dígitos (com DDD e 9)
            if len(digits) == 11:
                return f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"
            # Se tem 10 dígitos (com DDD sem 9)
            elif len(digits) == 10:
                return f"({digits[:2]}) {digits[2:6]}-{digits[6:]}"
            else:
                return phone
                
        except Exception as e:
            logger.error(f"Erro ao formatar telefone: {e}")
            return phone
