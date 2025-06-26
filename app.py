# app.py
import streamlit as st
import pandas as pd
import numpy as np
import random
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# -----------------------------
# FUNCION PARA GUARDAR RESULTADOS EN GOOGLE SHEETS
# -----------------------------
def guardar_resultado_en_sheets(periodo_perdida, consumos):
    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credenciales.json", scope)
    client = gspread.authorize(creds)

    sheet = client.open("EconomiaCaoticaResultados").sheet1

    fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fila = [fecha_hora, periodo_perdida] + consumos
    sheet.append_row(fila)

# -----------------------------
# CARGA DE DATOS FIJOS DEL JUEGO
# -----------------------------
data = {
    "Periodo": list(range(1, 21)),
    "IPC": [
        100.00, 105.00, 111.30, 119.09, 128.62,
        140.20, 154.22, 171.18, 191.73, 216.65,
        246.98, 284.03, 330.47, 388.65, 461.61,
        553.93, 670.26, 817.71, 1004.78, 1245.93
    ],
    "Inflacion": [
        5.00, 5.00, 6.00, 7.00, 8.00,
        9.00, 10.00, 11.00, 12.00, 13.00,
        14.00, 15.00, 16.35, 17.61, 18.77,
        20.00, 21.00, 22.00, 22.88, 24.00
    ],
    "Gasto_minimo": [
        650.00, 682.50, 716.63, 759.62, 812.79,
        877.83, 956.87, 1052.55, 1168.30, 1308.56,
        1478.64, 1685.64, 1938.50, 2255.46, 2652.54,
        3150.49, 3780.57, 4574.52, 5580.87, 6857.62
    ],
    "Sueldo": [
        1000.00, 1000.00, 1000.00, 1000.00, 1000.00,
        1100.00, 1100.00, 1100.00, 1100.00, 1100.00,
        1250.00, 1250.00, 1250.00, 1250.00, 1250.00,
        1500.00, 1500.00, 1500.00, 1500.00, 1500.00
    ],
    "PBI": [
        100.00, 97.00, 98.80, 93.50, 91.20,
        94.80, 96.20, 92.00, 94.30, 90.00,
        93.60, 95.00, 91.00, 88.30, 91.90,
        90.10, 92.50, 93.00, 91.25, 89.00
    ],
    "CRECI": [
        2.00, -3.00, 1.86, -5.36, -2.46,
        3.95, 1.48, -4.37, 2.50, -4.56,
        4.00, 1.50, -4.21, -2.97, 4.08,
        -1.96, 2.66, 0.54, -1.88, -2.47
    ]
}

# -----------------------------
# SETUP INICIAL
# -----------------------------
df = pd.DataFrame(data)
ahorro_inicial = 800.00

if "periodo_actual" not in st.session_state:
    st.session_state.periodo_actual = 1
    st.session_state.ahorro = ahorro_inicial
    st.session_state.estado_banco = "Abierto"
    st.session_state.historial = []
    st.session_state.perdio = False

# -----------------------------
# FUNCIONES
# -----------------------------
def procesar_consumo(consumo_usuario: int):
    periodo = st.session_state.periodo_actual
    fila = df.iloc[periodo - 1]

    gasto_minimo = fila["Gasto_minimo"]
    sueldo = fila["Sueldo"]
    ahorro = st.session_state.ahorro

    if sueldo + ahorro < gasto_minimo:
        st.session_state.perdio = True
        return

    nuevo_ahorro = ahorro

    if consumo_usuario < gasto_minimo:
        diferencia = gasto_minimo - consumo_usuario
        penalizacion = diferencia * 0.10
        total_retiro = diferencia + penalizacion

        if total_retiro > ahorro:
            st.session_state.perdio = True
            return
        else:
            nuevo_ahorro -= total_retiro
    else:
        sobrante = sueldo - consumo_usuario
        nuevo_ahorro += sobrante

    if st.session_state.estado_banco.startswith("Cerrado"):
        nuevo_ahorro *= 0.95

    st.session_state.ahorro = round(nuevo_ahorro, 2)

    st.session_state.historial.append({
        "Periodo": periodo,
        "Consumo": consumo_usuario,
        "Ahorro": round(nuevo_ahorro, 2),
        "Estado_banco": st.session_state.estado_banco
    })

def actualizar_estado_banco():
    periodo = st.session_state.periodo_actual

    if periodo == 1:
        st.session_state.estado_banco = "Abierto"
        return

    creci_anterior = df.iloc[periodo - 2]["CRECI"]

    prob_cierre = 0
    if creci_anterior < -4.00:
        prob_cierre = 0.5
    elif creci_anterior <= -2.00:
        prob_cierre = 0.3

    st.session_state.estado_banco = "Cerrado🟥🟥🟥" if random.random() < prob_cierre else "Abierto 🟩🟩🟩"

def reiniciar_juego():
    for key in st.session_state.keys():
        del st.session_state[key]
    st.rerun()

# -----------------------------
# INTERFAZ DE USUARIO
# -----------------------------
periodo = st.session_state.periodo_actual
fila_actual = df.iloc[periodo - 1]

st.title("\ud83d\udca5 Econom\u00eda ca\u00f3tica")
st.markdown(f"## Periodo actual: {periodo}")

st.markdown("Ingrese la cantidad de consumo para el periodo:")
consumo = st.number_input(" ", min_value=0, step=1, format="%d", key="input_consumo")

col1, col2 = st.columns([1, 1])
with col1:
    if st.button("Aceptar", use_container_width=True):
        if not st.session_state.perdio:
            procesar_consumo(consumo)
            if not st.session_state.perdio:
                actualizar_estado_banco()
                st.session_state.periodo_actual += 1
                st.rerun()
with col2:
    if st.button("Reiniciar", use_container_width=True):
        reiniciar_juego()

if st.session_state.perdio:
    periodo_final = st.session_state.periodo_actual
    st.markdown(f"""
    <div style="padding: 1rem; border: 2px solid red; border-radius: 10px; background-color: #212f3d ;">
        <h3 style="color: red; text-align: center;">\u2618\ufe0f\u2618\ufe0f \u00a1Perdiste! \u2618\ufe0f\u2618\ufe0f</h3>
        <p style="text-align: center; font-size: 18px;">
            Sobreviviste hasta el periodo:<br>
            <span style="font-size: 48px; font-weight: bold; color: white;">{periodo_final}</span>
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Guardar resultados al perder
    consumos = [item["Consumo"] for item in st.session_state.historial]
    guardar_resultado_en_sheets(periodo_final, consumos)

    if periodo_final <= 5:
        ruta_imagen = "pokemons/flojo.png"  
    elif 6 <= periodo_final <= 9:
        ruta_imagen = "pokemons/agresivo.png"
    elif 10 <= periodo_final <= 14:
        ruta_imagen = "pokemons/normal.png"
    elif 15 <= periodo_final <= 17:
        ruta_imagen = "pokemons/miedoso.png"
    else:
        ruta_imagen = "pokemons/inteligente.png"

    st.image(ruta_imagen, caption="Tu compa\u00f1ero de la ca\u00edda...", use_container_width=True)

    st.stop()

# -----------------------------
# VISUALIZACI\u00d3N DE VARIABLES\ud83d\udcca\ud83d\udcca\ud83d\udcca
# -----------------------------

if periodo > 1:
    inflacion_real = df.iloc[periodo - 2]["Inflacion"]
    inflacion_min = round(inflacion_real * 0.80, 2)
    inflacion_max = round(inflacion_real * 1.20, 2)
    inflacion_display = f"{inflacion_min}% a {inflacion_max}%"
    creci_anterior = df.iloc[periodo - 2]["CRECI"]
else:
    inflacion_display = "0% a 0%"
    creci_anterior = 0

with st.container():
    st.markdown("### \ud83d\udcca Valores actuales:")

st.markdown(f"""
<div style='
    border: 2px solid #000;
    border-radius: 12px;
    padding: 20px;
    background-color: #2c3e50;
    color: white;
    font-size: 16px;
    font-family: \"Segoe UI\", \"Roboto\", \"Helvetica Neue\", sans-serif;
'>

<p>
\ud83d\udcc8 <strong>Inflaci\u00f3n <sub><em>t-1</em></sub> estimada:</strong>
<span style='font-size: 20px; font-weight: bold;'>{inflacion_display}</span><br>

\ud83d\udcbc <strong>Sueldo actual:</strong>
<span style='font-size: 20px; font-weight: bold;'>S/ {fila_actual['Sueldo']}</span><br>

\ud83d\udcb0 <strong>Ahorro disponible:</strong>
<span style='font-size: 20px; font-weight: bold;'>S/ {round(st.session_state.ahorro, 2)}</span><br>

\ud83d\udcc9 <strong>PBI <sub><em>t-1</em></sub>:</strong>
<span style='font-size: 20px; font-weight: bold;'>{creci_anterior}%</span><br>

\ud83c\udfe6 <strong>Estado de los Bancos:</strong>
<span style='font-size: 20px; font-weight: bold;'>{st.session_state.estado_banco}</span>
</p>
</div>
""", unsafe_allow_html=True)
