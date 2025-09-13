from django.urls import path
from . import views

urlpatterns = [
    # Traditional form-based view
    path('', views.generate_text, name='generate_text'),
    path('generate/', views.generate_text, name='generate_text_alt'),
    
    # API endpoints
    path('api/chat/', views.chat_api, name='chat_api'),
    path('api/history/', views.chat_history_api, name='chat_history'),
    path('api/chat/<str:session_id>/', views.chat_messages_api, name='chat_messages'),
    path('api/chat/<str:session_id>/delete/', views.delete_chat_api, name='delete_chat'),
    path('api/health/', views.health_check, name='health_check'),
]