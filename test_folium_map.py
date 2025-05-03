import folium

m = folium.Map(
    location=[34.7, 135.5],  # 中心座標（例：大阪）
    zoom_start=6,
    tiles=None
)

folium.TileLayer(
    tiles='https://stamen-tiles.a.ssl.fastly.net/terrain-background/{z}/{x}/{y}.jpg',
    attr='Map tiles by Stamen Design, CC BY 3.0 — Map data © OpenStreetMap',
    name='Stamen Terrain Background',
    overlay=False,
    control=True
).add_to(m)

m.save('nolabel_map.html')
