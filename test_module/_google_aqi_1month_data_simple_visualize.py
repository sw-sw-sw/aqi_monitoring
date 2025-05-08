import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import os

def visualize_air_pollution_data(input_filepath, output_filepath):
    """
    大気汚染データ（O3とAQI）の時系列可視化を行い、画像として保存する関数
    
    Parameters:
    -----------
    input_filepath : str
        入力CSVファイルのパス
    output_filepath : str
        出力画像ファイルのパス
    """
    # データの読み込み
    print(f"CSVファイルを読み込んでいます: {input_filepath}")
    df = pd.read_csv(input_filepath)
    
    # 日付の変換
    df['dateTime'] = pd.to_datetime(df['dateTime'])
    
    # データを日付でソート
    df = df.sort_values('dateTime')
    
    # 欠損値の確認
    print(f"欠損値の数: \n{df[['dateTime', 'aqi_value', 'o3_concentration']].isna().sum()}")
    
    # Create subplots - one for AQI and one for all pollutants
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 12), sharex=True, 
                                  gridspec_kw={'height_ratios': [1, 2]})
    
    # Plot AQI values (top graph)
    ax1.plot(df['dateTime'], df['aqi_value'], color='red', marker='o', 
             linestyle='-', markersize=1, label='AQI')
    ax1.set_ylabel('AQI Value')
    ax1.set_title('Air Quality Index (AQI) Time Series', fontsize=14)
    ax1.grid(True, linestyle='--', alpha=0.7)
    ax1.legend(loc='upper left')
    
    # Plot all pollutant concentrations (bottom graph)
    pollutants = {
        'o3_concentration': ('O3', 'blue'),
        'no_concentration': ('NO', 'green'),
        'no2_concentration': ('NO2', 'purple'),
        'so2_concentration': ('SO2', 'brown'),
        'pm10_concentration': ('PM10', 'orange'),
        'co_concentration': ('CO', 'gray')
    }
    
    # Create a second y-axis for CO (which might have different scale)
    ax3 = ax2.twinx()
    
    for column, (label, color) in pollutants.items():
        if column == 'co_concentration':
            # Plot CO on secondary y-axis
            ax3.plot(df['dateTime'], df[column], color=color, marker='o', 
                    linestyle='-', markersize=1, label=label)
        else:
            # Plot other pollutants on primary y-axis
            ax2.plot(df['dateTime'], df[column], color=color, marker='o', 
                    linestyle='-', markersize=1, label=label)
    
    ax2.set_xlabel('Date')  
    ax2.set_ylabel('Concentration (µg/m³)')
    ax3.set_ylabel('CO Concentration (µg/m³)')
    ax2.set_title('Air Pollutant Concentrations Time Series', fontsize=14)
    ax2.grid(True, linestyle='--', alpha=0.7)
    
    # Combine legends from both y-axes
    lines1, labels1 = ax2.get_legend_handles_labels()
    lines2, labels2 = ax3.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    
    # x軸の日付フォーマット設定
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax2.xaxis.set_major_locator(mdates.DayLocator(interval=3))  # Show tick every 3 days
    plt.xticks(rotation=45)
    
    # レイアウトの調整
    plt.tight_layout()
    
    # Save figure
    print(f"Saving figure to: {output_filepath}")
    output_dir = os.path.dirname(output_filepath)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    plt.savefig(output_filepath, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Figure successfully saved to: {output_filepath}")

# メイン処理
if __name__ == "__main__":
    input_filepath = 'data/o3_google_api_1month/o3_by_google_aqi_api.csv'
    output_filepath = 'data/o3_google_api_1month/o3_by_google_aqi_api.png'
    
    visualize_air_pollution_data(input_filepath, output_filepath)