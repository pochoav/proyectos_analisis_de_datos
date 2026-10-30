--Verificar cumplimiento de normas de WHO

with daily as (

    select
        city,
        date(measured_at_local) as measured_date_local,
        avg(pm2_5_ugm3) as avg_pm2_5_ugm3,
        avg(pm10_ugm3) as avg_pm10_ugm3,
        count(*) as readings_count
    from {{ ref('stg_openmeteo_hourly') }}
    group by 1, 2
    having count(*) >= 24

)

select
    city,
    measured_date_local,
    avg_pm2_5_ugm3,
    avg_pm10_ugm3,
    readings_count,
    15 as who_limit_pm2_5_ugm3,
    45 as who_limit_pm10_ugm3,
    avg_pm2_5_ugm3 > 15 as exceeds_who_pm2_5,
    avg_pm10_ugm3 > 45 as exceeds_who_pm10,
    (avg_pm2_5_ugm3 > 15 or avg_pm10_ugm3 > 45) as exceeds_who_any
from daily
