import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from scipy import stats
import os
from datetime import datetime
from matplotlib.dates import DateFormatter
import matplotlib.dates as mdates

# 日本語フォント対応（japanize_matplotlibがインストールされている場合）
try:
    import japanize_matplotlib
    has_japanize = True
except ImportError:
    has_japanize = False
    print("注: japanize_matplotlibがインストールされていません。日本語フォントが正しく表示されない可能性があります。")

from config import *  # DATA_DIRを読み込むための設定ファイル

def advanced_analyze_aqi_data():
    # ファイルパス
    file_path = os.path.join(DATA_DIR, "o3_google_api_1month", "o3_by_google_aqi_api.csv")
    
    # ファイルの存在確認
    if not os.path.exists(file_path):
        print(f"エラー: データファイルが見つかりません: {file_path}")
        return
    
    # データの読み込み
    print(f"データファイル: {file_path} を読み込み中...")
    df = pd.read_csv(file_path)
    
    # 空のデータフレームをチェック
    if len(df) == 0:
        print("エラー: データファイルが空です。")
        return
    
    # カラム名を確認
    print("\n--- データカラム ---")
    print(df.columns.tolist())
    
    # 出力ディレクトリの設定
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(DATA_DIR, "o3_google_api_1month", "advanced_analysis")
    os.makedirs(output_dir, exist_ok=True)
    
    # データの前処理
    print("\n--- データの前処理を実行中... ---")
    
    # 日時データの変換
    df['dateTime'] = pd.to_datetime(df['dateTime'])
    df['日付'] = df['dateTime'].dt.date
    df['時間'] = df['dateTime'].dt.hour
    df['月'] = df['dateTime'].dt.month
    df['日'] = df['dateTime'].dt.day
    df['曜日'] = df['dateTime'].dt.dayofweek  # 0:月曜、6:日曜
    
    # 数値型への変換（エラーは欠損値として扱う）
    for column in df.columns:
        if 'concentration' in column:
            df[column] = pd.to_numeric(df[column], errors='coerce')
    
    if 'aqi_value' in df.columns:
        df['aqi_value'] = pd.to_numeric(df['aqi_value'], errors='coerce')
    
    # o3濃度が存在するか確認
    if 'o3_concentration' not in df.columns:
        print("エラー: o3_concentrationカラムが見つかりません。")
        return
    
    # 欠損値の処理
    missing_o3 = df['o3_concentration'].isna().sum()
    missing_ratio = (missing_o3 / len(df)) * 100
    print(f"O3濃度の欠損値: {missing_o3}件 ({missing_ratio:.1f}%)")
    
    # 欠損値を除外したデータセット
    df_cleaned = df.dropna(subset=['o3_concentration'])
    print(f"前処理後の有効データ数: {len(df_cleaned)}件")
    
    # 基本情報の表示
    print("\n--- データ基本情報 ---")
    print(f"データ期間: {df_cleaned['dateTime'].min()} 〜 {df_cleaned['dateTime'].max()}")
    print(f"総データポイント数: {len(df_cleaned)}")
    
    # 日ごとのO3最大値を計算
    daily_o3_max = df_cleaned.groupby('日付')['o3_concentration'].max().reset_index()
    daily_o3_max['日付'] = pd.to_datetime(daily_o3_max['日付'])
    
    # レポートファイル
    report_path = os.path.join(output_dir, f"advanced_analysis_report_{timestamp}.txt")
    
    with open(report_path, 'w', encoding='utf-8') as report_file:
        report_file.write(f"===== Google AQI API O3高度分析レポート ({timestamp}) =====\n\n")
        report_file.write(f"データ期間: {df_cleaned['dateTime'].min()} 〜 {df_cleaned['dateTime'].max()}\n")
        report_file.write(f"総データポイント数: {len(df_cleaned)}件\n\n")
        
        # 1. 図1: O3濃度の時系列推移
        print("\n--- O3濃度の時系列推移を可視化中... ---")
        
        plt.figure(figsize=(15, 8))
        plt.plot(daily_o3_max['日付'], daily_o3_max['o3_concentration'], marker='o', markersize=6, 
                 linestyle='-', linewidth=1, alpha=0.8, color='navy', label='日最高O3濃度')
        plt.axhline(y=30, color='orange', linestyle='--', linewidth=2, label='閾値: 30')
        plt.axhline(y=50, color='red', linestyle='--', linewidth=2, label='閾値: 50')
        plt.fill_between(daily_o3_max['日付'], 0, 30, alpha=0.3, color='green', label='正常範囲 (0-30)')
        plt.fill_between(daily_o3_max['日付'], 30, 50, alpha=0.3, color='yellow', label='要注意範囲 (30-50)')
        plt.fill_between(daily_o3_max['日付'], 50, daily_o3_max['o3_concentration'].max(), 
                         where=(daily_o3_max['o3_concentration'] > 50), alpha=0.3, color='red', label='警戒範囲 (50+)')
        
        plt.title('日最高O3濃度の時系列推移', fontsize=16, pad=20)
        plt.xlabel('日付', fontsize=14)
        plt.ylabel('O3濃度', fontsize=14)
        plt.legend(fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # 日付フォーマットの設定
        ax = plt.gca()
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
        
        # グラフ保存
        time_series_path = os.path.join(output_dir, f"o3_time_series_{timestamp}.png")
        plt.savefig(time_series_path)
        plt.close()
        
        print(f"時系列推移グラフを保存しました: {time_series_path}")
        
        # レポートに基本統計を追加
        report_file.write("===== O3濃度の時系列分析 =====\n")
        report_file.write(f"最低日最高O3濃度: {daily_o3_max['o3_concentration'].min():.1f} ppb\n")
        report_file.write(f"最高日最高O3濃度: {daily_o3_max['o3_concentration'].max():.1f} ppb\n")
        report_file.write(f"平均日最高O3濃度: {daily_o3_max['o3_concentration'].mean():.1f} ppb\n")
        report_file.write(f"中央値日最高O3濃度: {daily_o3_max['o3_concentration'].median():.1f} ppb\n\n")
        
        # 超過日数の分析
        total_days = len(daily_o3_max)
        days_over_30 = len(daily_o3_max[daily_o3_max['o3_concentration'] > 30])
        days_over_50 = len(daily_o3_max[daily_o3_max['o3_concentration'] > 50])
        
        report_file.write(f"分析対象期間の総日数: {total_days}日\n")
        report_file.write(f"O3濃度が30 ppbを超えた日数: {days_over_30}日 ({days_over_30/total_days*100:.1f}%)\n")
        report_file.write(f"O3濃度が50 ppbを超えた日数: {days_over_50}日 ({days_over_50/total_days*100:.1f}%)\n\n")
        
        # 2. O3濃度の分布ヒストグラム
        print("\n--- O3濃度の分布ヒストグラムを作成中... ---")
        
        plt.figure(figsize=(14, 8))
        bins = np.arange(0, daily_o3_max['o3_concentration'].max() + 10, 5)
        plt.hist(daily_o3_max['o3_concentration'], bins=bins, alpha=0.7, color='skyblue', edgecolor='darkblue')
        plt.axvline(x=30, color='orange', linestyle='--', linewidth=3, label='閾値: 30')
        plt.axvline(x=50, color='red', linestyle='--', linewidth=3, label='閾値: 50')
        plt.title('日最高O3濃度の分布', fontsize=16, pad=20)
        plt.xlabel('O3濃度 (ppb)', fontsize=14)
        plt.ylabel('日数', fontsize=14)
        plt.legend(fontsize=12)
        plt.grid(True, axis='y', alpha=0.3)
        plt.xticks(bins)
        plt.tight_layout()
        
        # グラフ保存
        histogram_path = os.path.join(output_dir, f"o3_histogram_{timestamp}.png")
        plt.savefig(histogram_path)
        plt.close()
        
        print(f"ヒストグラムを保存しました: {histogram_path}")
        
        # 3. 月ごとの超過状況
        print("\n--- 月ごとの超過状況を分析中... ---")
        
        # 月ごとの日ベースの分析
        monthly_days = df_cleaned.groupby(['月', '日付'])['o3_concentration'].max().reset_index()
        
        # 月ごとの統計
        monthly_stats = monthly_days.groupby('月')['o3_concentration'].agg([
            'count', 'min', 'max', 'mean', 'median', 'std'
        ]).reset_index()
        
        # 超過日数の計算
        over_30_by_month = monthly_days[monthly_days['o3_concentration'] > 30].groupby('月').size()
        over_50_by_month = monthly_days[monthly_days['o3_concentration'] > 50].groupby('月').size()
        total_days_by_month = monthly_days.groupby('月').size()
        
        # 月ごとの超過率
        monthly_stats['日数'] = monthly_stats['count']
        monthly_stats['30超過日数'] = monthly_stats['月'].map(over_30_by_month).fillna(0).astype(int)
        monthly_stats['50超過日数'] = monthly_stats['月'].map(over_50_by_month).fillna(0).astype(int)
        monthly_stats['30超過率'] = (monthly_stats['30超過日数'] / monthly_stats['日数'] * 100).round(1)
        monthly_stats['50超過率'] = (monthly_stats['50超過日数'] / monthly_stats['日数'] * 100).round(1)
        
        # レポートに月ごとの統計を追加
        report_file.write("===== 月ごとのO3濃度分析 =====\n")
        for _, row in monthly_stats.iterrows():
            month = int(row['月'])
            report_file.write(f"{month}月の統計:\n")
            report_file.write(f"  日数: {row['日数']}日\n")
            report_file.write(f"  最低濃度: {row['min']:.1f} ppb\n")
            report_file.write(f"  最高濃度: {row['max']:.1f} ppb\n")
            report_file.write(f"  平均濃度: {row['mean']:.1f} ppb\n")
            report_file.write(f"  中央値濃度: {row['median']:.1f} ppb\n")
            report_file.write(f"  標準偏差: {row['std']:.1f} ppb\n")
            report_file.write(f"  30 ppb超過日数: {row['30超過日数']}日 ({row['30超過率']}%)\n")
            report_file.write(f"  50 ppb超過日数: {row['50超過日数']}日 ({row['50超過率']}%)\n\n")
        
        # 月ごとの超過状況（棒グラフと円グラフ）
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        # 存在する月のリスト
        months = sorted(monthly_stats['月'].unique())
        
        # 棒グラフデータの準備
        normal_counts = monthly_stats['日数'] - monthly_stats['30超過日数']
        caution_counts = monthly_stats['30超過日数'] - monthly_stats['50超過日数']
        warning_counts = monthly_stats['50超過日数']
        
        # 棒グラフの作成
        bottoms = np.zeros(len(months))
        width = 0.7
        
        # 正常範囲（0-30）
        bars1 = ax1.bar(months, normal_counts, width, label='正常 (0-30)', color='green', alpha=0.7, bottom=bottoms)
        bottoms += normal_counts
        
        # 要注意範囲（30-50）
        bars2 = ax1.bar(months, caution_counts, width, label='要注意 (30-50)', color='yellow', alpha=0.7, bottom=bottoms)
        bottoms += caution_counts
        
        # 警戒範囲（50+）
        bars3 = ax1.bar(months, warning_counts, width, label='警戒 (50+)', color='red', alpha=0.7, bottom=bottoms)
        
        ax1.set_ylabel('日数', fontsize=12)
        ax1.set_xlabel('月', fontsize=12)
        ax1.set_xticks(months)
        ax1.set_xticklabels([f'{m}月' for m in months])
        ax1.set_title('月ごとの大気質分布', fontsize=14)
        ax1.legend()
        
        # 円グラフデータの準備
        total_days = len(daily_o3_max)
        days_normal = len(daily_o3_max[daily_o3_max['o3_concentration'] <= 30])
        days_caution = len(daily_o3_max[(daily_o3_max['o3_concentration'] > 30) & (daily_o3_max['o3_concentration'] <= 50)])
        days_warning = len(daily_o3_max[daily_o3_max['o3_concentration'] > 50])
        
        # 円グラフの作成
        sizes = [days_normal, days_caution, days_warning]
        colors = ['green', 'yellow', 'red']
        labels = [f'正常\n{days_normal}日 ({days_normal/total_days*100:.1f}%)', 
                  f'要注意\n{days_caution}日 ({days_caution/total_days*100:.1f}%)', 
                  f'警戒\n{days_warning}日 ({days_warning/total_days*100:.1f}%)']
        
        ax2.pie(sizes, labels=labels, colors=colors, autopct='', startangle=90, 
                wedgeprops={'alpha': 0.7, 'edgecolor': 'black'})
        ax2.set_title('O3濃度レベル別の日数分布', fontsize=14)
        
        plt.tight_layout()
        
        # グラフ保存
        monthly_path = os.path.join(output_dir, f"o3_monthly_analysis_{timestamp}.png")
        plt.savefig(monthly_path)
        plt.close()
        
        print(f"月ごとの分析グラフを保存しました: {monthly_path}")
        
        # 4. 箱ひげ図（月ごとのO3濃度分布）
        plt.figure(figsize=(12, 8))
        box_data = [monthly_days[monthly_days['月'] == m]['o3_concentration'].values for m in months]
        plt.boxplot(box_data, labels=[f'{m}月' for m in months], widths=0.6, 
                    boxprops={'color': 'navy', 'linewidth': 2},
                    whiskerprops={'color': 'navy', 'linewidth': 2},
                    capprops={'color': 'navy', 'linewidth': 2},
                    medianprops={'color': 'red', 'linewidth': 2})
        plt.axhline(y=30, color='orange', linestyle='--', linewidth=2, label='閾値: 30')
        plt.axhline(y=50, color='red', linestyle='--', linewidth=2, label='閾値: 50')
        plt.ylabel('O3濃度 (ppb)', fontsize=14)
        plt.title('月ごとのO3濃度分布（箱ひげ図）', fontsize=16, pad=20)
        plt.legend(fontsize=12)
        plt.grid(True, axis='y', alpha=0.3)
        plt.tight_layout()
        
        # グラフ保存
        boxplot_path = os.path.join(output_dir, f"o3_monthly_boxplot_{timestamp}.png")
        plt.savefig(boxplot_path)
        plt.close()
        
        print(f"箱ひげ図を保存しました: {boxplot_path}")
        
        # 5. 時間帯別のO3濃度分析
        print("\n--- 時間帯別のO3濃度分析を実行中... ---")
        
        hourly_o3 = df_cleaned.groupby('時間')['o3_concentration'].agg(['mean', 'max', 'min', 'std']).reset_index()
        
        # レポートに時間帯別統計を追加
        report_file.write("===== 時間帯別のO3濃度分析 =====\n")
        for _, row in hourly_o3.iterrows():
            hour = int(row['時間'])
            report_file.write(f"{hour}時の統計:\n")
            report_file.write(f"  平均濃度: {row['mean']:.1f} ppb\n")
            report_file.write(f"  最大濃度: {row['max']:.1f} ppb\n")
            report_file.write(f"  最小濃度: {row['min']:.1f} ppb\n")
            report_file.write(f"  標準偏差: {row['std']:.1f} ppb\n")
        
        # O3濃度の時間帯別パターン
        max_hour = hourly_o3.loc[hourly_o3['max'].idxmax()]['時間']
        max_mean_hour = hourly_o3.loc[hourly_o3['mean'].idxmax()]['時間']
        report_file.write(f"\nO3濃度の最大値が最も高い時間帯: {max_hour}時 ({hourly_o3.loc[hourly_o3['時間'] == max_hour, 'max'].values[0]:.1f} ppb)\n")
        report_file.write(f"O3濃度の平均値が最も高い時間帯: {max_mean_hour}時 ({hourly_o3.loc[hourly_o3['時間'] == max_mean_hour, 'mean'].values[0]:.1f} ppb)\n\n")
        
        # 時間帯別の棒グラフ（平均値と最大値）
        plt.figure(figsize=(14, 8))
        
        # 平均値と最大値の棒グラフ
        bar_width = 0.35
        hours = hourly_o3['時間']
        x = np.arange(len(hours))
        
        plt.bar(x - bar_width/2, hourly_o3['mean'], bar_width, label='平均値', color='skyblue', alpha=0.7)
        plt.bar(x + bar_width/2, hourly_o3['max'], bar_width, label='最大値', color='darkblue', alpha=0.7)
        
        plt.axhline(y=30, color='orange', linestyle='--', linewidth=2, label='閾値: 30')
        plt.axhline(y=50, color='red', linestyle='--', linewidth=2, label='閾値: 50')
        
        plt.xlabel('時間帯', fontsize=14)
        plt.ylabel('O3濃度 (ppb)', fontsize=14)
        plt.title('時間帯別のO3濃度（平均値と最大値）', fontsize=16, pad=20)
        plt.xticks(x, hours)
        plt.legend()
        plt.grid(True, axis='y', alpha=0.3)
        plt.tight_layout()
        
        # グラフ保存
        hourly_path = os.path.join(output_dir, f"o3_hourly_pattern_{timestamp}.png")
        plt.savefig(hourly_path)
        plt.close()
        
        print(f"時間帯別のグラフを保存しました: {hourly_path}")
        
        # 6. 曜日別のO3濃度分析
        print("\n--- 曜日別のO3濃度分析を実行中... ---")
        
        dayofweek_o3 = df_cleaned.groupby('曜日')['o3_concentration'].agg(['mean', 'max', 'min', 'std']).reset_index()
        
        # 曜日名の追加
        dayofweek_names = {0: '月曜日', 1: '火曜日', 2: '水曜日', 3: '木曜日', 4: '金曜日', 5: '土曜日', 6: '日曜日'}
        dayofweek_o3['曜日名'] = dayofweek_o3['曜日'].map(dayofweek_names)
        
        # レポートに曜日別統計を追加
        report_file.write("===== 曜日別のO3濃度分析 =====\n")
        for _, row in dayofweek_o3.iterrows():
            report_file.write(f"{row['曜日名']}の統計:\n")
            report_file.write(f"  平均濃度: {row['mean']:.1f} ppb\n")
            report_file.write(f"  最大濃度: {row['max']:.1f} ppb\n")
            report_file.write(f"  最小濃度: {row['min']:.1f} ppb\n")
            report_file.write(f"  標準偏差: {row['std']:.1f} ppb\n")
        
        # 曜日別の棒グラフ
        plt.figure(figsize=(14, 8))
        
        # 曜日順に並べ替え
        dayofweek_o3 = dayofweek_o3.sort_values('曜日')
        
        # 平均値と最大値の棒グラフ
        bar_width = 0.35
        days = dayofweek_o3['曜日名']
        x = np.arange(len(days))
        
        plt.bar(x - bar_width/2, dayofweek_o3['mean'], bar_width, label='平均値', color='lightgreen', alpha=0.7)
        plt.bar(x + bar_width/2, dayofweek_o3['max'], bar_width, label='最大値', color='darkgreen', alpha=0.7)
        
        plt.axhline(y=30, color='orange', linestyle='--', linewidth=2, label='閾値: 30')
        plt.axhline(y=50, color='red', linestyle='--', linewidth=2, label='閾値: 50')
        
        plt.xlabel('曜日', fontsize=14)
        plt.ylabel('O3濃度 (ppb)', fontsize=14)
        plt.title('曜日別のO3濃度（平均値と最大値）', fontsize=16, pad=20)
        plt.xticks(x, days, rotation=45)
        plt.legend()
        plt.grid(True, axis='y', alpha=0.3)
        plt.tight_layout()
        
        # グラフ保存
        dayofweek_path = os.path.join(output_dir, f"o3_dayofweek_pattern_{timestamp}.png")
        plt.savefig(dayofweek_path)
        plt.close()
        
        print(f"曜日別のグラフを保存しました: {dayofweek_path}")
        
        # 7. 相関分析（他の汚染物質とO3の関係）
        print("\n--- 汚染物質間の相関分析を実行中... ---")
        
        # 汚染物質のカラムを抽出
        pollutant_columns = [col for col in df_cleaned.columns if 'concentration' in col]
        
        # 相関行列の作成
        correlation_df = df_cleaned[pollutant_columns].copy()
        
        # カラム名を簡略化
        column_mapping = {col: col.replace('_concentration', '') for col in pollutant_columns}
        correlation_df = correlation_df.rename(columns=column_mapping)
        
        # 相関行列の計算
        corr_matrix = correlation_df.corr(method='pearson')
        
        # レポートに相関係数を追加
        report_file.write("===== 汚染物質間の相関分析 =====\n")
        for pollutant in corr_matrix.columns:
            if pollutant != 'o3':
                corr_value = corr_matrix.loc['o3', pollutant]
                if not pd.isna(corr_value):
                    report_file.write(f"O3と{pollutant}の相関係数: {corr_value:.3f}\n")
        
        # 相関行列のヒートマップ
        plt.figure(figsize=(12, 10))
        mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
        sns.heatmap(corr_matrix, mask=mask, annot=True, fmt='.2f', cmap='coolwarm', 
                    vmin=-1, vmax=1, square=True, linewidths=0.5)
        plt.title('汚染物質間の相関行列', fontsize=16, pad=20)
        plt.tight_layout()
        
        # グラフ保存
        corr_path = os.path.join(output_dir, f"pollutant_correlation_{timestamp}.png")
        plt.savefig(corr_path)
        plt.close()
        
        print(f"相関行列ヒートマップを保存しました: {corr_path}")
        
        # 8. 散布図による相関の詳細分析
        if 'pm2_5_concentration' in df_cleaned.columns and 'o3_concentration' in df_cleaned.columns:
            print("\n--- O3とPM2.5の相関の詳細分析を実行中... ---")
            
            # O3とPM2.5の相関係数
            o3_pm25_corr = df_cleaned['o3_concentration'].corr(df_cleaned['pm2_5_concentration'])
            
            # ピアソン相関とスピアマン相関の計算
            try:
                pearson_corr, pearson_p = stats.pearsonr(df_cleaned['o3_concentration'].dropna(), 
                                                        df_cleaned['pm2_5_concentration'].dropna())
                spearman_corr, spearman_p = stats.spearmanr(df_cleaned['o3_concentration'].dropna(), 
                                                            df_cleaned['pm2_5_concentration'].dropna())
                
                report_file.write("\n===== O3とPM2.5の詳細相関分析 =====\n")
                report_file.write(f"全データの相関係数: {o3_pm25_corr:.3f}\n")
                report_file.write(f"ピアソン相関係数: {pearson_corr:.3f} (p値: {pearson_p:.3e})\n")
                report_file.write(f"スピアマン相関係数: {spearman_corr:.3f} (p値: {spearman_p:.3e})\n\n")
                
                # 散布図による可視化
                plt.figure(figsize=(16, 12))
                
                # 基本的な散布図
                plt.subplot(2, 2, 1)
                plt.scatter(df_cleaned['pm2_5_concentration'], df_cleaned['o3_concentration'], alpha=0.5, color='navy', s=30)
                plt.xlabel('PM2.5濃度 (μg/m³)', fontsize=12)
                plt.ylabel('O3濃度 (ppb)', fontsize=12)
                plt.title(f'PM2.5とO3の散布図\n相関係数: {o3_pm25_corr:.3f}', fontsize=14)
                plt.grid(True, alpha=0.3)
                
                # 回帰直線の追加
                if len(df_cleaned) > 1:
                    try:
                        z = np.polyfit(df_cleaned['pm2_5_concentration'].dropna(), df_cleaned['o3_concentration'].dropna(), 1)
                        p = np.poly1d(z)
                        x_range = np.linspace(df_cleaned['pm2_5_concentration'].min(), df_cleaned['pm2_5_concentration'].max(), 100)
                        plt.plot(x_range, p(x_range), "r--", alpha=0.8, linewidth=2, label='回帰直線')
                        plt.legend()
                    except Exception as e:
                        print(f"回帰直線の計算中にエラーが発生しました: {str(e)}")
                
                # 時間帯別散布図（ヒートマップ）
                plt.subplot(2, 2, 2)
                try:
                    hb = plt.hexbin(df_cleaned['pm2_5_concentration'], df_cleaned['o3_concentration'], gridsize=20, cmap='YlOrRd', mincnt=1)
                    plt.colorbar(hb, label='データ密度')
                    plt.xlabel('PM2.5濃度 (μg/m³)', fontsize=12)
                    plt.ylabel('O3濃度 (ppb)', fontsize=12)
                    plt.title('PM2.5 vs O3 密度分布', fontsize=14)
                except Exception as e:
                    print(f"ヘキサビンプロットの作成中にエラーが発生しました: {str(e)}")
                    plt.text(0.5, 0.5, '十分なデータがありません', horizontalalignment='center', verticalalignment='center')
                
                # 時間帯別の相関プロット
                plt.subplot(2, 2, 3)
                hourly_corr = []
                hours = range(24)
                for hour in hours:
                    hour_data = df_cleaned[df_cleaned['時間'] == hour]
                    if len(hour_data) > 5:  # 最低5データポイント以上あれば相関を計算
                        corr = hour_data['pm2_5_concentration'].corr(hour_data['o3_concentration'])
                        hourly_corr.append(corr)
                    else:
                        hourly_corr.append(np.nan)
                
                if any(not pd.isna(corr) for corr in hourly_corr):
                    plt.plot(hours, hourly_corr, 'o-', linewidth=2, markersize=8, color='darkgreen')
                    plt.axhline(y=0, color='r', linestyle='--', alpha=0.5)
                    plt.xlabel('時間帯', fontsize=12)
                    plt.ylabel('相関係数', fontsize=12)
                    plt.title('時間帯別の相関係数', fontsize=14)
                    plt.grid(True, alpha=0.3)
                    plt.xticks(range(0, 24, 2))
                    
                    # レポートに時間帯別相関を追加
                    report_file.write("時間帯別の相関係数:\n")
                    for hour, corr in enumerate(hourly_corr):
                        if not pd.isna(corr):
                            report_file.write(f"{hour}時: {corr:.3f}\n")
                    
                    # 相関が最大・最小となる時間帯
                    valid_hourly_corr = [c for c in hourly_corr if not pd.isna(c)]
                    if valid_hourly_corr:
                        max_corr = max(valid_hourly_corr)
                        min_corr = min(valid_hourly_corr)
                        max_hour = hourly_corr.index(max_corr)
                        min_hour = hourly_corr.index(min_corr)
                        
                        report_file.write(f"\n最高相関: {max_corr:.3f} (時間: {max_hour}時)\n")
                        report_file.write(f"最低相関: {min_corr:.3f} (時間: {min_hour}時)\n")
                else:
                    plt.text(0.5, 0.5, '十分なデータがありません', horizontalalignment='center', verticalalignment='center')
                
                # 月別の相関プロット
                plt.subplot(2, 2, 4)
                
                # 月ごとの相関係数を計算
                monthly_corr_data = []
                months = sorted(df_cleaned['月'].unique())
                
                for month in months:
                    month_data = df_cleaned[df_cleaned['月'] == month]
                    if len(month_data) > 5:  # 最低5データポイント以上あれば相関を計算
                        month_corr = month_data['pm2_5_concentration'].corr(month_data['o3_concentration'])
                        monthly_corr_data.append((month, month_corr))
                
                if monthly_corr_data:
                    monthly_corr_df = pd.DataFrame(monthly_corr_data, columns=['月', '相関係数'])
                    
                    plt.bar(monthly_corr_df['月'], monthly_corr_df['相関係数'], 
                            color=['blue' if x > 0 else 'red' for x in monthly_corr_df['相関係数']], 
                            alpha=0.7, edgecolor='black')
                    plt.axhline(y=0, color='black', linestyle='-', linewidth=1)
                    plt.xlabel('月', fontsize=12)
                    plt.ylabel('相関係数', fontsize=12)
                    plt.title('月別の相関係数', fontsize=14)
                    plt.grid(True, axis='y', alpha=0.3)
                    
                    # レポートに月別相関を追加
                    report_file.write("\n月別の相関係数:\n")
                    for _, row in monthly_corr_df.iterrows():
                        report_file.write(f"{int(row['月'])}月: {row['相関係数']:.3f}\n")
                else:
                    plt.text(0.5, 0.5, '十分なデータがありません', horizontalalignment='center', verticalalignment='center')
                
                plt.tight_layout()
                
                # グラフ保存
                scatter_path = os.path.join(output_dir, f"o3_pm25_correlation_{timestamp}.png")
                plt.savefig(scatter_path)
                plt.close()
                
                print(f"PM2.5とO3の相関分析グラフを保存しました: {scatter_path}")
                
                # 9. 濃度レベル別の相関分析
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
                
                # PM2.5の濃度区分別
                pm25_bins = [0, 10, 25, 50, 100, 500]
                pm25_labels = ['良好', '普通', '敏感者影響', '不健全', '非常に不健全']
                
                # O3の濃度区分別
                o3_bins = [0, 30, 50, 80, 120, 500]
                o3_labels = ['良好', '普通', '敏感者影響', '不健全', '非常に不健全']
                
                try:
                    # PM2.5レベルのカテゴリ分け
                    df_cleaned['PM2.5_level'] = pd.cut(df_cleaned['pm2_5_concentration'], bins=pm25_bins, labels=pm25_labels, right=False)
                    
                    # O3レベルのカテゴリ分け
                    df_cleaned['O3_level'] = pd.cut(df_cleaned['o3_concentration'], bins=o3_bins, labels=o3_labels, right=False)
                    
                    # PM2.5レベル別の散布図
                    for level in pm25_labels:
                        mask = df_cleaned['PM2.5_level'] == level
                        if mask.sum() > 0:
                            ax1.scatter(df_cleaned[mask]['pm2_5_concentration'], df_cleaned[mask]['o3_concentration'], 
                                       alpha=0.6, label=level, s=40)
                    
                    ax1.set_xlabel('PM2.5濃度 (μg/m³)', fontsize=12)
                    ax1.set_ylabel('O3濃度 (ppb)', fontsize=12)
                    ax1.set_title('PM2.5濃度レベル別の分布', fontsize=14)
                    ax1.legend()
                    ax1.grid(True, alpha=0.3)
                    
                    # クロス集計表のヒートマップ
                    cross_tab = pd.crosstab(df_cleaned['PM2.5_level'], df_cleaned['O3_level'])
                    sns.heatmap(cross_tab, annot=True, fmt='d', cmap='Blues', ax=ax2)
                    ax2.set_title('PM2.5とO3の濃度レベル相関', fontsize=14)
                    ax2.set_xlabel('O3濃度レベル', fontsize=12)
                    ax2.set_ylabel('PM2.5濃度レベル', fontsize=12)
                    
                    # レポートにクロス集計表を追加
                    report_file.write("\n===== PM2.5とO3の濃度レベル相関 =====\n")
                    report_file.write("各レベルごとのデータポイント数:\n")
                    report_file.write(cross_tab.to_string())
                    report_file.write("\n")
                    
                except Exception as e:
                    print(f"濃度レベル別の分析中にエラーが発生しました: {str(e)}")
                    ax1.text(0.5, 0.5, 'エラーが発生しました', horizontalalignment='center', verticalalignment='center')
                    ax2.text(0.5, 0.5, 'エラーが発生しました', horizontalalignment='center', verticalalignment='center')
                
                plt.tight_layout()
                
                # グラフ保存
                level_path = os.path.join(output_dir, f"o3_pm25_level_correlation_{timestamp}.png")
                plt.savefig(level_path)
                plt.close()
                
                print(f"濃度レベル相関グラフを保存しました: {level_path}")
            except Exception as e:
                print(f"O3とPM2.5の相関分析中にエラーが発生しました: {str(e)}")
                report_file.write(f"\nO3とPM2.5の相関分析中にエラーが発生しました: {str(e)}\n")
                
        # 10. 時差相関分析（PM2.5とO3の時間差関係）
        if 'pm2_5_concentration' in df_cleaned.columns and 'o3_concentration' in df_cleaned.columns:
            print("\n--- PM2.5とO3の時差相関分析を実行中... ---")
            
            try:
                # 時間単位のデータに集約
                hourly_data = df_cleaned.set_index('dateTime')[['pm2_5_concentration', 'o3_concentration']].resample('H').mean()
                
                # 時差範囲の設定
                lag_range = range(-12, 13)  # -12時間から+12時間まで
                cross_correlations = []
                
                for lag in lag_range:
                    shifted_o3 = hourly_data['o3_concentration'].shift(lag)
                    valid_mask = ~(hourly_data['pm2_5_concentration'].isna() | shifted_o3.isna())
                    
                    if valid_mask.sum() > 5:  # 最低5データポイント以上あれば相関を計算
                        cross_corr = hourly_data['pm2_5_concentration'][valid_mask].corr(shifted_o3[valid_mask])
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
                
                # グラフ保存
                lag_path = os.path.join(output_dir, f"o3_pm25_lag_correlation_{timestamp}.png")
                plt.savefig(lag_path)
                plt.close()
                
                print(f"時差相関分析グラフを保存しました: {lag_path}")
                
                # レポートに時差相関を追加
                report_file.write("\n===== PM2.5とO3の時差相関分析 =====\n")
                for lag, corr in zip(lag_range, cross_correlations):
                    if not pd.isna(corr):
                        lag_desc = "O3が遅れる" if lag > 0 else "O3が先行" if lag < 0 else "同時刻"
                        report_file.write(f"ラグ {lag}時間 ({lag_desc}): {corr:.3f}\n")
                
                # 最大相関のタイムラグ
                valid_cross_corr = [c for c in cross_correlations if not pd.isna(c)]
                if valid_cross_corr:
                    max_cross_corr = max(valid_cross_corr)
                    max_lag = lag_range[cross_correlations.index(max_cross_corr)]
                    lag_desc = "O3が遅れる" if max_lag > 0 else "O3が先行" if max_lag < 0 else "同時刻"
                    
                    report_file.write(f"\n最大相関のタイムラグ: {max_lag}時間 ({lag_desc})\n")
                    report_file.write(f"最大相関係数: {max_cross_corr:.3f}\n")
            
            except Exception as e:
                print(f"時差相関分析中にエラーが発生しました: {str(e)}")
                report_file.write(f"\n時差相関分析中にエラーが発生しました: {str(e)}\n")
        
        # 11. 経時的相関分析（移動平均）
        if 'pm2_5_concentration' in df_cleaned.columns and 'o3_concentration' in df_cleaned.columns:
            print("\n--- PM2.5とO3の経時的相関分析（移動平均）を実行中... ---")
            
            try:
                # 時間単位の平均値
                hourly_avg = df_cleaned.set_index('dateTime')[['pm2_5_concentration', 'o3_concentration']].resample('H').mean()
                
                # 24時間移動平均の相関
                window = 24  # 24時間ウィンドウ
                rolling_corr = []
                dates = []
                
                # 十分なデータがあるか確認
                if len(hourly_avg) > window:
                    for i in range(window, len(hourly_avg)):
                        window_data = hourly_avg.iloc[i-window:i]
                        if len(window_data.dropna()) > 5:  # 最低5データポイント以上あれば相関を計算
                            corr = window_data['pm2_5_concentration'].corr(window_data['o3_concentration'])
                            rolling_corr.append(corr)
                            dates.append(hourly_avg.index[i])
                    
                    if rolling_corr and dates:
                        plt.figure(figsize=(16, 8))
                        plt.plot(dates, rolling_corr, linewidth=2, color='purple', label='24時間移動相関')
                        plt.axhline(y=0, color='r', linestyle='--', alpha=0.5)
                        plt.xlabel('日時', fontsize=12)
                        plt.ylabel('相関係数', fontsize=12)
                        plt.title('PM2.5とO3の24時間移動相関', fontsize=14)
                        plt.grid(True, alpha=0.3)
                        plt.legend(fontsize=12)
                        plt.xticks(rotation=45)
                        plt.tight_layout()
                        
                        # グラフ保存
                        rolling_path = os.path.join(output_dir, f"o3_pm25_rolling_correlation_{timestamp}.png")
                        plt.savefig(rolling_path)
                        plt.close()
                        
                        print(f"移動相関グラフを保存しました: {rolling_path}")
                        
                        # レポートに移動相関の統計を追加
                        report_file.write("\n===== PM2.5とO3の24時間移動相関分析 =====\n")
                        if rolling_corr:
                            report_file.write(f"移動相関の最大値: {max(rolling_corr):.3f}\n")
                            report_file.write(f"移動相関の最小値: {min(rolling_corr):.3f}\n")
                            report_file.write(f"移動相関の平均値: {np.mean(rolling_corr):.3f}\n")
                            report_file.write(f"移動相関の標準偏差: {np.std(rolling_corr):.3f}\n")
                    else:
                        print("移動相関の計算に十分なデータがありませんでした。")
                        report_file.write("\n移動相関の計算に十分なデータがありませんでした。\n")
                else:
                    print("移動相関の計算に十分なデータがありませんでした。")
                    report_file.write("\n移動相関の計算に十分なデータがありませんでした。\n")
            
            except Exception as e:
                print(f"移動相関分析中にエラーが発生しました: {str(e)}")
                report_file.write(f"\n移動相関分析中にエラーが発生しました: {str(e)}\n")
                
        # 12. AQI値とO3濃度の関係分析
        if 'aqi_value' in df_cleaned.columns and 'o3_concentration' in df_cleaned.columns:
            print("\n--- AQI値とO3濃度の関係分析を実行中... ---")
            
            try:
                # AQI値とO3濃度の相関係数
                aqi_o3_corr = df_cleaned['aqi_value'].corr(df_cleaned['o3_concentration'])
                
                # 散布図
                plt.figure(figsize=(14, 8))
                plt.scatter(df_cleaned['o3_concentration'], df_cleaned['aqi_value'], alpha=0.6, color='darkblue', s=30)
                
                # 回帰直線
                if len(df_cleaned) > 1:
                    z = np.polyfit(df_cleaned['o3_concentration'].dropna(), df_cleaned['aqi_value'].dropna(), 1)
                    p = np.poly1d(z)
                    x_range = np.linspace(df_cleaned['o3_concentration'].min(), df_cleaned['o3_concentration'].max(), 100)
                    plt.plot(x_range, p(x_range), "r--", alpha=0.8, linewidth=2, label='回帰直線')
                
                plt.xlabel('O3濃度 (ppb)', fontsize=14)
                plt.ylabel('AQI値', fontsize=14)
                plt.title(f'O3濃度とAQI値の関係\n相関係数: {aqi_o3_corr:.3f}', fontsize=16)
                plt.grid(True, alpha=0.3)
                plt.legend()
                plt.tight_layout()
                
                # グラフ保存
                aqi_path = os.path.join(output_dir, f"o3_aqi_relationship_{timestamp}.png")
                plt.savefig(aqi_path)
                plt.close()
                
                print(f"AQI関係グラフを保存しました: {aqi_path}")
                
                # レポートにAQI関係の分析を追加
                report_file.write("\n===== AQI値とO3濃度の関係分析 =====\n")
                report_file.write(f"相関係数: {aqi_o3_corr:.3f}\n")
                
                # 回帰方程式の係数
                report_file.write(f"回帰方程式: AQI = {z[0]:.3f} × O3 + {z[1]:.3f}\n")
                
                # 主要汚染物質の分布
                if 'dominantPollutant' in df_cleaned.columns:
                    dom_pollutant_counts = df_cleaned['dominantPollutant'].value_counts()
                    
                    report_file.write("\n主要汚染物質の分布:\n")
                    for pollutant, count in dom_pollutant_counts.items():
                        ratio = (count / len(df_cleaned)) * 100
                        report_file.write(f"  {pollutant}: {count}件 ({ratio:.1f}%)\n")
                    
                    # O3が主要汚染物質である割合
                    o3_dominant_count = dom_pollutant_counts.get('o3', 0)
                    o3_dominant_ratio = (o3_dominant_count / len(df_cleaned)) * 100 if len(df_cleaned) > 0 else 0
                    report_file.write(f"\nO3が主要汚染物質である割合: {o3_dominant_ratio:.1f}%\n")
                    
                    # 主要汚染物質の円グラフ
                    plt.figure(figsize=(12, 8))
                    dom_pollutant_counts.plot.pie(autopct='%1.1f%%', startangle=90, colors=sns.color_palette("pastel", len(dom_pollutant_counts)),
                                                wedgeprops={'edgecolor': 'black', 'linewidth': 1, 'antialiased': True})
                    plt.title('主要汚染物質の分布', fontsize=16)
                    plt.ylabel('')  # y軸ラベルを非表示に
                    plt.tight_layout()
                    
                    # グラフ保存
                    pollutant_path = os.path.join(output_dir, f"dominant_pollutant_{timestamp}.png")
                    plt.savefig(pollutant_path)
                    plt.close()
                    
                    print(f"主要汚染物質グラフを保存しました: {pollutant_path}")
            
            except Exception as e:
                print(f"AQI関係分析中にエラーが発生しました: {str(e)}")
                report_file.write(f"\nAQI関係分析中にエラーが発生しました: {str(e)}\n")
        
        # 13. O3と気象条件の関係（データがあれば）
        # 注: これは実際のデータに気象条件が含まれている場合のみ実行可能
        
        # 分析完了メッセージ
        print("\n===== 分析が完了しました =====")
        print(f"分析レポートは {report_path} に保存されました。")
        print(f"グラフは {output_dir} ディレクトリに保存されました。")
        
        report_file.write("\n===== 分析完了 =====\n")
        report_file.write(f"分析日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# メイン関数
def main():
    print("Google AQI API データの高度分析を開始します...")
    advanced_analyze_aqi_data()
    print("分析が完了しました。")

if __name__ == "__main__":
    main()