select ORDER_ITEM_ID, ORDER_ID, PRODUCT_ID, SELLER_ID   , PRICE, FREIGHT_VALUE
from read_parquet('s3://olist-raw/order_items.parquet')