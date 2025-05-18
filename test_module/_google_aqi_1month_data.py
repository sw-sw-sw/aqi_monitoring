import requests
import json
import os
import csv
import time
import signal
import sys
from datetime import datetime, timedelta
import pandas as pd
import shutil  # バックアップ用に追加
from config import *  # DATA_DIRを読み込むための設定ファイル

# 環境変数からAPIキーを取得
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv('GOOGLE_AQI_API_KEY')

# 取得したい地点の緯度・経度（例：神戸）
latlon = SUMA_LAT_LON
latitude = latlon[0]
longitude = latlon[1]

# 保存用ディレクトリとファイルパスの設定
save_dir = os.path.join(DATA_DIR, "o3_google_api_1month")
os.makedirs(save_dir, exist_ok=True)
file_path = os.path.join(save_dir, "o3_by_google_aqi_api.csv")  # ファイルパス変更

# グローバル変数
existing_data = []
new_data = []
existing_datetimes = set()

# CSVのヘッダーを定義（健康推奨メッセージを除外）
csv_headers = [
    "地点", "取得時間", "AQI値", "大気質ステータス", "主要汚染物質", 
    "PM2.5", "PM10", "O3", "NO2", "温度", "湿度", "気圧", "風速", "降水量"
]

# バックアップを作成する関数
def create_backup():
    if os.path.exists(file_path):
        backup_path = file_path.replace('.csv', '_bak.csv')
        try:
            shutil.copy2(file_path, backup_path)
            print(f"バックアップを作成しました: {backup_path}")
            return True
        except Exception as e:
            print(f"バックアップ作成中にエラーが発生しました: {str(e)}")
            return False
    return False

# データを保存する関数
def save_data():
    global existing_data, new_data
    
    # 新しく取得したデータと既存データを結合して保存
    combined_data = existing_data + new_data
    
    if combined_data:
        try:
            # データを日時でソート
            df_combined = pd.DataFrame(combined_data)
            df_combined['取得時間'] = pd.to_datetime(df_combined['取得時間'])
            df_combined = df_combined.sort_values('取得時間')
            
            # CSVに保存（インデックスなし）
            df_combined.to_csv(file_path, index=False, columns=csv_headers)
            
            print(f"\nデータの保存が完了しました。")
            print(f"既存データ: {len(existing_data)}件")
            print(f"新規データ: {len(new_data)}件")
            print(f"合計: {len(combined_data)}件のデータを {file_path} に保存しました。")
        except Exception as e:
            print(f"\nデータ保存中にエラーが発生しました: {str(e)}")
            # 緊急時のバックアップ保存を試みる
            try:
                backup_file = os.path.join(save_dir, f"backup_aqi_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
                pd.DataFrame(combined_data).to_csv(backup_file, index=False, columns=csv_headers)
                print(f"バックアップファイルを保存しました: {backup_file}")
            except:
                print("バックアップファイルの保存にも失敗しました。")
    else:
        print("\nデータが取得できませんでした。")

# シグナル処理関数
def signal_handler(sig, frame):
    print("\n\nプログラムが中断されました。取得済みデータを保存します...")
    save_data()
    sys.exit(0)

# シグナルハンドラーの登録
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# プログラム終了時の処理関数
def exit_program(message=""):
    print(message)
    save_data()
    sys.exit(0)

# 過去の大気汚染データを取得する関数
def fetch_historical_aqi_data(period=14):
    global existing_data, new_data, existing_datetimes
    
    # 現在の時刻から48時間前を終了時刻とする（APIの制限に対応）
    current_time = datetime.now() - timedelta(hours=48)
    # 過去の時刻（変更）
    start_time_base = current_time - timedelta(days=period)

    print(f"Google AQI APIの制限により、過去{period}日間のデータを取得します。")
    print(f"取得期間: {start_time_base.strftime('%Y-%m-%d %H:%M')} から {current_time.strftime('%Y-%m-%d %H:%M')}")
    
    # バックアップを作成
    create_backup()
    
    # 既に取得済みのデータの日時を確認
    if os.path.exists(file_path):
        try:
            # 既存のCSVファイルを読み込む
            df = pd.read_csv(file_path)
            # 取得済みの日時を記録
            existing_datetimes = set(df['取得時間'].tolist())
            # 既存データを保持
            existing_data = df.to_dict('records')
            print(f"既存のCSVファイルから{len(existing_datetimes)}件のデータを読み込みました。")
        except Exception as e:
            print(f"既存ファイルの読み込み中にエラーが発生しました: {str(e)}")
            print("新しいCSVファイルとして処理を続行します。")
    
    # history APIエンドポイント
    url = f'https://airquality.googleapis.com/v1/history:lookup?key={API_KEY}'
    
    # ヘッダー
    headers = {
        "Content-Type": "application/json"
    }
    
    # エラーカウンター（全体）
    total_error_count = 0

    print(f"過去{period}日間（{start_time_base.strftime('%Y-%m-%d %H:%M')}から{current_time.strftime('%Y-%m-%d %H:%M')}まで）の大気質データを取得中...")

    # 1日ごとにデータを取得する
    for day_offset in range(period):  
        # 各日の開始時刻と終了時刻を計算
        day_start = start_time_base + timedelta(days=day_offset)
        day_end = day_start + timedelta(days=1)
        
        # 最後の日は現在時刻までに制限
        if day_end > current_time:
            day_end = current_time
        
        # 開始時刻と終了時刻をISOフォーマットに変換
        day_start_iso = day_start.isoformat() + "Z"
        day_end_iso = day_end.isoformat() + "Z"
        
        print(f"日付: {day_start.strftime('%Y-%m-%d')} のデータを取得中...")
        
        # リクエストボディ
        payload = {
            "location": {
                "latitude": latitude,
                "longitude": longitude
            },
            "period": {
                "startTime": day_start_iso,
                "endTime": day_end_iso
            },
            "universalAqi": True,
            "extraComputations": [
                "DOMINANT_POLLUTANT_CONCENTRATION",
                "POLLUTANT_CONCENTRATION",
                "LOCAL_AQI",
                "POLLUTANT_ADDITIONAL_INFO"
            ],  # HEALTH_RECOMMENDATIONSを除外
            "languageCode": "ja",
            "pageSize": 24  # 一度に取得するデータ数（1日分）
        }
        
        # APIリクエストを送信
        day_data = []
        page_token = None
        retry_count = 0  # 各日付の再試行カウンターをリセット
        
        while True:
            if page_token:
                payload["pageToken"] = page_token
            
            try:
                # APIリクエストを送信
                response = requests.post(url, headers=headers, data=json.dumps(payload))
                
                # レスポンスを処理
                if response.status_code == 200:
                    # エラーカウンターをリセット
                    total_error_count = 0
                    retry_count = 0
                    
                    data = response.json()
                    
                    # データが空の場合は次の日に進む
                    if not data.get("hoursInfo"):
                        print(f"  警告: {day_start.strftime('%Y-%m-%d')}のデータが見つかりませんでした。")
                        break
                    
                    # 各時間のデータを処理
                    for hour_info in data.get("hoursInfo", []):
                        date_time = hour_info.get("dateTime", "N/A")
                        
                        # 既に取得済みのデータはスキップ
                        if date_time in existing_datetimes:
                            continue
                        
                        # aqi_data.csvフォーマットに合わせてデータをマッピング
                        row = {
                            "地点": "神戸市 須磨区",
                            "取得時間": date_time,
                            "AQI値": hour_info.get("indexes", [{}])[0].get("aqi", "N/A"),
                            "大気質ステータス": hour_info.get("indexes", [{}])[0].get("category", "N/A"),
                            "主要汚染物質": hour_info.get("indexes", [{}])[0].get("dominantPollutant", "N/A"),
                            "PM2.5": next((p.get("concentration", {}).get("value", "N/A") for p in hour_info.get("pollutants", []) if p.get("code") == "pm2_5"), "N/A"),
                            "PM10": next((p.get("concentration", {}).get("value", "N/A") for p in hour_info.get("pollutants", []) if p.get("code") == "pm10"), "N/A"),
                            "O3": next((p.get("concentration", {}).get("value", "N/A") for p in hour_info.get("pollutants", []) if p.get("code") == "o3"), "N/A"),
                            "NO2": next((p.get("concentration", {}).get("value", "N/A") for p in hour_info.get("pollutants", []) if p.get("code") == "no2"), "N/A"),
                            "温度": "N/A",  # プレースホルダー、温度データは利用できません
                            "湿度": "N/A",  # プレースホルダー、湿度データは利用できません
                            "気圧": "N/A",  # プレースホルダー、気圧データは利用できません
                            "風速": "N/A",  # プレースホルダー、風速データは利用できません
                            "降水量": "N/A"  # プレースホルダー、降水量データは利用できません
                        }
                        
                        # 新しいデータとして追加
                        day_data.append(row)
                        new_data.append(row)
                        existing_datetimes.add(date_time)  # 取得済みデータに追加
                    
                    # 次のページトークンがあれば保存
                    page_token = data.get("nextPageToken")
                    
                    # 次のページトークンがなければ終了
                    if not page_token:
                        break
                    
                    # APIレート制限を回避するために少し待機
                    # time.sleep(0.5)
                
                else:
                    print(f"  エラーが発生しました。ステータスコード: {response.status_code}")
                    print(f"  エラーが発生したため、次の日に進みます。")
                    break
                    
                    
            except Exception as e:
                print(f"  データ取得中にエラーが発生しました: {str(e)}")
                
                break
        
        print(f"  {day_start.strftime('%Y-%m-%d')}のデータを{len(day_data)}時間分新たに取得しました。")
        
        # 日ごとのデータ取得間に少し待機（APIレート制限対策）
        if day_offset < 29:  # 最後の日でなければ待機
            time.sleep(0.1)
    
    # すべてのデータ取得が完了したら保存
    save_data()

if __name__ == "__main__":
    try:
        fetch_historical_aqi_data(30)
    except Exception as e:
        print(f"予期せぬエラーが発生しました: {str(e)}")
        save_data()  # エラー発生時も保存を試みる