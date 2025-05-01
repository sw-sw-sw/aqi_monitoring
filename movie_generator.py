import os
import cv2
import glob
from config import *

FPS = 30

def format_timestamp(filename):
    """ファイル名からフォーマット済みのタイムスタンプを取得"""
    # ファイル名から拡張子を除去
    basename = os.path.basename(filename)
    name_without_ext = os.path.splitext(basename)[0]
    
    # タイムスタンプが適切な形式かチェック (YYYYMMDDHHMMSSの14桁を想定)
    if len(name_without_ext) == 14 and name_without_ext.isdigit():
        year = name_without_ext[0:4]
        month = name_without_ext[4:6]
        day = name_without_ext[6:8]
        hour = name_without_ext[8:10]
        minute = name_without_ext[10:12]
        
        # 指定された形式に変換 (2025-0429-1310)
        return f"{year}-{month}{day}-{hour}{minute}"
    
    # 形式が異なる場合はそのまま返す
    return name_without_ext

def add_timestamp_to_image(img, timestamp):
    """画像にタイムスタンプを追加"""
    # フォント設定
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.7
    font_color = (255, 255, 255)  # 白色
    font_thickness = 2
    
    # 影の色 (黒)
    shadow_color = (0, 0, 0)
    
    # テキストサイズを取得
    text_size = cv2.getTextSize(timestamp, font, font_scale, font_thickness)[0]
    
    # 位置を計算 (右下に配置)
    x = img.shape[1] - text_size[0] - 10  # 右端から10ピクセル内側
    y = img.shape[0] - 10  # 下端から10ピクセル上
    
    # 影を付けてテキストを描画 (読みやすさのため)
    cv2.putText(img, timestamp, (x+2, y+2), font, font_scale, shadow_color, font_thickness)
    cv2.putText(img, timestamp, (x, y), font, font_scale, font_color, font_thickness)
    
    return img

def generate_movie(input_dir, output_dir, output_file_name, time_stamp=True):
    """タイムスタンプ付きの画像からムービーを作成する"""
    # 出力ディレクトリの作成
    os.makedirs(output_dir, exist_ok=True)
    
    # 入力ディレクトリから画像ファイルを取得（jpgのみ）
    image_files = glob.glob(os.path.join(input_dir, "*.jpg"))
    
    if not image_files:
        print("画像ファイルが見つかりません")
        return None
    
    # タイムスタンプでソート
    image_files.sort()
    print(f"合計 {len(image_files)} 枚の画像を処理します")
    
    # 最初の画像を読み込んでサイズを取得
    first_image = cv2.imread(image_files[0])
    if first_image is None:
        print(f"画像の読み込みに失敗しました: {image_files[0]}")
        return None
    
    height, width = first_image.shape[:2]
    
    # 出力ファイル名の設定
    output_filename = f"timelapse_{output_file_name}.mp4"
    output_path = os.path.join(output_dir, output_filename)
    
    # 動画ライターの設定
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # MP4形式
    video_writer = cv2.VideoWriter(
        output_path, fourcc, FPS, (width, height)
    )
    
    # 各画像を動画に追加
    for i, img_file in enumerate(image_files):
        if i % 20 == 0:  # 進捗表示を減らす
            print(f"処理中: {i+1}/{len(image_files)}")
        
        img = cv2.imread(img_file)
        if img is not None and time_stamp:
            # タイムスタンプを取得
            timestamp = format_timestamp(img_file)
            # 画像にタイムスタンプを追加
            img = add_timestamp_to_image(img, timestamp)
            # 動画に追加
            video_writer.write(img)
    
    # リソースの解放
    video_writer.release()
    
    print(f"タイムスタンプ付き動画が生成されました: {output_path}")
    return output_path

if __name__ == "__main__":
    AREA_DIR ="suma"
    input_dir = os.path.join(IMAGE_CRAWLER_DIR, AREA_DIR)
    output_dir = os.path.join(MOVIE_DIR, AREA_DIR)
    generate_movie(input_dir, output_dir, AREA_DIR, time_stamp=True)