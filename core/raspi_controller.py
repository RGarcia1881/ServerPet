import sys
import subprocess
import json
import os

def grabar_video(duracion_segundos, ruta_salida):
    """
    Graba un video usando ffmpeg.
    Se ejecuta sin pantalla y sin audio para evitar bloqueos.
    """
    if not isinstance(duracion_segundos, (int, float)) or duracion_segundos <= 0:
        return {"error": "La duración debe ser un número positivo."}, False

    if not isinstance(ruta_salida, str) or not ruta_salida:
        return {"error": "La ruta de salida es obligatoria."}, False
    
    # Asegúrate de que la carpeta de salida exista.
    directorio_salida = os.path.dirname(ruta_salida)
    if not os.path.exists(directorio_salida):
        os.makedirs(directorio_salida)

    # El comando de ffmpeg
    try:
        command = [
            'ffmpeg',
            '-f', 'v4l2',
            '-i', '/dev/video0',
            '-t', str(duracion_segundos),
            '-nostdin',       # Evita que intente leer de la entrada estándar.
            '-an',            # Desactiva la grabación de audio.
            '-y',             # Sobrescribe el archivo de salida si ya existe.
            ruta_salida
        ]
        
        # Ejecuta el comando
        result = subprocess.run(command, check=True, timeout=duracion_segundos + 5, capture_output=True, text=True)
        
        return {"message": f"Video grabado exitosamente en: {ruta_salida}", "detalles": result.stdout}, True
        
    except FileNotFoundError:
        return {"error": "ffmpeg no está instalado o no se encuentra en el PATH."}, False
    except subprocess.CalledProcessError as e:
        return {"error": "El comando de ffmpeg falló.", "detalles": e.stderr}, False
    except subprocess.TimeoutExpired:
        return {"error": "El comando de grabación excedió el tiempo de espera."}, False
    except Exception as e:
        return {"error": f"Ocurrió un error inesperado: {e}"}, False

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Uso: python raspi_controller.py <accion> [argumentos]"}), file=sys.stderr)
        sys.exit(1)

    accion = sys.argv[1]
    
    if accion == 'grabar_video' and len(sys.argv) == 4:
        # Se espera: accion, duracion, ruta_salida
        duracion_segundos = float(sys.argv[2])
        ruta_salida = sys.argv[3]
        
        output, success = grabar_video(duracion_segundos, ruta_salida)
        if success:
            print(json.dumps(output))
        else:
            print(json.dumps(output), file=sys.stderr)
    else:
        print(json.dumps({"error": "Acción o argumentos inválidos."}), file=sys.stderr)
        sys.exit(1)
