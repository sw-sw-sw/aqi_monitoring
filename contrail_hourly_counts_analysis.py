import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import numpy as np
import japanize_matplotlib  # 日本語表示のため
from config import *
import os

input_file_name = 'contrail_timeline_by_qwen.csv'
output_file_name = 'contrail_hourly_counts.csv'
INPUT_FILE_PATH = os.path.join(DATA_DIR, input_file_name)
OUTPUT_FILE_PATH = os.path.join(DATA_DIR, output_file_name)


# CSVデータを読み込む
df = pd.read_csv(INPUT_FILE_PATH)

# 日時文字列をdatetime型に変換
df['timestamp'] = pd.to_datetime(df['date'], format='%Y%m%d%H%M%S')

# 時間単位でグループ化して合計を計算
hourly_data = df.groupby(pd.Grouper(key='timestamp', freq='H'))['contrail_count'].sum().reset_index()

# 集計したデータをCSVとして保存
hourly_data.to_csv(OUTPUT_FILE_PATH, index=False)
print(f"時間ごとの飛行機雲検出数を {output_file_name} として保存しました。")

# 可視化
plt.figure(figsize=(15, 6))
plt.plot(hourly_data['timestamp'], hourly_data['contrail_count'], marker='o', linestyle='-', color='#3366cc')

# グラフのスタイル設定
plt.title('飛行機雲の1時間ごとの検出数', fontsize=16)
plt.xlabel('日時', fontsize=12)
plt.ylabel('検出数', fontsize=12)
plt.grid(True, alpha=0.3)

# x軸の日付フォーマットを設定
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%S'))
plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=6))
plt.xticks(rotation=45)

# マージンを調整して見やすくする
plt.tight_layout()

# グラフを表示
# plt.show()
# グラフを保存
GRAPH_OUTPUT_PATH = os.path.join(DATA_DIR, 'contrail_hourly_counts.png')  # 画像形式のパスに変更
plt.savefig(GRAPH_OUTPUT_PATH)

# 時間帯別の検出回数を計算（全期間）
df['hour'] = df['timestamp'].dt.hour
hourly_counts = df.groupby('hour')['contrail_count'].sum()

# 時間帯別の検出回数のグラフを作成
plt.figure(figsize=(12, 5))
plt.bar(hourly_counts.index, hourly_counts.values, color='#5599cc')
plt.title('時間帯別の飛行機雲検出回数（全期間）', fontsize=16)
plt.xlabel('時間（時）', fontsize=12)
plt.ylabel('検出回数', fontsize=12)
plt.xticks(range(0, 24))
plt.grid(True, alpha=0.3, axis='y')
plt.tight_layout()
plt.show()

# データの詳細情報
total_detections = df['contrail_count'].sum()
detection_days = df['timestamp'].dt.date.nunique()
max_hour_detection = hourly_counts.max()
max_hour = hourly_counts.idxmax()

print(f'総検出回数: {total_detections}回')
print(f'観測期間: {detection_days}日')
print(f'最も検出が多い時間帯: {max_hour}時 ({max_hour_detection}回)')