/*
  Intermediate: reglas de negocio y enriquecimiento.
  - Métricas derivadas: duración, velocidad, propina %
  - Enriquecimiento con seeds (pago, tarifa) y clima horario
  - Filtro de calidad: descarta viajes físicamente imposibles
*/

with trips as (

    select * from {{ ref('stg_taxi_trips') }}

),

payment as (select * from {{ ref('payment_types') }}),
rates   as (select * from {{ ref('rate_codes') }}),
weather as (select * from {{ ref('stg_weather_hourly') }}),

enriched as (

    select
        t.*,
        date_diff('second', t.pickup_at, t.dropoff_at) / 60.0              as trip_duration_min,
        coalesce(p.payment_type_name, 'Unknown')                           as payment_type_name,
        coalesce(r.rate_code_name, 'Unknown')                              as rate_code_name,
        w.weather_category,
        w.weather_description,
        w.temperature_c,
        w.precipitation_mm
    from trips t
    left join payment p on t.payment_type_id = p.payment_type_id
    left join rates   r on t.rate_code_id    = r.rate_code_id
    left join weather w on date_trunc('hour', t.pickup_at) = w.observed_at

),

with_metrics as (

    select
        *,
        {{ dbt_utils.safe_divide('trip_distance_miles', '(trip_duration_min / 60.0)') }} as avg_speed_mph,
        {{ dbt_utils.safe_divide('(tip_amount * 100.0)', 'fare_amount') }}               as tip_pct
    from enriched

)

select *
from with_metrics
where trip_duration_min between 1 and 180
  and trip_distance_miles > 0 and trip_distance_miles < 100
  and fare_amount > 0
  and total_amount > 0
  and avg_speed_mph < 80
