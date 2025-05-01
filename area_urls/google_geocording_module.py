
import requests
import urllib.parse
import json
from dotenv import load_dotenv
import os
load_dotenv()

API_KEY = os.getenv('GEOCORDING_API')

def geocode(address):

    try:
        # 住所をURLエンコード
        encoded_address = urllib.parse.quote(address)
        
        # Google Maps Geocoding APIのエンドポイント
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_address}&key={API_KEY}"
        
        # APIリクエスト
        response = requests.get(url)
        data = response.json()
        
        # レスポンスのステータスを確認
        if data['status'] != 'OK':
            print(f"Geocoding API エラー: {data['status']}")
            return None
        
        # 最初の結果から緯度経度を抽出
        location = data['results'][0]['geometry']['location']
        return (location['lat'], location['lng'])
    
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return None

# 使用例
if __name__ == "__main__":

    # テスト住所
    test_address = '東京都渋谷区渋谷2-21-1'
    
    # ジオコーディング実行
    coordinates = geocode(test_address)
    
    if coordinates:
        lat, lng = coordinates
        print(f"住所: {test_address}")
        print(f"緯度: {lat}")
        print(f"経度: {lng}")
        print(f"Google Maps URL: https://www.google.com/maps?q={lat},{lng}")
    else:
        print("ジオコーディングに失敗しました")