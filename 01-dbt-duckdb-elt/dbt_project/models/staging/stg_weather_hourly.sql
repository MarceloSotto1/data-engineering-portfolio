with source as (

    select * from {{ source('raw', 'weather_hourly') }}

),

codes as (

    select * from {{ ref('wmo_weather_codes') }}

)

select
    cast(s.time as timestamp)        as observed_at,
    s.temperature_2m                 as temperature_c,
    s.precipitation                  as precipitation_mm,
    s.rain                           as rain_mm,
    s.snowfall                       as snowfall_cm,
    s.wind_speed_10m                 as wind_speed_kmh,
    s.weather_code,
    coalesce(c.weather_description, 'Unknown') as weather_description,
    coalesce(c.weather_category, 'unknown')    as weather_category
from source s
left join codes c on s.weather_code = c.weather_code
