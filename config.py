import os
import logging

# 基本設定
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
ABOVE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
IMAGE_ANALYSIS_DIR = os.path.join(DATA_DIR, "image_analysis")
IMAGE_CRAWLER_DIR = os.path.join(DATA_DIR, "image_crawler_data")
MOVIE_DIR = os.path.join(DATA_DIR, "movies")
STATIC_DIR = os.path.join(PROJECT_ROOT, "static")
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")
IMAGE_WEB_URL_DIR = os.path.join(DATA_DIR, "image_web_urls")

# ディレクトリの作成
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(IMAGE_ANALYSIS_DIR, exist_ok=True)
os.makedirs(IMAGE_CRAWLER_DIR, exist_ok=True)
# ファイルパス
AQI_URL = "https://aqicn.org/city/japan/kobeshisumaku/suma/jp/"
CSV_FILE_PATH = os.path.join(DATA_DIR, "kobe_aqi_data.csv")
CSV_FILE_PATH2 = os.path.join(ABOVE_PATH, "aqi_analysis/kobe_aqi_data.csv")
HTML_OUTPUT_PATH = os.path.join(STATIC_DIR, "aqi_graph.html")
LOG_FILE_PATH = os.path.join(LOG_DIR, "app.log")

# スクレイピング設定
SCRAPE_INTERVAL = 3600  # デフォルト: 1時間 (秒単位)
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# フラスク設定
FLASK_HOST = "0.0.0.0"
FLASK_PORT = 8000
FLASK_DEBUG = False

# ロギング設定
def setup_logging():
    """アプリケーションのロギングを設定する"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE_PATH),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("AQI_System")

# グローバルロガーの初期化
logger = setup_logging()


MODEL_PRICING = {
    "claude-3-opus-20240229": {"input": 15.0, "output": 75.0},  # $15/1M入力トークン, $75/1M出力トークン
    "claude-3-sonnet-20240229": {"input": 3.0, "output": 15.0},  # $3/1M入力トークン, $15/1M出力トークン
    "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},  # $0.25/1M入力トークン, $1.25/1M出力トークン
    "claude-3-5-sonnet-20240620": {"input": 3.0, "output": 15.0}  # $3/1M入力トークン, $15/1M出力トークン
}