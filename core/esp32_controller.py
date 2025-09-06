import sys
import random
import serial
import time

# Variable de control para alternar entre modo de prueba y modo real
TEST_MODE = False

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
        print(f"Error al conectar con el puerto serial: {e}", file=sys.stderr)
        return None

# Sensores
sensores = {
    '1': 'PESO_A',
    '2': 'PESO_B',
    '3': 'DISTANCIA_A',
    '4': 'DISTANCIA_B'
}

def leer_datos_serial(filtro_etiqueta):
    """Lee datos del puerto serial (real o simulado)."""
    if TEST_MODE:
        # Lógica de prueba
        if filtro_etiqueta == 'PESO_A':
            valor_simulado = f"{random.randint(50, 200)} g"
        elif filtro_etiqueta == 'PESO_B':
            valor_simulado = f"{random.randint(10, 50)} g"
        elif filtro_etiqueta == 'DISTANCIA_A':
            valor_simulado = f"{random.randint(20, 100)} cm"
        elif filtro_etiqueta == 'DISTANCIA_B':
            valor_simulado = f"{random.randint(5, 30)} cm"
        else:
            print(f"Error: Sensor '{filtro_etiqueta}' no reconocido.", file=sys.stderr)
            return

        print(f"{filtro_etiqueta} => {valor_simulado}", file=sys.stdout)
        return
    else:
        # Lógica de Hardware Real
        ser = get_serial_connection()
        if not ser: return
        try:
            key_to_send = None
            for key, value in sensores.items():
                if value == filtro_etiqueta:
                    key_to_send = key
                    break

            if not key_to_send:
                print(f"Sensor '{filtro_etiqueta}' no encontrado.", file=sys.stderr)
                return

            ser.write(f"{key_to_send}\n".encode())
            inicio = time.time()
            while time.time() - inicio < 2:
                if ser.in_waiting > 0:
                    linea = ser.readline().decode('utf-8', errors='ignore').strip()
                    if filtro_etiqueta in linea:
                        valor = linea.split(':')[-1].strip()
                        print(f"{filtro_etiqueta} => {valor}", file=sys.stdout)
                        return
            print("⚠️ No se recibió respuesta.", file=sys.stderr)
        except Exception as e:
            print(f"Error leyendo datos: {e}", file=sys.stderr)
        finally:
            if ser and ser.is_open: ser.close()

def activar_motor():
    """Envía el comando para activar el motor (real o simulado)."""
    if TEST_MODE:
        print("Comando de activación de motor ejecutado.", file=sys.stdout)
    else:
        ser = get_serial_connection()
        if not ser: return
        try:
            ser.write(b'r\n')
            print("Comando de activación de motor ejecutado.", file=sys.stdout)
        except Exception as e:
            print(f"Error al activar el motor: {e}", file=sys.stderr)
        finally:
            if ser and ser.is_open: ser.close()

def activar_bomba():
    """Envía el comando para activar la bomba de agua (real o simulado)."""
    if TEST_MODE:
        print("Comando de activación de bomba ejecutado.", file=sys.stdout)
    else:
        ser = get_serial_connection()
        if not ser: return
        try:
            ser.write(b'b\n')
            print("Comando de activación de bomba ejecutado.", file=sys.stdout)
        except Exception as e:
            print(f"Error al activar la bomba: {e}", file=sys.stderr)
        finally:
            if ser and ser.is_open: ser.close()

def calibrar_balanza(nombre_balanza):
    """Inicia la rutina de calibración (real o simulado)."""
    if TEST_MODE:
        print(f"--- Modo de prueba: Iniciando calibración de Balanza {nombre_balanza.upper()} ---")
        print("Mensaje simulado: Coloca un peso conocido y escribe su valor en gramos:")
        input("Ingresa el peso y presiona Enter: ")
        print(f"Balanza {nombre_balanza.upper()} calibrada. Nuevo factor: -613.43000 guardado en EEPROM.")
        return
    else:
        ser = get_serial_connection()
        if not ser: return
        try:
            if nombre_balanza.upper() == 'A':
                ser.write(b'c\n')
            elif nombre_balanza.upper() == 'B':
                ser.write(b'd\n')
            else:
                print("Nombre de balanza no válido. Use 'A' o 'B'.", file=sys.stderr)
                return

            # Leer el prompt de la ESP32
            inicio = time.time()
            while time.time() - inicio < 5 and not "gramos" in ser.readline().decode('utf-8', errors='ignore'):
                pass

            peso_real = input("Ingresa el peso conocido (en gramos): ")
            ser.write(f"{peso_real}\n".encode())

            # Leer la respuesta final de la ESP32
            inicio = time.time()
            while time.time() - inicio < 5:
                if ser.in_waiting > 0:
                    linea = ser.readline().decode('utf-8', errors='ignore').strip()
                    print(linea)
                    if "calibrada" in linea: break
        except Exception as e:
            print(f"Error durante la calibración: {e}", file=sys.stderr)
        finally:
            if ser and ser.is_open: ser.close()

# Esta sección permite que el script se ejecute desde la línea de comandos
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python esp32_controller.py <accion> [argumentos]", file=sys.stderr)
        sys.exit(1)

    accion = sys.argv[1]

    if accion == 'leer_datos_serial' and len(sys.argv) == 3:
        leer_datos_serial(sys.argv[2])
    elif accion == 'activar_motor':
        activar_motor()
    elif accion == 'activar_bomba':
        activar_bomba()
    elif accion == 'calibrar_balanza' and len(sys.argv) == 3:
        calibrar_balanza(sys.argv[2])
    else:
        print("Acción o argumentos inválidos.", file=sys.stderr)
        sys.exit(1)
