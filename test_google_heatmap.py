import math
import requests
import os
from config import *
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv('GOOGLE_AQI_API_KEY')


def latlon_to_tile_coords(lat, lon, zoom):
    """
    緯度・経度からタイル座標を計算
    """
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    x_tile = int((lon + 180.0) / 360.0 * n)
    y_tile = int((1.0 - math.log(math.tan(lat_rad) + 1 / math.cos(lat_rad)) / math.pi) / 2.0 * n)
    return x_tile, y_tile

def fetch_heatmap_tile(lat, lon, zoom, map_type, api_key, output_filename):
    """
    指定した地点のヒートマップタイルを取得して保存
    """
    x_tile, y_tile = latlon_to_tile_coords(lat, lon, zoom)
    url = f"https://airquality.googleapis.com/v1/mapTypes/{map_type}/heatmapTiles/{zoom}/{x_tile}/{y_tile}?key={api_key}"

    response = requests.get(url)
    if response.status_code == 200:
        with open(output_filename, 'wb') as f:
            f.write(response.content)
        print(f"ヒートマップタイルを保存しました: {output_filename}")
    else:
        print(f"エラーが発生しました。ステータスコード: {response.status_code}")
        print(response.text)

# 使用例
if __name__ == "__main__":
    # 指定する緯度・経度（例: 台湾・内埔）
    latitude = SUMA_LAT_LON[0]
    longitude = SUMA_LAT_LON[1]
    zoom = 6  # ズームレベル（0〜16）
    map_type = "US_AQI"  # ヒートマップの種類（例: US_AQI, PM25, O3 など）
 
    output_filename = "heatmap_tile.png"

    fetch_heatmap_tile(latitude, longitude, zoom, map_type, API_KEY, output_filename)
