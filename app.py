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

# ---------- ESTADÍSTICAS ----------
st.markdown("---")
st.subheader("📈 Estadísticas")

# contadores
total_dias = len([d for d in dias if str(d) in cal])
contador = {nombre: 0 for nombre in CODIGOS}
fines = {nombre: 0 for nombre in CODIGOS}

for dia in dias:
    key = str(dia)
    turno_corto = cal.get(key, {}).get("turno", "")
    if not turno_corto:
        continue
    nombre = NOMBRES.get(turno_corto, "Otro")
    contador[nombre] += 1
    if dia.weekday() >= 5:  # sábado=5, domingo=6
        fines[nombre] += 1

for nombre in CODIGOS:
    st.write(f"**{nombre}** → {contador[nombre]} días ({fines[nombre]} fin de semana)")    

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

# ---------- VISTA MENSUAL ----------
st.markdown("---")
st.subheader("📊 Resumen mensual")

hoy = date.today()
meses = [hoy.replace(day=1) + timedelta(days=32*i) for i in range(3)]
for mes in meses:
    dias_mes = [mes.replace(day=d) for d in range(1, (mes + timedelta(days=32)).day) if (mes.replace(day=d)).month == mes.month]
    st.write(f"**{MESES[mes.month-1].capitalize()} {mes.year}**")
    cols_mes = st.columns(7, gap="small")
    for dia, col in zip(dias_mes, cols_mes):
        with col:
            key = str(dia)
            turno_corto = cal.get(key, {}).get("turno", "")
            turno_largo = NOMBRES.get(turno_corto, "Otro")
            st.markdown(
                f"<div style='background:{COLORES.get(turno_largo, '#ffffff')};"
                f"padding:2px;border-radius:3px;text-align:center;font-size:0.7em'>"
                f"{dia.day}</div>",
                unsafe_allow_html=True
            )