-- Reconciliación: la suma del mart diario debe coincidir con la tabla de hechos.
select
    (select sum(total_revenue) from {{ ref('mart_daily_revenue') }}) as mart_total,
    (select sum(total_amount)  from {{ ref('fct_trips') }})          as fact_total
where abs(
    (select sum(total_revenue) from {{ ref('mart_daily_revenue') }})
  - (select sum(total_amount)  from {{ ref('fct_trips') }})
) > 0.01
