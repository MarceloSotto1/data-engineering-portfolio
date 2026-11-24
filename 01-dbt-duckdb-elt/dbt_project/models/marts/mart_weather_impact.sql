/*
  ¿Cómo afecta el clima a la demanda y al comportamiento de los pasajeros?
  `trips_per_hour` normaliza por la cantidad de horas de cada categoría de clima
  (si no, "clear" ganaría siempre simplemente por haber más horas despejadas).
*/

with trips as (

    select
        weather_category,
        count(*)               as trips,
        avg(total_amount)      as avg_total_amount,
        avg(tip_pct)           as avg_tip_pct,
        avg(avg_speed_mph)     as avg_speed_mph,
        avg(trip_duration_min) as avg_duration_min
    from {{ ref('fct_trips') }}
    where weather_category is not null
    group by 1

),

weather_hours as (

    select weather_category, count(*) as hours_observed
    from {{ ref('stg_weather_hourly') }}
    where observed_at >= cast('{{ var("data_start_date") }}' as timestamp)
      and observed_at <  cast('{{ var("data_end_date") }}' as timestamp)
    group by 1

)

select
    t.weather_category,
    w.hours_observed,
    t.trips,
    t.trips * 1.0 / nullif(w.hours_observed, 0)      as trips_per_hour,
    t.avg_total_amount,
    t.avg_tip_pct,
    t.avg_speed_mph,
    t.avg_duration_min
from trips t
left join weather_hours w using (weather_category)
