import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Eco-Loop Dashboard", layout="wide")
st.title("Eco-Loop Building Agents: Quantitative Savings Dashboard")

log_path = "simulation_log.csv"

if os.path.exists(log_path):
    df = pd.read_csv(log_path)
    
    st.header("Real-Time Simulation Metrics")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Energy (kWh)", f"{df['Energy_kWh'].sum():.2f}")
    col2.metric("Average PMV", f"{df['PMV'].mean():.2f}")
    col3.metric("Current Zone Temp", f"{df['ZoneTemp'].iloc[-1]:.2f} °C")
    
    st.subheader("Thermal Comfort (PMV)")
    fig_pmv = px.line(df, y="PMV", title="Predicted Mean Vote (PMV) over Time")
    fig_pmv.add_hline(y=0.5, line_dash="dash", line_color="red", annotation_text="Upper Limit")
    fig_pmv.add_hline(y=-0.5, line_dash="dash", line_color="blue", annotation_text="Lower Limit")
    st.plotly_chart(fig_pmv, use_container_width=True)
    
    st.subheader("HVAC Setpoints (Agent Control)")
    fig_sp = px.line(df, y=["HeatingSetPoint", "CoolingSetPoint"], title="Dynamic Setpoints Injected by LLM")
    st.plotly_chart(fig_sp, use_container_width=True)
else:
    st.warning("Simulation log not found. Please run the backend simulation first to generate data.")
