import requests
from PIL import Image
from io import BytesIO
import datetime
import os, time, random
from config import *
import re
from datetime import datetime, timedelta



def convert_to_base_url(page_url, size="640"):
    """
    ウェザーニュースのライブカメラページURLから画像のBASE_URLを生成する
    
    Args:
        page_url (str): ライブカメラのページURL
            例: https://weathernews.jp/onebox/livecam/kinki/hyogo/7CDDE906BA8F/
        size (str, optional): 画像サイズ. デフォルトは "640"
        
    Returns:
        str: 画像のBASE_URL
            例: https://gvs.weathernews.jp/livecam/7CDDE906BA8F/640/
    """
    # カメラIDを抽出する正規表現パターン
    pattern = r'/([0-9A-F]{12})/?'
    
    # カメラIDを抽出
    match = re.search(pattern, page_url)
    if not match:
        raise ValueError("URLからカメラIDを抽出できませんでした")
    
    camera_id = match.group(1)
    
    # 新しいBASE_URLを構築
    base_url = f"https://gvs.weathernews.jp/livecam/{camera_id}/{size}/"
    
    return base_url

def generate_url(url, _time_stamp):
    acquisition_time = _time_stamp
    timestamp = acquisition_time.strftime("%Y%m%d%H%M") + "00"

    BASE_URL = convert_to_base_url(url)
    full_url = BASE_URL + timestamp + ".webp"
    print(f"Generated URL: {full_url}")
    return full_url, timestamp

def download_image(url,save_dir, timestamp):
    full_url, timestamp = generate_url(url, timestamp)
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        response = requests.get(full_url, headers=headers)
        if response.status_code == 200:
            image = Image.open(BytesIO(response.content))
            rgb_image = image.convert("RGB")
            output_path = os.path.join(save_dir, timestamp + ".jpg")
            rgb_image.save(output_path, "JPEG", quality=95)
            print(f"Saved: {output_path}")
        else:
            print(f"Image not found (status {response.status_code}): {full_url}")
    except Exception as e:
        print(f"Error downloading {full_url}: {e}")

if __name__ == "__main__":
    # setting
    URL ='https://weathernews.jp/onebox/livecam/kinki/hyogo/7CDDE906BA8F/'
    AREA_DIR = 'suma'
    save_dir = os.path.join(IMAGE_CRAWLER_DIR, AREA_DIR)
    timestamp = datetime.now() - timedelta(minutes=10) # 10 minutes ago

    download_image(URL, save_dir, timestamp)
