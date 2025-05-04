from config import *    
import _movie_generator

file_name = 'timelasp_movie_suma'
input_dir = os.path.join(IMAGE_CRAWLER_DIR, 'suma')
output_dir = MOVIE_DIR
_movie_generator.generate_movie(input_dir, output_dir, file_name, 1, True)
