import os
import json
import time
import requests
from datetime import datetime
from config import logger, DATA_DIR
from dotenv import load_dotenv
load_dotenv()

# WAQI API エンドポイントとトークン
# 注意: 実際のAPIキーに置き換える必要があります
API_BASE_URL = "https://api.waqi.info"
API_TOKEN = os.getenv('AQI_API_TOKEN')  # api_token.pyからインポート

def fetch_aqi_data():
    """神戸市須磨区の大気質データをAPIから取得する関数"""
    try:
        # 須磨区の地点を取得するためのURL
        # 地点名で検索する方法
        url = f"{API_BASE_URL}/feed/japan/kobeshisumaku/suma/?token={API_TOKEN}"
        
        # 代替方法: 地理座標を使用（須磨区の緯度経度を使用）
        # Suma Ward, Kobe coordinates: 約 34.65, 135.13
        # url = f"{API_BASE_URL}/feed/geo:34.65;135.13/?token={API_TOKEN}"
        
        logger.info(f"APIリクエストを送信: {url.replace(API_TOKEN, '***')}")
        
        # APIリクエストを送信
        response = requests.get(url)
        
        # レスポンスをチェック
        if response.status_code != 200:
            logger.error(f"APIエラー: ステータスコード {response.status_code}")
            return None
            
        # JSONデータを解析
        data = response.json()
        
        # レスポンスの詳細をデバッグ用に保存
        debug_dir = os.path.join(DATA_DIR, "debug")
        os.makedirs(debug_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        with open(os.path.join(debug_dir, f"api_response_{timestamp}.json"), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # データの有効性をチェック
        if data["status"] != "ok" or "data" not in data:
            logger.error(f"無効なAPIレスポンス: {data['status']}")
            # エラーの場合はその情報を詳細に記録
            if "data" in data and isinstance(data["data"], str):
                logger.error(f"エラーメッセージ: {data['data']}")
            return None
            
        # 結果を整形
        result = parse_api_response(data)
        
        return result
        
    except Exception as e:
        logger.error(f"APIリクエスト中にエラーが発生しました: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None
     
def parse_api_response(api_data):
    """APIレスポンスからデータを抽出・整形する関数"""
    try:
        data = api_data["data"]
        
        # 基本データを取得
        result = {
            "地点": "神戸市 須磨区",  # 固定値として設定
            "取得時間": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "AQI値": data.get("aqi", ""),
            "大気質ステータス": get_aqi_status(data.get("aqi", 0)),
            "主要汚染物質": data.get("dominentpol", ""),
        }
        
        # 時間情報を更新
        if "time" in data and "iso" in data["time"]:
            try:
                api_time = datetime.fromisoformat(data["time"]["iso"].replace("Z", "+00:00"))
                result["取得時間"] = api_time.strftime('%Y-%m-%d %H:%M:%S')
            except:
                pass
        
        # 汚染物質データと気象データの取得
        if "iaqi" in data:
            iaqi = data["iaqi"]
            
            # 大気汚染物質
            result.update({
                "PM2.5": str(iaqi.get("pm25", {}).get("v", "")),
                "PM10": str(iaqi.get("pm10", {}).get("v", "")),
                "O3": str(iaqi.get("o3", {}).get("v", "")),
                "NO2": str(iaqi.get("no2", {}).get("v", "")),
            })
            
            # 気象データ（CSVのカラム名に合わせて変更）
            result.update({
                "温度": str(iaqi.get("t", {}).get("v", "0.0")),
                "湿度": str(iaqi.get("h", {}).get("v", "0.0")),
                "気圧": str(iaqi.get("p", {}).get("v", "0.0")),
                "風速": str(iaqi.get("w", {}).get("v", "0.0")),
                "降水量": str(iaqi.get("r", {}).get("v", "0.0")),
            })
        
        # 予報データがある場合は保存
        if "forecast" in data and data["forecast"]:
            save_forecast_data(data["forecast"])
        
        return result
        
    except Exception as e:
        logger.error(f"APIレスポンスの解析中にエラーが発生しました: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None
    
def get_aqi_status(aqi_value):
    """AQI値に基づいて大気質ステータスを返す関数"""
    try:
        aqi = int(aqi_value)
        if aqi <= 50:
            return "良好"
        elif aqi <= 100:
            return "普通"
        elif aqi <= 150:
            return "敏感な人に有害"
        elif aqi <= 200:
            return "健康に良くない"
        elif aqi <= 300:
            return "非常に健康に良くない"
        else:
            return "危険"
    except (ValueError, TypeError):
        return ""
    
def save_forecast_data(forecast_data):
    """予報データを別のJSONファイルに保存する関数"""
    try:
        forecast_dir = os.path.join(DATA_DIR, "forecast")
        os.makedirs(forecast_dir, exist_ok=True)
        
        # ファイル名に日付を含める
        date_str = datetime.now().strftime('%Y%m%d')
        filename = os.path.join(forecast_dir, f"forecast_{date_str}.json")
        
        # JSONに保存
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(forecast_data, f, ensure_ascii=False, indent=2)
            
        logger.info(f"予報データをJSONファイルに保存しました: {filename}")
    except Exception as e:
        logger.error(f"予報データの保存中にエラーが発生しました: {e}")
    
if __name__ == "__main__":
    """スクリプトを直接実行した場合のテスト実行"""
    print("神戸市須磨区のAQIデータをAPI経由で取得します...")
    result = fetch_aqi_data()
    if result:
        print("\nAPI取得結果:")
        for key, value in result.items():
            print(f"{key}: {value}")

    else:
        print("データを取得できませんでした。APIキーが設定されているか確認してください。")