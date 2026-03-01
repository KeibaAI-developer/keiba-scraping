"""馬柱スクレイパーのサンプルスクリプト

指定したhorse_idの馬情報ページから馬柱（過去の出走成績）を取得して表示する。
Seleniumを使用するため、Chrome/ChromeDriverが必要。
"""

from scraping.config import ScrapingConfig
from scraping.past_performances import PastPerformancesScraper


def main() -> None:
    """メイン処理

    horse_idを指定してPastPerformancesScraperで馬情報ページをスクレイピングし、
    馬柱データを表示する。
    """
    # スクレイピング対象のhorse_id
    horse_id = "2022105081"  # ミュージアムマイル

    # 設定を初期化
    config = ScrapingConfig()

    print(f"馬ID: {horse_id}")
    print("=" * 80)

    try:
        # PastPerformancesScraperを生成（Seleniumでページ取得が行われる）
        scraper = PastPerformancesScraper(horse_id, config)

        # 馬柱データ
        print("\n【馬柱データ】")
        df = scraper.get_past_performances()
        print(f"  レース数: {len(df)}件")
        print()

        if df.empty:
            print("  戦績なし（新馬）")
        else:
            for i, row in df.iterrows():
                print(f"--- {i + 1}走前---")
                for col in df.columns:
                    print(f"  {col}: {row[col]}")
                print()

    except Exception as e:
        print(f"エラーが発生しました: {e}")


if __name__ == "__main__":
    main()
