"""馬ページスクレイパーのサンプルスクリプト

指定したhorse_idの馬情報ページから馬柱（過去の出走成績）および馬の基本情報を取得して表示する。
Seleniumを使用するため、Chrome/ChromeDriverが必要。
"""

from scraping.config import ScrapingConfig
from scraping.horse_page import HorsePageScraper


def main() -> None:
    """メイン処理

    horse_idを指定してHorsePageScraperで馬情報ページをスクレイピングし、
    馬柱データを表示する。
    """
    # スクレイピング対象のhorse_id
    horse_id = "2022105081"  # ミュージアムマイル

    # 設定を初期化
    config = ScrapingConfig()

    print(f"馬ID: {horse_id}")
    print("=" * 80)

    try:
        # HorsePageScraperを生成（Seleniumでページ取得が行われる）
        scraper = HorsePageScraper(horse_id, config)

        # 馬柱データ
        print("\n【馬柱データ】")
        df = scraper.get_past_performances()
        print(f"  レース数: {len(df)}件")
        print()

        if df.empty:
            print("  戦績なし（新馬）")
        else:
            for i, (_, row) in enumerate(df.iterrows()):
                print(f"--- {i + 1}走前---")
                for col in df.columns:
                    print(f"  {col}: {row[col]}")
                print()

        # 馬基本情報
        print("\n【馬基本情報】")
        info_df = scraper.get_horse_basic_info()
        row = info_df.iloc[0]
        for col in info_df.columns:
            print(f"  {col}: {row[col]}")

    except Exception as e:
        print(f"エラーが発生しました: {e}")


if __name__ == "__main__":
    main()
