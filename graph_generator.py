import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import matplotlib.colors as mcolors
import matplotlib.font_manager as fm
import os
from config import logger, DATA_DIR

def setup_japanese_font():
    """
    日本語フォントを設定する関数
    
    Returns:
        str: 使用可能な日本語フォント名
    """
    # 明示的にIPAexゴシックを指定
    plt.rcParams['font.family'] = 'IPAexGothic'
    
    # matplotlibのグローバル設定
    plt.rcParams['axes.unicode_minus'] = False
    
    return 'IPAexGothic'

def rgba_to_matplotlib(rgba_str):
    """
    CSS形式のrgba文字列をmatplotlibの色形式に変換する関数
    
    Args:
        rgba_str (str): CSSスタイルのrgba文字列 (例: 'rgba(0,228,0,0.2)')
    
    Returns:
        tuple: matplotlibで使用可能な色とアルファ値のタプル
    """
    # rgba文字列から数値を抽出
    rgba_values = rgba_str.replace('rgba(', '').replace(')', '').split(',')
    
    # RGB値を0-1の範囲に正規化
    r, g, b = [int(x.strip()) / 255 for x in rgba_values[:3]]
    
    # アルファ値を取得（指定がない場合は1）
    alpha = float(rgba_values[3]) if len(rgba_values) > 3 else 1.0
    
    return (r, g, b, alpha)

def load_and_preprocess_data(file_path):
    """
    CSVデータを読み込み、前処理を行う関数
    
    Args:
        file_path (str): CSVファイルのパス
    
    Returns:
        pd.DataFrame: 前処理されたデータフレーム
    """
    # CSVファイルを読み込む
    df = pd.read_csv(file_path, encoding='utf-8-sig')
    
    # 日時列を datetime 型に変換
    df['取得時間'] = pd.to_datetime(df['取得時間'])
    
    # 数値型に変換する列
    numeric_columns = ['AQI値', 'PM2.5', 'PM10', 'O3', 'NO2', '温度', '湿度', '気圧', '風速', '降水量']
    
    # 各列を数値型に変換（"non"はNaNに置き換え）
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].replace('non', pd.NA), errors='coerce')
    
    return df

def create_aqi_visualization(df, output_path='aqi_visualization.png'):
    """
    AQIデータを可視化し、画像として保存する関数
    3つのサブプロットに分けて表示する:
    1. AQI値の推移
    2. 汚染物質の推移 (PM2.5, O3)
    3. 気象データの推移 (温度, 湿度, 気圧, 風速, 降水量)
    
    Args:
        df (pd.DataFrame): 前処理されたデータフレーム
        output_path (str): 出力画像のパス
    """
    # 日本語フォントの設定
    japanese_font = setup_japanese_font()
    
    # グラフのスタイル設定
    plt.style.use('ggplot')
    
    # サブプロットを作成 (3つの階層)
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 18), dpi=300, 
                                       gridspec_kw={'height_ratios': [1, 1, 1.2]})
    
    # カラーパレット
    color_palette = {
        'AQI値': '#FF9500',
        'PM2.5': '#FF5733',
        'PM10': '#C70039',
        'O3': '#44BD32',
        'NO2': '#3498DB',
        '温度': '#E74C3C',  # 赤 - 温度
        '湿度': '#3498DB',  # 青 - 湿度
        '気圧': '#9B59B6',  # 紫 - 気圧
        '風速': '#2ECC71',  # 緑 - 風速
        '降水量': '#1ABC9C'   # ターコイズ - 降水量
    }
    
    # AQIカテゴリの背景色（matplotlibに対応した形式）
    aqi_categories = [
        (0, 50, 'rgba(0,228,0,0.2)', '良好'),
        (50, 100, 'rgba(255,255,0,0.2)', '普通'),
        (100, 150, 'rgba(255,126,0,0.2)', '敏感な人に有害'),
        (150, 200, 'rgba(255,0,0,0.2)', '健康に良くない'),
        (200, 300, 'rgba(143,63,151,0.2)', '非常に健康に良くない'),
        (300, 500, 'rgba(126,0,35,0.2)', '危険')
    ]
    
    # 日付変更点（0時）を特定
    # 日付のみを抽出し、重複を削除して一意の日付リストを取得
    df['日付'] = df['取得時間'].dt.date
    unique_dates = df['日付'].unique()[1:]  # 最初の日付を除外（グラフの開始点）
    
    # 各日付の0時のタイムスタンプを生成
    midnight_timestamps = [pd.Timestamp(date).replace(hour=0, minute=0, second=0) for date in unique_dates]
    
    # 1. AQI値のグラフ作成
    # カテゴリの背景を描画
    for start, end, color, label in aqi_categories:
        rgba_color = rgba_to_matplotlib(color)
        ax1.axhspan(start, end, facecolor=rgba_color[:3], alpha=rgba_color[3], edgecolor='none')
    
    # AQI値の折れ線グラフ
    ax1.plot(df['取得時間'], df['AQI値'], 
             color=color_palette['AQI値'], 
             linewidth=1, 
             marker='o', 
             markersize=4,
             label='AQI値')
    
    # 日付変更線を追加（AQI値グラフ）
    for timestamp in midnight_timestamps:
        ax1.axvline(x=timestamp, color='#333333', linestyle='-', linewidth=1, alpha=0.7)
    
    # フォントを明示的に指定
    fig.suptitle('神戸市須磨区 大気質指数（AQI）および気象データの推移', fontsize=16, fontweight='bold', fontname='IPAexGothic')
    
    ax1.set_title('AQI値の推移', fontsize=14, fontweight='bold', fontname='IPAexGothic')
    ax1.set_ylabel('AQI値', fontsize=12, fontname='IPAexGothic')
    ax1.set_ylim(0, max(df['AQI値'].dropna()) * 1.1 if not df['AQI値'].dropna().empty else 100)
    ax1.grid(True, linestyle='--', linewidth=0.5, color='gray', alpha=0.5)
    ax1.tick_params(axis='x', rotation=45, labelsize=10)
    ax1.xaxis.set_major_locator(plt.MaxNLocator(8))
    
    # 日付のフォーマットを調整
    plt.setp(ax1.get_xticklabels(), rotation=45, ha='right', fontname='IPAexGothic')
    
    # 凡例の追加
    ax1.legend(loc='upper left', prop={'family': 'IPAexGothic'})
    
    # 2. 汚染物質のグラフ作成
    pollutants = ['PM2.5', 'PM10', 'O3', 'NO2']
    # 各汚染物質をプロット
    for pollutant in pollutants:
        if pollutant in df.columns:
            ax2.plot(df['取得時間'], df[pollutant], 
                    color=color_palette.get(pollutant, 'gray'), 
                    linewidth=1, 
                    marker='o', 
                    markersize=3,
                    label=pollutant)
    
    # 日付変更線を追加（汚染物質グラフ）
    for timestamp in midnight_timestamps:
        ax2.axvline(x=timestamp, color='#333333', linestyle='-', linewidth=1, alpha=0.7)
    
    ax2.set_title('汚染物質の推移', fontsize=14, fontname='IPAexGothic')
    ax2.set_ylabel('濃度', fontsize=10, fontname='IPAexGothic')
    ax2.grid(True, linestyle='--', linewidth=0.5, color='gray', alpha=0.5)
    ax2.tick_params(axis='x', rotation=45, labelsize=10)
    ax2.xaxis.set_major_locator(plt.MaxNLocator(8))
    
    # 日付のフォーマットを調整
    plt.setp(ax2.get_xticklabels(), rotation=45, ha='right', fontname='IPAexGothic')
    
    ax2.legend(loc='best', prop={'family': 'IPAexGothic'})
    
    # 3. 気象データのグラフ作成
    weather_data = ['温度', '湿度', '気圧', '風速', '降水量']
    
    # 主軸（左側）と第2軸（右側）を使い分ける
    ax3_2 = ax3.twinx()  # 第2軸を作成
    
    # 気圧は右軸、他は左軸に表示
    left_axis_data = ['温度', '湿度', '風速', '降水量']
    right_axis_data = ['気圧']
    
    # スケールの調整（左軸）
    has_left_data = False
    left_max = 0
    
    # 左軸のデータをプロット
    for param in left_axis_data:
        if param in df.columns and not df[param].dropna().empty:
            has_left_data = True
            ax3.plot(df['取得時間'], df[param], 
                    color=color_palette.get(param, 'gray'), 
                    linewidth=1, 
                    marker='o', 
                    markersize=3,
                    label=param)
            current_max = df[param].dropna().max()
            if current_max > left_max:
                left_max = current_max
    
    # 右軸のデータをプロット（気圧）
    has_right_data = False
    if '気圧' in df.columns and not df['気圧'].dropna().empty:
        has_right_data = True
        ax3_2.plot(df['取得時間'], df['気圧'], 
                 color=color_palette.get('気圧', 'purple'), 
                 linewidth=1, 
                 marker='o', 
                 markersize=3,
                 label='気圧')
        
        # 気圧のスケールを調整
        pressure_mean = df['気圧'].dropna().mean()
        if not pd.isna(pressure_mean):
            pressure_variance = max(30, df['気圧'].dropna().std() * 3)
            ax3_2.set_ylim(pressure_mean - pressure_variance, pressure_mean + pressure_variance)
        ax3_2.set_ylabel('気圧 (hPa)', fontsize=10, fontname='IPAexGothic')
        ax3_2.tick_params(axis='y', labelcolor=color_palette.get('気圧', 'purple'))
    
    # 日付変更線を追加（気象データグラフ）
    for timestamp in midnight_timestamps:
        ax3.axvline(x=timestamp, color='#333333', linestyle='-', linewidth=1, alpha=0.7)
    
    ax3.set_title('気象データの推移', fontsize=14, fontname='IPAexGothic')
    ax3.set_xlabel('日時', fontsize=10, fontname='IPAexGothic')
    
    if has_left_data:
        ax3.set_ylabel('温度(°C), 湿度(%), 風速(m/s), 降水量(mm)', fontsize=10, fontname='IPAexGothic')
        ax3.set_ylim(0, left_max * 1.1)
    
    ax3.grid(True, linestyle='--', linewidth=0.5, color='gray', alpha=0.5)
    ax3.tick_params(axis='x', rotation=45, labelsize=10)
    ax3.xaxis.set_major_locator(plt.MaxNLocator(8))
    
    # 日付のフォーマットを調整
    plt.setp(ax3.get_xticklabels(), rotation=45, ha='right', fontname='IPAexGothic')
    
    # 凡例を作成（左軸と右軸を合わせて）
    lines1, labels1 = ax3.get_legend_handles_labels()
    if has_right_data:
        lines2, labels2 = ax3_2.get_legend_handles_labels()
        ax3.legend(lines1 + lines2, labels1 + labels2, loc='best', prop={'family': 'IPAexGothic'})
    else:
        ax3.legend(loc='best', prop={'family': 'IPAexGothic'})
    
    # データ生成時刻を追加
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    plt.figtext(0.5, 0.01, f'データ生成: {current_time}', 
                ha='center', fontsize=8, fontname='IPAexGothic')
    
    # レイアウトの調整
    plt.tight_layout()
    plt.subplots_adjust(top=0.95, bottom=0.05)
    
    # 保存
    plt.savefig(output_path, bbox_inches='tight')
    plt.close()
    
    print(f"AQIデータの可視化が完了しました。出力先: {output_path}")

def generate_graph(output_path):
    """
    メイン関数
    """
    # CSVファイルのパス
    csv_path = os.path.join(DATA_DIR, 'kobe_aqi_data.csv')
    
    
    try:
        # データの読み込みと前処理
        df = load_and_preprocess_data(csv_path)
        
        # 可視化
        create_aqi_visualization(df, output_path)
        
        return True
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    output_path = os.path.join(DATA_DIR, 'aqi_graph.png')
    generate_graph(output_path)