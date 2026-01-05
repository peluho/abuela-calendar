import streamlit as st
import json, os, pytz
from datetime import date, timedelta
from git import Repo

# ---------- CONFIG ----------
REPO_PATH   = "."               # estamos dentro del repo
JSON_FILE   = "calendar.json"
PERSONAS    = ["Fer", "Nines", "Conchi", "Otro"]
COLORES     = {"Fer":"#8ac6d1","Nines":"#ffb6b9","Conchi":"#cae4db","Otro":"#ffd36e"}
DIA_SEM     = ["L","M","X","J","V","S","D"]
MESES       = ["ene","feb","mar","abr","may","jun","jul","ago","sep","oct","nov","dic"]
CODIGOS     = {"Fer":"F", "Nines":"N", "Conchi":"C", "Otro":"Otro"}  # largo → corto
NOMBRES     = {v:k for k,v in CODIGOS.items()}                        # corto → largo
# Clave GitHub (máquina) → la guardamos en Secrets de Streamlit
TOKEN       = st.secrets.get("GH_TOKEN", os.getenv("GH_TOKEN"))
REPO_URL    = st.secrets.get("REPO_URL", os.getenv("REPO_URL"))  # https://<token>@github.com/USER/REPO.git

st.set_page_config(page_title="Cuidados abuela", layout="centered")
st.title("📅 Turnos cuidados abuela")
# st.write("TOKEN existe:", bool(st.secrets.get("GH_TOKEN")))
# st.write("REPO_URL existe:", bool(st.secrets.get("REPO_URL")))

# ---------- FUNCIONES ----------
@st.cache_data
def cargar_calendario():
    ruta = "calendar.json"
    if not os.path.exists(ruta):
        return {}
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            contenido = f.read().strip()
            if not contenido:
                return {}
            return json.loads(contenido)
    except (json.JSONDecodeError, OSError):
        return {}          # <-- silencioso
    
def guardar_json(data):
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# def guardar_y_commit(data, msg="Update calendar"):
#     with open(JSON_FILE, "w", encoding="utf-8") as f:
#         json.dump(data, f, ensure_ascii=False, indent=2)
#     repo = Repo(REPO_PATH)
#     repo.git.add(JSON_FILE)
#     repo.index.commit(msg)
#     origin = repo.remote(name="origin")
    # origin.push()
    # url_con_token = st.secrets["REPO_URL"]
    # repo.git.push(url_con_token, "main")   # main o la rama que use

def guardar_y_commit(data, msg="Update calendar"):
    guardar_json(data)
    # repo = Repo(REPO_PATH)

    # # <-- AÑADE ESTAS DOS LÍNEAS -->
    # with repo.config_writer() as cfg:
    #     cfg.set_value("user", "name", "abuela-bot")
    #     cfg.set_value("user", "email", "abuela@bot.local")

    # repo.git.add(JSON_FILE)
    # repo.index.commit(msg)

def rango_visible():
    hoy = date.today()
    # mostramos 15 días atrás y 45 adelante → 2 meses aprox
    return [hoy + timedelta(days=i) for i in range(-15, 46)]

# ---------- LÓGICA ----------
# cargar_calendario.clear()
cal = cargar_calendario()
dias = rango_visible()


# if not cal and os.path.isfile(JSON_FILE):
    # st.warning("El archivo calendar.json estaba vacío o corrupto; se ha inicializado a {}.")

st.markdown("Pulsa sobre el día para cambiar turno o dejar comentario.")

# Formulario lateral para nuevos comentarios
# ---------- SIDEBAR ----------
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
        # st.rerun()

    if st.button("🔒 Subir cambios a GitHub"):
        url_con_token = st.secrets["REPO_URL"]
        try:
            repo = Repo(REPO_PATH)
            repo.git.push(url_con_token, "main")
            st.success("✅ Cambios subidos")
        except Exception as e:
            st.error(f"Error al subir: {e}")

    st.markdown("---")  # separador visual
    if st.button("Reiniciar calendario"):
        # vaciamos el dict y sobrescribimos el archivo
        cal.clear()
        with open(JSON_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
        guardar_y_commit(cal, "Reinicio completo del calendario")
        st.success("Calendario reiniciado")
        st.rerun()

# Tabla de días
st.markdown("---")
cols = st.columns(7)   # una por día de semana
for i, dia in enumerate(dias):
    with cols[i % 7]:
        key = str(dia)
        turno = cal.get(key, {}).get("turno", "")
        comms = cal.get(key, {}).get("comentarios", [])
        turno_corto = cal.get(key, {}).get("turno", "")
        turno_largo = NOMBRES.get(turno_corto, "Otro")
        color       = COLORES.get(turno_largo, "#ffffff")

        # Tarjetita
        st.markdown(
            f"<div style='background:{color};padding:6px;border-radius:6px;text-align:center'>"
            f"<b>{DIA_SEM[dia.weekday()]}</b><br>{dia.day} {MESES[dia.month-1]}"
            f"<br><small>{turno_largo or '-'}</small></div>",
            unsafe_allow_html=True
        )
        # Selector
        nuevo = st.selectbox("Cambiar", [""]+list(CODIGOS.keys()), key=f"sel{key}",
                     format_func=lambda x: x if x else "-",
                     label_visibility="collapsed")
        if nuevo and nuevo != turno_largo:
            cal.setdefault(key, {})["turno"] = CODIGOS[nuevo]
            guardar_y_commit(cal, f"Turno {dia} → {nuevo}")
            # st.rerun()
        # Mini lista de comentarios
        if comms:
            with st.expander("📝"):
                for c in comms:
                    st.caption(c)