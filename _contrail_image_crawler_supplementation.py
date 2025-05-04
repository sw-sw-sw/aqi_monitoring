import os
import re
import sys
import random
import time
from datetime import datetime, timedelta
import requests
from config import *

def get_timestamp_from_filename(filename):
    """ファイル名からタイムスタンプを抽出する"""
    match = re.match(r'(\d{14})\.jpg', filename)
    if match:
        timestamp_str = match.group(1)
        try:
            return datetime.strptime(timestamp_str, "%Y%m%d%H%M%S")
        except ValueError:
            return None
    return None

def list_existing_files(directory):
    """ディレクトリ内の既存のJPGファイルをリストアップし、タイムスタンプでソートする"""
    files = []
    for filename in os.listdir(directory):
        if filename.endswith('.jpg'):
            timestamp = get_timestamp_from_filename(filename)
            if timestamp:
                files.append((filename, timestamp))
    
    # タイムスタンプでソート
    files.sort(key=lambda x: x[1])
    return files

def generate_expected_timestamps(start_time, end_time, interval_minutes=1):
    """開始時間から終了時間までの間隔ごとのタイムスタンプを生成する"""
    expected_timestamps = []
    current_time = start_time
    
    while current_time <= end_time:
        expected_timestamps.append(current_time)
        current_time += timedelta(minutes=interval_minutes)
    
    return expected_timestamps

def find_missing_files(existing_files, expected_timestamps):
    """欠損ファイルを特定する"""
    existing_timestamps = [file[1] for file in existing_files]
    missing_timestamps = []
    
    for timestamp in expected_timestamps:
        # 00秒を付加して完全な形式に
        timestamp_with_seconds = timestamp.replace(second=0)
        if timestamp_with_seconds not in existing_timestamps:
            missing_timestamps.append(timestamp_with_seconds)
    
    return missing_timestamps

def load_downloaded_history(save_dir):
    """既にダウンロード試行済みの記録を読み込む"""
    history_file = os.path.join(save_dir, "download_history.txt")
    downloaded_timestamps = set()
    
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        parts = line.split(',')
                        if len(parts) >= 2:
                            timestamp_str = parts[0]
                            try:
                                timestamp = datetime.strptime(timestamp_str, "%Y%m%d%H%M%S")
                                downloaded_timestamps.add(timestamp)
                            except ValueError:
                                pass
            print(f"ダウンロード履歴を読み込みました: {len(downloaded_timestamps)}件")
        except Exception as e:
            print(f"ダウンロード履歴の読み込み中にエラーが発生しました: {str(e)}")
    else:
        print("ダウンロード履歴ファイルが見つかりません。新規作成します。")
    
    return downloaded_timestamps

def save_download_history(save_dir, timestamp, success):
    """ダウンロード試行の結果を履歴に保存する"""
    history_file = os.path.join(save_dir, "download_history.txt")
    
    try:
        with open(history_file, 'a') as f:
            timestamp_str = timestamp.strftime('%Y%m%d%H%M%S')
            status = "成功" if success else "失敗"
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"{timestamp_str},{status},{now}\n")
        return True
    except Exception as e:
        print(f"ダウンロード履歴の保存中にエラーが発生しました: {str(e)}")
        return False

def sample_missing_files(missing_timestamps, downloaded_history, sample_size, success_hour=0):
    """未ダウンロードの欠損ファイルからランダムにサンプリングする
    成功例を参考にして、同様の時間帯の画像を優先的に選択"""
    # 未ダウンロードのファイルだけをフィルタリング
    undownloaded_timestamps = [ts for ts in missing_timestamps if ts not in downloaded_history]
    
    if not undownloaded_timestamps:
        print("未ダウンロードの欠損ファイルはありません。")
        return []
    
    print(f"未ダウンロード欠損ファイル: {len(undownloaded_timestamps)}件")
    
    # 優先サンプリング（成功例と同じ時間帯）
    priority_timestamps = [ts for ts in undownloaded_timestamps if ts.hour == success_hour]
    
    if priority_timestamps:
        print(f"優先サンプリング: {success_hour}時台の画像 {len(priority_timestamps)}件")
        # 優先サンプリングから選べる数
        priority_sample_size = min(int(sample_size * 0.7), len(priority_timestamps))
        priority_selected = random.sample(priority_timestamps, priority_sample_size)
        
        # 残りを通常のサンプリングから選択
        remaining_timestamps = [ts for ts in undownloaded_timestamps if ts not in priority_selected]
        remaining_sample_size = min(sample_size - priority_sample_size, len(remaining_timestamps))
        
        if remaining_sample_size > 0 and remaining_timestamps:
            remaining_selected = random.sample(remaining_timestamps, remaining_sample_size)
            sampled_timestamps = priority_selected + remaining_selected
        else:
            sampled_timestamps = priority_selected
    else:
        # 優先サンプリングできない場合は通常のサンプリング
        actual_sample_size = min(sample_size, len(undownloaded_timestamps))
        sampled_timestamps = random.sample(undownloaded_timestamps, actual_sample_size)
    
    return sampled_timestamps



def download_image_with_headers(url, save_path):
    """ランダムなカスタムヘッダーを使用して画像をダウンロードする"""
    # ランダムにヘッダーセットを選択
    header_type = random.choice(list(HEADERS_COLLECTION.keys()))
    headers = HEADERS_COLLECTION[header_type]
    
    print(f"使用するヘッダーセット: {header_type}")
    
    response = requests.get(url, headers=headers, stream=True)
    
    if response.status_code == 200:
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    else:
        print(f"エラー: ステータスコード {response.status_code}")
        return False

def sample_missing_files(missing_timestamps, downloaded_history, sample_size):
    """未ダウンロードの欠損ファイルからランダムにサンプリングする（24時間以内に制限）"""
    # 現在の時刻を取得
    now = datetime.now()
    
    # 24時間前の時刻を計算
    time_limit = now - timedelta(hours=24)
    
    # 24時間以内の未ダウンロードファイルだけをフィルタリング
    recent_undownloaded_timestamps = [
        ts for ts in missing_timestamps 
        if ts >= time_limit and ts not in downloaded_history
    ]
    
    if not recent_undownloaded_timestamps:
        print("24時間以内の未ダウンロード欠損ファイルはありません。")
        return []
    
    print(f"24時間以内の未ダウンロード欠損ファイル: {len(recent_undownloaded_timestamps)}件")
    
    # サンプルサイズが残りの未ダウンロードファイル数を超えないように調整
    actual_sample_size = min(sample_size, len(recent_undownloaded_timestamps))
    
    # ランダムサンプリング
    sampled_timestamps = random.sample(recent_undownloaded_timestamps, actual_sample_size)
    return sampled_timestamps

def download_sampled_files(url_base, save_dir, sampled_timestamps, delay_range=(60, 180)):
    """サンプリングした欠損ファイルをダウンロードする"""
    successful_downloads = 0
    failed_downloads = 0
    
    for i, timestamp in enumerate(sampled_timestamps):
        try:
            # ファイル名とURLを生成
            timestamp_str = timestamp.strftime('%Y%m%d%H%M%S')
            save_path = os.path.join(save_dir, f"{timestamp_str}.jpg")
            
            # WebP形式のURLを生成
            url = f"{url_base}640/{timestamp_str}.webp"
            
            # 進捗表示
            print(f"[{i+1}/{len(sampled_timestamps)}] ダウンロード: {timestamp_str}")
            print(f"Generated URL: {url}")
            
            # ファイルをダウンロード
            success = download_image_with_headers(url, save_path)
            
            if success:
                print(f"Saved: {save_path}")
                successful_downloads += 1
                save_download_history(save_dir, timestamp, True)
            else:
                print(f"Image not found: {url}")
                failed_downloads += 1
                save_download_history(save_dir, timestamp, False)
            
            # 次のダウンロードまで十分に長い待機時間を設ける
            if i < len(sampled_timestamps) - 1:
                delay = random.uniform(delay_range[0], delay_range[1])
                print(f"次のダウンロードまで {delay:.1f}秒待機...")
                time.sleep(delay)
            
        except Exception as e:
            print(f"エラー: {timestamp_str} - {str(e)}")
            failed_downloads += 1
            save_download_history(save_dir, timestamp, False)
    
    return successful_downloads, failed_downloads

def main():
    # 設定
    URL_BASE = 'https://gvs.weathernews.jp/livecam/7CDDE906BA8F/'
    AREA_DIR = 'suma'
    save_dir = os.path.join(IMAGE_CRAWLER_DIR, AREA_DIR)
    
    # ディレクトリが存在することを確認
    if not os.path.exists(save_dir):
        print(f"エラー: ディレクトリ {save_dir} が見つかりません。")
        sys.exit(1)
    
    print(f"=== 欠損画像ファイル検出・24時間以内限定リカバリープログラム ===")
    print(f"対象ディレクトリ: {save_dir}")
    
    # 既存ファイルのリストを取得
    existing_files = list_existing_files(save_dir)
    
    if not existing_files:
        print("ファイルが見つかりません。")
        sys.exit(1)
    
    # 最古と最新のタイムスタンプを取得
    oldest_file, oldest_timestamp = existing_files[0]
    newest_file, newest_timestamp = existing_files[-1]
    
    print(f"検出された最古のファイル: {oldest_file} ({oldest_timestamp})")
    print(f"検出された最新のファイル: {newest_file} ({newest_timestamp})")
    
    # 現在の時刻を取得
    now = datetime.now()
    
    # 24時間前の時刻を計算
    time_limit = now - timedelta(hours=24)
    
    print(f"検索対象期間: {time_limit.strftime('%Y-%m-%d %H:%M')} から {now.strftime('%Y-%m-%d %H:%M')} まで")
    
    # 直近24時間の予想されるタイムスタンプのリストを生成
    # 最新ファイルの時刻から現在までの間にある可能性のあるファイルも含める
    start_time = max(newest_timestamp, time_limit)
    expected_timestamps = generate_expected_timestamps(start_time, now)
    
    print(f"24時間以内で期待されるファイル数: {len(expected_timestamps)}")
    
    # 既存ファイルから24時間以内のものだけを抽出
    recent_existing_files = [(f, ts) for f, ts in existing_files if ts >= time_limit]
    print(f"24時間以内の既存ファイル数: {len(recent_existing_files)}")
    
    # 欠損ファイルを特定
    missing_timestamps = find_missing_files(recent_existing_files, expected_timestamps)
    
    if not missing_timestamps:
        print("24時間以内の欠損ファイルはありません。")
        return
    
    print(f"24時間以内の欠損ファイル数: {len(missing_timestamps)}")
    print(f"24時間以内の欠損率: {len(missing_timestamps) / len(expected_timestamps) * 100:.2f}%")
    
    # ダウンロード履歴の読み込み
    downloaded_history = load_downloaded_history(save_dir)
    
    # アクセス数の設定

    sample_size = 3
    
    # アクセス間隔の設定
    delay_range = (1, 10)
    
    # 24時間以内の欠損ファイルからサンプリング
    sampled_timestamps = sample_missing_files(missing_timestamps, downloaded_history, sample_size)
    
    if not sampled_timestamps:
        print("ダウンロードするファイルがありません。")
        return
    
    print(f"\n{len(sampled_timestamps)}個の24時間以内欠損ファイルがランダムに選択されました。")
    print(f"アクセス間隔: {delay_range[0]:.1f}〜{delay_range[1]:.1f}秒")
    
    # サンプリングされたファイルの表示
    print("\n選択されたファイル:")
    for i, timestamp in enumerate(sampled_timestamps):
        print(f"  {i+1}. {timestamp.strftime('%Y%m%d%H%M%S')} ({timestamp.strftime('%Y-%m-%d %H:%M')})")

    if True:
        print(f"\n{len(sampled_timestamps)}個の欠損ファイルをダウンロードします...")
        successful, failed = download_sampled_files(URL_BASE, save_dir, sampled_timestamps, delay_range)
        print(f"\nダウンロード完了: 成功 {successful}件, 失敗 {failed}件")
        
        # 残りの欠損ファイル数を表示
        remaining_24h = sum(1 for ts in missing_timestamps if ts not in downloaded_history) - successful
        print(f"残りの24時間以内未ダウンロード欠損ファイル: 約{remaining_24h}件")
    else:
        print("ダウンロードをキャンセルしました。")

if __name__ == "__main__":
    main()