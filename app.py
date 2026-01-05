import streamlit as st
import json, os, pytz
from datetime import date, timedelta
from git import Repo

# ---------- CONFIG ----------
REPO_PATH   = "."               # estamos dentro del repo
JSON_FILE   = "calendar.json"
COLORES     = {"F":"#8ac6d1","N":"#ffb6b9","C":"#cae4db","Otro":"#ffd36e"}
PERSONAS    = ["F","N","C","Otro"]
DIA_SEM     = ["L","M","X","J","V","S","D"]
MESES       = ["ene","feb","mar","abr","may","jun","jul","ago","sep","oct","nov","dic"]
# Clave GitHub (máquina) → la guardamos en Secrets de Streamlit
TOKEN       = st.secrets.get("GH_TOKEN", os.getenv("GH_TOKEN"))
REPO_URL    = st.secrets.get("REPO_URL", os.getenv("REPO_URL"))  # https://<token>@github.com/USER/REPO.git


# ---------- FUNCIONES ----------
@st.cache_data(show_spinner=False)
def cargar_calendario():
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def guardar_y_commit(data, msg="Update calendar"):
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    repo = Repo(REPO_PATH)
    repo.git.add(JSON_FILE)
    repo.index.commit(msg)
    origin = repo.remote(name="origin")
    origin.push()

def rango_visible():
    hoy = date.today()
    # mostramos 15 días atrás y 45 adelante → 2 meses aprox
    return [hoy + timedelta(days=i) for i in range(-15, 46)]

# ---------- LÓGICA ----------
cargar_calendario.clear()
cal = cargar_calendario()
dias = rango_visible()

st.set_page_config(page_title="Cuidados abuela", layout="centered")
st.title("📅 Turnos cuidados abuela")
st.markdown("Pulsa sobre el día para cambiar turno o dejar comentario.")

# Formulario lateral para nuevos comentarios
with st.sidebar:
    st.header("Añadir comentario")
    dia_sel = st.date_input("Día", date.today())
    txt = st.text_area("Comentario (opcional)")
    if st.button("Guardar comentario"):
        key = str(dia_sel)
        cal.setdefault(key, {})
        cal[key].setdefault("comentarios", []).append(txt)
        guardar_y_commit(cal, f"Comentario {dia_sel}")
        st.success("Guardado")
        st.rerun()

# Tabla de días
st.markdown("---")
cols = st.columns(7)   # una por día de semana
for i, dia in enumerate(dias):
    with cols[i % 7]:
        key = str(dia)
        turno = cal.get(key, {}).get("turno", "")
        comms = cal.get(key, {}).get("comentarios", [])
        color = COLOURS.get(turno, "#ffffff")

        # Tarjetita
        st.markdown(
            f"<div style='background:{color};padding:6px;border-radius:6px;text-align:center'>"
            f"<b>{DIA_SEM[dia.weekday()]}</b><br>{dia.day} {MESES[dia.month-1]}"
            f"<br><small>{turno or '-'}</small></div>",
            unsafe_allow_html=True
        )
        # Selector
        nuevo = st.selectbox("Cambiar", [""]+PERSONAS, key=f"sel{key}",
                             format_func=lambda x: x if x else "-",
                             label_visibility="collapsed")
        if nuevo and nuevo != turno:
            cal.setdefault(key, {})["turno"] = nuevo
            guardar_y_commit(cal, f"Turno {dia} → {nuevo}")
            st.rerun()
        # Mini lista de comentarios
        if comms:
            with st.expander("📝"):
                for c in comms:
                    st.caption(c)