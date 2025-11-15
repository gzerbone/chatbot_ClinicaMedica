"""
Serviço de Handoff para WhatsApp.
Gera links pré-formatados com as informações essenciais do pré-agendamento.
"""
import logging
import urllib.parse
from typing import Dict, Optional

from django.conf import settings

logger = logging.getLogger(__name__)


class HandoffService:
    """Responsável por montar mensagens de handoff para a equipe humana."""

    def __init__(self):
        self.clinic_phone = getattr(settings, 'CLINIC_WHATSAPP_NUMBER', '5511999999999')
        self.base_url = 'https://api.whatsapp.com/send'

    def generate_appointment_handoff_link(
        self,
        patient_name: str,
        doctor_name: str,
        specialty: Optional[str] = None,
        date: Optional[str] = None,
        time: Optional[str] = None,
    ) -> str:
        """
        Gera um link do WhatsApp contendo os dados do pré-agendamento.

        Campos utilizados: paciente, médico, especialidade, data e horário.
        """
        try:
            message = self._build_message(
                patient_name=patient_name,
                doctor_name=doctor_name,
                specialty=specialty,
                date=date,
                time=time,
            )

            encoded_message = urllib.parse.quote(message)
            whatsapp_link = f"{self.base_url}?phone={self.clinic_phone}&text={encoded_message}"

            logger.info("Link de handoff gerado para %s - %s", patient_name, doctor_name)
            return whatsapp_link

        except Exception as exc:
            logger.error("Erro ao gerar link de handoff: %s", exc)
            return self._generate_fallback_link()

    def _build_message(
        self,
        patient_name: str,
        doctor_name: str,
        specialty: Optional[str],
        date: Optional[str],
        time: Optional[str],
    ) -> str:
        """Monta o texto que será enviado para a equipe humana via WhatsApp."""
        patient = patient_name or "Paciente"
        doctor = doctor_name or "Médico"
        speciality = specialty or "Especialidade a definir"
        appointment_date = date or "Data a definir"
        appointment_time = time or "Horário a definir"

        doctor_display = doctor.replace("Dr. ", "").replace("Dra. ", "").strip() or doctor

        return (
            "Agendamento via Chatbot:\n"
            f"Paciente: {patient}\n"
            f"Médico: {doctor_display}\n"
            f"Especialidade: {speciality}\n"
            f"Data/Horário: {appointment_date} às {appointment_time}"
        )

    def _generate_fallback_link(self) -> str:
        """Gera um link genérico quando não é possível montar os dados do agendamento."""
        fallback_message = "Olá! Gostaria de agendar uma consulta através do chatbot."
        encoded_message = urllib.parse.quote(fallback_message)
        return f"{self.base_url}?phone={self.clinic_phone}&text={encoded_message}"

    def create_confirmation_message(
        self,
        doctor_name: str,
        specialty: str,
        date: str,
        time: str,
        patient_info: Dict,
    ) -> str:
        """Formata a mensagem de confirmação enviada ao paciente dentro do chat."""
        message = f"""✅ *Perfeito! Vamos confirmar seu pré-agendamento:*

📋 *RESUMO:*
👤 Paciente: {patient_info.get('patient_name', 'Não informado')}
👨‍⚕️ Médico: {doctor_name}
🧠 Especialidade: {specialty}
📅 Data: {date}
🕐 Horário: {time}

*📞 Clique no link abaixo para falar diretamente com nossa equipe:*"""

        return message


# Instância global do serviço
handoff_service = HandoffService()
