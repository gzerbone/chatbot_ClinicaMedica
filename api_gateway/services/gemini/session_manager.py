"""
Session Manager - Gerenciamento de Sessões de Conversa

Responsável por:
- Criar e recuperar sessões
- Atualizar dados da sessão
- Sincronizar com cache e banco de dados
- Gerenciar histórico de conversas
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

# Termos usados para reconhecer que o usuário está confirmando o médico por pronome
PRONOUN_DOCTOR_TERMS = {
    'ele', 'ela', 'ele mesmo', 'ela mesma', 'com ele', 'com ela', 'com ele mesmo', 'com ela mesma',
    'ele sim', 'ela sim', 'com o mesmo', 'com a mesma', 'o mesmo', 'a mesma',
    'nele', 'nela', 'ele msm', 'ela msm', 'com ele msm', 'com ela msm'
}

# Termos complementares (variações comuns na mensagem)
PRONOUN_DOCTOR_MESSAGE_TERMS = PRONOUN_DOCTOR_TERMS.union(
    {f"quero {term}" for term in PRONOUN_DOCTOR_TERMS}.union(
        {f"prefiro {term}" for term in PRONOUN_DOCTOR_TERMS},
        {f"gostaria {term}" for term in PRONOUN_DOCTOR_TERMS}
    )
)

# Padrões regex para capturar pronome isolado na frase
PRONOUN_DOCTOR_REGEX = [r'\bele\b', r'\bela\b']

from django.core.cache import cache
from django.utils import timezone

from ..token_monitor import token_monitor

logger = logging.getLogger(__name__)


def resolve_doctor_reference(doctor_reference: Optional[str], message_lower: str, session: Dict) -> Optional[str]:
    """
    Resolve referência ao médico utilizando contexto atual (pronome, sugestões anteriores).
    
    Função utilitária compartilhada entre SessionManager e SmartSchedulingService.
    
    Args:
        doctor_reference: Referência ao médico extraída da mensagem
        message_lower: Mensagem original em lowercase
        session: Dados da sessão atual
        
    Returns:
        Nome do médico resolvido ou None
    """
    reference_clean = (doctor_reference or '').strip()
    reference_lower = reference_clean.lower()

    # Função auxiliar para normalizar expressões removendo prefixos como "dr." ou "com"
    def _normalize_reference(text: str) -> str:
        normalized = text.strip().lower()
        # Remover prefixos comuns
        normalized = re.sub(r'^(dr\.?|dra\.?|doutor(a)?)\s+', '', normalized)
        if normalized.startswith('com '):
            normalized = normalized[4:]
        return normalized.strip()

    normalized_reference = _normalize_reference(reference_lower) if reference_lower else ''

    # Determinar se a referência (ou a mensagem) indica um pronome
    pronoun_detected = False
    if normalized_reference in PRONOUN_DOCTOR_TERMS or reference_lower in PRONOUN_DOCTOR_TERMS:
        pronoun_detected = True
    elif normalized_reference and any(term in normalized_reference for term in PRONOUN_DOCTOR_TERMS):
        pronoun_detected = True
    elif reference_lower and any(term in reference_lower for term in PRONOUN_DOCTOR_TERMS):
        pronoun_detected = True
    elif message_lower:
        simplified_message = message_lower.replace('  ', ' ')
        if any(term in simplified_message for term in PRONOUN_DOCTOR_MESSAGE_TERMS):
            pronoun_detected = True
        else:
            for regex_pattern in PRONOUN_DOCTOR_REGEX:
                if re.search(regex_pattern, simplified_message):
                    pronoun_detected = True
                    break

    if pronoun_detected:
        # Prioridade: médico já confirmado > último sugerido > primeira sugestão disponível
        candidate = session.get('selected_doctor') or session.get('last_suggested_doctor')
        if not candidate:
            suggested_list = session.get('last_suggested_doctors') or []
            if suggested_list:
                candidate = suggested_list[0]
        return candidate

    # Caso não seja pronome, retornar referência original normalizada (com capitalização)
    if reference_clean:
        if reference_clean.lower().startswith('com '):
            reference_clean = reference_clean[4:]
        return reference_clean.strip().title()

    # Nenhuma referência encontrada
    return None


class SessionManager:
    """Gerenciamento de sessões de conversa"""
    
    def get_or_create_session(self, phone_number: str) -> Dict[str, Any]:
        """
        Obtém ou cria sessão da conversa - carrega do banco se necessário
        
        Args:
            phone_number: Número de telefone do usuário
            
        Returns:
            Dict com dados da sessão
        """
        cache_key = f"gemini_session_{phone_number}"
        session = cache.get(cache_key)
        
        if not session:
            # Tentar carregar do banco de dados
            try:
                from api_gateway.models import ConversationSession
                db_session = ConversationSession.objects.filter(phone_number=phone_number).first()
                
                if db_session:
                    # Carregar dados do banco para o cache
                    session = {
                        'phone_number': phone_number,
                        'current_state': db_session.current_state,
                        'previous_state': db_session.previous_state,
                        'patient_name': db_session.patient_name,
                        'pending_name': db_session.pending_name,
                        'name_confirmed': db_session.name_confirmed,
                        'selected_doctor': db_session.selected_doctor,
                        'selected_specialty': db_session.selected_specialty,
                        'preferred_date': db_session.preferred_date.isoformat() if db_session.preferred_date else None,
                        'preferred_time': db_session.preferred_time.isoformat() if db_session.preferred_time else None,
                        'insurance_type': db_session.insurance_type,
                        'created_at': db_session.created_at.isoformat(),
                        'last_activity': timezone.now().isoformat(),
                        'has_greeted': getattr(db_session, 'name_confirmed', False)
                    }
                    logger.info(f"📥 Sessão carregada do banco - Nome: {db_session.patient_name}, Médico: {db_session.selected_doctor}")
                else:
                    # Criar nova sessão
                    session = self._create_empty_session(phone_number)
                    logger.info(f"🆕 Nova sessão criada para {phone_number}")
            except Exception as e:
                logger.error(f"Erro ao carregar sessão do banco: {e}")
                # Fallback: criar sessão vazia
                session = self._create_empty_session(phone_number)
            
            cache.set(cache_key, session, token_monitor.get_cache_timeout())
        
        session.setdefault('has_greeted', False)
        return session
    
    def _create_empty_session(self, phone_number: str) -> Dict[str, Any]:
        """Cria uma sessão vazia"""
        session = {
            'phone_number': phone_number,
            'current_state': 'idle',
            'previous_state': None,
            'patient_name': None,
            'pending_name': None,
            'name_confirmed': False,
            'selected_doctor': None,
            'selected_specialty': None,
            'preferred_date': None,
            'preferred_time': None,
            'insurance_type': None,
            'created_at': timezone.now().isoformat(),
            'last_activity': timezone.now().isoformat(),
            'has_greeted': False
        }
        return session
    
    def update_session(self, phone_number: str, session: Dict, 
                      analysis_result: Dict, response_result: Dict):
        """
        Atualiza sessão com base na análise e resposta
        
        Args:
            phone_number: Número de telefone
            session: Sessão atual
            analysis_result: Resultado da análise de intenção
            response_result: Resultado da geração de resposta
        """
        try:
            # Garantir flags padrão
            session.setdefault('has_greeted', False)
            session.setdefault('pending_name', None)
            session.setdefault('name_confirmed', False)

            # Atualizar estado (não sobrescrever se já estiver confirmando ou respondendo dúvidas)
            # Se está respondendo dúvidas (answering_questions), manter esse estado
            # IMPORTANTE: Se next_state estiver definido e não for None, atualizar o estado
            next_state = analysis_result.get('next_state')
            if next_state and session.get('current_state') not in ['confirming', 'answering_questions']:
                session['current_state'] = next_state
                logger.debug(f"🔄 Estado atualizado no cache: {next_state}")
            session['last_activity'] = timezone.now().isoformat()
            
            # CORREÇÃO: Armazenar informações da resposta gerada
            if response_result:
                session['last_response'] = response_result.get('response', '')
                session['last_intent'] = response_result.get('intent', analysis_result.get('intent', ''))
                session['last_confidence'] = response_result.get('confidence', analysis_result.get('confidence', 0.0))
                
                # Marcar que a saudação/apresentação já foi enviada após a primeira resposta
                if not session.get('has_greeted'):
                    session['has_greeted'] = True
                
                # Armazenar link de handoff se disponível
                if response_result.get('handoff_link'):
                    session['handoff_link'] = response_result['handoff_link']

                # Guardar médicos sugeridos para interpretar confirmações por pronome
                suggested_doctors = response_result.get('suggested_doctors') or []
                primary_suggested_doctor = response_result.get('primary_suggested_doctor')
                
                if suggested_doctors:
                    # Normaliza nomes removendo espaços extras
                    normalized_suggestions = [doctor.strip() for doctor in suggested_doctors if isinstance(doctor, str) and doctor.strip()]
                    if normalized_suggestions:
                        session['last_suggested_doctors'] = normalized_suggestions
                        logger.info(f"📝 Lista de médicos sugeridos registrada: {normalized_suggestions}")
                        if not primary_suggested_doctor:
                            primary_suggested_doctor = normalized_suggestions[0]
                
                if primary_suggested_doctor and isinstance(primary_suggested_doctor, str):
                    session['last_suggested_doctor'] = primary_suggested_doctor.strip()
                    logger.info(f"🗂️ Último médico sugerido registrado:\n {session['last_suggested_doctor']}")
            
            # Atualizar entidades extraídas
            entities = analysis_result['entities']

            # Normalizar referência ao médico (pronome -> nome do médico sugerido/anterior)
            raw_message = analysis_result.get('raw_message', '') or ''
            message_lower = raw_message.lower() if isinstance(raw_message, str) else ''
            resolved_doctor = self._resolve_doctor_reference(
                entities.get('medico'),
                message_lower,
                session
            )
            if resolved_doctor:
                entities['medico'] = resolved_doctor
                logger.info(f"🤝 Médico confirmado a partir do contexto/pronome: {resolved_doctor}")
            elif entities.get('medico') and isinstance(entities['medico'], str):
                # Garantir que nomes venham sem espaços extras
                entities['medico'] = entities['medico'].strip()
            
            # Log das entidades extraídas para debug
            if entities:
                logger.info(f"🔍 Entidades extraídas: {entities}")
            
            # Atualizar nome do paciente
            if entities.get('nome_paciente') and entities['nome_paciente'] != 'null':
                nome_extraido = entities['nome_paciente'].strip()
                session['patient_name'] = nome_extraido
                session['pending_name'] = None
                session['name_confirmed'] = True
            
            # Atualizar médico selecionado (VALIDAR ANTES DE SALVAR)
            if entities.get('medico') and entities['medico'] != 'null':
                medico_extraido = entities['medico']
                # Validar se médico existe no banco antes de salvar
                medico_validado = self._validate_doctor(medico_extraido, session.get('selected_specialty'))
                if medico_validado:
                    session['selected_doctor'] = medico_validado
                    logger.info(f"✅ Médico atualizado e validado: {medico_validado}")
                else:
                    # Médico inválido - limpar se já estava salvo
                    if session.get('selected_doctor'):
                        logger.warning(f"⚠️ Médico inválido detectado: '{medico_extraido}'. Limpando médico salvo anteriormente.")
                        session['selected_doctor'] = None
                    else:
                        logger.warning(f"⚠️ Médico inválido extraído: '{medico_extraido}'. Não será salvo.")
            
            # Atualizar especialidade selecionada (VALIDAR ANTES DE SALVAR)
            if entities.get('especialidade') and entities['especialidade'] != 'null':
                especialidade_extraida = entities['especialidade']
                # Validar se especialidade existe no banco antes de salvar
                especialidade_validada = self._validate_specialty(especialidade_extraida)
                if especialidade_validada:
                    session['selected_specialty'] = especialidade_validada
                    logger.info(f"✅ Especialidade atualizada e validada: {especialidade_validada}")
                else:
                    # Especialidade inválida - limpar se já estava salva
                    if session.get('selected_specialty'):
                        logger.warning(f"⚠️ Especialidade inválida detectada: '{especialidade_extraida}'. Limpando especialidade salva anteriormente.")
                        session['selected_specialty'] = None
                    else:
                        logger.warning(f"⚠️ Especialidade inválida extraída: '{especialidade_extraida}'. Não será salva.")
            
            # Atualizar data preferida (SOMENTE se já tiver especialidade E médico)
            if entities.get('data') and entities['data'] != 'null':
                # Verificar se especialidade E médico já foram selecionados
                if session.get('selected_specialty') and session.get('selected_doctor'):
                    processed_date = self._process_date(entities['data'])
                    if processed_date:
                        session['preferred_date'] = processed_date
                        logger.info(f"✅ Data atualizada (normalizada): {processed_date}")
                    else:
                        # Data não pôde ser normalizada - marcar para informar ao usuário
                        session['invalid_date_provided'] = entities['data']
                        logger.warning(f"⚠️ Data não pôde ser normalizada: '{entities['data']}' - será solicitada novamente")
                else:
                    logger.warning(f"⚠️ Data ignorada: '{entities['data']}' - Especialidade e médico devem ser selecionados primeiro")
            
            # Atualizar horário preferido (SOMENTE se já tiver especialidade E médico)
            if entities.get('horario') and entities['horario'] != 'null':
                # Verificar se especialidade E médico já foram selecionados
                if session.get('selected_specialty') and session.get('selected_doctor'):
                    session['preferred_time'] = self._process_time(entities['horario'])
                    logger.info(f"✅ Horário atualizado (especialidade e médico já selecionados)")
                else:
                    logger.warning(f"⚠️ Horário ignorado: '{entities['horario']}' - Especialidade e médico devem ser selecionados primeiro")
            
            # ═══════════════════════════════════════════════════════════════════════════════
            # LOG DO STATUS DAS INFORMAÇÕES COLETADAS
            # ═══════════════════════════════════════════════════════════════════════════════
            # Mostra quais informações já foram coletadas para facilitar debug
            # ═══════════════════════════════════════════════════════════════════════════════
            
            info_status = {
                'nome': bool(session.get('patient_name')),
                'medico': bool(session.get('selected_doctor')),
                'especialidade': bool(session.get('selected_specialty')),
                'data': bool(session.get('preferred_date')),
                'horario': bool(session.get('preferred_time'))
            }
            logger.info(f"📋 Status das informações: {info_status}")
            
            # ═══════════════════════════════════════════════════════════════════════════════
            # CORREÇÃO DO ESTADO: Ajustar estado baseado nas informações coletadas
            # ═══════════════════════════════════════════════════════════════════════════════
            # 1. Se tem médico mas NÃO tem especialidade, deve estar em selecting_specialty
            # 2. Se tem especialidade mas NÃO tem médico, deve estar em selecting_doctor
            # 3. Se tem ambos, deve estar em choosing_schedule
            # ═══════════════════════════════════════════════════════════════════════════════
            
            has_doctor = bool(session.get('selected_doctor'))
            has_specialty = bool(session.get('selected_specialty'))
            
            if has_doctor and not has_specialty:
                # Tem médico mas falta especialidade - deve perguntar especialidade
                if session.get('current_state') != 'selecting_specialty':
                    session['current_state'] = 'selecting_specialty'
                    logger.info(f"🔄 Estado corrigido: {session.get('current_state')} → selecting_specialty (tem médico mas falta especialidade)")
            elif has_specialty and not has_doctor:
                # Tem especialidade mas falta médico - deve perguntar médico
                if session.get('current_state') != 'selecting_doctor':
                    session['current_state'] = 'selecting_doctor'
                    logger.info(f"🔄 Estado corrigido: {session.get('current_state')} → selecting_doctor (tem especialidade mas falta médico)")
            elif has_doctor and has_specialty:
                # Tem ambos - pode perguntar data/horário
                if session.get('current_state') in ['selecting_doctor', 'selecting_specialty']:
                    session['current_state'] = 'choosing_schedule'
                    logger.info(f"🔄 Estado avançado automaticamente: {session.get('current_state')} → choosing_schedule (médico e especialidade já selecionados)")
            
            # ═══════════════════════════════════════════════════════════════════════════════
            # NOTA IMPORTANTE: ESTADO 'confirming' NÃO É DEFINIDO AQUI
            # ═══════════════════════════════════════════════════════════════════════════════
            # O estado 'confirming' deve ser definido APENAS pelo core_service.py
            # quando o handoff for efetivamente gerado (primeira confirmação do usuário).
            # 
            # ❌ ANTES: SessionManager mudava automaticamente para 'confirming' quando
            #          todas as informações estavam completas (causava bug)
            # 
            # ✅ AGORA: core_service controla quando mudar para 'confirming'
            #          (somente após gerar o handoff com sucesso)
            # 
            # Razão: Evitar que o sistema trate a PRIMEIRA confirmação como duplicada
            # ═══════════════════════════════════════════════════════════════════════════════
            
            # Salvar sessão no cache
            cache_key = f"gemini_session_{phone_number}"
            cache.set(cache_key, session, token_monitor.get_cache_timeout())
            
            # Log do estado final da sessão ANTES de sincronizar
            logger.info(f"📋 Sessão atualizada - Estado: {session['current_state']}, Nome: {session.get('patient_name')}, Médico: {session.get('selected_doctor')}")
            
            # Sincronizar com banco de dados
            # IMPORTANTE: O estado já foi atualizado no cache (linhas 201-202 e 337-361)
            # Agora sincronizamos com o banco para persistir
            self.sync_to_database(phone_number, session)
        except Exception as e:
            logger.error(f"Erro ao atualizar sessão: {e}")
    
    def _process_date(self, date_str: str) -> Optional[str]:
        """Processa e normaliza string de data"""
        try:
            # Primeiro, tentar extrair data de formatos como "Sexta (10/10/2025)"
            date_pattern = r'\((\d{1,2}/\d{1,2}/\d{4})\)'
            match = re.search(date_pattern, date_str)
            if match:
                extracted_date = match.group(1)
                logger.info(f"🔍 Data extraída do padrão: {extracted_date}")
                date_str = extracted_date
            
            # Normalizar data
            from ..conversation_service import conversation_service
            normalized_date = conversation_service.normalize_date_for_database(date_str)
            
            # Verificar se a data foi normalizada corretamente (formato YYYY-MM-DD)
            if normalized_date and re.match(r'^\d{4}-\d{2}-\d{2}$', normalized_date):
                logger.info(f"✅ Data atualizada (normalizada): {normalized_date}")
                return normalized_date
            else:
                # Se não conseguir normalizar, NÃO salvar e retornar None
                logger.warning(f"⚠️ Data não pôde ser normalizada: '{date_str}' - formato inválido")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao processar data: {e}")
            logger.warning(f"⚠️ Data não pôde ser normalizada: '{date_str}' - erro: {e}")
            return None
    
    def _process_time(self, time_str: str) -> Optional[str]:
        """Processa e normaliza string de horário"""
        try:
            # Tentar diferentes formatos de horário
            from datetime import datetime
            time_formats = ['%H:%M', '%H:%M:%S', '%I:%M %p', '%I:%M:%S %p']
            parsed_time = None
            
            for fmt in time_formats:
                try:
                    parsed_time = datetime.strptime(time_str, fmt).time()
                    break
                except ValueError:
                    continue
            
            if parsed_time:
                return parsed_time.isoformat()
            else:
                # Se não conseguir fazer parse, salvar como string
                return time_str
                
        except Exception as e:
            logger.error(f"Erro ao processar horário: {e}")
            return time_str
    
    def _validate_specialty(self, specialty_name: str) -> Optional[str]:
        """
        Valida se especialidade existe no banco de dados
        
        Args:
            specialty_name: Nome da especialidade a validar
            
        Returns:
            Nome da especialidade validada (normalizado) ou None se inválida
        """
        try:
            from rag_agent.models import Especialidade
            
            if not specialty_name:
                return None
            
            specialty_name_lower = specialty_name.lower().strip()
            
            # Busca exata (case-insensitive)
            especialidade = Especialidade.objects.filter(
                nome__iexact=specialty_name_lower,
                ativa=True
            ).first()
            
            if especialidade:
                return especialidade.nome
            
            # Busca parcial (contém)
            especialidade = Especialidade.objects.filter(
                nome__icontains=specialty_name_lower,
                ativa=True
            ).first()
            
            if especialidade:
                return especialidade.nome
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao validar especialidade '{specialty_name}': {e}")
            return None
    
    def _validate_doctor(self, doctor_name: str, specialty: Optional[str] = None) -> Optional[str]:
        """
        Valida se médico existe no banco de dados
        
        Args:
            doctor_name: Nome do médico a validar
            specialty: Especialidade (opcional) para validar se médico tem essa especialidade
            
        Returns:
            Nome do médico validado ou None se inválido
        """
        try:
            from rag_agent.models import Especialidade, Medico
            
            if not doctor_name:
                return None
            
            doctor_name_lower = doctor_name.lower().strip()
            
            # Buscar médico diretamente no banco (mais confiável que via serializer)
            medicos = Medico.objects.prefetch_related('especialidades').all()
            
            # Buscar médico por nome (busca flexível)
            for medico in medicos:
                medico_name = medico.nome
                medico_name_lower = medico_name.lower()
                
                # Busca exata ou parcial
                if (doctor_name_lower in medico_name_lower or 
                    medico_name_lower in doctor_name_lower):
                    
                    # Se especialidade foi fornecida, validar se médico tem essa especialidade
                    if specialty:
                        # Buscar especialidades do médico diretamente do banco
                        especialidades_medico = medico.especialidades.filter(ativa=True)
                        especialidades_nomes = [esp.nome.lower() for esp in especialidades_medico]
                        specialty_lower = specialty.lower()
                        
                        if specialty_lower not in especialidades_nomes:
                            logger.warning(f"⚠️ Médico '{medico_name}' não tem especialidade '{specialty}'. Especialidades do médico: {[esp.nome for esp in especialidades_medico]}")
                            continue
                    
                    logger.info(f"✅ Médico '{medico_name}' validado com sucesso" + (f" para especialidade '{specialty}'" if specialty else ""))
                    return medico_name
            
            logger.warning(f"⚠️ Médico '{doctor_name}' não encontrado no banco de dados")
            return None
            
        except Exception as e:
            logger.error(f"Erro ao validar médico '{doctor_name}': {e}")
            return None
    
    def sync_to_database(self, phone_number: str, session: Dict):
        """
        Sincroniza sessão do cache com o banco de dados
        
        Args:
            phone_number: Número de telefone
            session: Dados da sessão
        """
        try:
            from api_gateway.models import ConversationSession

            from ..conversation_service import conversation_service

            # Normalizar data antes de salvar
            normalized_date = conversation_service.normalize_date_for_database(session.get('preferred_date'))

            # Obter ou criar sessão no banco
            db_session, created = ConversationSession.objects.get_or_create(
                phone_number=phone_number,
                defaults={
                    'current_state': session.get('current_state', 'idle'),
                    'previous_state': session.get('previous_state'),
                    'patient_name': session.get('patient_name'),
                    'pending_name': session.get('pending_name'),
                    'name_confirmed': session.get('name_confirmed', False),
                    'insurance_type': session.get('insurance_type'),
                    'selected_doctor': session.get('selected_doctor'),
                    'selected_specialty': session.get('selected_specialty'),
                    'preferred_date': normalized_date,
                    'preferred_time': session.get('preferred_time'),
                    'additional_notes': session.get('additional_notes'),
                    'created_at': timezone.now(),
                    'updated_at': timezone.now()
                }
            )
            
            if not created:
                # Atualizar sessão existente
                current_state_from_session = session.get('current_state', 'idle')
                # Log para debug: verificar se o estado está sendo atualizado
                if db_session.current_state != current_state_from_session:
                    logger.info(f"🔄 Atualizando estado no banco: {db_session.current_state} → {current_state_from_session}")
                db_session.current_state = current_state_from_session
                # IMPORTANTE: Preservar previous_state se já existir no banco e não estiver na sessão em memória
                # Isso evita que o previous_state seja limpo incorretamente quando pause_for_question já salvou
                previous_state_from_session = session.get('previous_state')
                if previous_state_from_session is not None:
                    # Se a sessão em memória tem previous_state, usar esse valor
                    db_session.previous_state = previous_state_from_session
                # Se previous_state não está na sessão em memória (None), manter o valor do banco
                # Isso preserva o previous_state salvo pelo pause_for_question mesmo se a sessão em memória não foi atualizada
                elif db_session.previous_state:
                    # Manter o previous_state do banco se ele já existir
                    pass  # Não sobrescrever
                else:
                    # Se não tem no banco nem na sessão, pode ser None
                    db_session.previous_state = None
                # Garantir que o nome completo seja salvo (sem truncamento)
                patient_name = session.get('patient_name')
                if patient_name:
                    patient_name = patient_name.strip()
                db_session.patient_name = patient_name
                # Garantir que o pending_name completo seja salvo (sem truncamento)
                pending_name = session.get('pending_name')
                if pending_name:
                    pending_name = pending_name.strip()
                db_session.pending_name = pending_name
                db_session.name_confirmed = session.get('name_confirmed', False)
                db_session.insurance_type = session.get('insurance_type')
                db_session.selected_doctor = session.get('selected_doctor')
                db_session.selected_specialty = session.get('selected_specialty')
                db_session.preferred_date = normalized_date
                db_session.preferred_time = session.get('preferred_time')
                db_session.additional_notes = session.get('additional_notes')
                db_session.updated_at = timezone.now()
                db_session.save()
            
            logger.info(f"💾 Sessão sincronizada com banco - ID: {db_session.id}, Estado: {db_session.current_state}, Nome: {db_session.patient_name}, Data: {normalized_date}")
            
        except Exception as e:
            logger.error(f"Erro ao sincronizar sessão com banco: {e}")
    
    def get_conversation_history(self, phone_number: str, limit: int = 10) -> List[Dict]:
        """
        Obtém histórico da conversa
        
        Args:
            phone_number: Número de telefone
            limit: Limite de mensagens a retornar
            
        Returns:
            Lista de mensagens do histórico
        """
        try:
            from ..conversation_service import conversation_service
            return conversation_service.get_conversation_history(phone_number, limit)
        except:
            return []
    
    def save_messages(self, phone_number: str, user_message: str, bot_response: str, 
                     analysis_result: Dict = None):
        """
        Salva mensagens no histórico com entidades extraídas
        
        Args:
            phone_number: Número de telefone
            user_message: Mensagem do usuário
            bot_response: Resposta do bot
            analysis_result: Resultado da análise (opcional)
        """
        try:
            from ..conversation_service import conversation_service

            # Preparar entidades para salvar no banco
            entities_to_save = {}
            if analysis_result and analysis_result.get('entities'):
                entities_to_save = analysis_result['entities']
            
            # Salvar mensagem do usuário com entidades
            conversation_service.add_message(
                phone_number, user_message, 'user',
                analysis_result.get('intent', 'user_message') if analysis_result else 'user_message',
                analysis_result.get('confidence', 1.0) if analysis_result else 1.0,
                entities_to_save
            )
            
            # Salvar resposta do bot
            conversation_service.add_message(
                phone_number, bot_response, 'bot',
                'bot_response', 1.0, {}
            )
            
        except Exception as e:
            logger.error(f"Erro ao salvar mensagens: {e}")

    def _resolve_doctor_reference(self, doctor_reference: Optional[str], message_lower: str, session: Dict) -> Optional[str]:
        """
        Resolve referência ao médico (wrapper para a função utilitária).
        DEPRECATED: Use resolve_doctor_reference() diretamente do módulo.
        """
        return resolve_doctor_reference(doctor_reference, message_lower, session)


