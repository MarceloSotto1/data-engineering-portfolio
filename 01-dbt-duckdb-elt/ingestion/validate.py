"""
Validación del warehouse: conteos por capa, cobertura, plausibilidad y checks automáticos.
Sale con código 1 si falla algún check (se usa en el CI).

Uso:  python ingestion/validate.py
"""
import sys
from pathlib import Path

import duckdb

DB = Path(__file__).resolve().parent.parent / "data" / "warehouse.duckdb"
con = duckdb.connect(str(DB), read_only=True)


def show(title, sql):
    cur = con.execute(sql)
    cols = [d[0] for d in cur.description]
    print(f"\n=== {title} ===")
    print(" | ".join(cols))
    for r in cur.fetchall():
        print(" | ".join(str(round(x, 2) if isinstance(x, float) else x) for x in r))


def scalar(sql):
    return con.execute(sql).fetchall()[0][0]


show("1. Conteo por capa", """
    select 'raw.taxi_trips' capa, count(*) filas from raw.taxi_trips
    union all select 'staging.stg_taxi_trips', count(*) from staging.stg_taxi_trips
    union all select 'marts.fct_trips', count(*) from marts.fct_trips""")

show("2. Filas crudas por archivo", """
    select regexp_extract(_source_file, '[^/\\\\]+$') archivo, count(*) filas
    from raw.taxi_trips group by 1 order by 1""")

show("3. Rango de fechas en fct_trips", """
    select min(pickup_at) desde, max(pickup_at) hasta, count(distinct pickup_date) dias
    from marts.fct_trips""")

show("4. Cobertura del clima", """
    select (select count(*) from raw.weather_hourly) horas_clima,
           (select count(*) from marts.fct_trips where weather_category is null) viajes_sin_clima""")

show("5. Valores plausibles", """
    select round(avg(fare_amount),2) tarifa_prom, round(avg(trip_distance_miles),2) millas_prom,
           round(avg(trip_duration_min),1) min_prom, round(avg(avg_speed_mph),1) mph_prom,
           round(max(total_amount),2) max_total from marts.fct_trips""")

show("6. Top 5 zonas por ingresos", """
    select zone_name, borough, pickups, round(total_revenue) ingresos
    from marts.mart_zone_performance order by revenue_rank limit 5""")

show("7. Impacto del clima", """
    select weather_category, hours_observed, trips, round(trips_per_hour,1) viajes_por_hora,
           round(avg_tip_pct,1) propina_pct
    from marts.mart_weather_impact order by trips_per_hour desc""")

show("8. Viajes con mayor monto (revisar outliers)", """
    select pickup_at, trip_distance_miles, round(trip_duration_min,1) min, fare_amount, total_amount, rate_code_name
    from marts.fct_trips order by total_amount desc limit 5""")

# ------------------------------------------------------------------ checks automáticos
raw = scalar("select count(*) from raw.taxi_trips")
stg = scalar("select count(*) from staging.stg_taxi_trips")
fct = scalar("select count(*) from marts.fct_trips")
by_file = scalar("select sum(n) from (select count(*) n from raw.taxi_trips group by _source_file)")
no_weather = scalar("select count(*) from marts.fct_trips where weather_category is null")
dup = scalar("select count(*) - count(distinct trip_id) from marts.fct_trips")
pct = 100.0 * fct / raw

checks = {
    "raw == suma por archivo": raw == by_file,
    "raw >= staging >= fct": raw >= stg >= fct > 0,
    "se conserva >= 90% de raw": pct >= 90,
    "0 viajes sin clima": no_weather == 0,
    "0 trip_id duplicados en fct": dup == 0,
}
print(f"\n=== Checks automáticos (conservado: {pct:.2f}% de raw) ===")
for name, ok in checks.items():
    print(("✅" if ok else "❌"), name)
sys.exit(0 if all(checks.values()) else 1)
