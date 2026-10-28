with source as (

    select * from {{ source('air_quality_raw', 'openmeteo_hourly') }}

),

cleaned as (

    select
        city,
        timezone as city_timezone,
        latitude,
        longitude,
        parse_timestamp('%Y-%m-%dT%H:%M', time) as measured_at_utc,
        temperature_2m as temperature_c,
        relative_humidity_2m as relative_humidity_pct,
        pm10 as pm10_ugm3,
        pm2_5 as pm2_5_ugm3,
        ingested_at
    from source

),

final as (

    select
        concat(city, '|', format_timestamp('%Y-%m-%dT%H:%M', measured_at_utc)) as reading_id,
        city,
        city_timezone,
        latitude,
        longitude,
        measured_at_utc,
        datetime(measured_at_utc, city_timezone) as measured_at_local,
        temperature_c,
        relative_humidity_pct,
        pm10_ugm3,
        pm2_5_ugm3,
        ingested_at
    from cleaned
    where city is not null
      and measured_at_utc is not null
      and measured_at_utc <= current_timestamp()
      and coalesce(temperature_c, relative_humidity_pct, pm10_ugm3, pm2_5_ugm3) is not null

)

select * from final