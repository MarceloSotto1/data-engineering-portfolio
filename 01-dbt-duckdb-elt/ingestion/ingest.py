"""
Ingesta (la "E" y "L" del ELT).

Carga datos crudos en DuckDB (schema `raw`) SIN transformarlos: dbt se encarga del resto.

Fuentes reales (gratuitas, sin API key):
  - NYC TLC Yellow Taxi trips (Parquet)   https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
  - NYC TLC taxi zone lookup (CSV)
  - Open-Meteo Historical Weather API (JSON) https://open-meteo.com/en/docs/historical-weather-api

Uso:
  python ingestion/ingest.py --source real   --start 2024-01 --end 2024-03
  python ingestion/ingest.py --source sample --start 2024-01 --end 2024-03   # offline
"""
from __future__ import annotations

import argparse
import calendar
import math
import random
from datetime import date, datetime, timedelta
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
TAXI_DIR = RAW_DIR / "taxi"
DB_PATH = ROOT / "data" / "warehouse.duckdb"

TLC_BASE = "https://d37ci6vzurychx.cloudfront.net"
OPEN_METEO_URL = "https://archive-api.open-meteo.com/v1/archive"
NYC_LAT, NYC_LON = 40.7128, -74.0060


# --------------------------------------------------------------------------- utils
def month_range(start: str, end: str) -> list[tuple[int, int]]:
    """'2024-01','2024-03' -> [(2024,1),(2024,2),(2024,3)] (ambos inclusive)."""
    sy, sm = map(int, start.split("-"))
    ey, em = map(int, end.split("-"))
    out, y, m = [], sy, sm
    while (y, m) <= (ey, em):
        out.append((y, m))
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def download(url: str, dest: Path) -> None:
    """Descarga idempotente: si el archivo existe, no se vuelve a bajar."""
    import requests

    if dest.exists():
        print(f"  = ya existe {dest.name}")
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"  ↓ {url}")
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        tmp = dest.with_suffix(dest.suffix + ".part")
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 20):
                f.write(chunk)
        tmp.rename(dest)


# ------------------------------------------------------------------ real sources
def fetch_real(months: list[tuple[int, int]]) -> list[tuple]:
    import requests

    print("Descargando viajes de taxi (TLC)...")
    for y, m in months:
        download(f"{TLC_BASE}/trip-data/yellow_tripdata_{y}-{m:02d}.parquet",
                 TAXI_DIR / f"yellow_tripdata_{y}-{m:02d}.parquet")
    print("Descargando zonas de taxi...")
    download(f"{TLC_BASE}/misc/taxi_zone_lookup.csv", RAW_DIR / "taxi_zone_lookup.csv")

    print("Consultando Open-Meteo (clima horario NYC)...")
    (y0, m0), (y1, m1) = months[0], months[-1]
    params = {
        "latitude": NYC_LAT, "longitude": NYC_LON,
        "start_date": date(y0, m0, 1).isoformat(),
        "end_date": date(y1, m1, calendar.monthrange(y1, m1)[1]).isoformat(),
        "hourly": "temperature_2m,precipitation,rain,snowfall,wind_speed_10m,weather_code",
        "timezone": "America/New_York",
    }
    resp = requests.get(OPEN_METEO_URL, params=params, timeout=120)
    resp.raise_for_status()
    h = resp.json()["hourly"]
    return list(zip(h["time"], h["temperature_2m"], h["precipitation"], h["rain"],
                    h["snowfall"], h["wind_speed_10m"], h["weather_code"]))


# ---------------------------------------------------------------- sample (offline)
SAMPLE_ZONES = [
    (1, "EWR", "Newark Airport", "EWR"), (4, "Manhattan", "Alphabet City", "Yellow Zone"),
    (13, "Manhattan", "Battery Park City", "Yellow Zone"), (43, "Manhattan", "Central Park", "Yellow Zone"),
    (79, "Manhattan", "East Village", "Yellow Zone"), (132, "Queens", "JFK Airport", "Airports"),
    (138, "Queens", "LaGuardia Airport", "Airports"), (161, "Manhattan", "Midtown Center", "Yellow Zone"),
    (236, "Manhattan", "Upper East Side North", "Yellow Zone"), (237, "Manhattan", "Upper East Side South", "Yellow Zone"),
    (68, "Manhattan", "East Chelsea", "Yellow Zone"), (74, "Manhattan", "East Harlem North", "Boro Zone"),
    (186, "Manhattan", "Penn Station/Madison Sq West", "Yellow Zone"), (230, "Manhattan", "Times Sq/Theatre District", "Yellow Zone"),
    (249, "Manhattan", "West Village", "Yellow Zone"), (265, "N/A", "Unknown", "N/A"),
]


def make_sample(months: list[tuple[int, int]], rows_per_month: int = 20_000) -> list[tuple]:
    random.seed(42)
    TAXI_DIR.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    ids = [z[0] for z in SAMPLE_ZONES]
    id_list = "[" + ",".join(map(str, ids)) + "]"

    for y, m in months:
        start = datetime(y, m, 1)
        span = calendar.monthrange(y, m)[1] * 86400
        out = TAXI_DIR / f"yellow_tripdata_{y}-{m:02d}.parquet"
        con.execute(f"""
        copy (
          with b as materialized (
            select i,
                   timestamp '{start:%Y-%m-%d}' + to_seconds((random() * {span - 1})::bigint) as pu_ts,
                   (1 + random() * 14)::double as dist,
                   random() as r1, random() as r2, random() as r3
            from range({rows_per_month}) t(i)
          )
          select
            (1 + (r1 * 2)::int)::bigint                                   as VendorID,
            pu_ts                                                        as tpep_pickup_datetime,
            case when i % 700 = 0 then pu_ts - interval 5 minute
                 else pu_ts + to_minutes((4 + dist * 4)::int) end        as tpep_dropoff_datetime,
            (1 + (r2 * 4)::int)::double                                  as passenger_count,
            round(dist, 2)::double                                       as trip_distance,
            case when r3 < 0.9 then 1 when r3 < 0.95 then 2 else 99 end::double as RatecodeID,
            'N'                                                          as store_and_fwd_flag,
            {id_list}[1 + (hash(i) % {len(ids)})::int]                    as PULocationID,
            {id_list}[1 + (hash(i * 7 + 3) % {len(ids)})::int]            as DOLocationID,
            case when r1 < 0.7 then 1 when r1 < 0.95 then 2 else 3 end::bigint as payment_type,
            case when i % 500 = 0 then -10.0 else round(3 + dist * 2.8, 2) end as fare_amount,
            0.5::double as extra, 0.5::double as mta_tax,
            case when r1 < 0.7 then round((3 + dist * 2.8) * (0.1 + r2 * 0.15), 2) else 0 end as tip_amount,
            0.0::double as tolls_amount, 1.0::double as improvement_surcharge,
            round((3 + dist * 2.8) * 1.3 + 2.5, 2)::double               as total_amount,
            2.5::double as congestion_surcharge
          from b
          union all
          select 1, timestamp '2002-12-31 23:00:00', timestamp '2002-12-31 23:20:00', 1.0, 2.0, 1.0, 'N',
                 161, 237, 1, 10.0, 0.5, 0.5, 2.0, 0.0, 1.0, 14.0, 2.5
        ) to '{out.as_posix()}' (format parquet)""")
        print(f"  ✓ sample {out.name}")

    with open(RAW_DIR / "taxi_zone_lookup.csv", "w", encoding="utf-8") as f:
        f.write("LocationID,Borough,Zone,service_zone\n")
        for z in SAMPLE_ZONES:
            f.write(",".join(f'"{c}"' if isinstance(c, str) else str(c) for c in z) + "\n")

    # clima sintético horario con ciclo diario/estacional y lluvias aleatorias
    rows, t = [], datetime(months[0][0], months[0][1], 1)
    (ey, em) = months[-1]
    end = datetime(ey, em, calendar.monthrange(ey, em)[1], 23)
    while t <= end:
        temp = 10 + 8 * math.sin((t.hour - 9) / 24 * 2 * math.pi) + random.gauss(0, 1.5)
        raining = random.random() < 0.15
        snowing = raining and temp < 1
        precip = round(random.uniform(0.1, 6), 1) if raining else 0.0
        code = 73 if snowing else 63 if raining else random.choice([0, 1, 2, 3, 45])
        rows.append((t.strftime("%Y-%m-%dT%H:%M"), round(temp, 1), precip,
                     0.0 if snowing else precip, round(precip * 0.7, 1) if snowing else 0.0,
                     round(random.uniform(2, 30), 1), code))
        t += timedelta(hours=1)
    return rows


# ------------------------------------------------------------------------- load
def load_duckdb(weather_rows: list[tuple]) -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB_PATH))
    con.execute("create schema if not exists raw")

    taxi_glob = (TAXI_DIR / "*.parquet").as_posix()
    con.execute(f"""
        create or replace table raw.taxi_trips as
        select * exclude (filename), filename as _source_file, current_timestamp as _loaded_at
        from read_parquet('{taxi_glob}', union_by_name = true, filename = true)""")

    con.execute(f"""
        create or replace table raw.taxi_zones as
        select * from read_csv('{(RAW_DIR / "taxi_zone_lookup.csv").as_posix()}', header = true)""")

    con.execute("""
        create or replace table raw.weather_hourly (
            time varchar, temperature_2m double, precipitation double, rain double,
            snowfall double, wind_speed_10m double, weather_code integer,
            _loaded_at timestamp default current_timestamp)""")
    con.executemany(
        "insert into raw.weather_hourly (time, temperature_2m, precipitation, rain, snowfall, wind_speed_10m, weather_code) "
        "values (?,?,?,?,?,?,?)", weather_rows)

    for t in ("taxi_trips", "taxi_zones", "weather_hourly"):
        n = con.execute(f"select count(*) from raw.{t}").fetchone()[0]
        print(f"  raw.{t:<15} {n:>12,} filas")
    con.close()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", choices=["real", "sample"], default="real")
    ap.add_argument("--start", default="2024-01", help="YYYY-MM")
    ap.add_argument("--end", default="2024-03", help="YYYY-MM")
    a = ap.parse_args()

    # Cada fuente usa su propia carpeta: los archivos reales y los de muestra nunca se mezclan.
    global RAW_DIR, TAXI_DIR
    RAW_DIR = ROOT / "data" / "raw" / a.source
    TAXI_DIR = RAW_DIR / "taxi"

    months = month_range(a.start, a.end)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    if a.source == "real":
        weather = fetch_real(months)
    else:
        for old in TAXI_DIR.glob("*.parquet"):
            old.unlink()
        weather = make_sample(months)
    print("Cargando en DuckDB...")
    load_duckdb(weather)
    print(f"Listo → {DB_PATH}")


if __name__ == "__main__":
    main()
