import json, os
from datetime import date, timedelta
import streamlit as st
from git import Repo
import requests
from calendar import monthrange

# ---------- CONFIG ----------
JSON_FILE = "calendar.json"
CODIGOS = {"Fer": "F", "Nines": "N", "Conchi": "C", "Otro": "Otro"}
NOMBRES = {v: k for k, v in CODIGOS.items()}
COLORES = {"Nines": "#8aa1d1", "Fer": "#ffb6b9", "Conchi": "#cae4d6", "Otro": "#ffd36e"}
DIA_SEM = list("LMXJVSD")
MESES = "ene feb mar abr may jun jul ago sep oct nov dic".split()

año = date.today().year
FESTIVOS_JSON = f"festivos_{año}.json"

# ---------- FUNCIONES ----------
@st.cache_data(show_spinner=False)
def cargar_festivos_españa():
    if os.path.exists(FESTIVOS_JSON):
        with open(FESTIVOS_JSON, encoding="utf-8") as f:
            return set(json.load(f))
    url = f"https://date.nager.at/api/v3/publicholidays/{año}/ES"
    try:
        res = requests.get(url, timeout=5)
        res.raise_for_status()
        dias = [dt["date"] for dt in res.json()]
        with open(FESTIVOS_JSON, "w", encoding="utf-8") as f:
            json.dump(dias, f)
        return set(dias)
    except Exception:
        return set()

festivos = cargar_festivos_españa()

@st.cache_data
def cargar_calendario():
    if not os.path.exists(JSON_FILE):
        return {}
    try:
        with open(JSON_FILE, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def guardar_json(data):
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ---------- LÓGICA ----------
cal = cargar_calendario()
hoy = date.today()

# ---------- SIDEBAR ----------
# ---------- ESTADÍSTICAS REFINADAS + GRÁFICOS ----------
# import matplotlib.pyplot as plt
import pandas as pd
from calendar import monthrange

def contar_por_tipo(dias, es_tipo):
    cont = {nombre: 0 for nombre in CODIGOS}
    for dia in dias:
        key = str(dia)
        turno = cal.get(key, {}).get("turno", "")
        if turno:
            nombre = NOMBRES.get(turno, "Otro")
            if es_tipo(dia):
                cont[nombre] += 1
    return cont

# ---------- SIDEBAR ESTADÍSTICAS ----------
with st.sidebar:
    st.header("📊 Estadísticas")

    # meses
    for i in range(3):
        mes = (hoy.replace(day=1) + timedelta(days=32*i)).replace(day=1)
        ultimo_dia = monthrange(mes.year, mes.month)[1]
        dias_mes = [mes.replace(day=d) for d in range(1, ultimo_dia + 1)]
        total_mes = contar_por_tipo(dias_mes, lambda _: True)
        fines_mes = contar_por_tipo(dias_mes, lambda d: d.weekday() >= 5)
        fest_mes = contar_por_tipo(dias_mes, lambda d: d.isoformat() in festivos)

        with st.expander(f"{MESES[mes.month-1].capitalize()} {mes.year}"):
            for nombre in CODIGOS:
                st.write(f"{nombre}: **{total_mes[nombre]}** días | **{fines_mes[nombre]}** finde | **{fest_mes[nombre]}** festivos")

    # año completo
    año_actual = hoy.year
    dias_año = [date(año_actual, 1, 1) + timedelta(days=d) for d in range(366)]
    total_año = contar_por_tipo(dias_año, lambda _: True)
    fines_año = contar_por_tipo(dias_año, lambda d: d.weekday() >= 5)
    fest_año = contar_por_tipo(dias_año, lambda d: d.isoformat() in festivos)

    with st.expander(f"Año {año_actual}"):
        for nombre in CODIGOS:
            st.write(f"{nombre}: **{total_año[nombre]}** días | **{fines_año[nombre]}** finde | **{fest_año[nombre]}** festivos")

            # ---------- EXPORTAR CALENDARIO COMPLETO ----------
    st.markdown("---")
    st.subheader("📄 Exportar calendario")

    if st.button("Descargar calendario mensual"):
        mes = hoy.replace(day=1)
        ultimo_dia = monthrange(mes.year, mes.month)[1]
        dias_mes = [mes.replace(day=d) for d in range(1, ultimo_dia + 1)]

        # HTML bonito
        html_lines = [f"<h2>Calendario {MESES[mes.month-1].capitalize()} {mes.year}</h2><table border='1' style='border-collapse:collapse;width:100%;text-align:center;'>"]
        html_lines.append("<tr>" + "".join(f"<th>{d}</th>" for d in DIA_SEM) + "</tr>")

        inicio = mes - timedelta(days=mes.weekday())
        dias_vis = [inicio + timedelta(days=d) for d in range(42)]
        filas = [dias_vis[i:i+7] for i in range(0, 42, 7)]

        for sem in filas:
            html_lines.append("<tr>")
            for dia in sem:
                es_mes = dia.month == mes.month
                key = str(dia)
                turno = cal.get(key, {}).get("turno", "")
                nombre = NOMBRES.get(turno, "Otro")
                color = COLORES.get(nombre, "#ffffff") if es_mes else "#eeeeee"
                texto = f"{dia.day}" if es_mes else ""
                inicial = CODIGOS[nombre] if es_mes and turno else ""
                html_lines.append(f"<td style='background:{color};width:14%;height:60px;'>"
                                  f"<div style='font-size:0.8em;'>{texto}</div>"
                                  f"<div style='font-weight:bold;'>{inicial}</div></td>")
            html_lines.append("</tr>")
        html_lines.append("</table>")

        html_str = "\n".join(html_lines)
        st.sidebar.download_button("📥 Descargar HTML", data=html_str, file_name=f"calendario_{mes.month}_{mes.year}.html", mime="text/html")

        st.markdown("---")
        st.header("Añadir comentario")
        dia_sel = st.date_input("Día", date.today())
        txt = st.text_area("Comentario (opcional)")
        if st.button("Guardar comentario"):
            key = str(dia_sel)
            cal.setdefault(key, {}).setdefault("comentarios", []).append(txt)
            guardar_json(cal)
            st.success("Guardado")

        if st.button("🔒 Subir cambios a GitHub"):
            try:
                repo = Repo(".")
                with repo.config_writer() as cfg:
                    cfg.set_value("user", "name", "abuela-bot")
                    cfg.set_value("user", "email", "abuela@bot.local")
                repo.git.add(JSON_FILE)
                repo.index.commit("Update calendar")
                repo.git.push(st.secrets["REPO_URL"], "main")
                st.success("✅ Cambios subidos")
            except Exception as e:
                st.error(f"Error al subir: {e}")

        if st.button("Reiniciar calendario"):
            cal.clear()
            guardar_json({})
            st.success("Calendario reiniciado")
            st.rerun()

# # ---------- GRÁFICOS (solo Streamlit) ----------
# st.markdown("---")
# st.subheader("📈 Gráficos")

# # barra mes actual
# mes = hoy.replace(day=1)
# ultimo_dia = monthrange(mes.year, mes.month)[1]
# dias_mes = [mes.replace(day=d) for d in range(1, ultimo_dia + 1)]
# total_mes = contar_por_tipo(dias_mes, lambda _: True)
# df_mes = pd.DataFrame({"Persona": list(CODIGOS.keys()),
#                        "Días": [total_mes[n] for n in CODIGOS]})
# st.bar_chart(df_mes.set_index("Persona"))

# # pastel año (simulado con barra horizontal)
# año_actual = hoy.year
# dias_año = [date(año_actual, 1, 1) + timedelta(days=d) for d in range(366)]
# total_año = contar_por_tipo(dias_año, lambda _: True)
# df_año = pd.DataFrame({"Persona": list(CODIGOS.keys()),
#                        "Días": [total_año[n] for n in CODIGOS]})
# st.bar_chart(df_año.set_index("Persona"))



# ---------- LEYENDA ----------
st.markdown("---")
st.subheader("📅 Meses editables")
col_leyenda = st.columns(len(CODIGOS))
for i, (nombre, cod) in enumerate(CODIGOS.items()):
    with col_leyenda[i]:
        st.markdown(
            f"<div style='background:{COLORES[nombre]};padding:4px;border-radius:4px;"
            f"text-align:center;color:#000;font-weight:bold'>"
            f"{nombre}</div>",
            unsafe_allow_html=True
        )

# ---------- 3 MESES EDITABLES (celda bonita + selector debajo) ----------
hoy = date.today()
for i in range(3):
    mes = (hoy.replace(day=1) + timedelta(days=32*i)).replace(day=1)
    st.write(f"### {MESES[mes.month-1].capitalize()} {mes.year}")

    hdr = st.columns(7, gap="small")
    for d, col in zip(DIA_SEM, hdr):
        with col:
            st.markdown(f"**{d}**")

    inicio = mes - timedelta(days=mes.weekday())
    dias_visibles = [inicio + timedelta(days=d) for d in range(42)]
    filas = [dias_visibles[i:i+7] for i in range(0, 42, 7)]

    # pre-cargamos cambios
    for dia in dias_visibles:
        es_mes = dia.month == mes.month
        if not es_mes:
            continue
        key = str(dia)
        sel_key = f"sel_mes_{mes.month}_{dia.day}"
        if st.session_state.get(sel_key):
            cal.setdefault(key, {})["turno"] = CODIGOS[st.session_state[sel_key]]
            guardar_json(cal)
            st.session_state[sel_key] = None

    # pintamos fila a fila
    for semana in filas:
        cols = st.columns(7, gap="small")
        for dia, col in zip(semana, cols):
            with col:
                es_mes = dia.month == mes.month
                key = str(dia)
                turno_corto = cal.get(key, {}).get("turno", "")
                turno_largo = NOMBRES.get(turno_corto, "Otro")
                color = COLORES.get(turno_largo, "#ffffff") if es_mes else "#eeeeee"
                texto = f"{dia.day}" if es_mes else ""
                inicial = CODIGOS[turno_largo] if es_mes and turno_corto else ""
                es_festivo = dia.isoformat() in festivos
                borde_fest = "2px solid #ff4d4d" if es_festivo else "none"
                cerco_color = f"2px solid {color}" if es_mes else "none"

                if es_mes:
                    # celda bonita
                    st.markdown(
                        f"<div style='background:{color};border:{cerco_color};border-top:{borde_fest};"
                        f"padding:6px;border-radius:6px;text-align:center;font-size:1em;"
                        f"min-height:48px;display:flex;flex-direction:column;justify-content:space-between;'>"
                        f"<div style='font-size:0.8em;color:#333'>{texto}</div>"
                        f"<div style='font-weight:bold;color:#000;font-size:1.1em'>{inicial}</div>"
                        f"</div>",
                        unsafe_allow_html=True
                    )
                    # selector debajo, mismo orden
                    sel_key = f"sel_mes_{mes.month}_{dia.day}"
                    nuevo = st.selectbox(
                        "⇄",  # texto corto para no romper
                        options=list(CODIGOS.keys()),
                        index=list(CODIGOS.keys()).index(turno_largo),
                        key=sel_key,
                        format_func=lambda x: x,
                        label_visibility="collapsed"
                    )
                    if nuevo and nuevo != turno_largo:
                        cal.setdefault(key, {})["turno"] = CODIGOS[nuevo]
                        guardar_json(cal)
                        st.rerun()
                else:
                    st.markdown(
                        f"<div style='background:#eeeeee;padding:6px;border-radius:6px;min-height:48px;'></div>",
                        unsafe_allow_html=True
                    )
# ---------- ESTADÍSTICAS Y GRÁFICOS FINALES ----------
st.markdown("---")
st.header("📊 Resumen final")

# estadísticas
st.subheader("Estadísticas por mes")
for i in range(3):
    mes = (hoy.replace(day=1) + timedelta(days=32*i)).replace(day=1)
    ultimo_dia = monthrange(mes.year, mes.month)[1]
    dias_mes = [mes.replace(day=d) for d in range(1, ultimo_dia + 1)]
    total_mes = contar_por_tipo(dias_mes, lambda _: True)
    fines_mes = contar_por_tipo(dias_mes, lambda d: d.weekday() >= 5)
    fest_mes = contar_por_tipo(dias_mes, lambda d: d.isoformat() in festivos)

    with st.expander(f"{MESES[mes.month-1].capitalize()} {mes.year}"):
        for nombre in CODIGOS:
            st.write(f"{nombre}: **{total_mes[nombre]}** días | **{fines_mes[nombre]}** finde | **{fest_mes[nombre]}** festivos")

st.subheader("Estadísticas anuales")
año_actual = hoy.year
dias_año = [date(año_actual, 1, 1) + timedelta(days=d) for d in range(366)]
total_año = contar_por_tipo(dias_año, lambda _: True)
fines_año = contar_por_tipo(dias_año, lambda d: d.weekday() >= 5)
fest_año = contar_por_tipo(dias_año, lambda d: d.isoformat() in festivos)
for nombre in CODIGOS:
    st.write(f"{nombre}: **{total_año[nombre]}** días | **{fines_año[nombre]}** finde | **{fest_año[nombre]}** festivos")

# ---------- GRÁFICOS (quesito sin matplotlib ni pandas.plot) ----------
st.subheader("📊 Gráficos")

# datos
año_actual = hoy.year
dias_año = [date(año_actual, 1, 1) + timedelta(days=d) for d in range(366)]
total_año = contar_por_tipo(dias_año, lambda _: True)
valores = [total_año[n] for n in CODIGOS]
etiquetas = list(CODIGOS.keys())
colores = [COLORES[n] for n in CODIGOS]

# quesito con st.pyplot
import math
fig, ax = st.pyplot()
ax.pie(valores, labels=etiquetas, autopct='%1.1f%%', colors=colores)
ax.set_title(f"Distribución {año_actual}")
st.pyplot(fig)