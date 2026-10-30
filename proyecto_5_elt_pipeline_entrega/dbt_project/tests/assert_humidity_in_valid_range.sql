-- Valores porcentuales deben estar entre 0% y 100%

select
    reading_id,
    city,
    measured_at_utc,
    relative_humidity_pct
from {{ ref('stg_openmeteo_hourly') }}
where relative_humidity_pct < 0
   or relative_humidity_pct > 100