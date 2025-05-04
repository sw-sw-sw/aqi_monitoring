# キャプチャーした画像をcvで解析
# その画像をムービー化する

from bak.image_analyzer_cv import *
from contrail_movie_generator import *

AREA_DIR = 'suma'
input_dir = os.path.join(IMAGE_CRAWLER_DIR, AREA_DIR)
print(f"input_dir: {input_dir}")
output_dir = os.path.join(IMAGE_ANALYSIS_DIR, "cv_output/suma")
print(f"output_dir: {output_dir}")
cv_analyzer(input_dir, output_dir)


input_dir =  os.path.join(IMAGE_ANALYSIS_DIR, "cv_output/suma")
output_dir = os.path.join(MOVIE_DIR, AREA_DIR)
file_name = "suma_cv_movie"
generate_movie(input_dir, output_dir, file_name, time_stamp=True)