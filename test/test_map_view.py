# 必要なライブラリをインポート
import folium
import pandas as pd
from folium.plugins import MarkerCluster, Search
from folium import LayerControl
from config import IMAGE_WEB_URL_DIR
import os
# CSVファイルを読み込む
data_dir = os.path.join(IMAGE_WEB_URL_DIR, "livecam_links_with_lat_lon.csv")
df = pd.read_csv(data_dir, encoding='utf-8')

# データの欠損値を確認し、緯度・経度が有効なレコードのみを対象とする
df = df.dropna(subset=['latitude', 'longitude'])

# 地図の中心点を計算（全ポイントの平均）
center_lat = df['latitude'].mean()
center_lon = df['longitude'].mean()

# 地図オブジェクトを作成
m = folium.Map(location=[center_lat, center_lon], zoom_start=6)

# 地域ごとにレイヤーを作成
region_layers = {}
for region in df['region'].unique():
    # 地域ごとのマーカークラスターを作成
    region_layers[region] = MarkerCluster(name=f"{region}地域", overlay=True)
    region_layers[region].add_to(m)

# 色の辞書を作成
region_colors = {
    '北海道': 'pink',
    '東北': 'blue',
    '関東': 'purple',
    '中部': 'orange',
    '近畿': 'red',
    '中国': 'darkblue',
    '四国': 'green',
    '九州': 'cadetblue',
    '沖縄': 'orange'
}

# アイコンの辞書を作成
region_icons = {
    '北海道': 'snowflake-o',
    '東北': 'leaf',
    '関東': 'building',
    '中部': 'mountain',
    '近畿': 'university',
    '中国': 'pagelines',
    '四国': 'ship',
    '九州': 'sun-o',
    '沖縄': 'umbrella-beach'
}

# 各ポイントをそれぞれの地域レイヤーに追加
for idx, row in df.iterrows():
    region = row['region']
    
    # 対応する色を取得（デフォルトはグレー）
    color = region_colors.get(region, 'gray')
    icon_name = region_icons.get(region, 'info-sign')
    
    # ポップアップにエリア名、地域名、リンクを含める
    popup_html = f"""
    <div style="width: 200px">
        <h4>{row['area']}</h4>
        <p>地域: {row['region']} / {row['division']}</p>
        <p><a href="{row['area_url']}" target="_blank">詳細を見る</a></p>
    </div>
    """
    
    # マーカーを作成してレイヤーに追加
    folium.Marker(
        location=[row['latitude'], row['longitude']],
        popup=folium.Popup(popup_html, max_width=300),
        tooltip=row['area'],
        icon=folium.Icon(color=color, icon=icon_name, prefix='fa')
    ).add_to(region_layers[region])

# レイヤーコントロールを追加
LayerControl().add_to(m)

# 検索機能を追加（エリア名で検索可能に）
search = Search(
    layer=list(region_layers.values())[0],  # 最初のレイヤーを検索対象にする
    geom_type='Point',
    placeholder='エリアを検索...',
    search_label='area',
    search_zoom=15,
    position='topright'
).add_to(m)

# 凡例を追加
legend_html = '''
<div style="position: fixed; 
            bottom: 50px; right: 50px; 
            border:2px solid grey; z-index:9999; 
            background-color:white;
            padding: 10px;
            font-size:14px;
            ">
<h4>地域の凡例</h4>
'''

# 地域ごとに凡例項目を追加
for region, color in region_colors.items():
    icon = region_icons.get(region, 'info-sign')
    legend_html += f'''
    <div style="display: flex; align-items: center; margin-bottom: 5px;">
        <i class="fa fa-{icon}" style="color:{color}; margin-right: 5px;"></i>
        <span>{region}</span>
    </div>
    '''

legend_html += '</div>'

# 凡例をHTMLオブジェクトとして地図に追加
m.get_root().html.add_child(folium.Element(legend_html))

# HTMLファイルとして保存
m.save('livecam_map_optimized.html')

print("最適化された地図が正常に生成され、'livecam_map_optimized.html'として保存されました。")