"""
API URL configuration.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health_check, name='health_check'),
    path('webhook/transcribe/', views.transcribe_webhook, name='transcribe_webhook'),
    path('status/<str:task_id>/', views.task_status, name='task_status'),
]
