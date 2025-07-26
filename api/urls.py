from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, PetViewSet, DispenserViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'pets', PetViewSet)
router.register(r'dispensers', DispenserViewSet)

urlpatterns = [
    path('', include(router.urls)),
]