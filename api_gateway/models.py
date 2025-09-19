"""
Modelos para armazenar dados de conversas e agendamentos
"""
from django.db import models
from django.utils import timezone


class ConversationSession(models.Model):
    """
    Sessão de conversa persistente para fluxos de agendamento
    """
    phone_number = models.CharField(max_length=20, unique=True)
    patient_name = models.CharField(max_length=100, blank=True, null=True)
    pending_name = models.CharField(max_length=100, blank=True, null=True, help_text="Nome extraído aguardando confirmação")
    name_confirmed = models.BooleanField(default=False, help_text="Nome do paciente foi confirmado")
    current_state = models.CharField(
        max_length=50,
        choices=[
            ('idle', 'Ocioso'),
            ('collecting_patient_info', 'Coletando Dados do Paciente'),
            ('collecting_info', 'Coletando Informações'),
            ('confirming_name', 'Confirmando Nome do Paciente'),
            ('selecting_doctor', 'Selecionando Médico'),
            ('choosing_schedule', 'Escolhendo Horário'),
            ('confirming', 'Confirmando'),
            ('completed', 'Concluído'),
            ('cancelled', 'Cancelado')
        ],
        default='idle'
    )
    specialty_interest = models.CharField(max_length=100, blank=True, null=True)
    insurance_type = models.CharField(max_length=50, blank=True, null=True)
    preferred_date = models.DateField(blank=True, null=True)
    preferred_time = models.TimeField(blank=True, null=True)
    selected_doctor = models.CharField(max_length=100, blank=True, null=True)
    additional_notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-last_activity']
        verbose_name = 'Sessão de Conversa'
        verbose_name_plural = 'Sessões de Conversa'
    
    def __str__(self):
        return f"{self.phone_number} - {self.patient_name or 'Paciente'} ({self.current_state})"
    
    def is_active(self):
        """Verifica se a sessão está ativa (última atividade há menos de 24h)"""
        return (timezone.now() - self.last_activity).total_seconds() < 86400  # 24 horas
    
    def update_activity(self):
        """Atualiza timestamp da última atividade"""
        self.last_activity = timezone.now()
        self.save(update_fields=['last_activity'])


class ConversationMessage(models.Model):
    """
    Mensagens individuais da conversa
    """
    MESSAGE_TYPES = [
        ('user', 'Usuário'),
        ('bot', 'Bot'),
        ('system', 'Sistema')
    ]
    
    session = models.ForeignKey(ConversationSession, on_delete=models.CASCADE, related_name='messages')
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES)
    content = models.TextField()
    intent = models.CharField(max_length=50, blank=True, null=True)
    confidence = models.FloatField(blank=True, null=True)
    entities = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp']
        verbose_name = 'Mensagem da Conversa'
        verbose_name_plural = 'Mensagens da Conversa'
    
    def __str__(self):
        return f"{self.get_message_type_display()}: {self.content[:50]}..."


class AppointmentRequest(models.Model):
    """
    Solicitações de agendamento geradas pelo chatbot
    """
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('confirmed', 'Confirmado'),
        ('cancelled', 'Cancelado'),
        ('completed', 'Concluído')
    ]
    
    session = models.OneToOneField(ConversationSession, on_delete=models.CASCADE, related_name='appointment_request')
    patient_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    doctor_name = models.CharField(max_length=100)
    specialty = models.CharField(max_length=100)
    appointment_type = models.CharField(max_length=50)  # Particular, Convênio, etc.
    preferred_date = models.DateField()
    preferred_time = models.TimeField()
    insurance = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    handoff_link = models.URLField(blank=True, null=True)
    confirmation_code = models.CharField(max_length=20, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Solicitação de Agendamento'
        verbose_name_plural = 'Solicitações de Agendamento'
    
    def __str__(self):
        return f"{self.patient_name} - {self.doctor_name} ({self.preferred_date})"


class RAGCache(models.Model):
    """
    Cache para dados do RAG (informações da clínica)
    """
    cache_key = models.CharField(max_length=255, unique=True)
    data = models.JSONField()
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Cache RAG'
        verbose_name_plural = 'Caches RAG'
    
    def __str__(self):
        return f"{self.cache_key} (expires: {self.expires_at})"
    
    def is_expired(self):
        return timezone.now() > self.expires_at