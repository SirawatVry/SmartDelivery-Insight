SELECT
    zip_code,
    avg(lat) AS lat,
    avg(lng) AS lng,
    any_value(city) AS city,
    any_value(state) AS state
from(
    select
        geolocation_zip_code_prefix AS zip_code,
        geolocation_lat AS lat,
        geolocation_lng AS lng,
        geolocation_city AS city,
        geolocation_state AS state
        from read_parquet('s3://olist-raw/geolocations.parquet')
)
group by zip_code