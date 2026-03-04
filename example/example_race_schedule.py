"""レーススケジュールスクレイパーのサンプルスクリプト

指定した日付のレーススケジュールページからレース情報を取得して表示する。
Seleniumを使用するため、Chrome/ChromeDriverが必要。
"""

from scraping.config import ScrapingConfig
from scraping.race_schedule import RaceScheduleScraper


def main() -> None:
    """メイン処理

    日付を指定してRaceScheduleScraperでレーススケジュールページをスクレイピングし、
    レーススケジュールデータを表示する。
    """
    # スクレイピング対象の日付
    year = 2026
    month = 2
    day = 8

    # 設定を初期化
    config = ScrapingConfig()

    print(f"対象日: {year}/{month:02d}/{day:02d}")
    print("=" * 80)

    try:
        # RaceScheduleScraperを生成（Seleniumでページ取得が行われる）
        scraper = RaceScheduleScraper(year, month, day, config)

        # レーススケジュールデータ
        print("\n【レーススケジュール】")
        df = scraper.get_race_schedule()
        print(f"  レース数: {len(df)}件")
        print()

        if df.empty:
            print("  開催なし")
        else:
            for i in range(len(df)):
                row = df.iloc[i]
                print(f"--- {row['R']}R ---")
                for col in df.columns:
                    print(f"  {col}: {row[col]}")
                print()

    except Exception as e:
        print(f"エラーが発生しました: {e}")


if __name__ == "__main__":
    main()
