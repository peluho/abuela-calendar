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

# ---------- 3 MESES EDITABLES (color + selector sin romper grid) ----------
hoy = date.today()
for i in range(3):
    mes = (hoy.replace(day=1) + timedelta(days=32*i)).replace(day=1)
    st.write(f"### {MESES[mes.month-1].capitalize()} {mes.year}")

    # encabezado
    hdr = st.columns(7, gap="small")
    for d, col in zip(DIA_SEM, hdr):
        with col:
            st.markdown(f"**{d}**")

    # días (6 filas x 7 columnas)
    inicio = mes - timedelta(days=mes.weekday())
    dias_visibles = [inicio + timedelta(days=d) for d in range(42)]
    filas = [dias_visibles[i:i+7] for i in range(0, 42, 7)]

    # pre-cargamos cambios antes de pintar
    for dia in dias_visibles:
        es_mes = dia.month == mes.month
        if not es_mes:
            continue
        key = str(dia)
        sel_key = f"sel_mes_{mes.month}_{dia.day}"
        if st.session_state.get(sel_key):
            cal.setdefault(key, {})["turno"] = CODIGOS[st.session_state[sel_key]]
            guardar_json(cal)
            st.session_state[sel_key] = None  # reset

    # pintamos el grid
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
                borde = "2px solid #ff4d4d" if es_festivo else "none"

                # botón con color/inicial
                if es_mes:
                    label = f"{texto} {inicial}".strip()
                    if st.button(label, key=f"btn_{mes.month}_{dia.day}",
                                 help=f"Cambiar turno {dia.day}/{mes.month}",
                                 use_container_width=True):
                        # al pulsar, el selector aparecerá debajo
                        st.session_state[f"editando_{mes.month}_{dia.day}"] = True

                else:
                    st.markdown(
                        f"<div style='background:#eeeeee;padding:6px;border-radius:6px;min-height:48px;'></div>",
                        unsafe_allow_html=True
                    )

    # selectores **debajo del grid completo**, mismo orden
    st.write("")  # separador
    sel_cols = st.columns(7, gap="small")
    for semana in filas:
        for dia, col in zip(semana, sel_cols):
            with col:
                es_mes = dia.month == mes.month
                if not es_mes:
                    st.empty()
                    continue
                key = str(dia)
                turno_largo = NOMBRES.get(cal.get(key, {}).get("turno", ""), "Otro")
                edit_key = f"editando_{mes.month}_{dia.day}"
                if st.session_state.get(edit_key):
                    sel_key = f"sel_mes_{mes.month}_{dia.day}"
                    nuevo = st.selectbox("⇄", [""] + list(CODIGOS.keys()),
                                         key=sel_key,
                                         format_func=lambda x: x if x else "-",
                                         label_visibility="collapsed")
                    if nuevo:
                        cal.setdefault(key, {})["turno"] = CODIGOS[nuevo]
                        guardar_json(cal)
                        st.session_state[edit_key] = False
                        st.rerun()