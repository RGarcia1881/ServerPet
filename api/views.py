from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from .models import User, Pet, Dispenser
from .serializers import UserSerializer, PetSerializer, DispenserSerializer
import subprocess
import os
import re

# Esta es la ruta a tu script. Asegúrate de ajustarla si tu archivo
# esp32_controller.py no está en la misma carpeta que manage.py.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPT_PATH = os.path.join(PROJECT_ROOT, 'ServerPet', 'core', 'esp32_controller.py')


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

        try:
            command = ['python', SCRIPT_PATH, 'leer_datos_serial', sensor_label]
            result = subprocess.run(command, capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                return Response({"error": "El script falló al ejecutarse.", "detalles": result.stderr}, status=500)

            match = re.search(rf"{re.escape(sensor_label)} => (.*)", result.stdout)
            if match:
                value = match.group(1).strip()
                return Response({"sensor": sensor_label, "value": value})
            else:
                return Response({"error": "No se pudo analizar la salida del script.", "salida": result.stdout}, status=500)

        except FileNotFoundError:
            return Response({"error": "No se encontró el archivo del script."}, status=500)
        except subprocess.TimeoutExpired:
            return Response({"error": "El script excedió el tiempo de espera."}, status=500)
        except Exception as e:
            return Response({"error": f"Ocurrió un error inesperado: {e}"}, status=500)

    @action(detail=False, methods=['post'])
    def activate_motor(self, request):
        try:
            command = ['python', SCRIPT_PATH, 'activar_motor']
            result = subprocess.run(command, check=True, timeout=10, capture_output=True)
            return Response({"message": "Comando de activación de motor enviado.", "salida": result.stdout})
        except subprocess.CalledProcessError as e:
            return Response({"error": f"El script falló: {e.stderr}"}, status=500)
        except subprocess.TimeoutExpired:
            return Response({"error": "El script excedió el tiempo de espera."}, status=500)
        except FileNotFoundError:
            return Response({"error": "No se encontró el archivo del script."}, status=500)

    @action(detail=False, methods=['post'])
    def activate_pump(self, request):
        try:
            command = ['python', SCRIPT_PATH, 'activar_bomba']
            result = subprocess.run(command, check=True, timeout=10, capture_output=True)
            return Response({"message": "Comando de activación de bomba enviado.", "salida": result.stdout})
        except subprocess.CalledProcessError as e:
            return Response({"error": f"El script falló: {e.stderr}"}, status=500)
        except subprocess.TimeoutExpired:
            return Response({"error": "El script excedió el tiempo de espera."}, status=500)
        except FileNotFoundError:
            return Response({"error": "No se encontró el archivo del script."}, status=500)

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