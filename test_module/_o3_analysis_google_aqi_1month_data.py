import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
from config import *  # DATA_DIRを読み込むための設定ファイル
import seaborn as sns
from datetime import datetime

def analyze_aqi_data():
    # データファイルのパス
    file_path = os.path.join(DATA_DIR, "o3_google_api_1month", "o3_by_google_aqi_api.csv")
    
    # ファイルの存在確認
    if not os.path.exists(file_path):
        print(f"エラー: データファイルが見つかりません: {file_path}")
        return
    
    # CSVデータを読み込み
    print(f"データファイル: {file_path} を読み込み中...")
    df = pd.read_csv(file_path)
    
    # データの前処理
    print("データの前処理を実行中...")
    
    # 空のデータフレームをチェック
    if len(df) == 0:
        print("エラー: データファイルが空です。")
        return
    
    # カラム名を確認
    print("\n--- データカラム ---")
    print(df.columns.tolist())
    
    # o3_concentrationがデータフレームにあるか確認
    if 'o3_concentration' not in df.columns:
        print("エラー: o3_concentrationカラムが見つかりません。")
        return
    
    # 取得時間を日付型に変換
    df['dateTime'] = pd.to_datetime(df['dateTime'])
    
    # 数値型に変換（エラーは欠損値として扱う）
    df['o3_concentration'] = pd.to_numeric(df['o3_concentration'], errors='coerce')
    
    # 欠損値の数と割合を確認
    missing_count = df['o3_concentration'].isna().sum()
    missing_ratio = (missing_count / len(df)) * 100
    print(f"\n欠損値: {missing_count}件 ({missing_ratio:.1f}%)")
    
    # 欠損値を除外
    df_cleaned = df.dropna(subset=['o3_concentration'])
    print(f"有効データ数: {len(df_cleaned)}件")
    
    # 基本情報の表示
    print("\n--- データ基本情報 ---")
    print(f"データ期間: {df_cleaned['dateTime'].min()} 〜 {df_cleaned['dateTime'].max()}")
    print(f"総データポイント数: {len(df_cleaned)}")
    
    # 日付と時間の情報を追加
    df_cleaned['日付'] = df_cleaned['dateTime'].dt.date
    df_cleaned['月'] = df_cleaned['dateTime'].dt.month
    df_cleaned['時'] = df_cleaned['dateTime'].dt.hour
    
    # ===== 1. O3濃度の日ベース分析 =====
    print("\n===== O3濃度の日ベース分析 =====")
    
    # 日ごとのO3最大値を計算
    daily_o3_max = df_cleaned.groupby('日付')['o3_concentration'].max().reset_index()
    
    # メインの分析結果
    total_days = len(daily_o3_max)
    days_over_30 = len(daily_o3_max[daily_o3_max['o3_concentration'] > 30])
    days_over_50 = len(daily_o3_max[daily_o3_max['o3_concentration'] > 50])
    
    # 割合の計算
    ratio_over_30 = (days_over_30 / total_days) * 100 if total_days > 0 else 0
    ratio_over_50 = (days_over_50 / total_days) * 100 if total_days > 0 else 0
    
    print(f"分析対象期間: {df_cleaned['日付'].min()} 〜 {df_cleaned['日付'].max()}")
    print(f"全日数: {total_days}日")
    print(f"O3が30を超えた日数: {days_over_30}日 ({ratio_over_30:.1f}%)")
    print(f"O3が50を超えた日数: {days_over_50}日 ({ratio_over_50:.1f}%)")
    
    # ===== 2. 月ごとの詳細分析 =====
    print("\n===== 月ごとの詳細分析（日ベース） =====")
    
    # 月ごとの日数ベースの分析
    monthly_days = df_cleaned.groupby(['月', '日付'])['o3_concentration'].max().reset_index()
    
    # 月ごとの集計
    try:
        monthly_summary = monthly_days.groupby('月').agg({
            'o3_concentration': ['count', 'max', 'mean']
        }).reset_index()
        
        # 月ごとの超過日数を計算
        over_30_by_month = monthly_days[monthly_days['o3_concentration'] > 30].groupby('月').size()
        over_50_by_month = monthly_days[monthly_days['o3_concentration'] > 50].groupby('月').size()
        
        # 月ごとの合計日数を計算
        total_days_by_month = monthly_days.groupby('月').size()
        
        # 超過率の計算（NaNの回避）
        monthly_summary['日数'] = total_days_by_month
        monthly_summary['O3_max'] = monthly_summary[('o3_concentration', 'max')]
        monthly_summary['O3_mean'] = monthly_summary[('o3_concentration', 'mean')]
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
        
        print(result_summary)
    except Exception as e:
        print(f"月ごとの分析中にエラーが発生しました: {str(e)}")
    
    # ===== 3. O3濃度の全体統計 =====
    print("\n===== O3濃度の統計サマリー =====")
    print(f"最低濃度: {df_cleaned['o3_concentration'].min():.1f}")
    print(f"最高濃度: {df_cleaned['o3_concentration'].max():.1f}")
    print(f"平均濃度: {df_cleaned['o3_concentration'].mean():.1f}")
    print(f"中央値: {df_cleaned['o3_concentration'].median():.1f}")
    print(f"標準偏差: {df_cleaned['o3_concentration'].std():.1f}")
    
    # ===== 4. 分布の概要 =====
    print("\n===== 分布の概要 =====")
    print("濃度区分ごとの頻度（日最高値ベース）:")
    print(f"  0-29: {len(daily_o3_max[daily_o3_max['o3_concentration'] <= 30])}日")
    print(f"  30-49: {len(daily_o3_max[(daily_o3_max['o3_concentration'] > 30) & (daily_o3_max['o3_concentration'] <= 50)])}日")
    print(f"  50以上: {len(daily_o3_max[daily_o3_max['o3_concentration'] > 50])}日")
    
    # ===== 5. 時間帯別のO3濃度分析 =====
    print("\n===== 時間帯別のO3濃度分析 =====")
    hourly_o3 = df_cleaned.groupby('時')['o3_concentration'].agg(['mean', 'max']).reset_index()
    print(hourly_o3)
    
    # O3濃度の最大値が出現する時間帯
    max_hour = hourly_o3.loc[hourly_o3['max'].idxmax()]['時']
    print(f"\nO3濃度の最大値が最も多く出現する時間帯: {max_hour}時")
    
    # O3濃度の平均値が最も高い時間帯
    max_mean_hour = hourly_o3.loc[hourly_o3['mean'].idxmax()]['時']
    print(f"O3濃度の平均値が最も高い時間帯: {max_mean_hour}時")

    # ===== 6. AQI値とO3濃度の関係分析 =====
    if 'aqi_value' in df.columns:
        print("\n===== AQI値とO3濃度の関係分析 =====")
        
        # 数値型に変換
        df_cleaned['aqi_value'] = pd.to_numeric(df_cleaned['aqi_value'], errors='coerce')
        
        # 相関係数
        correlation = df_cleaned['o3_concentration'].corr(df_cleaned['aqi_value'])
        print(f"O3濃度とAQI値の相関係数: {correlation:.3f}")
        
        # 主要汚染物質の分布
        if 'dominantPollutant' in df.columns:
            dom_pollutant_counts = df_cleaned['dominantPollutant'].value_counts()
            print("\n主要汚染物質の分布:")
            for pollutant, count in dom_pollutant_counts.items():
                ratio = (count / len(df_cleaned)) * 100
                print(f"  {pollutant}: {count}件 ({ratio:.1f}%)")
            
            # O3が主要汚染物質である割合
            o3_dominant_count = dom_pollutant_counts.get('o3', 0)
            o3_dominant_ratio = (o3_dominant_count / len(df_cleaned)) * 100 if len(df_cleaned) > 0 else 0
            print(f"\nO3が主要汚染物質である割合: {o3_dominant_ratio:.1f}%")

    # 結果レポートのファイル保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = os.path.join(DATA_DIR, "o3_google_api_1month", "reports")
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, f"o3_analysis_report_{timestamp}.txt")
    
    # 現在の標準出力をキャプチャして、ファイルに保存
    import sys
    from io import StringIO
    
    # 現在の標準出力を保存
    old_stdout = sys.stdout
    
    # 新しい出力先を設定
    new_stdout = StringIO()
    sys.stdout = new_stdout
    
    # 分析結果を再度出力（ファイル保存用）
    print(f"===== O3濃度分析レポート ({timestamp}) =====")
    print(f"\nデータ期間: {df_cleaned['dateTime'].min()} 〜 {df_cleaned['dateTime'].max()}")
    print(f"総データポイント数: {len(df_cleaned)}")
    
    print("\n===== O3濃度の日ベース分析 =====")
    print(f"全日数: {total_days}日")
    print(f"O3が30を超えた日数: {days_over_30}日 ({ratio_over_30:.1f}%)")
    print(f"O3が50を超えた日数: {days_over_50}日 ({ratio_over_50:.1f}%)")
    
    print("\n===== 月ごとの詳細分析（日ベース） =====")
    try:
        print(result_summary)
    except:
        print("月ごとの詳細分析は利用できません")
    
    print("\n===== O3濃度の統計サマリー =====")
    print(f"最低濃度: {df_cleaned['o3_concentration'].min():.1f}")
    print(f"最高濃度: {df_cleaned['o3_concentration'].max():.1f}")
    print(f"平均濃度: {df_cleaned['o3_concentration'].mean():.1f}")
    print(f"中央値: {df_cleaned['o3_concentration'].median():.1f}")
    print(f"標準偏差: {df_cleaned['o3_concentration'].std():.1f}")
    
    print("\n===== 時間帯別のO3濃度分析 =====")
    print(hourly_o3)
    print(f"\nO3濃度の最大値が最も多く出現する時間帯: {max_hour}時")
    print(f"O3濃度の平均値が最も高い時間帯: {max_mean_hour}時")
    
    # 元の標準出力に戻す
    sys.stdout = old_stdout
    
    # キャプチャした出力をファイルに保存
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(new_stdout.getvalue())
    
    print(f"\n分析レポートを保存しました: {report_path}")
    
    # ===== 7. グラフの作成と保存 =====
    print("\n===== グラフの作成と保存 =====")
    
    # グラフ保存用のディレクトリ
    graphs_dir = os.path.join(DATA_DIR, "o3_google_api_1month", "graphs")
    os.makedirs(graphs_dir, exist_ok=True)
    
    # 日付ごとのO3最大値の時系列グラフ
    plt.rcParams['font.family'] = 'IPAexGothic'
    plt.figure(figsize=(12, 6))
    plt.plot(daily_o3_max['日付'], daily_o3_max['o3_concentration'], marker='o', linestyle='-')
    plt.axhline(y=30, color='r', linestyle='--', alpha=0.7, label='30 ppb 基準線')
    plt.axhline(y=50, color='purple', linestyle='--', alpha=0.7, label='50 ppb 基準線')
    plt.title('日ごとのO3最大濃度の推移')
    plt.ylabel('O3濃度 (ppb)')
    plt.xlabel('日付')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    
    # グラフの保存
    daily_graph_path = os.path.join(graphs_dir, f"daily_o3_max_{timestamp}.png")
    plt.savefig(daily_graph_path)
    print(f"日次グラフを保存しました: {daily_graph_path}")
    
    # 時間帯別のO3平均濃度グラフ
    plt.figure(figsize=(10, 6))
    plt.bar(hourly_o3['時'], hourly_o3['mean'], alpha=0.7)
    plt.title('時間帯別のO3平均濃度')
    plt.ylabel('平均O3濃度 (ppb)')
    plt.xlabel('時間帯')
    plt.grid(True, alpha=0.3, axis='y')
    plt.xticks(range(0, 24))
    plt.tight_layout()
    
    # グラフの保存
    hourly_graph_path = os.path.join(graphs_dir, f"hourly_o3_mean_{timestamp}.png")
    plt.savefig(hourly_graph_path)
    print(f"時間帯別グラフを保存しました: {hourly_graph_path}")
    
    # O3濃度のヒストグラム
    plt.figure(figsize=(10, 6))
    plt.hist(df_cleaned['o3_concentration'], bins=20, alpha=0.7, color='skyblue', edgecolor='black')
    plt.axvline(x=30, color='r', linestyle='--', alpha=0.7, label='30 ppb 基準線')
    plt.axvline(x=50, color='purple', linestyle='--', alpha=0.7, label='50 ppb 基準線')
    plt.title('O3濃度の分布')
    plt.ylabel('頻度')
    plt.xlabel('O3濃度 (ppb)')
    plt.grid(True, alpha=0.3, axis='y')
    plt.legend()
    plt.tight_layout()
    
    # グラフの保存
    hist_graph_path = os.path.join(graphs_dir, f"o3_histogram_{timestamp}.png")
    plt.savefig(hist_graph_path)
    print(f"ヒストグラムを保存しました: {hist_graph_path}")
    
    print("\n分析が完了しました。")

if __name__ == "__main__":
    analyze_aqi_data()