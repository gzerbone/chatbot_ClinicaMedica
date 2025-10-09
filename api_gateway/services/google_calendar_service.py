"""
Serviço para integração com Google Calendar API
Consulta disponibilidade de horários dos médicos
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

# Importação condicional do Google Calendar API
try:
    from google.oauth2.credentials import Credentials
    from google.oauth2.service_account import \
        Credentials as ServiceAccountCredentials
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_CALENDAR_AVAILABLE = True
except ImportError:
    GOOGLE_CALENDAR_AVAILABLE = False

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class GoogleCalendarService:
    """
    Serviço para consultar disponibilidade no Google Calendar
    """
    
    def __init__(self):
        self.service = None
        self.enabled = getattr(settings, 'GOOGLE_CALENDAR_ENABLED', False)
        
        if not GOOGLE_CALENDAR_AVAILABLE:
            logger.warning("Google Calendar API não está disponível. Execute: pip install google-api-python-client google-auth")
            self.enabled = False
            return
        
        if not self.enabled:
            logger.info("Google Calendar está desabilitado nas configurações")
            return
            
        try:
            self._initialize_service()
        except Exception as e:
            logger.error(f"Erro ao inicializar Google Calendar: {e}")
            self.enabled = False
    
    def _initialize_service(self):
        """Inicializa o serviço do Google Calendar"""
        
        # Caminho para o arquivo de credenciais da conta de serviço
        service_account_file = getattr(settings, 'GOOGLE_SERVICE_ACCOUNT_FILE', '')
        
        if not service_account_file:
            logger.error("GOOGLE_SERVICE_ACCOUNT_FILE não configurado")
            raise ValueError("Arquivo de credenciais não configurado")
        
        try:
            # Usar conta de serviço (mais simples para aplicações server-side)
            credentials = ServiceAccountCredentials.from_service_account_file(
                service_account_file,
                scopes=['https://www.googleapis.com/auth/calendar.readonly']
            )
            
            self.service = build('calendar', 'v3', credentials=credentials)
            logger.info("Google Calendar API inicializada com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao configurar credenciais: {e}")
            raise
    
    def get_doctor_availability(self, doctor_name: str, days_ahead: int = 7) -> Dict[str, Any]:
        """
        Obtém disponibilidade de um médico nos próximos dias
        
        Args:
            doctor_name: Nome do médico
            days_ahead: Quantos dias à frente consultar
            
        Returns:
            Dicionário com disponibilidade por dia
        """
        if not self.enabled or not self.service:
            return self._get_mock_availability(doctor_name, days_ahead)
        
        try:
            # Usar calendário único da clínica
            clinic_calendar_id = self._get_clinic_calendar_id()
            
            # Definir período de consulta
            now = timezone.now()
            start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_time = start_time + timedelta(days=days_ahead)
            
            # Consultar eventos do médico específico no calendário da clínica
            events_result = self.service.events().list(
                calendarId=clinic_calendar_id,
                timeMin=start_time.isoformat(),
                timeMax=end_time.isoformat(),
                singleEvents=True,
                orderBy='startTime',
                q=doctor_name  # Buscar eventos que contenham o nome do médico
            ).execute()
            
            events = events_result.get('items', [])
            
            # Filtrar eventos específicos do médico
            doctor_events = self._filter_doctor_events(events, doctor_name)
            
            # Processar disponibilidade
            availability = self._process_availability(doctor_name, doctor_events, start_time, days_ahead)
            
            return availability
            
        except HttpError as e:
            logger.error(f"Erro na API do Google Calendar: {e}")
            return self._get_mock_availability(doctor_name, days_ahead)
        except Exception as e:
            logger.error(f"Erro ao consultar disponibilidade: {e}")
            return self._get_mock_availability(doctor_name, days_ahead)
    
    def _get_clinic_calendar_id(self) -> str:
        """
        Obtém o Calendar ID único da clínica
        
        Returns:
            Calendar ID da clínica configurado nas settings
        """
        clinic_calendar_id = getattr(settings, 'CLINIC_CALENDAR_ID', '')
        
        if not clinic_calendar_id:
            # Usar email padrão da clínica se não configurado
            clinic_domain = getattr(settings, 'CLINIC_DOMAIN', 'clinica.com')
            clinic_calendar_id = f"agenda@{clinic_domain}"
        
        return clinic_calendar_id
    
    def _filter_doctor_events(self, events: List[Dict], doctor_name: str) -> List[Dict]:
        """
        Filtra eventos do calendário único que pertencem ao médico específico
        
        Args:
            events: Lista de todos os eventos do calendário
            doctor_name: Nome do médico a filtrar
            
        Returns:
            Lista de eventos específicos do médico
        """
        doctor_events = []
        
        # Gerar keywords de forma inteligente
        keywords = self._generate_doctor_keywords(doctor_name)
        
        logger.debug(f"Buscando eventos para {doctor_name} com keywords: {keywords}")
        
        for event in events:
            event_title = event.get('summary', '').lower()
            event_description = event.get('description', '').lower()
            event_text = f"{event_title} {event_description}"
            
            # Verificar se o evento pertence ao médico
            if any(keyword in event_text for keyword in keywords):
                doctor_events.append(event)
                logger.debug(f"Evento encontrado para {doctor_name}: {event.get('summary', '')}")
        
        logger.info(f"Encontrados {len(doctor_events)} eventos para {doctor_name} no calendário da clínica")
        return doctor_events
    
    def _generate_doctor_keywords(self, doctor_name: str) -> List[str]:
        """
        Gera keywords para identificar eventos do médico no calendário
        
        PRIORIDADE:
        1. Padrões configurados manualmente (DOCTOR_EVENT_PATTERNS no settings.py)
        2. Padrões gerados automaticamente do banco de dados
        3. Padrões gerados do nome fornecido
        
        Args:
            doctor_name: Nome do médico
            
        Returns:
            Lista de keywords para buscar eventos
        """
        keywords = []
        normalized_doctor_name = doctor_name.lower().replace('dr. ', '').replace('dra. ', '')
        
        # 1. Tentar padrões configurados manualmente (FALLBACK para casos especiais)
        doctor_patterns = getattr(settings, 'DOCTOR_EVENT_PATTERNS', {})
        for pattern_key, pattern_list in doctor_patterns.items():
            if normalized_doctor_name in pattern_key or pattern_key in normalized_doctor_name:
                keywords.extend(pattern_list)
                logger.debug(f"✅ Usando padrões manuais configurados para {doctor_name}")
                return keywords
        
        # 2. Tentar gerar padrões do banco de dados (RECOMENDADO)
        try:
            from rag_agent.models import Medico

            # Buscar médico no banco
            medico = Medico.objects.filter(nome__icontains=normalized_doctor_name).first()
            
            if medico:
                # Gerar variações do nome do médico
                nome_completo = medico.nome.lower()
                partes_nome = nome_completo.split()
                
                keywords = [
                    nome_completo,                    # "joão carvalho"
                    f"dr. {nome_completo}",          # "dr. joão carvalho"
                    f"dra. {nome_completo}",         # "dra. joão carvalho"
                    f"dr {nome_completo}",           # "dr joão carvalho" (sem ponto)
                    f"dra {nome_completo}",          # "dra joão carvalho" (sem ponto)
                ]
                
                # Adicionar primeiro nome
                if len(partes_nome) > 0:
                    primeiro_nome = partes_nome[0]
                    keywords.extend([
                        primeiro_nome,
                        f"dr. {primeiro_nome}",
                        f"dra. {primeiro_nome}",
                        f"dr {primeiro_nome}",
                        f"dra {primeiro_nome}",
                    ])
                
                # Adicionar último sobrenome
                if len(partes_nome) > 1:
                    ultimo_sobrenome = partes_nome[-1]
                    keywords.extend([
                        ultimo_sobrenome,
                        f"dr. {ultimo_sobrenome}",
                        f"dra. {ultimo_sobrenome}",
                    ])
                
                logger.debug(f"✅ Keywords geradas automaticamente do banco para {doctor_name}: {len(keywords)} variações")
                return list(set(keywords))  # Remover duplicatas
                
        except Exception as e:
            logger.warning(f"⚠️ Não foi possível buscar médico no banco: {e}")
        
        # 3. Padrões gerados do nome fornecido (FALLBACK final)
        partes_nome = normalized_doctor_name.split()
        
        keywords = [
            doctor_name.lower(),
            normalized_doctor_name,
        ]
        
        # Adicionar primeiro nome
        if len(partes_nome) > 0:
            keywords.append(partes_nome[0])
            keywords.append(f"dr. {partes_nome[0]}")
            keywords.append(f"dra. {partes_nome[0]}")
        
        # Adicionar último nome
        if len(partes_nome) > 1:
            keywords.append(partes_nome[-1])
        
        logger.debug(f"⚠️ Usando keywords genéricas para {doctor_name}")
        return list(set(keywords))  # Remover duplicatas
    
    def _process_availability(self, doctor_name: str, events: List[Dict], start_date: datetime, days_ahead: int) -> Dict[str, Any]:
        """
        Processa eventos e gera disponibilidade
        """
        # Horários padrão de atendimento (pode vir do banco de dados)
        default_hours = self._get_doctor_working_hours(doctor_name)
        
        availability = {
            'doctor_name': doctor_name,
            'period': f"{start_date.strftime('%d/%m/%Y')} a {(start_date + timedelta(days=days_ahead-1)).strftime('%d/%m/%Y')}",
            'days': []
        }
        
        # Processar cada dia
        for day_offset in range(days_ahead):
            current_date = start_date + timedelta(days=day_offset)
            
            # Pular fins de semana se necessário
            if current_date.weekday() >= 5:  # Sábado=5, Domingo=6
                continue
            
            # Obter eventos do dia
            day_events = [
                event for event in events
                if self._is_same_day(current_date, event.get('start', {}).get('dateTime', ''))
            ]
            
            # Calcular horários disponíveis
            available_slots = self._calculate_available_slots(
                current_date, day_events, default_hours
            )
            
            if available_slots:
                availability['days'].append({
                    'date': current_date.strftime('%d/%m/%Y'),
                    'weekday': self._get_weekday_name(current_date.weekday()),
                    'available_times': available_slots
                })
        
        return availability
    
    def _get_doctor_working_hours(self, doctor_name: str) -> Dict[str, List[str]]:
        """
        Obtém horários de trabalho do médico
        Pode ser integrado com o modelo HorarioTrabalho do banco
        """
        # Horários padrão (pode ser customizado por médico)
        default_schedule = {
            'morning': ['08:00', '08:30', '09:00', '09:30', '10:00', '10:30', '11:00', '11:30'],
            'afternoon': ['14:00', '14:30', '15:00', '15:30', '16:00', '16:30', '17:00', '17:30']
        }
        
        # Aqui você pode consultar o banco de dados
        # from rag_agent.models import Medico, HorarioTrabalho
        # medico = Medico.objects.filter(nome__icontains=doctor_name).first()
        # if medico:
        #     horarios = medico.horarios_trabalho.all()
        #     return self._convert_db_schedule_to_slots(horarios)
        
        return default_schedule
    
    def _calculate_available_slots(self, date: datetime, events: List[Dict], working_hours: Dict) -> List[str]:
        """
        Calcula horários disponíveis baseado nos eventos ocupados
        """
        all_slots = working_hours['morning'] + working_hours['afternoon']
        occupied_slots = []
        
        # Processar eventos ocupados
        for event in events:
            start_time = event.get('start', {}).get('dateTime', '')
            if start_time:
                try:
                    event_datetime = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    event_time = event_datetime.strftime('%H:%M')
                    occupied_slots.append(event_time)
                except Exception as e:
                    logger.warning(f"Erro ao processar horário do evento: {e}")
        
        # Filtrar horários disponíveis
        available_slots = [slot for slot in all_slots if slot not in occupied_slots]
        
        # Remover horários passados se for hoje
        if date.date() == timezone.now().date():
            current_time = timezone.now().strftime('%H:%M')
            available_slots = [slot for slot in available_slots if slot > current_time]
        
        return available_slots
    
    def _is_same_day(self, date: datetime, event_datetime_str: str) -> bool:
        """Verifica se evento é no mesmo dia"""
        if not event_datetime_str:
            return False
        
        try:
            event_date = datetime.fromisoformat(event_datetime_str.replace('Z', '+00:00'))
            return date.date() == event_date.date()
        except:
            return False
    
    def _get_weekday_name(self, weekday: int) -> str:
        """Converte número do dia para nome"""
        days = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
        return days[weekday]
    
    def _get_mock_availability(self, doctor_name: str, days_ahead: int) -> Dict[str, Any]:
        """
        Retorna disponibilidade simulada baseada em calendário único
        Simula eventos como "Dr. João - Consulta" para demonstrar o conceito
        """
        logger.info(f"Usando disponibilidade simulada para {doctor_name} (calendário único)")
        
        availability = {
            'doctor_name': doctor_name,
            'period': f"Próximos {days_ahead} dias",
            'days': [],
            'mock_data': True,
            'source': 'calendario_unico_simulado'
        }
        
        # Simular alguns eventos ocupados para demonstrar funcionalidade
        mock_occupied_events = self._generate_mock_events(doctor_name, days_ahead)
        
        # Gerar horários disponíveis baseado nos eventos simulados
        now = timezone.now()
        for day_offset in range(days_ahead):
            current_date = now + timedelta(days=day_offset + 1)  # Começar amanhã
            
            # Pular fins de semana
            if current_date.weekday() >= 5:
                continue
            
            # Horários padrão de trabalho
            all_slots = ['08:00', '08:30', '09:00', '09:30', '10:00', '10:30', '11:00', '11:30',
                        '14:00', '14:30', '15:00', '15:30', '16:00', '16:30', '17:00', '17:30']
            
            # Simular alguns horários ocupados para este médico neste dia
            occupied_slots = mock_occupied_events.get(current_date.strftime('%d/%m/%Y'), [])
            
            # Calcular horários disponíveis
            available_times = [slot for slot in all_slots if slot not in occupied_slots]
            
            if available_times:
                availability['days'].append({
                    'date': current_date.strftime('%d/%m/%Y'),
                    'weekday': self._get_weekday_name(current_date.weekday()),
                    'available_times': available_times,
                    'occupied_times': occupied_slots  # Para demonstração
                })
        
        return availability
    
    def _generate_mock_events(self, doctor_name: str, days_ahead: int) -> Dict[str, List[str]]:
        """
        Gera eventos simulados para demonstrar calendário único
        """
        mock_events = {}
        now = timezone.now()
        
        # Simular alguns agendamentos para cada médico
        for day_offset in range(days_ahead):
            current_date = now + timedelta(days=day_offset + 1)
            date_str = current_date.strftime('%d/%m/%Y')
            
            # Pular fins de semana
            if current_date.weekday() >= 5:
                continue
            
            # Simular eventos ocupados baseado no médico
            occupied = []
            if 'joão' in doctor_name.lower():
                # Dr. João tem mais agendamentos
                occupied = ['09:00', '14:30', '16:00']
            elif 'maria' in doctor_name.lower():
                # Dra. Maria tem menos agendamentos
                occupied = ['10:00', '15:30']
            else:
                # Outros médicos
                occupied = ['08:30', '14:00']
            
            mock_events[date_str] = occupied
        
        return mock_events
    
    def get_all_doctors_availability(self, days_ahead: int = 7) -> Dict[str, Any]:
        """
        Obtém disponibilidade de todos os médicos
        """
        # Buscar médicos do banco de dados
        try:
            from rag_agent.models import Medico
            medicos = Medico.objects.all()
            
            all_availability = {
                'period': f"Próximos {days_ahead} dias",
                'doctors': []
            }
            
            for medico in medicos:
                doctor_availability = self.get_doctor_availability(medico.nome, days_ahead)
                all_availability['doctors'].append(doctor_availability)
            
            return all_availability
            
        except Exception as e:
            logger.error(f"Erro ao buscar disponibilidade de todos os médicos: {e}")
            return {'error': 'Erro ao consultar disponibilidade'}
    
    def test_connection(self) -> bool:
        """
        Testa conexão com Google Calendar API e acesso ao calendário da clínica
        """
        if not self.enabled or not self.service:
            return False
        
        try:
            # Testar acesso ao calendário específico da clínica
            clinic_calendar_id = self._get_clinic_calendar_id()
            
            # Tentar buscar eventos do calendário da clínica
            now = timezone.now()
            events_result = self.service.events().list(
                calendarId=clinic_calendar_id,
                timeMin=now.isoformat(),
                maxResults=1,
                singleEvents=True
            ).execute()
            
            logger.info(f"Google Calendar conectado. Acesso ao calendário da clínica ({clinic_calendar_id}) confirmado.")
            return True
            
        except HttpError as e:
            if e.resp.status == 404:
                logger.error(f"Calendário da clínica não encontrado: {clinic_calendar_id}")
            elif e.resp.status == 403:
                logger.error(f"Sem permissão para acessar calendário: {clinic_calendar_id}")
            else:
                logger.error(f"Erro HTTP na API do Google Calendar: {e}")
            return False
        except Exception as e:
            logger.error(f"Erro ao testar conexão: {e}")
            return False


# Instância global do serviço
google_calendar_service = GoogleCalendarService()
