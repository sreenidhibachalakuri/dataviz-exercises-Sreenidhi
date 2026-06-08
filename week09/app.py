import streamlit as st
import pandas as pd
import plotly.express as px

# Set page config for a wide dashboard layout
st.set_page_config(page_title="World Happiness", page_icon="🌍", layout="wide")

# Load data - safely handle paths
try:
    df = pd.read_csv('../data/world_happiness_2023.csv')
except FileNotFoundError:
    try:
        df = pd.read_csv('data/world_happiness_2023.csv')
    except FileNotFoundError:
        df = pd.read_csv('world_happiness_2023.csv')

df.columns = ['Country','Region','Score','GDP','Social_Support',
              'Life_Expectancy','Freedom','Generosity','Corruption']

# Calculate global average for the diverging chart midpoint
global_avg_score = df['Score'].mean()

# ── SIDEBAR FILTERS ──────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Filters")
    regions = ['All'] + sorted(df['Region'].unique().tolist())
    selected_region = st.selectbox("Region", regions)
    top_n = st.slider("Show top N", 5, 25, 15)

# Filter dataset based on selection
filtered = df if selected_region == 'All' else df[df['Region'] == selected_region]

# ── DASHBOARD HEADER & KPIs ──────────────────────────────────────────────────
st.title("🌍 World Happiness Dashboard")
st.caption("Source: World Happiness Report 2023 | Kaggle")

col1, col2, col3 = st.columns(3)
col1.metric("Countries", len(filtered))
col2.metric("Avg Score", f"{filtered['Score'].mean():.2f}",
            f"{filtered['Score'].mean() - global_avg_score:+.2f} vs global")
col3.metric("Happiest", filtered.nlargest(1,'Score')['Country'].values[0])

st.divider()

# ── ROW 1: TWO-COLUMN LAYOUT ─────────────────────────────────────────────────
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Rankings")
    top = filtered.nlargest(top_n, 'Score').sort_values('Score')
    
    fig1 = px.bar(top, x='Score', y='Country', orientation='h',
                  color_discrete_sequence=['#2E75B6'],
                  labels={'Score':'Score (0–10)','Country':''})
    
    fig1.update_layout(plot_bgcolor='white', paper_bgcolor='white',
                       xaxis=dict(range=[0,8.5]), font=dict(family='Arial',size=12),
                       margin=dict(l=10,r=10,t=5,b=10))
    fig1.update_traces(marker_line_width=0)
    st.plotly_chart(fig1, use_container_width=True)

with col_right:
    st.subheader("Score vs GDP")
    fig2 = px.scatter(filtered, x='GDP', y='Score', hover_name='Country',
                      color_discrete_sequence=['#E63946'])
    fig2.update_layout(plot_bgcolor='white', paper_bgcolor='white',
                       font=dict(family='Arial',size=12),
                       margin=dict(l=10,r=10,t=5,b=10))
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

# ── ROW 2: STEP 6 - DIVERGING COLOUR SCALE CHART ─────────────────────────────
st.subheader("Deviation from Global Average Happiness Score")
st.markdown(
    f"This chart highlights countries that score above or below the **Global Average Score ({global_avg_score:.2f})**."
)

# Create a calculated column for variance from the mean
filtered_dev = filtered.copy()
filtered_dev['Deviation'] = filtered_dev['Score'] - global_avg_score

# Sort to show highest and lowest clear variations
dev_subset = filtered_dev.dropna(subset=['Deviation']).sort_values('Deviation')

# Take top 10 and bottom 10 for better readability if "All" is selected
if selected_region == 'All':
    dev_subset = pd.concat([dev_subset.head(10), dev_subset.tail(10)]).drop_duplicates().sort_values('Deviation')

# Diverging Color Scale: 'RdBu' (Red for negative deviation, Blue for positive)
fig3 = px.bar(dev_subset, x='Deviation', y='Country', orientation='h',
              color='Deviation',
              color_continuous_scale='RdBu', 
              color_continuous_midpoint=0.0,
              labels={'Deviation': 'Distance from Global Avg', 'Country': ''})

fig3.update_layout(
    plot_bgcolor='white', 
    paper_bgcolor='white',
    font=dict(family='Arial', size=12),
    coloraxis_showscale=True,
    margin=dict(l=10, r=10, t=30, b=10)
)

# Labeling the midpoint (0 deviation line) with an annotation
fig3.add_vline(x=0, line_dash="dash", line_color="gray", line_width=1.5)
fig3.add_annotation(
    x=0, y=1.05, yref="paper",
    text=f"Global Avg ({global_avg_score:.2f})",
    showarrow=False,
    font=dict(color="gray", size=11, style="italic")
)

st.plotly_chart(fig3, use_container_width=True)

st.divider()
st.caption("Built with Streamlit + Plotly")