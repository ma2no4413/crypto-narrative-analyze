import requests
import pandas as pd

# CoinMarketCap APIキーとエンドポイント
API_KEY = 'ec179670-e07d-4a0d-af34-b7edb76e981d'
CRYPTO_LIST_URL = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'

# APIのヘッダー設定
headers = {
    'Accepts': 'application/json',
    'X-CMC_PRO_API_KEY': API_KEY,
}

def fetch_crypto_data():
    """トークンデータを取得"""
    params = {
        'start': 1,          # 取得開始位置
        'limit': 5000,       # 最大取得数（必要に応じて調整）
        'convert': 'USD'     # 通貨単位
    }
    response = requests.get(CRYPTO_LIST_URL, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching crypto data: {response.status_code}")
        return None

def process_crypto_data(crypto_data):
    """トークンデータを処理"""
    # データをDataFrameに変換
    crypto_df = pd.DataFrame([{
        'name': crypto['name'],
        'symbol': crypto['symbol'],
        'market_cap': crypto['quote']['USD']['market_cap'],
        'volume_24h': crypto['quote']['USD']['volume_24h']
    } for crypto in crypto_data['data']])
    
    # 数値型に変換
    crypto_df['market_cap'] = crypto_df['market_cap'].astype(float)
    crypto_df['volume_24h'] = crypto_df['volume_24h'].astype(float)
    
    # 最小値を計算
    min_market_cap = crypto_df['market_cap'].min()
    min_volume_24h = crypto_df['volume_24h'].min()
    
    # 全体の合計を計算
    total_market_cap = crypto_df['market_cap'].sum()
    total_volume_24h = crypto_df['volume_24h'].sum()
    
    # 各トークンの割合を計算
    crypto_df['market_cap_ratio'] = (crypto_df['market_cap'] / total_market_cap) * 100
    crypto_df['volume_24h_ratio'] = (crypto_df['volume_24h'] / total_volume_24h) * 100
    
    # 時価総額でソート
    sorted_df = crypto_df.sort_values(by='market_cap', ascending=False)
    
    return sorted_df, min_market_cap, min_volume_24h, total_market_cap, total_volume_24h

def save_to_csv(dataframe, filename):
    """CSVファイルに保存"""
    dataframe.to_csv(filename, index=False)
    print(f"データをCSVファイルに保存しました: {filename}")

def main():
    # トークンデータを取得
    crypto_data = fetch_crypto_data()
    if not crypto_data:
        return

    # トークンデータを処理
    sorted_df, min_market_cap, min_volume_24h, total_market_cap, total_volume_24h = process_crypto_data(crypto_data)

    # 出力
    print("最小の時価総額: {:.2f} USD".format(min_market_cap))
    print("最小の出来高: {:.2f} USD".format(min_volume_24h))
    print("\nトークン情報（時価総額順）:")
    print("全体の時価総額: {:.2f} USD".format(total_market_cap))
    print("全体の出来高: {:.2f} USD\n".format(total_volume_24h))
    
    # 表示用データの整形
    pd.set_option('display.float_format', '{:.2f}'.format)
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    
    # CSV用にフォーマット調整
    sorted_df['market_cap_ratio'] = sorted_df['market_cap_ratio'].map('{:.2f}'.format)
    sorted_df['volume_24h_ratio'] = sorted_df['volume_24h_ratio'].map('{:.2f}'.format)
    
    # CSVに保存
    save_to_csv(sorted_df, 'crypto_market_data.csv')

if __name__ == "__main__":
    main()
