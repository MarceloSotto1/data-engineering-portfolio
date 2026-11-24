{{ config(
    materialized='incremental',
    unique_key='trip_id',
    incremental_strategy='delete+insert',
    on_schema_change='append_new_columns'
) }}

/*
  Tabla de hechos. Grain: 1 fila por viaje.
  Incremental con ventana de reproceso de 1 día para absorber datos tardíos;
  `delete+insert` por trip_id evita duplicados al reprocesar.
*/

select
    trip_id,
    cast(pickup_at as date)         as pickup_date,
    pickup_at,
    dropoff_at,
    extract(hour from pickup_at)    as pickup_hour,
    pickup_zone_id,
    dropoff_zone_id,
    vendor_id,
    payment_type_name,
    rate_code_name,
    passenger_count,
    trip_distance_miles,
    trip_duration_min,
    avg_speed_mph,
    fare_amount,
    tip_amount,
    tolls_amount,
    total_amount,
    tip_pct,
    weather_category,
    temperature_c,
    precipitation_mm
from {{ ref('int_trips_enriched') }}

{% if is_incremental() %}
where pickup_at >= (select max(pickup_at) - interval 1 day from {{ this }})
{% endif %}
