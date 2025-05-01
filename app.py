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

# スポットデータ（元の20件フルデータ）
data = [
    ["大濠公園", 33.5833, 130.3833, "https://www.ohorikouen.jp/", "約1時間"],
    ["舞鶴公園", 33.5839, 130.3831, "https://www.midorimachi.jp/maiduru/", "約1時間"],
    ["福岡市植物園", 33.5708, 130.3894, "https://botanical-garden.city.fukuoka.lg.jp/", "約1.5時間"],
    ["能古島アイランドパーク", 33.6167, 130.2833, "https://nokonoshima.com/", "約2時間"],
    ["志賀島", 33.7000, 130.3833, "https://www.crossroadfukuoka.jp/spot/12747", "約2時間"],
    ["福岡タワー", 33.5950, 130.3519, "https://www.fukuokatower.co.jp/", "約1時間"],
    ["西公園", 33.5900, 130.3750, "https://www.midorimachi.jp/nishikouen/", "約1時間"],
    ["福岡市博物館", 33.5950, 130.3519, "https://museum.city.fukuoka.jp/", "約1.5時間"],
    ["シーサイドももち海浜公園", 33.5950, 130.3519, "https://www.momochi-seaside.com/", "約1.5時間"],
    ["野河内渓谷", 33.5833, 130.3333, "https://tripnote.jp/fukuoka-shi/place-nogouchi-keikoku", "約1.5時間"],
    ["油山自然観察の森", 33.5333, 130.3333, "https://www.city.fukuoka.lg.jp/jonanku/yusuiyama/", "約2時間"],
    ["海の中道海浜公園", 33.6833, 130.3833, "https://uminaka-park.jp/", "約3時間"],
    ["貝塚公園", 33.6161, 130.4431, "https://www.city.fukuoka.lg.jp/higashiku/seikatsukankyo/life/kaizuka-park.html", "約1時間"],
    ["鴻臚館跡展示館", 33.5839, 130.3831, "https://fukuokajyo.com/", "約1時間"],
    ["福岡城跡", 33.5835, 130.3835, "https://fukuokajyo.com/", "約1時間"],
    ["南公園展望台", 33.5700, 130.3890, "https://www.city.fukuoka.lg.jp/", "約1時間"],
    ["香椎花園跡地", 33.6658, 130.4433, "https://kashiikaen.com/", "約1.5時間"],
    ["三日月山", 33.6836, 130.4417, "https://yamaiko.com/fukuoka/mikadukiyama", "約2時間"],
    ["皿山公園", 33.5517, 130.3644, "https://www.city.fukuoka.lg.jp/sawaraku/shimin-center/saraya-park.html", "約1時間"],
    ["若杉山", 33.6400, 130.5400, "https://www.crossroadfukuoka.jp/spot/12534", "約2.5時間"]
]

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
