from config import *    
import _movie_generator

file_name = 'timelasp_movie_suma'
input_dir = os.path.join(IMAGE_ANALYSIS_DIR, 'suma/input_image')
output_dir = MOVIE_DIR
_movie_generator.set_FPS(10)
mp4_output = _movie_generator.generate_movie(input_dir, output_dir, file_name, 1, True)

if mp4_output:
    # MP4が生成できたらWebMに変換
    webm_output = _movie_generator.convert_to_webm(mp4_output)
    if webm_output:
        print(f"最終出力（WebM形式）: {webm_output}")