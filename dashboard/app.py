import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st
import joblib
import numpy as np
from pathlib import Path
from sklearn.preprocessing import LabelEncoder

# ── Config ────────────────────────────────────────────────
DUCKDB_PATH = Path("../data/duckdb/olist.duckdb")
MODEL_PATH  = Path("model.pkl")

st.set_page_config(
    page_title="SmartDelivery Insight",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }
    h1, h2, h3 { font-family: 'IBM Plex Mono', monospace; font-weight: 600; }
    .block-container { padding: 2rem 3rem; max-width: 1400px; }
    .section-label {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.7rem;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        color: #888;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_late_delivery_by_state():
    con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    df = con.execute("""
        SELECT
            c.customer_state,
            count(*)                                             as total_orders,
            sum(case when o.is_late_delivery then 1 end)         as late_orders,
            round(
                sum(case when o.is_late_delivery then 1 end) * 100.0 / count(*), 1
            )                                                    as late_pct
        FROM fact_orders o
        JOIN dim_customers c ON o.customer_id = c.customer_id
        GROUP BY c.customer_state
        ORDER BY late_pct DESC
    """).fetchdf()
    con.close()
    return df


@st.cache_data
def load_rfm():
    con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    df = con.execute("""
        WITH rfm_raw AS (
            SELECT
                customer_id,
                datediff('day', max(date_id), current_date) as recency,
                count(*)                                          as frequency,
                sum(total_price)                                  as monetary
            FROM fact_orders
            GROUP BY customer_id
        ),
        scored AS (
            SELECT *,
                ntile(4) OVER (ORDER BY recency DESC) as r_score,
                ntile(4) OVER (ORDER BY frequency)    as f_score,
                ntile(4) OVER (ORDER BY monetary)     as m_score
            FROM rfm_raw
        )
        SELECT
            CASE
                WHEN r_score = 4 AND f_score >= 3 THEN 'Champions'
                WHEN r_score >= 3 AND f_score >= 2 THEN 'Loyal'
                WHEN r_score >= 3 AND f_score = 1  THEN 'New Customers'
                WHEN r_score = 2                   THEN 'At Risk'
                ELSE 'Lost'
            END as segment,
            count(*) as customer_count
        FROM scored
        GROUP BY segment
        ORDER BY customer_count DESC
    """).fetchdf()
    con.close()
    return df


@st.cache_data
def load_categories_and_states():
    con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    cats   = con.execute("SELECT DISTINCT category_name FROM dim_products WHERE category_name IS NOT NULL ORDER BY 1").fetchdf()
    states = con.execute("SELECT DISTINCT customer_state FROM dim_customers WHERE customer_state IS NOT NULL ORDER BY 1").fetchdf()
    con.close()
    return cats['category_name'].tolist(), states['customer_state'].tolist()


@st.cache_resource
def load_model():
    return joblib.load(MODEL_PATH)


@st.cache_data
def load_training_data():
    con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    df = con.execute("""
        SELECT c.customer_state, p.category_name
        FROM fact_orders o
        JOIN dim_customers c ON o.customer_id = c.customer_id
        JOIN dim_products  p ON o.product_id  = p.product_id
        WHERE o.actual_delivery_days IS NOT NULL
          AND c.customer_state IS NOT NULL
          AND p.category_name IS NOT NULL
    """).fetchdf()
    con.close()
    return df


# ── Header ────────────────────────────────────────────────
st.markdown('<p class="section-label">Olist E-Commerce — Brazil</p>', unsafe_allow_html=True)
st.title("SmartDelivery Insight")
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["Late Delivery Map", "Delivery Predictor", "Customer Segments"])

# ── Tab 1: Late Delivery ──────────────────────────────────
with tab1:
    st.markdown('<p class="section-label">Late delivery rate by state (%)</p>', unsafe_allow_html=True)
    df_late = load_late_delivery_by_state()

    fig = px.bar(
        df_late,
        x="customer_state", y="late_pct",
        color="late_pct",
        color_continuous_scale="Reds",
        labels={"late_pct": "Late Delivery %", "customer_state": "State"},
        text="late_pct",
    )
    fig.update_traces(texttemplate='%{text}%', textposition='outside')
    fig.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        coloraxis_showscale=False,
        margin=dict(t=20, b=40),
        font_family="IBM Plex Sans",
    )
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Raw data"):
        st.dataframe(df_late, use_container_width=True)


# ── Tab 2: Predictor ──────────────────────────────────────
with tab2:
    st.markdown('<p class="section-label">Estimate delivery time for a new order</p>', unsafe_allow_html=True)
    categories, states = load_categories_and_states()

    col1, col2 = st.columns(2)
    with col1:
        state         = st.selectbox("Customer State", states)
        category      = st.selectbox("Product Category", categories)
    with col2:
        weight_g      = st.number_input("Product Weight (g)", min_value=0, max_value=50000, value=500, step=100)
        total_freight = st.number_input("Freight Value (BRL)", min_value=0.0, max_value=500.0, value=20.0, step=1.0)

    if st.button("Predict Delivery Time"):
        try:
            model    = load_model()
            train_df = load_training_data()

            le_state    = LabelEncoder().fit(train_df['customer_state'])
            le_category = LabelEncoder().fit(train_df['category_name'])

            state_enc    = le_state.transform([state])[0]
            category_enc = le_category.transform([category])[0]

            X_input = np.array([[total_freight, weight_g, state_enc, category_enc]])
            pred    = model.predict(X_input)[0]

            st.markdown("---")
            st.markdown(f"### Estimated delivery: **{pred:.0f} days**")

        except Exception as e:
            st.error(f"Prediction failed: {e}")


# ── Tab 3: RFM ────────────────────────────────────────────
with tab3:
    st.markdown('<p class="section-label">Customer segmentation — RFM analysis</p>', unsafe_allow_html=True)
    df_rfm = load_rfm()

    fig3 = px.bar(
        df_rfm,
        x="segment", y="customer_count",
        color="segment",
        color_discrete_sequence=["#2563eb", "#16a34a", "#dc2626", "#d97706", "#7c3aed"],
        labels={"customer_count": "Customers", "segment": "Segment"},
        text="customer_count",
    )
    fig3.update_traces(textposition='outside')
    fig3.update_layout(
        plot_bgcolor="#9d978a", paper_bgcolor="#9d978a",
        showlegend=False,
        margin=dict(t=20, b=40),
        font_family="IBM Plex Sans",
        font=dict(color="#111111")
    )
    st.plotly_chart(fig3, use_container_width=True)

    cols = st.columns(len(df_rfm))
    for i, row in df_rfm.iterrows():
        with cols[i]:
            st.metric(row['segment'], f"{row['customer_count']:,}")