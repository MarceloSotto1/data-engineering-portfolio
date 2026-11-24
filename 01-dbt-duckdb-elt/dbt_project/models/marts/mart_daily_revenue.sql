with daily as (

    select
        pickup_date,
        count(*)                      as trips,
        sum(total_amount)             as total_revenue,
        avg(fare_amount)              as avg_fare,
        avg(tip_pct)                  as avg_tip_pct,
        avg(trip_distance_miles)      as avg_distance_miles
    from {{ ref('fct_trips') }}
    group by 1

)

select
    d.pickup_date,
    dt.day_name,
    dt.is_weekend,
    d.trips,
    d.total_revenue,
    d.avg_fare,
    d.avg_tip_pct,
    d.avg_distance_miles,
    avg(d.total_revenue) over (
        order by d.pickup_date rows between 6 preceding and current row
    ) as revenue_7d_moving_avg
from daily d
left join {{ ref('dim_date') }} dt on d.pickup_date = dt.date_day
