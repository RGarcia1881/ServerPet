import os
import sys
import json
import re
import subprocess
from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from .models import User, Pet, Dispenser, Horario  # 🔥 Agregar Horario
from .serializers import UserSerializer, PetSerializer, DispenserSerializer, HorarioSerializer  # 🔥 Agregar HorarioSerializer
from django.http import StreamingHttpResponse

# --- LIBRERÍAS DE AUTENTICACIÓN ---
from django.contrib.auth.hashers import make_password, check_password
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

# --- HARDWARE LIBRARIES (MUST BE INSTALLED: pip install opencv-python) ---
import cv2
import threading

# IMPORTANT: Adjust this path to point to your modified script files.
SCRIPT_PATH_ESP32 = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'core', 'esp32_controller.py')
SCRIPT_PATH_RASPI = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'core', 'raspi_controller.py')

# Intenta importar las bibliotecas de DRF y DRF-Spectacular.
try:
    from rest_framework import viewsets
    from rest_framework.response import Response
    from drf_spectacular.utils import extend_schema
except ImportError as e:
    print(f"Error de importación: No se encontraron las bibliotecas de Django REST Framework o drf-spectacular. {e}", file=sys.stderr)
    raise

# --- Función Auxiliar para Ejecutar Scripts ---

def run_script(script_path, action_name, *args):
    """
    Ejecuta un script de Python con los argumentos especificados y
    captura la salida estándar y de error. Se espera una salida en formato JSON.
    """
    try:
        command = [sys.executable, script_path, action_name] + list(args)
        timeout = 10
        if action_name == 'grabar_video':
            try:
                video_duration = int(args[0])
                timeout = video_duration + 15
            except (ValueError, IndexError):
                pass
        
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
        
        if result.stderr:
            try:
                error_output = json.loads(result.stderr.strip())
                return None, error_output
            except json.JSONDecodeError:
                return None, {"error": "El script falló al ejecutarse.", "detalles": result.stderr.strip()}

        try:
            output = json.loads(result.stdout.strip())
            return output, None
        except json.JSONDecodeError:
            return {"message": result.stdout.strip()}, None

    except FileNotFoundError:
        return None, {"error": f"No se encontró el archivo del script en la ruta: {script_path}"}
    except subprocess.TimeoutExpired:
        return None, {"error": "El script excedió el tiempo de espera."}
    except Exception as e:
        return None, {"error": f"Ocurrió un error inesperado: {str(e)}"}


# --- VISTAS DE AUTENTICACIÓN ---

@extend_schema(tags=['Autenticación'])
class RegisterView(APIView):
    """
    Registra un nuevo usuario, hashea la contraseña y devuelve tokens JWT.
    """
    def post(self, request):
        data = request.data
        
        if 'password' in data:
            data['password'] = make_password(data['password'])
        
        serializer = UserSerializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'user_id': user.id,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(tags=['Autenticación'])
class LoginView(APIView):
    """
    Inicia sesión verificando el email y la contraseña, y devuelve tokens JWT.
    """
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response({"error": "Debe proporcionar email y contraseña."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "Credenciales inválidas."}, status=status.HTTP_401_UNAUTHORIZED)
        
        if check_password(password, user.password):
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'user_id': user.id,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        else:
            return Response({"error": "Credenciales inválidas."}, status=status.HTTP_401_UNAUTHORIZED)


# --- VISTAS DE CONTROL DE HARDWARE ---

@extend_schema(tags=['ESP32 Control'])
class ESP32ControlViewSet(viewsets.ViewSet):
    """
    Un ViewSet para controlar el ESP32 usando un script externo.
    """
    @action(detail=False, methods=['get'])
    def read_sensor(self, request):
        sensor_label = request.query_params.get('sensor', None)
        if not sensor_label:
            return Response({"error": "No se proporcionó la etiqueta del sensor."}, status=400)
        
        output, error = run_script(SCRIPT_PATH_ESP32, 'leer_datos_serial', sensor_label)
        if error:
            return Response(error, status=500)
        
        return Response(output)

    @action(detail=False, methods=['post'])
    def activate_motor(self, request):
        output, error = run_script(SCRIPT_PATH_ESP32, 'activar_motor')
        if error:
            return Response(error, status=500)
        return Response(output)

    @action(detail=False, methods=['post'])
    def activate_pump(self, request):
        output, error = run_script(SCRIPT_PATH_ESP32, 'activar_bomba')
        if error:
            return Response(error, status=500)
        return Response(output)

    @action(detail=False, methods=['post'])
    def calibrate_tare(self, request):
        scale = request.data.get('scale')
        if not scale or scale.upper() not in ['A', 'B']:
            return Response({"error": "El campo 'scale' es obligatorio y debe ser 'A' o 'B'."}, status=400)
        
        output, error = run_script(SCRIPT_PATH_ESP32, 'calibrar_balanza_tara', scale.upper())
        if error:
            return Response(error, status=500)
        return Response(output)

    @action(detail=False, methods=['post'])
    def calibrate_set_weight(self, request):
        scale = request.data.get('scale')
        known_weight = request.data.get('known_weight')

        if not scale or scale.upper() not in ['A', 'B'] or known_weight is None:
            return Response({"error": "Los campos 'scale' y 'known_weight' son obligatorios."}, status=400)
        
        output, error = run_script(SCRIPT_PATH_ESP32, 'calibrar_balanza_peso', scale.upper(), str(known_weight))
        if error:
            return Response(error, status=500)
        
        return Response(output)

@extend_schema(tags=['Raspberry Pi Control'])
class RaspiControlViewSet(viewsets.ViewSet):
    """
    Un ViewSet para controlar las funciones de la Raspberry Pi.
    """
    @action(detail=False, methods=['get'])
    def stream_video(self, request):
        def generate_frames():
            camera = cv2.VideoCapture(0)  
            if not camera.isOpened():
                print("Error: No se pudo abrir la cámara.", file=sys.stderr)
                return
            
            camera.set(cv2.CAP_PROP_FRAME_WIDTH, 720)
            camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            
            while True:
                success, frame = camera.read()
                if not success:
                    break
                
                ret, buffer = cv2.imencode('.jpg', frame)
                if not ret:
                    continue
                
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            
            camera.release()
        
        return StreamingHttpResponse(generate_frames(), content_type='multipart/x-mixed-replace; boundary=frame')
    
    @action(detail=False, methods=['post'])
    def reproducir_audio(self, request):
        if 'audio_file' not in request.FILES:
            return Response({"error": "No se proporcionó un archivo de audio."}, status=400)
        
        audio_file = request.FILES['audio_file']
        
        temp_dir = '/tmp/audio_uploads'
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
            
        temp_file_path = os.path.join(temp_dir, audio_file.name)
        
        try:
            with open(temp_file_path, 'wb+') as destination:
                for chunk in audio_file.chunks():
                    destination.write(chunk)
        except Exception as e:
            return Response({"error": f"Error al guardar el archivo temporal: {str(e)}"}, status=500)
        
        output, error = run_script(SCRIPT_PATH_RASPI, 'reproducir_audio', temp_file_path)
        
        try:
            os.remove(temp_file_path)
        except OSError as e:
            print(f"Error: {e.strerror} - {e.filename}")
        
        if error:
            return Response(error, status=500)
        
        return Response(output)


# --- VISTAS DE MODELOS ---

@extend_schema(tags=['Usuarios'])
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

@extend_schema(tags=['Mascotas'])
class PetViewSet(viewsets.ModelViewSet):
    serializer_class = PetSerializer
    
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Pet.objects.none()
        return Pet.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

@extend_schema(tags=['Dispensadores'])
class DispenserViewSet(viewsets.ModelViewSet):
    serializer_class = DispenserSerializer
    
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Dispenser.objects.none()
        return Dispenser.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@extend_schema(tags=['Horarios'])
class HorarioViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar horarios de dispensación.
    """
    serializer_class = HorarioSerializer
    
    def get_queryset(self):
        """
        Filtrar horarios por el usuario autenticado
        """
        if not self.request.user.is_authenticated:
            return Horario.objects.none()
        
        # 🔥 Ahora podemos filtrar directamente por usuario
        return Horario.objects.filter(usuario=self.request.user)
    
    def perform_create(self, serializer):
        """
        Validar que la mascota y dispensador pertenezcan al usuario
        """
        mascota = serializer.validated_data.get('mascota')
        dispensador = serializer.validated_data.get('dispensador')
        
        # Verificar que la mascota pertenezca al usuario
        if mascota.user != self.request.user:
            raise serializers.ValidationError({
                'mascota': 'No puedes asignar horarios a mascotas que no te pertenecen'
            })
        
        # Verificar que el dispensador pertenezca al usuario
        if dispensador and dispensador.user != self.request.user:
            raise serializers.ValidationError({
                'dispensador': 'No puedes usar dispensadores que no te pertenecen'
            })
        
        # 🔥 Asignar automáticamente el usuario autenticado
        serializer.save(usuario=self.request.user)
    
    def perform_update(self, serializer):
        """
        Mismas validaciones para actualizar
        """
        self.perform_create(serializer)