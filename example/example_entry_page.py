"""出馬表ページスクレイパーのサンプルスクリプト

指定したrace_idの出馬表ページからレース情報・出馬表を取得して表示する。
"""

from scraping.config import ScrapingConfig
from scraping.entry_page import EntryPageScraper


def main() -> None:
    """メイン処理

    race_idを指定してEntryPageScraperで出馬表ページをスクレイピングし、
    レース情報・出馬表を表示する。
    """
    # スクレイピング対象のrace_id
    race_id = "202607010211"

    # 設定を初期化
    config = ScrapingConfig()

    print(f"レースID: {race_id}")
    print("=" * 80)

    try:
        # EntryPageScraperを生成（HTTP取得とBeautifulSoup生成が行われる）
        scraper = EntryPageScraper(race_id, config)

        # レース情報
        print("\n【レース情報】")
        race_info_df = scraper.get_race_info()
        for col in race_info_df.columns:
            value = race_info_df.at[0, col]
            print(f"  {col}: {value}")

        # 出馬表
        print("\n【出馬表】")
        entry_df = scraper.get_entry()
        print(f"  出走頭数: {len(entry_df)}頭")
        print()
        print(entry_df.to_string(index=False))

    except Exception as e:
        print(f"エラーが発生しました: {e}")


if __name__ == "__main__":
    main()
