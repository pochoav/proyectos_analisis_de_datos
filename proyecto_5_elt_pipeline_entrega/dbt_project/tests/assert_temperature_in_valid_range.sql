--Temperatura debe estar dentro del rango posible en la Tierra

select
    reading_id,
    city,
    measured_at_utc,
    temperature_c
from {{ ref('stg_openmeteo_hourly') }}
where temperature_c < -90
   or temperature_c > 60