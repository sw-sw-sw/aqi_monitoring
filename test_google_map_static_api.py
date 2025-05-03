import requests, os
from config import *
import urllib.parse

from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv('GOOGLE_AQI_API_KEY')
# Google Maps Static API を使用する

latitude = SUMA_LAT_LON[0]
longitude = SUMA_LAT_LON[1]
zoom = 6
size = "1024x1024"  # ヒートマップタイルに合わせる
maptype = "roadmap"
style = urllib.parse.quote("element:labels|visibility:off")
url = f"https://maps.googleapis.com/maps/api/staticmap?center={latitude},{longitude}&zoom={zoom}&size={size}&maptype={maptype}&key={API_KEY}"

response = requests.get(url)
if response.status_code == 200:
    with open('basemap_tile.png', 'wb') as f:
        f.write(response.content)
    print("ベースマップ画像を保存しました。")
else:
    print("地図画像の取得に失敗しました。")
