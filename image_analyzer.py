import glob
import base64
import json
from datetime import datetime
import anthropic
from PIL import Image
from io import BytesIO
from config import *
import logging
from dotenv import load_dotenv


load_dotenv()
api_key = os.getenv('CLAUDE_API')

# httpxのログレベルをWARNINGに設定してINFOログを抑制
logging.getLogger("httpx").setLevel(logging.WARNING)

client = anthropic.Anthropic(api_key=api_key)

def encode_image(image_data):
    """画像データをbase64エンコードする"""
    return base64.b64encode(image_data).decode('utf-8')

def resize_image(image_path, size=(320, 180)):
    """画像を指定したサイズにリサイズする"""
    try:
        # 画像を開く
        img = Image.open(image_path)
        
        # 画像をリサイズ（アスペクト比を維持しつつ、指定サイズに収まるようにする）
        img.thumbnail(size, Image.LANCZOS)
        
        # 新しい320x180の白い背景画像を作成
        new_img = Image.new("RGB", size, (255, 255, 255))
        
        # リサイズした画像を中央に配置
        position = ((size[0] - img.width) // 2, (size[1] - img.height) // 2)
        new_img.paste(img, position)
        
        # リサイズした画像をバイトストリームに保存
        buffered = BytesIO()
        new_img.save(buffered, format=img.format if img.format else "JPEG")
        return buffered.getvalue()
    
    except Exception as e:
        print(f"画像のリサイズ中にエラーが発生しました: {e}")
        # エラーの場合は元の画像をそのまま読み込む
        with open(image_path, "rb") as image_file:
            return image_file.read()

def analyze_image(image_path):
    """Anthropic APIを使用して画像を解析する"""
    try:
        # 画像をリサイズしてbase64エンコード
        resized_image_data = resize_image(image_path)
        base64_image = encode_image(resized_image_data)
        
        # 画像の形式を取得
        img_extension = os.path.splitext(image_path)[1][1:].lower()
        # 拡張子がない場合やjfif等特殊な拡張子の場合はjpegとして扱う
        
        # jpgの場合はjpegとして扱う（この部分を修正）
        if img_extension == 'jpg':
            img_extension = 'jpeg'
        # その他の非対応拡張子の場合もjpegとして扱う
        elif not img_extension or img_extension not in ['jpeg', 'png', 'gif', 'bmp', 'webp']:
            img_extension = 'jpeg'
        
        # 使用するモデル
        model = "claude-3-haiku-20240307"  # 現在使用しているモデル
        # model = "claude-3-5-sonnet-20240620"  # 現在使用しているモデル
        # Anthropic APIにリクエストを送信
        message = client.messages.create(
            model=model,
            max_tokens=2000,
            temperature=0,  # Set to 0 for deterministic responses
            # system="You are an expert in accurately analyzing sky photographs, specifically distinguishing between natural clouds and airplane contrails (condensation trails). Airplane contrails are characterized by their distinctive linear or occasionally curved paths that are clearly man-made, typically appearing as thin, straight lines across the sky that may expand over time. Natural clouds have irregular, organic shapes formed by atmospheric processes. Only identify actual airplane contrails - do not classify natural clouds, cirrus clouds, or other meteorological phenomena as contrails unless they clearly show the distinctive linear pattern of aircraft origin. If you see no contrails in the image, report zero contrails. Your analysis should be objective and evidence-based.",
            system="You are an expert in accurately analyzing sky photographs, specifically distinguishing between natural clouds and airplane contrails.",

            messages=[
                {
                "role": "user",
                "content": [
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
                    "text": """Please analyze this sky photo and determine if there are any airplane contrails (condensation trails) visible. Do NOT classify natural clouds as contrails.

Key identification points for contrails:
- Linear, straight-line structure
- Clearly man-made appearance - distinct from natural cloud formations
- Usually appear as thin, white lines crossing the sky
- May have a clear starting and ending point visible
- Often appears as diffuse, fuzzy lines
- Multiple lines are often present

Return the results in the following JSON format:
{
"total_contrails": 0,  # Use 0 if no actual contrails are present
"contrails": []  # Empty array if no contrails are found
}

OR, if contrails are present:

{
"total_contrails": 2,
"contrails": [
    {
    "id": 1,
    "thickness": 0.3,  # Scale from 0.1 (extremely thin) to 0.9 (very thick)
    "shape": "linear",  # Either "linear" or "curvilinear"
    "diffusion": 0.2,  # Scale from 0.1 (solid line) to 0.9 (highly diffused)
    }
    # ... additional contrails if present
]
}

Return only the JSON."""
                    }
                ]
                }
            ]
        )
        
        # トークン使用量の取得
        input_tokens = message.usage.input_tokens
        output_tokens = message.usage.output_tokens
        
        # コスト計算（ドル単位）
        input_cost = (input_tokens / 1000000) * MODEL_PRICING[model]["input"]
        output_cost = (output_tokens / 1000000) * MODEL_PRICING[model]["output"]
        total_cost = input_cost + output_cost
        
        # コスト情報を含めて結果を返す
        return {
            "image_path": image_path,
            "analysis": message.content[0].text,
            "timestamp": datetime.now().isoformat(),
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
    
    except Exception as e:
        return {
            "image_path": image_path,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def main(input_dir, output_dir):
    """メイン関数"""
    # photos ディレクトリ内の画像ファイルを検索
    image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']
    image_paths = []
    
    for ext in image_extensions:
        image_paths.extend(glob.glob(f'{input_dir}/*.{ext}'))
        image_paths.extend(glob.glob(f'{output_dir}/*.{ext.upper()}'))

    if not image_paths:
        print("画像ファイルが見つかりませんでした。")
        return
    
    print(f"{len(image_paths)}個の画像ファイルを処理します...\n")
    
    # 結果を格納するリスト
    results = []
    
    # 合計コストの初期化
    total_tokens = {"input": 0, "output": 0, "total": 0}
    total_cost = {"input": 0.0, "output": 0.0, "total": 0.0}
    
    # 各画像を解析
    for i, image_path in enumerate(image_paths, 1):
        print(f"{i}/{len(image_paths)} is processing... {image_path}")
        result = analyze_image(image_path)
        results.append(result)
        
        # 合計トークン数とコストを更新
        if "tokens" in result:
            total_tokens["input"] += result["tokens"]["input"]
            total_tokens["output"] += result["tokens"]["output"]
            total_tokens["total"] += result["tokens"]["total"]
            
            total_cost["input"] += result["cost"]["input"]
            total_cost["output"] += result["cost"]["output"]
            total_cost["total"] += result["cost"]["total"]
        
    
    # 合計コスト情報を結果に追加
    summary = {
        "total_tokens": total_tokens,
        "total_cost": total_cost,
        "currency": "USD"
    }
    
    # 結果をファイルに保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_file = os.path.join(IMAGE_ANALYSIS_DIR, f"image_analysis_results_{timestamp}.json")

    with open(result_file, "w", encoding="utf-8") as f:
        json.dump({"results": results, "summary": summary}, f, ensure_ascii=False, indent=2)
    
    print(f"すべての解析結果を {result_file} に保存しました。")

    # 合計コスト情報を表示
    print("\n" + "=" * 50)
    print(f"API使用トークン合計: {total_tokens['total']:,} トークン")
    print(f"入力トークン: {total_tokens['input']:,} トークン (${total_cost['input']:.6f} USD)")
    print(f"出力トークン: {total_tokens['output']:,} トークン (${total_cost['output']:.6f} USD)")
    print(f"合計コスト: ${total_cost['total']:.6f} USD")
    # 日本円表示
    yen_cost = total_cost['total'] * 142  # Assuming a conversion rate
    print(f"合計コスト: ¥{yen_cost:.2f} JPY")
    
    
    print_contrails_analysis(results)

def print_contrails_analysis(analysis_results):

    import json
    
    # リストが渡された場合は各項目を処理
    if isinstance(analysis_results, list):
        for i, result in enumerate(analysis_results, 1):
            print(f"\nresult #{i}:")
            if "error" in result:
                print(f"  エラー: {result['error']}")
                continue
                
            # 画像パスを表示
            if "image_path" in result:
                print(f"{result['image_path']}")
                
            # 分析結果を取得
            if "analysis" in result:
                try:
                    # 文字列からJSONを解析
                    analysis_data = json.loads(result["analysis"])
                    _print_single_contrail_analysis(analysis_data, result.get("image_path"))
                except json.JSONDecodeError:
                    print("  エラー: 分析結果が有効なJSON形式ではありません")
                    print(f"  生データ: {result['analysis']}")
                except Exception as e:
                    print(f"  エラー: 分析結果の処理中に問題が発生しました: {e}")
    
    # 単一の辞書が渡された場合
    elif isinstance(analysis_results, dict):
        # 通常の分析結果の辞書かチェック
        if "total_contrails" in analysis_results:
            _print_single_contrail_analysis(analysis_results)
        # APIレスポンス形式の辞書の場合
        elif "analysis" in analysis_results:
            try:
                analysis_data = json.loads(analysis_results["analysis"])
                _print_single_contrail_analysis(analysis_data)
            except json.JSONDecodeError:
                print("エラー: 分析結果が有効なJSON形式ではありません")
            except Exception as e:
                print(f"エラー: 分析結果の処理中に問題が発生しました: {e}")
    
    # その他の型の場合
    else:
        print(f"エラー: サポートされていないデータ型です: {type(analysis_results)}")
        
def _print_single_contrail_analysis(data, image_path=None):
    print("=" * 50)
    print(f"\n■ total chemtrails: {data.get('total_contrails', '不明')}")
    if 'contrails' in data and data['contrails']:
        print("\n■ each information:")
        for contrail in data['contrails']:
            print(f"\n  ID #{contrail.get('id', '?')}:")
            print(f"    Shape: {contrail.get('shape', '不明')}")
            print(f"    Thickness: {contrail.get('thickness', '不明')}")
            print(f"    Diffusion: {contrail.get('diffusion', '不明')}")
    else:
        print("\n■ 飛行機雲の詳細情報: なし")
    
    print("\n" + "=" * 50)
   
if __name__ == "__main__":
    input_dir = os.path.join(IMAGE_ANALYSIS_DIR, "input")
    print(f"input_dir: {input_dir}")
    output_dir = os.path.join(IMAGE_ANALYSIS_DIR, "output")
    print(f"output_dir: {output_dir}")
    main(input_dir, output_dir)
    print("すべての処理が完了しました")
