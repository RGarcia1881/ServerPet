import serial
import time

# Configuración del puerto UART
PUERTO = '/dev/ttyAMA10'
BAUDRATE = 115200

ser = serial.Serial(PUERTO, BAUDRATE, timeout=1)
time.sleep(2)  # Espera a que el puerto esté listo

sensores = {
    '1': 'PESO_A',
    '2': 'PESO_B',
    '3': 'DISTANCIA_A',
    '4': 'DISTANCIA_B'
}

def mostrar_menu():
    print("\n=== MENÚ DE SENSORES DISPONIBLES ===")
    for key, value in sensores.items():
        print(f"{key}. {value}")
    print("5. MOTOR")
    print("6. BOMBA")
    print("7. SALIR")

def leer_datos_serial(filtro_etiqueta):
    try:
        print(f"\nSolicitando dato de {filtro_etiqueta}...\n")
        # Envía el código del sensor correspondiente
        for key, value in sensores.items():
            if value == filtro_etiqueta:
                ser.write(key.encode())
                ser.flush()
                break

        # Espera la respuesta
        inicio = time.time()
        while time.time() - inicio < 2:  # Timeout 2s
            if ser.in_waiting > 0:
                linea = ser.readline().decode('utf-8', errors='ignore').strip()
                if filtro_etiqueta in linea:
                    valor = linea.split(':')[-1].strip()
                    print(f"{filtro_etiqueta} => {valor}")
                    return
        print("⚠️ No se recibió respuesta.")
    except Exception as e:
        print(f"Error leyendo datos: {e}")

def activar_motor():
    try:
        print("Activando motor...")
        ser.write(b'r')
        ser.flush()
    except Exception as e:
        print(f"Error al activar el motor: {e}")

def activar_bomba():
    try:
        print("Activando bomba de agua...")
        ser.write(b'b')
        ser.flush()
    except Exception as e:
        print(f"Error al activar la bomba: {e}")

# Menú principal
try:
    while True:
        mostrar_menu()
        opcion = input("Selecciona una opción: ").strip()

        if opcion in sensores:
            leer_datos_serial(sensores[opcion])
        elif opcion == '5':
            activar_motor()
        elif opcion == '6':
            activar_bomba()
        elif opcion == '7':
            print("Saliendo del programa.")
            break
        else:
            print("Opción inválida. Intenta de nuevo.")
finally:
    if ser.is_open:
        ser.close()