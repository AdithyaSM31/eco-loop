import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

st.set_page_config(page_title="Eco-Loop Dashboard", layout="wide")
st.title("Eco-Loop Building Agents: Quantitative Savings Dashboard")

baseline_path = "baseline_log.csv"
agent_path = "agent_log.csv"

baseline_exists = os.path.exists(baseline_path)
agent_exists = os.path.exists(agent_path)

if baseline_exists and agent_exists:
    df_base = pd.read_csv(baseline_path)
    df_agent = pd.read_csv(agent_path)
    
    st.header("Comparative Simulation Metrics (Baseline vs AI-Driven)")
    
    base_energy = df_base['Energy_kWh'].sum()
    agent_energy = df_agent['Energy_kWh'].sum()
    savings_pct = ((base_energy - agent_energy) / base_energy) * 100 if base_energy > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Baseline Total Energy (kWh)", f"{base_energy:.2f}")
    col2.metric("AI Agent Total Energy (kWh)", f"{agent_energy:.2f}", delta=f"-{savings_pct:.1f}%", delta_color="inverse")
    col3.metric("AI Average PMV", f"{df_agent['PMV'].mean():.2f}")
    
    st.subheader("Cumulative Energy Consumption")
    df_base['Cumulative_Energy_Base'] = df_base['Energy_kWh'].cumsum()
    df_agent['Cumulative_Energy_Agent'] = df_agent['Energy_kWh'].cumsum()
    
    fig_energy = go.Figure()
    fig_energy.add_trace(go.Scatter(y=df_base['Cumulative_Energy_Base'], mode='lines', name='Baseline (Static Schedules)'))
    fig_energy.add_trace(go.Scatter(y=df_agent['Cumulative_Energy_Agent'], mode='lines', name='AI Agent (Dynamic Control)'))
    fig_energy.update_layout(title="Cumulative Energy (kWh)", xaxis_title="Timestep", yaxis_title="kWh")
    st.plotly_chart(fig_energy, use_container_width=True)
    
    st.subheader("Thermal Comfort (PMV)")
    fig_pmv = go.Figure()
    fig_pmv.add_trace(go.Scatter(y=df_base['PMV'], mode='lines', name='Baseline PMV', opacity=0.5))
    fig_pmv.add_trace(go.Scatter(y=df_agent['PMV'], mode='lines', name='AI Agent PMV'))
    fig_pmv.add_hline(y=0.5, line_dash="dash", line_color="red", annotation_text="Upper Comfort Limit")
    fig_pmv.add_hline(y=-0.5, line_dash="dash", line_color="blue", annotation_text="Lower Comfort Limit")
    fig_pmv.update_layout(title="Predicted Mean Vote (PMV) Comparison", xaxis_title="Timestep", yaxis_title="PMV")
    st.plotly_chart(fig_pmv, use_container_width=True)
    
    st.subheader("Dynamic Setpoints Injected by LLM")
    fig_sp = px.line(df_agent, y=["HeatingSetPoint", "CoolingSetPoint"], title="LLM Setpoints")
    st.plotly_chart(fig_sp, use_container_width=True)
    
elif baseline_exists:
    st.warning("Baseline simulation found, but Agent simulation is missing. Please run `python backend/simulation.py --agentic`.")
elif agent_exists:
    st.warning("Agent simulation found, but Baseline simulation is missing. Please run `python backend/simulation.py`.")
else:
    st.error("No simulation logs found. Run baseline and agentic simulations first.")
