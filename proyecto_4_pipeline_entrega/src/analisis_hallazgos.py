#Este es un módulo extra que realiza un análisis de los resultados 
#presentes en market_data.db y en app.py para utilizar en reporte_tecnico.pdf

import os
import sqlite3
import pandas as pd

BASE_DIR=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH=os.path.join(BASE_DIR, "data", "market_data.db")

def cargar_noticias_analizadas():
    conexion = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        """
        SELECT ticker, categoria_vader, categoria_textblob,
               sentimiento_vader, sentimiento_textblob
        FROM noticias
        WHERE categoria_vader IS NOT NULL AND categoria_textblob IS NOT NULL
        """,
        conexion
    )
    conexion.close()
    return df

def porcentaje_coincidencia(df):    #Calcular coincidencia entre modelos
    coincide=df["categoria_vader"]==df["categoria_textblob"]
    return coincide.mean() * 100

def matriz_confusion(df):   #Presentar matriz de confusión (visualizar coincidencia)
    return pd.crosstab(df["categoria_vader"], df["categoria_textblob"],
                       rownames=["VADER"], colnames=["TextBlob"])

def correlacion_pearson(df):    #Calcula Índice de Correlación de Pearson para medir similitud
    return df["sentimiento_vader"].corr(df["sentimiento_textblob"])

def cargar_precios_diarios():   #Calcula variación de precios día a día
    conexion = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT ticker, fecha, cierre, volumen FROM precios ORDER BY ticker, fecha", conexion
    )
    conexion.close()
    df["fecha"] = pd.to_datetime(df["fecha"])
    df["variacion_pct"] = df.groupby("ticker")["cierre"].pct_change() * 100
    return df

def cargar_sentimiento_diario():    #Sentimiento promedio por día y por ticker
    conexion = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        """
        SELECT ticker, fecha, sentimiento_vader, sentimiento_textblob
        FROM noticias WHERE sentimiento_vader IS NOT NULL
        """, conexion
    )
    conexion.close()
    df["fecha"] = pd.to_datetime(df["fecha"], utc=True).dt.tz_localize(None).dt.floor("D")
    return df.groupby(["ticker", "fecha"])[["sentimiento_vader", "sentimiento_textblob"]].mean().reset_index()

def correlacion_sentimiento_mercado():  #Compara días donde hay por lo menos precio y una noticia
    precios = cargar_precios_diarios()
    sentimiento = cargar_sentimiento_diario()

    combinado = pd.merge(precios, sentimiento, on=["ticker", "fecha"], how="inner")

    resultados = []
    for ticker, grupo in combinado.groupby("ticker"):   #Correlación entre precio/volumen y sentimiento diario
        resultados.append({
            "ticker": ticker,
            "dias_comparados": len(grupo),
            "corr_precio_vader": grupo["variacion_pct"].corr(grupo["sentimiento_vader"]),
            "corr_precio_textblob": grupo["variacion_pct"].corr(grupo["sentimiento_textblob"]),
            "corr_volumen_vader": grupo["volumen"].corr(grupo["sentimiento_vader"]),
            "corr_volumen_textblob": grupo["volumen"].corr(grupo["sentimiento_textblob"]),
        })

    #Correlación con TODOS los tickers agrupados en un solo cálculo
    resultados.append({
        "ticker": "TODOS (agrupado)",
        "dias_comparados": len(combinado),
        "corr_precio_vader": combinado["variacion_pct"].corr(combinado["sentimiento_vader"]),
        "corr_precio_textblob": combinado["variacion_pct"].corr(combinado["sentimiento_textblob"]),
        "corr_volumen_vader": combinado["volumen"].corr(combinado["sentimiento_vader"]),
        "corr_volumen_textblob": combinado["volumen"].corr(combinado["sentimiento_textblob"]),
    })

    return pd.DataFrame(resultados)

def contruir_panel_diario():
    #Calendario de días hábiles para el análisis de correlación entre sentimiento y precio CON REZAGO TEMPORAL
    precios = cargar_precios_diarios()
    precios = precios.drop_duplicates(subset=["ticker", "fecha"]) #Protección de filas repetidas
    precios = precios.sort_values(["ticker", "fecha"])
    precios["variacion_pct"] = precios.groupby("ticker")["cierre"].pct_change() * 100

    sentimiento = cargar_sentimiento_diario()
    return pd.merge(precios, sentimiento, on=["ticker", "fecha"], how="left")

def correlacion_con_rezago(rezagos=(0, 1, 2)):
    #Correlación entre el precio del día y el sentimiento promedio anterior
    panel = contruir_panel_diario()

    for k in rezagos:
        panel[f"vader_{k}"] = panel.groupby("ticker")["sentimiento_vader"].shift(k)
        panel[f"textblob_{k}"] = panel.groupby("ticker")["sentimiento_textblob"].shift(k)

    grupos = list(panel.groupby("ticker")) + [("TODOS (agrupado)", panel)]

    resultados = []
    for nombre, grupo in grupos:
        for k in rezagos:
            pares = grupo[f"vader_{k}"].notna() & grupo["variacion_pct"].notna()
            resultados.append({
                "ticker": nombre,
                "rezago": k,
                "pares": int(pares.sum()),
                "corr_vader": grupo["variacion_pct"].corr(grupo[f"vader_{k}"]),
                "corr_textblob": grupo["variacion_pct"].corr(grupo[f"textblob_{k}"]),
            })
    return pd.DataFrame(resultados)





if __name__ == "__main__":
   df = cargar_noticias_analizadas()
   print(f"\nNoticias comparadas : {len(df)}")
   print(f"% de coincidencia de categoría (VADER vs. TextBlob): {porcentaje_coincidencia(df):.1f}%")

   print("\nMatriz de confusión (filas = VADER, columnas = TextBlob):")
   print(matriz_confusion(df))
                                         #Correlación entre entre 'positividad' o 'negatividad'
   print(f"Correlación de Pearson entre compound(VADER) y polarity (TextBlob): {correlacion_pearson(df):.3f}")

   print(f"Correlación entre sentimiento diario y precio/volumen:")
   print(correlacion_sentimiento_mercado().to_string(index=False))

   print("\nCorrelación sentimiento (día t-k) vs. variación de precio (día t):")
   print(correlacion_con_rezago().round(3).to_string(index=False))

