--Búsqueda de horas pico

with hourly as (

    select
        city,
        extract(hour from measured_at_local) as hour_of_day_local,
        avg(pm2_5_ugm3) as avg_pm2_5_ugm3,
        avg(pm10_ugm3) as avg_pm10_ugm3,
        count(*) as readings_count
    from {{ ref('stg_openmeteo_hourly') }}
    group by 1, 2

)

select
    city,
    hour_of_day_local,
    avg_pm2_5_ugm3,
    avg_pm10_ugm3,
    readings_count,
    rank() over (partition by city order by avg_pm2_5_ugm3 desc) as pm2_5_rank
from hourly