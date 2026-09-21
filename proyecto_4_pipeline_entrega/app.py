import os
import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

#Configuración de página y rutas
st.set_page_config(
    page_title="Tracker Financiero y de Sentimiento",
    page_icon="📈",
    layout="wide"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "market_data.db")

#Lectura de market_data.db
def cargar_precios(ticker_buscado):
    if not os.path.exists(DB_PATH):
        return pd.DataFrame()
        
    conexion = sqlite3.connect(DB_PATH)
    query = """
        SELECT fecha, ticker, apertura, maximo, minimo, cierre, volumen 
        FROM precios 
        WHERE ticker = ?
        ORDER BY fecha ASC
    """
    df_precios = pd.read_sql_query(query, conexion, params=(ticker_buscado,))
    conexion.close()
    
    if not df_precios.empty:
        df_precios['fecha'] = pd.to_datetime(df_precios['fecha'])
        
    return df_precios


def cargar_noticias(ticker_buscado):
    if not os.path.exists(DB_PATH):
        return pd.DataFrame()

    conexion = sqlite3.connect(DB_PATH)
    
    try:
        query = """
            SELECT fecha, ticker, titular, 
                   sentimiento_vader, categoria_vader, 
                   sentimiento_textblob, categoria_textblob 
            FROM noticias 
            WHERE ticker = ?
            ORDER BY fecha DESC
        """
        df_noticias = pd.read_sql_query(query, conexion, params=(ticker_buscado,))
    except Exception:
        query = "SELECT fecha, ticker, titular FROM noticias WHERE ticker = ?"
        df_noticias = pd.read_sql_query(query, conexion, params=(ticker_buscado,))
    
    conexion.close()
    
    if not df_noticias.empty:
        df_noticias['fecha'] = pd.to_datetime(df_noticias['fecha'], utc=True).dt.tz_localize(None)
        
    return df_noticias

#Filtros barra lateral
st.sidebar.title("⚙️ Filtros de Análisis")

lista_activos = ["AAPL", "TSLA", "NVDA", "AMZN", "MSFT"]
ticker_seleccionado = st.sidebar.selectbox("Selecciona un Activo Financiero:", lista_activos)

modelo_nlp = st.sidebar.radio(
    "Modelo NLP de Sentimiento:",
    options=["VADER", "TextBlob"],
    index=0
)

if modelo_nlp == "VADER":
    col_score = "sentimiento_vader"
    col_cat = "categoria_vader"
else:
    col_score = "sentimiento_textblob"
    col_cat = "categoria_textblob"

fecha_inicio_defecto = datetime.now() - timedelta(days=90)
fechas_seleccionadas = st.sidebar.date_input(
    "Rango de Fechas:",
    value=(fecha_inicio_defecto, datetime.now())
)

if isinstance(fechas_seleccionadas, tuple) and len(fechas_seleccionadas) == 2:
    fecha_inicio, fecha_fin = fechas_seleccionadas
else:
    fecha_inicio, fecha_fin = fecha_inicio_defecto, datetime.now()

#Carga y filtrado de datos
if not os.path.exists(DB_PATH):
    st.error("❌ No se encontró la base de datos 'data/market_data.db'. Por favor ejecuta primero 'python src/fetch_data.py'.")
    st.stop()

df_precios_bruto = cargar_precios(ticker_seleccionado)
df_noticias_bruto = cargar_noticias(ticker_seleccionado)

if not df_precios_bruto.empty:
    mask_precios = (df_precios_bruto['fecha'].dt.date >= fecha_inicio) & (df_precios_bruto['fecha'].dt.date <= fecha_fin)
    df_precios = df_precios_bruto.loc[mask_precios]
else:
    df_precios = pd.DataFrame()

if not df_noticias_bruto.empty:
    mask_noticias = (df_noticias_bruto['fecha'].dt.date >= fecha_inicio) & (df_noticias_bruto['fecha'].dt.date <= fecha_fin)
    df_noticias = df_noticias_bruto.loc[mask_noticias]
else:
    df_noticias = pd.DataFrame()

nlp_completado = not df_noticias.empty and col_score in df_noticias.columns
if not nlp_completado and not df_noticias.empty:
    st.warning("⚠️ Los análisis de sentimiento aún no han sido calculados. Ejecuta 'python src/nlp_analysis.py' en tu terminal.")

#Encabezados y KPIs
st.title(f"📈 Tracker Financiero y de Sentimiento: {ticker_seleccionado}")
st.write(f"Visualizando modelo **{modelo_nlp}** del **{fecha_inicio}** al **{fecha_fin}**")

col1, col2, col3, col4 = st.columns(4)

if not df_precios.empty:
    ultimo_precio = df_precios['cierre'].iloc[-1]
    precio_anterior = df_precios['cierre'].iloc[-2] if len(df_precios) > 1 else ultimo_precio
    variacion = ((ultimo_precio - precio_anterior) / precio_anterior) * 100
    col1.metric("Último Precio", f"${ultimo_precio:,.2f}", f"{variacion:+.2f}%")
else:
    col1.metric("Último Precio", "Sin datos")

if nlp_completado:
    sentimiento_prom = df_noticias[col_score].mean()
    col2.metric(f"Sentimiento ({modelo_nlp})", f"{sentimiento_prom:+.3f}")
else:
    col2.metric("Sentimiento Promedio", "N/A")

col3.metric("Noticias Analizadas", f"{len(df_noticias)}")
col4.metric("Activo Seleccionado", ticker_seleccionado)

st.markdown("---")

#Gráficos interactivos
if not df_precios.empty:
    fig_velas = make_subplots(
        rows=2, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.05, 
        row_width=[0.2, 0.8]
    )

    fig_velas.add_trace(
        go.Candlestick(
            x=df_precios['fecha'],
            open=df_precios['apertura'],
            high=df_precios['maximo'],
            low=df_precios['minimo'],
            close=df_precios['cierre'],
            name="Precio ($)"
        ),
        row=1, col=1
    )

    fig_velas.add_trace(
        go.Bar(
            x=df_precios['fecha'],
            y=df_precios['volumen'],
            name="Volumen",
            marker_color='royalblue'
        ),
        row=2, col=1
    )

    fig_velas.update_layout(
        title="1. Precio de Cierre Histórico y Volumen Operado",
        xaxis_rangeslider_visible=False,
        template="plotly_white",
        height=450
    )
    st.plotly_chart(fig_velas, use_container_width=True)
else:
    st.warning("No hay precios registrados para el rango seleccionado.")

col_g1, col_g2 = st.columns(2)

with col_g1:
    if nlp_completado:
        conteo = df_noticias[col_cat].value_counts().reset_index()
        conteo.columns = ['Categoría', 'Cantidad']
        
        colores = {'Positiva': '#2ecc71', 'Neutral': '#95a5a6', 'Negativa': '#e74c3c'}
        
        fig_barras = px.bar(
            conteo, 
            x='Categoría', 
            y='Cantidad', 
            color='Categoría',
            color_discrete_map=colores,
            title=f"2. Distribución de Sentimiento ({modelo_nlp})"
        )
        fig_barras.update_layout(template="plotly_white")
        st.plotly_chart(fig_barras, use_container_width=True)
    else:
        st.info("Se requiere ejecutar nlp_analysis.py para ver las categorías de sentimiento.")

with col_g2:
    if not df_precios.empty and nlp_completado:
        df_sent_diario = df_noticias.groupby(df_noticias['fecha'].dt.date)[col_score].mean().reset_index()
        df_sent_diario['fecha'] = pd.to_datetime(df_sent_diario['fecha'])

        df_comp = pd.merge(df_precios, df_sent_diario, on='fecha', how='left').fillna({col_score: 0})

        fig_comp = make_subplots(specs=[[{"secondary_y": True}]])
        
        fig_comp.add_trace(
            go.Scatter(x=df_comp['fecha'], y=df_comp['cierre'], name="Precio Cierre ($)", line=dict(color="blue")),
            secondary_y=False
        )
        
        fig_comp.add_trace(
            go.Scatter(x=df_comp['fecha'], y=df_comp[col_score], name=f"Sentimiento {modelo_nlp}", line=dict(color="orange", dash='dash')),
            secondary_y=True
        )

        fig_comp.update_layout(title="3. Comparación: Precio Cierre vs. Índice de Sentimiento", template="plotly_white")
        st.plotly_chart(fig_comp, use_container_width=True)
    else:
        st.info("No hay suficientes datos combinados para generar la comparativa.")

#Tabla de noticias
st.markdown("---")
st.subheader("📰 Titulares de Noticias Recientes")

if not df_noticias.empty:
    if nlp_completado:
        cols_mostrar = ['fecha', 'titular', col_cat, col_score]
    else:
        cols_mostrar = ['fecha', 'titular']
        
    st.dataframe(
        df_noticias[cols_mostrar],
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("No hay noticias registradas para mostrar.")