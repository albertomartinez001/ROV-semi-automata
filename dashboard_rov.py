import streamlit as st
import pandas as pd
import mysql.connector
import time
import os

st.set_page_config(page_title="Dashboard ROV NEMO", page_icon="⚓", layout="wide")

FICHERO_PROFUNDIDAD = "profundidad.txt"

# Estilos CSS
st.markdown("""
<style>
    .sensor-card {
        padding: 18px 20px;
        border-radius: 14px;
        margin-bottom: 10px;
        backdrop-filter: blur(8px);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4);
    }
    .sensor-title { font-size: 0.9rem; font-weight: 700; text-transform: uppercase; margin-bottom: 8px; }
    .sensor-value { font-size: 2.3rem; font-weight: 800; line-height: 1.1; }
    .sensor-unit { font-size: 1.1rem; font-weight: 500; opacity: 0.85; }
    
    .card-turbidez { background: linear-gradient(135deg, rgba(0, 164, 214, 0.25) 0%, rgba(10, 22, 36, 0.9) 100%); border-left: 6px solid #00a4d6; color: #ffffff; }
    .card-temperatura { background: linear-gradient(135deg, rgba(255, 75, 75, 0.25) 0%, rgba(36, 14, 18, 0.9) 100%); border-left: 6px solid #ff4b4b; color: #ffffff; }
    .card-ph { background: linear-gradient(135deg, rgba(156, 39, 176, 0.25) 0%, rgba(30, 14, 36, 0.9) 100%); border-left: 6px solid #9c27b0; color: #ffffff; }
    .card-profundidad { background: linear-gradient(135deg, rgba(0, 230, 118, 0.25) 0%, rgba(10, 36, 22, 0.9) 100%); border-left: 6px solid #00e676; color: #ffffff; }
</style>
""", unsafe_allow_html=True)

posibles_nombres = ["logo.JPEG", "logo.jpeg", "logo.jpg", "logo.png"]
ruta_logo = next((n for n in posibles_nombres if os.path.exists(n)), None)

col_logo, col_titulo = st.columns([1, 5])
with col_logo:
    if ruta_logo: st.image(ruta_logo, width=130)

with col_titulo:
    st.title("Centro de Control - ROV Submarino NEMO")
    st.markdown("**NEMO** — *Telemetría y Registro Manual de Profundidad*")

st.markdown("---")

def conectar_db():
    return mysql.connector.connect(host="localhost", user="root", password="", database="bd_turbidez")

def enviar_comando_bomba(comando_char):
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO comandos (comando) VALUES (%s)", (comando_char,))
        conn.commit()
        cursor.close()
        conn.close()
        st.toast(f"Comando enviado: {comando_char}", icon="🚀")
    except Exception as e:
        st.error(f"Error al enviar comando: {e}")

def leer_profundidad_archivo():
    if os.path.exists(FICHERO_PROFUNDIDAD):
        try:
            with open(FICHERO_PROFUNDIDAD, "r") as f:
                return float(f.read().strip())
        except Exception:
            return 0.0
    return 0.0

def guardar_profundidad_archivo(valor):
    try:
        with open(FICHERO_PROFUNDIDAD, "w") as f:
            f.write(str(valor))
        st.toast(f"Profundidad ajustada a {valor} m. Las siguientes lecturas llevarán este valor.", icon="📍")
    except Exception as e:
        st.error(f"Error al guardar profundidad: {e}")

def obtener_historial():
    try:
        conn = conectar_db()
        query = """
            SELECT 
                l.id,
                l.fecha_registro,
                t.valor AS temperatura,
                p.valor AS ph,
                tb.valor AS turbidez,
                l.profundidad
            FROM lecturas l
            INNER JOIN sensor_temperatura t ON l.id_temperatura = t.id
            INNER JOIN sensor_ph p ON l.id_ph = p.id
            INNER JOIN sensor_turbidez tb ON l.id_turbidez = tb.id
            ORDER BY l.id DESC LIMIT 50
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df.iloc[::-1].reset_index(drop=True)
    except Exception:
        return pd.DataFrame()

# CONTROLES SUPERIORES
ctrl_col1, ctrl_col2 = st.columns([1, 2])

with ctrl_col1:
    with st.container(border=True):
        st.subheader("📍 Marca del Cable (Profundidad)")
        prof_actual = leer_profundidad_archivo()
        nueva_prof = st.number_input(
            "Ingrese metros de cable sumergidos:",
            min_value=0.0, max_value=100.0, step=0.5,
            value=float(prof_actual)
        )
        if st.button("Fijar Profundidad Actual", use_container_width=True):
            guardar_profundidad_archivo(nueva_prof)

with ctrl_col2:
    with st.container(border=True):
        st.subheader("⚙ Control de Bombas")
        b_col1, b_col2, b_col3, b_col4, b_col5, b_col6 = st.columns(6)
        if b_col1.button("▶️ B1", use_container_width=True): enviar_comando_bomba('1')
        if b_col2.button("▶️ B2", use_container_width=True): enviar_comando_bomba('2')
        if b_col3.button("🔥 AMBAS", use_container_width=True): enviar_comando_bomba('3')
        if b_col4.button("⏹️ B1", use_container_width=True): enviar_comando_bomba('4')
        if b_col5.button("⏹️ B2", use_container_width=True): enviar_comando_bomba('5')
        if b_col6.button("🛑 OFF", type="primary", use_container_width=True): enviar_comando_bomba('0')

st.markdown("---")

placeholder = st.empty()

while True:
    df = obtener_historial()
    
    if not df.empty:
        with placeholder.container():
            ultimo = df.iloc[-1]
            
            # Tarjetas del último registro
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f'<div class="sensor-card card-turbidez"><div class="sensor-title">💧 Turbidez</div><div class="sensor-value">{ultimo["turbidez"]} <span class="sensor-unit">%</span></div></div>', unsafe_allow_html=True)
            with col2:
                st.markdown(f'<div class="sensor-card card-temperatura"><div class="sensor-title">🌡️ Temperatura</div><div class="sensor-value">{ultimo["temperatura"]} <span class="sensor-unit">°C</span></div></div>', unsafe_allow_html=True)
            with col3:
                st.markdown(f'<div class="sensor-card card-ph"><div class="sensor-title">🧪 Nivel pH</div><div class="sensor-value">{ultimo["ph"]}</div></div>', unsafe_allow_html=True)
            with col4:
                st.markdown(f'<div class="sensor-card card-profundidad"><div class="sensor-title">⚓ Profundidad Registrada</div><div class="sensor-value">{ultimo["profundidad"]} <span class="sensor-unit">m</span></div></div>', unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Gráficas
            g1, g2, g3, g4 = st.columns(4)
            with g1:
                with st.container(border=True):
                    st.subheader("Turbidez (%)")
                    st.line_chart(df, y="turbidez", color="#00a4d6")
            with g2:
                with st.container(border=True):
                    st.subheader("Temperatura (°C)")
                    st.line_chart(df, y="temperatura", color="#ff4b4b")
            with g3:
                with st.container(border=True):
                    st.subheader("Nivel de pH")
                    st.line_chart(df, y="ph", color="#9c27b0")
            with g4:
                with st.container(border=True):
                    st.subheader("Profundidad Histórica (m)")
                    st.line_chart(df, y="profundidad", color="#00e676")
                
            st.caption(f"Última Lectura N° {ultimo['id']} | Timestamp: {ultimo['fecha_registro']}")
    else:
        st.warning("Esperando lecturas de la base de datos...")
        
    time.sleep(5)
    st.rerun()