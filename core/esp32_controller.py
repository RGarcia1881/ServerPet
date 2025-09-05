import sys
import random
import serial
import time

# Variable de control para alternar entre modo de prueba y modo real
TEST_MODE = False

# --- Lógica de Hardware Real ---
# Configuración del puerto UART
PUERTO = '/dev/ttyAMA10'
BAUDRATE = 115200

def get_serial_connection():
    """Establece y devuelve una conexión serial real."""
    try:
        ser = serial.Serial(PUERTO, BAUDRATE, timeout=1)
        time.sleep(2)  # Espera a que el puerto esté listo
        return ser
    except Exception as e:
        print(f"Error al conectar con el puerto serial: {e}", file=sys.stderr)
        return None

sensores = {
    '1': 'PESO_A',
    '2': 'PESO_B',
    '3': 'DISTANCIA_A',
    '4': 'DISTANCIA_B'
}

def leer_datos_serial(filtro_etiqueta):
    """
    Lee datos del puerto serial (real o simulado).
    """
    if TEST_MODE:
        # --- Lógica de prueba ---
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
        # --- Lógica de Hardware Real ---
        ser = get_serial_connection()
        if not ser:
            return
        try:
            # Limpia el buffer de entrada para evitar lecturas "residuales"
            ser.flushInput()

            key_to_send = None
            for key, value in sensores.items():
                if value == filtro_etiqueta:
                    key_to_send = key
                    break
            
            if not key_to_send:
                print(f"Sensor '{filtro_etiqueta}' no encontrado.", file=sys.stderr)
                return

            ser.write(key_to_send.encode())
            ser.flush()

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
            if ser and ser.is_open:
                ser.close()

def activar_motor():
    """Envía el comando para activar el motor (real o simulado)."""
    if TEST_MODE:
        mensaje = "Comando de activación de motor ejecutado."
        print(mensaje, file=sys.stdout)
        return mensaje
    else:
        ser = get_serial_connection()
        if not ser:
            return
        try:
            ser.write(b'r')
            ser.flush()
            print("Comando de activación de motor ejecutado.", file=sys.stdout)
        except Exception as e:
            print(f"Error al activar el motor: {e}", file=sys.stderr)
        finally:
            if ser and ser.is_open:
                ser.close()

def activar_bomba():
    """Envía el comando para activar la bomba de agua (real o simulado)."""
    if TEST_MODE:
        mensaje = "Comando de activación de bomba ejecutado."
        print(mensaje, file=sys.stdout)
        return mensaje
    else:
        ser = get_serial_connection()
        if not ser:
            return
        try:
            ser.write(b'b')
            ser.flush()
            print("Comando de activación de bomba ejecutado.", file=sys.stdout)
        except Exception as e:
            print(f"Error al activar la bomba: {e}", file=sys.stderr)
        finally:
            if ser and ser.is_open:
                ser.close()

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
    else:
        print("Acción o argumentos inválidos.", file=sys.stderr)
        sys.exit(1)