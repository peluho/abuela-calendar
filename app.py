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
with st.sidebar:
    st.header("📊 Estadísticas")
    for i in range(3):
        mes = (hoy.replace(day=1) + timedelta(days=32*i)).replace(day=1)
        ultimo_dia = monthrange(mes.year, mes.month)[1]
        dias_mes = [mes.replace(day=d) for d in range(1, ultimo_dia + 1)]
        contador = {nombre: 0 for nombre in CODIGOS}
        fines = {nombre: 0 for nombre in CODIGOS}
        for dia in dias_mes:
            key = str(dia)
            turno_corto = cal.get(key, {}).get("turno", "")
            if turno_corto:
                nombre = NOMBRES.get(turno_corto, "Otro")
                contador[nombre] += 1
                if dia.weekday() >= 5:
                    fines[nombre] += 1
        with st.expander(f"{MESES[mes.month-1].capitalize()} {mes.year}"):
            for nombre in CODIGOS:
                st.write(f"{nombre}: **{contador[nombre]}** días (**{fines[nombre]}** fin de semana)")

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

# ---------- VISTA MENSUAL EDITABLE ----------
st.markdown("---")
st.subheader("📅 Mes actual editable")

mes_actual = hoy.replace(day=1)
ultimo_dia = monthrange(mes_actual.year, mes_actual.month)[1]
dias_mes = [mes_actual.replace(day=d) for d in range(1, ultimo_dia + 1)]

# Empieza en lunes
inicio = mes_actual - timedelta(days=mes_actual.weekday())
dias_visibles = [inicio + timedelta(days=d) for d in range(42)]

cols_mes = st.columns(7, gap="small")
for dia in dias_visibles:
    with cols_mes[dia.weekday()]:
        es_mes = dia.month == mes_actual.month
        key = str(dia)
        turno_corto = cal.get(key, {}).get("turno", "")
        turno_largo = NOMBRES.get(turno_corto, "Otro")
        color = COLORES.get(turno_largo, "#ffffff") if es_mes else "#eeeeee"
        texto = f"{dia.day}" if es_mes else ""
        es_festivo = dia.isoformat() in festivos
        borde = "2px solid #ff4d4d" if es_festivo else "none"

        st.markdown(
            f"<div style='background:{color};border:{borde};padding:6px;border-radius:6px;"
            f"text-align:center;font-size:1em'>"
            f"{'🎉' if es_festivo else ''}{texto}</div>",
            unsafe_allow_html=True
        )

        if es_mes:
            nuevo = st.selectbox("⇄", [""] + list(CODIGOS.keys()),
                                 key=f"sel_mes_{key}",
                                 format_func=lambda x: x if x else "-",
                                 label_visibility="collapsed")
            if nuevo and nuevo != turno_largo:
                cal.setdefault(key, {})["turno"] = CODIGOS[nuevo]
                guardar_json(cal)

        if es_mes and cal.get(key, {}).get("comentarios"):
            with st.expander("📝"):
                for c in cal[key]["comentarios"]:
                    st.caption(c)