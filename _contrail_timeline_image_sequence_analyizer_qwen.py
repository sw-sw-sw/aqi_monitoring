

import glob
import json
import re
import csv
import shutil  # <-- この import が抜けていました！
from datetime import datetime
from PIL import Image, ImageDraw
from dotenv import load_dotenv
import os
from config import *
from _contrail_analyzer_qwen import QwenCloudAnalyzer, AnalysisManager

class EnhancedAnalysisManager(AnalysisManager):
    """飛行機雲分析と結果管理を行う拡張クラス - 完全な時系列記録に対応"""
    
    def __init__(self, analyzer, input_dir, output_dir, output_img_dir):
        super().__init__(analyzer, input_dir, output_dir)
        self.output_img_dir = output_img_dir
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.csv_file_path = os.path.join(output_dir, f"contrail_timeline_by_qwen_{timestamp}.csv")
        
        # 出力画像ディレクトリを作成
        os.makedirs(output_img_dir, exist_ok=True)
        
        # CSVファイルが存在しない場合、ヘッダーを作成
        self._initialize_csv()
    
    def _initialize_csv(self):
        """CSVファイルを初期化（存在しない場合はヘッダーを作成）"""
        if not os.path.exists(self.csv_file_path):
            with open(self.csv_file_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["date", "contrail_count"])
    
    def _extract_date_from_filename(self, filepath):
        """ファイル名から日付を抽出（例: 20250429130900.jpg => 20250429130900）"""
        filename = os.path.basename(filepath)
        # 日付形式を抽出（14桁の数字を想定）
        date_match = re.search(r'\d{14}', filename)
        return date_match.group(0) if date_match else None
    
    def _add_to_csv(self, date, contrail_count):
        """CSVに新しい記録を追加"""
        with open(self.csv_file_path, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([date, contrail_count])
    
    def _add_white_circle_to_image(self, image_path, output_path):
        """画像の左下に白丸を追加して保存"""
        try:
            # 画像を開く
            image = Image.open(image_path)
            draw = ImageDraw.Draw(image)
            
            # 画像サイズを取得
            width, height = image.size
            
            # 白丸の設定（画像サイズに応じて調整）
            circle_radius = min(width, height) // 20  # サイズの5%程度
            margin = circle_radius  # 端からの距離
            center_x = margin + circle_radius
            center_y = height - margin - circle_radius
            
            # 白丸を描画
            draw.ellipse(
                [center_x - circle_radius, center_y - circle_radius,
                 center_x + circle_radius, center_y + circle_radius],
                fill='white',
                outline='white'
            )
            
            # 画像を保存
            image.save(output_path)
            
        except Exception as e:
            print(f"画像処理中にエラーが発生しました: {e}")
    
    def _copy_original_image(self, image_path, output_path):
        """オリジナル画像をそのままコピー"""
        try:
            shutil.copy2(image_path, output_path)
        except Exception as e:
            print(f"画像のコピー中にエラーが発生しました: {e}")
    
    def process_images(self, additional_instructions=""):
        """すべての画像を処理し、全ての結果をCSVに記録、全画像を保存"""
        image_paths = self.find_images()
        
        if not image_paths:
            print("画像ファイルが見つかりませんでした。")
            return
        
        print(f"{len(image_paths)}個の画像ファイルを処理します...\n")
        
        # 結果をリセット
        self.results = []
        
        # 各画像を解析
        for i, image_path in enumerate(image_paths, 1):
            print(f"{i}/{len(image_paths)} を処理中... {image_path}")
            result = self.analyzer.analyze(image_path, additional_instructions=additional_instructions)
            self.results.append(result)
            
            # 分析結果から飛行機雲の数を取得
            try:
                contrail_count = 0
                if 'analysis' in result:
                    # APIからの応答が数字の場合
                    if isinstance(result['analysis'], (int, str)):
                        contrail_count = int(result['analysis'])
                
                # ファイル名から日付を抽出
                date = self._extract_date_from_filename(image_path)
                
                if date:
                    # CSVに追加（飛行機雲の有無に関わらず）
                    self._add_to_csv(date, contrail_count)
                    print(f"  -> 飛行機雲: {contrail_count}本, 日付: {date}")
                    
                    # 出力ファイル名を設定
                    filename = os.path.basename(image_path)
                    output_image_path = os.path.join(self.output_img_dir, filename)
                    
                    # 飛行機雲の有無に応じて画像を処理
                    if contrail_count > 0:
                        # 飛行機雲が見つかった場合は白丸を追加
                        self._add_white_circle_to_image(image_path, output_image_path)
                        print(f"    白丸付き画像を保存: {output_image_path}")
                    else:
                        # 飛行機雲が見つからなかった場合はそのままコピー
                        self._copy_original_image(image_path, output_image_path)
                        print(f"    オリジナル画像を保存: {output_image_path}")
                else:
                    print(f"  警告: 日付を抽出できませんでした: {image_path}")
                    
            except Exception as e:
                print(f"  エラー: 結果の処理中に問題が発生しました: {e}")
    
    def get_csv_summary(self):
        """CSVファイルの概要を表示"""
        try:
            with open(self.csv_file_path, "r") as f:
                reader = csv.reader(f)
                rows = list(reader)
                
            print(f"\n時系列データ概要:")
            print(f"総記録数: {len(rows) - 1}行（ヘッダー除く）")
            
            if len(rows) > 1:
                total_contrails = sum(int(row[1]) for row in rows[1:])
                print(f"総飛行機雲数: {total_contrails}本")
                print(f"最初の記録: {rows[1][0]}")
                print(f"最後の記録: {rows[-1][0]}")
                
                # 飛行機雲が見つかった日の割合
                days_with_contrails = sum(1 for row in rows[1:] if int(row[1]) > 0)
                print(f"飛行機雲が見つかった日: {days_with_contrails}/{len(rows) - 1}日")
                
        except Exception as e:
            print(f"CSV概要の表示中にエラーが発生しました: {e}")

# mainは以前と同じ
def main():
    # 環境変数の読み込み
    load_dotenv()
    api_key = os.getenv("DASHSCOPE_API_KEY")
    
    # パスの設定
    # INPUT_DIR = "/home/sw/aqi_monitoring/data/image_crawler_data/suma"
    INPUT_DIR = os.path.join(IMAGE_ANALYSIS_DIR, "suma/input_image")

    OUTPUT_DIR = os.path.join(IMAGE_ANALYSIS_DIR, "suma")
    OUTPUT_IMG_DIR = os.path.join(IMAGE_ANALYSIS_DIR, "suma/output_image")
    
    if not api_key:
        print("エラー: DASHSCOPE_API_KEYが設定されていません。")
        return
    
    # 分析器と拡張マネージャーの初期化
    analyzer = QwenCloudAnalyzer(api_key=api_key,
                                model="qwen2.5-vl-7b-instruct", 
                                resize_dimensions=(640, 360))
    
    manager = EnhancedAnalysisManager(analyzer=analyzer,
                                    input_dir=INPUT_DIR,
                                    output_dir=OUTPUT_DIR,
                                    output_img_dir=OUTPUT_IMG_DIR)
    
    # 処理を実行
    result_file = manager.run()
    
    # CSV概要を表示
    manager.get_csv_summary()
    
    if result_file:
        print(f"\n結果は {result_file} に保存されました。")
        print(f"CSV記録は {manager.csv_file_path} に保存されました。")
        print(f"処理済み画像は {OUTPUT_IMG_DIR} に保存されました。")

if __name__ == "__main__":
    main()
    
# _cloud_analyzer_qwen.pyをインポートして画像中のケムトレイルを検出
# 検出数をcsvに保存
# 検出画像に◯をつけて保存する