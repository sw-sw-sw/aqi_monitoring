import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


import os
import glob
from config import *

def delete_data(delete_dir):
    # 削除対象のディレクトリ

    # 画像ファイルのパターン
    image_patterns = ['*.png', '*.jpg', '*.jpeg', '*.mp4']

    # 画像ファイルを削除
    deleted_count = 0
    for pattern in image_patterns:
        file_paths = glob.glob(os.path.join(delete_dir, pattern))
        print(f"削除対象: {file_paths}")
        for file_path in file_paths:
            try:
                os.remove(file_path)
                print(f"削除: {file_path}")
                deleted_count += 1
            except Exception as e:
                print(f"削除エラー {file_path}: {e}")

    print(f"合計 {deleted_count} 個の画像ファイルを削除しました。")

if __name__ == "__main__":
    data_dir = [
                'image_analysis/cv_output/suma',
                'image_analysis/cv_input/suma',
                #   'iamge_analysis/output',
                #   'image_analysis/input',
                  'movies/suma',
                  ''
                  ]

    delete_dirs = [os.path.join(DATA_DIR, dir) for dir in data_dir]
    
    for delete_dir in delete_dirs:
        delete_data(delete_dir)
        print(f"deleted : {delete_dir}")