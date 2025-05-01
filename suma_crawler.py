import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import os
from datetime import datetime, timedelta
from config import *
from movie_generator import *
from image_crawler import *

URL ='https://weathernews.jp/onebox/livecam/kinki/hyogo/7CDDE906BA8F/'
AREA_DIR = 'suma'
save_dir = os.path.join(IMAGE_CRAWLER_DIR, AREA_DIR)

#capture image
timestamp = datetime.now() - timedelta(minutes=10) # 10 minutes ago
download_image(URL, save_dir, timestamp)
