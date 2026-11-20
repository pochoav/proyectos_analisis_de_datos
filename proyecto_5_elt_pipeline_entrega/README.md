# Pipeline ELT de calidad del aire y clima en la nube

**Environmental & Smart City Analytics** · Proyecto 5 Análisis de Datos

Pipeline de datos moderno con arquitectura **ELT** que monitorea la calidad del aire y clima en 5 grandes ciudades para la toma de decisiones. Extrae datos de la API Open-Meteo, los carga a BigQuery, se tranforman dentro del warehouse con dbt, orquesta la ejecución con Apahce Airflow y los presenta en un dashboard de Data Studio.

- **Ciudades:** Ciudad de México, Delhi, Los Ángeles, São Paulo y Madrid.
- **Variables:** PM2.5, PM10, temperatura y humedad relativa, por hora.
- **Ventana de datos:** los últimos 7 días
- **Dashboard:** [Ver dashboard en Data Studio](https://datastudio.google.com/reporting/fbab7b1b-e32b-4397-878c-b3f255bbb960)

## Preguntas de negocio

| Pregunta | Modelo dbt que la responde | Dashboard |
| --- | --- | --- |
| ¿Cuáles son las horas pico del día con peor calidad del aire por ciudad? | `mart_peak_hours` | Página 2 del dashboard|
| ¿Existe correlación entre temperatura o humedad y la concentración de PM2.5 y PM10? | `mart_weather_correlation` | Página 3 del dashboard|
| ¿Qué ciudades superaron los límites de la OMS en la última semana? | `mart_who_exceedances` | Página 1 del dashboard|

Un cuarto model, `mart_air_quality_hourly`, deja los promedios por ciudad, fecha local y hora local como tabla base para análisis posterior.

## Arquitectura

![Arquitectura del pipeline](architecture_diagram.png)

El flujo sigue el patrón **ElT**: los datos se cargan en bruto y se transforman dentro del warehouse.

1. **Extracción (Python).** `scripts/extract_to_warehouse.py` consulta dos endpoints de Open-Meteo por ciudad: el de clima (temperatura y humedad) y el de calidad del aire (PM2.5 y PM10). Une ambos por hora y obtiene 192 filas por ciudad (7 días anteriores y el día en curso, en UTC).
2. **Carga (BigQuery, capa cruda).** La tabla `air_quality_raw.openmeteo_hourly` guarda los datos tal como llegan, sin transformaciones. Cada ejecución reemplaza la tabla (`WRITE_TRUNCATE`).
3. **Transformación (dbt Core).** Dentro de BigQuery, el modelo de *staging* limpia y tipifica los datos (vista) y cuatro *marts* los agregan para negocio (tablas), en el dataset `air_quality_dbt`. `dbt test` ejecuta 16 pruebas de calidad.
4. **Orquestación (Apache Airflow).** El DAG `air_quality_elt_pipeline` encadena tres tareas: extracción, `dbt run` y `dbt test`. Se ejecuta de forma manual desde la interfaz local.
5. **Visualización (Data Studio).** El dashboard se conecta directamente a los marts en BigQuery.

En el diagrama, Airflow aparece como una banda que encuelce las tareas y no como un paso del flujo de datos, porque orquesta la ejecución mientras no mueve datos.

## Herramientas

| Capa | Herramienta | Versión |
| --- | --- | --- |
| Entorno de desarrollo | WSL2 con Ubuntu y VSCode | |
| Extracción | Python, requests, pandas, pyarrow | Python 3.14 · pandas 3.1.0 |
| Data warehouse | Google BigQuery (google-cloud-bigquery) | 3.46.2 |
| Transformación y calidad | dbt Core con dbt-bigquery | 1.12.6 · 1.12.1 |
| Orquestación | Apache Airflow (modo standalone) | 3.2.0 · Python 3.12 |
| Business intelligence | Data Studio (anteriormente Looker Studio) | |
| Diagrama | Graphviz y la librería graphviz de Python | 14.1 · 0.21 |

Cada herramienta usa su propio entorno virtual de Python. Las versiones exactas se encuentran en los archivos `requirements-*.txt`.

## Estructura del repositorio

```text
proyecto_5_elt_pipeline_entrega/
├── dashboard/
│   └── dashboard_link.txt            # Enlace al dashboard de Data Studio
├── dbt_project/
│   ├── models/
│   │   ├── staging/
│   │   │   ├── sources.yml           # Declaración de la tabla cruda de BigQuery
│   │   │   ├── schema.yml            # Pruebas del modelo de staging
│   │   │   └── stg_openmeteo_hourly.sql
│   │   └── marts/
│   │       ├── schema.yml            # Pruebas de los marts
│   │       ├── mart_air_quality_hourly.sql
│   │       ├── mart_peak_hours.sql
│   │       ├── mart_weather_correlation.sql
│   │       └── mart_who_exceedances.sql
│   ├── tests/                        # Pruebas de rangos imposibles (SQL)
│   │   ├── assert_temperature_in_valid_range.sql
│   │   ├── assert_humidity_in_valid_range.sql
│   │   └── assert_pm_not_negative.sql
│   └── dbt_project.yml
├── orchestration/
│   └── dags/
│       └── airflow_pipeline.py       # DAG de Airflow
├── scripts/
│   ├── extract_to_warehouse.py       # Ingesta API -> BigQuery
│   └── generate_architecture_diagram.py
├── architecture_diagram.png
├── .env.example                      # Plantilla para variables de entorno
├── requirements-extract.txt
├── requirements-dbt.txt
├── requirements-airflow.txt
├── requirements-diagram.txt
└── README.md
```

Fuera del repositorio quedan el archivo `~/.dbt/profiles.yml` (conexión de dbt), el archivo `.env` con tus valores reales y los entornos virtuales en `~/venvs/`.