"""
Streamlit Dashboard — Weather Analytics
=========================================
An interactive web dashboard to visualize weather data from the ETL pipeline.

Run with:  streamlit run dashboard.py

Features:
- Real-time data display from MySQL
- Interactive charts (temperature, humidity, wind)
- City comparison tools
- Pipeline status overview

This was my first time building a Streamlit app — it's surprisingly
easy to create professional-looking dashboards with just Python.
No HTML/CSS/JS needed!
"""

import os
import sys

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import CLEANED_DATA_PATH, ANALYSIS_OUTPUT_PATH

# ========================
# Page Configuration
# ========================
st.set_page_config(
    page_title="Weather ETL Dashboard",
    page_icon="🌦️",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data(ttl=60)
def load_data() -> pd.DataFrame | None:
    """Loads cleaned weather data from CSV."""
    if not os.path.exists(CLEANED_DATA_PATH):
        return None
    df = pd.read_csv(CLEANED_DATA_PATH)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    return df


def render_header():
    """Renders the dashboard header."""
    st.markdown(
        """
        <div style="text-align:center; padding: 1rem 0;">
            <h1>🌦️ Weather ETL Pipeline Dashboard</h1>
            <p style="color: #888; font-size: 1.1rem;">
                Real-time analytics from the Automated ETL Pipeline
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_cards(df: pd.DataFrame):
    """Renders KPI metric cards at the top."""
    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("🌍 Cities Tracked", len(df["city"].unique()))
    col2.metric("🌡️ Avg Temp", f"{df['temperature'].mean():.1f} °C")
    col3.metric("💧 Avg Humidity", f"{df['humidity'].mean():.1f}%")
    col4.metric(
        "🔥 Hottest",
        f"{df.loc[df['temperature'].idxmax(), 'city']}",
        f"{df['temperature'].max():.1f} °C",
    )
    col5.metric(
        "❄️ Coldest",
        f"{df.loc[df['temperature'].idxmin(), 'city']}",
        f"{df['temperature'].min():.1f} °C",
    )


def render_temperature_chart(df: pd.DataFrame):
    """Bar chart of temperatures by city."""
    fig = px.bar(
        df.sort_values("temperature", ascending=False),
        x="city",
        y="temperature",
        color="temperature",
        color_continuous_scale="RdYlBu_r",
        title="🌡️ Temperature by City (°C)",
        labels={"temperature": "Temp (°C)", "city": "City"},
    )
    fig.update_layout(template="plotly_dark", height=400)
    st.plotly_chart(fig, use_container_width=True)


def render_humidity_chart(df: pd.DataFrame):
    """Bar chart of humidity by city."""
    fig = px.bar(
        df.sort_values("humidity", ascending=False),
        x="city",
        y="humidity",
        color="humidity",
        color_continuous_scale="Blues",
        title="💧 Humidity by City (%)",
        labels={"humidity": "Humidity (%)", "city": "City"},
    )
    fig.update_layout(template="plotly_dark", height=400)
    st.plotly_chart(fig, use_container_width=True)


def render_weather_pie(df: pd.DataFrame):
    """Pie chart of weather conditions."""
    condition_counts = df["weather_condition"].value_counts().reset_index()
    condition_counts.columns = ["condition", "count"]

    fig = px.pie(
        condition_counts,
        values="count",
        names="condition",
        title="☁️ Weather Conditions Distribution",
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig.update_layout(template="plotly_dark", height=400)
    st.plotly_chart(fig, use_container_width=True)


def render_scatter(df: pd.DataFrame):
    """Scatter plot: temperature vs humidity."""
    fig = px.scatter(
        df,
        x="temperature",
        y="humidity",
        color="weather_condition",
        size="wind_speed",
        hover_name="city",
        title="🔬 Temperature vs Humidity (bubble size = wind speed)",
        labels={"temperature": "Temp (°C)", "humidity": "Humidity (%)"},
    )
    fig.update_layout(template="plotly_dark", height=450)
    st.plotly_chart(fig, use_container_width=True)


def render_wind_chart(df: pd.DataFrame):
    """Horizontal bar chart of wind speeds."""
    fig = px.bar(
        df.sort_values("wind_speed", ascending=True),
        x="wind_speed",
        y="city",
        orientation="h",
        color="wind_speed",
        color_continuous_scale="Viridis",
        title="💨 Wind Speed by City (m/s)",
    )
    fig.update_layout(template="plotly_dark", height=400)
    st.plotly_chart(fig, use_container_width=True)


def render_data_table(df: pd.DataFrame):
    """Renders the raw data table."""
    st.subheader("📊 Complete Data Table")
    st.dataframe(
        df.style.background_gradient(subset=["temperature"], cmap="RdYlBu_r")
        .background_gradient(subset=["humidity"], cmap="Blues")
        .format({"temperature": "{:.1f}", "humidity": "{:.0f}", "wind_speed": "{:.1f}"}),
        use_container_width=True,
        height=400,
    )


def main():
    """Main dashboard layout."""
    render_header()

    df = load_data()

    if df is None or df.empty:
        st.warning(
            "⚠️ No data found. Run the ETL pipeline first:\n\n"
            "```\npython main.py\n```"
        )
        return

    # Sidebar filters
    st.sidebar.header("🔧 Filters")
    selected_cities = st.sidebar.multiselect(
        "Select Cities", df["city"].unique(), default=df["city"].unique()
    )
    filtered_df = df[df["city"].isin(selected_cities)]

    if filtered_df.empty:
        st.info("No data for selected filters.")
        return

    # KPI Cards
    render_kpi_cards(filtered_df)
    st.divider()

    # Charts Row 1
    col1, col2 = st.columns(2)
    with col1:
        render_temperature_chart(filtered_df)
    with col2:
        render_humidity_chart(filtered_df)

    # Charts Row 2
    col3, col4 = st.columns(2)
    with col3:
        render_weather_pie(filtered_df)
    with col4:
        render_wind_chart(filtered_df)

    # Scatter Plot (full width)
    render_scatter(filtered_df)

    # Data Table
    render_data_table(filtered_df)

    # Analysis Report
    if os.path.exists(ANALYSIS_OUTPUT_PATH):
        with st.expander("📄 SQL Analysis Report"):
            with open(ANALYSIS_OUTPUT_PATH, "r", encoding="utf-8") as f:
                st.code(f.read(), language="text")

    # Footer
    st.divider()
    st.caption("Built with ❤️ | Automated ETL Pipeline using Python & MySQL")


if __name__ == "__main__":
    main()
