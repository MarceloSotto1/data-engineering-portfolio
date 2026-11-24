with spine as (

    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('" ~ var('data_start_date') ~ "' as date)",
        end_date="cast('" ~ var('data_end_date') ~ "' as date)"
    ) }}

)

select
    cast(date_day as date)           as date_day,
    year(date_day)                   as year,
    month(date_day)                  as month,
    monthname(date_day)              as month_name,
    isodow(date_day)                 as iso_day_of_week,
    dayname(date_day)                as day_name,
    isodow(date_day) in (6, 7)       as is_weekend
from spine
