"""
Serviço de Consulta de Horários
Consulta disponibilidade no Google Calendar e informa horários ao usuário
"""
import logging
import re
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from django.utils import timezone

# Importar função e constantes compartilhadas do session_manager
from .gemini.session_manager import (PRONOUN_DOCTOR_MESSAGE_TERMS,
                                     PRONOUN_DOCTOR_REGEX,
                                     PRONOUN_DOCTOR_TERMS,
                                     resolve_doctor_reference)
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
        Extrai informações de agendamento da mensagem e complementa com dados da sessão
        
        Estratégia:
        1. Tenta extrair informações da mensagem atual (usando regex)
        2. Se não encontrar na mensagem, busca na sessão (informações de mensagens anteriores)
        3. Retorna informações combinadas para manter contexto da conversa
        """
        message_lower = message.lower()

        info = {
            'message': message_lower,
            'doctor_mentioned': None,
            'specialty_mentioned': None,
            'date_mentioned': None,
            'time_mentioned': None,
            'appointment_type': None
        }
        
        # Extrair médico mencionado da mensagem
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
                doctor_reference = match.group(1).strip()
                resolved_doctor = resolve_doctor_reference(doctor_reference, message_lower, session)
                if resolved_doctor:
                    info['doctor_mentioned'] = resolved_doctor
                    logger.info(f"🤝 Referência ao médico interpretada como: {resolved_doctor}")
                    break
                # Caso a referência encontrada seja apenas um pronome sem contexto, continuar procurando
        
        # Se não encontrou médico na mensagem, buscar na sessão
        if not info['doctor_mentioned'] and session.get('selected_doctor'):
            info['doctor_mentioned'] = session.get('selected_doctor')
            logger.info(f"🔄 Médico recuperado da sessão: {info['doctor_mentioned']}")
        
        # Extrair data mencionada da mensagem
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
        
        # Se não encontrou data na mensagem, buscar na sessão
        if not info['date_mentioned'] and session.get('preferred_date'):
            info['date_mentioned'] = session.get('preferred_date')
            logger.info(f"🔄 Data recuperada da sessão: {info['date_mentioned']}")
        
        # Extrair horário mencionado da mensagem
        time_patterns = [
            r'(as|às)\s+(\d{1,2})h(\d{2})?',
            r'(as|às)\s+(\d{1,2})hr(\d{2})?',
            r'(\d{1,2})horas(\d{2})?',
            r'(as|às)\s+(\d{1,2})',
            r'(as|às)\s+(\d{1,2})horas(\d{2})?',
            r'(as|às)\s+(\d{1,2}):(\d{2})',
            r'(as|às)\s+(\d{1,2})\s+hr\s+(\d{2})?',
            r'(as|às)\s+(\d{1,2})\s+horas\s+(\d{2})?',
            r'(\d{1,2}):(\d{2})',
            r'(\d{1,2})\s+horas\s+(\d{2})?',
            r'(\d{1,2})hr(\d{2})?',
            r'(\d{1,2})\s+da\s+(manhã|tarde|noite)',
            r'de\s+manhã|da\s+tarde|à\s+noite'
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, message_lower)
            if match:
                info['time_mentioned'] = match.group(0).strip()
                break
        
        # Se não encontrou horário na mensagem, buscar na sessão
        if not info['time_mentioned'] and session.get('preferred_time'):
            info['time_mentioned'] = session.get('preferred_time')
            logger.info(f"🔄 Horário recuperado da sessão: {info['time_mentioned']}")
        
        # Extrair tipo de consulta
        if any(word in message_lower for word in ['consulta', 'retorno']):
            if 'retorno' in message_lower:
                info['appointment_type'] = 'retorno'
            else:
                info['appointment_type'] = 'consulta'
        
        # Log das informações extraídas
        logger.info(f"📋 Informações extraídas - Médico: {info['doctor_mentioned']}, "
                   f"Data: {info['date_mentioned']}, Horário: {info['time_mentioned']}")
        
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
                availability = self.get_doctor_availability(doctor_info['nome'], days_ahead=7, date_filter=date_mentioned)
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
            'sim', 'confirmo', 'confirma', 'está correto', 'está certo','s',
            'perfeito', 'ótimo', 'ok', 'beleza', 'pode ser',
            'quero esse horário', 'aceito', 'concordo', 'isso está correto','isso','confirmado','correto'
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
            specialty = session.get('selected_specialty', 'Especialidade a definir')
            date_mentioned = extracted_info.get('date_mentioned', 'Data a definir')
            time_mentioned = extracted_info.get('time_mentioned', 'Horário a definir')
            
            # Gerar link de handoff
            from .handoff_service import handoff_service
            
            handoff_link = handoff_service.generate_appointment_handoff_link(
                patient_name=patient_name,
                doctor_name=doctor_name,
                specialty=specialty,
                date=date_mentioned,
                time=time_mentioned
            )
            
            # Criar mensagem de confirmação com link
            confirmation_message = f"""✅ **Perfeito! Vamos confirmar seu pré-agendamento:**

📋 **RESUMO:**
👤 Paciente: {patient_name}
👨‍⚕️ Médico: {doctor_name}
🧠 Especialidade: {specialty}
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


    def _parse_date(self, date_str: str) -> Optional[date]:
        """
        Converte string de data para objeto date
        Suporta múltiplos formatos: DD/MM, DD/MM/YYYY, YYYY-MM-DD, nomes de dias, etc.
        """
        import re  # Import no início da função
        
        try:
            today = timezone.now().date()
            date_lower = date_str.lower().strip()
            
            # Se já é um objeto date, retornar diretamente
            if isinstance(date_str, date):
                return date_str
            
            # Tentar formato ISO primeiro (YYYY-MM-DD)
            if re.match(r'^\d{4}-\d{1,2}-\d{1,2}$', date_str):
                try:
                    return datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    logger.warning(f"Erro ao parsear data ISO: {date_str}")
            
            # Nomes de dias relativos
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
            date_match = re.search(r'(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?', date_str)
            if date_match:
                day, month, year = date_match.groups()
                year = int(year) if year else today.year
                if year < 100:
                    year += 2000
                return date(int(year), int(month), int(day))
            
            # Se só tem um número (ex: "20"), assumir como dia do mês atual
            if re.match(r'^\d{1,2}$', date_str):
                try:
                    day = int(date_str)
                    # Verificar se o dia é válido
                    if 1 <= day <= 31:
                        # Tentar criar data com mês/ano atuais
                        try:
                            result_date = date(today.year, today.month, day)
                            # Se a data resultante já passou, assumir mês seguinte
                            if result_date < today:
                                # Tentar próximo mês
                                if today.month == 12:
                                    result_date = date(today.year + 1, 1, day)
                                else:
                                    result_date = date(today.year, today.month + 1, day)
                            logger.info(f"✅ Dia isolado '{day}' convertido para: {result_date}")
                            return result_date
                        except ValueError:
                            # Dia inválido para o mês (ex: 31 de fevereiro)
                            logger.warning(f"⚠️ Dia {day} inválido para mês {today.month}")
                except ValueError:
                    pass
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao parsear data '{date_str}': {e}")
            return None

    # REMOVIDO: _parse_time() - função não utilizada (código morto)
    # Era usada apenas por _check_real_availability() que também foi removida
    # O parsing de horário é feito pelo entity_extractor que retorna no formato correto

    # Métodos de mensagens
    def _format_doctor_price(self, preco) -> str:
        """
        Formata preço para exibição em moeda brasileira
        """
        if preco is None:
            return "Preço sob consulta"
        
        try:
            # Converter para float (funciona com Decimal, string ou número)
            preco_value = float(preco)
            
            # Formatar como R$ 150,00
            return f"R$ {preco_value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        except (ValueError, TypeError):
            return "Preço sob consulta"
    
    def _get_doctor_list_message(self, include_header: bool = True) -> str:
        """
        Obtém mensagem com lista de médicos do banco de dados
        
        Args:
            include_header: Se True, inclui o cabeçalho "👨‍⚕️ **Nossos médicos disponíveis:**"
        """
        try:
            medicos = self.rag_service.get_medicos()
            
            if not medicos:
                header = "👨‍⚕️ **Nossos médicos disponíveis:**\n\n" if include_header else ""
                return f"""{header}❌ Não há médicos cadastrados no momento.

Entre em contato conosco para mais informações."""
            
            message = ""
            if include_header:
                message = "👨‍⚕️ **Nossos médicos disponíveis:**\n\n"
            
            for medico in medicos:
                nome = medico.get('nome', 'Médico')
                especialidades = medico.get('especialidades_display', 'Especialidade não informada')
                preco = medico.get('preco_particular')
                
                message += f"**{nome}**\n"
                message += f"🩺 {especialidades}\n"
                message += f"💰 Consulta particular: {self._format_doctor_price(preco)}\n\n"
            
            if include_header:
                message += "Para consultar horários, digite o nome do médico desejado."
            
            return message
            
        except Exception as e:
            logger.error(f"Erro ao obter lista de médicos: {e}")
            header = "👨‍⚕️ **Nossos médicos disponíveis:**\n\n" if include_header else ""
            return f"""{header}❌ Erro ao carregar informações dos médicos.

Entre em contato conosco para mais informações."""

    def _get_doctor_not_found_message(self, doctor_mentioned: str) -> str:
        """
        Obtém mensagem de médico não encontrado, incluindo lista de médicos disponíveis do banco de dados
        """
        doctor_list_message = self._get_doctor_list_message(include_header=True)
        
        return f"""❌ Não encontrei o médico "{doctor_mentioned.title()}".

{doctor_list_message}

Para qual médico gostaria de consultar os horários?"""

    def _get_availability_info_message(self, doctor_info: Dict, availability: Dict, date_filter: str = None) -> str:
        """
        Formata mensagem com informações de disponibilidade do médico
        
        Args:
            doctor_info: Dicionário com informações do médico (nome, especialidades, preço)
            availability: Dicionário com informações de disponibilidade (days, available)
            date_filter: Data filtrada (opcional) - usado para personalizar a mensagem
        
        Returns:
            String formatada com mensagem de disponibilidade
        """
        doctor_name = doctor_info.get('nome', 'Médico')
        specialties = doctor_info.get('especialidades_display', 'Especialidade não informada')
        price = doctor_info.get('preco_particular')
        
        # Formatar preço usando função auxiliar (lida com None, Decimal, int, float, string)
        price_formatted = self._format_doctor_price(price)
        
        if not availability.get('available'):
            # Se não há horários para o dia específico, consultar outros dias
            general_availability = self.get_doctor_availability(doctor_name, days_ahead=7, date_filter=None)
            
            if general_availability.get('available'):
                days_info = general_availability.get('days', [])
                
                # Personalizar mensagem com a data solicitada se houver filtro
                date_message = ""
                if date_filter:
                    date_display = date_filter.title() if isinstance(date_filter, str) else str(date_filter)
                    date_message = f" para {date_display}"
                
                message = f"""👨‍⚕️ **{doctor_name}**
🩺 {specialties}
💰 Consulta particular: {price_formatted}

❌ Não há horários disponíveis{date_message}.

📅 **Mas temos horários disponíveis em outros dias:**

"""
                for day in days_info[:3]:  # Mostrar até 3 dias
                    date_str = day.get('date', '')
                    weekday = day.get('weekday', '')
                    available_times = day.get('available_times', [])
                    
                    if available_times:
                        message += f"**{weekday} ({date_str}):** {', '.join(available_times[:4])}\n"
                
                message += f"""
📞 **Se quiser pode agendar ligando para:**
(73) 3613-5380"""
                
                return message
            else:
                return f"""👨‍⚕️ **{doctor_name}**
🩺 {specialties}
💰 Consulta particular: {price_formatted}

❌ Não há horários disponíveis no momento.

Entre em contato conosco para mais informações ligando para:
📞 (73) 3613-5380
"""

        days_info = availability.get('days', [])
        
        # Personalizar cabeçalho com data filtrada se houver
        availability_header = "*Horários disponíveis:*"
        if date_filter:
            date_display = date_filter.title() if isinstance(date_filter, str) else str(date_filter)
            availability_header = f"*Horários disponíveis para {date_display}:*"
        
        message = f"""👨‍⚕️ **{doctor_name}**
🩺 {specialties}
💰 Consulta particular: {price_formatted}

📅 {availability_header}"""

        for day in days_info[:5]:  # Mostrar até 5 dias
            date_str = day.get('date', '')
            weekday = day.get('weekday', '')
            available_times = day.get('available_times', [])
            
            if available_times:
                message += f"\n\n*{weekday} ({date_str}):*"
                message += f"\n✅ Disponíveis: {', '.join(available_times[:6])}"  # Até 6 horários
                if len(available_times) > 6:
                    message += f" (+{len(available_times) - 6} outros)"
        
        if len(days_info) > 5:
            message += f"\n\n📅 *E mais {len(days_info) - 5} dias com horários disponíveis*"
        
        return message

    def get_doctor_availability(self, doctor_name: str, days_ahead: int = 7, date_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        Consulta disponibilidade do médico no Google Calendar
        
        Baseado no GUIA_SECRETARIA_CALENDAR.md:
        - Consulta Google Calendar em tempo real
        - Filtra eventos por padrão "Dr. Nome - Tipo"
        - Calcula horários livres nos próximos dias
        
        Args:
            doctor_name: Nome do médico (ex: "Dr. João Carvalho")
            days_ahead: Quantos dias à frente consultar (padrão: 7)
            date_filter: Data específica para filtrar (opcional, ex: "20/11", "amanhã")
                        Se especificado, retorna apenas o dia solicitado
            
        Returns:
            Dict com informações de disponibilidade:
            - success: bool - Se a consulta foi bem-sucedida
            - doctor_name: str - Nome do médico
            - days_ahead: int - Quantos dias foram consultados
            - days_info: list - Lista de dias com horários disponíveis
            - available_slots: int - Total de slots disponíveis
            - has_availability: bool - Se há horários disponíveis
            - available: bool - Compatibilidade com código antigo
            - doctor: str - Compatibilidade com código antigo
            - total_days: int - Compatibilidade com código antigo
            - error: str - Mensagem de erro (se houver)
        """
        try:
            if date_filter:
                logger.info(f"🗓️ Consultando disponibilidade para {doctor_name} - filtrando por data: {date_filter}")
            else:
                logger.info(f"🗓️ Consultando disponibilidade para {doctor_name} - próximos {days_ahead} dias")
            
            # Consultar disponibilidade para os próximos 7 dias (máximo)
            # Depois filtramos conforme necessário
            availability = self.calendar_service.get_doctor_availability(
                doctor_name=doctor_name,
                days_ahead=7
            )
            
            if not availability:
                return {
                    'success': False,
                    'available': False,
                    'doctor_name': doctor_name,
                    'doctor': doctor_name,
                    'days_ahead': days_ahead,
                    'days_info': [],
                    'available_slots': 0,
                    'has_availability': False,
                    'total_days': 0,
                    'reason': 'calendar_error',
                    'message': 'Erro ao consultar agenda',
                    'error': 'Erro ao consultar agenda'
                }
            
            # Obter lista de dias
            days_info = availability.get('days', [])
            
            # Filtrar por data específica se solicitado
            if date_filter:
                target_date = self._parse_date(date_filter)
                if target_date:
                    # Filtrar apenas o dia solicitado
                    filtered_days = [day for day in days_info 
                                   if datetime.strptime(day['date'], '%d/%m/%Y').date() == target_date]
                    days_info = filtered_days
                else:
                    # Se não conseguiu parsear a data, retornar erro
                    logger.warning(f"⚠️ Não foi possível parsear a data: {date_filter}")
                    return {
                        'success': False,
                        'available': False,
                        'doctor_name': doctor_name,
                        'doctor': doctor_name,
                        'days_ahead': days_ahead,
                        'days_info': [],
                        'available_slots': 0,
                        'has_availability': False,
                        'total_days': 0,
                        'reason': 'invalid_date',
                        'message': f'Data inválida: {date_filter}',
                        'error': f'Data inválida: {date_filter}'
                    }
            
            # Limitar aos dias solicitados (se não foi filtrado por data específica)
            if not date_filter and days_ahead < 7:
                days_info = days_info[:days_ahead]
            
            # Verificar se há horários disponíveis
            has_availability = any(len(day.get('available_times', [])) > 0 for day in days_info)
            
            # Contar slots disponíveis
            total_slots = sum(len(day.get('available_times', [])) for day in days_info)
            
            # Retornar formato unificado com compatibilidade
            return {
                'success': True,
                'available': has_availability,
                'doctor_name': doctor_name,
                'doctor': doctor_name,  # Compatibilidade
                'days_ahead': days_ahead,
                'days_info': days_info,
                'available_slots': total_slots,
                'has_availability': has_availability,
                'total_days': len(days_info)  # Compatibilidade
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao consultar disponibilidade para {doctor_name}: {e}")
            return {
                'success': False,
                'available': False,
                'doctor_name': doctor_name,
                'doctor': doctor_name,
                'days_ahead': days_ahead,
                'days_info': [],
                'available_slots': 0,
                'has_availability': False,
                'total_days': 0,
                'reason': 'error',
                'message': 'Erro ao consultar disponibilidade',
                'error': str(e)
            }

    def is_time_slot_available(self, doctor_name: str, requested_date: str, requested_time: str) -> Dict[str, Any]:
        """
        Verifica se um horário específico está disponível no calendário
        
        Args:
            doctor_name: Nome do médico
            requested_date: Data solicitada (formato DD/MM ou DD/MM/YYYY ou date object)
            requested_time: Horário solicitado (formato HH:MM ou time object)
            
        Returns:
            Dict com:
                - available: bool - Se o horário está disponível
                - date_formatted: str - Data formatada (DD/MM/YYYY)
                - time_formatted: str - Horário formatado (HH:MM)
                - alternative_times: list - Horários alternativos próximos (se não disponível)
                - message: str - Mensagem descritiva
        """
        try:
            # Normalizar data
            if isinstance(requested_date, str):
                logger.info(f"📅 Parseando data string: '{requested_date}'")
                target_date = self._parse_date(requested_date)
                if target_date:
                    logger.info(f"✅ Data parseada com sucesso: {target_date}")
                else:
                    logger.error(f"❌ Falha ao parsear data: '{requested_date}'")
            elif isinstance(requested_date, date):
                target_date = requested_date
                logger.info(f"📅 Data já é objeto date: {target_date}")
            else:
                # Tentar converter tipos diversos
                logger.warning(f"⚠️ Tipo de data inesperado: {type(requested_date)}")
                target_date = None
            
            if not target_date:
                return {
                    'available': False,
                    'error': 'Data inválida',
                    'message': 'Não foi possível processar a data solicitada.'
                }
            
            # Normalizar horário
            logger.info(f"⏰ Parseando horário: '{requested_time}' (tipo: {type(requested_time)})")
            if isinstance(requested_time, str):
                # Remover "as" ou "às" se presente
                time_clean = requested_time.lower().replace('as ', '').replace('às ', '').replace('horas', '').replace('h', '').strip()
                # Remover segundos se presente (HH:MM:SS -> HH:MM)
                if time_clean.count(':') == 2:
                    time_clean = ':'.join(time_clean.split(':')[:2])
                # Garantir formato HH:MM
                if ':' not in time_clean:
                    if len(time_clean) <= 2:
                        # Se é só um número (ex: "8"), adicionar ":00"
                        time_clean = f"{time_clean.zfill(2)}:00"
                time_str = time_clean
            else:
                # Se é um objeto time
                time_str = requested_time.strftime('%H:%M')
            
            # Garantir formato HH:MM com zero à esquerda se necessário
            if len(time_str.split(':')[0]) == 1:
                time_str = f"0{time_str}"
            
            logger.info(f"✅ Horário normalizado para: '{time_str}'")
            
            # ═══════════════════════════════════════════════════════════════════
            # VERIFICAR SE A DATA É HOJE E SE JÁ PASSOU O HORÁRIO DE EXPEDIENTE
            # ═══════════════════════════════════════════════════════════════════
            from django.utils import timezone
            today = timezone.now().date()
            current_time = timezone.now().time()
            
            if target_date == today:
                # Se é hoje, verificar se já passou o horário de expediente (18:00)
                from datetime import time as dt_time
                end_of_day = dt_time(18, 0)  # 18:00
                
                # Converter time_str para objeto time para comparação
                try:
                    requested_time_obj = datetime.strptime(time_str, '%H:%M').time()
                    
                    # Se o horário solicitado já passou hoje OU se já passou 18:00
                    if requested_time_obj < current_time or current_time >= end_of_day:
                        logger.warning(f"⚠️ Data é hoje ({today}) mas horário já passou ou expediente acabou")
                        
                        # Consultar disponibilidade para outros dias
                        availability = self.get_doctor_availability(
                            doctor_name=doctor_name,
                            days_ahead=7
                        )
                        
                        if availability.get('has_availability'):
                            days_info = availability.get('days_info', [])
                            # Filtrar apenas dias futuros (não hoje)
                            future_days = [day for day in days_info 
                                         if datetime.strptime(day['date'], '%d/%m/%Y').date() > today]
                            
                            if future_days:
                                alternative_days = []
                                for day in future_days[:3]:
                                    if day.get('available_times'):
                                        alternative_days.append({
                                            'date': day.get('date'),
                                            'weekday': day.get('weekday'),
                                            'times': day.get('available_times', [])[:5]
                                        })
                                
                                return {
                                    'available': False,
                                    'date_formatted': target_date.strftime('%d/%m/%Y'),
                                    'time_formatted': time_str,
                                    'message': f'Hoje ({target_date.strftime("%d/%m/%Y")}) o expediente já acabou ou o horário {time_str} já passou.',
                                    'alternative_days': alternative_days,
                                    'alternative_times': [],
                                    'reason': 'past_time_today'
                                }
                except ValueError:
                    logger.warning(f"⚠️ Erro ao converter horário para comparação: {time_str}")
                    # Continuar com validação normal se não conseguir converter
            
            # Consultar disponibilidade do médico
            availability = self.get_doctor_availability(
                doctor_name=doctor_name,
                days_ahead=7
            )
            
            if not availability.get('has_availability'):
                return {
                    'available': False,
                    'message': f'O médico {doctor_name} não tem horários disponíveis nos próximos dias.',
                    'alternative_times': []
                }
            
            # Procurar o dia específico
            days_info = availability.get('days_info', [])
            if not days_info:
                days_info = availability.get('days', [])  # Compatibilidade com formato antigo
            
            target_date_str = target_date.strftime('%d/%m/%Y')
            
            logger.info(f"🔍 DEBUG - Procurando dia {target_date_str} em {len(days_info)} dias disponíveis")
            
            target_day = None
            for day in days_info:
                day_date = day.get('date')
                logger.debug(f"  Comparando: '{day_date}' == '{target_date_str}'")
                if day_date == target_date_str:
                    target_day = day
                    logger.info(f"✅ Dia encontrado: {day_date}")
                    break
            
            if not target_day:
                # Dia não tem disponibilidade - sugerir dias próximos
                logger.warning(f"⚠️ Dia {target_date_str} não encontrado na disponibilidade")
                alternative_days = []
                for day in days_info[:3]:
                    if day.get('available_times'):
                        alternative_days.append({
                            'date': day.get('date'),
                            'weekday': day.get('weekday'),
                            'times': day.get('available_times', [])[:5]
                        })
                
                logger.info(f"📅 Sugerindo {len(alternative_days)} dias alternativos")
                return {
                    'available': False,
                    'date_formatted': target_date_str,
                    'message': f'Não há horários disponíveis para {target_date_str}.',
                    'alternative_days': alternative_days,
                    'alternative_times': []
                }
            
            # Verificar se o horário específico está disponível
            available_times = target_day.get('available_times', [])
            logger.info(f"📋 Horários disponíveis no dia {target_date_str}: {len(available_times)} horários")
            logger.debug(f"  Horários: {available_times[:10]}")  # Mostrar até 10 para debug
            
            # Normalizar horários para comparação (remover segundos se necessário)
            available_times_normalized = []
            for t in available_times:
                t_clean = t.strip()
                # Se tem formato HH:MM:SS, converter para HH:MM
                if t_clean.count(':') == 2:
                    t_clean = ':'.join(t_clean.split(':')[:2])
                available_times_normalized.append(t_clean)
            
            # Normalizar horário solicitado
            time_str_normalized = time_str.strip()
            # Se tem formato HH:MM:SS, converter para HH:MM
            if time_str_normalized.count(':') == 2:
                time_str_normalized = ':'.join(time_str_normalized.split(':')[:2])
            
            logger.info(f"🔍 Verificando se '{time_str_normalized}' está em {available_times_normalized[:5]}...")
            
            is_available = time_str_normalized in available_times_normalized
            
            if is_available:
                logger.info(f"✅ Horário {time_str_normalized} está disponível!")
                return {
                    'available': True,
                    'date_formatted': target_date_str,
                    'time_formatted': time_str_normalized,
                    'weekday': target_day.get('weekday'),
                    'message': f'Horário {time_str_normalized} disponível em {target_date_str}.'
                }
            else:
                # Horário não disponível - sugerir horários próximos do mesmo dia
                logger.warning(f"❌ Horário {time_str_normalized} NÃO está disponível")
                logger.info(f"📅 Retornando {len(available_times)} horários alternativos")
                logger.info(f"📋 Horários alternativos: {available_times[:8]}")
                
                result = {
                    'available': False,
                    'date_formatted': target_date_str,
                    'time_formatted': time_str_normalized,
                    'weekday': target_day.get('weekday'),
                    'message': f'O horário {time_str_normalized} não está disponível em {target_date_str}.',
                    'alternative_times': available_times[:8],  # Até 8 horários alternativos
                    'total_alternatives': len(available_times)
                }
                logger.info(f"📦 RETORNO FINAL: {result}")
                return result
                
        except Exception as e:
            logger.error(f"Erro ao verificar disponibilidade de horário: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'available': False,
                'error': str(e),
                'message': 'Erro ao verificar disponibilidade do horário.'
            }
    
    def _get_fallback_analysis(self) -> Dict[str, Any]:
        return {
            'action': 'fallback',
            'response_type': 'error',
            'next_state': 'idle',
            'message': 'Desculpe, ocorreu um erro. Como posso ajudá-lo?'
        }


# Instância global do serviço
smart_scheduling_service = SmartSchedulingService()
