from config import *    
from contrail_movie_generator import generate_movie    

file_name = 'timelasp_movie_suma_contrai_detection'
input_dir = os.path.join(IMAGE_ANALYSIS_DIR, 'output_img_path')
output_dir = MOVIE_DIR
generate_movie(input_dir, output_dir, file_name, time_stamp=True)
