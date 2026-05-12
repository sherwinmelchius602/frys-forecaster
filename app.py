# app.py
# ─────────────────────────────────────────────────────────────────────────────
# Fry's Burgers — Daily Forecast Dashboard
# Run with:  streamlit run app.py
# ─────────────────────────────────────────────────────────────────────────────

import streamlit as st
import plotly.graph_objects as go
import datetime
import pandas as pd

# Import all business logic from model.py
from model import (
    compare_all_cities,
    get_price_curve,
    find_optimal_price,
    get_breakeven_demand,
    FOOD_COST,
    FIXED_COST,
    CITIES,
)

# ── PAGE SETUP ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Fry's Burgers Forecaster",
    page_icon="🍔",
    layout="wide",
)

CITY_COLORS = {
    "Hamilton": "#378ADD",
    "London":   "#1D9E75",
    "Waterloo": "#BA7517",
    "Toronto":  "#D4537E",
}


# ── SECTION 1: HEADER ────────────────────────────────────────────────────────
st.title("🍔 Fry's Burgers — Daily Forecaster")
st.caption("Linear Regression model · 365 days of training data · Capstone Project, Mahindra University")
st.divider()


# ── SECTION 2: INPUT CONDITIONS ──────────────────────────────────────────────
st.subheader("Today's conditions")

col1, col2, col3, col4 = st.columns(4)

with col1:
    temperature = st.slider("Temperature (°C)", min_value=-15, max_value=35, value=10)

with col2:
    rain_pct    = st.slider("Rain probability (%)", min_value=0, max_value=100, value=30)
    precip_prob = rain_pct / 100   # convert percentage to decimal for the model

with col3:
    festival = 1 if st.radio("Festival today?", ["No", "Yes"], horizontal=True) == "Yes" else 0

with col4:
    weekday  = 1 if st.radio("Day type", ["Weekday", "Weekend"], horizontal=True) == "Weekday" else 0

st.divider()


# ── COMPUTE RESULTS ───────────────────────────────────────────────────────────
# One call to model.py — does all the heavy lifting
results    = compare_all_cities(temperature, precip_prob, festival, weekday)
best_city  = results.loc[results["Recommended"], "City"].values[0]


# ── SECTION 3: CITY RECOMMENDATION CARDS ─────────────────────────────────────
st.subheader("City recommendation")

cols = st.columns(4)
for i, row in results.iterrows():
    with cols[i]:
        if row["Recommended"]:
            st.success(f"**⭐ {row['City']}** — Recommended")
        else:
            st.info(f"**{row['City']}**")
        st.metric("Optimal price",   f"${row['Optimal Price']:.2f}")
        st.metric("Est. demand",     f"{row['Pred. Demand']} burgers")
        st.metric("Expected profit", f"${row['Profit']:.0f}")

st.divider()


# ── SECTION 4: CHARTS ────────────────────────────────────────────────────────
st.subheader("Profit analysis")

chart_left, chart_right = st.columns(2)

# --- Bar chart: profit per city at optimal price ---
with chart_left:
    st.caption("Expected profit per city (at optimal price)")

    bar_colors = []

# --- Bar chart: profit per city at optimal price ---
with chart_left:
    st.caption("Expected profit per city (at optimal price)")

    bar_colors = []

    for c in results["City"]:
        is_recommended = results.loc[
            results["City"] == c,
            "Recommended"
        ].values[0]

        if is_recommended:
            bar_colors.append(CITY_COLORS[c])
        else:
            bar_colors.append("rgba(180,180,180,0.5)")

    fig_bar = go.Figure(go.Bar(
        x=results["City"],
        y=results["Profit"],
        marker_color=bar_colors,
        text=results["Profit"].apply(lambda v: f"${v:.0f}"),
        textposition="outside",
    ))

    fig_bar.update_layout(
        height=280,
        showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=20, b=10, l=10, r=10),
        yaxis=dict(
            tickprefix="$",
            gridcolor="rgba(128,128,128,0.1)"
        ),
    )

    st.plotly_chart(fig_bar, use_container_width=True)

# --- Line chart: price vs profit for best city ---
with chart_right:
    st.caption(f"Price sensitivity — {best_city} (recommended city)")

    curve_df = get_price_curve(best_city, temperature, precip_prob, festival, weekday)

    fig_line = go.Figure(go.Scatter(
        x=curve_df["Price"],
        y=curve_df["Profit"],
        mode="lines+markers",
        line=dict(color=CITY_COLORS[best_city], width=2),
        marker=dict(size=5),
    ))
    fig_line.update_layout(
        height=280, showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=20, b=10, l=10, r=10),
        xaxis=dict(tickprefix="$"),
        yaxis=dict(tickprefix="$", gridcolor="rgba(128,128,128,0.1)"),
    )
    st.plotly_chart(fig_line, use_container_width=True)

st.divider()


# ── SECTION 5: BREAKEVEN TABLE ────────────────────────────────────────────────
st.subheader("Breakeven analysis")
st.caption("Minimum burgers Sally must sell to cover all costs (food + travel + parking)")

# Build a clean display table
be_table = results[[
    "City", "Optimal Price", "Breakeven", "Pred. Demand", "Safety Margin", "Viability"
]].copy()

be_table["Optimal Price"]  = be_table["Optimal Price"].apply(lambda v: f"${v:.2f}")
be_table["Breakeven"]      = be_table["Breakeven"].apply(lambda v: f"{v} burgers")
be_table["Pred. Demand"]   = be_table["Pred. Demand"].apply(lambda v: f"{v} burgers")
be_table["Safety Margin"]  = be_table["Safety Margin"].apply(
    lambda v: f"+{v:.0f}" if v >= 0 else f"{v:.0f}"
)
be_table = be_table.rename(columns={
    "Optimal Price": "Price",
    "Breakeven":     "Break-even demand",
    "Pred. Demand":  "Model predicts",
    "Safety Margin": "Buffer",
})

st.dataframe(be_table, use_container_width=True, hide_index=True)
st.divider()


# ── SECTION 6: SCENARIO COMPARISON ───────────────────────────────────────────
st.subheader("Scenario comparison")
st.caption("Pick any two cities and compare them head-to-head")

sel_col1, _, sel_col2 = st.columns([2, 0.3, 2])

with sel_col1:
    city_a = st.selectbox("City A", CITIES, index=1)   # default: London
with sel_col2:
    city_b = st.selectbox("City B", [c for c in CITIES if c != city_a], index=2)

# Get optimal results for each selected city
opt_a = find_optimal_price(city_a, temperature, precip_prob, festival, weekday)
opt_b = find_optimal_price(city_b, temperature, precip_prob, festival, weekday)
be_a  = get_breakeven_demand(city_a, opt_a["price"])
be_b  = get_breakeven_demand(city_b, opt_b["price"])

# Build comparison rows
comparison = [
    ("Optimal price",    f"${opt_a['price']:.2f}",   f"${opt_b['price']:.2f}"),
    ("Predicted demand", f"{round(opt_a['qty'])} burgers",  f"{round(opt_b['qty'])} burgers"),
    ("Expected revenue", f"${opt_a['revenue']:.0f}", f"${opt_b['revenue']:.0f}"),
    ("Expected profit",  f"${opt_a['profit']:.0f}",  f"${opt_b['profit']:.0f}"),
    ("Break-even demand",f"{be_a:.1f} burgers",      f"{be_b:.1f} burgers"),
    ("Food cost/burger", f"${FOOD_COST[city_a]:.2f}",f"${FOOD_COST[city_b]:.2f}"),
    ("Fixed cost/day",   f"${FIXED_COST[city_a]:.2f}",f"${FIXED_COST[city_b]:.2f}"),
]

card_a, card_b = st.columns(2)
for col, city, opt, rows_side in [(card_a, city_a, opt_a, 0), (card_b, city_b, opt_b, 1)]:
    with col:
        st.markdown(f"**{city}**")
        for label, val_a, val_b in comparison:
            val = val_a if rows_side == 0 else val_b
            st.markdown(
                f"<div style='display:flex;justify-content:space-between;"
                f"padding:5px 0;border-bottom:1px solid rgba(128,128,128,.15)'>"
                f"<span style='color:gray;font-size:13px'>{label}</span>"
                f"<span style='font-size:13px'><b>{val}</b></span></div>",
                unsafe_allow_html=True,
            )

# Head-to-head profit curves
st.caption("Head-to-head profit curve across all price points")

curve_a = get_price_curve(city_a, temperature, precip_prob, festival, weekday)
curve_b = get_price_curve(city_b, temperature, precip_prob, festival, weekday)

fig_cmp = go.Figure()
fig_cmp.add_trace(go.Scatter(
    x=curve_a["Price"], y=curve_a["Profit"], name=city_a,
    line=dict(color=CITY_COLORS[city_a], width=2),
    mode="lines+markers", marker=dict(size=4),
))
fig_cmp.add_trace(go.Scatter(
    x=curve_b["Price"], y=curve_b["Profit"], name=city_b,
    line=dict(color=CITY_COLORS[city_b], width=2, dash="dash"),
    mode="lines+markers", marker=dict(size=4),
))
fig_cmp.update_layout(
    height=260, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    margin=dict(t=10, b=10, l=10, r=10),
    xaxis=dict(tickprefix="$"),
    yaxis=dict(tickprefix="$", gridcolor="rgba(128,128,128,0.1)"),
    legend=dict(orientation="h", y=1.1),
)
st.plotly_chart(fig_cmp, use_container_width=True)
st.divider()


# ── SECTION 7: MODEL HEALTH ───────────────────────────────────────────────────
st.subheader("Model health")

m1, m2, m3, m4 = st.columns(4)
m1.metric("R² — training",     "0.43")
m2.metric("R² — cross-val",    "0.30", delta="-0.13", delta_color="inverse")
m3.metric("Avg error",         "±18 burgers")
m4.metric("Within 30 burgers", "89%")

with st.expander("Per-city accuracy and notes"):
    st.dataframe(pd.DataFrame([
        {"City": "Hamilton", "R²": 0.342, "Quality": "Moderate"},
        {"City": "London",   "R²": 0.098, "Quality": "Weak — use directionally"},
        {"City": "Waterloo", "R²": 0.480, "Quality": "Good"},
        {"City": "Toronto",  "R²": 0.262, "Quality": "Moderate"},
    ]), hide_index=True, use_container_width=True)

    st.info(
        "**London R² = 0.10** — The model explains London's day-to-day demand poorly. "
        "However, London still dominates profit rankings due to structural cost advantages: "
        "lowest food cost ($2.05/burger) and free parking.\n\n"
        "**CV R² drop (0.43 → 0.30)** — Mild overfitting. A second year of data would help."
    )

st.divider()


# ── SECTION 8: EXPORT ────────────────────────────────────────────────────────
st.subheader("Export")

# Build CSV content
csv_lines = [
    "Fry's Burgers — Forecast Export",
    f"Date,{datetime.date.today()}",
    f"Temperature,{temperature}°C",
    f"Rain probability,{rain_pct}%",
    f"Festival,{'Yes' if festival else 'No'}",
    f"Day type,{'Weekday' if weekday else 'Weekend'}",
    "",
]
export_df = results[[
    "City", "Optimal Price", "Pred. Demand", "Revenue",
    "Profit", "Breakeven", "Safety Margin", "Viability",
    "Food Cost", "Fixed Cost",
]]
csv_content = "\n".join(csv_lines) + export_df.to_csv(index=False)

st.download_button(
    label="⬇️  Download forecast as CSV",
    data=csv_content,
    file_name=f"frys_forecast_{datetime.date.today()}.csv",
    mime="text/csv",
)
