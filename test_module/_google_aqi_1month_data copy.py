import requests
import json
import os
import csv
import time
from datetime import datetime, timedelta
import pandas as pd
from config import *  # DATA_DIRを読み込むための設定ファイル

# 環境変数からAPIキーを取得
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv('GOOGLE_AQI_API_KEY')

# 取得したい地点の緯度・経度（例：神戸）
latlon = [34.644428177814845, 135.11131387124348]
latitude = latlon[0]
longitude = latlon[1]

# 過去1ヶ月の大気汚染データを1時間おきに取得する関数
def fetch_historical_aqi_data():
    # 現在の時刻から48時間前を終了時刻とする（APIの制限に対応）
    current_time = datetime.now() - timedelta(hours=48)
    # 過去1ヶ月前の時刻
    start_time_base = current_time - timedelta(days=15)
    # start_time_base = current_time - timedelta(days=30)

    print(f"Google AQI APIの制限により、過去15日間のデータのみを取得します。")
    print(f"取得期間: {start_time_base.strftime('%Y-%m-%d %H:%M')} から {current_time.strftime('%Y-%m-%d %H:%M')}")

    
    # 保存用ディレクトリの作成
    save_dir = os.path.join(DATA_DIR, "o3_google_api_1month")
    os.makedirs(save_dir, exist_ok=True)
    
    # 保存用のCSVファイルパス
    file_path = os.path.join(save_dir, "o3_by_google_aqi_api.csv")
    
    # CSVのヘッダーを定義（健康推奨メッセージを除外）
    csv_headers = [
        "dateTime", "regionCode", "aqi_code", "aqi_displayName", "aqi_value", 
        "aqi_category", "dominantPollutant", "co_concentration", "no_concentration", 
        "no2_concentration", "o3_concentration", "so2_concentration", "pm2_5_concentration", 
        "pm10_concentration", "nh3_concentration"
    ]
    
    # 既に取得済みのデータの日時を確認
    existing_datetimes = set()
    existing_data = []
    if os.path.exists(file_path):
        try:
            # 既存のCSVファイルを読み込む
            df = pd.read_csv(file_path)
            # 取得済みの日時を記録
            existing_datetimes = set(df['dateTime'].tolist())
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
    
    # 新しく取得したデータを格納するリスト
    new_data = []
    
    print(f"過去1ヶ月間（{start_time_base.strftime('%Y-%m-%d %H:%M')}から{current_time.strftime('%Y-%m-%d %H:%M')}まで）の大気質データを取得中...")
    
    # 1日ごとにデータを取得する
    for day_offset in range(30):
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
                    data = response.json()
                    
                    # データが空の場合
                    if not data.get("hoursInfo"):
                        print(f"  警告: {day_start.strftime('%Y-%m-%d')}のデータが見つかりませんでした。")
                        break
                    
                    # 各時間のデータを処理
                    for hour_info in data.get("hoursInfo", []):
                        date_time = hour_info.get("dateTime", "N/A")
                        
                        # 既に取得済みのデータはスキップ
                        if date_time in existing_datetimes:
                            continue
                        
                        row = {field: "N/A" for field in csv_headers}  # すべてのフィールドに初期値を設定
                        row["dateTime"] = date_time
                        row["regionCode"] = data.get("regionCode", "N/A")
                        
                        # AQIインデックス情報
                        for index in hour_info.get("indexes", []):
                            if index.get("code") == "uaqi":  # Universal AQI
                                row["aqi_code"] = index.get("code", "N/A")
                                row["aqi_displayName"] = index.get("displayName", "N/A")
                                row["aqi_value"] = index.get("aqi", "N/A")
                                row["aqi_category"] = index.get("category", "N/A")
                                row["dominantPollutant"] = index.get("dominantPollutant", "N/A")
                        
                        # 汚染物質の詳細
                        for pollutant in hour_info.get("pollutants", []):
                            code = pollutant.get("code", "")
                            concentration = pollutant.get("concentration", {}).get("value", "N/A")
                            if code:
                                field_name = f"{code}_concentration"
                                if field_name in row:
                                    row[field_name] = concentration
                        
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
                    time.sleep(0.5)
                
                else:
                    print(f"  エラーが発生しました。ステータスコード: {response.status_code}")
                    print(f"  エラー詳細: {response.text}")
                    # APIのレスポンスが3回連続で失敗したら、この日をスキップ
                    retry_count = retry_count + 1 if 'retry_count' in locals() else 1
                    if retry_count >= 3:
                        print(f"  3回連続でエラーが発生したため、{day_start.strftime('%Y-%m-%d')}の取得をスキップします。")
                        break
                    # 1分間待機してから再試行
                    print("  1分間待機してから再試行します...")
                    time.sleep(60)
                    continue
                    
            except Exception as e:
                print(f"  データ取得中にエラーが発生しました: {str(e)}")
                # APIのレスポンスが3回連続で失敗したら、この日をスキップ
                retry_count = retry_count + 1 if 'retry_count' in locals() else 1
                if retry_count >= 3:
                    print(f"  3回連続でエラーが発生したため、{day_start.strftime('%Y-%m-%d')}の取得をスキップします。")
                    break
                # 1分間待機してから再試行
                print("  1分間待機してから再試行します...")
                time.sleep(60)
                continue
        
        print(f"  {day_start.strftime('%Y-%m-%d')}のデータを{len(day_data)}時間分新たに取得しました。")
        
        # 日ごとのデータ取得間に少し待機（APIレート制限対策）
        if day_offset < 29:  # 最後の日でなければ待機
            time.sleep(2)
    
    # 新しく取得したデータと既存データを結合して保存
    combined_data = existing_data + new_data
    
    if combined_data:
        # データを日時でソート
        df_combined = pd.DataFrame(combined_data)
        df_combined['dateTime'] = pd.to_datetime(df_combined['dateTime'])
        df_combined = df_combined.sort_values('dateTime')
        
        # CSVに保存（インデックスなし）
        df_combined.to_csv(file_path, index=False)
        
        print(f"\nデータの取得と保存が完了しました。")
        print(f"既存データ: {len(existing_data)}件")
        print(f"新規データ: {len(new_data)}件")
        print(f"合計: {len(combined_data)}件のデータを {file_path} に保存しました。")
        
        # データの概要を表示
        if len(df_combined) > 0:
            print("\n--- データの概要 ---")
            print(f"データ期間: {df_combined['dateTime'].min()} から {df_combined['dateTime'].max()}")
            print(f"データポイント数: {len(df_combined)}")
            
            # 数値データに変換できる列のみを処理
            try:
                df_combined['o3_concentration'] = pd.to_numeric(df_combined['o3_concentration'], errors='coerce')
                print(f"O3 濃度の平均値: {df_combined['o3_concentration'].mean():.2f}")
            except:
                print("O3 濃度の統計を計算できませんでした。")
                
            try:
                df_combined['aqi_value'] = pd.to_numeric(df_combined['aqi_value'], errors='coerce')
                print(f"最大 AQI 値: {df_combined['aqi_value'].max()}")
                print(f"最小 AQI 値: {df_combined['aqi_value'].min()}")
            except:
                print("AQI 値の統計を計算できませんでした。")
            
            # 主要汚染物質の分布
            try:
                dominant_pollutants = df_combined['dominantPollutant'].value_counts()
                print("\n--- 主要汚染物質の分布 ---")
                for pollutant, count in dominant_pollutants.items():
                    print(f"{pollutant}: {count} 時間 ({count/len(df_combined)*100:.1f}%)")
            except:
                print("主要汚染物質の分布を計算できませんでした。")
    else:
        print("\nデータが取得できませんでした。")

if __name__ == "__main__":
    fetch_historical_aqi_data()