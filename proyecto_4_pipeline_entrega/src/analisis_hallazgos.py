#Este es un módulo extra que realiza un análisis de los resultados 
#presentes en market_data.db y en app.py para utilizar en reporte_tecnico.pdf

import os
import sqlite3
import pandas as pd
from textblob import TextBlob
from collections import Counter
from nlp_analysis import limpiar_texto

BASE_DIR=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH=os.path.join(BASE_DIR, "data", "market_data.db")

def cargar_noticias_analizadas():
    conexion = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        """
        SELECT ticker, fecha, titular, categoria_vader, categoria_textblob,
               sentimiento_vader, sentimiento_textblob
        FROM noticias
        WHERE categoria_vader IS NOT NULL AND categoria_textblob IS NOT NULL
        """,
        conexion
    )
    conexion.close()
    df["fecha"] = pd.to_datetime(df["fecha"], utc=True).dt.tz_localize(None)
    return df

def porcentaje_coincidencia(df):    #Calcular coincidencia entre modelos
    coincide=df["categoria_vader"]==df["categoria_textblob"]
    return coincide.mean() * 100

def matriz_confusion(df):   #Presentar matriz de confusión (visualizar coincidencia)
    return pd.crosstab(df["categoria_vader"], df["categoria_textblob"],
                       rownames=["VADER"], colnames=["TextBlob"])

def palabras_clave_frecuentes(df, columna_categoria, top_n=15):
    """Top de palabras en titulares 'Negativa', según el modelo indicado en columna_categoria."""
    titulares_negativos = df.loc[df[columna_categoria] == "Negativa", "titular"]

    conteo = Counter()
    for titular in titulares_negativos:
        conteo.update(limpiar_texto(titular))

    return pd.DataFrame(conteo.most_common(top_n), columns=["palabra", "frecuencia"])

def correlacion_pearson(df):    #Calcula Índice de Correlación de Pearson para medir similitud
    return df["sentimiento_vader"].corr(df["sentimiento_textblob"])

def tendencia_semanal_sentimiento(df, columna_score):
    #Promedio de sentimiento por semana, y la semana más baja/más alta.
    semanal = (
        df.set_index("fecha")
        .resample("W")
        .agg(sentimiento_promedio=(columna_score, "mean"), n_noticias=(columna_score, "count"))
        .reset_index()
        .dropna()
    )

    fila_min = semanal.loc[semanal["sentimiento_promedio"].idxmin()]
    fila_max = semanal.loc[semanal["sentimiento_promedio"].idxmax()]

    resumen = {
        "semana_mas_baja": fila_min["fecha"].date(),
        "valor_mas_bajo": fila_min["sentimiento_promedio"],
        "semana_mas_alta": fila_max["fecha"].date(),
        "valor_mas_alto": fila_max["sentimiento_promedio"],
        "rango": fila_max["sentimiento_promedio"] - fila_min["sentimiento_promedio"],
        "n_min": fila_min["n_noticias"],
        "n_max": fila_max["n_noticias"],

    }
    return semanal, resumen

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

def construir_panel_diario():
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

def cargar_noticias_con_titular():
    #Conservar el titular para obtener subjectivity
    conexion = sqlite3.connect(DB_PATH)
    df=pd.read_sql_query(
        """
        SELECT ticker, titular, categoria_vader, categoria_textblob,
               sentimiento_vader, sentimiento_textblob
        FROM noticias
        WHERE categoria_vader IS NOT NULL AND categoria_textblob IS NOT NULL
        """,
        conexion
    )
    conexion.close()
    return df

def calcular_subjectivity(df):
    #Usar TextBlob para calcular subjectivity y agrega la columna extra
    df=df.copy()
    df["subjectivity"]=df["titular"].apply(lambda t: TextBlob(t).sentiment.subjectivity)
    return df

def resumen_subjectivity(df):
    #Promedio, mediana y % de titulares sin léxico en TextBlob
    return {
        "promedio": df["subjectivity"].mean(),
        "mediana": df["subjectivity"].median(),
        "pct_subjectivity_cero": (df["subjectivity"]==0).mean() * 100
    }

def subjectivity_por_categoria(df, columna_categoria):
    #Subjectivity promedio, mediana y conteo
    return df.groupby(columna_categoria)["subjectivity"].agg(["mean", "median", "count"])

def prueba_neutralidad_textblob(df):
    #Prueba la suposición: TextBlob marca mucha neutralidad por no encontrar el vocabulario en su léxico, no por nautralidad real
    neutrales_tb = df[df["categoria_textblob"]=="Neutral"]
    pct_cero_en_neutrales = (neutrales_tb["subjectivity"]==0).mean() * 100

    #Verificar si VADER detecta sentimiento diferente a TextBlob
    desacuerdo = df[(df["categoria_textblob"]=="Neutral") & (df["categoria_vader"] != "Neutral")]
    pct_cero_en_desacuerdo = (desacuerdo["subjectivity"]==0).mean() * 100

    return {
        "neutrales_textblob": len(neutrales_tb),
        "pct_subjectivity_cero_en_neutrales": pct_cero_en_neutrales,
        "casos_desacuerdo_vader_no_neutral": len(desacuerdo),
        "pct_subjectivity_cero_en_desacuerdo": pct_cero_en_desacuerdo,
    }


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

   print("\nAnálisis de subjectivity (TextBlob)")
   df_subj = calcular_subjectivity(cargar_noticias_con_titular())

   resumen = resumen_subjectivity(df_subj)
   print(f"Promedio: {resumen['promedio']:.3f} | Mediana_ {resumen['mediana']:.3f} | "
         f"% con subjectivity = 0: {resumen['pct_subjectivity_cero']:.1f}%")

   print("\nSubjectivity por categoria de TextBlob:")
   print(subjectivity_por_categoria(df_subj, "categoria_textblob").round(3))

   print("\nSubjectivity por categoria de VADER:")
   print(subjectivity_por_categoria(df_subj, "categoria_vader").round(3))

   print("Prueba de Hipótesis de neutralidad de TextBlob:")
   prueba = prueba_neutralidad_textblob(df_subj)
   for clave, valor in prueba.items():
       print(f" {clave}: {valor}")

   print("\nPalabras clave en noticias negativas (VADER):")
   print(palabras_clave_frecuentes(df, "categoria_vader").to_string(index=False))

   print("\nPalabras clave en noticias negativas (TextBlob):")
   print(palabras_clave_frecuentes(df, "categoria_textblob").to_string(index=False))

   _, resumen_vader = tendencia_semanal_sentimiento(df, "sentimiento_vader")
   print(f"\nTendencia semanal (VADER): semana más baja {resumen_vader['semana_mas_baja']} "
         f"({resumen_vader['valor_mas_bajo']:+.3f}), más alta {resumen_vader['semana_mas_alta']} "
         f"({resumen_vader['valor_mas_alto']:+.3f}), rango {resumen_vader['rango']:.3f}")

   _, resumen_textblob = tendencia_semanal_sentimiento(df, "sentimiento_textblob")
   print(f"\nTendencia semanal (TextBlob): semana más baja {resumen_textblob['semana_mas_baja']} "
         f"({resumen_textblob['valor_mas_bajo']:+.3f}), más alta {resumen_textblob['semana_mas_alta']} "
         f"({resumen_textblob['valor_mas_alto']:+.3f}), rango {resumen_textblob['rango']:.3f}")
    


    




