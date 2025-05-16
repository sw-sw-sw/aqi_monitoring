import requests
import json, os

from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv('GOOGLE_AQI_API_KEY')

# 取得したい地点の緯度・経度（須磨）
latlon = [34.644428177814845, 135.11131387124348]
latitude = latlon[0]
longitude = latlon[1]

# APIエンドポイント
url = f'https://airquality.googleapis.com/v1/currentConditions:lookup?key={API_KEY}'

# リクエストボディ
payload = {
    "location": {
        "latitude": latitude,
        "longitude": longitude
    },
    "universalAqi": True,
    "extraComputations": [
        "HEALTH_RECOMMENDATIONS",
        "DOMINANT_POLLUTANT_CONCENTRATION",
        "POLLUTANT_CONCENTRATION",
        "LOCAL_AQI",
        "POLLUTANT_ADDITIONAL_INFO"
    ],
    "languageCode": "ja"
}

# ヘッダー
headers = {
    "Content-Type": "application/json"
}

# APIリクエストを送信
response = requests.post(url, headers=headers, data=json.dumps(payload))

# レスポンスを処理
if response.status_code == 200:
    data = response.json()
    print("取得日時:", data.get("dateTime", "N/A"))
    print("地域コード:", data.get("regionCode", "N/A"))
    print("\n--- AQI インデックス ---")
    for index in data.get("indexes", []):
        print(f"コード: {index.get('code', 'N/A')}")
        print(f"表示名: {index.get('displayName', 'N/A')}")
        print(f"AQI値: {index.get('aqi', 'N/A')}")
        print(f"カテゴリ: {index.get('category', 'N/A')}")
        print(f"主要汚染物質: {index.get('dominantPollutant', 'N/A')}")
        print("-" * 30)
    print("\n--- 汚染物質の詳細 ---")
    for pollutant in data.get("pollutants", []):
        print(f"コード: {pollutant.get('code', 'N/A')}")
        print(f"表示名: {pollutant.get('displayName', 'N/A')}")
        print(f"濃度: {pollutant.get('concentration', {}).get('value', 'N/A')} {pollutant.get('concentration', {}).get('units', '')}")
        print("-" * 30)
    print("\n--- 健康に関する推奨事項 ---")
    health_recommendations = data.get("healthRecommendations", {})
    for group, recommendation in health_recommendations.items():
        print(f"{group}: {recommendation}")
else:
    print(f"エラーが発生しました。ステータスコード: {response.status_code}")
    print(response.text)
