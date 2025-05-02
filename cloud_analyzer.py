import os
import base64
from PIL import Image
from io import BytesIO
from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, Optional, BinaryIO
from openai import OpenAI
from datetime import datetime

class ImageAnalyzer(ABC):
    """画像分析の基底クラス"""
    
    def __init__(self, resize_dimensions: Tuple[int, int] = (320, 180)):
        """
        初期化
        
        Args:
            resize_dimensions: リサイズする画像のサイズ（幅, 高さ）
        """
        self.resize_dimensions = resize_dimensions
    
    def resize_image(self, image_path: str) -> bytes:
        """
        画像をリサイズする
        
        Args:
            image_path: 画像ファイルのパス
            
        Returns:
            bytes: リサイズされた画像のバイナリデータ
            
        Raises:
            FileNotFoundError: 画像ファイルが見つからない場合
            Exception: その他のエラー
        """
        try:
            # 画像を開く
            img = Image.open(image_path)
            
            # 画像をリサイズ（アスペクト比を維持しつつ、指定サイズに収まるようにする）
            img.thumbnail(self.resize_dimensions, Image.LANCZOS)
            
            # 新しい白い背景画像を作成
            new_img = Image.new("RGB", self.resize_dimensions, (255, 255, 255))
            
            # リサイズした画像を中央に配置
            position = ((self.resize_dimensions[0] - img.width) // 2, 
                        (self.resize_dimensions[1] - img.height) // 2)
            new_img.paste(img, position)
            
            # リサイズした画像をバイトストリームに保存
            buffered = BytesIO()
            new_img.save(buffered, format=img.format if img.format else "JPEG")
            return buffered.getvalue()
        
        except FileNotFoundError as e:
            raise FileNotFoundError(f"画像ファイルが見つかりません: {image_path}")
        except Exception as e:
            print(f"画像のリサイズ中にエラーが発生しました: {e}")
            # エラーの場合は元の画像をそのまま読み込む
            with open(image_path, "rb") as image_file:
                return image_file.read()
    
    def encode_image(self, image_data: bytes) -> str:
        """
        画像データをbase64エンコードする
        
        Args:
            image_data: 画像のバイナリデータ
            
        Returns:
            str: base64エンコードされた画像データ
        """
        return base64.b64encode(image_data).decode('utf-8')
    
    @abstractmethod
    def analyze(self, image_path: str, **kwargs) -> Dict[str, Any]:
        """
        画像を分析する抽象メソッド（サブクラスで実装）
        
        Args:
            image_path: 分析する画像のパス
            **kwargs: 追加のパラメータ
            
        Returns:
            Dict[str, Any]: 分析結果
        """
        pass
    
class QwenCloudAnalyzer(ImageAnalyzer):
    """Qwen APIを使用した雲分析クラス"""
    
    def __init__(self, api_key: str, 
                 model: str = "qwen2.5-vl-7b-instruct", 
                 resize_dimensions: Tuple[int, int] = (320, 180),
                 base_url: str = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"):
        """
        初期化
        
        Args:
            api_key: Qwen API キー
            model: 使用するモデル名
            resize_dimensions: リサイズする画像のサイズ
            base_url: API のベースURL
        """
        super().__init__(resize_dimensions)
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.client = self._initialize_client()
    
    def _initialize_client(self) -> OpenAI:
        """
        APIクライアントを初期化
        
        Returns:
            OpenAI: 初期化されたクライアント
        """
        return OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    def _create_prompt(self, additional_instructions: str = "") -> str:

        prompt = """
Please analyze this sky photo and determine if there are any airplane contrails (condensation trails) or stratiform clouds visible. Do NOT classify other cloud types as contrails.

Key identification points for contrails:
- Linear, straight-line structure
- Clearly man-made appearance - distinct from natural cloud formations
- Usually appear as thin, white lines crossing the sky
- Often appears as diffuse, fuzzy lines
- Multiple lines are often present

Key identification points for stratiform clouds:
- layered appearance
- Uniform, sheet-like structure
- Typically cover large areas of the sky
- May appear as thin, translucent layers or thick, gray blankets
- Generally lack distinct edges or formations
- Often create a uniform overcast appearance
Please pay special attention to faint, thin linear cloud formations that may be present in any part of the image, especially near the edges or corners. Even very subtle, barely visible contrail lines should be identified and included in your analysis.

Return the results in the following JSON format:
{
"total_contrails": 0,  # Use 0 if no actual contrails are present
}
OR, if contrails are present:
{
"total_contrails": 2,
}

Return ONLY a single integer representing the total number of contrails. 
No text, no JSON, just the number.
"""

        # 追加指示がある場合は追加
        if additional_instructions:
            prompt += "\n\n" + additional_instructions
            
        return prompt
    
    def analyze(self, image_path: str, additional_instructions: str = "") -> Dict[str, Any]:
        """
        Qwen APIを使用して画像を分析
        
        Args:
            image_path: 分析する画像のパス
            additional_instructions: プロンプトに追加する指示
            
        Returns:
            Dict[str, Any]: 分析結果
        """
        try:
            # 画像をリサイズしてbase64エンコード
            resized_image_data = self.resize_image(image_path)
            base64_image = self.encode_image(resized_image_data)
            
            # プロンプトを作成
            prompt = self._create_prompt(additional_instructions)
            
            # APIリクエストを送信
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": [{"type": "text", "text": "You are an expert in accurately analyzing sky photographs, specifically distinguishing between natural clouds and airplane contrails."}],
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                },
                            },
                            {"type": "text", "text": prompt},
                        ],
                    },
                ],
                temperature=0  # 決定論的な応答を得るために0に設定
            )
            
            # レスポンスを取得
            response_text = completion.choices[0].message.content
            
            # 結果を返す
            return {
                "image_path": image_path,
                "analysis": response_text,
                # "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            return {
                "image_path": image_path,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
          
import glob
import json
from typing import List, Dict, Any, Optional

class AnalysisManager:
    """複数画像の分析と結果管理を行うクラス"""
    
    def __init__(self, analyzer: ImageAnalyzer, 
                 input_dir: str = "./input", 
                 output_dir: str = "./output"):
        """
        初期化
        
        Args:
            analyzer: 使用する画像分析器
            input_dir: 入力ディレクトリパス
            output_dir: 出力ディレクトリパス
        """
        self.analyzer = analyzer
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.results = []
        
        # ディレクトリが存在しない場合は作成
        os.makedirs(input_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"入力ディレクトリ: {input_dir}")
        print(f"出力ディレクトリ: {output_dir}")
    
    def find_images(self) -> List[str]:
        """
        指定ディレクトリから画像ファイルを検索
        
        Returns:
            List[str]: 検出された画像ファイルパスのリスト
        """
        image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']
        image_paths = []
        
        for ext in image_extensions:
            image_paths.extend(glob.glob(f'{self.input_dir}/*.{ext}'))
            image_paths.extend(glob.glob(f'{self.input_dir}/*.{ext.upper()}'))
            image_paths.extend(glob.glob(f'{self.output_dir}/*.{ext}'))
            image_paths.extend(glob.glob(f'{self.output_dir}/*.{ext.upper()}'))

        return image_paths
    
    def process_images(self, additional_instructions: str = "") -> None:
        """
        すべての画像を処理
        
        Args:
            additional_instructions: 分析に追加する指示
        """
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
    
    def save_results(self) -> str:
        """
        分析結果をJSONファイルに保存
        
        Returns:
            str: 保存したファイルのパス
        """
        if not self.results:
            print("保存する結果がありません。")
            return ""
        
        # タイムスタンプを使用してファイル名を作成
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = os.path.join(self.output_dir, f"cloud_analysis_results_{timestamp}.json")

        # 結果をJSONファイルに保存
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump({"results": self.results}, f, ensure_ascii=False, indent=2)
        
        print(f"すべての解析結果を {result_file} に保存しました。")
        return result_file
        
    def run(self, additional_instructions: str = "") -> str:
        """
        分析プロセス全体を実行
        
        Args:
            additional_instructions: 分析に追加する指示
            
        Returns:
            str: 保存したファイルのパス
        """
        self.process_images(additional_instructions)
        result_file = self.save_results()
        print("すべての処理が完了しました")
        return result_file