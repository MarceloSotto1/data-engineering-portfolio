-- Ningún viaje puede terminar antes de empezar.
select trip_id from {{ ref('fct_trips') }} where dropoff_at <= pickup_at
