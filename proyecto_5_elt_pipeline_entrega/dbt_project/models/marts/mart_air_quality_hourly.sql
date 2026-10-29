select
    city,
    city_timezone,
    date(measured_at_local) as measured_date_local,
    extract(hour from measured_at_local) as measured_hour_local,
    avg(temperature_c) as avg_temperature_c,
    avg(relative_humidity_pct) as avg_relative_humidity_pct,
    avg(pm10_ugm3) as avg_pm10_ugm3,
    avg(pm2_5_ugm3) as avg_pm2_5_ugm3,
    count(*) as readings_count
from {{ ref('stg_openmeteo_hourly') }}
group by 1, 2, 3, 4