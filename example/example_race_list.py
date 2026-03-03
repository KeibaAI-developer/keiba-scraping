"""レース一覧スクレイパーのサンプルスクリプト

指定した年のレース一覧ページからレース情報を取得して表示する。
requestsを使用するため、ネットワーク接続が必要。
"""

from scraping.config import ScrapingConfig
from scraping.race_list import RaceListScraper


def main() -> None:
    """メイン処理

    年を指定してRaceListScraperでレース一覧ページをスクレイピングし、
    レース情報データを表示する。
    """
    # スクレイピング対象の年
    year = 2025

    # 設定を初期化
    config = ScrapingConfig()

    print(f"対象年: {year}")
    print("=" * 80)

    try:
        # RaceListScraperを生成（ページ数取得が行われる）
        scraper = RaceListScraper(year, config=config)
        print(f"最大ページ数: {scraper.max_page_num}")
        print()

        # 最初の1ページだけスクレイピング
        print("【1ページ目の先頭行】")
        df = scraper.scrape_one_page(1)
        for col in df.columns:
            print(f"  {col}: {df.iloc[0][col]}")

    except Exception as e:
        print(f"エラーが発生しました: {e}")


if __name__ == "__main__":
    main()
