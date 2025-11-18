from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

from users.views import UserViewSet, CustomTokenObtainPairView
from farms.views import FarmViewSet, CropViewSet
from fields.views import FieldViewSet, IrrigationScheduleViewSet
from iot.views import (
    IoTDeviceViewSet,
    SensorViewSet,
    ActuatorViewSet,
    SensorReadingViewSet
)

# إعداد Swagger/OpenAPI
schema_view = get_schema_view(
    openapi.Info(
        title="Sahool Smart Agriculture API",
        default_version='v1',
        description="منصة سهول الذكية للزراعة المستدامة - API Documentation",
        terms_of_service="https://www.sahool.com/terms/",
        contact=openapi.Contact(email="contact@sahool.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

# إعداد Router
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'farms', FarmViewSet, basename='farm')
router.register(r'crops', CropViewSet, basename='crop')
router.register(r'fields', FieldViewSet, basename='field')
router.register(r'irrigation-schedules', IrrigationScheduleViewSet, basename='irrigation-schedule')
router.register(r'iot-devices', IoTDeviceViewSet, basename='iot-device')
router.register(r'sensors', SensorViewSet, basename='sensor')
router.register(r'actuators', ActuatorViewSet, basename='actuator')
router.register(r'sensor-readings', SensorReadingViewSet, basename='sensor-reading')

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # Authentication
    path('api/auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # API Routes
    path('api/', include(router.urls)),
]

# إضافة ملفات الوسائط في وضع التطوير
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
