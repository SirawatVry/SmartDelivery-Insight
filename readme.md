# SmartDelivery Insight

End-to-end data engineering project using the Brazilian Olist E-Commerce dataset.

## Architecture

```
data/raw/ (Kaggle CSVs)
        │
        ▼
[Docker] ingestion
        Python → CSV to Parquet → MinIO (local S3)
        │
        ▼
[Docker] transformer
        dbt-duckdb → Star Schema → olist.duckdb
        │
        ├──────────────────────┐
        ▼                      ▼
ml/train.py             dashboard/app.py
Scikit-learn            Streamlit
model.pkl               localhost:8501
```

## Star Schema

```
                  ┌─────────────┐
                  │  dim_time   │
                  │─────────────│
                  │ date_id  PK │
                  │ year        │
                  │ month       │
                  │ is_peak     │
                  └──────┬──────┘
                         │
┌──────────────┐  ┌──────┴───────┐  ┌──────────────┐
│ dim_customers│  │  fact_orders │  │ dim_products │
│──────────────│  │──────────────│  │──────────────│
│customer_id PK│◄─┤customer_id FK│  │product_id PK │
│ zip_code     │  │product_id FK ├─►│ category     │
│ city         │  │date_id FK    │  │ weight_g     │
│ state        │  │──────────────│  └──────────────┘
│ lat / lng    │  │ total_price  │
└──────────────┘  │ total_freight│
                  │ delivery_days│
                  │ is_late      │
                  └──────────────┘
```

## Tech Stack

| Layer          | Tool                        |
|----------------|-----------------------------|
| Storage        | MinIO (Docker) — S3-compatible |
| Warehouse      | DuckDB                      |
| Transform      | dbt-duckdb                  |
| ML             | Python / Scikit-learn       |
| Dashboard      | Streamlit                   |
| Infra          | Docker Compose              |

## ML Model Performance

| Model              | RMSE       | MAE        |
|--------------------|------------|------------|
| LinearRegression   | 9.39 days  | 5.99 days  |
| RandomForest       | 9.16 days  | 5.64 days  |
| GradientBoosting   | 8.77 days  | 5.42 days  |

Best model: **GradientBoosting** — saved as `ml/model.pkl`

## Quickstart

### 1. วาง Kaggle CSV ไว้ที่ `data/raw/`

```
data/raw/
├── olist_orders_dataset.csv
├── olist_order_items_dataset.csv
├── olist_order_payments_dataset.csv
├── olist_order_reviews_dataset.csv
├── olist_customers_dataset.csv
├── olist_products_dataset.csv
├── olist_sellers_dataset.csv
├── olist_geolocation_dataset.csv
└── product_category_name_translation.csv
```

### 2. สร้าง .env

```bash
cp .env.example .env
```

### 3. รัน pipeline

```bash
docker compose up --build
```

MinIO UI: http://localhost:9001 (minioadmin / minioadmin)

### 4. Train ML model

```bash
cd ml
pip install -r requirements.txt
python train.py
```

### 5. รัน Dashboard

```bash
cd dashboard
pip install -r requirements.txt
streamlit run app.py
```

Dashboard: http://localhost:8501

## Project Structure

```
SmartDelivery-Insight/
├── docker-compose.yml
├── .env.example
├── data/
│   ├── raw/          ← วาง Kaggle CSV ที่นี่
│   └── duckdb/       ← olist.duckdb จะถูกสร้างที่นี่
├── ingestion/        ← Python + Dockerfile
├── dbt_project/      ← dbt models (Star Schema)
│   └── models/
│       ├── staging/
│       └── mart/
├── ml/               ← train.py + model.pkl
└── dashboard/        ← Streamlit app
```