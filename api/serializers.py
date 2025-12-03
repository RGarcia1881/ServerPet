import base64
import uuid
from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from .models import User, Pet, Dispenser, Horario
import json
import re

# --- User Serializer ---
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

# --- Pet Serializer (ACTUALIZADO PARA MANEJAR BASE64) ---
class PetSerializer(serializers.ModelSerializer):
    # 🔥 NUEVO: Campo para recibir imagen en base64 desde el frontend
    image_base64 = serializers.CharField(
        write_only=True, 
        required=False, 
        allow_blank=True,
        help_text="Imagen en formato base64. Ej: data:image/jpeg;base64,XXXXX"
    )
    
    # 🔥 NUEVO: Campo para mostrar URL completa de la imagen
    image_url = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Pet
        fields = [
            'id', 
            'name', 
            'weight', 
            'age', 
            'race', 
            'image',        # Campo del modelo (solo lectura)
            'image_url',    # 🔥 NUEVO: URL completa
            'image_base64', # 🔥 NUEVO: Para recibir base64
            'user'
        ]
        read_only_fields = ['image', 'user', 'image_url']
    
    def get_image_url(self, obj):
        """Obtener URL completa de la imagen"""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None
    
    def validate(self, data):
        """Validaciones adicionales"""
        request = self.context.get('request')
        
        # Asegurar que el usuario esté autenticado (para updates)
        if request and hasattr(self, 'instance') and self.instance:
            if self.instance.user != request.user:
                raise serializers.ValidationError("No puedes modificar mascotas de otros usuarios")
        
        return data
    
    def create(self, validated_data):
        """Crear mascota con imagen en base64"""
        # Extraer imagen en base64 si viene
        image_base64 = validated_data.pop('image_base64', None)
        
        # Asignar usuario automáticamente
        request = self.context.get('request')
        if request and request.user:
            validated_data['user'] = request.user
        
        # Crear la mascota
        pet = Pet.objects.create(**validated_data)
        
        # Procesar imagen si viene
        self._process_image(pet, image_base64)
        
        return pet
    
    def update(self, instance, validated_data):
        """Actualizar mascota con imagen en base64"""
        # Extraer imagen en base64 si viene
        image_base64 = validated_data.pop('image_base64', None)
        
        # Actualizar campos normales
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Procesar imagen
        self._process_image(instance, image_base64)
        
        instance.save()
        return instance
    
    def _process_image(self, pet, image_base64):
        """Procesar imagen en base64"""
        print(f"🔍 [DEBUG] Recibiendo image_base64: {image_base64[:100] if image_base64 else 'None'}")
        
        if image_base64 is None:
            print("🔍 [DEBUG] image_base64 es None, no se procesa")
            return  # No hacer nada si no viene imagen
        
        if image_base64 == '':
            print("🔍 [DEBUG] image_base64 es string vacío, eliminando imagen")
            # String vacío = eliminar imagen existente
            if pet.image:
                pet.image.delete(save=False)
            pet.image = None
        elif image_base64.startswith('data:image'):
            try:
                print("🔍 [DEBUG] Procesando imagen base64...")
                # Decodificar base64
                format, imgstr = image_base64.split(';base64,')
                ext = format.split('/')[-1]  # jpeg, png, etc.
                
                print(f"🔍 [DEBUG] Formato: {format}, Extensión: {ext}")
                
                # Generar nombre único para el archivo
                filename = f"pet_{pet.id}_{uuid.uuid4().hex[:8]}.{ext}"
                print(f"🔍 [DEBUG] Nombre archivo: {filename}")
                
                # Decodificar base64 a bytes
                image_bytes = base64.b64decode(imgstr)
                print(f"🔍 [DEBUG] Tamaño imagen: {len(image_bytes)} bytes")
                
                # Crear archivo de contenido
                data = ContentFile(image_bytes, name=filename)
                
                # Eliminar imagen anterior si existe
                if pet.image:
                    print(f"🔍 [DEBUG] Eliminando imagen anterior: {pet.image.name}")
                    pet.image.delete(save=False)
                
                # Guardar nueva imagen
                print(f"🔍 [DEBUG] Guardando nueva imagen...")
                pet.image.save(filename, data, save=False)
                print(f"✅ [DEBUG] Imagen guardada exitosamente: {pet.image.name}")
                
            except Exception as e:
                print(f"❌ [DEBUG] Error procesando imagen base64: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"⚠️ [DEBUG] Formato de imagen no válido: {image_base64[:100]}...")
        
    def to_representation(self, instance):
        """Personalizar representación para el frontend"""
        representation = super().to_representation(instance)
        
        # Mantener compatibilidad: también incluir 'image' como URL
        if 'image_url' in representation and representation['image_url']:
            representation['image'] = representation['image_url']
        else:
            representation['image'] = None
        
        return representation

# --- Dispenser Serializer (ACTUALIZADO CON CAMPOS BOOLEAN) ---
class DispenserSerializer(serializers.ModelSerializer):
    # Campos booleanos explícitos para mejor manejo en el frontend
    status_display = serializers.SerializerMethodField(read_only=True)
    fp_display = serializers.SerializerMethodField(read_only=True)
    wp_display = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Dispenser
        fields = [
            'id',
            'ubication',
            'status',           # BooleanField
            'status_display',   # Campo adicional para display
            'FC',
            'WC',
            'FP',              # BooleanField  
            'fp_display',      # Campo adicional para display
            'WP',              # BooleanField
            'wp_display',      # Campo adicional para display
            'horarios',
            'user',
            'pet'
        ]

    def get_status_display(self, obj):
        """Devuelve 'Activo' o 'Inactivo' para el frontend"""
        return "Activo" if obj.status else "Inactivo"
    
    def get_fp_display(self, obj):
        """Devuelve 'Habilitado' o 'Deshabilitado' para FP"""
        return "Habilitado" if obj.FP else "Deshabilitado"
    
    def get_wp_display(self, obj):
        """Devuelve 'Habilitado' o 'Deshabilitado' para WP"""
        return "Habilitado" if obj.WP else "Deshabilitado"

    # Validación para campos booleanos
    def validate_status(self, value):
        """Asegurar que status sea booleano"""
        if not isinstance(value, bool):
            raise serializers.ValidationError("El status debe ser verdadero o falso")
        return value

    def validate_FP(self, value):
        """Asegurar que FP sea booleano"""
        if not isinstance(value, bool):
            raise serializers.ValidationError("FP debe ser verdadero o falso")
        return value

    def validate_WP(self, value):
        """Asegurar que WP sea booleano"""
        if not isinstance(value, bool):
            raise serializers.ValidationError("WP debe ser verdadero o falso")
        return value

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        
        # Manejo de horarios
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
        horarios_list = data.get('horarios')

        if horarios_list is not None and isinstance(horarios_list, list):
            data['horarios'] = json.dumps(horarios_list)
        
        return super().to_internal_value(data)

# --- HorarioSerializer (ACTUALIZADO) ---
class HorarioSerializer(serializers.ModelSerializer):
    
    # Campos de solo lectura para mostrar información relacionada
    mascota_nombre = serializers.CharField(source='mascota.name', read_only=True)
    dispensador_ubicacion = serializers.CharField(source='dispensador.ubication', read_only=True)
    usuario_email = serializers.CharField(source='usuario.email', read_only=True)
    
    # Campos para mostrar el estado del dispensador como string
    dispensador_status = serializers.BooleanField(source='dispensador.status', read_only=True)
    dispensador_status_display = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Horario
        fields = [
            'id', 
            'mascota', 'mascota_nombre',
            'dispensador', 'dispensador_ubicacion', 'dispensador_status', 'dispensador_status_display',
            'usuario', 'usuario_email',
            'horarios', 
            'creado_en', 'actualizado_en'
        ]
        read_only_fields = ['creado_en', 'actualizado_en', 'usuario']
    
    def get_dispensador_status_display(self, obj):
        """Devuelve el status del dispensador como string para display"""
        return "Activo" if obj.dispensador.status else "Inactivo"
    
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
        
        # Asignar automáticamente el usuario de la mascota
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