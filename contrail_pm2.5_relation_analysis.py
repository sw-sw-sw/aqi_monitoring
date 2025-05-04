import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import japanize_matplotlib  # 日本語表示のため
from datetime import datetime, timedelta
import seaborn as sns
from scipy import stats
import warnings
import os

# ディレクトリとファイル名の設定
# 更新や再利用の便宜のため、パスを明示的に定義
DATA_DIR = 'data'
input_file_name = 'contrail_timeline_by_qwen.csv'  # 入力ファイル名
output_file_name = 'contrail_pm25_hourly_contrail_counts.csv'  # 出力ファイル名
INPUT_FILE_PATH = os.path.join(DATA_DIR, input_file_name)
OUTPUT_FILE_PATH = os.path.join(DATA_DIR, output_file_name)

# 可視化出力ファイルのパス
CORRELATION_PLOT_PATH = os.path.join(DATA_DIR, 'contrail_pm25_correlation.png')
HOURLY_PATTERNS_PATH = os.path.join(DATA_DIR, 'contrail_pm25_hourly_patterns.png')
HEATMAP_PATH = os.path.join(DATA_DIR, 'contrail_pm25_correlation_heatmap.png')

# AQIデータファイルパス
AQI_DATA_PATH = os.path.join(DATA_DIR, 'kobe_aqi_data.csv')

# 警告を非表示にする
warnings.filterwarnings('ignore')

# コントレイルデータの読み込み
df_contrail = pd.read_csv(INPUT_FILE_PATH)

# AQIデータの読み込み
df_aqi = pd.read_csv(AQI_DATA_PATH)

# ===== コントレイルデータの前処理 =====
# 日時をdatetime型に変換
df_contrail['datetime'] = pd.to_datetime(df_contrail['date'], format='%Y%m%d%H%M%S')

# 時間単位でグループ化して合計を計算
contrail_hourly = df_contrail.groupby(pd.Grouper(key='datetime', freq='H'))['contrail_count'].sum().reset_index()
contrail_hourly['date'] = contrail_hourly['datetime'].dt.date
contrail_hourly['hour'] = contrail_hourly['datetime'].dt.hour

# 日付ごとに集計したデータも作成
contrail_daily = df_contrail.groupby(pd.Grouper(key='datetime', freq='D'))['contrail_count'].sum().reset_index()
contrail_daily['date'] = contrail_daily['datetime'].dt.date

# ===== AQIデータの前処理 =====
# 日時をdatetime型に変換
df_aqi['datetime'] = pd.to_datetime(df_aqi['取得時間'])
df_aqi['date'] = df_aqi['datetime'].dt.date
df_aqi['hour'] = df_aqi['datetime'].dt.hour

# ===== 可視化と分析 =====
# まず、日付範囲を確認
contrail_start = df_contrail['datetime'].min()
contrail_end = df_contrail['datetime'].max()
aqi_start = df_aqi['datetime'].min()
aqi_end = df_aqi['datetime'].max()

# 共通の分析期間を特定
analysis_start = max(contrail_start, aqi_start)
analysis_end = min(contrail_end, aqi_end)

print(f"分析期間を次の範囲に設定します: {analysis_start} から {analysis_end}")

# 期間内のデータのみを使用
df_contrail_filtered = df_contrail[(df_contrail['datetime'] >= analysis_start) & (df_contrail['datetime'] <= analysis_end)]
df_aqi_filtered = df_aqi[(df_aqi['datetime'] >= analysis_start) & (df_aqi['datetime'] <= analysis_end)]

# 時間単位でグループ化して合計を計算（フィルター済みデータを使用）
contrail_hourly = df_contrail_filtered.groupby(pd.Grouper(key='datetime', freq='H'))['contrail_count'].sum().reset_index()
contrail_hourly['date'] = contrail_hourly['datetime'].dt.date
contrail_hourly['hour'] = contrail_hourly['datetime'].dt.hour

# 日付ごとに集計したデータも作成
contrail_daily = df_contrail_filtered.groupby(pd.Grouper(key='datetime', freq='D'))['contrail_count'].sum().reset_index()
contrail_daily['date'] = contrail_daily['datetime'].dt.date

# フィギュアサイズとフォントを設定
plt.figure(figsize=(15, 10))
plt.rcParams.update({'font.size': 12})

# ===== 1. 時系列データの可視化 =====
plt.subplot(2, 1, 1)
# コントレイル検出数の時系列プロット
plt.plot(contrail_hourly['datetime'], contrail_hourly['contrail_count'], 
         marker='o', linestyle='-', label='コントレイル検出数', color='#3366cc')

# 右側のY軸でAQI値をプロット
ax2 = plt.gca().twinx()
ax2.plot(df_aqi_filtered['datetime'], df_aqi_filtered['AQI値'], 
         marker='x', linestyle='-', label='AQI値', color='#ff6600')

# グラフのスタイル設定
plt.title('コントレイル検出数とAQI値の時系列比較')
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=1))
plt.gcf().autofmt_xdate()  # x軸の日付を見やすく回転
plt.grid(True, alpha=0.3)

# 凡例
lines, labels = plt.gca().get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax2.legend(lines + lines2, labels + labels2, loc='upper right')

# ===== 2. 日次データでのコントレイル数とAQI値の相関分析 =====
plt.subplot(2, 1, 2)

# 日付単位でAQIデータを集計（平均値を使用）
aqi_daily = df_aqi_filtered.groupby('date')['AQI値'].mean().reset_index()

# コントレイルとAQIのデータを日付でマージ
merged_daily = pd.merge(contrail_daily, aqi_daily, on='date', how='inner')

# 散布図を描画
plt.scatter(merged_daily['contrail_count'], merged_daily['AQI値'], 
            alpha=0.7, s=80, c='#3366cc', edgecolors='black')

# 相関係数を計算
corr_daily, p_value_daily = stats.pearsonr(merged_daily['contrail_count'], merged_daily['AQI値'])

# 回帰直線を表示
slope, intercept, r_value, p_value, std_err = stats.linregress(
    merged_daily['contrail_count'], merged_daily['AQI値'])
x_values = np.array([merged_daily['contrail_count'].min(), merged_daily['contrail_count'].max()])
y_values = intercept + slope * x_values
plt.plot(x_values, y_values, color='red', 
         label=f'相関係数: {corr_daily:.3f} (p値: {p_value_daily:.3f})')

# グラフのスタイル設定
plt.title('日次でのコントレイル検出数とAQI値の相関関係')
plt.xlabel('コントレイル検出数 (日次合計)')
plt.ylabel('AQI値 (日次平均)')
plt.grid(True, alpha=0.3)
plt.legend()

plt.tight_layout()
plt.savefig(CORRELATION_PLOT_PATH)  # 画像を保存
# plt.show()

# ===== 3. 時間帯別のコントレイル検出数と平均AQI値 =====
plt.figure(figsize=(15, 6))

# 時間帯別のコントレイル合計を計算
hour_contrail = contrail_hourly.groupby('hour')['contrail_count'].sum()

# 時間帯別のAQI平均値を計算
hour_aqi = df_aqi_filtered.groupby('hour')['AQI値'].mean()

# 時間帯別コントレイル検出数のグラフ
ax1 = plt.subplot(1, 2, 1)
plt.bar(hour_contrail.index, hour_contrail.values, color='#3366cc')
plt.title('時間帯別コントレイル検出数 (合計)')
plt.xlabel('時間 (時)')
plt.ylabel('検出数 (合計)')
plt.xticks(range(0, 24))
plt.grid(True, alpha=0.3, axis='y')

# 時間帯別平均AQI値のグラフ
ax2 = plt.subplot(1, 2, 2)
plt.bar(hour_aqi.index, hour_aqi.values, color='#ff6600')
plt.title('時間帯別平均AQI値')
plt.xlabel('時間 (時)')
plt.ylabel('AQI値 (平均)')
plt.xticks(range(0, 24))
plt.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig(HOURLY_PATTERNS_PATH)  # 画像を保存
plt.show()

# ===== 4. 詳細な相関分析とレポート =====
# 時間帯別のコントレイル平均とAQI平均をマージ
hour_contrail_mean = contrail_hourly.groupby('hour')['contrail_count'].mean()

# Align indices of hour_contrail and hour_aqi
hour_contrail = hour_contrail.reindex(range(24), fill_value=0)
hour_aqi = hour_aqi.reindex(range(24), fill_value=np.nan)

hour_data = pd.DataFrame({
    'hour': hour_contrail.index,
    'contrail_sum': hour_contrail.values,
    'contrail_mean': hour_contrail_mean.reindex(range(24), fill_value=0).values,
    'aqi_mean': hour_aqi.values
})

# 時間帯別の相関係数計算
# NaN を含む行を削除
hour_data_cleaned = hour_data.dropna(subset=['contrail_sum', 'aqi_mean'])

hour_corr, hour_p = stats.pearsonr(hour_data_cleaned['contrail_sum'], hour_data_cleaned['aqi_mean'])

# 相関係数をヒートマップで表示
plt.figure(figsize=(10, 8))
# データフレームに相関係数を計算
correlation_data = pd.DataFrame({
    'コントレイル検出数': [1.0, corr_daily, hour_corr],
    'AQI値': [corr_daily, 1.0, hour_corr],
    '時間帯パターン': [hour_corr, hour_corr, 1.0]
})
correlation_data.index = ['コントレイル検出数', 'AQI値', '時間帯パターン']

# ヒートマップで表示
if Falserue:
    sns.heatmap(correlation_data, annot=True, cmap='coolwarm', vmin=-1, vmax=1)
    plt.title('相関係数ヒートマップ')
    plt.tight_layout()
    plt.savefig(HEATMAP_PATH)  # 画像を保存
    # plt.show()

# ===== 5. 解析結果のレポート出力 =====
# 分析期間の確認
analysis_days = (analysis_end - analysis_start).days + 1

# 結果レポートを表示
print("======= AQIとコントレイルの相関関係分析レポート =======")
print(f"分析期間: {analysis_start.date()} から {analysis_end.date()} ({analysis_days}日間)")
print(f"\n1. コントレイル検出の概要:")
print(f"   総検出数: {df_contrail_filtered['contrail_count'].sum()}")
print(f"   検出があった日数: {(contrail_daily['contrail_count'] > 0).sum()}日 / {len(contrail_daily)}日")
print(f"   1日あたりの平均検出数: {df_contrail_filtered['contrail_count'].sum() / len(contrail_daily):.2f}")

print(f"\n2. AQI値の概要:")
print(f"   平均AQI値: {df_aqi_filtered['AQI値'].mean():.2f}")
print(f"   最小AQI値: {df_aqi_filtered['AQI値'].min()} (観測日時: {df_aqi_filtered.loc[df_aqi_filtered['AQI値'].idxmin(), 'datetime']})")
print(f"   最大AQI値: {df_aqi_filtered['AQI値'].max()} (観測日時: {df_aqi_filtered.loc[df_aqi_filtered['AQI値'].idxmax(), 'datetime']})")

print(f"\n3. 相関分析結果:")
print(f"   日次データでの相関係数: {corr_daily:.3f} (p値: {p_value_daily:.3f})")
if p_value_daily < 0.05:
    print(f"   日次での相関は統計的に有意です (p < 0.05)")
else:
    print(f"   日次での相関は統計的に有意ではありません (p > 0.05)")

print(f"   時間帯パターンでの相関係数: {hour_corr:.3f} (p値: {hour_p:.3f})")
if hour_p < 0.05:
    print(f"   時間帯パターンでの相関は統計的に有意です (p < 0.05)")
else:
    print(f"   時間帯パターンでの相関は統計的に有意ではありません (p > 0.05)")

print("\n4. 考察:")
if abs(corr_daily) > 0.5:
    if corr_daily > 0:
        print("   日次データでは、コントレイル検出数とAQI値の間に強い正の相関が見られました。")
        print("   これは、コントレイルの増加が大気質の悪化（AQI値の上昇）と関連している可能性を示唆しています。")
    else:
        print("   日次データでは、コントレイル検出数とAQI値の間に強い負の相関が見られました。")
        print("   これは、コントレイルの増加が大気質の改善（AQI値の低下）と関連している可能性を示唆しています。")
elif abs(corr_daily) > 0.3:
    if corr_daily > 0:
        print("   日次データでは、コントレイル検出数とAQI値の間に中程度の正の相関が見られました。")
    else:
        print("   日次データでは、コントレイル検出数とAQI値の間に中程度の負の相関が見られました。")
else:
    print("   日次データでは、コントレイル検出数とAQI値の間に明確な相関は見られませんでした。")
    
print("\n   ※注意点:")
print("   この分析はあくまで相関関係を示すものであり、因果関係を証明するものではありません。")
print("   他の環境要因（気象条件、季節変動など）も考慮する必要があります。")
print("=================================================")

# CSVとして時間ごとの集計データを保存
# コントレイルとAQIデータを時間単位で結合
aqi_hourly = df_aqi_filtered.groupby(['date', 'hour'])['AQI値'].mean().reset_index()
contrail_hourly_simple = contrail_hourly[['date', 'hour', 'contrail_count']]
hourly_merged = pd.merge(contrail_hourly_simple, aqi_hourly, on=['date', 'hour'], how='outer')
hourly_merged.to_csv(OUTPUT_FILE_PATH, index=False)
print(f"\n時間ごとの集計データを '{output_file_name}' として {DATA_DIR} ディレクトリに保存しました。")