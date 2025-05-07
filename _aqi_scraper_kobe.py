import os
import json
import time
import requests
from datetime import datetime
from config import *

import pandas as pd
import re

from dotenv import load_dotenv
load_dotenv()

# WAQI API エンドポイントとトークン
# 注意: 実際のAPIキーに置き換える必要があります
API_BASE_URL = "https://api.waqi.info"
API_TOKEN = os.getenv('AQI_API_TOKEN')  # api_token.pyからインポート

def fetch_aqi_data():
    """神戸市須磨区の大気質データをAPIから取得する関数"""
    try:
        # トークンが設定されているか確認
        if not API_TOKEN:
            logger.error("APIトークンが設定されていません")
            return None

        # 須磨区の地点を取得するためのURL
        # 地点名で検索する方法
        # url = f"{API_BASE_URL}/feed/japan/kobeshisumaku/suma/?token={API_TOKEN}"
        url = f"{API_BASE_URL}/feed/geo:34.64375093046715;135.10933036233058/?token={API_TOKEN}"
        
        # 代替方法: 地理座標を使用（須磨区の緯度経度を使用）
        # Suma Ward, Kobe coordinates: 約 34.65, 135.13
        # url = f"{API_BASE_URL}/feed/geo:34.65;135.13/?token={API_TOKEN}"
        # 自宅　34.64375093046715, 135.10933036233058
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
        if not result:
            logger.error("APIレスポンスの解析に失敗しました")
            return None

        # CSVに保存
        logger.info("データをCSVに保存しています...")
        if not save_to_csv(result, CSV_FILE_PATH):
            logger.error("データの保存に失敗しました")
            return None

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
    
    
#------------------------- data handler-------------------------
    
def save_to_csv(data, filename=CSV_FILE_PATH):
    """
    スクレイピングしたデータをCSVファイルに保存する関数
    
    Args:
        data: 保存するデータ辞書
        filename: 保存先のファイル名
    
    Returns:
        bool: 保存が成功したかどうか
    """
    if not data:
        logger.warning("データがないため保存しません")
        return False
    
    try:
        # 保存するデータの順序とカラムを定義
        columns = [
            "地点", "取得時間", "AQI値", "大気質ステータス", "主要汚染物質",
            "PM2.5", "PM10", "O3", "NO2",
            "温度", "湿度", "気圧", "風速", "降水量"
        ]
        
        # データをDataFrameに変換
        df_new = pd.DataFrame([data])
        
        # 地点名を統一（Miyukichodのケースを「神戸市 須磨区」に変更）
        if "地点" in df_new.columns:
            df_new["地点"] = df_new["地点"].apply(lambda x: "神戸市 須磨区" if "須磨" in str(x) else x)
        
        # 必要なカラムがない場合は0または適切な初期値を設定
        for col in columns:
            if col not in df_new.columns:
                if col in ["温度", "湿度", "気圧", "風速", "降水量"]:
                    df_new[col] = 0.0  # 数値型カラムには0.0を設定
                else:
                    df_new[col] = ""   # 文字列型カラムには空文字を設定
        
        # 数値型カラムの値がNaNまたは空文字の場合、0.0に設定
        numeric_columns = ["温度", "湿度", "気圧", "風速", "降水量"]
        for col in numeric_columns:
            df_new[col] = df_new[col].fillna(0.0)
            df_new[col] = df_new[col].replace("", 0.0)
        
        # カラムの順序を整える
        df_new = df_new[columns]
        
        # ファイルの存在確認
        file_exists = os.path.isfile(filename)
        
        if file_exists:
            # 既存のCSVファイルを読み込み
            df_existing = pd.read_csv(filename, encoding='utf-8-sig')
            
            # 既存のデータに新しいデータを追加
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
            
            # 重複する行を取得時間に基づいて削除（最新のものを保持）
            df_combined = df_combined.drop_duplicates(subset=['取得時間'], keep='last')
            
            # 欠損値を適切な値で埋める
            for col in numeric_columns:
                df_combined[col] = df_combined[col].fillna(0.0)
            
            # 結合したデータを保存
            df_combined.to_csv(filename, index=False, encoding='utf-8-sig')
        else:
            # ディレクトリが存在するか確認し、なければ作成
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            # 新規ファイルとして保存
            df_new.to_csv(filename, index=False, encoding='utf-8-sig')
        
        logger.info(f"データを {filename} に保存しました")
        
        # 念のため保存されたデータの行数を確認
        saved_df = pd.read_csv(filename, encoding='utf-8-sig')
        logger.info(f"現在のCSVファイルには {len(saved_df)} 行のデータがあります")
        
        return True
        
    except Exception as e:
        logger.error(f"CSVへの保存中にエラーが発生しました: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def preprocess_aqi_data(df):
    """
    AQIデータを前処理する関数
    
    Args:
        df: 処理するデータフレーム
    
    Returns:
        DataFrame: 前処理済みのデータフレーム、エラー時はNone
    """
    if df is None or df.empty:
        logger.error("前処理するデータがありません")
        return None, []
        
    try:
        # 必要な列が存在するか確認
        required_columns = ["取得時間", "AQI値"]
        for col in required_columns:
            if col not in df.columns:
                logger.error(f"必要な列 '{col}' がデータフレームに存在しません")
                return None, []
        
        # データコピーを作成して元のデータを保持
        df_processed = df.copy()
        
        # AQI値の文字列を数値に変換
        if df_processed["AQI値"].dtype == object:  # 文字列の場合
            logger.info("AQI値を文字列から数値に変換します")
            df_processed["AQI値_数値"] = df_processed["AQI値"].apply(
                lambda x: extract_numeric_value(x) if isinstance(x, str) and x != "non" else x
            )
        else:
            logger.info("AQI値は既に数値型です")
            df_processed["AQI値_数値"] = df_processed["AQI値"]
        
        # AQI値の型を明示的に数値に変換
        df_processed["AQI値_数値"] = pd.to_numeric(df_processed["AQI値_数値"], errors='coerce')
        
        # 日時列の変換
        try:
            df_processed["取得時間"] = pd.to_datetime(df_processed["取得時間"])
        except Exception as e:
            logger.error(f"日時の変換中にエラー: {e}")
            logger.info("日時列の一部: " + str(df_processed["取得時間"].head(3).tolist()))
        
        # 汚染物質データと気象データを確認
        pollutant_columns = ["PM2.5", "PM10", "O3", "NO2"]
        weather_columns = ["温度", "湿度", "気圧", "風速", "降水量"]
        
        # 利用可能なカラムを特定
        available_pollutants = [col for col in pollutant_columns if col in df_processed.columns]
        available_weather = [col for col in weather_columns if col in df_processed.columns]
        
        # 数値に変換
        for col in available_pollutants + available_weather:
            if df_processed[col].dtype == object:  # 文字列の場合
                try:
                    logger.info(f"{col}を文字列から数値に変換します")
                    df_processed[f"{col}_数値"] = df_processed[col].apply(
                        lambda x: extract_numeric_value(x) if isinstance(x, str) and x != "non" else x
                    )
                    # 明示的に数値型に変換
                    df_processed[f"{col}_数値"] = pd.to_numeric(df_processed[f"{col}_数値"], errors='coerce')
                except Exception as e:
                    logger.error(f"{col}の変換中にエラー: {e}")
                    df_processed[f"{col}_数値"] = None
            else:
                logger.info(f"{col}は既に数値型です")
                df_processed[f"{col}_数値"] = df_processed[col]
        
        # 変換後のデータ型を確認
        logger.info(f"変換後のAQI値_数値の型: {df_processed['AQI値_数値'].dtype}")
        logger.info(f"変換後の取得時間の型: {df_processed['取得時間'].dtype}")
        
        # 欠損値があれば報告
        missing_values = df_processed["AQI値_数値"].isnull().sum()
        if missing_values > 0:
            logger.warning(f"AQI値_数値に {missing_values} 件の欠損値があります")
        
        logger.info("データの前処理が完了しました")
        return df_processed, available_pollutants + available_weather
    
    except Exception as e:
        logger.error(f"データの前処理中にエラーが発生しました: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None, []

def extract_numeric_value(text):
    """
    テキストから数値を抽出する関数
    
    Args:
        text: 数値を含むテキスト
    
    Returns:
        float: 抽出された数値、数値がない場合はNone
    """
    if not text or not isinstance(text, str) or text == "non":
        return None
        
    # 数値パターンを探す
    match = re.search(r'(\d+\.?\d*)', text)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None
    


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

# AQI値をAPI経由で取得する。
# https://api.waqi.info