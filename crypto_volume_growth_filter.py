'''
コード説明
1. データ取得: fetch_cryptocurrency_data関数でCoinMarketCap APIを呼び出し、暗号資産のリストデータを取得します。

2. データ変換とソート: データをPandasのDataFrameに変換し、volume_24h（24時間出来高）でソートします。

3. フィルタリング条件:
   時価総額が1億ドル未満 (market_cap < 1e9)
   24時間の価格変動が20%以上 (price_change_24h > 20)

4. 出力: フィルタリングされたデータを表示します。
'''
import requests
import pandas as pd
from datetime import datetime, timedelta

# CoinMarketCap APIキーを設定
API_KEY = 'ec179670-e07d-4a0d-af34-b7edb76e981d'
BASE_URL = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'

# パラメータ設定
params = {
    'start': '1',  # データの開始位置
    'limit': '1000',  # 取得する銘柄の数
    'convert': 'USD'  # 通貨単位
}

# ヘッダー設定
headers = {
    'Accepts': 'application/json',
    'X-CMC_PRO_API_KEY': API_KEY,
}

def fetch_cryptocurrency_data():
    """暗号資産データを取得"""
    response = requests.get(BASE_URL, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None

def filter_cryptocurrencies(data):
    """指定条件で銘柄をフィルタリング"""
    # データをDataFrameに変換
    df = pd.DataFrame([{
        'name': coin['name'],
        'symbol': coin['symbol'],
        'volume_24h': coin['quote']['USD']['volume_24h'],
        'market_cap': coin['quote']['USD']['market_cap'],
        'price_change_24h': coin['quote']['USD']['percent_change_24h']
    } for coin in data['data']])
    
    # 出来高でソート
    df = df.sort_values(by='volume_24h', ascending=False)
    
    # 時価総額が低く、出来高が急増している銘柄をフィルタ
    filtered_df = df[(df['market_cap'] < 1e9) & (df['price_change_24h'] > 20)]
    
    return filtered_df

def main():
    # データ取得
    data = fetch_cryptocurrency_data()
    if data is None:
        return

    # フィルタリング
    filtered_data = filter_cryptocurrencies(data)
    
    # 結果表示
    if not filtered_data.empty:
        print("出来高が急増している低時価総額銘柄:")
        print(filtered_data)
    else:
        print("条件を満たす銘柄は見つかりませんでした。")

if __name__ == "__main__":
    main()
