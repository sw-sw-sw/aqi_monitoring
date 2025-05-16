from config import *    
import _movie_generator

file_name = 'timelasp_movie_suma'
input_dir = os.path.join(IMAGE_ANALYSIS_DIR, 'suma/input_image')
output_dir = MOVIE_DIR
_movie_generator.set_FPS(30)  # FPSを30に設定
_movie_generator.generate_movie(input_dir, output_dir, file_name, 7, True)
