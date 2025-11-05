from rest_framework import serializers
from rest_framework.validators import UniqueValidator # <-- CORRECCIÓN: Importar desde validators
from .models import User, Pet, Dispenser
import json

# --- Serializers Básicos ---

class UserSerializer(serializers.ModelSerializer):
    # La contraseña solo se acepta como entrada, NUNCA se devuelve en la salida.
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        # Solo incluimos los campos necesarios para el registro y la visualización segura.
        fields = (
            'id', 
            'email', 
            'username', 
            'first_name', 
            'last_name', 
            'image', 
            'password' 
        )
        
        # Validaciones de la API: Aseguramos que el email sea único
        extra_kwargs = {
            'email': {
                'required': True, 
                'allow_blank': False, 
                'validators': [
                    # CORRECCIÓN: Usamos UniqueValidator importado directamente
                    UniqueValidator(
                        queryset=User.objects.all(), 
                        message="Este email ya está registrado."
                    )
                ]
            },
            # Ocultamos el hash de la contraseña de la salida 
            'password': {'write_only': True} 
        }

    # Sobreescribimos el método create para manejar el guardado del usuario
    def create(self, validated_data):
        # La vista de registro (RegisterView) es la responsable de hashear la contraseña
        # y guardar el usuario. Si la vista maneja el hasheo y el guardado, 
        # este método puede ser omitido o dejarse simple:
        return super().create(validated_data)


# --- Pet Serializer (Sin Cambios) ---

class PetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pet
        fields = '__all__'


# --- Dispenser Serializer (Sin Cambios) ---

class DispenserSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dispenser
        fields = '__all__'

    # 1. to_representation (SALIDA: De DB a API/Python)
    def to_representation(self, instance):
        # Deserializar el campo 'timetable' de JSON string a lista Python para la salida
        representation = super().to_representation(instance)
        
        db_string = instance.timetable
        
        try:
            if db_string and db_string != 'null':
                representation['timetable'] = json.loads(db_string)
            else:
                representation['timetable'] = []
        except json.JSONDecodeError:
            # En caso de datos corruptos, devolver una lista vacía
            representation['timetable'] = []
            
        return representation

    # 2. to_internal_value (ENTRADA: De API/Python a DB)
    def to_internal_value(self, data):
        # Serializar el campo 'timetable' de lista Python a JSON string para la DB
        timetable_list = data.get('timetable')

        if timetable_list is not None and isinstance(timetable_list, list):
            data['timetable'] = json.dumps(timetable_list)
        
        return super().to_internal_value(data)