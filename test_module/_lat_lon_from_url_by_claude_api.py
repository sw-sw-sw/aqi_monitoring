import requests
import re
import json
import os
from typing import Dict, Any, Optional, Tuple
from dotenv import load_dotenv
load_dotenv()

class CameraInfoExtractor:
    def __init__(self, api_key: str = None):
        """
        カメラ情報抽出クラスの初期化
        
        Args:
            api_key: Claude APIのキー（環境変数から取得するか直接指定）
        """
        self.api_key = api_key or os.environ.get("CLAUDE_API_KEY")
        if not self.api_key:
            raise ValueError("Claude APIキーが必要です。環境変数CLAUDE_API_KEYに設定するか、初期化時に指定してください。")
        
        self.claude_api_url = "https://api.anthropic.com/v1/messages"
        self.claude_api_version = "2023-06-01"
    
    def fetch_html_source(self, url: str) -> str:
        """
        指定されたURLからHTMLソースを取得
        
        Args:
            url: ウェブサイトのURL
            
        Returns:
            HTMLソース
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # エラーがあれば例外を発生
        
        return response.text
    
    def extract_nuxt_data(self, html_source: str) -> Optional[str]:
        """
        HTMLソースから__NUXT_DATA__タグの内容を抽出
        
        Args:
            html_source: HTMLソース
            
        Returns:
            抽出されたNUXTデータ、または見つからない場合はNone
        """
        nuxt_data_regex = r'<script[^>]*id="__NUXT_DATA__"[^>]*>([\s\S]*?)<\/script>'
        match = re.search(nuxt_data_regex, html_source)
        
        if match:
            return match.group(1)
        return None
    
    def extract_camera_info_using_claude(self, nuxt_data: str) -> Dict[str, Any]:
        """
        Claude APIを使用してNUXTデータから緯度経度とカメラ角度を抽出
        
        Args:
            nuxt_data: NUXTデータの文字列
            
        Returns:
            カメラ情報を含む辞書
        """
        # Claudeに送るプロンプト
        prompt = f"""
        以下のNuxt.jsのシリアライズされたデータから、以下の情報を抽出してください:
        1. 緯度 (latitude)
        2. 経度 (longitude)
        3. カメラの方向や角度に関する情報（"direction"の値）
        
        JSON形式でのみ回答してください。例:
        {{
          "latitude": 35.6895,
          "longitude": 139.6917,
          "direction": 180
        }}
        
        データ:
        {nuxt_data}
        """
        
        # Claude APIにリクエスト
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": self.claude_api_version
        }
        
        data = {
            "model": "claude-3-haiku-20240307",
            # "model": "claude-3-opus-20240229",
            "max_tokens": 1000,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        response = requests.post(self.claude_api_url, headers=headers, json=data)
        response.raise_for_status()
        
        # レスポンスから情報を抽出
        result = response.json()
        assistant_message = result.get("content", [{}])[0].get("text", "")
        
        # JSON部分を抽出して解析
        try:
            # JSONブロックを探す
            json_match = re.search(r'```json\s*(\{[\s\S]*?\})\s*```', assistant_message)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 直接JSONを探す
                json_match = re.search(r'(\{[\s\S]*?\})', assistant_message)
                json_str = json_match.group(1) if json_match else assistant_message
            
            return json.loads(json_str)
        except Exception as e:
            print(f"JSONの解析中にエラーが発生: {e}")
            print(f"Claude からの応答: {assistant_message}")
            return {
                "error": "Claude からの応答を解析できませんでした",
                "raw_response": assistant_message
            }
    
    def get_camera_info(self, url: str) -> Dict[str, Any]:
        """
        URLからカメラ情報を取得するメイン関数
        
        Args:
            url: ライブカメラのURL
            
        Returns:
            カメラの緯度、経度、方向を含む辞書
        """
        try:
            # HTMLソースを取得
            html_source = self.fetch_html_source(url)
            
            # NUXTデータを抽出
            nuxt_data = self.extract_nuxt_data(html_source)
            if not nuxt_data:
                return {"error": "NUXTデータが見つかりませんでした"}

            # Claude APIを使用して情報を抽出
            return self.extract_camera_info_using_claude(nuxt_data)
            
        except Exception as e:
            return {"error": f"処理中にエラーが発生しました: {str(e)}"}

# テストコード
def test_camera_info_extraction():
    # Claude APIキーを環境変数から取得または直接指定
    api_key = os.getenv('CLAUDE_API')

    if not api_key:
        print("環境変数CLAUDE_API_KEYにAPIキーを設定してください")
        return
    
    # テスト対象のURL
    url = "https://weathernews.jp/onebox/livecam/tohoku/akita/7CDDE907C4DE/"
    
    extractor = CameraInfoExtractor(api_key=api_key)
    result = extractor.get_camera_info(url)
    
    print("camera info results:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
if __name__ == "__main__":
    test_camera_info_extraction()