{{ config(materialized='view') }}

/*
  Staging: 1 fila por viaje, tipado y renombrado. Sin lógica de negocio.
  - Acota al rango [data_start_date, data_end_date): los archivos TLC traen fechas fuera de rango.
  - Deduplica por trip_id (clave surrogate de los campos naturales del viaje).
*/

with source as (

    select * from {{ source('raw', 'taxi_trips') }}

),

renamed as (

    select
        {{ dbt_utils.generate_surrogate_key([
            'VendorID', 'tpep_pickup_datetime', 'tpep_dropoff_datetime',
            'PULocationID', 'DOLocationID', 'total_amount'
        ]) }}                                          as trip_id,
        cast(VendorID as integer)                      as vendor_id,
        cast(tpep_pickup_datetime as timestamp)        as pickup_at,
        cast(tpep_dropoff_datetime as timestamp)       as dropoff_at,
        cast(passenger_count as integer)               as passenger_count,
        cast(trip_distance as double)                  as trip_distance_miles,
        coalesce(cast(RatecodeID as integer), 99)      as rate_code_id,
        cast(PULocationID as integer)                  as pickup_zone_id,
        cast(DOLocationID as integer)                  as dropoff_zone_id,
        coalesce(cast(payment_type as integer), 5)     as payment_type_id,
        cast(fare_amount as double)                    as fare_amount,
        cast(tip_amount as double)                     as tip_amount,
        cast(tolls_amount as double)                   as tolls_amount,
        cast(total_amount as double)                   as total_amount,
        _source_file,
        _loaded_at
    from source

),

in_range as (

    select * from renamed
    where pickup_at >= cast('{{ var("data_start_date") }}' as timestamp)
      and pickup_at <  cast('{{ var("data_end_date") }}' as timestamp)

)

select * from in_range
qualify row_number() over (partition by trip_id order by _loaded_at) = 1
