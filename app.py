import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap, FastMarkerCluster
from streamlit_folium import st_folium

# -------------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------------
st.set_page_config(
    page_title="UK Road Collision Explorer",
    layout="wide"
)

st.title("UK Road Collision Explorer")

st.markdown(
    """
    This interactive application explores **UK road collision data (STATS19)**.  
    Use the filters to examine how **location, environment, and time** relate to
    collision frequency and severity across the UK.
    """
)

# -------------------------------------------------------
# LOAD DATA
# -------------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("collision.csv")
    df = df.dropna(subset=["latitude", "longitude"]).reset_index(drop=True)

    if df["collision_severity"].dtype.kind in ("i", "u"):
        df["collision_severity"] = df["collision_severity"].map(
            {1: "Fatal", 2: "Serious", 3: "Slight"}
        )

    for c in [
        "collision_severity",
        "weather_conditions",
        "light_conditions",
        "road_type",
    ]:
        df[c] = df[c].astype(str).str.strip()

    df["collision_year"] = pd.to_numeric(df["collision_year"], errors="coerce")

    return df


df = load_data()

# -------------------------------------------------------
# DEFAULT FILTERS
# -------------------------------------------------------
DEFAULTS = {
    "map_mode": "Cluster",
    "severity": sorted(df["collision_severity"].unique()),
    "years": (int(df["collision_year"].min()), int(df["collision_year"].max())),
    "weather": sorted(df["weather_conditions"].unique()),
    "light": sorted(df["light_conditions"].unique()),
    "road": sorted(df["road_type"].unique()),
}

# -------------------------------------------------------
# SESSION STATE INIT
# -------------------------------------------------------
for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value

if "map_object" not in st.session_state:
    st.session_state.map_object = None

if "df_filtered" not in st.session_state:
    st.session_state.df_filtered = None

if "initialized" not in st.session_state:
    st.session_state.initialized = False

# -------------------------------------------------------
# SIDEBAR FILTER FORM
# -------------------------------------------------------
with st.sidebar:
    st.header("Filters")

    with st.form("filter_form"):
        map_mode = st.radio("Map Mode", ["Cluster", "Heatmap"], index=0)

        severity = st.multiselect(
            "Severity",
            sorted(df["collision_severity"].unique()),
            default=st.session_state.severity,
        )

        years = st.slider(
            "Year Range",
            DEFAULTS["years"][0],
            DEFAULTS["years"][1],
            st.session_state.years,
        )

        weather = st.multiselect(
            "Weather",
            sorted(df["weather_conditions"].unique()),
            default=st.session_state.weather,
        )

        light = st.multiselect(
            "Lighting",
            sorted(df["light_conditions"].unique()),
            default=st.session_state.light,
        )

        road = st.multiselect(
            "Road Type",
            sorted(df["road_type"].unique()),
            default=st.session_state.road,
        )

        col1, col2 = st.columns(2)
        apply_btn = col1.form_submit_button("Apply filters")
        reset_btn = col2.form_submit_button("Reset filters")

# -------------------------------------------------------
# FILTER FUNCTION
# -------------------------------------------------------
@st.cache_data
def apply_filters(df, sev, years, weather, light, road):
    return df[
        (df["collision_severity"].isin(sev))
        & (df["collision_year"].between(years[0], years[1]))
        & (df["weather_conditions"].isin(weather))
        & (df["light_conditions"].isin(light))
        & (df["road_type"].isin(road))
    ].copy()

# -------------------------------------------------------
# RESET FILTERS
# -------------------------------------------------------
if reset_btn:
    for key, value in DEFAULTS.items():
        st.session_state[key] = value
    st.session_state.map_object = None
    st.session_state.initialized = False
    st.rerun()

# -------------------------------------------------------
# APPLY FILTERS (BUTTON OR FIRST LOAD)
# -------------------------------------------------------
if apply_btn or not st.session_state.initialized:

    st.session_state.map_mode = map_mode
    st.session_state.severity = severity
    st.session_state.years = years
    st.session_state.weather = weather
    st.session_state.light = light
    st.session_state.road = road

    with st.spinner("Updating map..."):
        df_filtered = apply_filters(
            df,
            st.session_state.severity,
            st.session_state.years,
            st.session_state.weather,
            st.session_state.light,
            st.session_state.road,
        )

        if df_filtered.empty:
            st.warning("No data available for the selected filters.")
            st.stop()

        st.session_state.df_filtered = df_filtered

        coords = df_filtered[["latitude", "longitude"]].values.tolist()

        min_lat, max_lat = df_filtered["latitude"].min(), df_filtered["latitude"].max()
        min_lon, max_lon = df_filtered["longitude"].min(), df_filtered["longitude"].max()

        m = folium.Map(
            location=[(min_lat + max_lat) / 2, (min_lon + max_lon) / 2],
            zoom_start=6,
            tiles="cartodb positron",
        )

        if st.session_state.map_mode == "Cluster":
            FastMarkerCluster(coords).add_to(m)
        else:
            HeatMap(coords, radius=8, blur=12).add_to(m)

        st.session_state.map_object = m
        st.session_state.initialized = True

# -------------------------------------------------------
# SUMMARY
# -------------------------------------------------------
if st.session_state.df_filtered is not None:
    df_filtered = st.session_state.df_filtered

    total = len(df_filtered)
    fatal = (df_filtered["collision_severity"] == "Fatal").sum()

    st.markdown(
        f"""
        **Summary for selected filters**

        - Total collisions: **{total:,}**
        - Fatal collisions: **{fatal:,}**
        - Fatality rate: **{(fatal / total) * 100:.2f}%**
        """
    )

# -------------------------------------------------------
# MAP RENDER (ONCE)
# -------------------------------------------------------
if st.session_state.map_object is not None:
    st_folium(
        st.session_state.map_object,
        width=1300,
        height=900,
        returned_objects=[]
    )


# -------------------------------------------------------
# EDA SECTION
# -------------------------------------------------------
st.divider()
st.header("Exploratory Analysis")

st.markdown(
    """
    These visual summaries show how **fatality risk changes under different conditions**.
    """
)

tab_time, tab_weather, tab_surface, tab_light, tab_speed = st.tabs(
    ["Time", "Weather", "Road Surface", "Lighting", "Speed"]
)

with tab_time:
    st.subheader("Trends Over Time")
    st.markdown(
        """
        Collision volumes fluctuate over time, with clear COVID-related disruptions.  
        Fatal collisions, however, remain relatively stable year-on-year.
        """
    )
    st.image("assets/time_trend.png", width=1100)

with tab_weather:
    st.subheader("Weather Conditions & Fatality Risk")
    st.markdown(
        """
        Most collisions occur in fine weather, but adverse conditions
        disproportionately increase fatality risk.  
        Fog, mist, and high winds show markedly higher fatality rates.
        """
    )
    st.image("assets/weather_fatality.png", width=900)

with tab_surface:
    st.subheader("Road Surface Conditions & Fatality Rates")
    st.markdown(
        """
        Dry road surfaces account for the majority of collisions.  
        Flooded roads, while rare, are associated with substantially higher fatality rates.
        """
    )
    st.image("assets/surface_fatality.png", width=900)

with tab_light:
    st.subheader("Lighting Conditions & Fatality Rates")
    st.markdown(
        """
        Daylight collisions dominate in volume, but dark conditions — especially
        without street lighting — are far more severe.  
        Reduced visibility plays a critical role in fatal outcomes.
        """
    )
    st.image("assets/light_fatality.png", width=900)

with tab_speed:
    st.subheader("Speed Limits & Fatality Rates")
    st.markdown(
        """
        Lower-speed urban roads generate most collisions, while higher-speed
        roads exhibit sharply increased fatality rates.  
        Severity rises rapidly beyond typical urban speed limits.
        """
    )
    st.image("assets/speed_fatality.png", width=750)


