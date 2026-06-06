select 
    p.product_id,
    coalesce(c.category_english, p.category_name, 'unknown') as category_name,
    p.weight_g,
    p.length_cm,
    p.height_cm,
    p.width_cm
from {{ ref('stg_products') }} p
left join {{ ref('stg_categorical') }} c 
    on p.category_name = c.category_protuguese