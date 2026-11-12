"""JRAプレレーティングスクレイパーのサンプルスクリプト

指定したG1の登録馬のプレレーティングをJRA公式サイトから取得して表示する。
requestsを使用するため、ネットワーク接続が必要。
"""

from scraping.config import ScrapingConfig
from scraping.jra_pre_rating import JraPreRatingScraper


def main() -> None:
    """メイン処理

    開催年とページ名を指定してJraPreRatingScraperでプレレーティングをスクレイピングし、
    データを表示とCSV保存する。
    """
    # https://www.jra.go.jp/datafile/ranking/g1/2026/eliza.html の 2026 と eliza
    year = 2026
    g1_page = "eliza"

    # 設定を初期化
    config = ScrapingConfig()

    print(f"対象: {year}年 {g1_page}")
    print("=" * 80)

    try:
        scraper = JraPreRatingScraper(year, g1_page, config=config)
        df = scraper.get_pre_rating()

        print(f"取得件数: {len(df)}件")
        print()
        print(df.to_string(index=False))

        # CSV保存
        csv_path = f"jra_pre_rating_{year}_{g1_page}.csv"
        scraper.save_to_csv(df, csv_path)
        print(f"CSVファイルを保存しました: {csv_path}")

    except Exception as e:
        print(f"エラーが発生しました: {e}")


if __name__ == "__main__":
    main()
