import string
import nltk
import os
import sqlite3
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from textblob import TextBlob


#Preprocesamiento de datos
def _asegurar_recursos_nltk():
    #Descarga recursos de NLTK
    recursos = {
        "tokenizers/punkt_tab": "punkt_tab",
        "corpora/stopwords": "stopwords"
    }
    for ruta, nombre in recursos.items():
        try:
            nltk.data.find(ruta)
        except LookupError:
            nltk.download(nombre)


_asegurar_recursos_nltk()
STOPWORDS_EN = set(stopwords.words("english"))

def limpiar_texto(texto):
#Tokenización y limpieza de titulares
    return [
        t.lower() for t in word_tokenize(texto)
        if t not in string.punctuation
        and t.lower() not in STOPWORDS_EN
        and t.isalpha()
    ]


#Análisis de sentimiento (VADER/TextBlob)

_analizador_vader = SentimentIntensityAnalyzer()

UMBRAL_POSITIVO = 0.05
UMBRAL_NEGATIVO = -0.05

def calcular_sentimiento_vader(texto_crudo):
    return _analizador_vader.polarity_scores(texto_crudo)["compound"]

def calcular_sentimiento_textblob(texto_crudo):
    return TextBlob(texto_crudo).sentiment.polarity

def categorizar_sentimiento(puntaje):
    if puntaje >= UMBRAL_POSITIVO:
        return "Positiva"
    elif puntaje <= UMBRAL_NEGATIVO:
        return "Negativa"
    return "Neutral"


#Conexión a market_data.db

def conectar_bd():
    directorio_actual = os.path.dirname(os.path.abspath(__file__))
    directorio_proyecto = os.path.dirname(directorio_actual)
    ruta_data = os.path.join(directorio_proyecto, "data")
    os.makedirs(ruta_data, exist_ok=True)
    ruta_db = os.path.join(ruta_data, "market_data.db")
    return sqlite3.connect(ruta_db)


def _agregar_columnas_si_faltan(cursor):
    columnas_nuevas = {
        "sentimiento_vader": "REAL",
        "categoria_vader": "TEXT",
        "sentimiento_textblob": "REAL",
        "categoria_textblob": "TEXT",
    }
    for columna, tipo in columnas_nuevas.items():
        try:
            cursor.execute(f"ALTER TABLE noticias ADD COLUMN {columna} {tipo}")
        except sqlite3.OperationalError:
            pass  # la columna ya existe 


def procesar_noticias():
    conexion = conectar_bd()
    cursor = conexion.cursor()
    _agregar_columnas_si_faltan(cursor)

    cursor.execute("SELECT id, titular FROM noticias")
    noticias = cursor.fetchall()

    for id_noticia, titular in noticias:
        score_vader = calcular_sentimiento_vader(titular)
        score_textblob = calcular_sentimiento_textblob(titular)

        cursor.execute(
            """
            UPDATE noticias
            SET sentimiento_vader = ?, categoria_vader = ?,
                sentimiento_textblob = ?, categoria_textblob = ?
            WHERE id = ?
            """,
            (score_vader, categorizar_sentimiento(score_vader),
             score_textblob, categorizar_sentimiento(score_textblob),
             id_noticia)
        )

    conexion.commit()
    conexion.close()
    print(f"Sentimiento calculado para {len(noticias)} noticias.")


if __name__ == "__main__":
    procesar_noticias()