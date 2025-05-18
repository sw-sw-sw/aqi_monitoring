import pandas as pd
from config import *
import os

# CSVファイルを読み込み、日時でソートして重複を削除する関数
def remove_duplicates_and_sort_by_datetime(input_file, output_file):
    # データフレームにCSVを読み込む
    df = pd.read_csv(input_file)
    
    # 読み込み前の行数を記録
    rows_before = len(df)
    print(f"元のデータ行数: {rows_before}")
    
    # dateTimeを日時型に変換してソートできるようにする
    df['dateTime'] = pd.to_datetime(df['dateTime'])
    
    # dateTimeカラムでソートする（昇順：古い日付から新しい日付へ）
    df_sorted = df.sort_values(by='dateTime')
    
    # ソート後にdateTimeカラムに基づいて重複を削除（最初のエントリを保持）
    df_no_duplicates = df_sorted.drop_duplicates(subset=['dateTime'], keep='first')
    
    # 重複削除後の行数を記録
    rows_after = len(df_no_duplicates)
    print(f"重複削除後の行数: {rows_after}")
    print(f"削除された重複行: {rows_before - rows_after}")
    
    # 結果を新しいCSVファイルに保存
    # dateTimeをISOフォーマットの文字列に戻してからCSVに保存
    df_no_duplicates.to_csv(output_file, index=False)
    print(f"ソート済みで重複のないデータを {output_file} に保存しました")
    
    return df_no_duplicates

# 実行
# input_file_name ='backup_aqi_data_20250518_082727'  # 入力ファイル名
input_file_name ='o3_by_google_aqi_api'  # 入力ファイル名

input_file = os.path.join(PROJECT_ROOT,f"data/o3_google_api_1month/{input_file_name}.csv")  # 入力ファイルのパス
output_file = os.path.join(PROJECT_ROOT,f"data/o3_google_api_1month/{input_file_name}_no_duplicates.csv")  # 出力ファイルのパス

df_clean = remove_duplicates_and_sort_by_datetime(input_file, output_file)

