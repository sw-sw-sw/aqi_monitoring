

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import csv
import re
import os
import time
from config import DATA_DIR

BASE_URL = "https://weathernews.jp/onebox/livecam/"
HEADERS = {'User-Agent': 'Mozilla/5.0'}

def convert_to_base_url(page_url, size="640"):
    """
    ウェザーニュースのライブカメラページURLから画像のBASE_URLを生成する
    
    Args:
        page_url (str): ライブカメラのページURL
            例: https://weathernews.jp/onebox/livecam/kinki/hyogo/7CDDE906BA8F/
        size (str, optional): 画像サイズ. デフォルトは "640"
        
    Returns:
        str: 画像のBASE_URL
            例: https://gvs.weathernews.jp/livecam/7CDDE906BA8F/640/
    """
    # カメラIDを抽出する正規表現パターン
    pattern = r'/([0-9A-F]{12,}|[0-9]+)/?'
    
    # カメラIDを抽出
    match = re.search(pattern, page_url)
    if not match:
        raise ValueError("URLからカメラIDを抽出できませんでした")
    
    camera_id = match.group(1)
    
    # 新しいBASE_URLを構築
    base_url = f"https://gvs.weathernews.jp/livecam/{camera_id}/{size}/"
    
    return base_url

def get_soup(url):
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")

def get_area_links(base_url):
    """地方リンクを取得"""
    soup = get_soup(base_url)
    return [urljoin(base_url, a['href']) for a in soup.select("a[href^='/onebox/livecam/']") if a['href'].count('/') == 4]

def get_pref_links(area_url):
    """都道府県リンクを取得（同一地方に属するものだけ）"""
    soup = get_soup(area_url)
    area_path = area_url.replace(BASE_URL, "").strip("/")
    return [
        urljoin(area_url, a['href']) 
        for a in soup.select("a[href^='/onebox/livecam/']") 
        if f"/{area_path}/" in a['href'] and a['href'].count('/') == 5
    ]
def get_camera_links(pref_url, area_name, pref_name):
    """カメラリンクと地域名を取得"""
    soup = get_soup(pref_url)
    data = []

    for a in soup.select("a[href^='/onebox/livecam/']"):
        href = a['href']
        full_url = urljoin(pref_url, href)
        image_url = convert_to_base_url(full_url)
        if href.count('/') > 5:
            region_name = a.get_text(strip=True)
            data.append({
                "region": area_name,
                "division": pref_name,
                "area": region_name,
                "area_url": full_url,
                "image_url": image_url
            })
    return data

def scrape_all():
    all_data = []

    area_links = get_area_links(BASE_URL)

    for area_url in area_links:
        area_name = area_url.rstrip('/').split('/')[-1]
        print(f"[+] 地方: {area_name}")
        time.sleep(0.01)

        pref_links = get_pref_links(area_url)
        for pref_url in pref_links:
            pref_name = pref_url.rstrip('/').split('/')[-1]
            print(f"  ├─ 都道府県: {pref_name}")
            time.sleep(0.01)

            try:
                cam_data = get_camera_links(pref_url, area_name, pref_name)

                all_data.extend(cam_data)
            except Exception as e:
                print(f"  └─ エラー: {e}")

    return all_data

def save_to_csv(data, filename="livecam_links.csv"):
    
    keys = ["region", "division", "area", "area_url", "image_url"]
    # 重複を削除
    unique_data = [dict(t) for t in {tuple(d.items()) for d in data}]
    
    with open(filename, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(unique_data)

if __name__ == "__main__":
    print("全国のライブカメラリンクを収集中...")
    SAVE_DIR = os.path.join(DATA_DIR, "area_urls")
    filename= os.path.join(SAVE_DIR,"livecam_links.csv")
    all_links = scrape_all()
    save_to_csv(all_links, filename)
    print(f"完了！{len(all_links)} 件のリンクを {filename}に保存しました。")
