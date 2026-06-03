import os 
import boto3
import pandas as pd
import io
from pathlib import Path
from botocore.client import Config

MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT', 'http://minio:9000')
MINIO_ACCESS = os.getenv('MINIO_ROOT_USER', 'minioadmin')
MINIO_SECRET = os.getenv('MINIO_ROOT_PASSWORD', 'minioadmin')
BUCKET = 'olist-raw'
DATA_DIR = Path("/data/raw")

TABLES = {
    "orders": "olist_orders_dataset.csv",
    "customers": "olist_customers_dataset.csv",
    "products": "olist_products_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "geolocations": "olist_geolocation_dataset.csv",
    "order_payments": "olist_order_payments_dataset.csv",
    "order_reviews": "olist_order_reviews_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "product_category_name_translation": "product_category_name_translation.csv",

}

def get_client():
    return boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ACCESS,
        aws_secret_access_key=MINIO_SECRET,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )
def upload(s3,table_name,cs_filename):
    df = pd.read_csv(DATA_DIR / cs_filename)
    df.to_parquet(buffer := io.BytesIO(), index=False)
    buffer.seek(0)
    s3.put_object(
        Bucket=BUCKET,
        Key=f"{table_name}.parquet",
        Body=buffer.getvalue()
    )

def main():
    s3 = get_client()
    for table_name, filename in TABLES.items():
        upload(s3, table_name, filename)

if __name__ == "__main__":
    main()