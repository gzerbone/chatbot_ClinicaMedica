"""
Serviço para detecção de intenções nas mensagens do usuário
"""
import re
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class IntentDetectionService:
    """
    Serviço para detectar intenções nas mensagens do usuário
    """
    
    def __init__(self):
        # Padrões para detecção de intenções
        self.intent_patterns = {
            'saudacao': [
                r'\b(oi|olá|ola|eae|e aí|hey|hi|hello)\b',
                r'\b(bom dia|boa tarde|boa noite)\b',
                r'\b(como vai|tudo bem|beleza)\b',
                r'\b(oi bot|olá bot|hello bot)\b'
            ],
            
            'buscar_especialidade': [
                r'\b(especialidade|especialidades|especialista|especialistas)\b',
                r'\b(que tipo|que tipos|quais tipos)\b',
                r'\b(que médico|quais médicos|médico de)\b',
                r'\b(cardiologia|dermatologia|pediatria|ginecologia|ortopedia|neurologia)\b'
            ],
            
            'buscar_medico': [
                r'\b(médico|medicos|doutor|doutores|dr\.|dra\.)\b',
                r'\b(quem é|quem são|conhecer|conheço)\b',
                r'\b(profissional|profissionais)\b',
                r'\b(currículo|curriculo|experiência|experiencia)\b'
            ],
            
            'buscar_exame': [
                r'\b(exame|exames|procedimento|procedimentos)\b',
                r'\b(como funciona|como é feito|preparo|preparação)\b',
                r'\b(preço|preco|valor|custo|quanto custa)\b',
                r'\b(hemograma|raios x|ultrassom|tomografia|ressonância)\b'
            ],
            
            'buscar_info_clinica': [
                r'\b(clínica|clinica|endereço|endereco|localização|localizacao)\b',
                r'\b(telefone|contato|como chegar|onde fica)\b',
                r'\b(horário|horarios|funcionamento|aberto)\b',
                r'\b(informações|informacoes|info|sobre)\b'
            ],
            
            'agendar_consulta': [
                r'\b(agendar|marcar|consulta|consultar)\b',
                r'\b(quero|preciso|gostaria|posso)\s+(agendar|marcar)\b',
                r'\b(marcar consulta|agendar consulta)\b',
                r'\b(disponibilidade|disponível|horário livre)\b'
            ],
            
            'confirmar_agendamento': [
                r'\b(confirmar|confirmação|confirmacao)\b',
                r'\b(meu agendamento|minha consulta|agendado|marcado)\b',
                r'\b(verificar|verificar se|checar)\b',
                r'\b(data|horário|quando|que dia)\b'
            ],
            
            'cancelar_agendamento': [
                r'\b(cancelar|cancelamento|desmarcar)\b',
                r'\b(não posso|nao posso|não vou|nao vou)\b',
                r'\b(remarcar|reagendar|mudar)\b',
                r'\b(impedido|não consigo|nao consigo)\b'
            ],
            
            'horarios_disponiveis': [
                r'\b(horário|horarios|horas|manhã|manha|tarde|noite)\b',
                r'\b(disponível|disponivel|livre|aberto)\b',
                r'\b(quando|que dia|que hora)\b',
                r'\b(segunda|terça|quarta|quinta|sexta|sábado|domingo)\b'
            ],
            
            'despedida': [
                r'\b(tchau|até logo|ate logo|até mais|ate mais)\b',
                r'\b(obrigado|obrigada|valeu|valew)\b',
                r'\b(foi isso|só isso|so isso|não é mais|nao é mais)\b',
                r'\b(bye|goodbye|see you)\b'
            ],
            
            'ajuda': [
                r'\b(ajuda|help|socorro|não sei|nao sei)\b',
                r'\b(como usar|como funciona|o que posso|que posso)\b',
                r'\b(comandos|opções|opcoes|menu)\b',
                r'\b(início|inicio|começar|comecar|start)\b'
            ]
        }
    
    def detect_intent(self, message: str) -> Tuple[str, float]:
        """
        Detecta a intenção de uma mensagem do usuário
        
        Args:
            message: Mensagem do usuário
            
        Returns:
            Tupla com (intenção, confiança)
        """
        message_lower = message.lower().strip()
        
        # Remover pontuação e normalizar
        message_clean = re.sub(r'[^\w\s]', ' ', message_lower)
        message_clean = re.sub(r'\s+', ' ', message_clean).strip()
        
        intent_scores = {}
        
        # Calcular pontuação para cada intenção
        for intent, patterns in self.intent_patterns.items():
            score = 0
            total_patterns = len(patterns)
            
            for pattern in patterns:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    score += 1
            
            # Normalizar pontuação (0-1)
            intent_scores[intent] = score / total_patterns if total_patterns > 0 else 0
        
        # Encontrar a intenção com maior pontuação
        if intent_scores:
            best_intent = max(intent_scores.items(), key=lambda x: x[1])
            
            # Se a confiança for muito baixa, classificar como desconhecida
            if best_intent[1] < 0.1:
                return 'desconhecida', 0.0
            
            return best_intent
        
        return 'desconhecida', 0.0
    
    def get_intent_keywords(self, intent: str) -> List[str]:
        """
        Retorna palavras-chave relacionadas a uma intenção
        
        Args:
            intent: Intenção
            
        Returns:
            Lista de palavras-chave
        """
        keywords_map = {
            'saudacao': ['oi', 'olá', 'bom dia', 'boa tarde', 'boa noite', 'como vai'],
            'buscar_especialidade': ['especialidade', 'especialista', 'cardiologia', 'dermatologia'],
            'buscar_medico': ['médico', 'doutor', 'profissional', 'currículo'],
            'buscar_exame': ['exame', 'procedimento', 'hemograma', 'ultrassom'],
            'buscar_info_clinica': ['endereço', 'telefone', 'horário', 'funcionamento'],
            'agendar_consulta': ['agendar', 'marcar', 'consulta', 'disponibilidade'],
            'confirmar_agendamento': ['confirmar', 'agendamento', 'verificar'],
            'cancelar_agendamento': ['cancelar', 'desmarcar', 'remarcar'],
            'horarios_disponiveis': ['horário', 'disponível', 'manhã', 'tarde'],
            'despedida': ['tchau', 'obrigado', 'até logo', 'bye'],
            'ajuda': ['ajuda', 'help', 'como usar', 'comandos']
        }
        
        return keywords_map.get(intent, [])
    
    def is_question(self, message: str) -> bool:
        """
        Verifica se a mensagem é uma pergunta
        
        Args:
            message: Mensagem do usuário
            
        Returns:
            True se for uma pergunta
        """
        question_patterns = [
            r'\?$',  # Termina com ponto de interrogação
            r'\b(como|quando|onde|quem|o que|que|qual|quais|por que|porque)\b',
            r'\b(é|são|tem|tem)\s+',
            r'\b(pode|pode|consegue|sabe)\b'
        ]
        
        for pattern in question_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return True
        
        return False
    
    def extract_entities(self, message: str) -> Dict[str, List[str]]:
        """
        Extrai entidades da mensagem (nomes, números, datas, etc.)
        
        Args:
            message: Mensagem do usuário
            
        Returns:
            Dicionário com entidades encontradas
        """
        entities = {
            'numbers': [],
            'dates': [],
            'times': [],
            'specialties': [],
            'doctors': []
        }
        
        # Extrair números
        numbers = re.findall(r'\b\d+\b', message)
        entities['numbers'] = numbers
        
        # Extrair datas (formato DD/MM/YYYY ou DD/MM)
        dates = re.findall(r'\b\d{1,2}/\d{1,2}(?:/\d{2,4})?\b', message)
        entities['dates'] = dates
        
        # Extrair horários (formato HH:MM)
        times = re.findall(r'\b\d{1,2}:\d{2}\b', message)
        entities['times'] = times
        
        # Extrair especialidades médicas
        specialties = [
            'cardiologia', 'dermatologia', 'pediatria', 'ginecologia',
            'ortopedia', 'neurologia', 'psiquiatria', 'endocrinologia',
            'oftalmologia', 'otorrinolaringologia', 'urologia', 'gastroenterologia'
        ]
        
        found_specialties = []
        for specialty in specialties:
            if specialty in message.lower():
                found_specialties.append(specialty)
        
        entities['specialties'] = found_specialties
        
        return entities
