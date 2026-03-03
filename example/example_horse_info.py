"""馬情報スクレイパーのサンプルスクリプト

指定した生年の馬情報一覧ページから馬情報を取得して表示する。
requestsを使用するため、ネットワーク接続が必要。
"""

from scraping.config import ScrapingConfig
from scraping.horse_info import HorseInfoScraper


def main() -> None:
    """メイン処理

    生年を指定してHorseInfoScraperで馬情報一覧ページをスクレイピングし、
    馬情報データを表示する。
    """
    # スクレイピング対象の生年
    year = 2022

    # 設定を初期化
    config = ScrapingConfig()

    print(f"生年: {year}")
    print("=" * 80)

    try:
        # HorseInfoScraperを生成（ページ数取得が行われる）
        scraper = HorseInfoScraper(year, config=config)
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
