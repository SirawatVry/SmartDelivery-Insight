SELECT order_id, payment_sequential, payment_type, payment_installments, payment_value
FROM read_parquet('s3://olist-raw/order_payments.parquet')