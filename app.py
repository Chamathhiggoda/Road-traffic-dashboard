import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import zipfile
import io

# Page settings
st.set_page_config(
    page_title="Road Traffic Fatality Dashboard",
    layout="wide"
)

st.title("Global Road Traffic Fatality Rates Dashboard")
st.write("Dataset: Road traffic deaths per 100,000 people - World Bank")

# Load data from World Bank
@st.cache_data
def load_data():
    url = "https://api.worldbank.org/v2/en/indicator/SH.STA.TRAF.P5?downloadformat=csv"

    response = requests.get(url)
    zip_file = zipfile.ZipFile(io.BytesIO(response.content))

    csv_file = [
        file for file in zip_file.namelist()
        if file.startswith("API_SH.STA.TRAF.P5") and file.endswith(".csv")
    ][0]

    df = pd.read_csv(zip_file.open(csv_file), skiprows=4)
    return df

df = load_data()

# Data cleaning
year_columns = [col for col in df.columns if col.isdigit()]

df_clean = df[["Country Name", "Country Code"] + year_columns]

df_long = df_clean.melt(
    id_vars=["Country Name", "Country Code"],
    value_vars=year_columns,
    var_name="Year",
    value_name="Fatality Rate"
)

df_long["Year"] = pd.to_numeric(df_long["Year"])
df_long["Fatality Rate"] = pd.to_numeric(df_long["Fatality Rate"], errors="coerce")

df_long = df_long.dropna()

# Remove non-country groups
remove_list = [
    "World", "High income", "Low income", "Middle income",
    "Low & middle income", "Upper middle income", "Lower middle income",
    "Europe & Central Asia", "East Asia & Pacific", "South Asia",
    "Sub-Saharan Africa", "Latin America & Caribbean",
    "Middle East & North Africa", "North America", "European Union"
]

df_long = df_long[~df_long["Country Name"].isin(remove_list)]

# Sidebar filters
st.sidebar.header("Filters")

countries = sorted(df_long["Country Name"].unique())
selected_country = st.sidebar.selectbox("Select Country", countries)

years = sorted(df_long["Year"].unique())
selected_year = st.sidebar.slider(
    "Select Year",
    min_value=int(min(years)),
    max_value=int(max(years)),
    value=int(max(years))
)

country_data = df_long[df_long["Country Name"] == selected_country]
year_data = df_long[df_long["Year"] == selected_year]

# KPI cards
st.subheader("Key Summary")

col1, col2, col3 = st.columns(3)

selected_value = country_data[country_data["Year"] == selected_year]["Fatality Rate"]

with col1:
    if not selected_value.empty:
        st.metric(
            label=f"{selected_country} Fatality Rate",
            value=round(selected_value.iloc[0], 2)
        )
    else:
        st.metric(label=f"{selected_country} Fatality Rate", value="No Data")

with col2:
    st.metric(
        label=f"Average Fatality Rate in {selected_year}",
        value=round(year_data["Fatality Rate"].mean(), 2)
    )

with col3:
    highest = year_data.sort_values("Fatality Rate", ascending=False).iloc[0]
    st.metric(
        label="Highest Country",
        value=f"{highest['Country Name']} ({round(highest['Fatality Rate'], 2)})"
    )

# Line chart
st.subheader(f"Trend Analysis: {selected_country}")

fig_line = px.line(
    country_data,
    x="Year",
    y="Fatality Rate",
    markers=True,
    title=f"Road Traffic Fatality Rate Trend in {selected_country}"
)

st.plotly_chart(fig_line, use_container_width=True)

# Map
st.subheader(f"Global Fatality Rates in {selected_year}")

fig_map = px.choropleth(
    year_data,
    locations="Country Code",
    color="Fatality Rate",
    hover_name="Country Name",
    color_continuous_scale="Reds",
    title=f"Road Traffic Fatality Rates per 100,000 People in {selected_year}"
)

st.plotly_chart(fig_map, use_container_width=True)

# Top 10 bar chart
st.subheader(f"Top 10 Countries with Highest Fatality Rates in {selected_year}")

top10 = year_data.sort_values("Fatality Rate", ascending=False).head(10)

fig_bar = px.bar(
    top10,
    x="Country Name",
    y="Fatality Rate",
    text="Fatality Rate",
    title=f"Top 10 Highest Road Traffic Fatality Rates in {selected_year}"
)

st.plotly_chart(fig_bar, use_container_width=True)

st.subheader("Key Insights")

avg_rate = round(year_data["Fatality Rate"].mean(), 2)
max_country = year_data.loc[year_data["Fatality Rate"].idxmax()]
min_country = year_data.loc[year_data["Fatality Rate"].idxmin()]

st.write(f"""
- The global average road traffic fatality rate in {selected_year} is **{avg_rate} deaths per 100,000 people**.
- The highest fatality rate is observed in **{max_country['Country Name']} ({round(max_country['Fatality Rate'],2)})**.
- The lowest fatality rate is observed in **{min_country['Country Name']} ({round(min_country['Fatality Rate'],2)})**.
- There is a noticeable variation between countries, indicating differences in road safety conditions, infrastructure, and policy effectiveness.
""")

# Data table
st.subheader("Dataset Preview")

st.write("Top records for the selected year:")

table_data = year_data.sort_values("Fatality Rate", ascending=False).head(20)

st.markdown(
    table_data.to_html(index=False),
    unsafe_allow_html=True
)