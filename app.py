import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import calendar
import pytz
from streamlit_autorefresh import st_autorefresh
from io import BytesIO

st.set_page_config(layout="wide")

# =========================================
# SISTEMA DE CITAS - VERSION ESTABLE v2.0
# Febrero 2026
# =========================================

ARCHIVO_CITAS = "citas.csv"
ARCHIVO_METAS = "metas.csv"
ARCHIVO_VOLUMEN = "volumen.csv"

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

SEDES = ["TARAPOTO","JAEN","BAGUA","MOYOBAMBA","IQUITOS PROSPERO","IQUITOS QUIÑONES","PUCALLPA","YURIMAGUAS"]

# =============================
# FUNCION EXPORTAR EXCEL EJECUTIVO
# =============================
def generar_excel_ejecutivo(df_mes, metas, anio_sel, mes_sel):

    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:

        # =============================
        # HOJA 1 - RESUMEN GLOBAL
        # =============================
        total = len(df_mes)
        efectivas = len(df_mes[df_mes["Estado"] == "Asistió"])
        no_show = len(df_mes[df_mes["Estado"] == "No asistió"])
        reprogramadas = len(df_mes[df_mes["Estado"] == "Reprogramada"])

        efectividad_pct = round((efectivas/total)*100,1) if total>0 else 0
        no_show_pct = round((no_show/total)*100,1) if total>0 else 0

        df_resumen_global = pd.DataFrame({
            "Indicador":[
                "Total Citas",
                "Citas Efectivas",
                "No Show",
                "Reprogramadas",
                "% Efectividad",
                "% No Show"
            ],
            "Valor":[
                total,
                efectivas,
                no_show,
                reprogramadas,
                f"{efectividad_pct}%",
                f"{no_show_pct}%"
            ]
        })

        df_resumen_global.to_excel(writer, index=False, sheet_name="Resumen Global")

        # =============================
        # HOJA 2 - RESUMEN POR SEDE
        # =============================
        resumen_sedes = []

        for sede in SEDES:

            df_sede = df_mes[df_mes["Sede"] == sede]

            total_sede = len(df_sede)
            efectivas_sede = len(df_sede[df_sede["Estado"] == "Asistió"])
            no_show_sede = len(df_sede[df_sede["Estado"] == "No asistió"])

            efectividad_sede_pct = round((efectivas_sede/total_sede)*100,1) if total_sede>0 else 0

            meta_sede = 0
            fila_meta = metas[metas["Sede"] == sede]
            if not fila_meta.empty:
                meta_sede = int(fila_meta["MetaMensual"].values[0])

            citas_validas = len(df_sede[df_sede["Estado"].isin(["Pendiente","Asistió"])])
            avance_meta = round((citas_validas/meta_sede)*100,1) if meta_sede>0 else 0

            resumen_sedes.append({
                "Sede": sede,
                "Total Citas": total_sede,
                "Efectivas": efectivas_sede,
                "No Show": no_show_sede,
                "% Efectividad": f"{efectividad_sede_pct}%",
                "Meta": meta_sede,
                "Avance Meta %": f"{avance_meta}%"
            })

        pd.DataFrame(resumen_sedes).to_excel(writer, index=False, sheet_name="Resumen por Sede")

        # =============================
        # HOJA 3 - DETALLE
        # =============================
        df_detalle = df_mes.copy()

        if "Fecha" in df_detalle.columns:
            df_detalle["Fecha"] = pd.to_datetime(df_detalle["Fecha"]).dt.strftime("%d/%m/%Y")

        columnas = [
            "ID","Sede","Fecha","Hora","Tecnico",
            "Nombre","Celular",
            "Placa","Modelo",
            "TipoServicio","Duracion",
            "Estado","Reprogramada"
        ]

        columnas_validas = [c for c in columnas if c in df_detalle.columns]
        df_detalle[columnas_validas].to_excel(writer, index=False, sheet_name="Detalle Citas")

    output.seek(0)
    return output

# =============================
# TECNICOS POR SEDE
# =============================
TECNICOS = {
    "JAEN": ["CARLOS", "JAIRO", "LUIS EDWIN", "MESIAS", "DAGNER", "ABEL", "DENIS"],
    "TARAPOTO": ["BILLY", "ENRIQUE", "JULIO", "MARCOS", "ANSELMO", "ESLEYTER", "HANS", "FREDDY"],
    "YURIMAGUAS": ["JOSE", "JUNIOR", "GUIDO", "JHON"],
    "MOYOBAMBA": ["JACK", "MILLER", "LEONAN", "LUIS", "ALEX"],    
    
    # SEDES TEMPORALES
    "BAGUA": ["TEC 1", "TEC 2"],
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
    "DENIS": "#F8C471",

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

    # MOYOBAMBA
    "JACK": "#3498DB",
    "MILLER": "#27AE60",
    "LEONAN": "#F1C40F",
    "LUIS": "#E67E22",
    "ALEX": "#8E44AD",

    # TECNICOS TEMPORALES
    "TEC 1": "#D5DBDB",
    "TEC 2": "#AEB6BF",

    "ASESOR": "#D5D8DC"
}

# =============================
# CREAR / CARGAR ARCHIVO CITAS (PRO)
# =============================
columnas_base = [
    "ID","Sede","Fecha","Hora","Tecnico",
    "Placa","Modelo","Nombre","Celular",
    "TipoServicio","Duracion",
    "Estado","Reprogramada"
]

if not os.path.exists(ARCHIVO_CITAS):

    df = pd.DataFrame(columns=columnas_base)
    df.to_csv(ARCHIVO_CITAS, index=False)

else:
    # 🔥 cargar todo como texto evita corrupción de tipos
    df = pd.read_csv(ARCHIVO_CITAS, dtype=str)

# =============================
# NORMALIZAR COLUMNAS (PRO)
# =============================
for c in columnas_base:
    if c not in df.columns:
        df[c] = ""

# valores por defecto
df["Estado"] = df["Estado"].replace("", "Pendiente")
df["Reprogramada"] = df["Reprogramada"].replace("", "No")

# limpiar espacios
df["Hora"] = df["Hora"].astype(str).str.strip()
df["Tecnico"] = df["Tecnico"].astype(str).str.strip()
df["Sede"] = df["Sede"].astype(str).str.strip()

# tipado seguro
df["ID"] = pd.to_numeric(df["ID"], errors="coerce").fillna(0).astype(int)
df["Duracion"] = pd.to_numeric(df["Duracion"], errors="coerce").fillna(1).astype(int)

# copia segura para evitar bugs streamlit
df = df.copy()

# =============================
# CREAR / CARGAR METAS
# =============================
if not os.path.exists(ARCHIVO_METAS):
    metas = pd.DataFrame(columns=["Sede","MetaMensual"])
    metas.to_csv(ARCHIVO_METAS,index=False)
else:
    metas = pd.read_csv(ARCHIVO_METAS)

# =============================
# CREAR / CARGAR VOLUMEN
# =============================
if not os.path.exists(ARCHIVO_VOLUMEN):
    df_volumen = pd.DataFrame(columns=["Sede","Fecha","VolumenMensual","MetaCitas"])
    df_volumen.to_csv(ARCHIVO_VOLUMEN, index=False)
else:
    df_volumen = pd.read_csv(ARCHIVO_VOLUMEN)

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
        df_dia = df_dia.sort_values("Hora")

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
                if not row["Hora"]:
                    continue
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

        zona_peru = pytz.timezone("America/Lima")
        hora_actual = datetime.now(zona_peru).strftime('%d/%m/%Y %H:%M:%S')

        st.title("📊 Dashboard Ejecutivo General")

        col_refresh1, col_refresh2 = st.columns([6,2])
        with col_refresh1:
            st.caption(f"Última actualización: {hora_actual} (Perú)")
        with col_refresh2:
            if st.button("🔄 Actualizar"):
                st.rerun()

        st.divider()

        # =====================================================
        # ⭐ LAYOUT FILTROS + DASHBOARD
        # =====================================================
        col_filtros, col_dashboard = st.columns([1,3])

        # =============================
        # FILTROS
        # =============================
        with col_filtros:
        
            st.subheader("🎛 Filtros")
        
            sede_admin = st.selectbox(
                "Sede",
                ["TODAS"] + SEDES,
                key="admin_sede_selector"
            )
        
            if sede_admin == "TODAS":
                df_admin_filtrado = df.copy()
            else:
                df_admin_filtrado = df[df["Sede"] == sede_admin].copy()
        
            # ⭐ NO DETENER APP
            if df_admin_filtrado.empty:
                st.warning("No hay registros para la sede seleccionada")
                df_admin_filtrado = pd.DataFrame(columns=df.columns)
        
            # ⭐ FECHA SEGURA
            df_admin_filtrado["Fecha"] = pd.to_datetime(
                df_admin_filtrado["Fecha"], errors="coerce"
            )
        
            # ⭐ SI NO HAY FECHAS → usar año actual
            if df_admin_filtrado["Fecha"].dropna().empty:
                año_sel = datetime.today().year
                mes_sel = datetime.today().month
            else:
                df_admin_filtrado = df_admin_filtrado.dropna(subset=["Fecha"])
        
                año_sel = st.selectbox(
                    "Año",
                    sorted(df_admin_filtrado["Fecha"].dt.year.unique(), reverse=True),
                    key="admin_year"
                )
        
                mes_sel = st.selectbox(
                    "Mes",
                    list(range(1,13)),
                    index=datetime.today().month-1,
                    format_func=lambda x: calendar.month_name[x],
                    key="admin_month"
                )

        # =============================
        # DASHBOARD
        # =============================
        with col_dashboard:
        
            df_mes = df_admin_filtrado[
                (df_admin_filtrado["Fecha"].dt.year == año_sel) &
                (df_admin_filtrado["Fecha"].dt.month == mes_sel)
            ]
        
            st.subheader("🌎 Resumen Ejecutivo")
        
            total_mes = len(df_mes)
            efectivas = len(df_mes[df_mes["Estado"] == "Asistió"])
            no_show = len(df_mes[df_mes["Estado"] == "No asistió"])
            reprogramadas = len(df_mes[df_mes["Estado"] == "Reprogramada"])
        
            efectividad_pct = round((efectivas/total_mes)*100,1) if total_mes>0 else 0
            no_show_pct = round((no_show/total_mes)*100,1) if total_mes>0 else 0
        
            # ⭐ SEMÁFORO
            if efectividad_pct >= 80:
                semaforo = "🟢"
            elif efectividad_pct >= 60:
                semaforo = "🟡"
            else:
                semaforo = "🔴"
        
            # ⭐ PROYECCIÓN
            dias_mes = calendar.monthrange(año_sel, mes_sel)[1]
            dia_actual = datetime.today().day
            ritmo_diario = total_mes/dia_actual if dia_actual>0 else 0
            proyeccion = int(ritmo_diario*dias_mes)
        
            # ⭐ META
            df_validas = df_mes[df_mes["Estado"].isin(["Pendiente","Asistió"])]
            total_validas = len(df_validas)
        
            if sede_admin == "TODAS":
                meta_total = metas["MetaMensual"].sum()
            else:
                fila_meta = metas[metas["Sede"] == sede_admin]
                meta_total = int(fila_meta["MetaMensual"].values[0]) if not fila_meta.empty else 0
        
            avance_meta_pct = round((total_validas/meta_total)*100,1) if meta_total>0 else 0
        
            # ⭐ KPI PRINCIPALES
            c1,c2,c3,c4,c5 = st.columns(5)
            c1.metric("📅 Total citas", total_mes)
            c2.metric("✅ Efectivas", efectivas)
            c3.metric("❌ No Show", no_show)
            c4.metric("🔄 Reprogramadas", reprogramadas)
            c5.metric("🎯 Meta", meta_total)            
        
            st.divider()
        
            # ⭐ KPI AVANZADOS + META (MISMA FILA)
            cA,cB,cC,cD = st.columns(4)
            cA.metric(f"{semaforo} % Efectividad", f"{efectividad_pct}%")
            cB.metric("⚠ % No Show", f"{no_show_pct}%")
            cC.metric("📈 Proyección fin mes", proyeccion)
            cD.metric("📊 Avance meta", f"{avance_meta_pct}%")
        
            if meta_total > 0:
                st.progress(min(total_validas/meta_total,1.0))
        
            st.divider()
        
            # ⭐ ALERTAS
            col_alerta, col_ritmo = st.columns([2,1])
        
            with col_alerta:
                if efectividad_pct < 60:
                    st.error("🚨 Riesgo alto: baja asistencia")
                elif efectividad_pct < 80:
                    st.warning("⚠ Asistencia moderada")
                else:
                    st.success("✅ Excelente asistencia")
        
            with col_ritmo:
                st.info(f"📊 Ritmo actual:{round(ritmo_diario,1)} citas/día")

        # =====================================================
        # ⭐ DESCARGAR EXCEL
        # =====================================================
        st.subheader("⬇ Exportar reporte")

        excel_file = generar_excel_ejecutivo(df_mes, metas, año_sel, mes_sel)

        st.download_button(
            label="📥 Descargar Excel",
            data=excel_file,
            file_name=f"reporte_{sede_admin}_{mes_sel}_{año_sel}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.divider()

        # =====================================================
        # CALENDARIO
        # =====================================================
        st.subheader("📅 Calendario")
        
        # ⭐ FILTRO SEDE CALENDARIO
        sede_cal = st.selectbox(
            "Filtrar sede calendario",
            ["TODAS"] + SEDES,
            key="admin_cal_sede"
        )
        
        # ⭐ FILTRAR DATA
        if sede_cal == "TODAS":
            df_cal = df_mes.copy()
        else:
            df_cal = df_mes[df_mes["Sede"] == sede_cal].copy()
        
        # ⭐ CONTEO
        conteo = (
            df_cal.groupby(df_cal["Fecha"].dt.day)["ID"].count().to_dict()
            if not df_cal.empty else {}
        )
        
        # ⭐ CALENDARIO (ESTO NO CAMBIA)
        cal = calendar.monthcalendar(año_sel, mes_sel)
        
        html = "<table style='width:100%; text-align:center; border-collapse:collapse;'>"
        html += "<tr><th>L</th><th>M</th><th>M</th><th>J</th><th>V</th><th>S</th><th>D</th></tr>"
        
        for semana in cal:
        for semana in cal:
            html += "<tr>"
            for dia in semana:
                if dia == 0:
                    html += "<td style='border:1px solid #ddd;'></td>"
                else:
                    cant = conteo.get(dia,0)
        
                    color = "#2ECC71" if cant > 0 else "#2C3E50"
        
                    html += f"<td style='padding:8px;border:1px solid #ddd;'><b>{dia}</b><br><span style='color:{color}; font-weight:600;'>{cant}</span></td>"
            html += "</tr>"
        
        html += "</table>"
        st.markdown(html, unsafe_allow_html=True)

        # =====================================================
        # 🔥 ELIMINACIÓN CITAS ADMIN
        # =====================================================
        st.subheader("🗑 Eliminación de citas (modo supervisor)")

        fecha_admin = st.date_input(
            "Filtrar fecha",
            value=datetime.now().date(),
            key="admin_fecha_delete"
        )

        df_del = df_admin_filtrado.copy()
        df_del["Fecha"] = pd.to_datetime(df_del["Fecha"]).dt.date
        df_del = df_del[df_del["Fecha"] == fecha_admin]

        if df_del.empty:
            st.info("No hay citas para esa fecha")
        else:
            for _, row in df_del.iterrows():

                col1, col2 = st.columns([6,1])

                with col1:
                    st.markdown(f"""
                    **ID:** {row['ID']}  
                    **Sede:** {row['Sede']}  
                    **Cliente:** {row['Nombre']}  
                    **Hora:** {row['Hora']}  
                    **Estado:** {row['Estado']}
                    """)

                with col2:
                    if st.button(f"🗑 Eliminar {row['ID']}", key=f"del_admin_{row['ID']}"):
                        df = df[df["ID"] != row["ID"]]
                        df.to_csv(ARCHIVO_CITAS, index=False)
                        st.success("Cita eliminada")
                        st.rerun()
    # =====================================================
    # TAB 2 - PLANIFICACIÓN ANUAL
    # =====================================================
    with tab2:
    
        st.title("🎯 Planificación anual de citas")
    
        sede_vol = st.selectbox("Sede", SEDES)
        año_plan = st.selectbox("Año", [datetime.today().year, datetime.today().year+1])
    
        meses_es = [
            "Enero","Febrero","Marzo","Abril","Mayo","Junio",
            "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"
        ]
    
        porcentaje_citas = 0.40
    
        # =============================
        # INIT SESSION
        # =============================
        if "plan_df" not in st.session_state:
            st.session_state.plan_df = pd.DataFrame({
                "Mes": list(range(1,13)),
                "NombreMes": meses_es,
                "Volumen": [0]*12,
                "%Citas": [porcentaje_citas]*12,
                "MetaCitas": [0]*12
            })
    
        # =============================
        # EDITOR
        # =============================
        edited = st.data_editor(
            st.session_state.plan_df[["NombreMes","Volumen","%Citas","MetaCitas"]],
            num_rows="fixed",
            use_container_width=True,
            column_config={
                "NombreMes": st.column_config.TextColumn("Mes", disabled=True),
                "%Citas": st.column_config.NumberColumn("% citas", disabled=True),
                "MetaCitas": st.column_config.NumberColumn("Meta citas", disabled=True)
            },
            key="plan_editor"
        )
        
        # ⭐ LIMPIEZA NUMÉRICA
        preview = edited.copy()
        preview["Volumen"] = pd.to_numeric(preview["Volumen"], errors="coerce").fillna(0)
        
        # ⭐ CALCULO META
        preview["MetaCitas"] = (preview["Volumen"] * porcentaje_citas).round().astype(int)
        
        # ⭐ ACTUALIZAR SESSION
        st.session_state.plan_df["Volumen"] = preview["Volumen"].values
        st.session_state.plan_df["MetaCitas"] = preview["MetaCitas"].values
    
        # =============================
        # GUARDAR
        # =============================
        if st.button("💾 Guardar planificación anual"):
    
            guardar = st.session_state.plan_df.copy()
    
            guardar["Sede"] = sede_vol
            guardar["Año"] = año_plan
    
            df_volumen = df_volumen[
                ~(
                    (df_volumen["Sede"] == sede_vol) &
                    (df_volumen["Año"] == año_plan)
                )
            ]
    
            df_volumen = pd.concat(
                [df_volumen, guardar[["Sede","Año","Mes","Volumen","%Citas","MetaCitas"]]],
                ignore_index=True
            )
    
            df_volumen.to_csv(ARCHIVO_VOLUMEN, index=False)
    
            st.success("Planificación guardada correctamente")

# =============================
# ASESOR
# =============================
else:

    tab1, tab2, tab3 = st.tabs(["📅 Agendar","📋 Gestión de Citas","📈 Mi Avance"])

    # =====================================================
    # TAB 1 - AGENDAR (DISEÑO MEJORADO 3 COLUMNAS)
    # =====================================================
    with tab1:
        st.title("Agendar Cita")
    
        today = datetime.now().date()  # ✅ fecha segura
    
        col1, col2, col3 = st.columns([1,1.2,2])
    
        # ==============================
        # COLUMNA 1 - DATOS CORTOS
        # ==============================
        with col1:
            fecha = st.date_input(
                "Fecha",
                value=today,
                min_value=today
            )
        
            hora = st.selectbox(
                "Hora inicio",
                [f"{h:02d}:00" for h in range(8,19)],
            )
        
            duracion = st.selectbox(
                "Duración (horas)",
                list(range(1,9)),
                index=0,
            )
    
        # ==============================
        # COLUMNA 2 - VEHÍCULO
        # ==============================
        with col2:
            tecnico = st.selectbox(
                "Técnico",
                obtener_tecnicos(st.session_state.sede),
            )
    
            placa = st.text_input(
                "Placa",
                max_chars=8,
                placeholder="Ej: ABC123",
            ).upper()
    
            modelo = st.text_input(
                "Modelo",
                placeholder="Ej: Wave 110",
            )
    
        # ==============================
        # COLUMNA 3 - CLIENTE
        # ==============================
        with col3:
            nombre = st.text_input(
                "Nombres y apellidos",
                placeholder="Nombre completo del cliente",
            )
    
            celular = st.text_input(
                "Celular",
                max_chars=9,
                placeholder="9XXXXXXXX",
            )
    
            servicio = st.text_input("Tipo de Servicio",
                placeholder="Ej: Mantenimiento + cambio de pastillas",
            )
    
        st.divider()
    
        # =====================================================
        # GUARDAR CITA
        # =====================================================
        if st.button("Guardar Cita", use_container_width=True):
    
            # Validaciones básicas
            if not placa or not modelo or not nombre or not servicio:
                st.warning("Completa todos los datos obligatorios")
                st.stop()
    
            if not celular.isdigit() or len(celular) != 9:
                st.warning("El celular debe tener 9 dígitos numéricos")
                st.stop()
    
            df_temp = df.copy()
            df_temp["Fecha"] = pd.to_datetime(df_temp["Fecha"]).dt.date
    
            # 🔥 SOLO VALIDAR CITAS ACTIVAS
            df_dia = df_temp[
                (df_temp["Sede"] == st.session_state.sede) &
                (df_temp["Fecha"] == fecha) &
                (df_temp["Estado"].isin(["Pendiente","Asistió"]))
            ]
            dup = df_dia[df_dia["Celular"] == celular]
            if not dup.empty:
                st.warning("Cliente ya tiene cita ese día")
                st.stop()

            inicio_nuevo = datetime.strptime(hora,"%H:%M")
            fin_nuevo = inicio_nuevo + timedelta(hours=duracion)
    
            conflicto = False
    
            for _, row in df_dia.iterrows():
                if row["Tecnico"] == tecnico:
    
                    inicio_exist = datetime.strptime(row["Hora"],"%H:%M")
                    fin_exist = inicio_exist + timedelta(hours=row["Duracion"])
    
                    if inicio_nuevo < fin_exist and fin_nuevo > inicio_exist:
                        conflicto = True
                        break
    
            if conflicto:
                st.error("Conflicto de horario con otra cita activa")
            else:
                nuevo_id = df["ID"].max() + 1 if not df.empty else 1
    
                nueva = pd.DataFrame([{
                    "ID": nuevo_id,
                    "Sede": st.session_state.sede,
                    "Fecha": str(fecha),
                    "Hora": hora,
                    "Tecnico": tecnico,
                    "Placa": placa.upper(),
                    "Modelo": modelo,
                    "Nombre": nombre,
                    "Celular": celular,
                    "TipoServicio": servicio,
                    "Duracion": duracion,
                    "Estado": "Pendiente",
                    "Reprogramada": "No"
                }])
    
                df = pd.concat([df, nueva], ignore_index=True)
                df.to_csv(ARCHIVO_CITAS, index=False)
    
                st.success("Cita registrada correctamente")
                st.rerun()
    
        # =====================================================
        # TABLERO (SOLO CITAS ACTIVAS)
        # =====================================================
        mostrar_tablero(
            df[
                (df["Sede"] == st.session_state.sede) &
                (df["Fecha"] == str(fecha)) &
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
            value=datetime.now().date(),
            key="filtro_gestion"
        )
    
        df_sede = df[df["Sede"] == st.session_state.sede].copy()
        df_sede["Fecha"] = pd.to_datetime(df_sede["Fecha"], errors="coerce").dt.date
        df_sede = df_sede.dropna(subset=["Fecha"])
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
                    **Duración:** {row['Duracion']} h  
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
    
                            horas_lista = [f"{h:02d}:00" for h in range(8,19)]
                            index_hora = horas_lista.index(row["Hora"]) if row["Hora"] in horas_lista else 0
                            
                            nueva_hora = st.selectbox(
                                "Hora",
                                horas_lista,
                                index=index_hora,
                                key=f"edit_hora_{row['ID']}"
                            )

                            nueva_duracion = st.number_input(
                                "Duración (horas)",
                                min_value=1,
                                max_value=8,
                                value=int(row["Duracion"]),
                                key=f"edit_duracion_{row['ID']}"
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
                                fin_nuevo = inicio_nuevo + timedelta(hours=nueva_duracion)
    
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
                                    df.loc[df["ID"] == row["ID"], "Duracion"] = nueva_duracion
    
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
    
                        nueva_duracion = st.number_input(
                            "Duración (horas)",
                            min_value=1,
                            max_value=8,
                            value=int(row["Duracion"]),
                            key=f"reprog_duracion_{row['ID']}"
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
                            fin_nuevo = inicio_nuevo + timedelta(hours=nueva_duracion)
    
                            for _, r in df_conflicto.iterrows():
                                inicio_exist = datetime.strptime(r["Hora"],"%H:%M")
                                fin_exist = inicio_exist + timedelta(hours=r["Duracion"])
    
                                if inicio_nuevo < fin_exist and fin_nuevo > inicio_exist:
                                    conflicto = True
                                    break
    
                            if conflicto:
                                st.error("Conflicto de horario con otra cita activa")
                            else:
                                nuevo_id = df["ID"].max() + 1 if not df.empty else 1
    
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
                                    "Duracion": nueva_duracion,
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
        df_sede["Fecha"] = pd.to_datetime(df_sede["Fecha"], errors="coerce")
        df_sede = df_sede.dropna(subset=["Fecha"])
    
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





