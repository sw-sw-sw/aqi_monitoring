# claude_cost_calculator.py

import os
import json
from datetime import datetime
import anthropic
import logging
from dotenv import load_dotenv
from config import *
# 環境変数の読み込み
load_dotenv()

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# httpxのログレベルをWARNINGに設定してINFOログを抑制
logging.getLogger("httpx").setLevel(logging.WARNING)



# ClaudeのAPI料金（1Mトークンあたりの価格、単位: USD）
# 2025年5月時点の価格（最新価格に更新が必要）
CLAUDE_PRICING = {
    "claude-3-opus-20240229": {
        "input": 15.00,  # $15.00 per 1M input tokens
        "output": 75.00  # $75.00 per 1M output tokens
    },
    "claude-3-sonnet-20240229": {
        "input": 3.00,   # $3.00 per 1M input tokens
        "output": 15.00  # $15.00 per 1M output tokens
    },
    "claude-3-haiku-20240307": {
        "input": 0.25,   # $0.25 per 1M input tokens
        "output": 1.25   # $1.25 per 1M output tokens
    },
    "claude-3-5-sonnet-20240620": {
        "input": 3.00,   # $3.00 per 1M input tokens
        "output": 15.00  # $15.00 per 1M output tokens
    },
    "claude-3-7-sonnet-20240229": {
        "input": 5.00,   # $5.00 per 1M input tokens 
        "output": 20.00  # $20.00 per 1M output tokens
    }
}

class ClaudeCostCalculator:
    """
    Anthropic Claude APIの使用コストを計算するクラス
    """
    
    def __init__(self, api_key=None, model="claude-3-haiku-20240307", log_to_file=True, 
                 log_dir="logs", yen_rate=142.0):
        """
        初期化関数
        
        Args:
            api_key (str, optional): Claude API キー。指定がなければ環境変数から取得
            model (str, optional): 使用するClaudeモデル名
            log_to_file (bool, optional): ログをファイルに保存するかどうか
            log_dir (str, optional): ログを保存するディレクトリ
            yen_rate (float, optional): USDからJPYへの変換レート
        """
        self.api_key = api_key
        if not self.api_key:
            raise ValueError("Claude APIキーが必要です。環境変数CLAUDE_API_KEYに設定するか、初期化時に指定してください。")
        
        self.model = model
        self.log_to_file = log_to_file
        self.log_dir = log_dir
        self.yen_rate = yen_rate
        
        # ログディレクトリがない場合は作成
        if self.log_to_file and not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        # クライアントの初期化
        self.client = anthropic.Anthropic(api_key=self.api_key)
        
        # 結果を格納するリスト
        self.results = []
        
        # 合計トークン数とコスト
        self.total_tokens = {"input": 0, "output": 0, "total": 0}
        self.total_cost = {"input": 0.0, "output": 0.0, "total": 0.0}
    
    def send_text_request(self, prompt, system_prompt=None, max_tokens=2000, temperature=0):
        """
        テキストリクエストを送信してコストを計算
        
        Args:
            prompt (str): ユーザーからのプロンプト
            system_prompt (str, optional): システムプロンプト
            max_tokens (int, optional): 最大出力トークン数
            temperature (float, optional): モデルの温度パラメータ
            
        Returns:
            dict: レスポンスとコスト情報を含む辞書
        """
        try:
            # リクエストパラメータの準備
            request_params = {
                "model": self.model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            # システムプロンプトが指定されている場合は追加
            if system_prompt:
                request_params["system"] = system_prompt
            
            # APIリクエストの送信
            message = self.client.messages.create(**request_params)
            
            # コストの計算
            cost_info = self._calculate_cost(message)
            
            # 結果の整形
            result = {
                "type": "text",
                "prompt": prompt,
                "response": message.content[0].text,
                "timestamp": datetime.now().isoformat(),
                "tokens": cost_info["tokens"],
                "cost": cost_info["cost"]
            }
            
            # 結果をリストに追加
            self.results.append(result)
            
            # 合計を更新
            self._update_totals(cost_info)
            
            return result
        
        except Exception as e:
            error_result = {
                "type": "text",
                "prompt": prompt,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            self.results.append(error_result)
            logger.error(f"APIリクエスト中にエラーが発生しました: {e}")
            return error_result
    
    def send_multimodal_request(self, text_content, image_data=None, image_path=None, 
                               system_prompt=None, max_tokens=2000, temperature=0):
        """
        マルチモーダルリクエスト（テキスト＋画像）を送信してコストを計算
        
        Args:
            text_content (str): テキストコンテンツ
            image_data (bytes, optional): 画像のバイナリデータ
            image_path (str, optional): 画像ファイルのパス
            system_prompt (str, optional): システムプロンプト
            max_tokens (int, optional): 最大出力トークン数
            temperature (float, optional): モデルの温度パラメータ
            
        Returns:
            dict: レスポンスとコスト情報を含む辞書
        """
        try:
            # 画像データの準備
            if image_path and not image_data:
                with open(image_path, "rb") as f:
                    image_data = f.read()
            
            if not image_data:
                raise ValueError("画像データまたは画像パスが必要です")
            
            # 画像をbase64エンコード
            import base64
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            # 画像の拡張子を取得
            img_extension = "jpeg"  # デフォルト
            if image_path:
                ext = os.path.splitext(image_path)[1][1:].lower()
                if ext == 'jpg':
                    img_extension = 'jpeg'
                elif ext in ['png', 'gif', 'webp']:
                    img_extension = ext
            
            # メッセージの作成
            content = [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": f"image/{img_extension}",
                        "data": base64_image
                    }
                },
                {
                    "type": "text",
                    "text": text_content
                }
            ]
            
            # リクエストパラメータの準備
            request_params = {
                "model": self.model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [
                    {
                        "role": "user",
                        "content": content
                    }
                ]
            }
            
            # システムプロンプトが指定されている場合は追加
            if system_prompt:
                request_params["system"] = system_prompt
            
            # APIリクエストの送信
            message = self.client.messages.create(**request_params)
            
            # コストの計算
            cost_info = self._calculate_cost(message)
            
            # 結果の整形
            result = {
                "type": "multimodal",
                "text_content": text_content,
                "image_path": image_path if image_path else "from_data",
                "response": message.content[0].text,
                "timestamp": datetime.now().isoformat(),
                "tokens": cost_info["tokens"],
                "cost": cost_info["cost"]
            }
            
            # 結果をリストに追加
            self.results.append(result)
            
            # 合計を更新
            self._update_totals(cost_info)
            
            return result
        
        except Exception as e:
            error_result = {
                "type": "multimodal",
                "text_content": text_content,
                "image_path": image_path if image_path else "from_data",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            self.results.append(error_result)
            logger.error(f"マルチモーダルリクエスト中にエラーが発生しました: {e}")
            return error_result
    
    def _calculate_cost(self, message):
        """
        APIレスポンスからトークン使用量とコストを計算
        
        Args:
            message: Anthropic APIからのレスポンス
            
        Returns:
            dict: トークン使用量とコスト情報
        """
        # トークン使用量の取得
        input_tokens = message.usage.input_tokens
        output_tokens = message.usage.output_tokens
        
        # モデルの料金設定を取得
        pricing = CLAUDE_PRICING.get(self.model, {
            "input": 1.0,  # デフォルト値
            "output": 5.0  # デフォルト値
        })
        
        # コスト計算（ドル単位）
        input_cost = (input_tokens / 1000000) * pricing["input"]
        output_cost = (output_tokens / 1000000) * pricing["output"]
        total_cost = input_cost + output_cost
        
        return {
            "tokens": {
                "input": input_tokens,
                "output": output_tokens,
                "total": input_tokens + output_tokens
            },
            "cost": {
                "input": input_cost,
                "output": output_cost,
                "total": total_cost,
                "currency": "USD"
            }
        }
    
    def _update_totals(self, cost_info):
        """
        合計トークン数とコストを更新
        
        Args:
            cost_info (dict): 計算されたコスト情報
        """
        self.total_tokens["input"] += cost_info["tokens"]["input"]
        self.total_tokens["output"] += cost_info["tokens"]["output"]
        self.total_tokens["total"] += cost_info["tokens"]["total"]
        
        self.total_cost["input"] += cost_info["cost"]["input"]
        self.total_cost["output"] += cost_info["cost"]["output"]
        self.total_cost["total"] += cost_info["cost"]["total"]
    
    def get_summary(self):
        """
        使用状況の要約を取得
        
        Returns:
            dict: 要約情報
        """
        return {
            "total_requests": len(self.results),
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "total_cost_jpy": self.total_cost["total"] * self.yen_rate,
            "currency": {
                "usd": "USD",
                "jpy": "JPY"
            },
            "exchange_rate": f"1 USD = {self.yen_rate} JPY"
        }
    
    def save_results(self, filename=None):
        """
        結果をJSONファイルに保存
        
        Args:
            filename (str, optional): 保存先のファイル名
            
        Returns:
            str: 保存したファイルのパス
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"claude_api_results_{timestamp}.json"
        
        file_path = os.path.join(self.log_dir, filename)
        
        # 要約の作成
        summary = self.get_summary()
        
        # 結果の保存
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump({
                "results": self.results,
                "summary": summary
            }, f, ensure_ascii=False, indent=2)
        
        logger.info(f"結果を {file_path} に保存しました。")
        return file_path
    
    def print_summary(self):
        """
        使用状況の要約を表示
        """
        summary = self.get_summary()
        
        print("\n" + "=" * 50)
        print(f"リクエスト数: {summary['total_requests']}")
        print(f"API使用トークン合計: {summary['total_tokens']['total']:,} トークン")
        print(f"入力トークン: {summary['total_tokens']['input']:,} トークン (${summary['total_cost']['input']:.6f} USD)")
        print(f"出力トークン: {summary['total_tokens']['output']:,} トークン (${summary['total_cost']['output']:.6f} USD)")
        print(f"合計コスト: ${summary['total_cost']['total']:.6f} USD")
        print(f"合計コスト: ¥{summary['total_cost_jpy']:.2f} JPY")
        print("=" * 50)
    
    def reset_counters(self):
        """
        カウンターをリセット
        """
        self.results = []
        self.total_tokens = {"input": 0, "output": 0, "total": 0}
        self.total_cost = {"input": 0.0, "output": 0.0, "total": 0.0}
        logger.info("カウンターをリセットしました。")


# 使用例
def demo():

    
    """
    使用例の実行
    """

    api_key = os.getenv("CLAUDE_API")
    # カリキュレータの初期化
    calculator = ClaudeCostCalculator(api_key=api_key,  
                                      model='claude-3-haiku-20240307', 
                                      log_to_file=True,
                                        log_dir=LOG_DIR,
                                        yen_rate=142.0)
    
    # テキストリクエストの例
    text_result = calculator.send_text_request(
        prompt="こんにちは、私はAIについて学んでいます。AIの倫理についてわかりやすく説明してください。",
        system_prompt="あなたは親切なAIアシスタントです。簡潔で分かりやすい日本語で回答してください。"
    )
    print("\nテキストリクエスト結果:")
    print(f"レスポンス: {text_result['response'][:100]}...")
    print(f"トークン: 入力 {text_result['tokens']['input']}, 出力 {text_result['tokens']['output']}")
    print(f"コスト: ${text_result['cost']['total']:.6f} USD")
    
    # 要約を表示
    calculator.print_summary()
    
    # 結果を保存
    calculator.save_results()
    
    print("\nデモ完了")

if __name__ == "__main__":
    demo()