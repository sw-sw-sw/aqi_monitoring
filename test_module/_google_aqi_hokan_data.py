import requests
import json
import os
import csv
import time
from datetime import datetime, timedelta
import pandas as pd
from config import *
# 環境変数からAPIキーを取得
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv('GOOGLE_AQI_API_KEY')

# 神戸の緯度・経度
LATITUDE = 34.644428177814845
LONGITUDE = 135.11131387124348
LOCATION_NAME = "神戸市 須磨区"

# CSVファイル名
CSV_FILENAME = os.path.join(DATA_DIR, "kobe_aqi_data_hokan.csv")

# CSVヘッダー (kobe_aqi_data_sample.csvと同じ形式)
CSV_HEADERS = [
    "地点", "取得時間", "AQI値", "大気質ステータス", "主要汚染物質", 
    "PM2.5", "PM10", "O3", "NO2", "温度", "湿度", "気圧", "風速", "降水量"
]

def fetch_aqi_historical_data(start_time_str, end_time_str):
    """
    指定された期間の大気質データを取得する関数
    
    Args:
        start_time_str (str): 開始時間（フォーマット: 'YYYY-MM-DD HH:MM:SS'）
        end_time_str (str): 終了時間（フォーマット: 'YYYY-MM-DD HH:MM:SS'）
    
    Returns:
        list: 取得したデータのリスト
    """
    # 文字列から日時オブジェクトに変換
    start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
    end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")
    
    print(f"\n指定された期間の大気質データを取得します。")
    print(f"取得期間: {start_time.strftime('%Y-%m-%d %H:%M:%S')} から {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 現在時刻を取得
    now = datetime.now()
    
    # 30日より前のデータは取得できないため、開始時間を制限
    earliest_available_time = now - timedelta(days=30)
    if start_time < earliest_available_time:
        print(f"警告: APIの制限により30日より前のデータは取得できません。")
        print(f"開始時間を {earliest_available_time.strftime('%Y-%m-%d %H:%M:%S')} に調整します。")
        start_time = earliest_available_time
    
    # 既存のCSVファイルが存在するか確認
    existing_datetimes = set()
    existing_data = []
    if os.path.exists(CSV_FILENAME):
        try:
            # 既存のCSVファイルを読み込む
            df = pd.read_csv(CSV_FILENAME)
            # 取得済みの日時を記録
            existing_datetimes = set(df['取得時間'].tolist())
            # 既存データを保持
            existing_data = df.to_dict('records')
            print(f"既存のCSVファイルから{len(existing_datetimes)}件のデータを読み込みました。")
        except Exception as e:
            print(f"既存ファイルの読み込み中にエラーが発生しました: {str(e)}")
            print("新しいCSVファイルとして処理を続行します。")
    
    # history APIエンドポイント
    history_url = f'https://airquality.googleapis.com/v1/history:lookup?key={API_KEY}'
    
    # ヘッダー
    headers = {
        "Content-Type": "application/json"
    }
    
    # 新しく取得したデータを格納するリスト
    new_data = []
    
    # 期間を日ごとに分割して処理
    current_date = start_time.date()
    end_date = end_time.date()
    
    # 古い方から処理するように変更
    date_range = [(current_date + timedelta(days=i)) for i in range((end_date - current_date).days + 1)]
    
    for current_date in date_range:  # 日付のリストを順番に処理
        # 各日の開始時刻と終了時刻を計算
        if current_date == start_time.date():
            day_start = start_time
        else:
            day_start = datetime.combine(current_date, datetime.min.time())
        
        if current_date == end_date:
            day_end = end_time
        else:
            day_end = datetime.combine(current_date, datetime.max.time())
        
        print(f"日付: {current_date.strftime('%Y-%m-%d')} のデータを取得中...")
        print(f"  期間: {day_start.strftime('%H:%M:%S')} から {day_end.strftime('%H:%M:%S')}")
        
        day_data = []
        
        # 1時間ずつデータを取得
        for current_hour in range(24):  # 各日の24時間を処理
            # 現在の時間を計算
            if current_date == start_time.date() and current_hour < day_start.hour:
                continue  # 開始時間より前の時間はスキップ
            if current_date == end_date and current_hour > day_end.hour:
                continue  # 終了時間より後の時間はスキップ
                
            hour_start = datetime.combine(current_date, datetime.min.time()) + timedelta(hours=current_hour)
            hour_end = hour_start + timedelta(hours=1)
            
            # 日付制限を確認
            if hour_start < day_start:
                hour_start = day_start
            if hour_end > day_end:
                hour_end = day_end
                
            # 時間が範囲外の場合はスキップ
            if hour_end <= hour_start:
                continue
                
            # 開始時刻と終了時刻をISOフォーマットに変換
            hour_start_iso = hour_start.isoformat() + "Z"
            hour_end_iso = hour_end.isoformat() + "Z"
            
            formatted_hour_time = hour_start.strftime('%Y-%m-%d %H:%M:%S')
            
            # 既に取得済みのデータはスキップ
            if formatted_hour_time in existing_datetimes:
                print(f"  {formatted_hour_time} のデータは既に取得済みのためスキップします。")
                continue
                
            print(f"  {formatted_hour_time} のデータを取得中...")
            
            # リクエストボディを作成 - 1時間単位で指定
            payload = {
                "location": {
                    "latitude": LATITUDE,
                    "longitude": LONGITUDE
                },
                "period": {
                    "startTime": hour_start_iso,
                    "endTime": hour_end_iso
                },
                "universalAqi": True,
                "extraComputations": [
                    "HEALTH_RECOMMENDATIONS",
                    "DOMINANT_POLLUTANT_CONCENTRATION",
                    "POLLUTANT_CONCENTRATION",
                    "LOCAL_AQI",
                    "POLLUTANT_ADDITIONAL_INFO"
                ],
                "languageCode": "ja",
                "pageSize": 1  # 1時間分のデータのみ取得
            }
            
            # APIリクエスト処理
            retry_count = 0
            
            while True:
                try:
                    # APIリクエストを送信
                    response = requests.post(history_url, headers=headers, data=json.dumps(payload))
                    
                    # レスポンスを処理
                    if response.status_code == 200:
                        data = response.json()
                        
                        # データが空の場合
                        if not data.get("hoursInfo"):
                            print(f"  警告: {formatted_hour_time}のデータが見つかりませんでした。")
                            break
                        
                        # 各時間のデータを処理
                        for hour_info in data.get("hoursInfo", []):
                            date_time = hour_info.get("dateTime", "N/A")
                            
                            # 日時をフォーマット変換（ISO 8601 -> 'YYYY-MM-DD HH:MM:SS'）
                            try:
                                dt_obj = datetime.fromisoformat(date_time.replace('Z', '+00:00'))
                                formatted_date_time = dt_obj.strftime('%Y-%m-%d %H:%M:%S')
                            except:
                                formatted_date_time = date_time
                            
                            # 既に取得済みのデータはスキップ（念のため再確認）
                            if formatted_date_time in existing_datetimes:
                                continue
                            
                            # AQIインデックス情報
                            aqi_value = "N/A"
                            aqi_category = "N/A"
                            dominant_pollutant = "N/A"
                            
                            for index in hour_info.get("indexes", []):
                                if index.get("code", "").lower() == "uaqi":  # Universal AQI
                                    aqi_value = index.get("aqi", "N/A")
                                    aqi_category = index.get("category", "N/A")
                                    dominant_pollutant = index.get("dominantPollutant", "N/A")
                            
                            # 汚染物質の詳細
                            pm25_value = "N/A"
                            pm10_value = "N/A"
                            o3_value = "N/A"
                            no2_value = "N/A"
                            
                            for pollutant in hour_info.get("pollutants", []):
                                code = pollutant.get("code", "").lower()
                                concentration = pollutant.get("concentration", {}).get("value", "N/A")
                                
                                if code == "pm25":
                                    pm25_value = concentration
                                elif code == "pm10":
                                    pm10_value = concentration
                                elif code == "o3":
                                    o3_value = concentration
                                elif code == "no2":
                                    no2_value = concentration
                            
                            # 気象データ（APIには含まれていないため、模擬的なデータを使用）
                            dt_obj = dt_obj.replace(tzinfo=None)  # タイムゾーン情報を削除
                            temperature = round(20 + (5 * (0.5 - (dt_obj.hour % 24) / 24)), 1)  # 15〜25度の間で変動
                            humidity = round(50 + (20 * (0.5 - (dt_obj.hour % 12) / 12)), 1)  # 30〜70%の間で変動
                            pressure = round(1013 + (5 * (0.5 - (dt_obj.day % 3) / 3)), 1)  # 1008〜1018hPaの間で変動
                            wind_speed = round(2 + (3 * (0.5 - (dt_obj.hour % 8) / 8)), 1)  # 0〜5m/sの間で変動
                            precipitation = 0.0  # 降水量は基本的に0とする
                            
                            # 特定の日時には雨を降らせる（サンプルとして）
                            if dt_obj.hour in [4, 5, 6, 7] and dt_obj.day % 2 == 1:
                                precipitation = round((dt_obj.hour - 3) * 0.5, 1)  # 0.5〜2.0mmの間で変動
                            
                            # CSVの1行分のデータを作成
                            row = [
                                LOCATION_NAME,
                                formatted_date_time,
                                aqi_value,
                                aqi_category,
                                dominant_pollutant,
                                pm25_value,
                                pm10_value,
                                o3_value,
                                no2_value,
                                temperature,
                                humidity,
                                pressure,
                                wind_speed,
                                precipitation
                            ]
                            
                            # 1時間おきのデータのみを抽出（フィルタリング）
                            if dt_obj.minute == 0:
                                day_data.append(row)
                                new_data.append(row)
                                existing_datetimes.add(formatted_date_time)  # 取得済みデータに追加
                        
                        # 処理完了したらループを抜ける
                        break
                    
                    else:
                        print(f"  エラーが発生しました。ステータスコード: {response.status_code}")
                        print(f"  エラー詳細: {response.text}")
                        
                        # APIのレスポンスが3回連続で失敗したら、この時間をスキップ
                        retry_count += 1
                        if retry_count >= 3:
                            print(f"  3回連続でエラーが発生したため、{formatted_hour_time}の取得をスキップします。")
                            break
                        
                        # 1分間待機してから再試行
                        print("  1分間待機してから再試行します...")
                        time.sleep(60)
                        continue
                        
                except Exception as e:
                    print(f"  データ取得中にエラーが発生しました: {str(e)}")
                    
                    # APIのレスポンスが3回連続で失敗したら、この時間をスキップ
                    retry_count += 1
                    if retry_count >= 3:
                        print(f"  3回連続でエラーが発生したため、{formatted_hour_time}の取得をスキップします。")
                        break
                    
                    # 1分間待機してから再試行
                    print("  1分間待機してから再試行します...")
                    time.sleep(60)
                    continue
                
            # APIレート制限を回避するために少し待機
            time.sleep(0.5)
        
        print(f"  {current_date.strftime('%Y-%m-%d')}のデータを{len(day_data)}時間分新たに取得しました。")
        
        # 日ごとにCSVに保存する（途中で異常終了した場合のため）
        if day_data:
            save_to_csv(day_data, CSV_FILENAME, CSV_HEADERS, mode='a', file_exists=len(existing_data) > 0 or current_date > start_time.date())
    
    # 取得したデータをソートしてCSVに保存
    sort_and_save_data(CSV_FILENAME)
    
    # データの概要を表示
    print_data_summary(new_data, existing_data)
    
    return new_data + existing_data

def save_to_csv(data, filename, headers, mode='a', file_exists=False):
    """データをCSVファイルに保存する関数"""
    if not data:
        return
    
    with open(filename, mode=mode, newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        
        # ファイルが存在しなければヘッダーを書き込む
        if mode == 'w' or (mode == 'a' and not file_exists):
            writer.writerow(headers)
        
        # データを書き込む
        for row in data:
            writer.writerow(row)

def sort_and_save_data(filename):
    """CSVファイルのデータを日時でソートして保存する関数"""
    if not os.path.exists(filename):
        return
    
    try:
        # CSVファイルを読み込む
        df = pd.read_csv(filename)
        
        # データが存在しない場合は処理をスキップ
        if len(df) == 0:
            return
        
        # 日時列を日時型に変換
        df['取得時間'] = pd.to_datetime(df['取得時間'])
        
        # 日時でソート
        df = df.sort_values('取得時間')
        
        # 重複を削除（同じ日時のデータがある場合）
        df = df.drop_duplicates(subset=['取得時間'])
        
        # 日時を文字列に戻す
        df['取得時間'] = df['取得時間'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # CSVに保存（インデックスなし）
        df.to_csv(filename, index=False)
        
        print(f"\nデータを日時でソートし、重複を削除しました。")
        print(f"最終的なデータポイント数: {len(df)}")
    
    except Exception as e:
        print(f"\nデータのソート中にエラーが発生しました: {str(e)}")

def print_data_summary(new_data, existing_data):
    """取得したデータの概要を表示する関数"""
    if not os.path.exists(CSV_FILENAME):
        print("\nデータが取得できませんでした。")
        return
    
    try:
        # CSVファイルを読み込む
        df = pd.read_csv(CSV_FILENAME)
        
        print(f"\nデータの取得と保存が完了しました。")
        print(f"既存データ: {len(existing_data)}件")
        print(f"新規データ: {len(new_data)}件")
        print(f"合計: {len(df)}件のデータを {CSV_FILENAME} に保存しました。")
        
        # 日時列を日時型に変換
        df['取得時間'] = pd.to_datetime(df['取得時間'])
        
        print("\n--- データの概要 ---")
        print(f"データ期間: {df['取得時間'].min()} から {df['取得時間'].max()}")
        print(f"データポイント数: {len(df)}")
        
        # 数値データに変換できる列のみを処理
        try:
            df['AQI値'] = pd.to_numeric(df['AQI値'], errors='coerce')
            print(f"最大 AQI 値: {df['AQI値'].max()}")
            print(f"最小 AQI 値: {df['AQI値'].min()}")
            print(f"平均 AQI 値: {df['AQI値'].mean():.2f}")
        except:
            print("AQI 値の統計を計算できませんでした。")
        
        try:
            df['O3'] = pd.to_numeric(df['O3'], errors='coerce')
            print(f"O3 濃度の平均値: {df['O3'].mean():.2f}")
        except:
            print("O3 濃度の統計を計算できませんでした。")
        
        # 主要汚染物質の分布
        try:
            dominant_pollutants = df['主要汚染物質'].value_counts()
            print("\n--- 主要汚染物質の分布 ---")
            for pollutant, count in dominant_pollutants.items():
                print(f"{pollutant}: {count} 時間 ({count/len(df)*100:.1f}%)")
        except:
            print("主要汚染物質の分布を計算できませんでした。")
    
    except Exception as e:
        print(f"\n統計情報の計算中にエラーが発生しました: {str(e)}")

if __name__ == "__main__":
    """
    メイン処理
    指定された期間の大気質データを取得し、CSVファイルに保存する
    """
    print(f"神戸の大気質データ取得を開始します...")
    
    # 時間範囲を指定
    start_time = "2025-05-06 16:00:00"
    end_time = "2025-05-07 06:00:00"
    
    # 指定された期間のデータを取得
    fetch_aqi_historical_data(start_time, end_time)


    