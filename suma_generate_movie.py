from config import *    
from movie_generator import generate_movie    
    

AREA_DIR ="suma"
input_dir = os.path.join(IMAGE_CRAWLER_DIR, AREA_DIR)
output_dir = os.path.join(MOVIE_DIR, AREA_DIR)
generate_movie(input_dir, output_dir, AREA_DIR, time_stamp=True)
