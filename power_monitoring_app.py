import streamlit as st
import pandas as pd
import time
import random
import matplotlib.pyplot as plt
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Power Monitoring Dashboard",
    page_icon="🔌",
    layout="wide"
)

# Initialize session state for energy rate
if 'energy_rate' not in st.session_state:
    st.session_state.energy_rate = 0.12  # Default rate in $/kWh

# Cached function for data storage
@st.cache_data(ttl=3600)
def get_stored_data():
    return {"Time": [], "Fridge": [], "Air Conditioner": [], "Smart Light": []}

# Initialize data
devices = ['Fridge', 'Air Conditioner', 'Smart Light']
data = get_stored_data()

# Function to simulate power usage
def simulate_power():
    return {device: round(random.uniform(50, 300), 2) for device in devices}

st.title("🔌 Real-Time Power Monitoring Dashboard")
st.markdown("""
    Monitor real-time power consumption of your smart devices and track energy costs.
""")

# Control panel
col1, col2, col3 = st.columns(3)
with col1:
    monitoring_duration = st.slider("Select duration (seconds)", 10, 60, 30)
with col2:
    st.session_state.energy_rate = st.number_input(
        "Electricity Rate ($/kWh)",
        min_value=0.01,
        max_value=1.0,
        value=st.session_state.energy_rate,
        step=0.01
    )
with col3:
    start_button = st.button("Start Monitoring")

# Function to calculate energy cost
def calculate_energy_cost(power_w, rate, hours=1):
    kwh = (power_w * hours) / 1000  # Convert W to kWh
    return kwh * rate

# Real-Time Power Monitoring
col1, col2 = st.columns([2, 1])
with col1:
    st.write("### Device Power Usage (W)")
    power_chart = st.empty()
with col2:
    st.write("### Real-Time Cost Estimates")
    cost_display = st.empty()

try:
    if start_button:
        start_time = time.time()
        while time.time() - start_time < monitoring_duration:
            current_time = time.strftime("%H:%M:%S", time.localtime())
            power_readings = simulate_power()
            
            # Maintain a rolling window of last 100 readings
            max_readings = 100
            if len(data["Time"]) >= max_readings:
                for key in data:
                    data[key] = data[key][-max_readings:]
            
            # Append new data
            data["Time"].append(current_time)
            for device, value in power_readings.items():
                data[device].append(value)
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            # Display live power data
            power_chart.line_chart(
                df.set_index("Time"),
                use_container_width=True,
                height=400
            )
            
            # Calculate and display real-time costs
            hourly_costs = {
                device: calculate_energy_cost(
                    df[device].mean(),
                    st.session_state.energy_rate
                ) for device in devices
            }
            
            cost_df = pd.DataFrame({
                'Device': devices,
                'Hourly Cost ($)': [round(hourly_costs[d], 3) for d in devices],
                'Daily Cost ($)': [round(hourly_costs[d] * 24, 2) for d in devices],
                'Monthly Cost ($)': [round(hourly_costs[d] * 24 * 30, 2) for d in devices]
            }).set_index('Device')
            
            cost_display.dataframe(cost_df)
            
            time.sleep(1)
        
        st.success("Monitoring Complete! 🎉")
        
        # Export functionality with cost data
        if not df.empty:
            export_df = df.copy()
            for device in devices:
                export_df[f'{device}_hourly_cost'] = calculate_energy_cost(
                    export_df[device],
                    st.session_state.energy_rate
                )
            
            csv = export_df.to_csv(index=False)
            st.download_button(
                label="Download Data as CSV",
                data=csv,
                file_name=f'power_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                mime='text/csv',
            )
        
        # Summary statistics with costs
        st.write("### Power Usage and Cost Summary")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write("#### Average Power Consumption")
            st.dataframe(df[devices].mean().round(2))
        with col2:
            st.write("#### Peak Power Usage")
            st.dataframe(df[devices].max().round(2))
        with col3:
            st.write("#### Projected Annual Costs")
            annual_costs = {
                device: calculate_energy_cost(
                    df[device].mean(),
                    st.session_state.energy_rate,
                    hours=24 * 365
                ) for device in devices
            }
            st.dataframe(pd.Series(annual_costs).round(2))
        
        # Enhanced visualization with cost trends
        st.write("### Power Usage Trends")
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 12))
        
        # Power usage plot
        for device in devices:
            ax1.plot(df["Time"], df[device], label=device, marker='o', markersize=4)
        ax1.set_xlabel("Time")
        ax1.set_ylabel("Power (W)")
        ax1.legend()
        ax1.grid(True, linestyle='--', alpha=0.7)
        ax1.tick_params(axis='x', rotation=45)
        ax1.set_title("Power Consumption Over Time")
        
        # Cost projection plot
        costs = pd.DataFrame({
            'Hourly': hourly_costs.values(),
            'Daily': [cost * 24 for cost in hourly_costs.values()],
            'Monthly': [cost * 24 * 30 for cost in hourly_costs.values()],
            'Annual': [cost * 24 * 365 for cost in hourly_costs.values()]
        }, index=devices)
        
        costs.plot(kind='bar', ax=ax2)
        ax2.set_ylabel("Cost ($)")
        ax2.set_title("Cost Projections by Time Period")
        ax2.grid(True, linestyle='--', alpha=0.7)
        
        plt.tight_layout()
        st.pyplot(fig)

except Exception as e:
    st.error(f"An error occurred: {str(e)}")
    st.info("Please refresh the page and try again.")