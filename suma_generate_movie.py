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

# make movie
input_dir = os.path.join(IMAGE_CRAWLER_DIR, AREA_DIR)
output_dir = os.path.join(MOVIE_DIR, AREA_DIR)
generate_movie(input_dir, output_dir, AREA_DIR, time_stamp=True)
