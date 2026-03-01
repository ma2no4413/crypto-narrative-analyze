import os
import requests
import time
import csv
from datetime import datetime

# スクリプトのあるディレクトリを取得
script_dir = os.path.dirname(os.path.abspath(__file__))

# 定数
API_URL = "https://api.coingecko.com/api/v3/coins/markets"
VS_CURRENCY = "usd"
PER_PAGE = 100
TOTAL_COINS = 500
MAX_RETRIES = 5
INITIAL_BACKOFF = 2  # seconds

def fetch_page(page):
    retries = 0
    backoff = INITIAL_BACKOFF

    while retries < MAX_RETRIES:
        try:
            response = requests.get(API_URL, params={
                "vs_currency": VS_CURRENCY,
                "order": "market_cap_desc",
                "per_page": PER_PAGE,
                "page": page,
                "sparkline": "false"
            })
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                print(f"[429] Rate limited. Retrying in {backoff} seconds...")
                time.sleep(backoff)
                backoff *= 2
                retries += 1
            else:
                print(f"[{response.status_code}] Error: {response.text}")
                break
        except requests.RequestException as e:
            print(f"Request failed: {e}")
            time.sleep(backoff)
            backoff *= 2
            retries += 1

    return []

def main():
    all_data = []

    total_pages = TOTAL_COINS // PER_PAGE

    for page in range(1, total_pages + 1):
        print(f"Fetching page {page}/{total_pages}...")
        data = fetch_page(page)
        if not data:
            print(f"Failed to fetch page {page}. Skipping...")
            continue
        all_data.extend(data)
        time.sleep(1.2)  # Rate limit回避

    # タイムスタンプ付きファイル名
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"top_500_tokens_{timestamp}.csv"
    filepath = os.path.join(script_dir, filename)  # スクリプトと同じディレクトリに出力

    # CSV出力
    with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["id", "symbol", "name", "market_cap", "total_volume"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for coin in all_data:
            writer.writerow({
                "id": coin["id"],
                "symbol": coin["symbol"],
                "name": coin["name"],
                "market_cap": coin["market_cap"],
                "total_volume": coin["total_volume"]
            })

    print(f"✅ CSVファイル '{filename}' を出力しました。")

if __name__ == "__main__":
    main()
