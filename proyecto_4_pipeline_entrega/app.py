import os
import sys
import sqlite3
from collections import Counter

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

st.set_page_config(
    page_title="Tracker Financiero y de Sentimiento",
    page_icon="📈",
    layout="wide"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "market_data.db")

# Reutilizamos limpiar_texto() de nlp_analysis.py en vez de duplicar la lógica de NLTK aquí
sys.path.append(os.path.join(BASE_DIR, "src"))
from nlp_analysis import limpiar_texto


# --- Utilidades de datos (con caché) ---

def _version_bd():
    """mtime del archivo .db: cambia solo cuando fetch_data.py/nlp_analysis.py lo actualizan."""
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
    except sqlite3.OperationalError:
        query = "SELECT fecha, ticker, titular FROM noticias WHERE ticker = ? ORDER BY fecha ASC"
        df = pd.read_sql_query(query, conexion, params=(ticker_buscado,))
    conexion.close()
    if not df.empty:
        df["fecha"] = pd.to_datetime(df["fecha"], utc=True).dt.tz_localize(None)
    return df


# --- Validación inicial ---
if not os.path.exists(DB_PATH):
    st.error("❌ No se encontró 'data/market_data.db'. Ejecuta primero 'python src/fetch_data.py'.")
    st.stop()

version_bd = _version_bd()
tickers_disponibles = obtener_tickers_disponibles(version_bd)

if not tickers_disponibles:
    st.error("❌ La base de datos no tiene precios registrados todavía.")
    st.stop()

# --- Sidebar ---
st.sidebar.title("⚙️ Filtros de análisis")
ticker_seleccionado = st.sidebar.selectbox("Activo financiero:", tickers_disponibles)

modelo_nlp = st.sidebar.radio("Modelo NLP de sentimiento:", options=["VADER", "TextBlob"], index=0)
col_score, col_cat = (
    ("sentimiento_vader", "categoria_vader") if modelo_nlp == "VADER"
    else ("sentimiento_textblob", "categoria_textblob")
)

fecha_inicio_defecto = (datetime.now() - timedelta(days=90)).date()
fecha_fin_defecto = datetime.now().date()
fechas_seleccionadas = st.sidebar.date_input(
    "Rango de fechas:", value=(fecha_inicio_defecto, fecha_fin_defecto)
)

if isinstance(fechas_seleccionadas, tuple) and len(fechas_seleccionadas) == 2:
    fecha_inicio, fecha_fin = fechas_seleccionadas
else:
    fecha_inicio, fecha_fin = fecha_inicio_defecto, fecha_fin_defecto  # mismo tipo (date) en ambas ramas

if fecha_inicio > fecha_fin:
    st.sidebar.error("La fecha de inicio no puede ser posterior a la fecha final.")
    st.stop()

# --- Carga y filtrado ---
df_precios_bruto = cargar_precios(ticker_seleccionado, version_bd)
df_noticias_bruto = cargar_noticias(ticker_seleccionado, version_bd)

df_precios = (
    df_precios_bruto[(df_precios_bruto["fecha"].dt.date >= fecha_inicio) &
                      (df_precios_bruto["fecha"].dt.date <= fecha_fin)]
    if not df_precios_bruto.empty else df_precios_bruto
)
df_noticias = (
    df_noticias_bruto[(df_noticias_bruto["fecha"].dt.date >= fecha_inicio) &
                       (df_noticias_bruto["fecha"].dt.date <= fecha_fin)]
    if not df_noticias_bruto.empty else df_noticias_bruto
)

nlp_completado = not df_noticias.empty and col_score in df_noticias.columns
if not df_noticias.empty and not nlp_completado:
    st.warning("⚠️ Aún no se ha calculado el sentimiento. Ejecuta 'python src/nlp_analysis.py'.")

# --- Encabezado y KPIs (los 3 que pide el proyecto) ---
st.title(f"📈 Tracker financiero y de sentimiento: {ticker_seleccionado}")
st.write(f"Modelo **{modelo_nlp}** · del **{fecha_inicio}** al **{fecha_fin}**")

col1, col2, col3 = st.columns(3)

if not df_precios.empty:
    ultimo_precio = df_precios["cierre"].iloc[-1]
    precio_anterior = df_precios["cierre"].iloc[-2] if len(df_precios) > 1 else ultimo_precio
    variacion = ((ultimo_precio - precio_anterior) / precio_anterior) * 100
    col1.metric("Último precio", f"${ultimo_precio:,.2f}", f"{variacion:+.2f}%")
else:
    col1.metric("Último precio", "Sin datos")

if nlp_completado:
    col2.metric(f"Sentimiento promedio ({modelo_nlp})", f"{df_noticias[col_score].mean():+.3f}")
    col3.metric("Noticias analizadas", f"{len(df_noticias)}")
else:
    col2.metric("Sentimiento promedio", "N/A")
    col3.metric("Noticias encontradas", f"{len(df_noticias)}")

st.markdown("---")

# --- 1. Velas + volumen ---
if not df_precios.empty:
    fig_velas = make_subplots(
        rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.8, 0.2]
    )
    fig_velas.add_trace(go.Candlestick(
        x=df_precios["fecha"], open=df_precios["apertura"], high=df_precios["maximo"],
        low=df_precios["minimo"], close=df_precios["cierre"], name="Precio ($)"
    ), row=1, col=1)
    fig_velas.add_trace(go.Bar(
        x=df_precios["fecha"], y=df_precios["volumen"], name="Volumen", marker_color="royalblue"
    ), row=2, col=1)
    fig_velas.update_layout(
        title="1. Precio histórico y volumen operado",
        xaxis_rangeslider_visible=False, template="plotly_white", height=450
    )
    st.plotly_chart(fig_velas, width="stretch")
else:
    st.warning("No hay precios registrados para el rango seleccionado.")

col_g1, col_g2 = st.columns(2)

# --- 2. Distribución de sentimiento ---
with col_g1:
    if nlp_completado:
        conteo = df_noticias[col_cat].value_counts().reset_index()
        conteo.columns = ["Categoría", "Cantidad"]
        colores = {"Positiva": "#2ecc71", "Neutral": "#95a5a6", "Negativa": "#e74c3c"}
        fig_barras = px.bar(
            conteo, x="Categoría", y="Cantidad", color="Categoría",
            color_discrete_map=colores, title=f"2. Distribución de sentimiento ({modelo_nlp})"
        )
        fig_barras.update_layout(template="plotly_white")
        st.plotly_chart(fig_barras, width="stretch")
    else:
        st.info("Ejecuta nlp_analysis.py para ver las categorías de sentimiento.")

# --- 3. Precio vs. sentimiento diario ---
with col_g2:
    if not df_precios.empty and nlp_completado:
        df_sent_diario = (
            df_noticias.groupby(df_noticias["fecha"].dt.date)[col_score].mean().reset_index()
        )
        df_sent_diario["fecha"] = pd.to_datetime(df_sent_diario["fecha"])
        df_comp = pd.merge(df_precios, df_sent_diario, on="fecha", how="left")

        fig_comp = make_subplots(specs=[[{"secondary_y": True}]])
        fig_comp.add_trace(go.Scatter(
            x=df_comp["fecha"], y=df_comp["cierre"], name="Precio cierre ($)", line=dict(color="blue")
        ), secondary_y=False)
        fig_comp.add_trace(go.Scatter(
            x=df_comp["fecha"], y=df_comp[col_score], name=f"Sentimiento {modelo_nlp}",
            line=dict(color="orange", dash="dash"), connectgaps=True
        ), secondary_y=True)
        fig_comp.update_layout(title="3. Precio de cierre vs. índice de sentimiento", template="plotly_white")
        st.plotly_chart(fig_comp, width="stretch")
    else:
        st.info("No hay suficientes datos combinados para la comparativa.")

st.markdown("---")

# --- 4. Tendencia semanal de sentimiento (pregunta de negocio dedicada) ---
if nlp_completado:
    df_semanal = (
        df_noticias.sort_values("fecha").set_index("fecha")
        .resample("W")[col_score].mean().reset_index()
    )
    fig_semanal = px.line(
        df_semanal, x="fecha", y=col_score, markers=True,
        title=f"4. Sentimiento promedio semanal ({modelo_nlp})"
    )
    fig_semanal.update_layout(template="plotly_white", yaxis_title="Sentimiento promedio")
    st.plotly_chart(fig_semanal, width="stretch")

# --- 5. Palabras clave más frecuentes en noticias negativas ---
if nlp_completado:
    titulares_negativos = df_noticias.loc[df_noticias[col_cat] == "Negativa", "titular"]
    if not titulares_negativos.empty:
        conteo_palabras = Counter()
        for titular in titulares_negativos:
            conteo_palabras.update(limpiar_texto(titular))

        top_palabras = pd.DataFrame(conteo_palabras.most_common(15), columns=["Palabra", "Frecuencia"])
        fig_palabras = px.bar(
            top_palabras.sort_values("Frecuencia"), x="Frecuencia", y="Palabra", orientation="h",
            title=f"5. Palabras clave más frecuentes en noticias negativas ({modelo_nlp})"
        )
        fig_palabras.update_layout(template="plotly_white")
        st.plotly_chart(fig_palabras, width="stretch")
    else:
        st.info("No hay noticias negativas en el rango seleccionado.")

st.markdown("---")
st.subheader("📰 Titulares de noticias")
if not df_noticias.empty:
    cols_mostrar = ["fecha", "titular", col_cat, col_score] if nlp_completado else ["fecha", "titular"]
    st.dataframe(df_noticias[cols_mostrar], width="stretch", hide_index=True)
else:
    st.info("No hay noticias registradas para mostrar.")