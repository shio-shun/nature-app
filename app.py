import pandas as pd
import folium
from folium.plugins import MarkerCluster
from math import radians, cos, sin, sqrt, atan2
import json
import streamlit as st
from streamlit_folium import st_folium

st.set_page_config(layout="wide")
st.markdown("""
    <style>
        .title-style {
            font-size: 1.8em;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .folium-map {
            height: 100%;
            width: 100%;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='title-style'>🌿 福岡自然観光スポットルートナビ</div>", unsafe_allow_html=True)

# スポットデータ
... # スポットデータ定義部（省略：変更なし）

# データフレーム生成
df = pd.DataFrame(data, columns=["スポット名", "緯度", "経度", "公式サイト", "所要時間"])

# 距離計算関数
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    phi1, phi2 = radians(lat1), radians(lat2)
    d_phi = radians(lat2 - lat1)
    d_lambda = radians(lon2 - lon1)
    a = sin(d_phi / 2)**2 + cos(phi1) * cos(phi2) * sin(d_lambda / 2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))

# 起点マルチ選択対応
st.markdown("<br>", unsafe_allow_html=True)
origins = st.multiselect("📍 起点にしたい観光スポットを1つ以上選んでください", df["スポット名"].tolist(), default=[df["スポット名"].tolist()[0]])

# 地図作成
m = folium.Map(location=[df["緯度"].mean(), df["経度"].mean()], zoom_start=12, control_scale=True)
all_routes = []
favorites = []

# 起点ごとに処理
colors = ["red", "blue", "green", "purple", "orange"]
for idx, origin in enumerate(origins):
    origin_row = df[df["スポット名"] == origin].iloc[0]
    origin_lat, origin_lon = origin_row["緯度"], origin_row["経度"]

    # 起点マーカー
    folium.Marker(
        location=[origin_lat, origin_lon],
        popup=folium.Popup(f"<b>{origin}</b><br><a href='{origin_row['公式サイト']}' target='_blank'>公式サイト</a><br>所要時間: {origin_row['所要時間']}", max_width=250),
        tooltip=f"起点：{origin}",
        icon=folium.Icon(color=colors[idx % len(colors)], icon='info-sign')
    ).add_to(m)

    # 距離計算とおすすめスポット
    df["距離_km"] = df.apply(
        lambda row: haversine(origin_lat, origin_lon, row["緯度"], row["経度"])
        if row["スポット名"] != origin else float("inf"),
        axis=1
    )
    recommended = df.sort_values("距離_km").head(3)

    # 描画＋ルート線
    route = [(origin_lat, origin_lon)]
    for _, row in recommended.iterrows():
        folium.Marker(
            location=[row["緯度"], row["経度"]],
            popup=folium.Popup(f"<b>{row['スポット名']}</b><br><a href='{row['公式サイト']}' target='_blank'>公式サイト</a><br>所要時間: {row['所要時間']}", max_width=250),
            tooltip=row["スポット名"],
            icon=folium.Icon(color=colors[idx % len(colors)], icon='cloud')
        ).add_to(m)
        route.append((row["緯度"], row["経度"]))
        favorites.append(row["スポット名"])
    folium.PolyLine(route, color=colors[idx % len(colors)], weight=4, opacity=0.7).add_to(m)
    all_routes.append((origin, recommended))

# 地図表示
st_data = st_folium(m, width=900, height=500)

# 表形式表示（複数起点ごとに）
st.subheader("📌 起点ごとのおすすめスポット一覧")
for origin, table in all_routes:
    st.markdown(f"**▶ {origin} から近いスポット**")
    st.table(table[["スポット名", "距離_km", "所要時間"]].reset_index(drop=True))

# お気に入り保存
with open("favorite_spots.json", "w", encoding="utf-8") as f:
    json.dump(favorites, f, ensure_ascii=False, indent=2)
st.success("⭐ お気に入りスポットを保存しました → favorite_spots.json")
