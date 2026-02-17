import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import calendar
from streamlit_autorefresh import st_autorefresh

st.set_page_config(layout="wide")

# =========================================
# CONFIGURACIÓN
# =========================================
ARCHIVO_CITAS = "citas.csv"
ARCHIVO_METAS = "metas.csv"

# =========================================
# USUARIOS
# =========================================
USUARIOS = {
    "admin": {"password": "1234", "rol": "admin", "sede": "TODAS"},
    "jaen": {"password": "1234", "rol": "asesor", "sede": "JAEN"},
}

SEDES = ["JAEN"]

TECNICOS = {
    "JAEN": ["CARLOS", "JAIRO", "LUIS EDWIN", "MESIAS", "DAGNER", "ABEL"],
}

COLORES = {
    "CARLOS": "#AED6F1",
    "JAIRO": "#A9DFBF",
    "LUIS EDWIN": "#F9E79F",
    "MESIAS": "#F5B7B1",
    "DAGNER": "#D2B4DE",
    "ABEL": "#FAD7A0",
}

def obtener_tecnicos(sede):
    return TECNICOS.get(sede, [])

# =========================================
# LOGIN
# =========================================
if "usuario" not in st.session_state:
    st.session_state.usuario = None
    st.session_state.rol = None
    st.session_state.sede = None

if st.session_state.usuario is None:
    st.title("🔐 Login")
    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")

    if st.button("Ingresar"):
        if u in USUARIOS and USUARIOS[u]["password"] == p:
            st.session_state.usuario = u
            st.session_state.rol = USUARIOS[u]["rol"]
            st.session_state.sede = USUARIOS[u]["sede"]
            st.rerun()
        else:
            st.error("Credenciales incorrectas")
    st.stop()

# =========================================
# HEADER
# =========================================
col1, col2 = st.columns([8,2])
col1.markdown(f"👤 **{st.session_state.usuario}** | Rol: {st.session_state.rol}")

if col2.button("Cerrar sesión"):
    st.session_state.usuario = None
    st.rerun()

st.divider()

# =========================================
# AUTO REFRESH ASESOR
# =========================================
if st.session_state.rol == "asesor":
    st_autorefresh(interval=10000, key="refresh")

# =========================================
# ARCHIVOS
# =========================================
COLUMNAS = [
    "ID","Sede","Fecha","Hora","Tecnico",
    "Placa","Modelo","Nombre","Celular",
    "TipoServicio","Duracion","Estado"
]

if not os.path.exists(ARCHIVO_CITAS):
    df = pd.DataFrame(columns=COLUMNAS)
    df.to_csv(ARCHIVO_CITAS,index=False)
else:
    df = pd.read_csv(ARCHIVO_CITAS)
    if "Estado" not in df.columns:
        df["Estado"] = "PROGRAMADA"
        df.to_csv(ARCHIVO_CITAS,index=False)

df["ID"] = pd.to_numeric(df["ID"], errors="coerce").fillna(0).astype(int)
df["Duracion"] = pd.to_numeric(df["Duracion"], errors="coerce").fillna(1).astype(int)

# =========================================
# FUNCIÓN TABLERO
# =========================================
def mostrar_tablero(df_dia, sede):

    tecnicos = obtener_tecnicos(sede)
    horas = [f"{h:02d}:00" for h in range(8,19)]

    html = "<table style='width:100%; border-collapse:collapse;'>"
    html += "<tr><th>Hora</th>"

    for t in tecnicos:
        html += f"<th>{t}</th>"
    html += "</tr>"

    for hora in horas:
        html += "<tr>"
        html += f"<td><b>{hora}</b></td>"

        for tecnico in tecnicos:
            ocupado = False
            for _, row in df_dia.iterrows():

                inicio = datetime.strptime(row["Hora"], "%H:%M")
                fin = inicio + timedelta(hours=row["Duracion"])
                actual = datetime.strptime(hora, "%H:%M")

                if row["Tecnico"] == tecnico and actual >= inicio and actual < fin:

                    estado = row["Estado"]

                    if estado == "ASISTIO":
                        color = "#82E0AA"
                    elif estado == "NO ASISTIO":
                        color = "#F1948A"
                    else:
                        color = COLORES.get(tecnico,"#EAECEE")

                    card = f"""
                    <div style='background:{color};padding:8px;border-radius:8px;'>
                    <b>{row['Nombre']}</b><br>
                    {row['Placa']}<br>
                    {row['TipoServicio']}
                    </div>
                    """

                    html += f"<td>{card}</td>"
                    ocupado = True
                    break

            if not ocupado:
                html += "<td></td>"

        html += "</tr>"

    html += "</table>"
    st.markdown(html, unsafe_allow_html=True)

# =========================================
# ADMIN
# =========================================
if st.session_state.rol == "admin":

    st.title("📊 Resumen General")

    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
    df_mes = df[df["Fecha"].dt.month == datetime.today().month]

    total = len(df_mes)
    asistieron = len(df_mes[df_mes["Estado"]=="ASISTIO"])
    no_asistieron = len(df_mes[df_mes["Estado"]=="NO ASISTIO"])

    col1,col2,col3 = st.columns(3)
    col1.metric("Total Citas", total)
    col2.metric("Asistieron", asistieron)
    col3.metric("No Show", no_asistieron)

# =========================================
# ASESOR
# =========================================
else:

    st.title("📅 Agendar Cita")

    fecha = st.date_input("Fecha")
    hora = st.selectbox("Hora",[f"{h:02d}:00" for h in range(8,19)])
    duracion = st.number_input("Duración",1,8,1)
    tecnico = st.selectbox("Técnico", obtener_tecnicos(st.session_state.sede))

    placa = st.text_input("Placa")
    modelo = st.text_input("Modelo")
    nombre = st.text_input("Cliente")
    celular = st.text_input("Celular")
    servicio = st.text_input("Servicio")

    if st.button("Guardar"):
        nuevo_id = df["ID"].max()+1 if not df.empty else 1

        nueva = pd.DataFrame([{
            "ID":nuevo_id,
            "Sede":st.session_state.sede,
            "Fecha":str(fecha),
            "Hora":hora,
            "Tecnico":tecnico,
            "Placa":placa,
            "Modelo":modelo,
            "Nombre":nombre,
            "Celular":celular,
            "TipoServicio":servicio,
            "Duracion":duracion,
            "Estado":"PROGRAMADA"
        }])

        df = pd.concat([df,nueva],ignore_index=True)
        df.to_csv(ARCHIVO_CITAS,index=False)
        st.success("Cita registrada")
        st.rerun()

    df_dia = df[(df["Sede"]==st.session_state.sede) & (df["Fecha"]==str(fecha))]
    mostrar_tablero(df_dia, st.session_state.sede)

    st.divider()
    st.subheader("📋 Control de Asistencia")

    for _,row in df_dia.iterrows():

        c1,c2,c3,c4,c5,c6 = st.columns([3,1,1,1,1,2])

        c1.write(f"**{row['Nombre']}**")
        c2.write(row["Hora"])
        c3.write(row["Tecnico"])

        if c4.button("✔", key=f"ok_{row['ID']}"):
            df.loc[df["ID"]==row["ID"],"Estado"]="ASISTIO"
            df.to_csv(ARCHIVO_CITAS,index=False)
            st.rerun()

        if c5.button("✖", key=f"no_{row['ID']}"):
            df.loc[df["ID"]==row["ID"],"Estado"]="NO ASISTIO"
            df.to_csv(ARCHIVO_CITAS,index=False)
            st.rerun()

        if row["Estado"]=="NO ASISTIO":

            nueva_fecha = c6.date_input("Nueva fecha", key=f"fecha_{row['ID']}")

            if c6.button("Reprogramar", key=f"rep_{row['ID']}"):

                nuevo_id = df["ID"].max()+1

                nueva_cita = {
                    "ID":nuevo_id,
                    "Sede":row["Sede"],
                    "Fecha":str(nueva_fecha),
                    "Hora":row["Hora"],
                    "Tecnico":row["Tecnico"],
                    "Placa":row["Placa"],
                    "Modelo":row["Modelo"],
                    "Nombre":row["Nombre"],
                    "Celular":row["Celular"],
                    "TipoServicio":row["TipoServicio"],
                    "Duracion":row["Duracion"],
                    "Estado":"PROGRAMADA"
                }

                df = pd.concat([df,pd.DataFrame([nueva_cita])],ignore_index=True)
                df.to_csv(ARCHIVO_CITAS,index=False)
                st.success("Cita reprogramada")
                st.rerun()


