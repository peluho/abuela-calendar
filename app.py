import json, os
from datetime import date, timedelta
import streamlit as st
from git import Repo

# ---------- CONFIG ----------
JSON_FILE = "calendar.json"
CODIGOS   = {"Fer": "F", "Nines": "N", "Conchi": "C", "Otro": "Otro"}
NOMBRES   = {v: k for k, v in CODIGOS.items()}
COLORES   = {"Nines": "#8aa1d1", "Fer": "#ffb6b9", "Conchi": "#cae4d6", "Otro": "#ffd36e"}
DIA_SEM   = list("LMXJVSD")
MESES     = "ene feb mar abr may jun jul ago sep oct nov dic".split()

st.set_page_config(page_title="Cuidados abuela", layout="centered")
st.title("📅 Turnos cuidados abuela")
st.markdown("Pulsa sobre el día para cambiar turno o dejar comentario.")

# ---------- FUNCIONES ----------
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

def rango_visible():
    hoy = date.today()
    return [hoy + timedelta(days=i) for i in range(-5, 46)]

# ---------- LÓGICA ----------
cal  = cargar_calendario()
dias = rango_visible()

# ---------- SIDEBAR ----------
with st.sidebar:
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

# ---------- ESTADÍSTICAS (días totales por mes) ----------
st.markdown("---")
st.subheader("📈 Días totales por mes")

for i in range(3):
    mes = (hoy.replace(day=1) + timedelta(days=32*i)).replace(day=1)
    dias_mes = [mes.replace(day=d) for d in range(1, 32) if (mes.replace(day=d)).month == mes.month]
    contador_mes = {nombre: 0 for nombre in CODIGOS}
    for dia in dias_mes:
        key = str(dia)
        turno_corto = cal.get(key, {}).get("turno", "")
        if turno_corto:
            nombre = NOMBRES.get(turno_corto, "Otro")
            contador_mes[nombre] += 1

    st.write(f"**{MESES[mes.month-1].capitalize()} {mes.year}**")
    for nombre, total in contador_mes.items():
        st.write(f"{nombre}: {total} días")

# ---------- CUADRÍCULA RESPONSIVE ----------
semanas = [dias[i:i+7] for i in range(0, len(dias), 7)]
for sem in semanas:
    cols = st.columns([1]*7, gap="small")
    for dia, col in zip(sem, cols):
        with col:
            key = str(dia)
            turno_corto = cal.get(key, {}).get("turno", "")
            turno_largo = NOMBRES.get(turno_corto, "Otro")
            comms = cal.get(key, {}).get("comentarios", [])

            st.markdown(
                f"<div style='background:{COLORES.get(turno_largo, '#ffffff')};"
                f"padding:4px;border-radius:4px;text-align:center;font-size:0.75em'>"
                f"<b>{DIA_SEM[dia.weekday()]}</b><br>{dia.day} {MESES[dia.month - 1]}"
                f"<br><small>{turno_largo or '-'}</small></div>",
                unsafe_allow_html=True
            )

            nuevo = st.selectbox("⇄", [""] + list(CODIGOS.keys()),
                                 key=f"sel{key}",
                                 format_func=lambda x: x if x else "-",
                                 label_visibility="collapsed")
            if nuevo and nuevo != turno_largo:
                cal.setdefault(key, {})["turno"] = CODIGOS[nuevo]
                guardar_json(cal)

            if comms:
                with st.expander("📝"):
                    for c in comms:
                        st.caption(c)

# ---------- VISTA MENSUAL (3 meses, empieza en lunes) ----------
st.markdown("---")
st.subheader("📊 Resumen mensual")

hoy = date.today()
for i in range(3):
    mes = (hoy.replace(day=1) + timedelta(days=32*i)).replace(day=1)
    st.write(f"**{MESES[mes.month-1].capitalize()} {mes.year}**")

    # primer lunes de la semana que contiene el 1 del mes
    primer_dia_mes = mes.weekday()  # 0=Lunes ... 6=Domingo
    inicio = mes - timedelta(days=primer_dia_mes)
    dias_mes_visibles = [inicio + timedelta(days=d) for d in range(42)]  # 6 semanas

    cols_mes = st.columns(7, gap="small")
    for dia in dias_mes_visibles:
        with cols_mes[dia.weekday()]:
            es_mes = dia.month == mes.month
            key = str(dia)
            turno_corto = cal.get(key, {}).get("turno", "")
            turno_largo = NOMBRES.get(turno_corto, "Otro")
            color = COLORES.get(turno_largo, "#ffffff") if es_mes else "#eeeeee"
            texto = f"{dia.day}" if es_mes else ""
            st.markdown(
                f"<div style='background:{color};padding:2px;border-radius:3px;"
                f"text-align:center;font-size:0.7em'>{texto}</div>",
                unsafe_allow_html=True
            )