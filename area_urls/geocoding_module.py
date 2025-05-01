# geocoding_module.py
import re
import time
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

def clean_address(address):
    """住所文字列をクリーニングする関数"""
    # 日付や時刻、特殊文字を削除
    address = re.sub(r"\d{1,2}/\d{1,2} \d{1,2}:\d{1,2}", "", address)  # 日付と時刻を削除
    address = re.sub(r"[^\w\s一-龥]", "", address)  # 特殊文字を削除
    # 「周辺」や「付近」などの曖昧表現を削除
    address = re.sub(r"周辺|付近|あたり|近く", "", address)
    return address.strip()


def get_address_hierarchy(address):
    """住所を階層的に分解して、徐々に詳細度を下げたリストを返す関数"""
    # まず住所をクリーニング
    cleaned_address = clean_address(address)
    
    # 住所の階層リストを初期化（最も詳細なものから順に）
    address_levels = [cleaned_address]
    
    # 数字と番地を削除（例: 「4-5-6」や「123番地」など）
    address_without_numbers = re.sub(r'\d+[-－]\d+[-－]?\d*|[0-9０-９]+番地?', '', cleaned_address)
    address_without_numbers = address_without_numbers.strip()
    if address_without_numbers != cleaned_address:
        address_levels.append(address_without_numbers)
    
    # 町名レベルまで分解
    # 日本の住所で一般的な「〜町〜丁目」「〜区〜町」などのパターンを抽出
    town_match = re.search(r'(.+?[都道府県市区町村])', cleaned_address)
    if town_match:
        town_address = town_match.group(1)
        if town_address != cleaned_address and town_address not in address_levels:
            address_levels.append(town_address)
    
    # さらに市区町村レベルまで分解
    city_match = re.search(r'(.+?[市区町村])', cleaned_address)
    if city_match:
        city_address = city_match.group(1)
        if city_address != cleaned_address and city_address not in address_levels:
            address_levels.append(city_address)
    
    # 都道府県レベルまで分解
    pref_match = re.search(r'(.+?[都道府県])', cleaned_address)
    if pref_match:
        pref_address = pref_match.group(1)
        if pref_address != cleaned_address and pref_address not in address_levels:
            address_levels.append(pref_address)
    
    return address_levels


def geocode_address(address, verbose=False, max_retries=3, user_agent="geoapi"):
    """住所から緯度経度を取得する関数
    
    Parameters:
    -----------
    address : str
        住所文字列
    verbose : bool
        詳細なログを出力するかどうか
    max_retries : int
        各住所レベルでの最大リトライ回数
    user_agent : str
        Nominatimジオコーダーに渡すユーザーエージェント名
        
    Returns:
    --------
    tuple
        (緯度, 経度, マッチした住所) のタプル。取得できない場合は (None, None, None)
    """
    geolocator = Nominatim(user_agent=user_agent, timeout=10)
    address_levels = get_address_hierarchy(address)
    
    if verbose:
        print(f"住所の処理: {address}")
        print(f"階層化された住所: {address_levels}")
    
    for level, addr in enumerate(address_levels):
        for attempt in range(max_retries):
            try:
                if verbose:
                    print(f"  試行中 ({level+1}/{len(address_levels)}, 試行 {attempt+1}/{max_retries}): {addr}")
                
                location = geolocator.geocode(addr, timeout=10)
                
                if location:
                    if verbose:
                        print(f"  ー> 成功: {addr} ({location.latitude}, {location.longitude})")
                    return location.latitude, location.longitude, addr
                
                # locationがNoneの場合は次の住所レベルへ
                break
            
            except GeocoderTimedOut:
                if verbose:
                    print(f"  ー> タイムアウト: {addr} - 再試行... ({attempt+1}/{max_retries})")
                
                # 最後の試行でなければ再試行
                if attempt < max_retries - 1:
                    time.sleep(2)  # 2秒待機
                continue
                
            except Exception as e:
                if verbose:
                    print(f"  ー> エラー: {addr}: {e}")
                break  # その他のエラーは次の住所レベルへ
    
    if verbose:
        print(f"緯度経度を取得できませんでした: {address}")
    
    return None, None, None


# 使用例
if __name__ == "__main__":
    test_addresses = [
        "柳津町細八4/30 13:56",
        "北上市周辺",
        "愛知県名古屋市中区新栄1丁目1-1",
        "東京都渋谷区"
    ]
    
    for address in test_addresses:
        latitude, longitude, matched_address = geocode_address(address, verbose=True)
        
        if latitude and longitude:
            print(f"結果: {address} -> 緯度: {latitude}, 経度: {longitude} (マッチした住所: {matched_address})")
        else:
            print(f"結果: {address} -> 緯度経度の取得に失敗")
        
        print("-" * 50)