import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import calendar
from streamlit_autorefresh import st_autorefresh

st.set_page_config(layout="wide")

# =========================================
# SISTEMA DE CITAS - VERSION ESTABLE v2.0
# Febrero 2026
# =========================================

ARCHIVO_CITAS = "citas.csv"
ARCHIVO_METAS = "metas.csv"

# =============================
# USUARIOS
# =============================
USUARIOS = {
    "admin": {"password": "1234", "rol": "admin", "sede": "TODAS"},

    "tarapoto": {"password": "1234", "rol": "asesor", "sede": "TARAPOTO"},
    "jaen": {"password": "1234", "rol": "asesor", "sede": "JAEN"},
    "bagua": {"password": "1234", "rol": "asesor", "sede": "BAGUA"},
    "moyobamba": {"password": "1234", "rol": "asesor", "sede": "MOYOBAMBA"},
    "iquitos_prospero": {"password": "1234", "rol": "asesor", "sede": "IQUITOS PROSPERO"},
    "iquitos_quinones": {"password": "1234", "rol": "asesor", "sede": "IQUITOS QUIÑONES"},
    "pucallpa": {"password": "1234", "rol": "asesor", "sede": "PUCALLPA"},
    "yurimaguas": {"password": "1234", "rol": "asesor", "sede": "YURIMAGUAS"},
}

SEDES = [
    "TARAPOTO","JAEN","BAGUA","MOYOBAMBA",
    "IQUITOS PROSPERO","IQUITOS QUIÑONES",
    "PUCALLPA","YURIMAGUAS"
]

# =============================
# TECNICOS POR SEDE
# =============================
TECNICOS = {

    "JAEN": ["CARLOS", "JAIRO", "LUIS EDWIN", "MESIAS", "DAGNER", "ABEL"],
    "TARAPOTO": ["BILLY", "ENRIQUE", "JULIO", "MARCOS", "ANSELMO", "ESLEYTER", "HANS", "FREDDY"],
    "YURIMAGUAS": ["JOSE", "JUNIOR", "GUIDO", "JHON"],
    
    # SEDES TEMPORALES
    "BAGUA": ["TEC 1", "TEC 2"],
    "MOYOBAMBA": ["TEC 1", "TEC 2"],
    "IQUITOS PROSPERO": ["TEC 1", "TEC 2"],
    "IQUITOS QUIÑONES": ["TEC 1", "TEC 2"],
    "PUCALLPA": ["TEC 1", "TEC 2"],
}

# =============================
# COLORES
# =============================
COLORES = {

    # JAEN
    "CARLOS": "#AED6F1",
    "JAIRO": "#A9DFBF",
    "LUIS EDWIN": "#F9E79F",
    "MESIAS": "#F5B7B1",
    "DAGNER": "#D2B4DE",
    "ABEL": "#FAD7A0",

    # TARAPOTO
    "BILLY": "#85C1E9",
    "ENRIQUE": "#82E0AA",
    "JULIO": "#F7DC6F",
    "MARCOS": "#F1948A",
    "ANSELMO": "#BB8FCE",
    "ESLEYTER": "#F8C471",
    "HANS": "#76D7C4",
    "FREDDY": "#F5B041",

    # YURIMAGUAS
    "JOSE": "#7FB3D5",
    "JUNIOR": "#73C6B6",
    "GUIDO": "#F7DC6F",
    "JHON": "#F1948A",

    # TECNICOS TEMPORALES
    "TEC 1": "#D5DBDB",
    "TEC 2": "#AEB6BF",

    "ASESOR": "#D5D8DC"
}

# =============================
# FUNCION DINAMICA
# =============================
def obtener_tecnicos(sede):
    return TECNICOS.get(sede, ["ASESOR"])

# =============================
# LOGIN
# =============================
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

# =============================
# HEADER + CERRAR SESIÓN
# =============================
col_user, col_logout = st.columns([8,2])

with col_user:
    st.markdown(
        f"👤 **Usuario:** {st.session_state.usuario} | "
        f"Rol: {st.session_state.rol} | "
        f"Sede: {st.session_state.sede}"
    )

with col_logout:
    if st.button("🔓 Cerrar sesión"):
        st.session_state.usuario = None
        st.session_state.rol = None
        st.session_state.sede = None
        st.rerun()

st.divider()

# =============================
# AUTO REFRESH SOLO PARA ASESOR
# =============================
if st.session_state.rol == "asesor":
    st_autorefresh(interval=10000, key="auto_refresh")

# =============================
# ARCHIVOS
# =============================
if not os.path.exists(ARCHIVO_CITAS):
    df = pd.DataFrame(columns=[
        "ID","Sede","Fecha","Hora","Tecnico",
        "Placa","Modelo","Nombre","Celular",
        "TipoServicio","Duracion"
    ])
    df.to_csv(ARCHIVO_CITAS,index=False)
else:
    df = pd.read_csv(ARCHIVO_CITAS)

if not os.path.exists(ARCHIVO_METAS):
    metas = pd.DataFrame(columns=["Sede","MetaMensual"])
    metas.to_csv(ARCHIVO_METAS,index=False)
else:
    metas = pd.read_csv(ARCHIVO_METAS)

df["ID"] = pd.to_numeric(df["ID"], errors="coerce").fillna(0).astype(int)
df["Duracion"] = pd.to_numeric(df["Duracion"], errors="coerce").fillna(1).astype(int)

# =============================
# TABLERO RESPONSIVE
# =============================
def mostrar_tablero(df_dia, sede):

    tecnicos = obtener_tecnicos(sede)
    horas = [f"{h:02d}:00" for h in range(8,19)]

    html = "<div style='overflow-x:auto;'>"
    html += "<table style='width:100%; border-collapse:collapse; min-width:900px;'>"
    html += "<tr><th style='border:1px solid #ddd;padding:8px;'>Hora</th>"

    for t in tecnicos:
        html += f"<th style='border:1px solid #ddd;padding:8px;text-align:center;'>{t}</th>"
    html += "</tr>"

    for hora in horas:
        html += "<tr>"
        html += f"<td style='border:1px solid #ddd;padding:6px;text-align:center;'><b>{hora}</b></td>"

        for tecnico in tecnicos:
            ocupado = False
            for _, row in df_dia.iterrows():
                inicio = datetime.strptime(row["Hora"], "%H:%M")
                fin = inicio + timedelta(hours=row["Duracion"])
                actual = datetime.strptime(hora, "%H:%M")

                if row["Tecnico"] == tecnico and actual >= inicio and actual < fin:
                    color = COLORES.get(tecnico,"#EAECEE")

                    card = f"""
                    <div style='background:{color};padding:8px;border-radius:8px;font-size:12px;'>
                        <b>Placa:</b> {row['Placa']}<br>
                        <b>Modelo:</b> {row['Modelo']}<br>
                        <b>Cliente:</b> {row['Nombre']}<br>
                        <b>Servicio:</b> {row['TipoServicio']}
                    </div>
                    """
                    html += f"<td style='border:1px solid #ddd;padding:6px;'>{card}</td>"
                    ocupado = True
                    break

            if not ocupado:
                html += "<td style='border:1px solid #ddd;'></td>"

        html += "</tr>"

    html += "</table></div>"
    st.markdown(html, unsafe_allow_html=True)

# =============================
# ADMIN
# =============================
# =============================
# ADMIN
# =============================
if st.session_state.rol == "admin":

    tab1, tab2 = st.tabs(["📊 Resumen","🎯 Configurar Meta"])

    # =====================================================
    # TAB 1 - RESUMEN GENERAL
    # =====================================================
    with tab1:

        st.title("📊 Resumen General por Sede")

        # Si no hay datos, creamos estructura mínima
        if df.empty:
            df_admin = pd.DataFrame(columns=["ID","Sede","Fecha"])
        else:
            df_admin = df.copy()
            df_admin["Fecha"] = pd.to_datetime(df_admin["Fecha"])

        # Selector Año
        año_sel = st.selectbox(
            "Año",
            sorted(df_admin["Fecha"].dt.year.unique(), reverse=True)
            if not df_admin.empty else [datetime.today().year],
            key="admin_year"
        )

        # Selector Mes
        mes_sel = st.selectbox(
            "Mes",
            list(range(1,13)),
            index=datetime.today().month-1,
            format_func=lambda x: calendar.month_name[x],
            key="admin_month"
        )

        # Filtrado mensual
        if not df_admin.empty:
            df_mes = df_admin[
                (df_admin["Fecha"].dt.year == año_sel) &
                (df_admin["Fecha"].dt.month == mes_sel)
            ]
        else:
            df_mes = pd.DataFrame(columns=["ID","Sede","Fecha"])

        # =====================================================
        # GRAFICO AVANCE POR SEDE
        # =====================================================
        datos_grafico = []

        for sede in SEDES:

            df_sede = df_mes[df_mes["Sede"] == sede]
            total_citas = len(df_sede)

            meta_sede = 0
            fila_meta = metas[metas["Sede"] == sede]
            if not fila_meta.empty:
                meta_sede = int(fila_meta["MetaMensual"].values[0])

            porcentaje = round((total_citas/meta_sede)*100,1) if meta_sede>0 else 0

            datos_grafico.append({
                "Sede": sede,
                "Citas": total_citas,
                "Meta": meta_sede,
                "Avance %": porcentaje
            })

        df_grafico = pd.DataFrame(datos_grafico)

        st.subheader("📈 Avance por Sede (%)")
        st.bar_chart(df_grafico.set_index("Sede")["Avance %"])

        st.divider()

        st.subheader("📋 Detalle por Sede")
        st.dataframe(df_grafico, use_container_width=True)

        # =====================================================
        # CALENDARIOS POR SEDE (SIEMPRE VISIBLES)
        # =====================================================
        st.divider()
        st.subheader("📅 Calendario de Agendamiento por Sede")

        for sede in SEDES:

            st.markdown(f"### 🏢 {sede}")

            df_sede_cal = df_mes[df_mes["Sede"] == sede]

            conteo = (
                df_sede_cal
                .groupby(df_sede_cal["Fecha"].dt.day)["ID"]
                .count()
                .to_dict()
                if not df_sede_cal.empty else {}
            )

            cal = calendar.monthcalendar(año_sel, mes_sel)

            html = "<table style='width:100%; text-align:center; border-collapse:collapse;'>"
            html += "<tr><th>L</th><th>M</th><th>M</th><th>J</th><th>V</th><th>S</th><th>D</th></tr>"

            for semana in cal:
                html += "<tr>"
                for dia in semana:
                    if dia == 0:
                        html += "<td></td>"
                    else:
                        cant = conteo.get(dia, 0)

                        if cant == 0:
                            color = "#BFC9CA"
                        elif cant <= 2:
                            color = "#2E86C1"
                        elif cant <= 4:
                            color = "#28B463"
                        else:
                            color = "#CB4335"

                        html += "<td style='padding:10px;border:1px solid #ddd;font-weight:bold;"
                        html += f"color:{color};font-size:14px;'>"
                        html += f"{dia}<br><span style='font-size:11px;'>{cant} citas</span></td>"

                html += "</tr>"

            html += "</table>"
            st.markdown(html, unsafe_allow_html=True)

            st.divider()

    # =====================================================
    # TAB 2 - CONFIGURAR META
    # =====================================================
    with tab2:

        st.title("🎯 Configurar Meta")

        sede_meta = st.selectbox("Sede", SEDES, key="meta_sede")
        nueva_meta = st.number_input("Meta mensual", 0, 1000, 0)

        if st.button("Guardar Meta"):
            metas = metas[metas["Sede"] != sede_meta]
            metas = pd.concat([
                metas,
                pd.DataFrame([{
                    "Sede": sede_meta,
                    "MetaMensual": nueva_meta
                }])
            ])
            metas.to_csv(ARCHIVO_METAS, index=False)
            st.success("Meta guardada correctamente")

# =============================
# ASESOR
# =============================
else:

    tab1, tab2 = st.tabs(["📅 Agendar","📈 Mi Avance"])

    with tab1:
        st.title("Agendar Cita")

        col1, col2 = st.columns(2)

        with col1:
            fecha = st.date_input("Fecha")
            hora = st.selectbox("Hora inicio",[f"{h:02d}:00" for h in range(8,19)])
            duracion = st.number_input("Duración (horas)",1,8,1)
            tecnico = st.selectbox("Técnico", obtener_tecnicos(st.session_state.sede))

        with col2:
            placa = st.text_input("Placa")
            modelo = st.text_input("Modelo")
            nombre = st.text_input("Nombres y apellidos")
            celular = st.text_input("Celular")
            servicio = st.text_input("Tipo de Servicio")

        if st.button("Guardar"):

            df_dia = df[(df["Sede"]==st.session_state.sede) &
                        (df["Fecha"]==str(fecha))]

            inicio_nuevo = datetime.strptime(hora,"%H:%M")
            fin_nuevo = inicio_nuevo + timedelta(hours=duracion)

            conflicto=False

            for _,row in df_dia.iterrows():
                if row["Tecnico"]==tecnico:
                    inicio_exist = datetime.strptime(row["Hora"],"%H:%M")
                    fin_exist = inicio_exist + timedelta(hours=row["Duracion"])
                    if inicio_nuevo < fin_exist and fin_nuevo > inicio_exist:
                        conflicto=True
                        break

            if conflicto:
                st.error("Conflicto de horario con otra cita")
            else:
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
                    "Duracion":duracion
                }])
                df = pd.concat([df,nueva],ignore_index=True)
                df.to_csv(ARCHIVO_CITAS,index=False)
                st.success("Cita registrada")
                st.rerun()

        mostrar_tablero(
            df[(df["Sede"]==st.session_state.sede) &
               (df["Fecha"]==str(fecha))],
            st.session_state.sede
        )

    with tab2:
        st.title("Mi Avance")

        df_sede = df[df["Sede"]==st.session_state.sede].copy()
        df_sede["Fecha"] = pd.to_datetime(df_sede["Fecha"])

        año_sel = st.selectbox("Año",
            sorted(df_sede["Fecha"].dt.year.unique(), reverse=True)
            if not df_sede.empty else [datetime.today().year])

        mes_sel = st.selectbox("Mes",
            list(range(1,13)),
            index=datetime.today().month-1,
            format_func=lambda x: calendar.month_name[x])

        df_mes = df_sede[
            (df_sede["Fecha"].dt.month==mes_sel) &
            (df_sede["Fecha"].dt.year==año_sel)
        ]

        total_citas = len(df_mes)

        meta_sede = 0
        fila_meta = metas[metas["Sede"] == st.session_state.sede]
        if not fila_meta.empty:
            meta_sede = int(fila_meta["MetaMensual"].values[0])

        porcentaje = round((total_citas/meta_sede)*100,1) if meta_sede>0 else 0

        col1,col2,col3 = st.columns(3)
        col1.metric("📅 Citas del Mes", total_citas)
        col2.metric("🎯 Meta Mensual", meta_sede)
        col3.metric("📈 Avance", f"{porcentaje}%")

        if meta_sede>0:
            st.progress(min(total_citas/meta_sede,1.0))

        st.divider()
        conteo = df_mes.groupby(df_mes["Fecha"].dt.day)["ID"].count().to_dict()
        cal = calendar.monthcalendar(año_sel, mes_sel)

        html = "<table style='width:100%; text-align:center; border-collapse:collapse;'>"
        html += "<tr><th>L</th><th>M</th><th>M</th><th>J</th><th>V</th><th>S</th><th>D</th></tr>"

        for semana in cal:
            html += "<tr>"
            for dia in semana:
                if dia == 0:
                    html += "<td></td>"
                else:
                    cant = conteo.get(dia, 0)
                    if cant == 0:
                        color = "#BFC9CA"
                    elif cant <= 2:
                        color = "#2E86C1"
                    elif cant <= 4:
                        color = "#28B463"
                    else:
                        color = "#CB4335"

                    html += "<td style='padding:12px;border:1px solid #ddd;font-weight:bold;"
                    html += f"color:{color};font-size:16px;'>"
                    html += f"{dia}<br><span style='font-size:12px;'>{cant} citas</span></td>"

            html += "</tr>"

        html += "</table>"
        st.markdown(html, unsafe_allow_html=True)



