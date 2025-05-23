import os
import cv2
import glob
from config import *
import sys
from datetime import datetime

FPS = 60

def set_FPS(fps):
    """FPSを設定"""
    global FPS
    FPS = fps
    print(f"FPSが {FPS} に設定されました", file=sys.stderr)
    return FPS

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

def extract_date_from_filename(filename):
    """ファイル名から日付オブジェクトを抽出"""
    # ファイルパスからファイル名部分だけを取得
    basename = os.path.basename(filename)
    # ファイル名から拡張子を取り除いた部分を取得
    name_without_ext = os.path.splitext(basename)[0]
    
    # ファイル名が14桁の数字 (YYYYMMDDHHMMSS形式) であるかを確認
    if len(name_without_ext) == 14 and name_without_ext.isdigit():
        # 年、月、日をそれぞれ整数として抽出
        year = int(name_without_ext[0:4])
        month = int(name_without_ext[4:6])
        day = int(name_without_ext[6:8])
        
        # 年、月、日を使ってdatetimeオブジェクトを作成して返す
        return datetime(year, month, day)
    
    # ファイル名が期待する形式でない場合は None を返す
    return None

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

def filter_images_by_days(image_files, days=None):
    """
    指定された日数分の最新画像だけをフィルタリング
    days=None の場合はすべての画像を返す
    """
    if days is None or days <= 0:
        # 日数が指定されていない、または0以下の場合は全画像を返す
        return image_files
    
    # 日付ごとに画像をグループ化
    images_by_date = {}
    for img_file in image_files:
        date_obj = extract_date_from_filename(img_file)
        if date_obj:
            # 日付をキーとして画像をグループ化
            date_str = date_obj.strftime('%Y-%m-%d')
            if date_str not in images_by_date:
                images_by_date[date_str] = []
            images_by_date[date_str].append(img_file)
    
    # 日付でソート（新しい順）
    sorted_dates = sorted(images_by_date.keys(), reverse=True)
    
    # 指定された日数分だけ選択
    selected_dates = sorted_dates[:days]
    
    # 選択された日付の画像を集める
    filtered_images = []
    for date in sorted(selected_dates):  # 日付順に並べ直す
        filtered_images.extend(sorted(images_by_date[date]))  # 各日の画像もソート
    
    return filtered_images

def generate_movie(input_dir, output_dir, output_file_name, days=None, time_stamp=True):
    """
    タイムスタンプ付きの画像からムービーを作成する
    days: 処理する日数（指定がない場合はすべての日を処理）
    """
    # 出力ディレクトリの作成
    os.makedirs(output_dir, exist_ok=True)
    
    # 入力ディレクトリから画像ファイルを取得（jpgのみ）
    image_files = glob.glob(os.path.join(input_dir, "*.jpg"))
    
    if not image_files:
        print("画像ファイルが見つかりません")
        return None
    
    # タイムスタンプでソート
    image_files.sort()
    
    # 指定された日数でフィルタリング
    filtered_images = filter_images_by_days(image_files, days)
    total_images = len(filtered_images)
    
    if days:
        print(f"直近 {days} 日分、合計 {total_images} 枚の画像を処理します", file=sys.stderr)
    else:
        print(f"合計 {total_images} 枚の画像を処理します", file=sys.stderr)
    
    if not filtered_images:
        print("指定された日数分の画像が見つかりません")
        return None
    
    # 最初の画像を読み込んでサイズを取得
    first_image = cv2.imread(filtered_images[0])
    if first_image is None:
        print(f"画像の読み込みに失敗しました: {filtered_images[0]}")
        return None
    
    height, width = first_image.shape[:2]
    
    # 現在の日付と時刻を取得して出力ファイル名に追加
    current_datetime = datetime.now()
    
    # 出力ファイル名の設定
    if days:
        output_filename = f"{output_file_name}_{days}days.mp4"
    else:
        output_filename = f"{output_file_name}.mp4"

    output_path = os.path.join(output_dir, output_filename)
    
    # 動画ライターの設定
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # MP4形式
    video_writer = cv2.VideoWriter(
        output_path, fourcc, FPS, (width, height)
    )
    
    # プログレスバーの設定
    progress_bar_length = 20  # プログレスバーの最大長
    
    # 各画像を動画に追加
    for i, img_file in enumerate(filtered_images):
        if i % 20 == 0:  # 進捗表示を減らす
            # 現在の進捗率を計算
            progress = int((i + 1) / total_images * progress_bar_length)
            # ■の数を進捗に合わせて増やす
            progress_bar = '■' * progress + ' ' * (progress_bar_length - progress)
            # 標準エラー出力に進捗を表示（ログに記録されない）
            print(f"処理中: [{progress_bar}] {i+1}/{total_images}", end='\r', file=sys.stderr)
        
        img = cv2.imread(img_file)
        if img is not None and time_stamp:
            # タイムスタンプを取得
            timestamp = format_timestamp(img_file)
            # 画像にタイムスタンプを追加
            img = add_timestamp_to_image(img, timestamp)
            # 動画に追加
            video_writer.write(img)
    
    # 処理完了を標準エラー出力に表示（ログに記録されない）
    progress_bar = '■' * progress_bar_length
    print(f"処理完了: [{progress_bar}] {total_images}/{total_images}", file=sys.stderr)
    
    # リソースの解放
    video_writer.release()
    
    # 標準出力に結果のみを表示（ログに記録される）- 時分を含む
    time_with_minutes = current_datetime.strftime("%Y-%m-%d %H:%M")
    print(f"[{time_with_minutes}] タイムスタンプ付き動画が生成されました: {output_path}")
    return output_path

import subprocess

def convert_to_webm(input_file, output_file=None):
    """
    MP4ファイルをWebMに変換する
    input_file: 入力MP4ファイルのパス
    output_file: 出力WebMファイルのパス (指定がなければ拡張子を.webmに置き換えたもの)
    """
    if output_file is None:
        # 出力ファイル名を自動生成 (.mp4を.webmに置換)
        output_file = input_file.replace('.mp4', '.webm')
    
    try:
        # FFmpegコマンドを構築
        cmd = [
            'ffmpeg',
            '-i', input_file,    # 入力ファイル
            '-c:v', 'libvpx-vp9',  # VP9コーデック
            '-b:v', '1M',        # ビットレート
            '-crf', '30',        # 品質設定 (0-63、低いほど高品質)
            '-deadline', 'good', # エンコード速度と品質のバランス
            output_file          # 出力ファイル
        ]
        
        print(f"FFmpegでWebM変換を開始します: {input_file} -> {output_file}", file=sys.stderr)
        
        # サブプロセスとしてFFmpeg実行
        process = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 結果確認
        if process.returncode == 0:
            print(f"WebM変換が成功しました: {output_file}", file=sys.stderr)
            return output_file
        else:
            print(f"WebM変換に失敗しました。エラー: {process.stderr}", file=sys.stderr)
            return None
            
    except Exception as e:
        print(f"変換処理中にエラーが発生しました: {e}", file=sys.stderr)
        return None
    
if __name__ == "__main__":

    file_name = 'timelasp_movie_suma'
    input_dir = os.path.join(IMAGE_ANALYSIS_DIR, 'suma/input_image')
    output_dir = MOVIE_DIR
    
    # まずMP4で生成
    mp4_output = generate_movie(input_dir, output_dir, file_name, 20)
    
    if mp4_output:
        # MP4が生成できたらWebMに変換
        webm_output = convert_to_webm(mp4_output)
        if webm_output:
            print(f"最終出力（WebM形式）: {webm_output}")