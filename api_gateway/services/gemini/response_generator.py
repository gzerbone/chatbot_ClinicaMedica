"""
Response Generator - Geração de Respostas Contextualizadas

Responsável por:
- Gerar respostas usando Gemini
- Construir prompts contextualizados
- Formatar respostas para o usuário
"""

import logging
from typing import Any, Dict, List, Tuple

import google.generativeai as genai
from django.conf import settings

from ..token_monitor import token_monitor

logger = logging.getLogger(__name__)


class ResponseGenerator:
    """Geração de respostas contextualizadas"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'GEMINI_API_KEY', '')
        self.model = None
        
        # Configurações otimizadas para maior inteligência e qualidade de resposta
        # temperature: 0.8-0.9 = mais criativo e natural, 0.3-0.5 = mais determinístico
        # top_p: 0.9-0.95 = maior diversidade de respostas
        # top_k: 40-50 = considera mais opções de tokens
        # max_output_tokens: 1536-2048 = permite respostas mais completas
        self.generation_config = {
            "temperature": 0.8,  # Aumentado de 0.7 para respostas mais naturais
            "top_p": 0.9,        # Aumentado de 0.8 para maior diversidade
            "top_k": 50,         # Aumentado de 40 para considerar mais opções
            "max_output_tokens": 1536,  # Aumentado de 1024 para respostas mais completas
        }
        
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                model_name = getattr(settings, 'GEMINI_MODEL', 'gemini-2.5-flash-lite')
                self.model = genai.GenerativeModel(model_name)
                
                # Aplicar configurações de modo econômico se necessário
                self._apply_economy_config()
            except Exception as e:
                logger.error(f"Erro ao configurar Gemini no ResponseGenerator: {e}")
    
    def _apply_economy_config(self):
        """Aplica configurações de modo econômico se necessário"""
        try:
            if token_monitor.is_economy_mode_active():
                economy_config = token_monitor.get_economy_config()
                if economy_config:
                    self.generation_config.update(economy_config)
                    logger.info("💰 Configurações de modo econômico aplicadas")
        except Exception as e:
            logger.error(f"Erro ao aplicar configurações de modo econômico: {e}")
    
    def generate_response(self, message: str, analysis_result: Dict,
                         session: Dict, conversation_history: List,
                         clinic_data: Dict) -> Dict[str, Any]:
        """
        Gera resposta usando Gemini baseada na análise e contexto
        
        Args:
            message: Mensagem do usuário
            analysis_result: Resultado da análise de intenção
            session: Sessão atual
            conversation_history: Histórico de conversas
            clinic_data: Dados da clínica
            
        Returns:
            Dict com response, intent, confidence
        """
        try:
            # Construir prompt de resposta (retorna também metadados do contexto)
            response_prompt, prompt_metadata = self._build_response_prompt(
                message, analysis_result, session, conversation_history, clinic_data
            )
            
            # Gerar resposta com Gemini
            response = self.model.generate_content(
                response_prompt,
                generation_config=self.generation_config
            )
            
            # Log do uso de tokens para resposta
            token_monitor.log_token_usage("RESPOSTA", response_prompt, response.text, session.get('phone_number'))
            
            metadata = prompt_metadata or {}
            
            # Preparar resposta base
            response_text = response.text.strip()
            
            # Adicionar mensagem de retomada APENAS se:
            # 1. Está em answering_questions
            # 2. Há previous_state (agendamento pausado)
            # 3. A intenção NÃO é agendar_consulta (ou seja, está realmente em dúvidas, não fornecendo informações)
            # 4. Não há entidades de agendamento sendo fornecidas (nome, médico, especialidade, data, horário)
            current_state = session.get('current_state')
            previous_state = session.get('previous_state')
            intent = analysis_result.get('intent', '')
            entities = analysis_result.get('entities', {})
            
            # Verificar se há entidades de agendamento sendo fornecidas
            has_appointment_entities = any([
                entities.get('nome_paciente'),
                entities.get('medico'),
                entities.get('especialidade'),
                entities.get('data'),
                entities.get('horario')
            ])
            
            # Só mostrar mensagem de retomada se está em dúvidas (não fornecendo informações de agendamento)
            if (current_state == 'answering_questions' and 
                previous_state and
                intent not in ['agendar_consulta', 'confirmar_agendamento', 'selecionar_especialidade', 'confirming_name'] and
                not has_appointment_entities):
                response_text += "\n\nℹ️ Para voltar ao agendamento, diga 'continuar', 'retomar' ou 'voltar'."
            
            return {
                'response': response_text,
                'intent': analysis_result['intent'],
                'confidence': analysis_result['confidence'],
                # Enviar lista de médicos sugeridos para que outros módulos possam usar o contexto
                'suggested_doctors': metadata.get('suggested_doctors', []),
                'primary_suggested_doctor': metadata.get('primary_suggested_doctor')
            }
            
        except Exception as e:
            logger.error(f"Erro na geração de resposta com Gemini: {e}")
            return self._get_fallback_response(message)
    
    def _build_response_prompt(self, message: str, analysis_result: Dict,
                             session: Dict, conversation_history: List,
                             clinic_data: Dict) -> Tuple[str, Dict[str, Any]]:
        """Constrói prompt para geração de resposta com contexto otimizado.
        Retorna o prompt e um dicionário de metadados (ex: médicos sugeridos).
        """
        intent = analysis_result['intent']
        entities = analysis_result.get('entities', {})
        
        # Informações da clínica
        clinic_info = clinic_data.get('clinica_info', {})
        medicos = clinic_data.get('medicos', [])
        especialidades = clinic_data.get('especialidades', [])

        prompt_metadata: Dict[str, Any] = {}
        
        
        # Informações já coletadas
        patient_name = session.get('patient_name')
        selected_doctor = session.get('selected_doctor')
        selected_specialty = session.get('selected_specialty')
        preferred_date = session.get('preferred_date')
        preferred_time = session.get('preferred_time')
        has_greeted = bool(session.get('has_greeted'))
        saudacao_status = 'Sim' if has_greeted else 'Não'
        
        # Criar lista de informações já coletadas
        collected_info = []
        if patient_name:
            collected_info.append(f"Nome do paciente: {patient_name}")
        if selected_specialty:
            collected_info.append(f"Especialidade escolhida: {selected_specialty}")
        if selected_doctor:
            collected_info.append(f"Médico escolhido: {selected_doctor}")
        if preferred_date:
            collected_info.append(f"Data preferida: {preferred_date}")
        if preferred_time:
            collected_info.append(f"Horário preferido: {preferred_time}")
        
        # collected_info_str junta todas as infos já coletadas sobre o paciente, separando cada uma por uma linha. 
        # Isso facilita mostrar para o usuário o que já foi informado até agora.
        if collected_info:
            collected_info_str = '\n'.join(collected_info)
        else:
            # Se ainda não existe nenhuma informação coletada, ele mostra a mensagem "Nenhuma informação coletada ainda."
            collected_info_str = "Nenhuma informação coletada ainda."
        
        # Obter especialidades disponíveis
        # Se já temos um médico selecionado, mostrar apenas as especialidades dele
        if selected_doctor and medicos:
            # Encontrar o médico selecionado
            doctor_specialties = []
            for medico in medicos:
                if medico.get('nome', '').lower() == selected_doctor.lower():
                    # Obter especialidades do médico
                    especialidades_medico = medico.get('especialidades_display', '')
                    if especialidades_medico:
                        # Separar especialidades (podem estar separadas por vírgula ou ponto e vírgula)
                        specialties_list_raw = especialidades_medico.replace(';', ',').split(',')
                        doctor_specialties = [s.strip() for s in specialties_list_raw if s.strip()]
                    break
            
            if doctor_specialties:
                specialties_list = ', '.join(doctor_specialties)
            else:
                # Se não encontrou especialidades do médico, usar todas
                specialties_list = ', '.join([esp.get('nome', '') for esp in especialidades[:5]]) if especialidades else 'diversas especialidades'
        else:
            # Se não tem médico selecionado, mostrar todas as especialidades
            specialties_list = ', '.join([esp.get('nome', '') for esp in especialidades[:5]]) if especialidades else 'diversas especialidades'
        
        # Obter médicos disponíveis (filtrar por especialidade se selecionada)
        medicos_list = []
        medicos_to_show = []
        selected_doctor_price = None  # Preço do médico selecionado

        # Apenas sugerir médicos quando já temos uma especialidade selecionada (evita sugestão precoce)
        if selected_specialty and medicos:
            for medico in medicos:
                especialidades_medico = medico.get('especialidades_display', '').lower()
                if selected_specialty.lower() in especialidades_medico:
                    medicos_to_show.append(medico)
                    
                    # Se este é o médico selecionado, guardar o preço
                    if selected_doctor and medico.get('nome', '').lower() == selected_doctor.lower():
                        preco = medico.get('preco_particular')
                        if preco:
                            try:
                                preco_value = float(preco)
                                selected_doctor_price = f"R$ {preco_value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                            except (ValueError, TypeError):
                                selected_doctor_price = "Preço sob consulta"
        
        if medicos_to_show:
            for medico in medicos_to_show:
                nome = medico.get('nome', '')
                especialidades_medico = medico.get('especialidades_display', '')
                preco = medico.get('preco_particular')
                
                # Formatar preço
                preco_formatted = "Preço sob consulta"
                if preco:
                    try:
                        preco_value = float(preco)
                        preco_formatted = f"R$ {preco_value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                    except (ValueError, TypeError):
                        pass
                
                medicos_list.append(f"• {nome} ({especialidades_medico}) - Consulta particular: {preco_formatted}")

            # Guardar lista de médicos sugeridos para que possamos reconhecer confirmações por pronome
            suggested_doctors = [medico.get('nome', '').strip() for medico in medicos_to_show if medico.get('nome')]
            # Filtrar strings vazias
            suggested_doctors = [doctor for doctor in suggested_doctors if doctor]
            if suggested_doctors:
                prompt_metadata['suggested_doctors'] = suggested_doctors
                prompt_metadata['primary_suggested_doctor'] = suggested_doctors[0]

        medicos_text = '\n'.join(medicos_list) if medicos_list else 'Nenhum médico cadastrado'

        # Adicionar contexto sobre filtragem
        if selected_specialty:
            medicos_text = f"'{selected_specialty}':\n{medicos_text}"
        
        # Adicionar contexto de preço do médico selecionado
        doctor_price_context = ""
        if selected_doctor and selected_doctor_price:
            doctor_price_context = f"""
VALOR DA CONSULTA COM {selected_doctor}:
- Consulta particular: {selected_doctor_price}
- Se o usuário perguntar sobre preço/valor/custo, informe este valor
"""
        
        # Obter estado atual da sessão (ANTES de usar em outros blocos)
        current_state = session.get('current_state', 'idle')
        
        # Verificar se temos informações de disponibilidade real
        scheduling_info = analysis_result.get('scheduling_info', {})
        availability_context = ""
        
        # Verificar se há informações faltantes
        missing_info = analysis_result.get('missing_info', [])
        missing_context = ""
        
        if missing_info:
            missing_names = {
                'patient_name': 'nome do paciente',
                'selected_specialty': 'especialidade médica',
                'selected_doctor': 'médico',
                'preferred_date': 'data da consulta',
                'preferred_time': 'horário da consulta'
            }
            missing_list = [missing_names.get(info, info) for info in missing_info]
            missing_context = f"""
INFORMAÇÕES AINDA NECESSÁRIAS:
- Faltam: {', '.join(missing_list)}
- ORDEM OBRIGATÓRIA: 1) nome → 2) especialidade → 3) médico → 4) data → 5) horário
- IMPORTANTE: NÃO pergunte sobre data/horário se especialidade OU médico ainda não foram selecionados
- Pergunte APENAS a próxima informação faltante seguindo a ordem obrigatória
- Se restar apenas um item (ex.: nome), solicite exatamente esse item sem reiniciar etapas anteriores
- Antes de perguntar algo novamente, confira se a sessão já marcou esse dado como coletado"""
        
        # Adicionar validação de Especialidade extraída (sempre definir)
        specialty_validation_context = ""
        especialidade_extraida = entities.get('especialidade')
        
        if especialidade_extraida:
            # verificar se especialidade extraída existe no banco
            nome_especialidade = [esp.get('nome', '').lower() for esp in especialidades]
            if especialidade_extraida.lower() not in nome_especialidade:
                specialty_validation_context = f"""
- ESPECIALIDADE NÃO ENCONTRADA: "{especialidade_extraida}"
- Esta especialidade NÃO está disponível na clínica
- IMPORTANTE: Informe ao usuário que não temos esta especialidade
- Liste TODAS as especialidades disponíveis: {specialties_list}
"""
        
        if scheduling_info.get('has_availability_info'):
            calendar_availability = scheduling_info.get('calendar_availability', {})
            if calendar_availability.get('has_availability'):
                days_info = calendar_availability.get('days_info', [])
                doctor_name = calendar_availability.get('doctor_name', 'Médico')
                total_slots = calendar_availability.get('available_slots', 0)
                
                # Verificar se data E horário já foram fornecidos
                has_date = bool(preferred_date)
                has_time = bool(preferred_time)
                
                # Se data E horário já foram fornecidos, não mostrar lista completa
                if has_date and has_time:
                    # Data e horário já fornecidos - não mostrar lista de disponibilidade
                    availability_context = f"""
DISPONIBILIDADE REAL DO GOOGLE CALENDAR:
✅ O horário {preferred_time} em {preferred_date} foi validado e está disponível
⚠️ IMPORTANTE: NÃO liste horários disponíveis - o paciente já escolheu data e horário
- Você deve CONFIRMAR o agendamento, não listar horários novamente
"""
                elif has_date and not has_time:
                    # Tem data mas falta horário - mostrar apenas horários da data escolhida
                    # Normalizar formato da data para comparação
                    from datetime import datetime
                    try:
                        if isinstance(preferred_date, str):
                            if '-' in preferred_date:
                                date_obj = datetime.strptime(preferred_date, '%Y-%m-%d').date()
                            else:
                                date_obj = datetime.strptime(preferred_date, '%d/%m/%Y').date()
                        else:
                            date_obj = preferred_date
                        
                        # Encontrar o dia específico
                        selected_day_info = None
                        for day in days_info:
                            day_date_str = day.get('date', '')
                            try:
                                if '/' in day_date_str:
                                    day_date_obj = datetime.strptime(day_date_str, '%d/%m/%Y').date()
                                else:
                                    day_date_obj = datetime.strptime(day_date_str, '%Y-%m-%d').date()
                                
                                if day_date_obj == date_obj:
                                    selected_day_info = day
                                    break
                            except:
                                continue
                        
                        if selected_day_info:
                            available_times = selected_day_info.get('available_times', [])
                            weekday = selected_day_info.get('weekday', '')
                            date_str = selected_day_info.get('date', '')
                            availability_context = f"""
DISPONIBILIDADE REAL DO GOOGLE CALENDAR:
✅ Horários disponíveis para {weekday}, {date_str}:
{', '.join(available_times[:10])}
"""
                        else:
                            availability_context = f"""
DISPONIBILIDADE REAL DO GOOGLE CALENDAR:
✅ {doctor_name} tem {total_slots} horários disponíveis nos próximos 7 dias
📅 Informações detalhadas por dia:"""
                            max_days = 3
                            for day in days_info[:max_days]:
                                date_str = day.get('date', '')
                                weekday = day.get('weekday', '')
                                available_times = day.get('available_times', [])
                                if available_times:
                                    max_times = 6
                                    times_str = ', '.join(available_times[:max_times])
                                    if len(available_times) > max_times:
                                        times_str += f" (+{len(available_times) - max_times} outros)"
                                    availability_context += f"\n• {weekday} ({date_str}): {times_str}"
                    except Exception as e:
                        logger.warning(f"Erro ao processar data para filtrar horários: {e}")
                        availability_context = f"""
DISPONIBILIDADE REAL DO GOOGLE CALENDAR:
✅ {doctor_name} tem {total_slots} horários disponíveis nos próximos 7 dias
"""
                else:
                    # Não tem data - mostrar todos os dias
                    availability_context = f"""
DISPONIBILIDADE REAL DO GOOGLE CALENDAR:
✅ {doctor_name} tem {total_slots} horários disponíveis nos próximos 7 dias
📅 Informações detalhadas por dia:"""
                    
                    # Mostrar mais dias quando estiver em choosing_schedule (até 5 dias)
                    max_days = 5 if current_state == 'choosing_schedule' else 3
                    for day in days_info[:max_days]:
                        date_str = day.get('date', '')
                        weekday = day.get('weekday', '')
                        available_times = day.get('available_times', [])
                        if available_times:
                            # Mostrar mais horários quando estiver em choosing_schedule (até 8 por dia)
                            max_times = 8 if current_state == 'choosing_schedule' else 4
                            times_str = ', '.join(available_times[:max_times])
                            if len(available_times) > max_times:
                                times_str += f" (+{len(available_times) - max_times} outros)"
                            availability_context += f"\n• {weekday} ({date_str}): {times_str}"
                
                # Verificar se data E horário já foram fornecidos
                has_date = bool(preferred_date)
                has_time = bool(preferred_time)
                
                if current_state == 'choosing_schedule' and not (has_date and has_time):
                    # Só listar horários se ainda não tiver data E horário
                    if has_date:
                        # Tem data mas falta horário - filtrar apenas horários da data escolhida
                        availability_context += f"""

⚠️ CRÍTICO - ESTADO CHOOSING_SCHEDULE (DATA JÁ ESCOLHIDA):
- O paciente já escolheu a data: {preferred_date}
- Você DEVE LISTAR APENAS os horários disponíveis para essa data específica
- NÃO liste horários de outros dias
- Formate assim:
  📅 **Horários disponíveis para {preferred_date}:**
  • [listar apenas os horários do dia {preferred_date}]
- Após listar, pergunte: "Qual desses horários você prefere?"
"""
                    else:
                        # Não tem data - listar todos os dias
                        availability_context += f"""

⚠️ CRÍTICO - ESTADO CHOOSING_SCHEDULE:
- Você DEVE LISTAR esses horários disponíveis na sua resposta ao paciente!
- NÃO apenas pergunte "qual data você prefere?" ou "qual seria a data e horário?"
- OBRIGATÓRIO: LISTE os dias e horários disponíveis mostrados acima de forma clara
- Formate assim:
  📅 **Horários disponíveis:**
  • {days_info[0].get('weekday', 'Dia')} ({days_info[0].get('date', '')}): {', '.join(days_info[0].get('available_times', [])[:6])}
  • {days_info[1].get('weekday', 'Dia')} ({days_info[1].get('date', '')}): {', '.join(days_info[1].get('available_times', [])[:6]) if len(days_info) > 1 else ''}
  (e assim por diante para todos os dias listados acima)
- Após listar TODOS os horários, pergunte: "Qual desses horários você prefere?" ou "Qual data e horário funcionam melhor para você?"
- NUNCA pergunte sobre data/horário sem listar os horários disponíveis primeiro!
"""
                else:
                    availability_context += f"\n\n⚠️ IMPORTANTE: Use essas informações REAIS do calendário para informar horários disponíveis!"
            else:
                doctor_name = calendar_availability.get('doctor_name', 'Médico')
                availability_context = f"""
DISPONIBILIDADE REAL DO GOOGLE CALENDAR:
-{doctor_name} não tem horários disponíveis nos próximos 7 dias
-Informe que o médico está sem agenda disponível e sugira outro médico ou que entre em contato."""
        
        # Informações da clínica para incluir no prompt
        clinic_info_text = ""
        if clinic_info:
            clinic_name = clinic_info.get('nome', 'Clínica Médica')
            clinic_address = clinic_info.get('endereco', '')
            clinic_phone = clinic_info.get('telefone_contato', '') or clinic_info.get('whatsapp_contato', '')
            clinic_email = clinic_info.get('email_contato', '')
            clinic_reference = clinic_info.get('referencia_localizacao', '')
            
            clinic_info_text = f"""
INFORMAÇÕES DA CLÍNICA (USE APENAS ESTAS INFORMAÇÕES, NÃO INVENTE):
- Nome: {clinic_name}
- Endereço: {clinic_address if clinic_address else 'Não informado'}
- Referência de localização: {clinic_reference if clinic_reference else 'Não informado'}
- Telefone: {clinic_phone if clinic_phone else 'Não informado'}
- Email: {clinic_email if clinic_email else 'Não informado'}
"""

        # Contexto específico baseado no estado
        state_context = ""
        
        # Se tem médico mas NÃO tem especialidade, deve perguntar especialidade primeiro
        if selected_doctor and not selected_specialty:
            # Obter especialidades do médico selecionado
            doctor_specialties = []
            for medico in medicos:
                if medico.get('nome', '').lower() == selected_doctor.lower():
                    especialidades_medico = medico.get('especialidades_display', '')
                    if especialidades_medico:
                        specialties_list_raw = especialidades_medico.replace(';', ',').split(',')
                        doctor_specialties = [s.strip() for s in specialties_list_raw if s.strip()]
                    break
            
            if doctor_specialties:
                specialties_display = ', '.join(doctor_specialties)
                state_context = f"""
⚠️ ESTADO ATUAL: SELECIONANDO ESPECIALIDADE (MÉDICO JÁ ESCOLHIDO)
- O paciente já escolheu o médico: {selected_doctor}
- Agora você DEVE perguntar qual especialidade do {selected_doctor} o paciente deseja
- Especialidades disponíveis para {selected_doctor}: {specialties_display}
- NÃO pergunte sobre data ou horário ainda
- Pergunte: "Para qual especialidade você gostaria de agendar com o {selected_doctor}?" ou "Qual especialidade você precisa?"
"""
            else:
                state_context = f"""
⚠️ ESTADO ATUAL: SELECIONANDO ESPECIALIDADE (MÉDICO JÁ ESCOLHIDO)
- O paciente já escolheu o médico: {selected_doctor}
- Agora você DEVE perguntar qual especialidade o paciente deseja
- NÃO pergunte sobre data ou horário ainda
- Liste as especialidades disponíveis e pergunte qual o paciente prefere
"""
        elif current_state == 'selecting_doctor' and selected_specialty and medicos_list:
            state_context = f"""
⚠️ ESTADO ATUAL: SELECIONANDO MÉDICO
- O paciente já escolheu a especialidade: {selected_specialty}
- Agora você DEVE perguntar qual médico que atende nessa especialidade o paciente deseja
- NÃO pergunte sobre data ou horário ainda
- Liste os médicos disponíveis e pergunte: "Qual médico você prefere?" ou "Com qual desses médicos você gostaria de agendar?"
"""
        elif current_state == 'selecting_specialty' or (not selected_specialty and not selected_doctor):
            state_context = f"""
⚠️ ESTADO ATUAL: SELECIONANDO ESPECIALIDADE
- Pergunte qual especialidade o paciente deseja
- NÃO pergunte sobre médico, data ou horário ainda
- Liste as especialidades disponíveis
"""
        elif current_state == 'choosing_schedule':
            # Verificar se data E horário já foram fornecidos
            has_date = bool(preferred_date)
            has_time = bool(preferred_time)
            
            if has_date and has_time:
                # Data E horário já foram fornecidos - deve confirmar, não listar horários
                state_context = f"""
⚠️ ESTADO ATUAL: CONFIRMAÇÃO DE AGENDAMENTO
- O paciente já forneceu TODAS as informações: especialidade, médico, data ({preferred_date}) e horário ({preferred_time})
- NÃO liste horários disponíveis novamente
- Você DEVE confirmar o agendamento: "Para confirmar, o agendamento seria para [data] às [horário] com [médico], especialista em [especialidade]. Tudo certo?"
- Se o paciente confirmar, você pode prosseguir com a confirmação final
"""
            elif has_date and not has_time:
                # Tem data mas falta horário - listar horários APENAS para a data escolhida
                state_context = f"""
⚠️ ESTADO ATUAL: ESCOLHENDO HORÁRIO (DATA JÁ ESCOLHIDA)
- O paciente já escolheu a data: {preferred_date}
- Você DEVE listar APENAS os horários disponíveis para essa data específica
- NÃO liste horários de outros dias
- Após listar os horários disponíveis para {preferred_date}, pergunte: "Qual desses horários você prefere?"
"""
            else:
                # Não tem data ou horário - listar todos os horários disponíveis
                has_availability = scheduling_info.get('has_availability_info', False)
                if has_availability:
                    calendar_availability = scheduling_info.get('calendar_availability', {})
                    if calendar_availability.get('has_availability'):
                        days_info = calendar_availability.get('days_info', [])
                        if days_info:
                            state_context = f"""
⚠️ ESTADO ATUAL: ESCOLHENDO DATA/HORÁRIO
- O paciente já selecionou especialidade e médico
- Você DEVE listar os horários REAIS disponíveis do Google Calendar (veja "DISPONIBILIDADE REAL DO GOOGLE CALENDAR" abaixo)
- NÃO apenas pergunte "qual data você prefere?" - LISTE os dias e horários disponíveis
- Mostre os horários disponíveis por dia de forma clara e organizada
- Após listar, pergunte qual data e horário o paciente prefere
"""
                        else:
                            state_context = f"""
⚠️ ESTADO ATUAL: ESCOLHENDO DATA/HORÁRIO
- O paciente já selecionou especialidade e médico
- Não há horários disponíveis nos próximos dias
- Informe isso ao paciente e sugira entrar em contato
"""
                    else:
                        state_context = f"""
⚠️ ESTADO ATUAL: ESCOLHENDO DATA/HORÁRIO
- O paciente já selecionou especialidade e médico
- Não há horários disponíveis no momento
- Informe isso ao paciente e sugira entrar em contato
"""
                else:
                    state_context = f"""
⚠️ ESTADO ATUAL: ESCOLHENDO DATA/HORÁRIO
- O paciente já selecionou especialidade e médico
- Agora você pode perguntar sobre data e horário preferido
"""
        
        prompt = f"""Você é um assistente virtual da {clinic_info.get('nome', 'Clínica Médica')}.

MENSAGEM DO PACIENTE: "{message}"

INTENÇÃO DETECTADA: {intent}
SAUDAÇÃO JÁ ENVIADA: {saudacao_status}
{state_context}
{clinic_info_text}
{doctor_price_context}
INFORMAÇÕES JÁ COLETADAS (NÃO PERGUNTE NOVAMENTE):
{collected_info_str}
{availability_context}
{missing_context}
{specialty_validation_context}

ENTIDADES EXTRAÍDAS AGORA:
{entities}

ESPECIALIDADES DISPONÍVEIS: {specialties_list}

MÉDICOS DISPONÍVEIS PARA A ESPECIALIDADE '{selected_specialty}':
{medicos_text}

INSTRUÇÕES:
1. Responda de forma natural, educada e profissional.
2. Se "SAUDAÇÃO JÁ ENVIADA" = "Não", cumprimente o paciente uma única vez e mencione que é a assistente virtual da clínica. Caso contrário, NÃO utilize expressões como "Olá", "Oi" e NÃO repita a apresentação.
3. NÃO repita perguntas sobre informações já coletadas (veja acima).
4. Verifique "INFORMAÇÕES AINDA NECESSÁRIAS". Se estiver vazio, avance para a confirmação/handoff.
5. Se houver itens faltantes, pergunte APENAS o primeiro item da lista e aguarde a resposta.
6. Use emojis moderadamente para deixar a conversa mais amigável.
7. Seja objetivo e direto.

REGRAS IMPORTANTES:
- Se intent = "saudacao" E não tiver nome: SEMPRE pergunte o nome primeiro ("Olá! Para começar, qual é o seu nome?")
- Se já tiver nome do paciente, especialidade, médico, data e horário: pergunte se deseja confirmar o pré-agendamento
- Se faltar apenas UMA informação: pergunte exatamente essa informação faltante
- Se todas as entidades foram extraídas e confirmadas, então envie o handoff
- NÃO solicite informações que já estão na lista "INFORMAÇÕES JÁ COLETADAS"
- **CRÍTICO 1**: Se NÃO tem especialidade selecionada, você DEVE perguntar a especialidade PRIMEIRO. NÃO pergunte sobre médico, data ou horário até que a especialidade seja selecionada.
- **CRÍTICO 2**: Se tem especialidade mas NÃO tem médico selecionado, você DEVE perguntar qual médico o paciente prefere. NÃO pergunte sobre data ou horário até que o médico seja selecionado.
- **CRÍTICO 3**: Se tem médico mas NÃO tem especialidade, você DEVE perguntar qual especialidade do médico o paciente deseja. NÃO pergunte sobre data ou horário até que a especialidade seja selecionada.
- **CRÍTICO 4**: NUNCA pergunte sobre data ou horário se especialidade OU médico ainda não foram selecionados. A ordem obrigatória é: 1) Especialidade → 2) Médico → 3) Data → 4) Horário
- Se há médicos disponíveis para a especialidade, liste-os e pergunte: "Qual médico você prefere?" ou "Com qual desses médicos você gostaria de agendar?"
- **NUNCA** pule a etapa de seleção do médico indo direto para data/horário
- **NUNCA** pule a etapa de seleção da especialidade indo direto para médico ou data/horário

PRIORIDADE DE COLETA (ORDEM OBRIGATÓRIA - NÃO PULE ETAPAS):
1. Nome do paciente (pergunte somente se ainda estiver faltando)
2. Especialidade desejada (OBRIGATÓRIO antes de médico, data ou horário)
3. Médico específico (OBRIGATÓRIO após escolher especialidade) - SEMPRE pergunte ao paciente qual médico ele deseja, MESMO que haja apenas um disponível
4. Data preferida (SOMENTE após especialidade E médico serem selecionados)
5. Horário preferido (SOMENTE após especialidade E médico serem selecionados)
6. Confirmação final

Sempre confie na lista de faltantes para saber o próximo passo. Se faltar nome, peça o nome. Se faltar médico, apresente os médicos disponíveis e PERGUNTE qual o paciente prefere. Se faltar apenas horário, peça somente o horário.

REGRAS CRÍTICAS:
- NUNCA invente nomes de médicos! Use APENAS os médicos listados em "MÉDICOS DISPONÍVEIS"
- Se o usuário perguntar sobre médicos, liste APENAS os médicos reais do banco de dados
- Se não houver médicos para uma especialidade, informe que não há médicos disponíveis
- NUNCA invente informações sobre endereço, telefone ou localização da clínica! Use APENAS as informações fornecidas em "INFORMAÇÕES DA CLÍNICA"
- Se o usuário perguntar sobre localização, endereço ou onde a clínica está localizada, use EXATAMENTE o endereço fornecido em "INFORMAÇÕES DA CLÍNICA"
- Se o usuário perguntar sobre preço/valor/custo de consulta e já tiver médico selecionado, use o valor em "VALOR DA CONSULTA" acima
- Se o usuário perguntar sobre preço mas não tiver médico selecionado, mostre os preços da lista de "MÉDICOS DISPONÍVEIS"

DISTINÇÃO ENTRE DÚVIDAS E AGENDAMENTO:
- Se intent = "buscar_info": Forneça APENAS a informação solicitada, NÃO inicie processo de agendamento
- Se intent = "agendar_consulta": Inicie ou continue o processo de agendamento, coletando informações necessárias
- Se usuário pergunta sobre médicos/especialidades mas NÃO quer agendar: use "buscar_info"
- Se usuário quer agendar E menciona médico/especialidade: use "agendar_consulta"

Gere a resposta:"""
        
        return prompt, prompt_metadata
    
    def _get_fallback_response(self, message: str) -> Dict[str, Any]:
        """Resposta de fallback quando há erro"""
        return {
            'response': f"Desculpe, estou com dificuldades para responder no momento. Você poderia reformular ou tentar novamente em instantes?",
            'intent': 'error',
            'confidence': 0.0,
            'suggested_doctors': [],
            'primary_suggested_doctor': None
        }


