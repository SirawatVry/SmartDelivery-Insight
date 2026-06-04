select product_category_name AS category_protuguese ,
       product_category_name_english AS category_english
from read_parquet('s3://olist-raw/product_category_name_translation.parquet')