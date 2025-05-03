# 必要なライブラリをインポート
import folium

# 東京駅の緯度経度
tokyo_station_lat = 35.6812
tokyo_station_lon = 139.7671

# 地図オブジェクトを作成（東京駅を中心に、ズームレベル15で表示）
m = folium.Map(location=[tokyo_station_lat, tokyo_station_lon], zoom_start=15)

# 東京駅の位置にマーカーを追加（ポップアップ情報付き）
folium.Marker(
    location=[tokyo_station_lat, tokyo_station_lon],
    popup='I am here',
    tooltip='東京駅',
    icon=folium.Icon(color='orange', icon='train', prefix='fa')
).add_to(m)

# HTMLファイルとして保存
m.save('test/tokyo_station_map.html')

# 実行結果を表示するには、以下をJupyterノートブックで実行するか、
# ブラウザでtokyo_station_map.htmlを開いてください
m