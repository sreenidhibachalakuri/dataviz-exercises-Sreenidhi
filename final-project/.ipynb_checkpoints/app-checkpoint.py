import os
import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Page Configuration
st.set_page_config(
    page_title="US Flight Performance & Delay Analysis",
    page_icon="🛫",
    layout="wide"
)

# 2. Robust Data Loading & Feature Engineering
@st.cache_data
def load_data():
    # Dynamically resolve file path relative to app.py directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Try loading from main folder first, fallback to data/ subfolder
    file_path = os.path.join(base_dir, 'T_ONTIME_REPORTING.csv')
    if not os.path.exists(file_path):
        file_path = os.path.join(base_dir, 'data', 'T_ONTIME_REPORTING.csv')
        if not os.path.exists(file_path):
            file_path = os.path.join(base_dir, 'T_ONTIME_REPORTING_2.csv')

    df = pd.read_csv(file_path)

    # Clean numeric columns for smooth calculation
    numeric_cols = ['ARR_DELAY', 'DEP_DELAY', 'DISTANCE', 'CARRIER_DELAY', 
                    'WEATHER_DELAY', 'NAS_DELAY', 'SECURITY_DELAY', 'LATE_AIRCRAFT_DELAY']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Feature Engineering: Distance Tiers
    df['DISTANCE_TIER'] = pd.cut(
        df['DISTANCE'],
        bins=[0, 500, 1500, 10000],
        labels=['Short-haul (<500 mi)', 'Medium-haul (500-1500 mi)', 'Long-haul (>1500 mi)']
    )

    # Carrier Name Mapping
    carrier_map = {
        'AA': 'American Airlines', 'DL': 'Delta Air Lines', 'UA': 'United Airlines',
        'WN': 'Southwest Airlines', 'AS': 'Alaska Airlines', 'B6': 'JetBlue',
        'NK': 'Spirit Airlines', 'F9': 'Frontier Airlines', 'G4': 'Allegiant Air',
        'HA': 'Hawaiian Airlines', 'MQ': 'Envoy Air', 'OH': 'PSA Airlines',
        'OO': 'SkyWest Airlines', 'YX': 'Republic Airways'
    }
    df['CARRIER_NAME'] = df['OP_UNIQUE_CARRIER'].map(carrier_map).fillna(df['OP_UNIQUE_CARRIER'])
    
    return df

# Load Dataset
df = load_data()

# 3. Title & Header Block
st.title("🛫 US Flight Delays & Reliability Analytics")
st.markdown("An interactive overview of flight performance, root delay causes, and carrier reliability.")

# 4. Interactive Sidebar Filters
st.sidebar.header("Filter Options")
all_carriers = sorted(df['CARRIER_NAME'].dropna().unique().tolist())
selected_carriers = st.sidebar.multiselect(
    "Select Airlines:",
    options=all_carriers,
    default=all_carriers[:4]
)

# Filter Dataset based on user selection
if selected_carriers:
    filtered_df = df[df['CARRIER_NAME'].isin(selected_carriers)]
else:
    filtered_df = df.copy()

# 5. Top Metric Cards (KPI Summary)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Flights Analyzed", f"{len(filtered_df):,}")
col2.metric("Mean Arrival Delay", f"{filtered_df['ARR_DELAY'].mean():.1f} mins")
col3.metric("Cancellation Rate", f"{(filtered_df['CANCELLED'].mean() * 100):.2f}%")
col4.metric("Mean Flight Distance", f"{filtered_df['DISTANCE'].mean():.0f} miles")

st.markdown("---")

# 6. Multi-Tab Visualizations
tab1, tab2, tab3 = st.tabs(["📊 Carrier Delays", "⚠️ Root Cause Breakdown", "🗺️ Distance & Route Performance"])

# Tab 1: Departure Time Block vs Arrival Delays
with tab1:
    st.subheader("Carrier Delay Performance Across Time Blocks")
    q1_data = filtered_df.groupby(['DEP_TIME_BLK', 'CARRIER_NAME'])['ARR_DELAY'].mean().reset_index()
    q1_data = q1_data.sort_values('DEP_TIME_BLK')

    fig1 = px.line(
        q1_data,
        x='DEP_TIME_BLK',
        y='ARR_DELAY',
        color='CARRIER_NAME',
        title="<b>Late Evening Flights Suffer Peak Delays Across All Carriers</b>",
        labels={'DEP_TIME_BLK': 'Departure Time Block', 'ARR_DELAY': 'Mean Arrival Delay (Mins)'},
        color_discrete_sequence=px.colors.qualitative.Safe
    )
    fig1.update_layout(template='plotly_white', xaxis_tickangle=-45)
    st.plotly_chart(fig1, use_container_width=True)

# Tab 2: Delay Root Causes
with tab2:
    st.subheader("Delay Drivers by Distance Tier")
    delay_cols = ['CARRIER_DELAY', 'WEATHER_DELAY', 'NAS_DELAY', 'SECURITY_DELAY', 'LATE_AIRCRAFT_DELAY']
    
    # Calculate average minutes per delay category
    q2_data = filtered_df.groupby('DISTANCE_TIER', observed=False)[delay_cols].mean().reset_index()
    q2_melted = q2_data.melt(id_vars='DISTANCE_TIER', var_name='Delay Cause', value_name='Minutes')

    fig2 = px.bar(
        q2_melted,
        x='DISTANCE_TIER',
        y='Minutes',
        color='Delay Cause',
        barmode='group',
        title="<b>Late Aircraft & Carrier Issues Dominate Long-Haul Delays</b>",
        labels={'DISTANCE_TIER': 'Distance Tier', 'Minutes': 'Average Delay (Mins)'},
        color_discrete_sequence=px.colors.qualitative.Safe
    )
    fig2.update_layout(template='plotly_white')
    st.plotly_chart(fig2, use_container_width=True)

# Tab 3: Distance vs Delay Scatter
with tab3:
    st.subheader("Flight Distance Distribution vs Arrival Delay")
    sample_size = min(3000, len(filtered_df))
    sampled_df = filtered_df.dropna(subset=['ARR_DELAY', 'DISTANCE']).sample(sample_size, random_state=42)

    fig3 = px.scatter(
        sampled_df,
        x='DISTANCE',
        y='ARR_DELAY',
        color='CARRIER_NAME',
        opacity=0.6,
        title="<b>Arrival Delay vs Flight Distance (Sampled Points)</b>",
        labels={'DISTANCE': 'Distance (Miles)', 'ARR_DELAY': 'Arrival Delay (Mins)'},
        color_discrete_sequence=px.colors.qualitative.Safe
    )
    fig3.update_layout(template='plotly_white')
    st.plotly_chart(fig3, use_container_width=True)

