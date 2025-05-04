import os
from datetime import datetime, timedelta
from config import *
import _contrail_image_crawler

URL ='https://weathernews.jp/onebox/livecam/kinki/hyogo/7CDDE906BA8F/'
AREA_DIR = 'suma'
save_dir = os.path.join(IMAGE_CRAWLER_DIR, AREA_DIR)

#capture image
timestamp = datetime.now() - timedelta(minutes=10) # 10 minutes ago
_contrail_image_crawler.download_crawl_image(URL, save_dir, timestamp)
