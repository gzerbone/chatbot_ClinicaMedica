"""
URLs para API Gateway
"""
from django.urls import path
from . import views

app_name = 'api_gateway'

urlpatterns = [
    # Webhook do WhatsApp
    path('webhook/whatsapp/', views.whatsapp_webhook, name='whatsapp_webhook'),
    
    # Endpoints de teste (apenas para desenvolvimento)
    path('test/send-message/', views.send_test_message, name='send_test_message'),
    path('test/gemini/', views.test_gemini_connection, name='test_gemini'),
    path('test/intent/', views.test_intent_detection, name='test_intent'),
]
