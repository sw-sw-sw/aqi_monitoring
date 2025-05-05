import pandas as pd
import numpy as np

# CSVデータを読み込み
df = pd.read_csv('data/kobe_aqi_data.csv')

# 取得時間を日付型に変換
df['取得時間'] = pd.to_datetime(df['取得時間'])

# 欠損値を処理（例: 0で埋める、または欠損行を削除）
df['O3'] = df['O3'].fillna(0)  # 欠損値を0で埋める場合
# または
# df = df.dropna(subset=['O3'])  # 欠損値を含む行を削除する場合

# 1. まず日付単位での分析
df['日付'] = df['取得時間'].dt.date

# 日ごとのO3最大値を計算
daily_o3_max = df.groupby('日付')['O3'].max().reset_index()

# メインの分析結果
total_days = len(daily_o3_max)
days_over_30 = len(daily_o3_max[daily_o3_max['O3'] > 30])
days_over_50 = len(daily_o3_max[daily_o3_max['O3'] > 50])

# 割合の計算
ratio_over_30 = (days_over_30 / total_days) * 100
ratio_over_50 = (days_over_50 / total_days) * 100

print("=== O3濃度の日ベース分析 ===")
print(f"分析対象期間: {df['日付'].min()} 〜 {df['日付'].max()}")
print(f"全日数: {total_days}日")
print(f"O3が30を超えた日数: {days_over_30}日 ({ratio_over_30:.1f}%)")
print(f"O3が50を超えた日数: {days_over_50}日 ({ratio_over_50:.1f}%)")

# 2. より詳細な月ごとの分析 - 修正版
df['月'] = df['取得時間'].dt.month

# 月ごとの日数ベースの分析
monthly_days = df.groupby(['月', '日付'])['O3'].max().reset_index()
monthly_summary = monthly_days.groupby('月').agg({
    'O3': ['count', 'max', 'mean']
}).reset_index()

# 月ごとの超過日数を計算
over_30_by_month = monthly_days[monthly_days['O3'] > 30].groupby('月').size()
over_50_by_month = monthly_days[monthly_days['O3'] > 50].groupby('月').size()

# 月ごとの合計日数を計算
total_days_by_month = monthly_days.groupby('月').size()

# 超過率の計算（NaNの回避）
monthly_summary['日数'] = total_days_by_month
monthly_summary['O3_max'] = monthly_summary[('O3', 'max')]
monthly_summary['O3_mean'] = monthly_summary[('O3', 'mean')]
monthly_summary['30超過日数'] = over_30_by_month
monthly_summary['50超過日数'] = over_50_by_month

# NaNを0に置換して超過率を計算
monthly_summary['30超過日数'] = monthly_summary['30超過日数'].fillna(0)
monthly_summary['50超過日数'] = monthly_summary['50超過日数'].fillna(0)

monthly_summary['30超過率'] = (monthly_summary['30超過日数'] / monthly_summary['日数'] * 100).round(1)
monthly_summary['50超過率'] = (monthly_summary['50超過日数'] / monthly_summary['日数'] * 100).round(1)

# 不要な列を削除して表示
display_columns = ['月', '日数', 'O3_max', 'O3_mean', '30超過日数', '30超過率', '50超過日数', '50超過率']
result_summary = monthly_summary[display_columns]

print("\n=== 月ごとの詳細分析（日ベース） ===")
print(result_summary)

# 3. O3濃度の全体統計（時間単位データ）
print("\n=== O3濃度の統計サマリー ===")
print(f"最低濃度: {df['O3'].min():.1f}")
print(f"最高濃度: {df['O3'].max():.1f}")
print(f"平均濃度: {df['O3'].mean():.1f}")
print(f"中央値: {df['O3'].median():.1f}")
print(f"標準偏差: {df['O3'].std():.1f}")

# 4. 簡易視覚化のための補足情報
print("\n=== 分布の概要 ===")
print("濃度区分ごとの頻度（日最高値ベース）:")
print(f"  0-29: {len(daily_o3_max[daily_o3_max['O3'] <= 30])}日")
print(f"  30-49: {len(daily_o3_max[(daily_o3_max['O3'] > 30) & (daily_o3_max['O3'] <= 50)])}日")
print(f"  50以上: {len(daily_o3_max[daily_o3_max['O3'] > 50])}日")