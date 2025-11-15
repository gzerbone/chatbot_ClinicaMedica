"""
URLs para API Gateway
"""
from django.urls import path

from . import views

app_name = 'api_gateway'

urlpatterns = [
    # Webhook do WhatsApp
    path('webhook/whatsapp/', views.whatsapp_webhook, name='whatsapp_webhook'),
        
    # Endpoints de monitoramento de tokens
    path('monitor/tokens/', views.token_usage_stats, name='token_usage_stats'),
    path('monitor/tokens/reset/', views.reset_token_usage, name='reset_token_usage'),
]
