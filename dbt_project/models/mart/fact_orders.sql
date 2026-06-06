with items as (
    select
        order_id,
        first(product_id)  as product_id,
        sum(price)         as total_price,
        sum(freight_value) as total_freight
    from {{ ref('stg_order_items') }}
    group by order_id
),
orders as (
    select * from {{ ref('stg_orders') }}
)
select
    o.order_id,
    o.customer_id,
    i.product_id,
    o.order_purchase_timestamp::date as date_id,
    i.total_price,
    i.total_freight,
    
    datediff('day',o.order_purchase_timestamp::timestamp,o.order_delivered_customer_date::timestamp) as actual_delivery_days,
        case
            when o.order_delivered_customer_date > o.order_estimated_delivery_date then true
        else false
    end as is_late_delivery,

    o.order_status

from orders o
left join items i using(order_id)

where o.order_status = 'delivered'
  and o.order_delivered_customer_date is not null