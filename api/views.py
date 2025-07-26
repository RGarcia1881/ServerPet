from django.shortcuts import render
from rest_framework import viewsets
from .models import User, Pet, Dispenser
from .serializers import UserSerializer, PetSerializer, DispenserSerializer
from drf_spectacular.utils import extend_schema

# Create your views here.
@extend_schema(tags=['Usuarios'])
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

@extend_schema(tags=['Mascotas'])
class PetViewSet(viewsets.ModelViewSet):
    queryset = Pet.objects.all()
    serializer_class = PetSerializer

@extend_schema(tags=['Dispensadores'])
class DispenserViewSet(viewsets.ModelViewSet):
    queryset = Dispenser.objects.all()
    serializer_class = DispenserSerializer
