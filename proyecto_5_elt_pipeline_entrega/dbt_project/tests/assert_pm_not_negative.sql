-- Concentraciones de contaminantes no pueden ser negativas

select
    reading_id,
    city,
    measured_at_utc,
    pm10_ugm3,
    pm2_5_ugm3
from {{ ref('stg_openmeteo_hourly') }}
where pm10_ugm3 < 0
   or pm2_5_ugm3 < 0