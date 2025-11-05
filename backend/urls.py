from django.contrib import admin
from django.urls import path, include
# --- [CORRECCIÓN CRÍTICA] Importaciones para servir archivos media en desarrollo
from django.conf import settings
from django.conf.urls.static import static

# Importaciones para la documentación de la API (drf-spectacular)
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    # 1. Panel de Administración de Django
    path('admin/', admin.site.urls),
    
    # 2. Rutas de la Aplicación 'api'
    # Nota: Se recomienda 'api/' para rutas base, o puedes mantener 'api/v1/' si prefieres versionar.
    path('api/', include('api.urls')), 
    
    # 3. Rutas de Documentación de la API (DRF-Spectacular)
    # Esquema en formato YAML/JSON
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    
    # Interfaz de usuario de Swagger
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    
    # Interfaz de usuario de Redoc (Añadido para completar la documentación)
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

# 4. --- [CORRECCIÓN CRÍTICA] Configuración para servir archivos MEDIA (imágenes) ---
# Esto es fundamental para que las imágenes de usuarios y mascotas se carguen en DEBUG.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)