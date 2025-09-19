"""
Serviço de Handoff para WhatsApp
Gera links personalizados para transferir pacientes para atendimento humano
"""
import logging
import urllib.parse
from typing import Any, Dict, Optional

from django.conf import settings

logger = logging.getLogger(__name__)


class HandoffService:
    """
    Serviço para gerar links de handoff personalizados para WhatsApp
    """
    
    def __init__(self):
        self.clinic_phone = getattr(settings, 'CLINIC_WHATSAPP_NUMBER', '5511999999999')
        self.base_url = 'https://api.whatsapp.com/send'
    
    def generate_appointment_handoff_link(self, 
                                        patient_name: str,
                                        doctor_name: str,
                                        specialty: str = None,
                                        appointment_type: str = None,
                                        date: str = None,
                                        time: str = None,
                                        additional_info: Dict = None) -> str:
        """
        Gera link de WhatsApp para handoff de agendamento
        
        Args:
            patient_name: Nome do paciente
            doctor_name: Nome do médico
            specialty: Especialidade médica
            appointment_type: Tipo de consulta (Particular, Convênio, etc.)
            date: Data da consulta (formato: DD/MM/YYYY)
            time: Horário da consulta (formato: HH:mm)
            additional_info: Informações adicionais
            
        Returns:
            URL do WhatsApp com mensagem pré-formatada
        """
        try:
            # Obter informações completas do médico do banco de dados
            doctor_info = self._get_doctor_complete_info(doctor_name)
            
            # Usar dados do banco ou valores fornecidos
            final_specialty = specialty or doctor_info.get('specialty', 'Consulta Geral')
            final_appointment_type = appointment_type or 'Consulta'
            final_date = date or 'Data a definir'
            final_time = time or 'Horário a definir'
            
            # Construir mensagem no formato específico solicitado
            # Formato: "- Campo: Valor" com %20 para espaços e %0A para quebras de linha
            clean_doctor_name = (doctor_name or '').replace('Dr. ', '').replace('Dra. ', '')
            
            message_parts = [
                f"- Nome do Paciente: {patient_name}",
                f"- Médico: {clean_doctor_name}",
                f"- Especialidade: {final_specialty}",
                f"- Tipo de Consulta: {final_appointment_type}",
                f"- Data/Hora escolhida: {final_date} às {final_time}"
            ]
            
            # Adicionar CRM se disponível
            if doctor_info.get('crm'):
                message_parts.append(f"- CRM: {doctor_info['crm']}")
            
            # Adicionar convênios aceitos se disponível
            if doctor_info.get('convenios'):
                convenios_str = ', '.join(doctor_info['convenios'])
                message_parts.append(f"- Convênios aceitos: {convenios_str}")
            
            # Adicionar informações extras se fornecidas
            if additional_info:
                for key, value in additional_info.items():
                    if value:
                        formatted_key = key.replace('_', ' ').title()
                        message_parts.append(f"- {formatted_key}: {value}")
            
            # Juntar com quebras de linha e codificar manualmente
            # Usar %0A para quebras de linha e %20 para espaços
            encoded_parts = []
            for part in message_parts:
                # Substituir espaços por %20
                encoded_part = part.replace(' ', '%20')
                # Substituir caracteres especiais
                encoded_part = encoded_part.replace(':', '%3A')
                encoded_part = encoded_part.replace('/', '%2F')
                encoded_part = encoded_part.replace('à', '%C3%A0')
                encoded_part = encoded_part.replace('é', '%C3%A9')
                encoded_part = encoded_part.replace('ã', '%C3%A3')
                encoded_part = encoded_part.replace('ç', '%C3%A7')
                encoded_parts.append(encoded_part)
            
            # Juntar com %0A (quebra de linha)
            encoded_message = '%0A'.join(encoded_parts)
            
            # Gerar link completo
            whatsapp_link = f"{self.base_url}?phone={self.clinic_phone}&text={encoded_message}"
            
            logger.info(f"Link de handoff gerado para {patient_name} - {doctor_name}")
            
            return whatsapp_link
            
        except Exception as e:
            logger.error(f"Erro ao gerar link de handoff: {e}")
            return self._generate_fallback_link()
    
    def generate_simple_handoff_link(self, message: str) -> str:
        """
        Gera link simples de WhatsApp com mensagem personalizada
        
        Args:
            message: Mensagem a ser enviada
            
        Returns:
            URL do WhatsApp
        """
        try:
            encoded_message = urllib.parse.quote(message)
            return f"{self.base_url}?phone={self.clinic_phone}&text={encoded_message}"
        except Exception as e:
            logger.error(f"Erro ao gerar link simples: {e}")
            return self._generate_fallback_link()
    
    def generate_info_request_link(self, requested_info: str) -> str:
        """
        Gera link para solicitar informações específicas
        
        Args:
            requested_info: Tipo de informação solicitada
            
        Returns:
            URL do WhatsApp
        """
        message = f"""🤖 *SOLICITAÇÃO VIA CHATBOT*

📋 O paciente solicitou informações sobre:
{requested_info}

👩‍💼 Secretária: Por favor, forneça as informações solicitadas"""
        
        return self.generate_simple_handoff_link(message)
    
    def _generate_fallback_link(self) -> str:
        """Gera link de fallback em caso de erro"""
        fallback_message = "Olá! Gostaria de agendar uma consulta através do chatbot."
        encoded_message = urllib.parse.quote(fallback_message)
        return f"{self.base_url}?phone={self.clinic_phone}&text={encoded_message}"
    
    def format_appointment_summary(self, 
                                 patient_name: str,
                                 doctor_name: str,
                                 specialty: str,
                                 date: str,
                                 time: str,
                                 appointment_type: str = "Consulta") -> str:
        """
        Formata resumo do agendamento para exibição
        
        Returns:
            String formatada com resumo do agendamento
        """
        return f"""📋 *RESUMO DO PRÉ-AGENDAMENTO*

👤 **Paciente:** {patient_name}
👨‍⚕️ **Médico:** {doctor_name}
🩺 **Especialidade:** {specialty}
💼 **Tipo:** {appointment_type}
📅 **Data:** {date}
🕐 **Horário:** {time}

✅ Para confirmar este agendamento, clique no link abaixo"""
    
    def extract_patient_info_from_context(self, context_history: list, entities: Dict) -> Dict[str, str]:
        """
        Extrai informações do paciente a partir do contexto da conversa
        Usa dados do banco de dados para validar convênios
        
        Args:
            context_history: Histórico da conversa
            entities: Entidades extraídas da mensagem atual
            
        Returns:
            Dicionário com informações do paciente
        """
        patient_info = {
            'patient_name': 'Paciente',  # Padrão se não informado
            'phone_number': '',
            'insurance': '',
            'appointment_type': 'Consulta',
            'preferred_time': '',
            'additional_notes': ''
        }
        
        # Extrair informações das entidades atuais
        if 'patient_name' in entities:
            patient_info['patient_name'] = entities['patient_name']
        
        if 'insurance' in entities:
            patient_info['insurance'] = entities['insurance']
            patient_info['appointment_type'] = entities['insurance']
        
        if 'times' in entities and entities['times']:
            patient_info['preferred_time'] = entities['times'][0]
        
        if 'dates' in entities and entities['dates']:
            patient_info['preferred_date'] = entities['dates'][0]
        
        # Obter convênios válidos do banco de dados
        valid_insurances = self._get_valid_insurances()
        
        # Buscar informações no histórico da conversa
        for message in context_history:
            if message.get('is_user', True):
                content = message.get('content', '').lower()
                
                # Buscar menções de convênio usando dados do banco
                for insurance in valid_insurances:
                    if insurance.lower() in content:
                        patient_info['insurance'] = insurance
                        patient_info['appointment_type'] = insurance
                        break
                
                # Buscar se mencionou ser particular
                if any(word in content for word in ['particular', 'sem convênio', 'não tenho convênio']):
                    patient_info['appointment_type'] = 'Particular'
                
                # Buscar menção de nome próprio (primeira palavra maiúscula)
                words = content.split()
                for word in words:
                    if word.istitle() and len(word) > 2 and word not in ['Dr', 'Dra', 'Doutor', 'Doutora']:
                        patient_info['patient_name'] = word
                        break
        
        return patient_info
    
    def _get_valid_insurances(self) -> list:
        """
        Obtém lista de convênios válidos do banco de dados
        
        Returns:
            Lista de nomes de convênios
        """
        try:
            from .rag_service import RAGService
            
            convenios = RAGService.get_convenios()
            return [convenio.get('nome', '') for convenio in convenios if convenio.get('nome')]
            
        except Exception as e:
            logger.error(f"Erro ao obter convênios do banco: {e}")
            # Fallback para convênios comuns
            return ['Unimed', 'SulAmérica', 'Amil', 'Bradesco', 'Particular']
    
    def create_confirmation_message(self, 
                                  doctor_name: str,
                                  date: str,
                                  time: str,
                                  patient_info: Dict) -> str:
        """
        Cria mensagem de confirmação para o paciente
        
        Returns:
            Mensagem formatada para confirmação
        """
        appointment_type = patient_info.get('appointment_type', 'Consulta')
        
        message = f"""✅ **Perfeito! Vamos confirmar seu pré-agendamento:**

📋 **RESUMO:**
👤 Paciente: {patient_info.get('patient_name', 'Não informado')}
👨‍⚕️ Médico: {doctor_name}
📅 Data: {date}
🕐 Horário: {time}
💼 Tipo: {appointment_type}

**🔄 Para CONFIRMAR definitivamente:**
👩‍💼 Nossa secretária validará a disponibilidade e confirmará seu agendamento.

**📞 Clique no link abaixo para falar diretamente com nossa equipe:**"""
        
        return message
    
    def _get_doctor_complete_info(self, doctor_name: str) -> Dict[str, Any]:
        """
        Obtém informações completas do médico do banco de dados
        
        Args:
            doctor_name: Nome do médico
            
        Returns:
            Dicionário com informações do médico
        """
        try:
            from .rag_service import RAGService

            logger.info(f"Buscando médico: '{doctor_name}'")
            
            # Verificar se doctor_name é válido
            if not doctor_name or doctor_name == 'None':
                logger.warning("Nome do médico inválido, usando médico padrão")
                return {
                    'name': 'Dr. João Carvalho',
                    'crm': '12345',
                    'specialty': 'Cardiologia',
                    'convenios': ['Unimed', 'SulAmérica']
                }
            
            # Buscar médico no banco
            medico_data = RAGService.get_medico_by_name(doctor_name)
            
            if medico_data:
                # Extrair informações relevantes
                doctor_info = {
                    'name': medico_data.get('nome', doctor_name),
                    'crm': medico_data.get('crm', ''),
                    'specialty': '',
                    'convenios': []
                }
                
                # Processar especialidades
                especialidades = medico_data.get('especialidades', [])
                if especialidades:
                    if isinstance(especialidades[0], dict):
                        doctor_info['specialty'] = especialidades[0].get('nome', 'Consulta Geral')
                    else:
                        doctor_info['specialty'] = str(especialidades[0])
                
                # Processar convênios
                convenios = medico_data.get('convenios', [])
                if convenios:
                    doctor_info['convenios'] = [
                        conv.get('nome', '') if isinstance(conv, dict) else str(conv) 
                        for conv in convenios
                    ]
                
                logger.info(f"Informações do médico {doctor_name} obtidas do banco de dados")
                return doctor_info
            
            logger.warning(f"Médico {doctor_name} não encontrado no banco")
            
        except Exception as e:
            logger.error(f"Erro ao obter informações do médico {doctor_name}: {e}")
        
        # Retornar informações padrão se não encontrar no banco
        return {
            'name': doctor_name,
            'crm': '',
            'specialty': 'Consulta Geral',
            'convenios': ['Particular']
        }


# Instância global do serviço
handoff_service = HandoffService()
