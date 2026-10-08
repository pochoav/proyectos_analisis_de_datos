import html
import os
import sqlite3
import sys
from collections import Counter
from datetime import timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="Tracker financiero y de sentimiento",
    page_icon="📈",
    layout="wide",
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "market_data.db")

# Reutilizamos la lógica de nlp_analysis.py (limpieza de texto y umbrales de categoría)
sys.path.append(os.path.join(BASE_DIR, "src"))
from nlp_analysis import UMBRAL_NEGATIVO, UMBRAL_POSITIVO, limpiar_texto

DIAS_POR_DEFECTO = 30       # ventana inicial del selector de fechas
RANGO_SENTIMIENTO = (-1, 1)  # escala fija: ningún movimiento pequeño parece grande


# ---------------------------------------------------------------------------
# Identidad visual
# Frío = mercado (precios). Cálido = prensa (noticias y sentimiento).
# ---------------------------------------------------------------------------
PALETA = {
    "tinta": "#0F1C24",    # fondo
    "capa": "#172832",     # barra lateral y superficies elevadas
    "linea": "#2C404B",    # filetes y rejillas
    "niebla": "#DDE6E9",   # texto y línea de precio
    "apagado": "#8FA3AD",  # texto secundario y categoría neutral
    "sube": "#5FBF9A",     # alza / sentimiento positivo
    "baja": "#E5766E",     # baja / sentimiento negativo
    "papel": "#D9B97B",    # todo lo que sea noticias y sentimiento
}
FUENTE_CSS = '"Archivo", "Helvetica Neue", Arial, sans-serif'
FUENTE_PLOTLY = "Archivo, Helvetica Neue, Arial, sans-serif"

CSS_IMPORT = '@import url("https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,100..900&display=swap");'
CSS_VARIABLES = ":root{" + "".join(f"--{k}:{v};" for k, v in PALETA.items()) + "}"
CSS_BASE = f"""
html, body, .stApp, .stMarkdown, [data-testid="stSidebar"], button, input, textarea {{
  font-family: {FUENTE_CSS};
}}
.stApp {{ background: var(--tinta); }}
.stApp, .stApp p, .stApp li {{ color: var(--niebla); }}
[data-testid="stHeader"] {{ background: transparent; }}
#MainMenu, footer {{ visibility: hidden; }}
.block-container {{ max-width: 1180px; padding-top: 2.2rem; padding-bottom: 4rem; }}
[data-testid="stSidebar"] {{ background: var(--capa); border-right: 1px solid var(--linea); color: var(--niebla); }}
[data-testid="stAppDeployButton"] {{ display: none; }}
[data-testid="stSidebar"] label p {{ color: var(--apagado); font-size: .88rem; font-weight: 500; }}
.tk-lado {{ font-size: 1.5rem; font-weight: 700; font-stretch: 75%; margin: 0 0 .4rem; color: var(--niebla); }}

.tk-ticker {{ font-size: clamp(3.6rem, 9vw, 6.2rem); font-weight: 800; font-stretch: 62%;
  line-height: .9; letter-spacing: -.01em; margin: 0; }}
.tk-sub {{ color: var(--apagado); font-size: 1rem; margin-top: .7rem; max-width: 62ch; }}

.tk-banda {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
  border-top: 1px solid var(--linea); border-bottom: 1px solid var(--linea); margin: 1.7rem 0 .5rem; }}
.tk-kpi {{ padding: 1.1rem 1.4rem 1.2rem 0; }}
.tk-kpi + .tk-kpi {{ border-left: 1px solid var(--linea); padding-left: 1.4rem; }}
.tk-etiqueta {{ color: var(--apagado); font-size: .88rem; font-weight: 500; margin-bottom: .35rem; }}
.tk-valor {{ font-size: 2.8rem; font-weight: 700; font-stretch: 70%; line-height: 1;
  font-variant-numeric: tabular-nums lining-nums; }}
.tk-nota {{ color: var(--apagado); font-size: .85rem; margin-top: .6rem; line-height: 1.4; }}
.tk-sube {{ color: var(--sube); font-weight: 600; }}
.tk-baja {{ color: var(--baja); font-weight: 600; }}

.tk-escala {{ position: relative; height: 6px; margin: 1rem 0 .4rem; background: var(--linea); border-radius: 3px; }}
.tk-escala-neutra {{ position: absolute; top: -3px; bottom: -3px; background: rgba(143,163,173,.4); }}
.tk-escala-marca {{ position: absolute; top: -6px; width: 3px; height: 18px; margin-left: -1.5px;
  background: var(--papel); border-radius: 1px; }}
.tk-escala-ejes {{ display: flex; justify-content: space-between; color: var(--apagado); font-size: .75rem; }}

.tk-seccion {{ margin: 2.8rem 0 .6rem; }}
.tk-seccion h2.tk-titulo {{ font-size: 1.6rem; font-weight: 700; font-stretch: 76%; line-height: 1.15;
  margin: 0 0 .3rem; padding: 0; color: var(--niebla); }}
.tk-seccion p {{ color: var(--apagado); font-size: .95rem; margin: 0; max-width: 70ch; line-height: 1.45; }}
.tk-doble p {{ min-height: 2.9em; }}

.tk-feed {{ max-height: 430px; overflow-y: auto; border-top: 1px solid var(--linea); }}
.tk-item {{ display: grid; grid-template-columns: 8px 1fr auto; gap: .85rem; align-items: start;
  padding: .7rem .3rem; border-bottom: 1px solid var(--linea); }}
.tk-pip {{ width: 8px; height: 8px; border-radius: 50%; margin-top: .5rem; }}
.tk-item-txt {{ font-size: .93rem; line-height: 1.4; }}
.tk-item-meta {{ text-align: right; font-size: .78rem; color: var(--apagado); line-height: 1.35;
  font-variant-numeric: tabular-nums; white-space: nowrap; }}
.tk-aviso {{ border-left: 2px solid var(--papel); padding: .5rem 0 .5rem 1rem; color: var(--apagado);
  font-size: .95rem; margin: .8rem 0; }}

@media (max-width: 720px) {{
  .tk-kpi + .tk-kpi {{ border-left: 0; border-top: 1px solid var(--linea); padding-left: 0; }}
  .tk-kpi {{ padding-right: 0; }}
}}
"""
st.markdown(f"<style>{CSS_IMPORT}{CSS_VARIABLES}{CSS_BASE}</style>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def rgba(hex_color, alpha):
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


def seccion(titulo, descripcion, en_columna=False):
    clase = "tk-seccion tk-doble" if en_columna else "tk-seccion"
    st.markdown(
        f'<div class="{clase}"><h2 class="tk-titulo">{titulo}</h2><p>{descripcion}</p></div>',
        unsafe_allow_html=True,
    )


def aviso(mensaje):
    st.markdown(f'<div class="tk-aviso">{html.escape(mensaje)}</div>', unsafe_allow_html=True)


def mostrar(fig):
    # theme=None: que Streamlit no pise los colores y la tipografía de nuestra plantilla
    st.plotly_chart(fig, width="stretch", theme=None)


# ---------------------------------------------------------------------------
# Lectura de market_data.db (con caché; se invalida si el archivo .db cambia)
# ---------------------------------------------------------------------------
def _version_bd():
    return os.path.getmtime(DB_PATH) if os.path.exists(DB_PATH) else 0


@st.cache_data
def obtener_tickers_disponibles(version):
    conexion = sqlite3.connect(DB_PATH)
    tickers = pd.read_sql_query(
        "SELECT DISTINCT ticker FROM precios ORDER BY ticker", conexion
    )["ticker"].tolist()
    conexion.close()
    return tickers


@st.cache_data
def rango_disponible(version):
    conexion = sqlite3.connect(DB_PATH)
    precio_min, precio_max = conexion.execute("SELECT MIN(fecha), MAX(fecha) FROM precios").fetchone()
    noticia_max = conexion.execute("SELECT MAX(fecha) FROM noticias").fetchone()[0]
    conexion.close()
    inicio = pd.to_datetime(precio_min).date()
    fin = pd.to_datetime(precio_max).date()
    if noticia_max:
        fin = max(fin, pd.to_datetime(noticia_max, utc=True).date())
    return inicio, fin


@st.cache_data
def cargar_precios(ticker_buscado, version):
    conexion = sqlite3.connect(DB_PATH)
    query = """
        SELECT fecha, ticker, apertura, maximo, minimo, cierre, volumen
        FROM precios WHERE ticker = ? ORDER BY fecha ASC
    """
    df = pd.read_sql_query(query, conexion, params=(ticker_buscado,))
    conexion.close()
    if not df.empty:
        df["fecha"] = pd.to_datetime(df["fecha"])
    return df


@st.cache_data
def cargar_noticias(ticker_buscado, version):
    conexion = sqlite3.connect(DB_PATH)
    try:
        query = """
            SELECT fecha, ticker, titular,
                   sentimiento_vader, categoria_vader,
                   sentimiento_textblob, categoria_textblob
            FROM noticias WHERE ticker = ? ORDER BY fecha ASC
        """
        df = pd.read_sql_query(query, conexion, params=(ticker_buscado,))
    except (sqlite3.OperationalError, pd.errors.DatabaseError):
        # Las columnas de sentimiento todavía no existen: falta correr nlp_analysis.py
        query = "SELECT fecha, ticker, titular FROM noticias WHERE ticker = ? ORDER BY fecha ASC"
        df = pd.read_sql_query(query, conexion, params=(ticker_buscado,))
    conexion.close()
    if not df.empty:
        # NewsAPI entrega la fecha en UTC (sufijo Z); los precios traen solo YYYY-MM-DD
        df["fecha"] = pd.to_datetime(df["fecha"], utc=True).dt.tz_localize(None)
    return df


@st.cache_data
def contar_palabras(titulares, top_n):
    conteo = Counter()
    for titular in titulares:
        conteo.update(limpiar_texto(titular))
    return conteo.most_common(top_n)


# ---------------------------------------------------------------------------
# Gráficas (plantilla común + una función por gráfica)
# ---------------------------------------------------------------------------
def estilo_base(fig, alto, hovermode="x unified"):
    fig.update_layout(
        height=alto,
        margin=dict(l=4, r=4, t=10, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FUENTE_PLOTLY, color=PALETA["niebla"], size=12),
        hovermode=hovermode,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                    bgcolor="rgba(0,0,0,0)"),
        hoverlabel=dict(bgcolor=PALETA["capa"], bordercolor=PALETA["linea"],
                        font=dict(family=FUENTE_PLOTLY, color=PALETA["niebla"])),
    )
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor=PALETA["linea"], automargin=True,
                     tickfont=dict(color=PALETA["apagado"]))
    fig.update_yaxes(gridcolor=rgba(PALETA["linea"], 0.7), zeroline=False, automargin=True,
                     tickfont=dict(color=PALETA["apagado"]),
                     title_font=dict(color=PALETA["apagado"], size=12))
    return fig


def banda_neutral(fig, yref):
    """Franja gris con la zona que el proyecto clasifica como Neutral."""
    fig.add_shape(
        type="rect", xref="paper", x0=0, x1=1, yref=yref,
        y0=UMBRAL_NEGATIVO, y1=UMBRAL_POSITIVO,
        fillcolor=rgba(PALETA["apagado"], 0.16), line_width=0, layer="below",
    )


def grafica_velas(df):
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.04,
                        row_heights=[0.78, 0.22])
    fig.add_trace(go.Candlestick(
        x=df["fecha"], open=df["apertura"], high=df["maximo"], low=df["minimo"], close=df["cierre"],
        increasing=dict(line=dict(color=PALETA["sube"], width=1.3), fillcolor="rgba(0,0,0,0)"),
        decreasing=dict(line=dict(color=PALETA["baja"], width=1.3), fillcolor=PALETA["baja"]),
        name="Precio", showlegend=False,
    ), row=1, col=1)
    colores = [rgba(PALETA["sube"] if c >= a else PALETA["baja"], 0.45)
               for a, c in zip(df["apertura"], df["cierre"])]
    fig.add_trace(go.Bar(x=df["fecha"], y=df["volumen"], marker_color=colores,
                         name="Volumen", showlegend=False), row=2, col=1)
    estilo_base(fig, 520)
    fig.update_xaxes(rangeslider_visible=False, rangebreaks=[dict(bounds=["sat", "mon"])])
    fig.update_yaxes(title_text="Precio (USD)", row=1, col=1)
    fig.update_yaxes(title_text="Volumen", row=2, col=1)
    return fig


def grafica_precio_sentimiento(df_precios, df_noticias, col_score, modelo):
    diario = df_noticias.groupby(df_noticias["fecha"].dt.date)[col_score].mean().reset_index()
    diario["fecha"] = pd.to_datetime(diario["fecha"])
    comp = pd.merge(df_precios, diario, on="fecha", how="left")  # días sin noticias quedan vacíos, no en 0

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(
        x=comp["fecha"], y=comp["cierre"], name="Precio de cierre", mode="lines",
        line=dict(color=PALETA["niebla"], width=2),
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=comp["fecha"], y=comp[col_score], name=f"Sentimiento {modelo}", mode="lines+markers",
        connectgaps=True, line=dict(color=PALETA["papel"], width=1.6),
        marker=dict(size=6, color=PALETA["papel"]),
    ), secondary_y=True)
    banda_neutral(fig, "y2")
    estilo_base(fig, 400)
    fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])
    fig.update_yaxes(title_text="Precio (USD)", secondary_y=False)
    fig.update_yaxes(title_text="Sentimiento", range=list(RANGO_SENTIMIENTO), showgrid=False,
                     tickmode="array", tickvals=[-1, -0.5, 0, 0.5, 1], secondary_y=True)
    return fig


def grafica_distribucion(df_noticias, col_cat):
    orden = ["Negativa", "Neutral", "Positiva"]
    conteo = df_noticias[col_cat].value_counts().reindex(orden, fill_value=0)
    total = max(int(conteo.sum()), 1)
    fig = go.Figure(go.Bar(
        x=orden, y=conteo.values,
        marker_color=[PALETA["baja"], PALETA["apagado"], PALETA["sube"]],
        text=[f"{v:,} ({v / total:.0%})" for v in conteo.values],
        textposition="outside", cliponaxis=False, textfont=dict(color=PALETA["niebla"]),
        hovertemplate="%{x}: %{y} titulares<extra></extra>",
    ))
    estilo_base(fig, 340, hovermode="closest")
    fig.update_layout(showlegend=False, bargap=0.45)
    fig.update_yaxes(showticklabels=False, showgrid=False)
    return fig


def grafica_semanal(df_noticias, col_score):
    semanal = (
        df_noticias.sort_values("fecha").set_index("fecha").resample("W")
        .agg(sentimiento=(col_score, "mean"), n_noticias=(col_score, "count"))
        .reset_index()
    )
    semanal = semanal[semanal["n_noticias"] > 0]
    if semanal.empty:
        return None
    tamano = 7 + 13 * semanal["n_noticias"] / semanal["n_noticias"].max()
    fig = go.Figure(go.Scatter(
        x=semanal["fecha"], y=semanal["sentimiento"], mode="lines+markers",
        line=dict(color=PALETA["papel"], width=2),
        marker=dict(size=tamano, color=PALETA["papel"]),
        customdata=semanal["n_noticias"],
        hovertemplate="Semana que termina el %{x|%d/%m/%Y}<br>Sentimiento %{y:+.3f}"
                      "<br>%{customdata} titulares<extra></extra>",
    ))
    banda_neutral(fig, "y")
    estilo_base(fig, 340, hovermode="closest")
    fig.update_layout(showlegend=False)
    fig.update_yaxes(range=list(RANGO_SENTIMIENTO), title_text="Sentimiento promedio")
    fig.update_xaxes(tickformat="%d/%m")
    return fig


def grafica_palabras(df_noticias, col_cat, top_n=12):
    negativos = df_noticias.loc[df_noticias[col_cat] == "Negativa", "titular"]
    if negativos.empty:
        return None
    top = pd.DataFrame(contar_palabras(tuple(negativos), top_n), columns=["palabra", "frecuencia"])
    fig = go.Figure(go.Bar(
        x=top["frecuencia"], y=top["palabra"], orientation="h",
        marker_color=rgba(PALETA["baja"], 0.85),
        hovertemplate="%{y}: %{x} veces<extra></extra>",
    ))
    estilo_base(fig, 430, hovermode="closest")
    fig.update_layout(showlegend=False, bargap=0.35)
    fig.update_yaxes(autorange="reversed", showgrid=False)
    return fig


# ---------------------------------------------------------------------------
# Piezas HTML: franja de indicadores y lista de titulares
# ---------------------------------------------------------------------------
def kpi(etiqueta, valor, cuerpo):
    return (f'<div class="tk-kpi"><div class="tk-etiqueta">{etiqueta}</div>'
            f'<div class="tk-valor">{valor}</div>{cuerpo}</div>')


def kpi_precio(df_precios):
    if df_precios.empty:
        return kpi("Último cierre", "Sin datos",
                   '<div class="tk-nota">No hay precios en este rango. Amplía las fechas.</div>')
    ultimo = df_precios["cierre"].iloc[-1]
    anterior = df_precios["cierre"].iloc[-2] if len(df_precios) > 1 else ultimo
    variacion = (ultimo - anterior) / anterior * 100
    clase = "tk-sube" if variacion > 0 else "tk-baja" if variacion < 0 else ""
    flecha = "▲" if variacion > 0 else "▼" if variacion < 0 else "–"
    fecha = df_precios["fecha"].iloc[-1].strftime("%d/%m/%Y")
    nota = (f'<div class="tk-nota"><span class="{clase}">{flecha} {abs(variacion):.2f}%</span> '
            f'frente al cierre anterior. Último dato: {fecha}.</div>')
    return kpi("Último cierre", f"${ultimo:,.2f}", nota)


def kpi_sentimiento(scores, modelo):
    scores = scores.dropna() if scores is not None else None
    if scores is None or scores.empty:
        return kpi("Sentimiento promedio", "N/D",
                   '<div class="tk-nota">Ejecuta src/nlp_analysis.py para calcularlo.</div>')
    media = scores.mean()
    posicion = min(max((media + 1) / 2 * 100, 0), 100)
    zona_izq = (UMBRAL_NEGATIVO + 1) / 2 * 100
    zona_ancho = (UMBRAL_POSITIVO - UMBRAL_NEGATIVO) / 2 * 100
    zona = "positiva" if media >= UMBRAL_POSITIVO else "negativa" if media <= UMBRAL_NEGATIVO else "neutral"
    escala = (
        f'<div class="tk-escala"><div class="tk-escala-neutra" style="left:{zona_izq:.1f}%;width:{zona_ancho:.1f}%">'
        f'</div><div class="tk-escala-marca" style="left:{posicion:.1f}%"></div></div>'
        '<div class="tk-escala-ejes"><span>−1</span><span>0</span><span>+1</span></div>'
    )
    nota = f'<div class="tk-nota">Promedio {modelo} en zona {zona}. La franja gris marca el rango neutral.</div>'
    return kpi("Sentimiento promedio", f"{media:+.3f}", escala + nota)


def kpi_noticias(df_noticias):
    n = len(df_noticias)
    if n == 0:
        return kpi("Titulares en el rango", "0",
                   '<div class="tk-nota">No hay titulares en estas fechas.</div>')
    dias = df_noticias["fecha"].dt.date.nunique()
    return kpi("Titulares en el rango", f"{n:,}",
               f'<div class="tk-nota">Repartidos en {dias} días con noticias.</div>')


def lista_titulares(df, col_cat, col_score, hay_nlp, limite=40):
    recientes = df.sort_values("fecha", ascending=False).head(limite)
    colores = {"Positiva": PALETA["sube"], "Negativa": PALETA["baja"], "Neutral": PALETA["apagado"]}
    filas = []
    for _, fila in recientes.iterrows():
        texto = html.escape(str(fila["titular"]))  # los titulares vienen de internet: nunca sin escapar
        fecha = f'{fila["fecha"]:%d/%m}'
        if hay_nlp and pd.notna(fila[col_score]):
            categoria = str(fila[col_cat])
            color = colores.get(categoria, PALETA["apagado"])
            meta = f'{html.escape(categoria)} {fila[col_score]:+.2f}<br>{fecha}'
        else:
            color, meta = PALETA["apagado"], fecha
        filas.append(
            f'<div class="tk-item"><span class="tk-pip" style="background:{color}"></span>'
            f'<div class="tk-item-txt">{texto}</div><div class="tk-item-meta">{meta}</div></div>'
        )
    return f'<div class="tk-feed">{"".join(filas)}</div>', len(recientes)


# ---------------------------------------------------------------------------
# Validación inicial
# ---------------------------------------------------------------------------
if not os.path.exists(DB_PATH):
    st.error("No se encontró data/market_data.db. Ejecuta primero: python src/fetch_data.py")
    st.stop()

version_bd = _version_bd()
tickers_disponibles = obtener_tickers_disponibles(version_bd)
if not tickers_disponibles:
    st.error("La base de datos todavía no tiene precios. Ejecuta primero: python src/fetch_data.py")
    st.stop()

# ---------------------------------------------------------------------------
# Barra lateral
# ---------------------------------------------------------------------------
st.sidebar.markdown('<div class="tk-lado">Filtros</div>', unsafe_allow_html=True)
ticker = st.sidebar.selectbox("Activo", tickers_disponibles)
modelo_nlp = st.sidebar.radio(
    "Modelo de sentimiento", ["VADER", "TextBlob"],
    help="Cada modelo mide el tono de los titulares con su propio léxico, por eso sus resultados difieren.",
)
col_score, col_cat = (
    ("sentimiento_vader", "categoria_vader") if modelo_nlp == "VADER"
    else ("sentimiento_textblob", "categoria_textblob")
)

fecha_min_datos, fecha_max_datos = rango_disponible(version_bd)
inicio_defecto = max(fecha_min_datos, fecha_max_datos - timedelta(days=DIAS_POR_DEFECTO))
fechas = st.sidebar.date_input(
    "Rango de fechas", value=(inicio_defecto, fecha_max_datos),
    min_value=fecha_min_datos, max_value=fecha_max_datos,
)
if isinstance(fechas, (tuple, list)) and len(fechas) == 2:
    fecha_inicio, fecha_fin = fechas
else:  # el usuario todavía está eligiendo la segunda fecha
    fecha_inicio, fecha_fin = inicio_defecto, fecha_max_datos

# ---------------------------------------------------------------------------
# Datos del activo y rango elegidos
# ---------------------------------------------------------------------------
df_precios_bruto = cargar_precios(ticker, version_bd)
df_noticias_bruto = cargar_noticias(ticker, version_bd)

df_precios = df_precios_bruto[
    (df_precios_bruto["fecha"].dt.date >= fecha_inicio) & (df_precios_bruto["fecha"].dt.date <= fecha_fin)
] if not df_precios_bruto.empty else df_precios_bruto
df_noticias = df_noticias_bruto[
    (df_noticias_bruto["fecha"].dt.date >= fecha_inicio) & (df_noticias_bruto["fecha"].dt.date <= fecha_fin)
] if not df_noticias_bruto.empty else df_noticias_bruto

nlp_completado = not df_noticias.empty and col_score in df_noticias.columns
if not df_noticias.empty and not nlp_completado:
    aviso("Aún no se calculó el sentimiento. Ejecuta en la terminal: python src/nlp_analysis.py")

# ---------------------------------------------------------------------------
# Encabezado e indicadores
# ---------------------------------------------------------------------------
st.markdown(
    f'<div class="tk-ticker">{html.escape(ticker)}</div>'
    f'<div class="tk-sub">Precio y tono de las noticias del {fecha_inicio:%d/%m/%Y} al {fecha_fin:%d/%m/%Y}, '
    f'medido con {modelo_nlp}.</div>',
    unsafe_allow_html=True,
)
scores = df_noticias[col_score] if nlp_completado else None
st.markdown(
    '<div class="tk-banda">'
    + kpi_precio(df_precios) + kpi_sentimiento(scores, modelo_nlp) + kpi_noticias(df_noticias)
    + "</div>",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Secciones: cada una responde una pregunta
# ---------------------------------------------------------------------------
seccion("¿Cómo se movió el precio?",
        "Cada vela resume un día. Vacía: cerró al alza. Rellena: cerró a la baja. Abajo, el volumen operado.")
if df_precios.empty:
    aviso("No hay precios registrados en este rango. Amplía las fechas en la barra lateral.")
else:
    mostrar(grafica_velas(df_precios))

seccion("¿Se mueve el precio con el tono de las noticias?",
        "Precio de cierre contra el sentimiento promedio de cada día. "
        "La escala del sentimiento va siempre de −1 a +1; la franja gris es la zona neutral.")
if df_precios.empty or not nlp_completado:
    aviso("Hace falta tener precios y sentimiento calculado en este rango para compararlos.")
else:
    mostrar(grafica_precio_sentimiento(df_precios, df_noticias, col_score, modelo_nlp))

izq, der = st.columns(2, gap="large")
with izq:
    seccion("¿Qué tono dominan las noticias?", "Cantidad de titulares por categoría, con su porcentaje.", en_columna=True)
    if nlp_completado:
        mostrar(grafica_distribucion(df_noticias, col_cat))
    else:
        aviso("Ejecuta src/nlp_analysis.py para ver las categorías.")
with der:
    seccion("¿Cómo varía el tono por semana?",
            "El tamaño del punto indica cuántos titulares respaldan cada semana.", en_columna=True)
    fig_semanal = grafica_semanal(df_noticias, col_score) if nlp_completado else None
    if fig_semanal is not None:
        mostrar(fig_semanal)
    else:
        aviso("No hay titulares con sentimiento en este rango.")

izq, der = st.columns(2, gap="large")
with izq:
    seccion("¿Qué dicen las noticias negativas?",
            "Las palabras más repetidas en los titulares negativos, sin palabras vacías.", en_columna=True)
    fig_palabras = grafica_palabras(df_noticias, col_cat) if nlp_completado else None
    if fig_palabras is not None:
        mostrar(fig_palabras)
    else:
        aviso("No hay titulares negativos en este rango.")
with der:
    seccion("Titulares recientes", "El color del punto indica la categoría según el modelo elegido.",
            en_columna=True)
    if df_noticias.empty:
        aviso("No hay titulares en este rango.")
    else:
        bloque, mostrados = lista_titulares(df_noticias, col_cat, col_score, nlp_completado)
        st.markdown(bloque, unsafe_allow_html=True)
        st.markdown(
            f'<div class="tk-nota">Mostrando los {mostrados} más recientes de {len(df_noticias)}.</div>',
            unsafe_allow_html=True,
        )