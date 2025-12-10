import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap, FastMarkerCluster
from streamlit_folium import st_folium

st.set_page_config(page_title="Collision Map Explorer", layout="wide")
st.title("UK Road Collision Interactive Map")

# -------------------------------------------------------
# LOAD DATA
# -------------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("collision.csv")
    df = df.dropna(subset=["latitude", "longitude"]).reset_index(drop=True)

    # Make severity safe (string)
    if df["collision_severity"].dtype.kind in ("i", "u"):
        mapping = {1: "Fatal", 2: "Serious", 3: "Slight"}
        df["collision_severity"] = df["collision_severity"].astype(int).map(mapping)
    else:
        df["collision_severity"] = df["collision_severity"].astype(str).str.strip()

    df["weather_conditions"] = df["weather_conditions"].astype(str).str.strip()
    df["light_conditions"] = df["light_conditions"].astype(str).str.strip()
    df["road_type"] = df["road_type"].astype(str).str.strip()

    df["collision_year"] = pd.to_numeric(df["collision_year"], errors="coerce").astype("Int64")

    return df

df = load_data()

# -------------------------------------------------------
# SIDEBAR FILTERS
# -------------------------------------------------------
with st.sidebar:
    st.header("Filters")

    map_mode = st.radio("Map Mode", ["Cluster", "Heatmap"])

    severities = sorted(df["collision_severity"].unique().tolist())
    severity_filter = st.multiselect("Severity", severities, default=severities)

    year_min, year_max = int(df["collision_year"].min()), int(df["collision_year"].max())
    year_filter = st.slider("Year Range", year_min, year_max, (year_min, year_max))

    weather_options = sorted(df["weather_conditions"].unique())
    weather_filter = st.multiselect("Weather Conditions", weather_options, default=weather_options)

    light_options = sorted(df["light_conditions"].unique())
    light_filter = st.multiselect("Light Conditions", light_options, default=light_options)

    road_options = sorted(df["road_type"].unique())
    road_filter = st.multiselect("Road Type", road_options, default=road_options)

# -------------------------------------------------------
# APPLY FILTERS
# -------------------------------------------------------
@st.cache_data
def apply_filters(df, sev, years, weather, light, road):
    df2 = df[
        (df["collision_severity"].isin(sev)) &
        (df["collision_year"].between(years[0], years[1])) &
        (df["weather_conditions"].isin(weather)) &
        (df["light_conditions"].isin(light)) &
        (df["road_type"].isin(road))
    ]
    return df2.copy()

df_filtered = apply_filters(df, severity_filter, year_filter, weather_filter, light_filter, road_filter)

st.sidebar.write(f"Rows: {len(df_filtered):,}")

if df_filtered.empty:
    st.warning("No data for selected filters.")
    st.stop()

coords = df_filtered[["latitude", "longitude"]].values.tolist()

# -------------------------------------------------------
# SIGNATURE FOR CACHING
# -------------------------------------------------------
def signature(mode, sev, years, weather, light, road):
    return (
        mode,
        tuple(sev),
        years[0], years[1],
        tuple(weather),
        tuple(light),
        tuple(road)
    )

sig = signature(map_mode, severity_filter, year_filter, weather_filter, light_filter, road_filter)

if "last_sig" not in st.session_state:
    st.session_state.last_sig = None

# -------------------------------------------------------
# BUILD MAP ONLY WHEN NEEDED
# -------------------------------------------------------
if sig != st.session_state.last_sig:

    # compute center
    min_lat = df_filtered["latitude"].min()
    max_lat = df_filtered["latitude"].max()
    min_lon = df_filtered["longitude"].min()
    max_lon = df_filtered["longitude"].max()

    center_lat = (min_lat + max_lat) / 2
    center_lon = (min_lon + max_lon) / 2

    m = folium.Map(location=[center_lat, center_lon], zoom_start=6, tiles="cartodb positron")

    if map_mode == "Cluster":
        FastMarkerCluster(coords).add_to(m)
    else:
        HeatMap(coords, radius=8, blur=12).add_to(m)

    st.session_state.map_object = m
    st.session_state.last_sig = sig

# -------------------------------------------------------
# SHOW MAP without reruns
# -------------------------------------------------------
st.subheader(f"{map_mode} Map — {len(df_filtered):,} collisions")
st_folium(
    st.session_state.map_object,
    width=1300,
    height=900,
    returned_objects=[],   # <-- prevents tracking map events (NO reruns)
)

