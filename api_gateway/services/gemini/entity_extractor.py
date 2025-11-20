"""
Entity Extractor - Extração de Entidades das Mensagens

Responsável por:
- Extrair entidades relevantes das mensagens usando Gemini
- Normalizar e validar dados extraídos
- Sem fallbacks - se Gemini falhar, retorna vazio
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
        Extrai entidades da mensagem usando apenas Gemini
        Sem fallbacks - se falhar, retorna vazio e pede novamente ao usuário
        """
        try:
            # Tentar extração com Gemini primeiro
            if self.model:
                entities = self.extract_entities_with_gemini(message, session, conversation_history, clinic_data)
                if entities and any(entities.values()):
                    # Verificar se o nome extraído parece incompleto (apenas 2 palavras quando deveria ter mais)
                    if 'nome_paciente' in entities:
                        # Validar nome extraído pelo Gemini
                        nome_extraido = entities['nome_paciente']
                        if nome_extraido:
                            logger.info(f"✅ Nome extraído pelo Gemini: '{nome_extraido}'")
                    
                    return self.validate_entities(entities)
            
            # Sem fallback - se Gemini não extraiu, retornar vazio
            logger.warning("⚠️ Gemini não retornou entidades - retornando vazio")
            return {}
            
        except Exception as e:
            logger.error(f"❌ Erro na extração de entidades com Gemini: {e}")
            # Sem fallback - retornar vazio e deixar o sistema pedir novamente
            return {}
        
    # Método para extrair entidades com Gemini
    def extract_entities_with_gemini(self, message: str, session: Dict,
                                conversation_history: List, clinic_data: Dict) -> Dict[str, str]:
        """Extrai entidades usando Gemini"""
        try:
            prompt = self._build_entity_extraction_prompt(message, session, conversation_history, clinic_data)
            
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.4,  # Mantido baixo para extração precisa, mas aumentado de 0.5 para melhor contexto
                    "top_p": 0.85,      # Aumentado de 0.8 para melhor compreensão de referências
                    "top_k": 30,        # Aumentado de 20 para considerar mais variações de nomes/entidades
                    "max_output_tokens": 300  # Aumentado de 200 para extrair nomes completos e entidades complexas
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
        last_suggested_doctor = session.get('last_suggested_doctor')
        last_suggested_doctors = session.get('last_suggested_doctors') or []
        selected_specialty = session.get('selected_specialty')
        preferred_date = session.get('preferred_date')
        preferred_time = session.get('preferred_time')

        # Resumo compacto do histórico recente (últimas 4 mensagens)
        history_summary = "Sem histórico recente."
        if conversation_history:
            recent_messages = conversation_history[-4:]
            history_lines: List[str] = []
            for msg in recent_messages:
                role = "Paciente" if msg.get('is_user') else "Assistente"
                content = (msg.get('content') or "").replace('\n', ' ').strip()
                if len(content) > 90:
                    content = content[:87].strip() + "..."
                history_lines.append(f"- {role}: {content}")
            if history_lines:
                history_summary = "\n".join(history_lines)

        # Resumo de especialidades disponíveis (limitar a 5)
        specialties_summary = "Não disponível"
        specialties = clinic_data.get('especialidades') or []
        if specialties:
            specialties_summary = ', '.join([
                esp.get('nome', '').strip()
                for esp in specialties[:5]
                if esp.get('nome')
            ]) or "Não disponível"

        # Resumo de médicos disponíveis (limitar a 5)
        doctors_summary = "Não disponível"
        medicos = clinic_data.get('medicos') or []
        doctor_entries: List[str] = []
        for medico in medicos[:5]:
            nome = (medico.get('nome') or '').strip()
            if not nome:
                continue
            especialidades_medico = (medico.get('especialidades_display') or '').strip()
            if especialidades_medico:
                doctor_entries.append(f"{nome} ({especialidades_medico})")
            else:
                doctor_entries.append(nome)
        if doctor_entries:
            doctors_summary = ', '.join(doctor_entries)

        recent_doctors_context = []
        if selected_doctor:
            recent_doctors_context.append(f"Confirmado: {selected_doctor}")
        if last_suggested_doctor and last_suggested_doctor != selected_doctor:
            recent_doctors_context.append(f"Sugerido: {last_suggested_doctor}")
        if last_suggested_doctors:
            others = [doc for doc in last_suggested_doctors if doc not in {selected_doctor, last_suggested_doctor}]
            if others:
                recent_doctors_context.append("Lista sugerida: " + ', '.join(others[:4]))
        recent_doctors_text = recent_doctors_context and ' | '.join(recent_doctors_context) or 'Sem sugestões recentes.'

        prompt = f"""Você é um assistente especializado em extrair informações de mensagens de pacientes.

MENSAGEM: "{message}"

CONTEXTO:
- Estado atual: {current_state}
- Nome atual: {patient_name or 'Não informado'}
- Médico atual: {selected_doctor or 'Não selecionado'}
- Especialidade atual: {selected_specialty or 'Não selecionada'}
- Data atual: {preferred_date or 'Não informada'}
- Horário atual: {preferred_time or 'Não informado'}
- Médicos recentes: {recent_doctors_text}

HISTÓRICO RECENTE (máx. 4 mensagens):
{history_summary}

REFERÊNCIAS DISPONÍVEIS:
- Especialidades: {specialties_summary}
- Médicos: {doctors_summary}

EXTRAIA as seguintes entidades da mensagem (use null se não encontrar):
- nome_paciente: Nome completo do paciente (EXTRAIA TODAS AS PALAVRAS DO NOME, incluindo preposições como "da", "de", "dos", "das". Exemplo: "João da Silva" deve ser extraído completamente como "João da Silva", NÃO apenas "João da". Se o paciente disser "Maria de Souza Santos", extraia "Maria de Souza Santos" completo)
- medico: Nome do médico mencionado
- especialidade: Especialidade médica
- data: Data mencionada
- horario: Horário mencionado

IMPORTANTE - EXTRAÇÃO DE NOME:
- Para nome_paciente: SEMPRE extraia o nome completo com TODAS as palavras mencionadas pelo paciente. 
- NÃO trunque o nome em nenhuma circunstância. 
- Se o paciente disser "João da Silva", extraia EXATAMENTE "João da Silva" (3 palavras), NÃO "João da" (2 palavras).
- Se o paciente disser "Maria de Souza", extraia "Maria de Souza" completo.
- Preposições como "da", "de", "dos", "das" são PARTE DO NOME e devem ser incluídas.
- O nome pode ter 2, 3, 4 ou mais palavras - extraia TODAS elas.
- Se encontrar especialidade como "pneumologista", extraia como "pneumologia"
- Se a mensagem modifica informações já coletadas, extraia os novos valores
- Use o contexto para entender referências
- Se for uma confirmação curta (ex.: "sim", "ok", "isso mesmo") e houver médico confirmado ou sugerido, retorne esse médico.
- Caso o paciente utilize pronomes (ex.: "com ele"), utilize o histórico e a lista de médicos para identificar o nome correto.

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
            
            # Log detalhado para debug de nomes
            if 'nome_paciente' in entities and entities['nome_paciente']:
                logger.info(f"🔍 Nome extraído pelo Gemini (RAW): '{entities['nome_paciente']}' (tamanho: {len(entities['nome_paciente'])})")
            
            # Remover valores null
            result = {k: v for k, v in entities.items() if v and v != 'null'}
            
            return result
            
        except Exception as e:
            logger.error(f"Erro ao extrair entidades do JSON: {e}")
            logger.error(f"Resposta recebida: {response_text}")
            return {}


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
            
            # Aceitar nomes com pelo menos 3 caracteres e que contenham espaço (nome e sobrenome)
            # Não limitar a 3 palavras - aceitar nomes completos com todas as palavras
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