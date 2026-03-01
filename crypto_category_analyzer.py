import requests
import pandas as pd

# CoinMarketCap APIキーとエンドポイント
API_KEY = 'ec179670-e07d-4a0d-af34-b7edb76e981d'
CATEGORIES_URL = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/categories'

# APIのヘッダー設定
headers = {
    'Accepts': 'application/json',
    'X-CMC_PRO_API_KEY': API_KEY,
}

def fetch_categories_data():
    """カテゴリデータを取得"""
    response = requests.get(CATEGORIES_URL, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching categories data: {response.status_code}")
        return None

def calculate_category_ratios(categories_data):
    """カテゴリごとの出来高比率を計算"""
    # データをDataFrameに変換
    category_df = pd.DataFrame(categories_data['data'])
    
    # 出来高列を数値型に変換
    category_df['volume'] = category_df['volume'].astype(float)
    
    # 全体の出来高を計算
    total_volume = category_df['volume'].sum()
    
    # 各カテゴリの出来高比率を計算
    category_df['volume_ratio'] = (category_df['volume'] / total_volume) * 100
    
    # 比率でソート
    category_df = category_df.sort_values(by='volume_ratio', ascending=False)
    
    return category_df[['name', 'volume', 'volume_ratio']], total_volume

def main():
    # カテゴリデータを取得
    categories_data = fetch_categories_data()
    if not categories_data:
        return

    # カテゴリごとの出来高比率を計算
    category_ratios, total_volume = calculate_category_ratios(categories_data)
    
    # 全データ表示の設定
    pd.set_option('display.float_format', '{:.2f}'.format)  # 小数点の表示形式
    pd.set_option('display.max_rows', None)  # すべての行を表示
    pd.set_option('display.max_columns', None)  # すべての列を表示
    
    # 出力
    print("全体の出来高: {:.2f} USD".format(total_volume))
    print("\nカテゴリごとの出来高比率:")
    
    # パーセンテージ表記のフォーマット
    category_ratios['volume_ratio'] = category_ratios['volume_ratio'].map('{:.2f}%'.format)
    print(category_ratios)

if __name__ == "__main__":
    main()
