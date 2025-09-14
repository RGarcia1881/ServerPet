from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, PetViewSet, DispenserViewSet, ESP32ControlViewSet, RaspiControlViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'pets', PetViewSet)
router.register(r'dispensers', DispenserViewSet)
router.register(r'esp32', ESP32ControlViewSet, basename='esp32-control')
router.register(r'raspi', RaspiControlViewSet, basename='raspi-control')

urlpatterns = [
    path('', include(router.urls)),
]
