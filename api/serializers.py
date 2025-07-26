from rest_framework import serializers
from .models import User, Pet, Dispenser

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'
        extra_kwargs = {
            'password': {'write_only': True, 'help_text': 'Contraseña del usuario, se encripta al guardar.'},
            'email': {'help_text': 'Correo electrónico único del usuario.'},
        }


class PetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pet
        fields = '__all__'
        extra_kwargs = {
            'image': {'help_text': 'Imagen del perfil de la mascota.'},
            'weight': {'help_text': 'Peso en kilogramos.'},
            'age': {'help_text': 'Edad en años.'},
        }


class DispenserSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dispenser
        fields = '__all__'
        extra_kwargs = {
            'status': {'help_text': 'Estado activo o inactivo del dispensador.'},
            'timetable': {'help_text': 'Horario programado para dispensar comida/agua.'},
        }
