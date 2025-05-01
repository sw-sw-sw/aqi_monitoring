import csv
from geopy.distance import geodesic
from config import *
from google_geocording_module import geocode
from get_area_urls import get_area_links, get_pref_links, get_camera_links


def find_nearest_points(user_address, input_file, top_n=5, verbose=True):
    """
    ユーザーの住所から最も近いポイントを見つける関数
    
    Parameters:
    -----------
    user_address : str
        ユーザーの住所
    input_file : str
        緯度経度情報を含むCSVファイルのパス
    top_n : int
        取得する最寄りのポイント数
    verbose : bool
        詳細なログを出力するかどうか
    
    Returns:
    --------
    list
        最寄りのポイントのリスト。各ポイントは辞書形式。
        取得できない場合は空のリスト。
    """
    # ユーザーの位置情報を取得
    if verbose:
        print(f"ユーザーの住所を処理中: {user_address}")
    
    coordinates = geocode(user_address)
    
    if not coordinates:
        if verbose:
            print("ユーザーの住所を取得できませんでした。")
        return []

    user_lat, user_lon = coordinates
    user_coords = (user_lat, user_lon)
    if verbose:
        print(f"ユーザーの位置: {user_coords}")
    
    points = []

    # CSVからポイントを読み込み、距離を計算
    with open(input_file, "r", encoding="utf-8-sig") as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            try:
                if row["latitude"] and row["longitude"]:
                    point_coords = (float(row["latitude"]), float(row["longitude"]))
                    distance = geodesic(user_coords, point_coords).kilometers
                    points.append({
                        "area": row["area"], 
                        "distance": distance,
                        "matched_address": row.get("matched_address", ""),
                        "latitude": row["latitude"],
                        "longitude": row["longitude"],
                        "url": row.get("url", "")  # URLカラムがある場合
                    })
                    # if verbose:
                        # print(f"エリア: {row['area']}, 距離: {distance:.2f} km")
            except ValueError:
                if verbose:
                    print(f"警告: エリア '{row.get('area', '不明')}' の緯度経度データに問題があります")
                continue

    # 距離でソートして上位N件を取得
    nearest_points = sorted(points, key=lambda x: x["distance"])[:top_n]

    if verbose and nearest_points:
        print("\nユーザーのもっとも近いエリア:")
        for i, point in enumerate(nearest_points, start=1):
            matched_info = f" (マッチした住所: {point['matched_address']})" if point.get('matched_address') else ""
            print(f"{i}. {point['area']} - {point['distance']:.2f} km{matched_info}")
    
    return nearest_points


def export_nearest_points(user_address, input_file, output_file, top_n=10):
    """
    最寄りのポイントをCSVファイルにエクスポートする関数
    
    Parameters:
    -----------
    user_address : str
        ユーザーの住所
    input_file : str
        緯度経度情報を含むCSVファイルのパス
    output_file : str
        出力するCSVファイルのパス
    top_n : int
        取得する最寄りのポイント数
    """
    nearest_points = find_nearest_points(user_address, input_file, top_n)
    
    if not nearest_points:
        print(f"最寄りのポイントが見つからなかったため、{output_file}の作成をスキップします。")
        return
    
    # CSVにエクスポート
    fieldnames = nearest_points[0].keys()
    
    with open(output_file, "w", encoding="utf-8-sig", newline="") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(nearest_points)
    
    print(f"最寄りの{len(nearest_points)}件のポイントを{output_file}にエクスポートしました。")


if __name__ == "__main__":
    USER_ADDRESS = "神戸市須磨区潮見台町1-3-7"  # ユーザーの住所を指定
    INPUT_CSV = os.path.join(IMAGE_WEB_URL_DIR, "livecam_links_with_lat_lon.csv")
    OUTPUT_CSV = os.path.join(IMAGE_WEB_URL_DIR, "nearest_points.csv")
    
    # 最寄りのポイントを検索
    find_nearest_points(USER_ADDRESS, INPUT_CSV)
    
    # CSVファイルにエクスポート（オプション）
    export_nearest_points(USER_ADDRESS, INPUT_CSV, OUTPUT_CSV)