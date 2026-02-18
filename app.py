import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import calendar
from streamlit_autorefresh import st_autorefresh
from io import BytesIO

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
# FUNCION EXPORTAR EXCEL
# =============================
def generar_excel(dataframe):
    output = BytesIO()
    with pd.ExcelWriter(output) as writer:
        dataframe.to_excel(writer, index=False, sheet_name='Reporte')
    output.seek(0)
    return output

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
# CREAR / CARGAR ARCHIVO CITAS
# =============================
if not os.path.exists(ARCHIVO_CITAS):

    df = pd.DataFrame(columns=[
        "ID","Sede","Fecha","Hora","Tecnico",
        "Placa","Modelo","Nombre","Celular",
        "TipoServicio","Duracion",
        "Estado","Reprogramada"
    ])

    df.to_csv(ARCHIVO_CITAS,index=False)

else:
    df = pd.read_csv(ARCHIVO_CITAS)

# =============================
# NORMALIZAR COLUMNAS
# =============================
if "Estado" not in df.columns:
    df["Estado"] = "Pendiente"

if "Reprogramada" not in df.columns:
    df["Reprogramada"] = "No"

df["ID"] = pd.to_numeric(df["ID"], errors="coerce").fillna(0).astype(int)
df["Duracion"] = pd.to_numeric(df["Duracion"], errors="coerce").fillna(1).astype(int)

# =============================
# CREAR / CARGAR METAS
# =============================
if not os.path.exists(ARCHIVO_METAS):
    metas = pd.DataFrame(columns=["Sede","MetaMensual"])
    metas.to_csv(ARCHIVO_METAS,index=False)
else:
    metas = pd.read_csv(ARCHIVO_METAS)

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
    st_autorefresh(interval=15000, key="auto_refresh")

# =============================
# TABLERO RESPONSIVE
# =============================
def mostrar_tablero(df_dia, sede):

    # Mostrar solo citas pendientes
    if "Estado" in df_dia.columns:
        df_dia = df_dia[df_dia["Estado"] == "Pendiente"]

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
if st.session_state.rol == "admin":

    tab1, tab2 = st.tabs(["📊 Resumen Ejecutivo","🎯 Configurar Meta"])

    # =====================================================
    # TAB 1 - RESUMEN EJECUTIVO
    # =====================================================
    with tab1:

        st.title("📊 Dashboard Ejecutivo General")

        # ==============================
        # NORMALIZAR DATA
        # ==============================
        if df.empty:
            df_admin = pd.DataFrame(columns=["ID","Sede","Fecha","Estado"])
        else:
            df_admin = df.copy()

            if "Estado" not in df_admin.columns:
                df_admin["Estado"] = "Pendiente"

            df_admin["Fecha"] = pd.to_datetime(df_admin["Fecha"])

        # ==============================
        # SELECTORES
        # ==============================
        año_sel = st.selectbox(
            "Año",
            sorted(df_admin["Fecha"].dt.year.unique(), reverse=True)
            if not df_admin.empty else [datetime.today().year],
            key="admin_year"
        )

        mes_sel = st.selectbox(
            "Mes",
            list(range(1,13)),
            index=datetime.today().month-1,
            format_func=lambda x: calendar.month_name[x],
            key="admin_month"
        )

        df_mes = df_admin[
            (df_admin["Fecha"].dt.year == año_sel) &
            (df_admin["Fecha"].dt.month == mes_sel)
        ]

        # =====================================================
        # KPIs GLOBALES
        # =====================================================
        st.subheader("🌎 Indicadores Globales")

        total_mes = len(df_mes)
        efectivas = len(df_mes[df_mes["Estado"] == "Asistió"])
        no_show = len(df_mes[df_mes["Estado"] == "No asistió"])
        reprogramadas = len(df_mes[df_mes["Estado"] == "Reprogramada"])

        efectividad_pct = round((efectivas/total_mes)*100,1) if total_mes > 0 else 0
        no_show_pct = round((no_show/total_mes)*100,1) if total_mes > 0 else 0

        c1,c2,c3,c4 = st.columns(4)
        c1.metric("📅 Total Citas", total_mes)
        c2.metric("✅ Efectivas", efectivas)
        c3.metric("❌ No Show", no_show)
        c4.metric("🔄 Reprogramadas", reprogramadas)

        st.divider()

        cA,cB = st.columns(2)
        cA.metric("🎯 % Efectividad Global", f"{efectividad_pct}%")
        cB.metric("⚠ % No Show Global", f"{no_show_pct}%")

        st.divider()

        # =====================================================
        # RESUMEN EJECUTIVO POR SEDE
        # =====================================================
        st.subheader("🏢 Resumen Ejecutivo por Sede")

        for sede in SEDES:

            df_sede = df_mes[df_mes["Sede"] == sede]

            total_sede = len(df_sede)
            efectivas_sede = len(df_sede[df_sede["Estado"] == "Asistió"])
            no_show_sede = len(df_sede[df_sede["Estado"] == "No asistió"])
            reprog_sede = len(df_sede[df_sede["Estado"] == "Reprogramada"])

            efectividad_sede_pct = round((efectivas_sede/total_sede)*100,1) if total_sede > 0 else 0

            # Meta
            meta_sede = 0
            fila_meta = metas[metas["Sede"] == sede]
            if not fila_meta.empty:
                meta_sede = int(fila_meta["MetaMensual"].values[0])

            citas_validas = len(df_sede[df_sede["Estado"].isin(["Pendiente","Asistió"])])
            avance_meta_pct = round((citas_validas/meta_sede)*100,1) if meta_sede > 0 else 0

            # Semáforo meta
            if avance_meta_pct >= 100:
                semaforo = "🟢"
            elif avance_meta_pct >= 70:
                semaforo = "🟡"
            else:
                semaforo = "🔴"

            st.markdown(f"### {semaforo} {sede}")

            col1,col2,col3,col4,col5 = st.columns(5)

            col1.metric("📅 Total", total_sede)
            col2.metric("✅ Efectivas", efectivas_sede)
            col3.metric("❌ No Show", no_show_sede)
            col4.metric("🎯 % Efectividad", f"{efectividad_sede_pct}%")
            col5.metric("📈 Avance Meta", f"{avance_meta_pct}%")

            if meta_sede > 0:
                st.progress(min(citas_validas/meta_sede,1.0))

            st.divider()

        # =====================================================
        # CALENDARIO POR SEDE
        # =====================================================
        st.subheader("📅 Calendario de Agendamiento")

        for sede in SEDES:

            st.markdown(f"### 🏢 {sede}")

            df_sede_cal = df_mes[
                (df_mes["Sede"] == sede) &
                (df_mes["Estado"].isin(["Pendiente","Asistió"]))
            ]

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

                        html += f"<td style='padding:8px;border:1px solid #ddd;color:{color};font-weight:bold;'>"
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

    tab1, tab2, tab3 = st.tabs(["📅 Agendar","📋 Gestión de Citas","📈 Mi Avance"])

    # =====================================================
    # TAB 1 - AGENDAR
    # =====================================================
    with tab1:
        st.title("Agendar Cita")
    
        col1, col2 = st.columns(2)
    
        with col1:
            fecha = st.date_input("Fecha", min_value=datetime.today())
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
    
            if not placa or not modelo or not nombre or not servicio:
                st.warning("Completa todos los datos obligatorios")
                st.stop()
    
            df_temp = df.copy()
            df_temp["Fecha"] = pd.to_datetime(df_temp["Fecha"]).dt.date
    
            # 🔥 SOLO VALIDAR CITAS ACTIVAS
            df_dia = df_temp[
                (df_temp["Sede"] == st.session_state.sede) &
                (df_temp["Fecha"] == fecha) &
                (df_temp["Estado"].isin(["Pendiente","Asistió"]))
            ]
    
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
                st.error("Conflicto de horario con otra cita activa")
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
                    "Duracion":duracion,
                    "Estado":"Pendiente",
                    "Reprogramada":"No"
                }])
    
                df = pd.concat([df,nueva],ignore_index=True)
                df.to_csv(ARCHIVO_CITAS,index=False)
    
                st.success("Cita registrada correctamente")
                st.rerun()
    
        # 🔥 TABLERO SOLO CON CITAS ACTIVAS
        mostrar_tablero(
            df[
                (df["Sede"]==st.session_state.sede) &
                (df["Fecha"]==str(fecha)) &
                (df["Estado"].isin(["Pendiente","Asistió"]))
            ],
            st.session_state.sede
        )
    
     # =====================================================
    # TAB 2 - GESTIÓN DE CITAS
    # =====================================================
    with tab2:
    
        st.title("📋 Gestión de Citas")
    
        fecha_gestion = st.date_input(
            "Seleccionar fecha",
            value=datetime.today(),
            key="filtro_gestion"
        )
    
        df_sede = df[df["Sede"] == st.session_state.sede].copy()
        df_sede["Fecha"] = pd.to_datetime(df_sede["Fecha"]).dt.date
    
        df_filtrado = df_sede[df_sede["Fecha"] == fecha_gestion]
    
        if df_filtrado.empty:
            st.info("No hay citas para la fecha seleccionada")
        else:
            for i, row in df_filtrado.iterrows():
    
                st.markdown("---")
    
                col1, col2, col3, col4 = st.columns([4,2,3,1])
    
                # ==========================
                # DATOS
                # ==========================
                with col1:
                    st.markdown(f"""
                    **Cliente:** {row['Nombre']}  
                    **Celular:** {row['Celular']}  
                    **Modelo:** {row['Modelo']}  
                    **Servicio:** {row['TipoServicio']}  
                    **Hora:** {row['Hora']}  
                    **Estado:** {row['Estado']}
                    """)
    
                # =====================================================
                # SOLO SI ESTÁ PENDIENTE
                # =====================================================
                if row["Estado"] == "Pendiente":
    
                    # ==========================
                    # ASISTENCIA
                    # ==========================
                    with col2:
                        if st.button(f"✔ Asistió {row['ID']}"):
                            df.loc[df["ID"] == row["ID"], "Estado"] = "Asistió"
                            df.to_csv(ARCHIVO_CITAS, index=False)
                            st.rerun()
    
                        if st.button(f"❌ No asistió {row['ID']}"):
                            df.loc[df["ID"] == row["ID"], "Estado"] = "No asistió"
                            df.to_csv(ARCHIVO_CITAS, index=False)
                            st.rerun()
    
                    # ==========================
                    # EDITAR
                    # ==========================
                    with col3:
                        with st.expander("✏️ Editar"):
    
                            nueva_placa = st.text_input("Placa", value=row["Placa"], key=f"edit_placa_{row['ID']}")
                            nuevo_modelo = st.text_input("Modelo", value=row["Modelo"], key=f"edit_modelo_{row['ID']}")
                            nuevo_nombre = st.text_input("Cliente", value=row["Nombre"], key=f"edit_nombre_{row['ID']}")
                            nuevo_servicio = st.text_input("Servicio", value=row["TipoServicio"], key=f"edit_serv_{row['ID']}")
                            nueva_hora = st.selectbox(
                                "Hora",
                                [f"{h:02d}:00" for h in range(8,19)],
                                index=[f"{h:02d}:00" for h in range(8,19)].index(row["Hora"]),
                                key=f"edit_hora_{row['ID']}"
                            )
    
                            if st.button(f"Guardar cambios {row['ID']}"):
    
                                df_temp_edit = df.copy()
                                df_temp_edit["Fecha"] = pd.to_datetime(df_temp_edit["Fecha"]).dt.date
    
                                df_conflicto = df_temp_edit[
                                    (df_temp_edit["Sede"] == st.session_state.sede) &
                                    (df_temp_edit["Fecha"] == fecha_gestion) &
                                    (df_temp_edit["Tecnico"] == row["Tecnico"]) &
                                    (df_temp_edit["Estado"].isin(["Pendiente","Asistió"])) &
                                    (df_temp_edit["ID"] != row["ID"])
                                ]
    
                                conflicto = False
                                inicio_nuevo = datetime.strptime(nueva_hora,"%H:%M")
                                fin_nuevo = inicio_nuevo + timedelta(hours=row["Duracion"])
    
                                for _, r in df_conflicto.iterrows():
                                    inicio_exist = datetime.strptime(r["Hora"],"%H:%M")
                                    fin_exist = inicio_exist + timedelta(hours=r["Duracion"])
    
                                    if inicio_nuevo < fin_exist and fin_nuevo > inicio_exist:
                                        conflicto = True
                                        break
    
                                if conflicto:
                                    st.error("Conflicto de horario con otra cita activa")
                                else:
                                    df.loc[df["ID"] == row["ID"], "Placa"] = nueva_placa
                                    df.loc[df["ID"] == row["ID"], "Modelo"] = nuevo_modelo
                                    df.loc[df["ID"] == row["ID"], "Nombre"] = nuevo_nombre
                                    df.loc[df["ID"] == row["ID"], "TipoServicio"] = nuevo_servicio
                                    df.loc[df["ID"] == row["ID"], "Hora"] = nueva_hora
    
                                    df.to_csv(ARCHIVO_CITAS, index=False)
                                    st.success("Cita actualizada correctamente")
                                    st.rerun()
    
                    # ==========================
                    # ELIMINAR
                    # ==========================
                    with col4:
                        if st.button(f"🗑 {row['ID']}"):
                            df = df[df["ID"] != row["ID"]]
                            df.to_csv(ARCHIVO_CITAS, index=False)
                            st.warning("Cita eliminada")
                            st.rerun()
    
                    # ==========================
                    # REPROGRAMAR
                    # ==========================
                    with st.expander(f"🔄 Reprogramar {row['ID']}"):
    
                        nueva_fecha = st.date_input(
                            "Nueva fecha",
                            value=fecha_gestion,
                            key=f"fecha_{row['ID']}"
                        )
    
                        nueva_hora = st.selectbox(
                            "Nueva hora",
                            [f"{h:02d}:00" for h in range(8,19)],
                            key=f"hora_{row['ID']}"
                        )
    
                        nuevo_tecnico = st.selectbox(
                            "Técnico",
                            obtener_tecnicos(st.session_state.sede),
                            key=f"tec_{row['ID']}"
                        )
    
                        if st.button(f"Guardar nueva cita {row['ID']}"):
    
                            df_temp_reprog = df.copy()
                            df_temp_reprog["Fecha"] = pd.to_datetime(df_temp_reprog["Fecha"]).dt.date
    
                            df_conflicto = df_temp_reprog[
                                (df_temp_reprog["Sede"] == st.session_state.sede) &
                                (df_temp_reprog["Fecha"] == nueva_fecha) &
                                (df_temp_reprog["Tecnico"] == nuevo_tecnico) &
                                (df_temp_reprog["Estado"].isin(["Pendiente","Asistió"]))
                            ]
    
                            conflicto = False
                            inicio_nuevo = datetime.strptime(nueva_hora,"%H:%M")
                            fin_nuevo = inicio_nuevo + timedelta(hours=row["Duracion"])
    
                            for _, r in df_conflicto.iterrows():
                                inicio_exist = datetime.strptime(r["Hora"],"%H:%M")
                                fin_exist = inicio_exist + timedelta(hours=r["Duracion"])
    
                                if inicio_nuevo < fin_exist and fin_nuevo > inicio_exist:
                                    conflicto = True
                                    break
    
                            if conflicto:
                                st.error("Conflicto de horario con otra cita activa")
                            else:
                                nuevo_id = df["ID"].max() + 1
    
                                nueva = pd.DataFrame([{
                                    "ID": nuevo_id,
                                    "Sede": st.session_state.sede,
                                    "Fecha": str(nueva_fecha),
                                    "Hora": nueva_hora,
                                    "Tecnico": nuevo_tecnico,
                                    "Placa": row["Placa"],
                                    "Modelo": row["Modelo"],
                                    "Nombre": row["Nombre"],
                                    "Celular": row["Celular"],
                                    "TipoServicio": row["TipoServicio"],
                                    "Duracion": row["Duracion"],
                                    "Estado": "Pendiente",
                                    "Reprogramada": "Sí"
                                }])
    
                                df.loc[df["ID"] == row["ID"], "Estado"] = "Reprogramada"
                                df.loc[df["ID"] == row["ID"], "Reprogramada"] = "Sí"
    
                                df = pd.concat([df, nueva], ignore_index=True)
                                df.to_csv(ARCHIVO_CITAS, index=False)
    
                                st.success("Cita reprogramada correctamente")
                                st.rerun()
    
                else:
                    st.info("Registro cerrado. No se permiten modificaciones.")
    
    # =====================================================
    # TAB 3 - MI AVANCE
    # =====================================================
    with tab3:
        st.title("📈 Mi Avance")
    
        df_sede = df[df["Sede"] == st.session_state.sede].copy()
        df_sede["Fecha"] = pd.to_datetime(df_sede["Fecha"])
    
        # ================================
        # SELECTORES
        # ================================
        año_sel = st.selectbox(
            "Año",
            sorted(df_sede["Fecha"].dt.year.unique(), reverse=True)
            if not df_sede.empty else [datetime.today().year]
        )
    
        mes_sel = st.selectbox(
            "Mes",
            list(range(1,13)),
            index=datetime.today().month-1,
            format_func=lambda x: calendar.month_name[x]
        )
    
        df_mes = df_sede[
            (df_sede["Fecha"].dt.month == mes_sel) &
            (df_sede["Fecha"].dt.year == año_sel)
        ]
    
        # ================================
        # CÁLCULOS
        # ================================
        total_mes = len(df_mes)
    
        efectivas = len(df_mes[df_mes["Estado"] == "Asistió"])
        no_show = len(df_mes[df_mes["Estado"] == "No asistió"])
        reprogramadas = len(df_mes[df_mes["Estado"] == "Reprogramada"])
        pendientes = len(df_mes[df_mes["Estado"] == "Pendiente"])
    
        efectividad_pct = round((efectivas / total_mes) * 100, 1) if total_mes > 0 else 0
        no_show_pct = round((no_show / total_mes) * 100, 1) if total_mes > 0 else 0
        reprog_pct = round((reprogramadas / total_mes) * 100, 1) if total_mes > 0 else 0
    
        # ================================
        # TARJETAS PRINCIPALES
        # ================================
        col1, col2, col3, col4 = st.columns(4)
    
        col1.metric("📅 Total Citas", total_mes)
        col2.metric("✅ Citas Efectivas", efectivas)
        col3.metric("❌ No Show", no_show)
        col4.metric("🔄 Reprogramadas", reprogramadas)
    
        st.divider()
    
        # ================================
        # INDICADORES DE DESEMPEÑO
        # ================================
        st.subheader("📊 Indicadores de Desempeño")
    
        colA, colB, colC = st.columns(3)
    
        colA.metric("🎯 % Efectividad", f"{efectividad_pct}%")
        colB.metric("⚠ % No Show", f"{no_show_pct}%")
        colC.metric("🔁 % Reprogramación", f"{reprog_pct}%")
    
        if total_mes > 0:
            st.progress(efectivas / total_mes)
    
        # ================================
        # META MENSUAL
        # ================================
        st.divider()
        st.subheader("🎯 Cumplimiento de Meta")
    
        df_validas = df_mes[df_mes["Estado"].isin(["Pendiente","Asistió"])]
        total_validas = len(df_validas)
    
        meta_sede = 0
        fila_meta = metas[metas["Sede"] == st.session_state.sede]
        if not fila_meta.empty:
            meta_sede = int(fila_meta["MetaMensual"].values[0])
    
        avance_pct = round((total_validas/meta_sede)*100,1) if meta_sede > 0 else 0
    
        colM1, colM2, colM3 = st.columns(3)
        colM1.metric("📅 Citas válidas", total_validas)
        colM2.metric("🎯 Meta Mensual", meta_sede)
        colM3.metric("📈 Avance Meta", f"{avance_pct}%")
    
        if meta_sede > 0:
            st.progress(min(total_validas/meta_sede,1.0))

    

