"""
URL configuration for sahool_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.documentation import include_docs_urls

urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('api/docs/', include_docs_urls(title='Sahool API Documentation')),
    
    # API Endpoints - Version 1
    path('api/v1/users/', include('users.urls')),
    path('api/v1/farms/', include('farms.urls')),
    path('api/v1/fields/', include('fields.urls')),
    path('api/v1/crops/', include('crops.urls')),
    path('api/v1/iot/', include('iot.urls')),
    path('api/v1/irrigation/', include('irrigation.urls')),
    path('api/v1/marketplace/', include('marketplace.urls')),
    path('api/v1/ai/', include('ai.urls')),
    path('api/v1/satellite/', include('satellite.urls')),
    path('api/v1/weather/', include('weather.urls')),
    path('api/v1/finance/', include('finance.urls')),
    path('api/v1/analytics/', include('analytics.urls')),
    
    # DRF Auth
    path('api-auth/', include('rest_framework.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Customize admin site
admin.site.site_header = "منصة سهول للزراعة الذكية"
admin.site.site_title = "Sahool Admin"
admin.site.index_title = "لوحة التحكم"
