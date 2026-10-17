"""JRA調教後馬体重スクレイパーのサンプルスクリプト

指定したG1の出走馬の調教後馬体重をJRA公式サイトから取得して表示する。
requestsを使用するため、ネットワーク接続が必要。
"""

from scraping.config import ScrapingConfig
from scraping.jra_chokyo_bataiju import JraChokyoBataijuScraper


def main() -> None:
    """メイン処理

    G1特設ページ名を指定してJraChokyoBataijuScraperで調教後馬体重をスクレイピングし、
    データを表示とCSV保存する。
    """
    # JRAのG1特設ページ名（https://www.jra.go.jp/keiba/g1/shuka/ の shuka）
    g1_page = "shuka"

    # 設定を初期化
    config = ScrapingConfig()

    print(f"対象G1特設ページ: {g1_page}")
    print("=" * 80)

    try:
        scraper = JraChokyoBataijuScraper(g1_page, config=config)
        df = scraper.get_chokyo_bataiju()

        print(f"取得件数: {len(df)}件")
        print()
        print(df.to_string(index=False))

        # CSV保存
        csv_path = f"jra_chokyo_bataiju_{g1_page}.csv"
        scraper.save_to_csv(df, csv_path)
        print(f"CSVファイルを保存しました: {csv_path}")

    except Exception as e:
        print(f"エラーが発生しました: {e}")


if __name__ == "__main__":
    main()
