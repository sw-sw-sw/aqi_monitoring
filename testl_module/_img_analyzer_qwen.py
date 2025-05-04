# main.py
from dotenv import load_dotenv
import os
from config import *
from _contrail_analyzer_qwen import QwenCloudAnalyzer, AnalysisManager

def main():
    # 環境変数の読み込み
    load_dotenv()
    api_key = os.getenv("DASHSCOPE_API_KEY")
    INPUT_DIR = os.path.join(IMAGE_ANALYSIS_DIR, "input")
    OUTPUT_DIR = os.path.join(IMAGE_ANALYSIS_DIR, "output")
    
    if not api_key:
        print("エラー: DASHSCOPE_API_KEYが設定されていません。")
        return
        
    # 分析器とマネージャーの初期化
    analyzer = QwenCloudAnalyzer(api_key=api_key,
                                #  model='qwen-vl-max',
                                #  model='qwen-VL-plus',
                                # model='qwen-turbo-latest',
                                #  model='qwen2.5-vl-72b-instruct',
                                 model="qwen2.5-vl-7b-instruct", 
                                 resize_dimensions=(640, 360),
                                )
    manager = AnalysisManager(analyzer=analyzer,
                              
                              input_dir=INPUT_DIR,
                              output_dir=OUTPUT_DIR
            )
    
    # 処理を実行
    result_file = manager.run()
    
    if result_file:
        print(f"結果は {result_file} に保存されました。")

if __name__ == "__main__":
    main()
     
    # claude_analyze.pyとセットで使用する！