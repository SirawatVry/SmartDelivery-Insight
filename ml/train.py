import duckdb
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error
from sklearn.preprocessing import LabelEncoder
import joblib
import numpy as np
from pathlib import Path
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import GradientBoostingRegressor

DUCKDB_PATH = Path("../data/duckdb/olist.duckdb")
MODEL_PATH  = Path("model.pkl")

def load_data():
    con = duckdb.connect(DUCKDB_PATH)
    query = """
    SELECT 
        o.actual_delivery_days,
        o.total_freight,
        o.is_late_delivery,
        c.customer_state,
        p.category_name,
        p.weight_g
    FROM fact_orders o
    JOIN dim_customers c ON o.customer_id = c.customer_id
    JOIN dim_products p ON o.product_id = p.product_id
    """
    df = con.execute(query).fetchdf()
    con.close()
    return df

def prepare_features(df):
    y = df['actual_delivery_days']
    x = df[[
        'total_freight',
        'weight_g',
        'customer_state',
        'category_name'
    ]].copy()
    x = x.dropna()
    y = y[x.index]
    le_customer_state = LabelEncoder()
    le_category = LabelEncoder()
    x['customer_state'] = le_customer_state.fit_transform(x['customer_state'])
    x['category_name'] = le_category.fit_transform(x['category_name'])
    return x, y

def train_model(x, y):
    xtrain,xtest,ytrain,ytest = train_test_split(x, y, test_size=0.2, random_state=50)
    models = {
    "LinearRegression":      LinearRegression(),
    "RandomForest":          RandomForestRegressor(n_estimators=100, random_state=50),
    "GradientBoosting":      GradientBoostingRegressor(n_estimators=100, random_state=50),
    }
    best_model = None
    best_rmse = float('inf')
    for name, model in models.items():
        model.fit(xtrain, ytrain)
        ypred = model.predict(xtest)
        rmse = np.sqrt(mean_squared_error(ytest, ypred))
        mae = mean_absolute_error(ytest, ypred)
        print(f"{name}:")
        print(f"  RMSE: {rmse:.2f} days")
        print(f"  MAE:  {mae:.2f} days")
        if rmse < best_rmse:
            best_rmse = rmse
            best_model = model
    return best_model   

def save_model(model):
    joblib.dump(model, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")

if __name__ == "__main__":
    df = load_data()
    x, y = prepare_features(df)
    model = train_model(x, y)
    save_model(model)
