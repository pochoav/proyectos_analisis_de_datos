import os
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv
from google.cloud import bigquery

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

PROJECT_ID = os.environ["GCP_PROJECT_ID"]
DATASET = os.environ["BQ_DATASET_RAW"]
LOCATION = os.environ["BQ_LOCATION"]
TABLE = "openmeteo_hourly"

WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
AIR_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

CITIES = [
    {"city": "Ciudad de México", "latitude": 19.4326, "longitude": -99.1332, "timezone": "America/Mexico_City"},
    {"city": "Delhi", "latitude": 28.6139, "longitude": 77.2090, "timezone": "Asia/Kolkata"},
    {"city": "Los Ángeles", "latitude": 34.0522, "longitude": -118.2437, "timezone": "America/Los_Angeles"},
    {"city": "São Paulo", "latitude": -23.5505, "longitude": -46.6333, "timezone": "America/Sao_Paulo"},
    {"city": "Madrid", "latitude": 40.4168, "longitude": -3.7038, "timezone": "Europe/Madrid"},
]

def get_hourly(url, city, variables):
    """Llama a Open-Meteo y devuelve una tabla por hora"""
    params = {
        "latitude": city["latitude"],
        "longitude": city["longitude"],
        "hourly": ",".join(variables),
        "past_days": 7,
        "forecast_days": 1,
        "timezone": "UTC",
    }
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return pd.DataFrame(response.json()["hourly"])

def extract_city(city):
    """Mezclar tablas de clima y calidad de aire"""
    weather = get_hourly(WEATHER_URL, city, ["temperature_2m", "relative_humidity_2m"])
    air = get_hourly(AIR_URL, city, ["pm10", "pm2_5"])

    df = weather.merge(air, on="time", how="outer")
    df.insert(0, "city", city["city"])
    df.insert(1, "latitude", city["latitude"])
    df.insert(2, "longitude", city["longitude"])
    df.insert(3, "timezone", city["timezone"])
    return df

def load_to_bigquery(df):
    """Cargar la tabla a BigQuery"""
    client = bigquery.Client(project=PROJECT_ID, location=LOCATION)
    table_id = f"{PROJECT_ID}.{DATASET}.{TABLE}"

    schema = [
        bigquery.SchemaField("city", "STRING"),
        bigquery.SchemaField("latitude", "FLOAT"),
        bigquery.SchemaField("longitude", "FLOAT"),
        bigquery.SchemaField("timezone", "STRING"),
        bigquery.SchemaField("time", "STRING"),
        bigquery.SchemaField("temperature_2m", "FLOAT"),
        bigquery.SchemaField("relative_humidity_2m", "FLOAT"),
        bigquery.SchemaField("pm10", "FLOAT"),
        bigquery.SchemaField("pm2_5", "FLOAT"),
        bigquery.SchemaField("ingested_at", "TIMESTAMP"),
    ]
    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition="WRITE_TRUNCATE",
    )
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()
    print(f"Cargadas {len(df)} filas en {table_id}")


def main():
    frames = []
    for city in CITIES:
        df = extract_city(city)
        print(f"{city['city']}: {len(df)} filas")
        frames.append(df)

    raw = pd.concat(frames, ignore_index=True)
    raw["ingested_at"] = pd.Timestamp.now(tz="UTC")
    load_to_bigquery(raw)

if __name__ == "__main__":
    main()
