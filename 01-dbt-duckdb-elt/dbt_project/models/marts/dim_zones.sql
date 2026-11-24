select
    location_id as zone_id,
    borough,
    zone_name,
    service_zone,
    service_zone in ('Airports', 'EWR') as is_airport
from {{ ref('stg_taxi_zones') }}
