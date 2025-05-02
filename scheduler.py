
import sys
import os
import traceback
from datetime import datetime
from graph_generator import generate_graph
from config import *
from aqi_scraper import fetch_aqi_data
from data_handler import save_to_csv

def main():
    """
    メイン実行関数 - データの取得、保存、グラフ生成を行います
    """
    # 開始時間の記録
    start_time = datetime.now()
    logger.info("==== スケジューラによるデータ更新を開始します ====")
    logger.info(f"開始時間: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # AQIデータの取得
        logger.info("AQIデータを取得しています...")
        data = fetch_aqi_data()
        
        if not data:
            logger.error("データを取得できませんでした")
            return
            
        # 取得したデータのログ出力
        logger.info("取得したデータ:")
        # 基本情報のログ出力
        basic_keys = ["地点", "取得時間", "AQI値", "大気質ステータス", "主要汚染物質"]
        for key in basic_keys:
            if key in data:
                logger.info(f"  {key}: {data[key]}")
        
        # 汚染物質データのログ出力
        logger.info("  汚染物質データ:")
        pollutant_keys = ["PM2.5", "PM10", "O3", "NO2"]
        for key in pollutant_keys:
            if key in data and data[key]:
                logger.info(f"    {key}: {data[key]}")
        
        # 気象データのログ出力
        logger.info("  気象データ:")
        weather_keys = ["温度", "湿度", "気圧", "風速", "降水量"]
        for key in weather_keys:
            if key in data and data[key]:
                logger.info(f"    {key}: {data[key]}")
        
        # CSVに保存
        logger.info("データをCSVに保存しています...")
        save_result = save_to_csv(data, CSV_FILE_PATH)
        save_to_csv(data, CSV_FILE_PATH2)
        
        if not save_result:
            logger.error("データの保存に失敗しました")
            return
            
        # グラフの更新
        logger.info("グラフを更新しています...")
        graph_result = generate_graph(os.path.join(DATA_DIR, "aqi_graph.png"))
        
        if graph_result:
            logger.info("すべての処理が完了しました")
        else:
            logger.error("グラフの更新に失敗しました")
    
    except Exception as e:
        logger.error(f"実行中にエラーが発生しました: {e}")
        logger.error(traceback.format_exc())
    
    # 終了時間と実行時間の記録
    end_time = datetime.now()
    duration = end_time - start_time
    logger.info(f"終了時間: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"実行時間: {duration.total_seconds():.2f} 秒")
    logger.info("==== スケジューラによるデータ更新を終了します ====\n")

if __name__ == "__main__":
    main()
    print("すべての処理が完了しました")