import socket
import json
import mysql.connector
import time
import re
import os

# Configuración de red para el cable UTP / ServerBridgeX
HOST = '10.107.104.99'  # Puerta de enlace Ethernet
PORT = 1234             # Puerto de ServerBridgeX

FICHERO_PROFUNDIDAD = "profundidad.txt"

# ==============================================================================
# EXPRESIONES REGULARES (REGEX)
# ==============================================================================
PATRON_JSON_VALIDO = re.compile(r'^\s*\{.*\}\s*$')
PATRON_EXTRACTOR_SENSORES = re.compile(r'"(?P<clave>turbidez|temperatura|ph)":\s*(?P<valor>[-+]?\d*\.?\d+)')
PATRON_COMANDO_BOMBA = re.compile(r'^[0-5]$')
# ==============================================================================

def conectar_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="bd_turbidez"
    )

def obtener_profundidad_actual():
    """Lee el valor ingresado manualmente desde la interfaz mediante archivo plano"""
    if os.path.exists(FICHERO_PROFUNDIDAD):
        try:
            with open(FICHERO_PROFUNDIDAD, "r") as f:
                return float(f.read().strip())
        except Exception:
            return 0.0
    return 0.0

def guardar_en_db(turbidez, temperatura, ph):
    try:
        profundidad = obtener_profundidad_actual()

        conn = conectar_db()
        cursor = conn.cursor()

        # Inserts independientes en tablas físicas
        cursor.execute("INSERT INTO sensor_temperatura (valor) VALUES (%s)", (temperatura,))
        id_temp = cursor.lastrowid

        cursor.execute("INSERT INTO sensor_ph (valor) VALUES (%s)", (ph,))
        id_ph = cursor.lastrowid

        cursor.execute("INSERT INTO sensor_turbidez (valor) VALUES (%s)", (turbidez,))
        id_turb = cursor.lastrowid

        # Insert directo en 'lecturas' asociando la profundidad actual
        query_lectura = """
            INSERT INTO lecturas (id_temperatura, id_ph, id_turbidez, profundidad) 
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query_lectura, (id_temp, id_ph, id_turb, profundidad))

        conn.commit()
        print(f"[REGISTRO CREADO] Reg #{cursor.lastrowid} | Temp:{temperatura}°C | pH:{ph} | Turb:{turbidez}% | Profundidad:{profundidad}m")

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error en MySQL: {e}")

def procesar_comandos_pendientes(sock):
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, comando FROM comandos WHERE ejecutado = 0 ORDER BY id ASC")
        filas = cursor.fetchall()

        for id_cmd, cmd in filas:
            cmd_limpio = str(cmd).strip()

            if PATRON_COMANDO_BOMBA.match(cmd_limpio):
                sock.sendall(cmd_limpio.encode('utf-8'))
                print(f"[COMANDO ENVIADO] -> '{cmd_limpio}'")
                cursor.execute("UPDATE comandos SET ejecutado = 1 WHERE id = %s", (id_cmd,))
            else:
                cursor.execute("UPDATE comandos SET ejecutado = -1 WHERE id = %s", (id_cmd,))
                
            conn.commit()

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error procesando comandos: {e}")

def iniciar_servidor():
    print(f"Conectando a ServerBridgeX en {HOST}:{PORT}...")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((HOST, PORT))
            s.settimeout(0.5)
            print("Conectado con éxito. Escuchando datos e insertando profundidad fija...")
            
            buffer = ""
            while True:
                procesar_comandos_pendientes(s)

                try:
                    data = s.recv(1024).decode('utf-8')
                    if not data:
                        break
                    buffer += data
                    while "\n" in buffer:
                        linea, buffer = buffer.split("\n", 1)
                        linea = linea.strip()

                        if PATRON_JSON_VALIDO.match(linea):
                            coincidencias = PATRON_EXTRACTOR_SENSORES.findall(linea)
                            datos = {clave: float(valor) for clave, valor in coincidencias}

                            if all(k in datos for k in ("turbidez", "temperatura", "ph")):
                                guardar_en_db(
                                    datos["turbidez"],
                                    datos["temperatura"],
                                    datos["ph"]
                                )
                except socket.timeout:
                    pass
        except Exception as e:
            print(f"Error de conexión: {e}")

if __name__ == "__main__":
    iniciar_servidor()