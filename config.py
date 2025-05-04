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
HEADERS_COLLECTION = {
    # 一般的なWindowsのChromeブラウザ
    "windows_chrome": {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": "https://weathernews.jp/onebox/livecam/kinki/hyogo/7CDDE906BA8F/",
        "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache"
    },
    
    # MacのSafariブラウザ
    "mac_safari": {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15",
        "Referer": "https://weathernews.jp/onebox/",
        "Accept": "image/png,image/svg+xml,image/*;q=0.8,video/*;q=0.8,*/*;q=0.5",
        "Accept-Language": "ja-jp",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive"
    },
    
    # iPhoneのSafariブラウザ
    "iphone_safari": {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
        "Referer": "https://weathernews.jp/",
        "Accept": "image/png,image/svg+xml,image/*;q=0.8,*/*;q=0.5",
        "Accept-Language": "ja-jp",
        "Connection": "keep-alive",
        "Pragma": "no-cache"
    },
    
    # Androidのモバイルブラウザ
    "android_chrome": {
        "User-Agent": "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.91 Mobile Safari/537.36",
        "Referer": "https://weathernews.jp/onebox/livecam/kinki/hyogo/7CDDE906BA8F/",
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Accept-Language": "ja,en;q=0.9",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive"
    },
    
    # Firefoxブラウザ
    "firefox": {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
        "Referer": "https://weathernews.jp/onebox/livecam/",
        "Accept": "image/webp,*/*",
        "Accept-Language": "ja,en-US;q=0.7,en;q=0.3",
        "Cache-Control": "max-age=0",
        "DNT": "1"
    }
}