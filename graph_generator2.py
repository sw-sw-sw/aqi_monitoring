import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import fftpack
import matplotlib.dates as mdates
from datetime import datetime
import matplotlib.font_manager as fm
import os
from sklearn.preprocessing import StandardScaler
from scipy.signal import find_peaks

def setup_japanese_font():
    plt.rcParams['font.family'] = 'IPAexGothic'
    plt.rcParams['axes.unicode_minus'] = False
    return 'IPAexGothic'

def load_and_preprocess_data(file_path):
    df = pd.read_csv(file_path, encoding='utf-8-sig')
    df['取得時間'] = pd.to_datetime(df['取得時間'])
    numeric_columns = ['AQI値', 'PM2.5', 'PM10', 'O3', 'NO2', '温度', '湿度', '気圧', '風速', '降水量']
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].replace('non', pd.NA), errors='coerce')
    df_numeric = df[['取得時間'] + [col for col in numeric_columns if col in df.columns]]
    df_numeric = df_numeric.set_index('取得時間')
    df_resampled = df_numeric.resample('h').mean()
    df_resampled = df_resampled.interpolate(method='linear')
    return df_resampled

def fourier_transform(data, sampling_freq=1.0):
    if isinstance(data, pd.Series):
        data = data.dropna().values
    n = len(data)
    if n < 4:
        return np.array([]), np.array([]), np.array([])
    data_normalized = data - np.mean(data)
    fft_result = fftpack.fft(data_normalized)
    freqs = fftpack.fftfreq(n, d=1/sampling_freq)[:n//2]
    amplitudes = 2.0/n * np.abs(fft_result)[:n//2]
    phases = np.angle(fft_result)[:n//2]
    return freqs, amplitudes, phases

def find_dominant_frequencies(freqs, amplitudes, n_peaks=5, min_dist=1):
    """
    振幅スペクトルから主要な周波数成分を特定
    
    Args:
        freqs (np.array): 周波数配列
        amplitudes (np.array): 振幅スペクトル配列
        n_peaks (int): 抽出するピークの数
        min_dist (int): ピーク間の最小距離
    
    Returns:
        tuple: (主要周波数配列, 対応する振幅配列)
    """
    # データが空の場合は空の配列を返す
    if len(freqs) == 0 or len(amplitudes) == 0:
        return np.array([]), np.array([])
    
    # 直流成分（ゼロ周波数）を除外
    start_idx = 1 if len(freqs) > 0 and freqs[0] < 1e-10 else 0
    
    # ピークを検出するのに十分なデータがあることを確認
    if len(amplitudes[start_idx:]) < min_dist + 1:
        return np.array([]), np.array([])
    
    # ピーク検出
    peaks, _ = find_peaks(amplitudes[start_idx:], distance=min_dist)
    
    # ピークが見つからない場合は空の配列を返す
    if len(peaks) == 0:
        return np.array([]), np.array([])
    
    # ピークのインデックスを振幅でソート
    sorted_peak_indices = sorted(peaks, key=lambda i: amplitudes[i+start_idx], reverse=True)
    
    # 上位n_peaksのピークを選択
    top_indices = sorted_peak_indices[:min(n_peaks, len(sorted_peak_indices))]
    
    # インデックスを適切に調整
    top_indices = [i + start_idx for i in top_indices]
    
    # 周波数と振幅を抽出
    dominant_freqs = freqs[top_indices]
    dominant_amps = amplitudes[top_indices]
    
    return dominant_freqs, dominant_amps

def reconstruct_signal(data, dominant_freqs, sampling_freq=1.0, n_points=None):
    """
    主要な周波数成分から信号を再構成
    
    Args:
        data (np.array): 元の時系列データ
        dominant_freqs (np.array): 主要周波数配列
        sampling_freq (float): サンプリング周波数
        n_points (int, optional): 再構成するデータ点数
    
    Returns:
        np.array: 再構成された信号
    """
    # 主要周波数が空の場合は元のデータを返す
    if len(dominant_freqs) == 0:
        if isinstance(data, pd.Series):
            return data.values
        return data
    
    if n_points is None:
        if isinstance(data, pd.Series):
            n_points = len(data.dropna())
        else:
            n_points = len(data)
    
    # 平均を引いてトレンドを削除
    if isinstance(data, pd.Series):
        data_clean = data.dropna().values
        if len(data_clean) == 0:
            return np.zeros(n_points)
        data_normalized = data_clean - np.mean(data_clean)
    else:
        if len(data) == 0:
            return np.zeros(n_points)
        data_normalized = data - np.mean(data)
    
    # FFTの実行
    fft_result = fftpack.fft(data_normalized)
    
    # 周波数軸
    freqs = fftpack.fftfreq(len(data_normalized), d=1/sampling_freq)
    
    # 0に初期化した新しいFFT結果
    filtered_fft = np.zeros_like(fft_result, dtype=complex)
    
    # 主要周波数のみを保持
    for freq in dominant_freqs:
        # 最も近い周波数インデックスを見つける
        idx = np.argmin(np.abs(freqs - freq))
        neg_idx = np.argmin(np.abs(freqs + freq))  # 負の周波数も保持
        
        # その周波数成分を保持
        filtered_fft[idx] = fft_result[idx]
        filtered_fft[neg_idx] = fft_result[neg_idx]
    
    # 逆FFTで信号を再構成
    reconstructed = fftpack.ifft(filtered_fft)
    
    # 実部のみを取り出し、元の平均値を加算
    if isinstance(data, pd.Series):
        return np.real(reconstructed) + np.mean(data_clean)
    else:
        return np.real(reconstructed) + np.mean(data)

def hours_to_period_label(hours):
    """
    時間を周期ラベルに変換
    
    Args:
        hours (float): 時間（単位：時間）
    
    Returns:
        str: 周期ラベル
    """
    if hours >= 24:
        days = hours / 24
        if days >= 7:
            weeks = days / 7
            return f"{weeks:.1f}週間"
        else:
            return f"{days:.1f}日"
    else:
        return f"{hours:.1f}時間"

def create_fourier_analysis_visualization(df, output_path='fourier_analysis.png'):
    """
    フーリエ解析を行い、結果を可視化する関数
    
    Args:
        df (pd.DataFrame): 前処理されたデータフレーム
        output_path (str): 出力画像のパス
    """
    # 日本語フォントの設定
    japanese_font = setup_japanese_font()
    
    # 解析対象のパラメータ
    parameters = ['AQI値', 'PM2.5', 'PM10', 'O3', 'NO2']
    
    # 実際に存在するパラメータのみをフィルタリング
    parameters = [p for p in parameters if p in df.columns]
    
    # データがない場合の処理
    if not parameters:
        print("解析対象のパラメータがデータフレームに存在しません。")
        return
    
    # グラフのスタイル設定
    plt.style.use('ggplot')
    
    # カラーパレット
    color_palette = {
        'AQI値': '#FF9500',
        'PM2.5': '#FF5733',
        'PM10': '#C70039',
        'O3': '#44BD32',
        'NO2': '#3498DB',
    }
    
    # 各パラメータに対してフーリエ解析を行う
    fig = plt.figure(figsize=(18, 5 * len(parameters)), dpi=300)
    
    # グリッド設定
    gs = fig.add_gridspec(len(parameters), 3, hspace=0.4, wspace=0.3)
    
    # タイトル設定
    fig.suptitle('神戸市須磨区 大気質データのフーリエ解析', fontsize=20, fontweight='bold', fontname='IPAexGothic')
    
    # 各パラメータに対して処理
    for i, param in enumerate(parameters):
        if param in df.columns:
            # データの取得
            data = df[param]
            
            # 欠損値やNaNを確認
            if data.isna().all() or len(data.dropna()) < 4:
                print(f"{param}のデータが不足しているため、解析をスキップします。")
                continue
            
            # 1. 元の時系列データのプロット
            ax1 = fig.add_subplot(gs[i, 0])
            ax1.plot(data.index, data.values, color=color_palette.get(param, 'gray'), 
                    linewidth=1, marker='o', markersize=2)
            ax1.set_title(f'{param}の時系列データ', fontsize=14, fontname='IPAexGothic')
            ax1.set_ylabel(param, fontsize=12, fontname='IPAexGothic')
            ax1.set_xlabel('日時', fontsize=12, fontname='IPAexGothic')
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            ax1.grid(True, linestyle='--', linewidth=0.5, color='gray', alpha=0.5)
            
            # 2. フーリエ変換
            freqs, amplitudes, phases = fourier_transform(data)
            
            # データが不足している場合はスキップ
            if len(freqs) == 0 or len(amplitudes) == 0:
                print(f"{param}のフーリエ変換に失敗しました。")
                continue
            
            # 周波数を周期（時間）に変換
            periods = 1.0 / freqs
            
            # 主要周波数の検出
            dom_freqs, dom_amps = find_dominant_frequencies(freqs, amplitudes, n_peaks=5, min_dist=2)
            
            # 主要周波数が見つからない場合の処理
            if len(dom_freqs) == 0:
                print(f"{param}の主要周波数が見つかりませんでした。")
                # 空のプロットを作成
                ax2 = fig.add_subplot(gs[i, 1])
                ax2.text(0.5, 0.5, '主要周波数が検出できませんでした', 
                       horizontalalignment='center', verticalalignment='center',
                       fontsize=12, fontname='IPAexGothic')
                ax2.set_title(f'{param}のパワースペクトル', fontsize=14, fontname='IPAexGothic')
                
                ax3 = fig.add_subplot(gs[i, 2])
                ax3.text(0.5, 0.5, '再構成データが作成できませんでした', 
                       horizontalalignment='center', verticalalignment='center',
                       fontsize=12, fontname='IPAexGothic')
                ax3.set_title(f'{param}の再構成データ', fontsize=14, fontname='IPAexGothic')
                continue
            
            # 主要周期を計算
            dom_periods = 1.0 / dom_freqs
            
            # 周期（時間）でソート
            sort_indices = np.argsort(dom_periods)
            dom_periods = dom_periods[sort_indices]
            dom_amps = dom_amps[sort_indices]
            
            # 2. スペクトルのプロット（周期表示）
            ax2 = fig.add_subplot(gs[i, 1])
            
            # 全体のパワースペクトルをプロット
            ax2.plot(periods, amplitudes, color='gray', alpha=0.5, linewidth=1)
            
            # 主要周期を強調
            ax2.scatter(dom_periods, dom_amps, color=color_palette.get(param, 'red'), s=100, 
                      marker='o', zorder=5, label='主要周期')
            
            # 主要周期にラベル付け
            for period, amp in zip(dom_periods, dom_amps):
                if period >= 1.0:  # 1時間以上の周期のみラベル表示
                    period_label = hours_to_period_label(period)
                    ax2.annotate(period_label, (period, amp), 
                               textcoords="offset points", 
                               xytext=(0, 10), 
                               ha='center',
                               fontsize=10,
                               fontname='IPAexGothic')
            
            ax2.set_title(f'{param}のパワースペクトル', fontsize=14, fontname='IPAexGothic')
            ax2.set_xlabel('周期（時間）', fontsize=12, fontname='IPAexGothic')
            ax2.set_ylabel('振幅', fontsize=12, fontname='IPAexGothic')
            ax2.set_xscale('log')  # 周期を対数スケールで表示
            ax2.grid(True, linestyle='--', linewidth=0.5, color='gray', alpha=0.5)
            ax2.legend(loc='best', prop={'family': 'IPAexGothic'})
            
            # X軸の範囲を調整（2時間〜データ長の半分まで）
            max_period = min(len(data)/2, periods.max() if len(periods) > 0 else 100)
            ax2.set_xlim(2, max_period)
            
            # 3. 元データと主要周期による再構成
            # 主要周期に対応する周波数
            dominant_frequencies = 1.0 / dom_periods
            
            # 再構成
            reconstructed_signal = reconstruct_signal(data, dominant_frequencies)
            
            # プロット
            ax3 = fig.add_subplot(gs[i, 2])
            ax3.plot(data.index, data.values, color='gray', alpha=0.5, linewidth=1, label='元データ')
            ax3.plot(data.index, reconstructed_signal, color=color_palette.get(param, 'blue'), 
                   linewidth=2, label='主要周期成分')
            ax3.set_title(f'{param}の再構成データ', fontsize=14, fontname='IPAexGothic')
            ax3.set_xlabel('日時', fontsize=12, fontname='IPAexGothic')
            ax3.set_ylabel(param, fontsize=12, fontname='IPAexGothic')
            ax3.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            ax3.grid(True, linestyle='--', linewidth=0.5, color='gray', alpha=0.5)
            ax3.legend(loc='best', prop={'family': 'IPAexGothic'})
    
    # データ生成時刻を追加
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    plt.figtext(0.5, 0.01, f'データ生成: {current_time}', 
                ha='center', fontsize=10, fontname='IPAexGothic')
    
    # レイアウトの調整
    plt.tight_layout(rect=[0, 0.02, 1, 0.97])
    
    # 保存
    plt.savefig(output_path, bbox_inches='tight')
    plt.close()
    
    print(f"フーリエ解析の可視化が完了しました。出力先: {output_path}")

def create_weekly_daily_comparison(df, output_path='daily_weekly_patterns.png'):
    """
    日内変動と週間変動を分離して可視化する関数
    
    Args:
        df (pd.DataFrame): 前処理されたデータフレーム
        output_path (str): 出力画像のパス
    """
    # 日本語フォントの設定
    japanese_font = setup_japanese_font()
    
    # 解析対象のパラメータ
    parameters = ['AQI値', 'PM2.5', 'PM10', 'O3', 'NO2']
    
    # カラーパレット
    color_palette = {
        'AQI値': '#FF9500',
        'PM2.5': '#FF5733',
        'PM10': '#C70039',
        'O3': '#44BD32',
        'NO2': '#3498DB',
    }
    
    # 日付と時間の情報を追加
    df_with_time = df.copy()
    df_with_time['hour'] = df_with_time.index.hour
    df_with_time['day_of_week'] = df_with_time.index.dayofweek
    df_with_time['date'] = df_with_time.index.date
    
    # 日内変動と週間変動を可視化
    fig, axes = plt.subplots(len(parameters), 2, figsize=(16, 4*len(parameters)), dpi=300)
    
    # タイトル設定
    fig.suptitle('神戸市須磨区 大気質データの日内変動と週間変動', fontsize=20, fontweight='bold', fontname='IPAexGothic')
    
    for i, param in enumerate(parameters):
        if param in df.columns:
            # 日内変動（時間別平均）
            hourly_avg = df_with_time.groupby('hour')[param].mean()
            axes[i, 0].plot(hourly_avg.index, hourly_avg.values, 
                          color=color_palette.get(param, 'blue'), 
                          marker='o', linewidth=2)
            axes[i, 0].set_title(f'{param}の日内変動', fontsize=14, fontname='IPAexGothic')
            axes[i, 0].set_xlabel('時間', fontsize=12, fontname='IPAexGothic')
            axes[i, 0].set_ylabel(param, fontsize=12, fontname='IPAexGothic')
            axes[i, 0].set_xticks(range(0, 24, 3))
            axes[i, 0].grid(True, linestyle='--', linewidth=0.5, color='gray', alpha=0.5)
            
            # 週間変動（曜日別平均）
            daily_avg = df_with_time.groupby('day_of_week')[param].mean()
            day_names = ['月', '火', '水', '木', '金', '土', '日']
            axes[i, 1].plot(daily_avg.index, daily_avg.values, 
                          color=color_palette.get(param, 'green'), 
                          marker='o', linewidth=2)
            axes[i, 1].set_title(f'{param}の週間変動', fontsize=14, fontname='IPAexGothic')
            axes[i, 1].set_xlabel('曜日', fontsize=12, fontname='IPAexGothic')
            axes[i, 1].set_ylabel(param, fontsize=12, fontname='IPAexGothic')
            axes[i, 1].set_xticks(range(7))
            axes[i, 1].set_xticklabels(day_names, fontname='IPAexGothic')
            axes[i, 1].grid(True, linestyle='--', linewidth=0.5, color='gray', alpha=0.5)
    
    # データ生成時刻を追加
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    plt.figtext(0.5, 0.01, f'データ生成: {current_time}', 
                ha='center', fontsize=10, fontname='IPAexGothic')
    
    # レイアウトの調整
    plt.tight_layout(rect=[0, 0.02, 1, 0.97])
    
    # 保存
    plt.savefig(output_path, bbox_inches='tight')
    plt.close()
    
    print(f"日内・週間変動パターンの可視化が完了しました。出力先: {output_path}")

def create_correlation_matrix(df, output_path='correlation_matrix.png'):
    """
    各測定パラメータ間の相関行列を可視化
    
    Args:
        df (pd.DataFrame): 前処理されたデータフレーム
        output_path (str): 出力画像のパス
    """
    # 日本語フォントの設定
    japanese_font = setup_japanese_font()
    
    # 解析対象のパラメータ
    parameters = ['AQI値', 'PM2.5', 'PM10', 'O3', 'NO2', '温度', '湿度', '気圧', '風速', '降水量']
    
    # 相関行列の計算
    corr_matrix = df[parameters].corr()
    
    # プロット
    fig, ax = plt.subplots(figsize=(14, 12), dpi=300)
    
    # ヒートマップの作成
    cax = ax.matshow(corr_matrix, cmap='coolwarm', vmin=-1, vmax=1)
    
    # カラーバー
    cbar = fig.colorbar(cax)
    cbar.ax.set_ylabel('相関係数', fontsize=12, fontname='IPAexGothic')
    
    # タイトル
    plt.title('神戸市須磨区 大気質パラメータ間の相関行列', fontsize=18, fontname='IPAexGothic', pad=20)
    
    # 軸ラベル
    ax.set_xticks(np.arange(len(parameters)))
    ax.set_yticks(np.arange(len(parameters)))
    ax.set_xticklabels(parameters, fontname='IPAexGothic', rotation=45)
    ax.set_yticklabels(parameters, fontname='IPAexGothic')
    
    # 相関係数を表示
    for i in range(len(parameters)):
        for j in range(len(parameters)):
            text = ax.text(j, i, f'{corr_matrix.iloc[i, j]:.2f}', 
                           ha="center", va="center", 
                           color="white" if abs(corr_matrix.iloc[i, j]) > 0.5 else "black",
                           fontsize=10)
    
    # データ生成時刻を追加
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    plt.figtext(0.5, 0.01, f'データ生成: {current_time}', 
                ha='center', fontsize=10, fontname='IPAexGothic')
    
    # レイアウトの調整
    plt.tight_layout(rect=[0, 0.02, 1, 0.97])
    
    # 保存
    plt.savefig(output_path, bbox_inches='tight')
    plt.close()
    
    print(f"相関行列の可視化が完了しました。出力先: {output_path}")

def generate_fourier_analysis(csv_path, output_dir):
    """
    メイン関数
    """
    try:
        # 出力ディレクトリの確認・作成
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # データの読み込みと前処理
        df = load_and_preprocess_data(csv_path)
        
        # フーリエ解析の可視化
        fourier_output_path = os.path.join(output_dir, 'fourier_analysis.png')
        create_fourier_analysis_visualization(df, fourier_output_path)
        
        # 日内・週間変動の可視化
        pattern_output_path = os.path.join(output_dir, 'daily_weekly_patterns.png')
        create_weekly_daily_comparison(df, pattern_output_path)
        
        # 相関行列の可視化
        corr_output_path = os.path.join(output_dir, 'correlation_matrix.png')
        create_correlation_matrix(df, corr_output_path)
        
        print("すべての解析が完了しました。")
        return True
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # CSVファイルのパス
    csv_path = 'data/kobe_aqi_data.csv'
    
    # 出力ディレクトリ
    output_dir = 'data/fourier_analysis'
    
    # フーリエ解析を実行
    generate_fourier_analysis(csv_path, output_dir)