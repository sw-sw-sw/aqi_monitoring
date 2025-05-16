import os
from datetime import datetime, timedelta
from config import *
import _contrail_image_crawler

URL ='https://weathernews.jp/onebox/livecam/kinki/hyogo/7CDDE906BA8F/'

save_dir = os.path.join(IMAGE_ANALYSIS_DIR, "suma/input_image")

#capture image
timestamp = datetime.now() - timedelta(minutes=20) # 20 minutes ago
_contrail_image_crawler.download_crawl_image(URL, save_dir, timestamp)
