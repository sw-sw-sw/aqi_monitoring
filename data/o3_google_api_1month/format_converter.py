import pandas as pd
import os

def convert_aqi_data_format():
    # ファイルパスを手動で設定
    input_file = '/home/sw/aqi_monitoring/data/o3_google_api_1month/o3_by_google_aqi_api_bak.csv'
    output_file = '/home/sw/aqi_monitoring/data/o3_google_api_1month/o3_by_google_aqi_api.csv'
    
    # 入力CSVファイルを読み込む
    df_input = pd.read_csv(input_file)
    
    # 出力フォーマットのデータフレームを作成
    df_output = pd.DataFrame(columns=[
        "地点", "取得時間", "AQI値", "大気質ステータス", "主要汚染物質", 
        "PM2.5", "PM10", "O3", "NO2", "温度", "湿度", "気圧", "風速", "降水量"
    ])
    
    # データをマッピング
    # 地点は常に「神戸市 須磨区」に設定
    df_output["地点"] = "神戸市 須磨区"
    df_output["取得時間"] = df_input["dateTime"]
    df_output["AQI値"] = df_input["aqi_value"]
    
    # 大気質ステータスのマッピング
    status_mapping = {
        "": "N/A",  # 空の場合
        "N/A": "N/A",
    }
    
    # aqi_categoryが存在する場合にマッピングを使用
    if "aqi_category" in df_input.columns:
        df_output["大気質ステータス"] = df_input["aqi_category"].map(status_mapping).fillna(df_input["aqi_category"])
    else:
        df_output["大気質ステータス"] = "N/A"
    
    # 主要汚染物質
    df_output["主要汚染物質"] = df_input["dominantPollutant"]
    
    # 汚染物質の濃度データをマッピング
    df_output["PM2.5"] = df_input["pm2_5_concentration"]
    df_output["PM10"] = df_input["pm10_concentration"]
    df_output["O3"] = df_input["o3_concentration"]
    df_output["NO2"] = df_input["no2_concentration"]
    
    # 気象データ（APIからは取得できないので固定値またはN/Aに設定）
    df_output["温度"] = "N/A"
    df_output["湿度"] = "N/A"
    df_output["気圧"] = "N/A"
    df_output["風速"] = "N/A"
    df_output["降水量"] = "N/A"
    
    # CSVに保存
    df_output.to_csv(output_file, index=False)
    
    print(f"変換が完了しました。出力ファイル: {output_file}")
    print(f"処理されたレコード数: {len(df_output)}")

if __name__ == "__main__":
    convert_aqi_data_format()