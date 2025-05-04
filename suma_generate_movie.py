from config import *    
import movie_generator

file_name = 'timelasp_movie_suma'
input_dir = os.path.join(IMAGE_CRAWLER_DIR, "suma")
output_dir = MOVIE_DIR
movie_generator.generate_movie(input_dir, output_dir, file_name, time_stamp=True)
