
import os
import pandas as pd
import re
from config import logger, CSV_FILE_PATH

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
    
def load_csv_data(filename=CSV_FILE_PATH):
    """
    CSVファイルからデータを読み込む関数
    
    Args:
        filename: 読み込むCSVファイルのパス
    
    Returns:
        DataFrame: 読み込んだデータフレーム、エラー時はNone
    """
    try:
        if not os.path.exists(filename):
            logger.error(f"CSVファイルが見つかりません: {filename}")
            return None
            
        # CSVファイルを読み込む
        df = pd.read_csv(filename, encoding='utf-8-sig')
        logger.info(f"CSVファイルを読み込みました: {filename}")
        logger.info(f"データ形状: {df.shape}")
        
        # 列名のログ出力
        logger.info(f"列名: {', '.join(df.columns)}")
        
        # 古いフォーマットのCSVかどうかを確認（SO2とCOがある場合）
        if "SO2" in df.columns and "CO" in df.columns:
            logger.warning("古いフォーマットのCSVが検出されました。新しいフォーマットに変換します。")
            
            # 新しいデータフレームの作成
            new_df = pd.DataFrame()
            
            # 共通カラムをコピー
            common_columns = ["地点", "取得時間", "AQI値", "大気質ステータス", "主要汚染物質", "PM2.5", "PM10", "O3", "NO2"]
            for col in common_columns:
                if col in df.columns:
                    new_df[col] = df[col]
                else:
                    new_df[col] = "non"
            
            # 新しいカラムを追加
            new_weather_columns = ["温度", "湿度", "気圧", "風速", "降水量"]
            for col in new_weather_columns:
                new_df[col] = "non"
            
            # 欠損値を "non" に置き換え
            new_df = new_df.fillna("non")
            
            # 新しいデータフレームを返す
            df = new_df
            
            # 変換したデータを保存
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            logger.info(f"CSVファイルを新しいフォーマットに変換して保存しました: {filename}")
        
        # 必要な列が存在するか確認
        required_columns = ["地点", "取得時間", "AQI値", "大気質ステータス", "主要汚染物質", 
                           "PM2.5", "PM10", "O3", "NO2", "温度", "湿度", "気圧", "風速", "降水量"]
        
        missing_columns = set(required_columns) - set(df.columns)
        if missing_columns:
            logger.warning(f"CSVファイルに以下の列が不足しています: {', '.join(missing_columns)}")
            # 不足している列を追加
            for col in missing_columns:
                df[col] = "non"
            # 変更を保存
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            logger.info("不足している列を追加しました")
        
        # データ型の確認
        for col in df.columns:
            logger.info(f"列 '{col}' の型: {df[col].dtype}")
            
        # "non"を除外してデータ型を確認
        for col in ["AQI値", "PM2.5", "PM10", "O3", "NO2", "温度", "湿度", "気圧", "風速", "降水量"]:
            if col in df.columns:
                # "non"を一時的にNaNに変換して数値型に変換を試みる
                temp_series = df[col].replace("non", pd.NA)
                try:
                    numeric_series = pd.to_numeric(temp_series, errors='coerce')
                    non_na_count = numeric_series.notna().sum()
                    logger.info(f"列 '{col}' の数値データ数: {non_na_count}/{len(df)}")
                except:
                    logger.warning(f"列 '{col}' の数値変換に失敗しました")
        
        # 一部のデータを表示
        if not df.empty:
            logger.info(f"最初の行: {df.iloc[0].to_dict()}")
        
        return df
    except Exception as e:
        logger.error(f"CSVファイルの読み込み中にエラーが発生しました: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

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

