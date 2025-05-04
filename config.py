import os
import logging

# 基本設定
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
ABOVE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(PROJECT_ROOT, "static")
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")

DATA_DIR = os.path.join(PROJECT_ROOT, "data")

IMAGE_ANALYSIS_DIR = os.path.join(DATA_DIR, "image_analysis")
IMAGE_CRAWLER_DIR = os.path.join(DATA_DIR, "image_crawler_data")
MOVIE_DIR = os.path.join(DATA_DIR, "movies")
IMAGE_WEB_URL_DIR = os.path.join(DATA_DIR, "image_web_urls")

# ディレクトリの作成
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(IMAGE_ANALYSIS_DIR, exist_ok=True)
os.makedirs(IMAGE_CRAWLER_DIR, exist_ok=True)
os.makedirs(MOVIE_DIR, exist_ok=True)
os.makedirs(IMAGE_WEB_URL_DIR, exist_ok=True)

# ファイルパス
AQI_URL = "https://aqicn.org/city/japan/kobeshisumaku/suma/jp/"
CSV_FILE_PATH = os.path.join(DATA_DIR, "kobe_aqi_data.csv")
CSV_FILE_PATH2 = os.path.join(ABOVE_PATH, "aqi_analysis/kobe_aqi_data.csv")
HTML_OUTPUT_PATH = os.path.join(STATIC_DIR, "aqi_graph.html")
LOG_FILE_PATH = os.path.join(LOG_DIR, "app.log")
SUMA_LAT_LON =[34.64178340622669, 135.11472440241536]


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

QWEN_MODEL_PRICING = {
    "Qwen-Max": {
        "最大コンテキスト長": 32768,
        "入力料金（100万トークンあたり）": 1.6,
        "出力料金（100万トークンあたり）": 6.4,
        "特徴": "最高の推論性能を提供するフラッグシップモデル"
    },
    "Qwen-Plus": {
        "最大コンテキスト長": 131072,
        "入力料金（100万トークンあたり）": 0.4,
        "出力料金（100万トークンあたり）": "1.2または8.0",
        "特徴": "性能、速度、コストのバランスが取れたモデル"
    },
    "Qwen-Turbo": {
        "最大コンテキスト長": 1008192,
        "入力料金（100万トークンあたり）": 0.05,
        "出力料金（100万トークンあたり）": "0.2または1.0",
        "特徴": "高速かつ低コストで、最大100万トークンのコンテキストをサポート"
    }
,    
    "Qwen-VL-Max": {
        "最大コンテキスト長": 30720,
        "入力料金（1000トークンあたり）": 0.00041,
        "出力料金（1000トークンあたり）": "未公開",
        "特徴": "最高の視覚理解能力を持つフラッグシップモデル"
    },
    "Qwen-VL-Plus": {
        "最大コンテキスト長": 30720,
        "入力料金（1000トークンあたり）": "未公開",
        "出力料金（1000トークンあたり）": "未公開",
        "特徴": "性能とコストのバランスが取れたモデル"
    },
    "Qwen2.5-VL-72B-Instruct": {
        "最大コンテキスト長": 131072,
        "最大出力長": 129024,
        "画像あたりの最大トークン数": 16384,
        "出力料金（100万トークンあたり）": "未公開",
        "特徴": "高精度な視覚理解と構造化出力を提供する大規模モデル"
    },
    "Qwen2.5-VL-32B-Instruct": {
        "最大コンテキスト長": 131072,
        "最大出力長": 129024,
        "画像あたりの最大トークン数": 16384,
        "出力料金（100万トークンあたり）": "未公開",
        "特徴": "軽量でありながら高性能な視覚理解を提供するモデル"
    },
    "Qwen2.5-VL-7B-Instruct": {
        "最大コンテキスト長": "未公開",
        "最大出力長": "未公開",
        "画像あたりの最大トークン数": "未公開",
        "出力料金（100万トークンあたり）": "未公開",
        "特徴": "軽量でありながら高性能な視覚理解を提供するモデル"
    },
    "Qwen2.5-VL-3B-Instruct": {
        "最大コンテキスト長": "未公開",
        "最大出力長": "未公開",
        "画像あたりの最大トークン数": "未公開",
        "出力料金（100万トークンあたり）": "未公開",
        "特徴": "軽量でありながら高性能な視覚理解を提供するモデル"
    }
}