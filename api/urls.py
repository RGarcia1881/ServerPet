from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet, PetViewSet, DispenserViewSet, HorarioViewSet,
    ESP32ControlViewSet, RaspiControlViewSet, 
    RegisterView, LoginView
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')  # 🔥 Agregar basename
router.register(r'pets', PetViewSet, basename='pet')
router.register(r'dispensers', DispenserViewSet, basename='dispenser')
router.register(r'horarios', HorarioViewSet, basename='horario')
router.register(r'esp32', ESP32ControlViewSet, basename='esp32')
router.register(r'raspi', RaspiControlViewSet, basename='raspi')

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('', include(router.urls)),
]