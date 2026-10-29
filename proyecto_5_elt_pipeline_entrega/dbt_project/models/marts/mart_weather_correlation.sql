#Verificar correlación entre temperatura o humedad y la contaminación

select
    city,
    round(corr(temperature_c, pm2_5_ugm3), 3) as corr_temperature_pm2_5,
    round(corr(temperature_c, pm10_ugm3), 3) as corr_temperature_pm10,
    round(corr(relative_humidity_pct, pm2_5_ugm3), 3) as corr_humidity_pm2_5,
    round(corr(relative_humidity_pct, pm10_ugm3), 3) as corr_humidity_pm10,
    count(*) as readings_count
from {{ ref('stg_openmeteo_hourly') }}
group by city