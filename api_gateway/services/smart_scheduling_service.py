"""
Serviço de Consulta de Horários
Consulta disponibilidade no Google Calendar e informa horários ao usuário
"""
import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from django.utils import timezone

from .google_calendar_service import google_calendar_service
from .rag_service import RAGService

logger = logging.getLogger(__name__)


class SmartSchedulingService:
    """
    Serviço de Consulta de Horários
    
    Responsável por:
    1. Consultar disponibilidade real no Google Calendar
    2. Informar horários disponíveis para o médico escolhido
    3. Otimizar fluxo de conversa para evitar repetições
    4. Fornecer informações claras sobre agenda do médico
    """

    def __init__(self):
        self.calendar_service = google_calendar_service
        self.rag_service = RAGService

    def analyze_scheduling_request(self, message: str, session: Dict) -> Dict[str, Any]:
        """
        Analisa solicitação de consulta de horários e determina próxima ação
        """
        try:
            message_lower = message.lower()
            
            # Extrair informações da mensagem
            extracted_info = self._extract_scheduling_info(message, session)
            
            # Determinar estado atual e próxima ação
            analysis = self._determine_next_action(extracted_info, session)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Erro na análise de consulta: {e}")
            return self._get_fallback_analysis()

    def _extract_scheduling_info(self, message: str, session: Dict) -> Dict[str, Any]:
        """
        Extrai informações de agendamento da mensagem
        """
        import re
        
        info = {
            'doctor_mentioned': None,
            'specialty_mentioned': None,
            'date_mentioned': None,
            'time_mentioned': None,
            'appointment_type': None
        }
        
        message_lower = message.lower()
        
        # Extrair médico mencionado
        doctor_patterns = [
            r'dr\.?\s+([a-záêãõç\s]+)',
            r'dra\.?\s+([a-záêãõç\s]+)',
            r'doutor\s+([a-záêãõç\s]+)',
            r'doutora\s+([a-záêãõç\s]+)',
            r'com\s+([a-záêãõç\s]+)'
        ]
        
        for pattern in doctor_patterns:
            match = re.search(pattern, message_lower)
            if match:
                doctor_name = match.group(1).strip()
                info['doctor_mentioned'] = doctor_name
                break
        
        # Extrair data mencionada
        date_patterns = [
            r'(amanhã|hoje|depois de amanhã)',
            r'(segunda|terça|quarta|quinta|sexta|sábado|domingo)',
            r'(\d{1,2})/(\d{1,2})',
            r'(\d{1,2})/(\d{1,2})/(\d{2,4})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, message_lower)
            if match:
                info['date_mentioned'] = match.group(0).strip()
                break
        
        # Extrair horário mencionado
        time_patterns = [
            r'(\d{1,2})h(\d{2})?',
            r'(\d{1,2}):(\d{2})',
            r'(\d{1,2})\s+da\s+(manhã|tarde|noite)',
            r'de\s+manhã|da\s+tarde|à\s+noite'
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, message_lower)
            if match:
                info['time_mentioned'] = match.group(0).strip()
                break
        
        # Extrair tipo de consulta
        if any(word in message_lower for word in ['consulta', 'retorno', 'exame']):
            if 'retorno' in message_lower:
                info['appointment_type'] = 'retorno'
            elif 'exame' in message_lower:
                info['appointment_type'] = 'exame'
            else:
                info['appointment_type'] = 'consulta'
        
        return info

    def _determine_next_action(self, extracted_info: Dict, session: Dict) -> Dict[str, Any]:
        """
        Determina próxima ação baseada nas informações extraídas
        Foco: consultar horários e gerar handoff quando confirmado
        """
        message = extracted_info.get('message', '').lower()
        doctor_mentioned = extracted_info.get('doctor_mentioned')
        date_mentioned = extracted_info.get('date_mentioned')
        time_mentioned = extracted_info.get('time_mentioned')
        
        # Caso 1: Confirmação de agendamento - GERAR HANDOFF
        if self._is_confirmation_message(message):
            return self._handle_appointment_confirmation(extracted_info, session)
        
        # Caso 2: Médico mencionado - mostrar horários
        if doctor_mentioned:
            # Validar se médico existe
            doctor_info = self._validate_doctor(doctor_mentioned)
            if doctor_info:
                # Consultar disponibilidade real
                availability = self._get_doctor_availability(doctor_info['nome'], date_mentioned)
                return {
                    'action': 'show_availability',
                    'response_type': 'availability_info',
                    'next_state': 'showing_availability',
                    'doctor_info': doctor_info,
                    'availability': availability,
                    'message': self._get_availability_info_message(doctor_info, availability, date_mentioned)
                }
            else:
                return {
                    'action': 'doctor_not_found',
                    'response_type': 'error',
                    'next_state': 'idle',
                    'message': self._get_doctor_not_found_message(doctor_mentioned)
                }
        
        # Caso 3: Solicitação geral de horários
        if any(word in message for word in ['horário', 'horarios', 'disponível', 'disponiveis']):
            return {
                'action': 'show_doctors',
                'response_type': 'doctor_list',
                'next_state': 'showing_doctors',
                'message': self._get_doctor_list_message()
            }
        
        # Fallback - mostrar lista de médicos
        return {
            'action': 'show_doctors',
            'response_type': 'doctor_list',
            'next_state': 'showing_doctors',
            'message': self._get_doctor_list_message()
        }

    def _is_confirmation_message(self, message: str) -> bool:
        """
        Verifica se a mensagem é uma confirmação de agendamento
        """
        confirmation_keywords = [
            'sim', 'confirmo', 'confirma', 'está correto', 'está certo',
            'perfeito', 'ótimo', 'ok', 'beleza', 'pode ser',
            'quero esse horário', 'aceito', 'concordo'
        ]
        
        return any(keyword in message for keyword in confirmation_keywords)
    
    def _handle_appointment_confirmation(self, extracted_info: Dict, session: Dict) -> Dict[str, Any]:
        """
        Processa confirmação de agendamento e gera handoff
        """
        try:
            # Obter informações da sessão
            patient_name = session.get('patient_name', 'Paciente')
            doctor_name = extracted_info.get('doctor_mentioned', 'Médico')
            date_mentioned = extracted_info.get('date_mentioned', 'Data a definir')
            time_mentioned = extracted_info.get('time_mentioned', 'Horário a definir')
            
            # Gerar link de handoff
            from .handoff_service import handoff_service
            
            handoff_link = handoff_service.generate_appointment_handoff_link(
                patient_name=patient_name,
                doctor_name=doctor_name,
                date=date_mentioned,
                time=time_mentioned,
                appointment_type=extracted_info.get('appointment_type', 'Consulta')
            )
            
            # Criar mensagem de confirmação com link
            confirmation_message = f"""✅ **Perfeito! Vamos confirmar seu pré-agendamento:**

📋 **RESUMO:**
👤 Paciente: {patient_name}
👨‍⚕️ Médico: {doctor_name}
📅 Data: {date_mentioned}
🕐 Horário: {time_mentioned}

**🔄 Para CONFIRMAR definitivamente:**
👩‍💼 Nossa secretária validará a disponibilidade e confirmará seu agendamento.

**📞 Clique no link abaixo para falar diretamente com nossa equipe:**
{handoff_link}"""
            
            return {
                'action': 'generate_handoff',
                'response_type': 'handoff_generated',
                'next_state': 'appointment_confirmed',
                'message': confirmation_message,
                'handoff_link': handoff_link,
                'entities': {
                    'patient_name': patient_name,
                    'doctor_name': doctor_name,
                    'date': date_mentioned,
                    'time': time_mentioned
                }
            }
            
        except Exception as e:
            logger.error(f"Erro ao gerar handoff: {e}")
            return {
                'action': 'handoff_error',
                'response_type': 'error',
                'next_state': 'idle',
                'message': 'Desculpe, ocorreu um erro ao processar sua confirmação. Tente novamente.'
            }

    def _validate_doctor(self, doctor_name: str) -> Optional[Dict]:
        """
        Valida se médico existe no banco de dados
        """
        try:
            clinic_data = self.rag_service.get_all_clinic_data()
            medicos = clinic_data.get('medicos', [])
            
            # Buscar médico por nome (busca flexível)
            doctor_name_lower = doctor_name.lower().strip()
            
            for medico in medicos:
                medico_name_lower = medico.get('nome', '').lower()
                
                # Busca exata ou parcial
                if (doctor_name_lower in medico_name_lower or 
                    medico_name_lower in doctor_name_lower):
                    return medico
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao validar médico: {e}")
            return None

    def _get_doctor_availability(self, doctor_name: str, date_filter: str = None) -> Dict[str, Any]:
        """
        Consulta disponibilidade do médico no Google Calendar
        """
        try:
            # Consultar disponibilidade para os próximos 7 dias
            availability = self.calendar_service.get_doctor_availability(
                doctor_name=doctor_name,
                days_ahead=7
            )
            
            if not availability:
                return {
                    'available': False,
                    'reason': 'calendar_error',
                    'message': 'Erro ao consultar agenda'
                }
            
            # Filtrar por data se especificada
            days_info = availability.get('days', [])
            if date_filter:
                target_date = self._parse_date(date_filter)
                if target_date:
                    # Filtrar apenas o dia solicitado
                    filtered_days = [day for day in days_info 
                                   if datetime.strptime(day['date'], '%d/%m/%Y').date() == target_date]
                    days_info = filtered_days
            
            return {
                'available': len(days_info) > 0,
                'doctor': doctor_name,
                'days': days_info,
                'total_days': len(days_info)
            }
            
        except Exception as e:
            logger.error(f"Erro ao consultar disponibilidade: {e}")
            return {
                'available': False,
                'reason': 'error',
                'message': 'Erro ao consultar disponibilidade'
            }

    def _check_real_availability(self, doctor_name: str, date_str: str, time_str: str) -> Dict[str, Any]:
        """
        Verifica disponibilidade real no Google Calendar
        """
        try:
            # Converter data para formato adequado
            target_date = self._parse_date(date_str)
            target_time = self._parse_time(time_str)
            
            if not target_date or not target_time:
                return {
                    'available': False,
                    'reason': 'invalid_date_time',
                    'message': 'Data ou horário inválidos'
                }
            
            # Verificar disponibilidade no Google Calendar
            availability = self.calendar_service.get_doctor_availability(
                doctor_name=doctor_name,
                start_date=target_date,
                days=1
            )
            
            if not availability:
                return {
                    'available': False,
                    'reason': 'calendar_error',
                    'message': 'Erro ao consultar agenda'
                }
            
            # Verificar se horário específico está disponível
            day_availability = availability.get('days', [])
            if not day_availability:
                return {
                    'available': False,
                    'reason': 'no_schedule',
                    'message': 'Médico não atende neste dia'
                }
            
            day_info = day_availability[0]
            available_times = day_info.get('available_times', [])
            
            # Verificar se horário solicitado está disponível
            time_available = target_time in available_times
            
            return {
                'available': time_available,
                'requested_time': target_time,
                'available_times': available_times,
                'occupied_times': day_info.get('occupied_times', []),
                'date': target_date.strftime('%d/%m/%Y'),
                'doctor': doctor_name
            }
            
        except Exception as e:
            logger.error(f"Erro ao verificar disponibilidade: {e}")
            return {
                'available': False,
                'reason': 'error',
                'message': 'Erro ao verificar disponibilidade'
            }

    def _parse_date(self, date_str: str) -> Optional[date]:
        """
        Converte string de data para objeto date
        """
        try:
            today = timezone.now().date()
            date_lower = date_str.lower().strip()
            
            if 'hoje' in date_lower:
                return today
            elif 'amanhã' in date_lower:
                return today + timedelta(days=1)
            elif 'depois de amanhã' in date_lower:
                return today + timedelta(days=2)
            elif 'segunda' in date_lower:
                days_ahead = 0 - today.weekday()  # Monday is 0
                if days_ahead <= 0:  # Target day already happened this week
                    days_ahead += 7
                return today + timedelta(days=days_ahead)
            elif 'terça' in date_lower:
                days_ahead = 1 - today.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                return today + timedelta(days=days_ahead)
            elif 'quarta' in date_lower:
                days_ahead = 2 - today.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                return today + timedelta(days=days_ahead)
            elif 'quinta' in date_lower:
                days_ahead = 3 - today.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                return today + timedelta(days=days_ahead)
            elif 'sexta' in date_lower:
                days_ahead = 4 - today.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                return today + timedelta(days=days_ahead)
            
            # Tentar parsear formato DD/MM ou DD/MM/YYYY
            import re
            date_match = re.search(r'(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?', date_str)
            if date_match:
                day, month, year = date_match.groups()
                year = int(year) if year else today.year
                if year < 100:
                    year += 2000
                return date(int(year), int(month), int(day))
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao parsear data: {e}")
            return None

    def _parse_time(self, time_str: str) -> Optional[str]:
        """
        Converte string de horário para formato HH:MM
        """
        try:
            import re
            
            time_lower = time_str.lower().strip()
            
            # Padrão HH:MM
            time_match = re.search(r'(\d{1,2}):(\d{2})', time_str)
            if time_match:
                hour, minute = time_match.groups()
                return f"{int(hour):02d}:{minute}"
            
            # Padrão HHhMM ou HHh
            time_match = re.search(r'(\d{1,2})h(\d{2})?', time_str)
            if time_match:
                hour, minute = time_match.groups()
                minute = minute or '00'
                return f"{int(hour):02d}:{minute}"
            
            # Padrão "X da manhã/tarde/noite"
            time_match = re.search(r'(\d{1,2})\s+da\s+(manhã|tarde|noite)', time_lower)
            if time_match:
                hour, period = time_match.groups()
                hour = int(hour)
                
                if period == 'manhã':
                    return f"{hour:02d}:00"
                elif period == 'tarde':
                    if hour < 12:
                        hour += 12
                    return f"{hour:02d}:00"
                elif period == 'noite':
                    if hour < 12:
                        hour += 12
                    return f"{hour:02d}:00"
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao parsear horário: {e}")
            return None

    # Métodos de mensagens
    def _get_doctor_not_found_message(self, doctor_mentioned: str) -> str:
        return f"""❌ Não encontrei o médico "{doctor_mentioned.title()}".

Nossos médicos disponíveis são:
• Dr. Gustavo (Medicina do Sono, Pneumologia)
• Dr. Gleyton Porto (Endocrinologia)

Para qual médico gostaria de consultar os horários?"""

    def _get_doctor_list_message(self) -> str:
        return """👨‍⚕️ **Nossos médicos disponíveis:**

**Dr. Gustavo**
🩺 Medicina do Sono, Pneumologia
💰 Consulta particular: R$ 150,00

**Dr. Gleyton Porto**
🩺 Endocrinologia  
💰 Consulta particular: R$ 150,00

Para consultar horários, digite o nome do médico desejado."""

    def _get_availability_info_message(self, doctor_info: Dict, availability: Dict, date_filter: str = None) -> str:
        doctor_name = doctor_info.get('nome', 'Médico')
        specialties = doctor_info.get('especialidades_display', 'Especialidade não informada')
        price = doctor_info.get('preco_particular', 'Preço não informado')
        
        if not availability.get('available'):
            # Se não há horários para o dia específico, consultar outros dias
            general_availability = self._get_doctor_availability(doctor_name, None)
            
            if general_availability.get('available'):
                days_info = general_availability.get('days', [])
                message = f"""👨‍⚕️ **{doctor_name}**
🩺 {specialties}
💰 Consulta particular: R$ {price}

❌ Não há horários disponíveis para a data solicitada.

📅 **Mas temos horários disponíveis em outros dias:**

"""
                for day in days_info[:3]:  # Mostrar até 3 dias
                    date_str = day.get('date', '')
                    weekday = day.get('weekday', '')
                    available_times = day.get('available_times', [])
                    
                    if available_times:
                        message += f"**{weekday} ({date_str}):** {', '.join(available_times[:4])}\n"
                
                message += f"""
📞 **Para agendar:**
(73) 3613-5380 | (73) 98822-1003"""
                
                return message
            else:
                return f"""👨‍⚕️ **{doctor_name}**
🩺 {specialties}
💰 Consulta particular: R$ {price}

❌ Não há horários disponíveis no momento.

Entre em contato conosco para mais informações:
📞 (73) 3613-5380
📱 (73) 98822-1003"""

        days_info = availability.get('days', [])
        
        message = f"""👨‍⚕️ **{doctor_name}**
🩺 {specialties}
💰 Consulta particular: R$ {price}

📅 **Horários disponíveis:**"""

        for day in days_info[:5]:  # Mostrar até 5 dias
            date_str = day.get('date', '')
            weekday = day.get('weekday', '')
            available_times = day.get('available_times', [])
            occupied_times = day.get('occupied_times', [])
            
            if available_times:
                message += f"\n\n**{weekday} ({date_str}):**"
                message += f"\n✅ Disponíveis: {', '.join(available_times[:6])}"  # Até 6 horários
                if len(available_times) > 6:
                    message += f" (+{len(available_times) - 6} outros)"
        
        if len(days_info) > 5:
            message += f"\n\n📅 *E mais {len(days_info) - 5} dias com horários disponíveis*"
        
        message += f"""

📞 **Para agendar:**
(73) 3613-5380 | (73) 98822-1003"""
        
        return message

    def _get_fallback_analysis(self) -> Dict[str, Any]:
        return {
            'action': 'fallback',
            'response_type': 'error',
            'next_state': 'idle',
            'message': 'Desculpe, ocorreu um erro. Como posso ajudá-lo?'
        }


# Instância global do serviço
smart_scheduling_service = SmartSchedulingService()
