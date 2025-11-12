from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet, PetViewSet, DispenserViewSet, HorarioViewSet,  # 🔥 Agregar HorarioViewSet
    ESP32ControlViewSet, RaspiControlViewSet, 
    RegisterView, LoginView
)

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'pets', PetViewSet, basename='pet')  # 🔥 Ya tenías este
router.register(r'dispensers', DispenserViewSet, basename='dispenser')  # 🔥 AGREGAR basename
router.register(r'horarios', HorarioViewSet, basename='horario')  # 🔥 NUEVA RUTA
router.register(r'esp32', ESP32ControlViewSet, basename='esp32')
router.register(r'raspi', RaspiControlViewSet, basename='raspi')

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('', include(router.urls)),
]