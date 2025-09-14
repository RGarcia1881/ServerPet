import sys
import random
import serial
import time
import json
import re

# Variable de control para alternar entre modo de prueba y modo real
TEST_MODE = True

# --- Modo Real ---
# Configuración del puerto UART
PUERTO = '/dev/ttyAMA10'
BAUDRATE = 115200

def get_serial_connection():
    """Establece y devuelve una conexión serial real."""
    try:
        ser = serial.Serial(PUERTO, BAUDRATE, timeout=5)
        time.sleep(2)
        return ser
    except Exception as e:
        # Imprime el error al stderr para que la vista de Django lo capture.
        print(json.dumps({"error": f"Error al conectar con el puerto serial: {e}"}), file=sys.stderr)
        return None

# Sensores
sensores = {
    '1': 'PESO_A',
    '2': 'PESO_B',
    '3': 'DISTANCIA_A',
    '4': 'DISTANCIA_B'
}

def leer_datos_serial(filtro_etiqueta):
    """Lee datos del puerto serial (real o simulado) y los imprime como JSON."""
    valor_final = "No se recibió respuesta"
    if TEST_MODE:
        if filtro_etiqueta == 'PESO_A':
            valor_final = f"{random.randint(50, 200)} g"
        elif filtro_etiqueta == 'PESO_B':
            valor_final = f"{random.randint(10, 50)} g"
        elif filtro_etiqueta == 'DISTANCIA_A':
            valor_final = f"{random.randint(20, 100)} cm"
        elif filtro_etiqueta == 'DISTANCIA_B':
            valor_final = f"{random.randint(5, 30)} cm"
        else:
            print(json.dumps({"error": f"Sensor '{filtro_etiqueta}' no reconocido."}), file=sys.stderr)
            return
    else:
        ser = get_serial_connection()
        if not ser: return
        try:
            key_to_send = None
            for key, value in sensores.items():
                if value == filtro_etiqueta:
                    key_to_send = key
                    break
            if not key_to_send:
                print(json.dumps({"error": f"Sensor '{filtro_etiqueta}' no encontrado."}), file=sys.stderr)
                return
            
            ser.write(f"{key_to_send}\n".encode())
            inicio = time.time()
            while time.time() - inicio < 2:
                if ser.in_waiting > 0:
                    linea = ser.readline().decode('utf-8', errors='ignore').strip()
                    if filtro_etiqueta in linea:
                        valor_final = linea.split(':')[-1].strip()
                        break
        except Exception as e:
            print(json.dumps({"error": f"Error leyendo datos: {e}"}), file=sys.stderr)
        finally:
            if ser and ser.is_open: ser.close()
    
    # Imprime la respuesta como un objeto JSON
    print(json.dumps({filtro_etiqueta: valor_final}))


def activar_motor():
    """Envía el comando para activar el motor y devuelve un mensaje JSON."""
    if TEST_MODE:
        print(json.dumps({"message": "Comando de activación de motor ejecutado."}))
    else:
        ser = get_serial_connection()
        if not ser: return
        try:
            ser.write(b'r\n')
            print(json.dumps({"message": "Comando de activación de motor enviado."}))
        except Exception as e:
            print(json.dumps({"error": f"Error al activar el motor: {e}"}), file=sys.stderr)
        finally:
            if ser and ser.is_open: ser.close()

def activar_bomba():
    """Envía el comando para activar la bomba de agua y devuelve un mensaje JSON."""
    if TEST_MODE:
        print(json.dumps({"message": "Comando de activación de bomba ejecutado."}))
    else:
        ser = get_serial_connection()
        if not ser: return
        try:
            ser.write(b'b\n')
            print(json.dumps({"message": "Comando de activación de bomba enviado."}))
        except Exception as e:
            print(json.dumps({"error": f"Error al activar la bomba: {e}"}), file=sys.stderr)
        finally:
            if ser and ser.is_open: ser.close()


def calibrar_balanza_tara(nombre_balanza):
    """
    Paso 1: Inicia la rutina de calibración tarando la balanza.
    """
    if TEST_MODE:
        print(json.dumps({"status": "success", "message": "Modo de prueba: Balanza tarada. Ahora coloca el peso."}))
        return
    else:
        ser = get_serial_connection()
        if not ser:
            print(json.dumps({"status": "error", "message": "Error al conectar con la ESP32."}), file=sys.stderr)
            return
        
        try:
            if nombre_balanza.upper() == 'A':
                ser.write(b'c\n')
            elif nombre_balanza.upper() == 'B':
                ser.write(b'd\n')
            else:
                print(json.dumps({"status": "error", "message": "Nombre de balanza no válido. Use 'A' o 'B'."}), file=sys.stderr)
                return
            
            # Leer la respuesta de la ESP32 que indica que está lista
            inicio = time.time()
            response_line = "No se recibió respuesta."
            while time.time() - inicio < 5:
                if ser.in_waiting > 0:
                    response_line = ser.readline().decode('utf-8', errors='ignore').strip()
                    if "gramos" in response_line or "lista para calibrar" in response_line:
                         print(json.dumps({"status": "success", "message": "Balanza tarada. Por favor, coloca el peso conocido."}))
                         return

            print(json.dumps({"status": "error", "message": response_line}), file=sys.stderr)

        except Exception as e:
            print(json.dumps({"status": "error", "message": f"Error durante la calibración: {e}"}), file=sys.stderr)
        finally:
            if ser and ser.is_open: ser.close()


def calibrar_balanza_peso(nombre_balanza, peso_conocido):
    """
    Paso 2: Envía el peso conocido para finalizar la calibración.
    """
    if TEST_MODE:
        factor = "-613.43000"
        message = f"Balanza {nombre_balanza.upper()} calibrada. Nuevo factor: {factor} guardado en EEPROM."
        print(json.dumps({"status": "success", "message": message, "factor": factor}))
        return
    else:
        ser = get_serial_connection()
        if not ser:
            print(json.dumps({"status": "error", "message": "Error al conectar con la ESP32."}), file=sys.stderr)
            return

        try:
            if nombre_balanza.upper() == 'A':
                ser.write(b'c\n')
            elif nombre_balanza.upper() == 'B':
                ser.write(b'd\n')
            else:
                print(json.dumps({"status": "error", "message": "Nombre de balanza no válido. Use 'A' o 'B'."}), file=sys.stderr)
                return

            ser.write(f"{peso_conocido}\n".encode())
            
            inicio = time.time()
            response_line = "No se recibió respuesta final."
            while time.time() - inicio < 5:
                if ser.in_waiting > 0:
                    response_line = ser.readline().decode('utf-8', errors='ignore').strip()
                    if "calibrada" in response_line:
                        match = re.search(r"Nuevo factor: (.*?) guardado", response_line)
                        factor = match.group(1).strip() if match else "Desconocido"
                        print(json.dumps({"status": "success", "message": response_line, "factor": factor}))
                        return

            print(json.dumps({"status": "error", "message": response_line}), file=sys.stderr)

        except Exception as e:
            print(json.dumps({"status": "error", "message": f"Error durante la calibración: {e}"}), file=sys.stderr)
        finally:
            if ser and ser.is_open: ser.close()


# Esta sección permite que el script se ejecute desde la línea de comandos
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Uso: python esp32_controller.py <accion> [argumentos]"}), file=sys.stderr)
        sys.exit(1)

    accion = sys.argv[1]
    
    if accion == 'leer_datos_serial' and len(sys.argv) == 3:
        leer_datos_serial(sys.argv[2])
    elif accion == 'activar_motor':
        activar_motor()
    elif accion == 'activar_bomba':
        activar_bomba()
    elif accion == 'calibrar_balanza_tara' and len(sys.argv) == 3:
        calibrar_balanza_tara(sys.argv[2])
    elif accion == 'calibrar_balanza_peso' and len(sys.argv) == 4:
        calibrar_balanza_peso(sys.argv[2], sys.argv[3])
    else:
        print(json.dumps({"error": "Acción o argumentos inválidos."}), file=sys.stderr)
        sys.exit(1)
