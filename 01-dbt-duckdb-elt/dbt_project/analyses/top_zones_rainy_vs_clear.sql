-- Análisis ad-hoc: zonas con más viajes bajo lluvia vs. clima despejado.
with by_weather as (
    select
        f.pickup_zone_id,
        f.weather_category,
        count(*) as trips
    from {{ ref('fct_trips') }} f
    where f.weather_category in ('clear', 'rain')
    group by 1, 2
)
select
    z.zone_name,
    z.borough,
    max(trips) filter (where weather_category = 'rain')  as rainy_trips,
    max(trips) filter (where weather_category = 'clear') as clear_trips
from by_weather b
join {{ ref('dim_zones') }} z on b.pickup_zone_id = z.zone_id
group by 1, 2
order by rainy_trips desc
limit 10
