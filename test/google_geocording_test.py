
import requests
import urllib.parse
import json
from dotenv import load_dotenv
import os
load_dotenv()

API_KEY = os.getenv('GEOCORDING_API')


def get_coordinates_from_address(address):
    """
    住所から緯度経度を取得する関数
    
    Parameters:
        address (str): 住所
        
    Returns:
        dict: 緯度経度情報を含む辞書
    """
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
            raise Exception(f"Geocoding API エラー: {data['status']}")
        
        # 最初の結果から緯度経度を抽出
        location = data['results'][0]['geometry']['location']
        formatted_address = data['results'][0]['formatted_address']
        
        return {
            'latitude': location['lat'],
            'longitude': location['lng'],
            'formatted_address': formatted_address,
            'original_address': address
        }
    
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        raise

def main(address):
    """
    使用例
    """
    try:
        
        print(f"「{address}」の緯度経度を取得しています...")
        
        coordinates = get_coordinates_from_address(address)
        
        print('結果:')
        print(f"入力住所: {coordinates['original_address']}")
        print(f"フォーマット済み住所: {coordinates['formatted_address']}")
        print(f"緯度: {coordinates['latitude']}")
        print(f"経度: {coordinates['longitude']}")
        print(f"Google Maps URL: https://www.google.com/maps?q={coordinates['latitude']},{coordinates['longitude']}")
    
    except Exception as e:
        print(f"処理中にエラーが発生しました: {e}")

if __name__ == "__main__":
    address = '浅間ハイランドパーク'
    main(address)
