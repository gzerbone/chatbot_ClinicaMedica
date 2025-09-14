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
    path('test/clear-context/', views.clear_context, name='clear_context'),
    path('test/calendar/', views.test_calendar_connection, name='test_calendar'),
    path('test/availability/<str:doctor_name>/', views.get_doctor_availability, name='get_doctor_availability'),
]
