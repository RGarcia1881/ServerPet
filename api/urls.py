from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet, PetViewSet, DispenserViewSet, 
    ESP32ControlViewSet, RaspiControlViewSet, 
    RegisterView, LoginView # <-- ¡Importaciones añadidas!
)

# Creamos un router para los ViewSets de modelos
router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'pets', PetViewSet)
router.register(r'dispensers', DispenserViewSet)

# Los ViewSets de control de hardware también usan el router para las acciones
router.register(r'esp32-control', ESP32ControlViewSet, basename='esp32-control')
router.register(r'raspi-control', RaspiControlViewSet, basename='raspi-control')


urlpatterns = [
    # --- 1. Rutas de Autenticación (JWT) ---
    # Estas rutas apuntan a las clases RegisterView y LoginView
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    
    # --- 2. Rutas de Modelos y Control (Usando el Router) ---
    path('', include(router.urls)),
]
