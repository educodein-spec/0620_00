import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium
from datetime import datetime

st.set_page_config(
    page_title="Global Earthquake Visualizer",
    layout="wide"
)

st.title("🌎 Global Earthquake Visualizer")
st.markdown("USGS 실시간 지진 데이터 기반")

# 연도 선택
current_year = datetime.now().year

year = st.selectbox(
    "연도 선택",
    list(range(current_year, 1900, -1))
)

# 기간 생성
start_date = f"{year}-01-01"
end_date = f"{year}-12-31"

url = (
    "https://earthquake.usgs.gov/fdsnws/event/1/query"
    f"?format=geojson"
    f"&starttime={start_date}"
    f"&endtime={end_date}"
    "&minmagnitude=1"
    "&limit=20000"
)

@st.cache_data(ttl=3600)
def load_data(api_url):
    response = requests.get(api_url, timeout=60)
    response.raise_for_status()

    data = response.json()

    records = []

    for feature in data["features"]:
        props = feature["properties"]
        coords = feature["geometry"]["coordinates"]

        records.append({
            "time": pd.to_datetime(props["time"], unit="ms"),
            "place": props["place"],
            "magnitude": props["mag"],
            "longitude": coords[0],
            "latitude": coords[1],
            "depth": coords[2]
        })

    return pd.DataFrame(records)

with st.spinner("데이터 불러오는 중..."):
    df = load_data(url)

if len(df) == 0:
    st.warning("데이터가 없습니다.")
    st.stop()

# 통계
col1, col2, col3 = st.columns(3)

col1.metric("지진 수", f"{len(df):,}")
col2.metric("최대 규모", round(df["magnitude"].max(), 2))
col3.metric("평균 규모", round(df["magnitude"].mean(), 2))

# 규모 필터
min_mag, max_mag = st.slider(
    "규모(Magnitude) 범위",
    float(df["magnitude"].min()),
    float(df["magnitude"].max()),
    (
        float(df["magnitude"].min()),
        float(df["magnitude"].max())
    )
)

filtered = df[
    (df["magnitude"] >= min_mag) &
    (df["magnitude"] <= max_mag)
]

st.write(f"표시 중: {len(filtered):,}건")

# 지도 생성
m = folium.Map(
    location=[20, 0],
    zoom_start=2,
    tiles="CartoDB positron"
)

for _, row in filtered.iterrows():

    magnitude = row["magnitude"]

    if pd.isna(magnitude):
        continue

    if magnitude >= 7:
        color = "red"
    elif magnitude >= 5:
        color = "orange"
    else:
        color = "blue"

    folium.CircleMarker(
        location=[row["latitude"], row["longitude"]],
        radius=max(2, magnitude * 2),
        popup=f"""
        <b>Location:</b> {row['place']}<br>
        <b>Magnitude:</b> {magnitude}<br>
        <b>Depth:</b> {row['depth']} km<br>
        <b>Time:</b> {row['time']}
        """,
        color=color,
        fill=True,
        fill_opacity=0.7
    ).add_to(m)

st_folium(
    m,
    width=1400,
    height=700
)

st.subheader("데이터")

st.dataframe(
    filtered.sort_values(
        "magnitude",
        ascending=False
    ),
    use_container_width=True
)
