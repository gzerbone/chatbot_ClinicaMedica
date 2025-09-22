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
    path('test/calendar/', views.test_calendar_connection, name='test_calendar'),
    path('test/availability/<str:doctor_name>/', views.get_doctor_availability, name='get_doctor_availability'),
    path('test/chatbot/', views.test_chatbot_service, name='test_chatbot'),
    path('test/intent-analysis/', views.test_intent_analysis, name='test_intent_analysis'),
    path('test/entity-extraction/', views.test_entity_extraction, name='test_entity_extraction'),
    path('test/check-data/', views.check_stored_data, name='check_stored_data'),
    path('test/handoff/', views.test_handoff_generation, name='test_handoff'),
]
