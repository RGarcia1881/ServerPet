from rest_framework import serializers
from .models import User, Pet, Dispenser
import json # Necesario para serializar/deserializar el TextField

# --- Serializers Básicos ---

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

class PetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pet
        fields = '__all__'


# --- Dispenser Serializer (Modificado para TextField) ---

class DispenserSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dispenser
        fields = '__all__'

    # 1. to_representation (SALIDA: De DB a API/Python)
    # Convierte la cadena JSON almacenada en el TextField a una lista de Python para el cliente.
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        
        # El campo timetable es un TextField, debemos cargarlo manualmente.
        db_string = instance.timetable # Esto es una cadena de texto JSON (e.g., '["10:00", "15:30"]')
        
        try:
            if db_string and db_string != 'null':
                # Convertimos la cadena JSON a una lista de Python
                representation['timetable'] = json.loads(db_string)
            else:
                representation['timetable'] = [] # Si es nulo o vacío, devolvemos una lista vacía
        except json.JSONDecodeError:
            # En caso de datos corruptos, devolvemos una lista vacía para evitar fallos
            representation['timetable'] = []
            
        return representation

    # 2. to_internal_value (ENTRADA: De API/Python a DB)
    # Convierte la lista de Python recibida del cliente a una cadena JSON para guardar en el TextField.
    def to_internal_value(self, data):
        # 1. Obtenemos el valor del timetable (que debe ser una lista de Python)
        timetable_list = data.get('timetable')

        # 2. Si es una lista, la convertimos a cadena JSON
        if timetable_list is not None and isinstance(timetable_list, list):
            data['timetable'] = json.dumps(timetable_list)
        
        # 3. Dejamos que el padre maneje el resto de la validación y guardado
        return super().to_internal_value(data)
