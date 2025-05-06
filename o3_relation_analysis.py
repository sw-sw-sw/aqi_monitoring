import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import japanize_matplotlib
import numpy as np
from scipy import stats

output_path = 'data'
# CSVデータを読み込み
df = pd.read_csv('data/kobe_aqi_data.csv')

# 取得時間を日付型に変換
df['取得時間'] = pd.to_datetime(df['取得時間'])
df['日付'] = df['取得時間'].dt.date
df['時間'] = df['取得時間'].dt.hour

# データの前処理（主要汚染物質のデータクレンジング）
# 主要汚染物質が文字列で記録されている場合があるため、数値に変換
df['PM2.5_clean'] = pd.to_numeric(df['PM2.5'], errors='coerce')
df['O3_clean'] = pd.to_numeric(df['O3'], errors='coerce')

# 外れ値のフィルタリング（必要に応じて）
df_filtered = df.dropna(subset=['PM2.5_clean', 'O3_clean'])

# 1. 基本的な相関分析
print("=== PM2.5とO3の相関分析 ===")

# 全データでの相関係数
correlation_all = df_filtered['PM2.5_clean'].corr(df_filtered['O3_clean'])
print(f"全データの相関係数: {correlation_all:.3f}")

# ピアソン相関とスピアマン相関の計算
pearson_corr, pearson_p = stats.pearsonr(df_filtered['PM2.5_clean'], df_filtered['O3_clean'])
spearman_corr, spearman_p = stats.spearmanr(df_filtered['PM2.5_clean'], df_filtered['O3_clean'])

print(f"ピアソン相関係数: {pearson_corr:.3f} (p値: {pearson_p:.3e})")
print(f"スピアマン相関係数: {spearman_corr:.3f} (p値: {spearman_p:.3e})")

# 2. 散布図による可視化
plt.figure(figsize=(16, 12))

# 2-1: 基本的な散布図
plt.subplot(2, 2, 1)
plt.scatter(df_filtered['PM2.5_clean'], df_filtered['O3_clean'], alpha=0.5, color='navy', s=30)
plt.xlabel('PM2.5濃度', fontsize=12)
plt.ylabel('O3濃度', fontsize=12)
plt.title(f'PM2.5とO3の散布図\n相関係数: {correlation_all:.3f}', fontsize=14)
plt.grid(True, alpha=0.3)

# 回帰直線の追加
z = np.polyfit(df_filtered['PM2.5_clean'], df_filtered['O3_clean'], 1)
p = np.poly1d(z)
plt.plot(df_filtered['PM2.5_clean'], p(df_filtered['PM2.5_clean']), "r--", alpha=0.8, linewidth=2, label='回帰直線')
plt.legend()

# 2-2: 時間帯別散布図（ヒートマップ）
plt.subplot(2, 2, 2)
hb = plt.hexbin(df_filtered['PM2.5_clean'], df_filtered['O3_clean'], gridsize=20, cmap='YlOrRd', mincnt=1)
plt.colorbar(hb, label='データ密度')
plt.xlabel('PM2.5濃度', fontsize=12)
plt.ylabel('O3濃度', fontsize=12)
plt.title('PM2.5 vs O3 密度分布', fontsize=14)

# 2-3: 時間帯別の相関プロット
plt.subplot(2, 2, 3)
hourly_corr = []
hours = range(24)
for hour in hours:
    hour_data = df_filtered[df_filtered['時間'] == hour]
    if len(hour_data) > 1:
        corr = hour_data['PM2.5_clean'].corr(hour_data['O3_clean'])
        hourly_corr.append(corr)
    else:
        hourly_corr.append(np.nan)

plt.plot(hours, hourly_corr, 'o-', linewidth=2, markersize=8, color='darkgreen')
plt.axhline(y=0, color='r', linestyle='--', alpha=0.5)
plt.xlabel('時間帯', fontsize=12)
plt.ylabel('相関係数', fontsize=12)
plt.title('時間帯別の相関係数', fontsize=14)
plt.grid(True, alpha=0.3)
plt.xticks(range(0, 24, 2))

# 2-4: 月別の相関プロット
plt.subplot(2, 2, 4)
monthly_corr = df_filtered.groupby(df_filtered['日付'].apply(lambda x: x.month)).apply(
    lambda x: x['PM2.5_clean'].corr(x['O3_clean'])
).reset_index()
monthly_corr.columns = ['月', '相関係数']

plt.bar(monthly_corr['月'], monthly_corr['相関係数'], color=['blue' if x > 0 else 'red' for x in monthly_corr['相関係数']], 
        alpha=0.7, edgecolor='black')
plt.axhline(y=0, color='black', linestyle='-', linewidth=1)
plt.xlabel('月', fontsize=12)
plt.ylabel('相関係数', fontsize=12)
plt.title('月別の相関係数', fontsize=14)
plt.grid(True, axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('data/o3_月別相関係数.png')

# 3. 濃度レベル別の相関分析
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

# PM2.5の濃度区分別
pm25_bins = [0, 35, 50, 75, 100, 150]
pm25_labels = ['良好', '普通', '敏感者有害', '不健全', '非常に不健全']
df_filtered['PM2.5_level'] = pd.cut(df_filtered['PM2.5_clean'], bins=pm25_bins, labels=pm25_labels, right=False)

# O3の濃度区分別
o3_bins = [0, 30, 50, 70, 90, 150]
o3_labels = ['良好', '普通', '敏感者有害', '不健全', '非常に不健全']
df_filtered['O3_level'] = pd.cut(df_filtered['O3_clean'], bins=o3_bins, labels=o3_labels, right=False)

# PM2.5レベル別の散布図
for level in pm25_labels:
    mask = df_filtered['PM2.5_level'] == level
    if mask.sum() > 0:
        ax1.scatter(df_filtered[mask]['PM2.5_clean'], df_filtered[mask]['O3_clean'], 
                   alpha=0.6, label=level, s=40)

ax1.set_xlabel('PM2.5濃度', fontsize=12)
ax1.set_ylabel('O3濃度', fontsize=12)
ax1.set_title('PM2.5濃度レベル別の分布', fontsize=14)
ax1.legend()
ax1.grid(True, alpha=0.3)

# クロス集計表のヒートマップ
cross_tab = pd.crosstab(df_filtered['PM2.5_level'], df_filtered['O3_level'])
sns.heatmap(cross_tab, annot=True, fmt='d', cmap='Blues', ax=ax2)
ax2.set_title('PM2.5とO3の濃度レベル相関', fontsize=14)
ax2.set_xlabel('O3濃度レベル', fontsize=12)
ax2.set_ylabel('PM2.5濃度レベル', fontsize=12)

plt.tight_layout()
plt.savefig('data/o3_PM2.5とO3の濃度レベル相関.png')

# 4. 経時的相関分析（移動平均）
plt.figure(figsize=(16, 8))

# 1時間ごとの平均値
hourly_avg = df_filtered.groupby(df_filtered['取得時間'].dt.floor('H'))[['PM2.5_clean', 'O3_clean']].mean()

# 24時間移動平均
window = 24
rolling_corr = []
dates = []

for i in range(window, len(hourly_avg)):
    window_data = hourly_avg.iloc[i-window:i]
    if len(window_data) > 1:
        corr = window_data['PM2.5_clean'].corr(window_data['O3_clean'])
        rolling_corr.append(corr)
        dates.append(hourly_avg.index[i])

plt.plot(dates, rolling_corr, linewidth=2, color='purple', label='24時間移動相関')
plt.axhline(y=0, color='r', linestyle='--', alpha=0.5)
plt.xlabel('日時', fontsize=12)
plt.ylabel('相関係数', fontsize=12)
plt.title('PM2.5とO3の24時間移動相関', fontsize=14)
plt.grid(True, alpha=0.3)
plt.legend(fontsize=12)
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('data/o3_PM2.5とO3の24時間移動相関.png')

# 5. 相関分析の統計的要約
print("\n=== 詳細な統計分析 ===")
print("\n時間帯別の平均相関:")
valid_hourly_corr = [c for c in hourly_corr if not pd.isna(c)]
if valid_hourly_corr:
    print(f"最高相関: {max(valid_hourly_corr):.3f} (時間: {hourly_corr.index(max(valid_hourly_corr))}時)")
    print(f"最低相関: {min(valid_hourly_corr):.3f} (時間: {hourly_corr.index(min(valid_hourly_corr))}時)")
    print(f"平均相関: {np.mean(valid_hourly_corr):.3f}")

print("\n月別の相関:")
for _, row in monthly_corr.iterrows():
    print(f"{row['月']}月: {row['相関係数']:.3f}")

# 6. 交差相関分析（時差を考慮）
lag_range = range(-6, 7)  # -6時間から+6時間までのタイムラグ
cross_correlations = []

for lag in lag_range:
    shifted_o3 = df_filtered['O3_clean'].shift(lag)
    valid_mask = ~(df_filtered['PM2.5_clean'].isna() | shifted_o3.isna())
    if valid_mask.sum() > 1:
        cross_corr = df_filtered['PM2.5_clean'][valid_mask].corr(shifted_o3[valid_mask])
        cross_correlations.append(cross_corr)
    else:
        cross_correlations.append(np.nan)

plt.figure(figsize=(14, 8))
plt.bar(lag_range, cross_correlations, alpha=0.7, color='teal', edgecolor='black')
plt.axhline(y=0, color='black', linestyle='-', linewidth=1)
plt.xlabel('タイムラグ（時間）', fontsize=12)
plt.ylabel('相関係数', fontsize=12)
plt.title('PM2.5とO3の時差相関分析\n（正のラグ：O3が遅れる、負のラグ：O3が先行）', fontsize=14)
plt.grid(True, axis='y', alpha=0.3)
plt.tight_layout()

plt.savefig('data/o3_時差相関分析.png')

print(f"\n最大相関のタイムラグ: {lag_range[cross_correlations.index(max(cross_correlations))]}時間")
print(f"最大相関係数: {max(cross_correlations):.3f}")


# --------------------------------------------------

# o3_時差相関分析.png
# o3_PM2.5とO3の24時間移動相関
# o3_PM2.5とO3の濃度レベル相関
# o3_月別相関係数