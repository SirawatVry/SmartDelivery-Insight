select 
    customer_id,
    customer_unique_id,
    stg_customers.city as customer_city,
    stg_customers.state as customer_state,
    zip_code,
    lat,
    lng
from {{ ref('stg_customers') }}
left join {{ ref('stg_geolocation') }} using(zip_code)