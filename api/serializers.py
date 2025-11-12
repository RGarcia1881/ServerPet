from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from .models import User, Pet, Dispenser, Horario  # 🔥 Agregar Horario
import json
import re  # 🔥 Necesario para validar formato de hora

# --- Serializers Básicos ---

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = (
            'id', 
            'email', 
            'first_name', 
            'last_name', 
            'image', 
            'password' 
        )
        
        extra_kwargs = {
            'email': {
                'required': True, 
                'allow_blank': False, 
                'validators': [
                    UniqueValidator(
                        queryset=User.objects.all(), 
                        message="Este email ya está registrado."
                    )
                ]
            },
            'password': {'write_only': True} 
        }

    def create(self, validated_data):
        return super().create(validated_data)


# --- Pet Serializer ---

class PetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pet
        fields = '__all__'


# --- Dispenser Serializer (ACTUALIZADO) ---

class DispenserSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dispenser
        fields = '__all__'

    # 🔥 ACTUALIZAR: Cambiar 'timetable' por 'horarios'
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        
        # 🔥 CAMBIO: Ahora usamos 'horarios' en lugar de 'timetable'
        db_horarios = instance.horarios
        
        try:
            if db_horarios and db_horarios != 'null':
                representation['horarios'] = json.loads(db_horarios)
            else:
                representation['horarios'] = []
        except json.JSONDecodeError:
            representation['horarios'] = []
            
        return representation

    def to_internal_value(self, data):
        # 🔥 CAMBIO: Ahora usamos 'horarios' en lugar de 'timetable'
        horarios_list = data.get('horarios')

        if horarios_list is not None and isinstance(horarios_list, list):
            data['horarios'] = json.dumps(horarios_list)
        
        return super().to_internal_value(data)


# --- 🔥 NUEVO SERIALIZER: HorarioSerializer ---

class HorarioSerializer(serializers.ModelSerializer):
    
    # Campos de solo lectura para mostrar información relacionada
    mascota_nombre = serializers.CharField(source='mascota.name', read_only=True)
    dispensador_ubicacion = serializers.CharField(source='dispensador.ubication', read_only=True)
    usuario_email = serializers.CharField(source='usuario.email', read_only=True)  # 🔥 Nuevo campo
    
    class Meta:
        model = Horario
        fields = [
            'id', 
            'mascota', 'mascota_nombre',
            'dispensador', 'dispensador_ubicacion',
            'usuario', 'usuario_email',  # 🔥 Agregar usuario
            'horarios', 
            'creado_en', 'actualizado_en'
        ]
        read_only_fields = ['creado_en', 'actualizado_en', 'usuario']  # 🔥 usuario es de solo lectura
    
    def validate_horarios(self, value):
        """
        Validar que los horarios sean una lista de strings en formato HH:MM
        """
        if not isinstance(value, list):
            raise serializers.ValidationError("Los horarios deben ser una lista")
        
        for hora in value:
            if not isinstance(hora, str):
                raise serializers.ValidationError("Cada horario debe ser un string")
            # Validar formato HH:MM
            if not re.match(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$', hora):
                raise serializers.ValidationError(f"Formato de hora inválido: {hora}. Use formato HH:MM")
        
        return value
    
    def validate(self, data):
        """
        Validación adicional para asegurar que la mascota y dispensador coincidan
        """
        mascota = data.get('mascota')
        dispensador = data.get('dispensador')
        
        # Si no se proporciona dispensador, intentar asignar automáticamente
        if not dispensador and mascota:
            try:
                data['dispensador'] = mascota.dispenser
            except Dispenser.DoesNotExist:
                raise serializers.ValidationError({
                    'mascota': 'Esta mascota no tiene un dispensador asignado'
                })
        
        # 🔥 Asignar automáticamente el usuario de la mascota
        if mascota and not data.get('usuario'):
            data['usuario'] = mascota.user
        
        return data
    
    def create(self, validated_data):
        """
        Asegurar que el usuario se asigne automáticamente al crear
        """
        if 'usuario' not in validated_data and 'mascota' in validated_data:
            validated_data['usuario'] = validated_data['mascota'].user
        return super().create(validated_data)