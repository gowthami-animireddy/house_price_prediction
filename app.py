import joblib
import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_icon="🏠",
    page_title="House Price Prediction",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Custom CSS ----------
st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.4rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 0.2rem;
    }
    .subtitle {
        text-align: center;
        color: #808495;
        margin-bottom: 1.5rem;
    }
    .result-card {
        background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
        padding: 2rem;
        border-radius: 16px;
        text-align: center;
        color: white;
        margin-top: 1rem;
        box-shadow: 0 8px 24px rgba(37, 99, 235, 0.25);
    }
    .result-card h2 {
        margin: 0;
        font-size: 1rem;
        font-weight: 400;
        opacity: 0.85;
    }
    .result-card h1 {
        margin: 0.3rem 0 0 0;
        font-size: 2.6rem;
        font-weight: 800;
    }
    div[data-testid="stButton"] button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        font-weight: 600;
        font-size: 1.05rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Load model & data ----------
@st.cache_resource
def load_model():
    with open("Rf_model.joblib", "rb") as file:
        return joblib.load(file)

@st.cache_data
def load_data():
    return pd.read_csv("cleaned_df.csv")

model = load_model()
df = load_data()


def find_column(candidates, columns):
    """Return the first matching column name (case-insensitive) from a list of candidates."""
    lower_map = {c.lower(): c for c in columns}
    for cand in candidates:
        if cand in lower_map:
            return lower_map[cand]
    return None


SQFT_COL = find_column(
    ["sqft", "total_sqft", "area", "sq_ft", "square_feet", "area_sqft"], df.columns
)
PRICE_COL = find_column(
    ["price", "price_lakhs", "total_price", "cost", "value"], df.columns
)

if "history" not in st.session_state:
    st.session_state.history = []

# ---------- Sidebar ----------
with st.sidebar:
    try:
        st.image("house.jpg", width="stretch")
    except TypeError:
        st.image("house.jpg", use_column_width=True)

    st.markdown("## 🏠 House Price Predictor")
    st.write(
        "Estimate the market value of a home in Bangalore based on "
        "location, size, and configuration."
    )
    st.markdown("---")
    st.markdown(
        """
        **How it works**
        1. Pick a location
        2. Enter the area in sq.ft
        3. Choose bathrooms & BHK
        4. Click **Predict**
        """
    )
    st.markdown("---")
    c1, c2 = st.columns(2)
    c1.metric("Records", f"{len(df):,}")
    c2.metric("Locations", f"{df['location'].nunique():,}")

    with st.expander("🔧 Detected columns (debug)"):
        st.write(f"Area column: `{SQFT_COL}`")
        st.write(f"Price column: `{PRICE_COL}`")
        st.write("All columns:", list(df.columns))

# ---------- Header ----------
st.markdown('<div class="main-title">🏠 House Price Prediction</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Get an instant price estimate for your dream home</div>',
    unsafe_allow_html=True,
)

tab_predict, tab_compare, tab_insights, tab_history = st.tabs(
    ["🔮 Predict", "⚖️ Compare", "📊 Market Insights", "🕒 History"]
)


def get_encoded_loc(location):
    match = df.loc[df["location"] == location, "encoded_loc"]
    return match.iloc[0] if not match.empty else None


def predict_price(location, sqft, bath, bhk):
    encoded_loc = get_encoded_loc(location)
    if encoded_loc is None:
        return None
    inp_data = [[sqft, bath, bhk, encoded_loc]]
    pred = model.predict(inp_data)[0]
    return round(float(pred), 2)


# ================= PREDICT TAB =================
with tab_predict:
    with st.container(border=True):
        st.subheader("Property Details")
        col1, col2 = st.columns(2)

        with col1:
            location = st.selectbox("📍 Location", options=sorted(df["location"].unique()))
            sqft = st.number_input("📐 Area (sq.ft)", min_value=300, step=50, value=1000)

        with col2:
            bath = st.selectbox("🛁 Bathrooms", options=sorted(df["bath"].unique()))
            bhk = st.selectbox("🛏️ BHK", options=sorted(df["bhk"].unique()))

        predict_clicked = st.button("🔍 Predict Price", type="primary")

    if predict_clicked:
        encoded_loc = get_encoded_loc(location)

        if encoded_loc is None:
            st.error("Couldn't find an encoding for that location. Please pick another one.")
        else:
            with st.spinner("Crunching the numbers..."):
                inp_data = [[sqft, bath, bhk, encoded_loc]]
                pred = model.predict(inp_data)[0]
                price_lakhs = round(float(pred), 2)
                price_rupees = price_lakhs * 100000
                price_per_sqft = price_rupees / sqft

            st.markdown(
                f"""
                <div class="result-card">
                    <h2>Estimated Price for {bhk} BHK in {location}</h2>
                    <h1>₹ {price_rupees:,.0f}</h1>
                    <p style="margin-top:0.5rem; opacity:0.85;">
                        ({price_lakhs:.2f} Lakhs · {sqft} sq.ft · {bath} bath)
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.balloons()

            st.session_state.history.append(
                {
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "location": location,
                    "sqft": sqft,
                    "bath": bath,
                    "bhk": bhk,
                    "price_lakhs": price_lakhs,
                    "price_rupees": price_rupees,
                }
            )

            m1, m2, m3 = st.columns(3)
            m1.metric("Price / sq.ft", f"₹ {price_per_sqft:,.0f}")
            m2.metric("Total Area", f"{sqft:,} sq.ft")
            m3.metric("Configuration", f"{bhk} BHK · {bath} Bath")

            st.caption(
                "⚠️ This is an estimate based on historical data and may not reflect "
                "current market conditions."
            )

            # ---- Similar listings ----
            if SQFT_COL:
                similar = df[
                    (df["location"] == location)
                    & (df["bhk"] == bhk)
                    & (df[SQFT_COL].between(sqft * 0.8, sqft * 1.2))
                ]
                with st.expander(f"🏘️ Similar listings in {location} ({len(similar)} found)"):
                    if similar.empty:
                        st.write("No close matches found in the dataset for comparison.")
                    else:
                        show_cols = [
                            c for c in ["location", SQFT_COL, "bath", "bhk", PRICE_COL]
                            if c and c in similar.columns
                        ]
                        st.dataframe(similar[show_cols].reset_index(drop=True), width="stretch")

# ================= INSIGHTS TAB =================
with tab_insights:
    st.subheader("Market Overview")

    if PRICE_COL:
        top_locations = (
            df.groupby("location")[PRICE_COL].mean().sort_values(ascending=False).head(10)
        )
        st.markdown("**Top 10 locations by average price**")
        st.bar_chart(top_locations)

        colA, colB = st.columns(2)
        with colA:
            st.markdown("**Price distribution**")
            price_bins = pd.cut(df[PRICE_COL], bins=10)
            price_dist = price_bins.value_counts().sort_index()
            price_dist.index = price_dist.index.astype(str)
            st.bar_chart(price_dist)
        with colB:
            st.markdown("**BHK distribution**")
            st.bar_chart(df["bhk"].value_counts().sort_index())

        if SQFT_COL:
            st.markdown("**Sq.ft vs Price**")
            scatter_df = df[[SQFT_COL, PRICE_COL]].sample(min(500, len(df)), random_state=42)
            st.scatter_chart(scatter_df, x=SQFT_COL, y=PRICE_COL)
        else:
            st.info("No area/sqft column detected, so the sq.ft-vs-price chart is skipped.")
    else:
        st.info("No price column detected in the dataset to build market charts from.")

    # ---- Feature importance ----
    if hasattr(model, "feature_importances_"):
        st.markdown("**What drives the prediction most?**")
        feature_names = ["Area (sq.ft)", "Bathrooms", "BHK", "Location"]
        importances = model.feature_importances_
        if len(importances) == len(feature_names):
            imp_series = pd.Series(importances, index=feature_names).sort_values(ascending=False)
            st.bar_chart(imp_series)
            st.caption(
                "Relative importance the model assigns to each input feature when predicting price."
            )
        else:
            st.caption(
                f"Model has {len(importances)} features, which doesn't match the expected 4 — skipping this chart."
            )

# ================= COMPARE TAB =================
with tab_compare:
    st.subheader("Compare Two Properties Side by Side")
    colL, colR = st.columns(2)

    with colL:
        st.markdown("**Property A**")
        loc_a = st.selectbox("Location (A)", options=sorted(df["location"].unique()), key="loc_a")
        sqft_a = st.number_input("Area sq.ft (A)", min_value=300, step=50, value=1000, key="sqft_a")
        bath_a = st.selectbox("Bathrooms (A)", options=sorted(df["bath"].unique()), key="bath_a")
        bhk_a = st.selectbox("BHK (A)", options=sorted(df["bhk"].unique()), key="bhk_a")

    with colR:
        st.markdown("**Property B**")
        loc_b = st.selectbox("Location (B)", options=sorted(df["location"].unique()), key="loc_b")
        sqft_b = st.number_input("Area sq.ft (B)", min_value=300, step=50, value=1200, key="sqft_b")
        bath_b = st.selectbox("Bathrooms (B)", options=sorted(df["bath"].unique()), key="bath_b")
        bhk_b = st.selectbox("BHK (B)", options=sorted(df["bhk"].unique()), key="bhk_b")

    if st.button("⚖️ Compare Prices", type="primary"):
        price_a = predict_price(loc_a, sqft_a, bath_a, bhk_a)
        price_b = predict_price(loc_b, sqft_b, bath_b, bhk_b)

        if price_a is None or price_b is None:
            st.error("Couldn't encode one of the selected locations. Please try different ones.")
        else:
            rupees_a, rupees_b = price_a * 100000, price_b * 100000
            diff = rupees_b - rupees_a
            pct = (diff / rupees_a * 100) if rupees_a else 0

            r1, r2, r3 = st.columns(3)
            r1.metric(f"{loc_a} ({bhk_a} BHK)", f"₹ {rupees_a:,.0f}")
            r2.metric(f"{loc_b} ({bhk_b} BHK)", f"₹ {rupees_b:,.0f}", delta=f"₹ {diff:,.0f}")
            r3.metric("% Difference", f"{pct:+.1f}%")

            compare_df = pd.DataFrame(
                {"Property": [f"A: {loc_a}", f"B: {loc_b}"], "Price (₹)": [rupees_a, rupees_b]}
            ).set_index("Property")
            st.bar_chart(compare_df)

# ================= HISTORY TAB =================
with tab_history:
    st.subheader("Your Prediction History (this session)")

    if not st.session_state.history:
        st.info("No predictions yet — head to the Predict tab and try one out!")
    else:
        hist_df = pd.DataFrame(st.session_state.history).iloc[::-1].reset_index(drop=True)
        st.dataframe(hist_df, width="stretch")

        csv_bytes = hist_df.to_csv(index=False).encode("utf-8")
        col1, col2 = st.columns([1, 1])
        with col1:
            st.download_button(
                "⬇️ Download history as CSV",
                data=csv_bytes,
                file_name="prediction_history.csv",
                mime="text/csv",
            )
        with col2:
            if st.button("🗑️ Clear history"):
                st.session_state.history = []
                st.rerun()