select
    z.zone_id,
    z.borough,
    z.zone_name,
    z.is_airport,
    count(*)                          as pickups,
    sum(f.total_amount)               as total_revenue,
    avg(f.fare_amount)                as avg_fare,
    avg(f.trip_distance_miles)        as avg_distance_miles,
    rank() over (order by sum(f.total_amount) desc) as revenue_rank
from {{ ref('fct_trips') }} f
join {{ ref('dim_zones') }} z on f.pickup_zone_id = z.zone_id
group by 1, 2, 3, 4
