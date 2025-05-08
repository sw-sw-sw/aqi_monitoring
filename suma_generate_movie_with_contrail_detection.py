from config import *    
from _movie_generator import generate_movie    

file_name = 'timelasp_movie_suma_contrail_detection'
input_dir = os.path.join(IMAGE_ANALYSIS_DIR, 'suma/output_image')
output_dir = MOVIE_DIR
generate_movie(input_dir, output_dir, file_name,7, time_stamp=True)
