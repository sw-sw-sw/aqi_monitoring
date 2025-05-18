import sys
import os
import traceback
from datetime import datetime
from _aqi_graph_generator import create_aqi_visualization
from config import *
import _aqi_deta_getter_waqi 
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """
    メイン実行関数 - データの取得、保存、グラフ生成を行います
    """

    # 開始時間の記録
    start_time = datetime.now()
    logger.info("==== スケジューラによるデータ更新を開始します ====")
    logger.info(f"開始時間: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    get_aqi_data()
    draw_graph()
    
    # 終了時間と実行時間の記録
    end_time = datetime.now()
    duration = end_time - start_time
    logger.info(f"終了時間: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"実行時間: {duration.total_seconds():.2f} 秒")
    logger.info("==== スケジューラによるデータ更新を終了します ====\n")

def get_aqi_data():
    # AQIデータの取得
    logger.info("AQIデータを取得しています...")
    data = _aqi_deta_getter_waqi.fetch_aqi_data()
    
    if not data:
        logger.error("データを取得できませんでした")
        return

def draw_graph():
    # グラフの更新
    logger.info("グラフを更新しています...")
    csv_file_path = os.path.join(DATA_DIR, 'kobe_aqi_data.csv')
    all_data_output_path = os.path.join(DATA_DIR, 'aqi_graph_all.png')
    recent_data_output_path = os.path.join(DATA_DIR, 'aqi_graph_recent.png')
    
    # all data graph
    all_data_result = create_aqi_visualization(csv_file_path, all_data_output_path, days=None)
    if all_data_result:
        logger.info("すべてのデータを使用したグラフの更新が完了しました")
    else:
        logger.error("すべてのデータを使用したグラフの更新に失敗しました")     
    # latest N days graph
    recent_data_result = create_aqi_visualization(csv_file_path, recent_data_output_path, days=5)
    if recent_data_result:
        logger.info("最新5日間のデータを使用したグラフの更新が完了しました")
    else:
        logger.error("最新5日間のデータを使用したグラフの更新に失敗しました")
    
if __name__ == "__main__":
    main()
    print("すべての処理が完了しました")