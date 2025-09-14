import os
import sys
import json
import re
import subprocess
from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from .models import User, Pet, Dispenser
from .serializers import UserSerializer, PetSerializer, DispenserSerializer
from django.http import StreamingHttpResponse
import cv2
import threading

# IMPORTANT: Adjust this path to point to your modified script files.
# Esta es una forma robusta de manejar rutas relativas en Django.
# Se mueve dos niveles hacia arriba desde el directorio actual para llegar a la raíz del proyecto.
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

def run_script(script_path, action_name, *args):
    """
    Ejecuta un script de Python con los argumentos especificados y
    captura la salida estándar y de error. Se espera una salida en formato JSON.
    """
    try:
        command = [sys.executable, script_path, action_name] + list(args)
        # Aumenta el timeout para la grabación de video si es necesario
        timeout = 10
        if action_name == 'grabar_video':
            # Asume que el tercer argumento es la duración en segundos
            try:
                video_duration = int(args[0])
                timeout = video_duration + 15
            except (ValueError, IndexError):
                pass
        
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
        
        # Primero, revisamos si hay algo en stderr
        if result.stderr:
            try:
                # Si el error es un JSON, lo devolvemos
                error_output = json.loads(result.stderr.strip())
                return None, error_output
            except json.JSONDecodeError:
                # Si no es JSON, lo devolvemos como un error de texto simple
                return None, {"error": "El script falló al ejecutarse.", "detalles": result.stderr.strip()}

        # Ahora intentamos parsear la salida estándar como JSON
        try:
            output = json.loads(result.stdout.strip())
            return output, None
        except json.JSONDecodeError:
            return None, {"error": "Error de decodificación JSON en la salida.", "detalles": result.stdout.strip()}

    except FileNotFoundError:
        return None, {"error": f"No se encontró el archivo del script en la ruta: {script_path}"}
    except subprocess.TimeoutExpired:
        return None, {"error": "El script excedió el tiempo de espera."}
    except Exception as e:
        return None, {"error": f"Ocurrió un error inesperado: {str(e)}"}


# Create your views here.
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
        """
        Paso 1: Inicia la rutina de calibración tarando la balanza.
        La balanza debe estar vacía.
        """
        scale = request.data.get('scale')
        if not scale or scale.upper() not in ['A', 'B']:
            return Response({"error": "El campo 'scale' es obligatorio y debe ser 'A' o 'B'."}, status=400)
        
        output, error = run_script(SCRIPT_PATH_ESP32, 'calibrar_balanza_tara', scale.upper())
        if error:
            return Response(error, status=500)
        return Response(output)

    @action(detail=False, methods=['post'])
    def calibrate_set_weight(self, request):
        """
        Paso 2: Envía el peso conocido para finalizar la calibración.
        El peso debe estar sobre la balanza.
        """
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
        """
        Transmite video en vivo desde la cámara de la Raspberry Pi usando Motion JPEG.
        """
        def generate_frames():
            # Conecta a la cámara (usualmente /dev/video0)
            camera = cv2.VideoCapture(0)  
            if not camera.isOpened():
                return
            
            while True:
                success, frame = camera.read()
                if not success:
                    break
                
                # Codifica el fotograma como una imagen JPEG
                ret, buffer = cv2.imencode('.jpg', frame)
                if not ret:
                    continue
                
                # Devuelve el fotograma en formato de bytes
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            
            camera.release()
        
        return StreamingHttpResponse(generate_frames(), content_type='multipart/x-mixed-replace; boundary=frame')

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
