import csv, os
from config import *
# geocoding_module からの import を google_geocording_module からの import に変更
from area_urls._google_geocording_module import geocode

def add_lat_lon_to_csv(input_file, output_file, failed_output_file=None, verbose=True):
    """
    CSVファイル内の住所から緯度経度を取得し、新しいCSVファイルに保存する関数
    失敗した住所を別ファイルに保存することも可能
    
    Parameters:
    -----------
    input_file : str
        入力CSVファイルのパス
    output_file : str
        出力CSVファイルのパス
    failed_output_file : str, optional
        失敗した住所を保存するCSVファイルのパス
    verbose : bool
        詳細なログを出力するかどうか
    """
    # 失敗した住所を格納するリスト
    failed_addresses = []
    
    # 既存のデータを保持
    existing_data = {}
    try:
        with open(output_file, "r", encoding="utf-8-sig") as outfile:
            reader = csv.DictReader(outfile)
            for row in reader:
                key = row.get("area")
                if key:
                    existing_data[key] = row
        if verbose:
            print(f"{len(existing_data)}件の既存データを読み込みました。")
    except FileNotFoundError:
        if verbose:
            print(f"{output_file} が見つかりません。新しいファイルを作成します。")

    # 入力ファイルを読み込み、出力ファイルに書き込む
    with open(input_file, "r", encoding="utf-8-sig") as infile, open(output_file, "w", encoding="utf-8-sig", newline="") as outfile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames.copy() if reader.fieldnames else []
        
        # 必要なフィールドがまだ無ければ追加
        for field in ["latitude", "longitude", "matched_address"]:
            if field not in fieldnames:
                fieldnames.append(field)
        
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        
        # 各行を処理
        for index, row in enumerate(reader, start=1):
            if verbose:
                print(f"行 {index} を処理中...")
            
            # 既存データがある場合はスキップ
            if row["area"] in existing_data:
                existing_row = existing_data[row["area"]]
                if existing_row.get("latitude") and existing_row.get("longitude"):
                    if verbose:
                        print(f"  ー>住所をスキップ (既に処理済み): {row['area']} (行 {index})")
                    writer.writerow(existing_row)
                    continue

            try:
                if verbose:
                    print(f"住所の処理: {row['area']} (行 {index})")
                
                # Google Geocodingモジュールを使用して住所を処理
                result = geocode(row["area"])
                
                if result:
                    latitude, longitude = result
                    row["latitude"] = latitude
                    row["longitude"] = longitude
                    # Google Geocodingモジュールでは matched_address は提供されないため空欄に
                    row["matched_address"] = ""
                else:
                    row["latitude"] = ""
                    row["longitude"] = ""
                    row["matched_address"] = ""
                    if verbose:
                        print(f"住所の地理情報取得に失敗: {row['area']} (行 {index})")
                    # 失敗リストに追加
                    failed_addresses.append(dict(row))
            except Exception as e:
                row["latitude"] = ""
                row["longitude"] = ""
                row["matched_address"] = ""
                if verbose:
                    print(f"地理情報取得エラー {row['area']} (行 {index}): {e}")
                # 失敗リストに追加
                failed_addresses.append(dict(row))

            writer.writerow(row)
        
        if verbose:
            print(f"CSVファイルの処理が完了しました。")
    
    # 失敗した住所をCSVに保存
    if failed_output_file and failed_addresses:
        save_failed_addresses(failed_addresses, failed_output_file, verbose)
    
    return failed_addresses

def retry_lat_lon_for_missing_data(output_file, failed_output_file=None, verbose=True):
    """
    緯度経度が取得できなかった住所に対して再試行する関数
    
    Parameters:
    -----------
    output_file : str
        処理対象のCSVファイルのパス
    failed_output_file : str, optional
        失敗した住所を保存するCSVファイルのパス
    verbose : bool
        詳細なログを出力するかどうか
        
    Returns:
    --------
    list
        再試行後も失敗した住所のリスト
    """
    # 失敗した住所を格納するリスト
    failed_addresses = []
    
    # 既存データを読み込み
    rows = []
    with open(output_file, "r", encoding="utf-8-sig") as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames
        if "matched_address" not in fieldnames and fieldnames is not None:
            fieldnames.append("matched_address")
        for row in reader:
            rows.append(row)

    if verbose:
        print(f"{len(rows)}件のデータを読み込みました。")
    
    # 緯度経度が空のデータを集計
    missing_data = [row for row in rows if not row.get("latitude") or not row.get("longitude")]
    if verbose:
        print(f"地理情報が不足しているデータ: {len(missing_data)}件")
    
    # 不足データがなければ終了
    if not missing_data:
        if verbose:
            print("地理情報が不足しているデータはありません。")
        return []
    
    # 緯度経度が空のデータを再取得
    for i, row in enumerate(missing_data, 1):
        if verbose:
            print(f"地理情報の再取得 ({i}/{len(missing_data)}): {row['area']}")
        
        try:
            # Google Geocodingモジュールを使用
            region = row.get('region', '')
            division = row.get('division', '')
            area = row.get('area', '')
            combined_address = f"{region} {division} {area}".strip()
            result = geocode(combined_address)  # Use combined_address instead of row["area"]
            
            if result:
                latitude, longitude = result
                # 元のリストの該当行を更新
                for original_row in rows:
                    if original_row["area"] == row["area"]:
                        original_row["latitude"] = latitude
                        original_row["longitude"] = longitude
                        # Google Geocodingモジュールでは matched_address は提供されないため空欄に
                        original_row["matched_address"] = ""
                        break
            else:
                if verbose:
                    print(f"地理情報の再取得に失敗: {row['area']}")
                # 失敗リストに追加
                failed_addresses.append(dict(row))
        except Exception as e:
            if verbose:
                print(f"再取得時のエラー {row['area']}: {e}")
            # 失敗リストに追加
            failed_addresses.append(dict(row))

    # 更新されたデータを書き戻す
    with open(output_file, "w", encoding="utf-8-sig", newline="") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    if verbose:
        print(f"再取得プロセスが完了しました。")
    
    # 失敗した住所をCSVに保存
    if failed_output_file and failed_addresses:
        save_failed_addresses(failed_addresses, failed_output_file, verbose)
    
    return failed_addresses

def save_failed_addresses(failed_addresses, output_file, verbose=True):
    """
    失敗した住所をCSVファイルに保存する関数
    
    Parameters:
    -----------
    failed_addresses : list
        失敗した住所の辞書のリスト
    output_file : str
        出力CSVファイルのパス
    verbose : bool
        詳細なログを出力するかどうか
    """
    if not failed_addresses:
        if verbose:
            print("失敗した住所はありません。")
        return
    
    # フィールド名を取得（すべての失敗データのキーの和集合）
    fieldnames = set()
    for address in failed_addresses:
        fieldnames.update(address.keys())
    fieldnames = list(fieldnames)
    
    # CSVに書き込み
    with open(output_file, "w", encoding="utf-8-sig", newline="") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(failed_addresses)
    
    if verbose:
        print(f"{len(failed_addresses)}件の失敗した住所を {output_file} に保存しました。")


def main():
    input_dir = os.path.join(PROJECT_ROOT, "area_urls")
    input_csv_path = os.path.join(input_dir, "livecam_links.csv")
    output_csv_path = os.path.join(input_dir, "livecam_links_with_lat_lon.csv")
    failed_csv_path = os.path.join(input_dir, "failed_geocoding_addresses.csv")
    
    # CSVファイルに緯度経度情報を追加（失敗した住所も保存）
    failed_addresses = add_lat_lon_to_csv(input_csv_path, output_csv_path, failed_csv_path)
    print(f"処理データを {output_csv_path} に保存しました。")
    print(f"初回処理で {len(failed_addresses)} 件の住所で緯度経度の取得に失敗しました。")
    
    # 未取得のデータに対して再試行（失敗した住所も保存）
    failed_after_retry = retry_lat_lon_for_missing_data(output_csv_path, failed_csv_path)
    print(f"{output_csv_path} の再試行プロセスが完了しました。")
    print(f"再試行後も {len(failed_after_retry)} 件の住所で緯度経度の取得に失敗しました。")
    
if __name__ == "__main__":
    main()