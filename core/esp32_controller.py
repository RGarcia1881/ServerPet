import sys
import serial
import time

# Configuración del puerto UART
PUERTO = '/dev/ttyAMA10'
BAUDRATE = 115200

def get_serial_connection():
    """Establece y devuelve una conexión serial."""
    try:
        ser = serial.Serial(PUERTO, BAUDRATE, timeout=5)
        time.sleep(2)
        return ser
    except Exception as e:
        print(f"Error al conectar con el puerto serial: {e}", file=sys.stderr)
        return None

def leer_datos_serial(filtro_etiqueta):
    """Lee datos del puerto serial para un sensor específico."""
    ser = get_serial_connection()
    if not ser:
        return
    try:
        if filtro_etiqueta == 'PESO_A':
            key_to_send = '1'
        elif filtro_etiqueta == 'PESO_B':
            key_to_send = '2'
        elif filtro_etiqueta == 'DISTANCIA_A':
            key_to_send = '3'
        elif filtro_etiqueta == 'DISTANCIA_B':
            key_to_send = '4'
        else:
            print(f"Sensor '{filtro_etiqueta}' no reconocido.", file=sys.stderr)
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
    """Envía el comando para activar el motor."""
    ser = get_serial_connection()
    if not ser:
        return
    try:
        ser.write(b'r')
        ser.flush()
        print("Comando de activación de motor enviado.", file=sys.stdout)
    except Exception as e:
        print(f"Error al activar el motor: {e}", file=sys.stderr)
    finally:
        if ser and ser.is_open:
            ser.close()

def activar_bomba():
    """Envía el comando para activar la bomba de agua."""
    ser = get_serial_connection()
    if not ser:
        return
    try:
        ser.write(b'b')
        ser.flush()
        print("Comando de activación de bomba enviado.", file=sys.stdout)
    except Exception as e:
        print(f"Error al activar la bomba: {e}", file=sys.stderr)
    finally:
        if ser and ser.is_open:
            ser.close()

def calibrar_balanza(nombre):
    """Inicia la rutina de calibración de una balanza."""
    ser = get_serial_connection()
    if not ser:
        return
    try:
        if nombre.upper() == 'A':
            ser.write(b'c')
        elif nombre.upper() == 'B':
            ser.write(b'd')
        else:
            print("Nombre de balanza no válido. Use 'A' o 'B'.", file=sys.stderr)
            return
        
        print("Esperando instrucciones de la ESP32...")
        time.sleep(2)
        
        while ser.in_waiting > 0:
            print(ser.readline().decode('utf-8', errors='ignore').strip())
        
        try:
            peso_real = input("Ingresa el valor del peso (en gramos) y presiona Enter: ")
            ser.write(f"{peso_real}\n".encode())
            ser.flush()
        except Exception:
            print("Entrada de usuario no válida.", file=sys.stderr)
            return
        
        inicio = time.time()
        while time.time() - inicio < 5:
            if ser.in_waiting > 0:
                linea = ser.readline().decode('utf-8', errors='ignore').strip()
                print(linea)
                if "Factor calculado" in linea:
                    break
        print("Calibración finalizada.")
    except Exception as e:
        print(f"Error durante la calibración: {e}", file=sys.stderr)
    finally:
        if ser and ser.is_open:
            ser.close()

def debug_all():
    """Ejecuta una secuencia de comandos de prueba."""
    print("--- Iniciando prueba de funcionalidad ---")
    leer_datos_serial('PESO_A')
    leer_datos_serial('PESO_B')
    leer_datos_serial('DISTANCIA_A')
    leer_datos_serial('DISTANCIA_B')
    activar_motor()
    activar_bomba()
    print("--- Prueba completada ---")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python3 esp32_controller.py <accion> [argumentos]", file=sys.stderr)
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
    elif accion == 'debug':
        debug_all()
    else:
        print("Acción o argumentos inválidos.", file=sys.stderr)
        sys.exit(1)