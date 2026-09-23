import yfinance as yf
import requests
from datetime import datetime, timedelta
import sqlite3
import os
from dotenv import load_dotenv
load_dotenv()


# Claves para empresas
empresas = {
    "AAPL": "Apple",
    "TSLA": "Tesla",
    "NVDA": "NVIDIA",
    "AMZN": "Amazon",
    "MSFT": "Microsoft"
}

fecha_inicio_precios= "2024-01-01"
fecha_fin = datetime.today().strftime("%Y-%m-%d")
fecha_inicio_noticias = (datetime.today() - timedelta(days=29)).strftime("%Y-%m-%d")


#Precios históricos (yfinance) 
precios_totales = yf.download(
    tickers=list(empresas.keys()),
    start=fecha_inicio_precios,
    end=fecha_fin,
    group_by="ticker"
)

#Titulares financieros (NewsAPI)
api_key = os.environ["NEWS_API_KEY"]
noticias_totales = []


for ticker, nombre_empresa in empresas.items():
    url = "https://newsapi.org/v2/everything"
    parametros = {
        "qInTitle": nombre_empresa,
        "from": fecha_inicio_noticias,
        "to": fecha_fin,
        "language": "en",
        "sortBy": "publishedAt",
        "apiKey": api_key
    }
    respuesta = requests.get(url, params=parametros)
    datos = respuesta.json()

    for articulo in datos["articles"]:
        noticias_totales.append({
            "ticker": ticker,
            "fecha": articulo["publishedAt"],
            "titular": articulo["title"]
        })

print(precios_totales.head())
print(noticias_totales[:3])

#---Tablas SQL---

directorio_actual = os.path.dirname(os.path.abspath(__file__))   # .../proyecto_4_pipeline_entrega/src
directorio_proyecto = os.path.dirname(directorio_actual)          # .../proyecto_4_pipeline_entrega
ruta_data = os.path.join(directorio_proyecto, "data")
os.makedirs(ruta_data, exist_ok=True)                              # crea data/ SIEMPRE dentro del proyecto 4

ruta_db = os.path.join(ruta_data, "market_data.db")
conexion = sqlite3.connect(ruta_db)
cursor=conexion.cursor()

cursor.execute("""                                       
    CREATE TABLE IF NOT EXISTS precios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT,
        fecha TEXT,
        apertura REAL,
        maximo REAL,
        minimo REAL,
        cierre REAL,
        volumen INTEGER
    )
""")                                                     

cursor.execute("""
    CREATE TABLE IF NOT EXISTS noticias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT,
        fecha TEXT,
        titular TEXT
    )
""")                                                     

# --- Insertar precios ---
for ticker in empresas.keys():
    df_ticker = precios_totales[ticker].reset_index()    
    for _, fila in df_ticker.iterrows():                 
        cursor.execute(
            "INSERT INTO precios (ticker, fecha, apertura, maximo, minimo, cierre, volumen) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                ticker,
                fila["Date"].strftime("%Y-%m-%d"),
                fila["Open"], fila["High"], fila["Low"], fila["Close"], fila["Volume"]
            )
        )                                                 

# --- Insertar noticias ---
for noticia in noticias_totales:
    cursor.execute(
        "INSERT INTO noticias (ticker, fecha, titular) VALUES (?, ?, ?)",
        (noticia["ticker"], noticia["fecha"], noticia["titular"])
    )                                                    

conexion.commit()                                        
conexion.close()                                          