import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import japanize_matplotlib  # 日本語フォント対応
import numpy as np

# パラメーター設定
plt.style.use('default')
plt.rcParams['figure.figsize'] = (14, 8)
plt.rcParams['font.family'] = 'IPAexGothic'
    
    # matplotlibのグローバル設定
plt.rcParams['axes.unicode_minus'] = False
# CSVデータを読み込み
df = pd.read_csv('data/kobe_aqi_data.csv')

# 取得時間を日付型に変換
df['取得時間'] = pd.to_datetime(df['取得時間'])
df['日付'] = df['取得時間'].dt.date

# 日ごとのO3最大値を計算
daily_o3_max = df.groupby('日付')['O3'].max().reset_index()
daily_o3_max['日付'] = pd.to_datetime(daily_o3_max['日付'])

# 図1: O3濃度の時系列推移
plt.figure(figsize=(15, 8))
plt.plot(daily_o3_max['日付'], daily_o3_max['O3'], marker='o', markersize=6, 
         linestyle='-', linewidth=1, alpha=0.8, color='navy', label='日最高O3濃度')
plt.axhline(y=30, color='orange', linestyle='--', linewidth=2, label='閾値: 30')
plt.axhline(y=50, color='red', linestyle='--', linewidth=2, label='閾値: 50')
plt.fill_between(daily_o3_max['日付'], 0, 30, alpha=0.3, color='green', label='正常範囲 (0-30)')
plt.fill_between(daily_o3_max['日付'], 30, 50, alpha=0.3, color='yellow', label='要注意範囲 (30-50)')
plt.fill_between(daily_o3_max['日付'], 50, daily_o3_max['O3'].max(), 
                 where=(daily_o3_max['O3'] > 50), alpha=0.3, color='red', label='警戒範囲 (50+)')
plt.title('日最高O3濃度の時系列推移 (2025年4月〜5月)', fontsize=16, pad=20)
plt.xlabel('日付', fontsize=14)
plt.ylabel('O3濃度', fontsize=14)
plt.legend(fontsize=12)
plt.grid(True, alpha=0.3)
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('data/o3_日最高O3濃度の時系列推移.png')

# 図2: O3濃度の分布ヒストグラム
plt.figure(figsize=(14, 8))
bins = np.arange(0, 80, 5)
plt.hist(daily_o3_max['O3'], bins=bins, alpha=0.7, color='skyblue', edgecolor='darkblue')
plt.axvline(x=30, color='orange', linestyle='--', linewidth=3, label='閾値: 30')
plt.axvline(x=50, color='red', linestyle='--', linewidth=3, label='閾値: 50')
plt.title('日最高O3濃度の分布', fontsize=16, pad=20)
plt.xlabel('O3濃度', fontsize=14)
plt.ylabel('日数', fontsize=14)
plt.legend(fontsize=12)
plt.grid(True, axis='y', alpha=0.3)
plt.xticks(bins)
plt.tight_layout()
plt.savefig('data/o3_日最高O3濃度の分布.png')

# 図3: 月ごとの超過状況（円グラフと棒グラフの組み合わせ）
df['月'] = df['取得時間'].dt.month
monthly_days = df.groupby(['月', '日付'])['O3'].max().reset_index()

# 月ごとの集計
monthly_summary = monthly_days.groupby('月').agg({
    'O3': ['count', 'max', 'mean']
}).reset_index()

# 超過日数の計算
over_30_by_month = monthly_days[monthly_days['O3'] > 30].groupby('月').size()
over_50_by_month = monthly_days[monthly_days['O3'] > 50].groupby('月').size()
total_days_by_month = monthly_days.groupby('月').size()

# 図3a: 月ごとの超過状況（棒グラフ）
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

months = [4, 5]
total_counts = [total_days_by_month.get(m, 0) for m in months]
over_30_counts = [over_30_by_month.get(m, 0) for m in months]
over_50_counts = [over_50_by_month.get(m, 0) for m in months]
normal_counts = [t - o30 for t, o30 in zip(total_counts, over_30_counts)]

x = np.arange(len(months))
width = 0.3

ax1.bar(x - width/2, normal_counts, width, label='正常 (0-30)', color='green', alpha=0.7)
ax1.bar(x - width/2, [o30 - o50 for o30, o50 in zip(over_30_counts, over_50_counts)], 
        width, bottom=normal_counts, label='要注意 (30-50)', color='yellow', alpha=0.7)
ax1.bar(x - width/2, over_50_counts, 
        width, bottom=[n + (o30-o50) for n, o30, o50 in zip(normal_counts, over_30_counts, over_50_counts)], 
        label='警戒 (50+)', color='red', alpha=0.7)

ax1.set_ylabel('日数', fontsize=12)
ax1.set_xticks(x)
ax1.set_xticklabels([f'{m}月' for m in months])
ax1.set_title('月ごとの大気質分布', fontsize=14)
ax1.legend()

# 図3b: 全体の超過状況（円グラフ）
total_days = len(daily_o3_max)
days_normal = len(daily_o3_max[daily_o3_max['O3'] <= 30])
days_caution = len(daily_o3_max[(daily_o3_max['O3'] > 30) & (daily_o3_max['O3'] <= 50)])
days_warning = len(daily_o3_max[daily_o3_max['O3'] > 50])

sizes = [days_normal, days_caution, days_warning]
colors = ['green', 'yellow', 'red']
labels = [f'正常\n{days_normal}日 ({days_normal/total_days*100:.1f}%)', 
          f'要注意\n{days_caution}日 ({days_caution/total_days*100:.1f}%)', 
          f'警戒\n{days_warning}日 ({days_warning/total_days*100:.1f}%)']

ax2.pie(sizes, labels=labels, colors=colors, autopct='', startangle=90, 
        wedgeprops={'alpha': 0.7, 'edgecolor': 'black'})
ax2.set_title('O3濃度レベル別の日数分布', fontsize=14)

plt.tight_layout()
plt.savefig('data/o3_O3濃度レベル別の日数分布.png')

# 図4: 箱ひげ図（月ごとのO3濃度分布）
plt.figure(figsize=(12, 8))
box_data = [monthly_days[monthly_days['月'] == m]['O3'].values for m in [4, 5]]
plt.boxplot(box_data, labels=['4月', '5月'], widths=0.6, 
            boxprops={'color': 'navy', 'linewidth': 2},
            whiskerprops={'color': 'navy', 'linewidth': 2},
            capprops={'color': 'navy', 'linewidth': 2},
            medianprops={'color': 'red', 'linewidth': 2})
plt.axhline(y=30, color='orange', linestyle='--', linewidth=2, label='閾値: 30')
plt.axhline(y=50, color='red', linestyle='--', linewidth=2, label='閾値: 50')
plt.ylabel('O3濃度', fontsize=14)
plt.title('月ごとのO3濃度分布（箱ひげ図）', fontsize=16, pad=20)
plt.legend(fontsize=12)
plt.grid(True, axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig('data/o3_月ごとのO3濃度分布.png')

# 数値サマリーの再表示（参考用）
print("=== 分析結果サマリー ===")
print(f"全日数: {total_days}日")
print(f"O3が30を超えた日数: {len(daily_o3_max[daily_o3_max['O3'] > 30])}日 ({len(daily_o3_max[daily_o3_max['O3'] > 30])/total_days*100:.1f}%)")
print(f"O3が50を超えた日数: {len(daily_o3_max[daily_o3_max['O3'] > 50])}日 ({len(daily_o3_max[daily_o3_max['O3'] > 50])/total_days*100:.1f}%)")