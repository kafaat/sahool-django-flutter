"""
URLs للذكاء الاصطناعي
"""
from django.urls import path
from . import views

app_name = 'ai'

urlpatterns = [
    # كشف الأمراض
    path('detect-disease/', views.detect_disease, name='detect_disease'),
    
    # قائمة الأمراض
    path('diseases/', views.list_diseases, name='list_diseases'),
    path('diseases/<str:disease_id>/', views.disease_info, name='disease_info'),
    
    # فحص الصحة
    path('health/', views.ai_health_check, name='health_check'),
]
