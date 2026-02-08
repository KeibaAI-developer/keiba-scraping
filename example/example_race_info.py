"""レース情報スクレイピングのサンプルスクリプト

指定したrace_idのレース情報をスクレイピングして表示する。
"""

import requests
from bs4 import BeautifulSoup

from scraping.config import ScrapingConfig
from scraping.race_info import scrape_race_info


def main() -> None:
    """メイン処理

    race_idを指定してレース情報をスクレイピングし、結果を表示する。
    """
    # スクレイピング対象のrace_id（例: 2023年日経賞）
    race_id = "202306030111"

    # 設定を初期化
    config = ScrapingConfig()

    # URLを構築（race.netkeiba.comの結果ページ）
    url = f"https://race.netkeiba.com/race/result.html?race_id={race_id}"

    print(f"スクレイピング対象URL: {url}")
    print(f"レースID: {race_id}")
    print("-" * 80)

    try:
        # HTTPリクエストでHTMLを取得
        response = requests.get(url, headers=config.headers, timeout=config.request_timeout)
        response.raise_for_status()
        response.encoding = "EUC-JP"
        # BeautifulSoupでHTMLをパース
        soup = BeautifulSoup(response.text, "html.parser")

        # レース情報をスクレイピング
        race_info_df = scrape_race_info(soup, race_id)

        # 結果を表示
        print("スクレイピング結果:")
        print(race_info_df)
        print()
        print("カラム一覧:")
        print(race_info_df.columns.tolist())
        print()
        print("詳細情報:")
        for col in race_info_df.columns:
            value = race_info_df[col].iloc[0]
            print(f"  {col}: {value} (型: {type(value).__name__})")

    except requests.exceptions.RequestException as e:
        print(f"HTTPリクエストエラー: {e}")
    except Exception as e:
        print(f"エラーが発生しました: {e}")


if __name__ == "__main__":
    main()
