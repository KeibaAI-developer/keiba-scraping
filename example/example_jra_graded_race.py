"""JRA重賞レース一覧スクレイパーのサンプルスクリプト

指定した年の重賞レース一覧をJRA公式サイトから取得して表示する。
requestsを使用するため、ネットワーク接続が必要。
"""

from scraping.config import ScrapingConfig
from scraping.jra_graded_race import JraGradedRaceScraper


def main() -> None:
    """メイン処理

    年を指定してJraGradedRaceScraperで重賞レース一覧をスクレイピングし、
    データを表示とCSV保存する。
    """
    # スクレイピング対象の年
    year = 2025

    # 設定を初期化
    config = ScrapingConfig()

    print(f"対象年: {year}")
    print("=" * 80)

    try:
        scraper = JraGradedRaceScraper(year, config=config)
        df = scraper.get_graded_races()

        if df.empty:
            print("データが取得できませんでした。")
            return

        print(f"取得件数: {len(df)}件")
        print()

        # 先頭5行を表示
        print("【先頭5行】")
        for i in range(min(5, len(df))):
            print(f"--- {i + 1}行目 ---")
            for col in df.columns:
                print(f"  {col}: {df.iloc[i][col]}")
            print()

        # CSV保存
        csv_path = f"jra_graded_races_{year}.csv"
        scraper.save_to_csv(df, csv_path)
        print(f"CSVファイルを保存しました: {csv_path}")

    except Exception as e:
        print(f"エラーが発生しました: {e}")


if __name__ == "__main__":
    main()
