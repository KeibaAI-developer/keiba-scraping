"""結果ページスクレイパーのサンプルスクリプト

指定したrace_idのレース結果ページから各種情報を取得して表示する。
"""

import pandas as pd

from scraping.config import ScrapingConfig
from scraping.result_page import ResultPageScraper


def main() -> None:
    """メイン処理

    race_idを指定してResultPageScraperで結果ページをスクレイピングし、
    レース情報・結果・コーナー通過順・払い戻し・ラップタイムを表示する。
    """
    # スクレイピング対象のrace_id
    race_id = "202306050911"

    # 設定を初期化
    config = ScrapingConfig()

    print(f"レースID: {race_id}")
    print("=" * 80)

    try:
        # ResultPageScraperを生成（HTTP取得とBeautifulSoup生成が行われる）
        scraper = ResultPageScraper(race_id, config)

        # レース情報
        print("\n【レース情報】")
        race_info_df = scraper.get_race_info()
        for col in race_info_df.columns:
            value = race_info_df.at[0, col]
            print(f"{col}: {value}")

        # レース結果
        print("\n【レース結果】")
        result_df = scraper.get_result()
        print(result_df)

        # コーナー通過順
        print("\n【コーナー通過順】")
        corner_df = scraper.get_corner()
        if corner_df.empty:
            print("コーナー通過順データなし（直線レース等）")
        else:
            for col in corner_df.columns:
                print(f"{col}: {corner_df.at[0, col]}")

        # 払い戻し
        print("\n【払い戻し】")
        payoff_methods = [
            ("単勝", scraper.get_win_payoff),
            ("複勝", scraper.get_show_payoff),
            ("枠連", scraper.get_bracket_payoff),
            ("馬連", scraper.get_quinella_payoff),
            ("ワイド", scraper.get_quinella_place_payoff),
            ("馬単", scraper.get_exacta_payoff),
            ("3連複", scraper.get_trio_payoff),
            ("3連単", scraper.get_trifecta_payoff),
        ]
        for bet_name, method in payoff_methods:
            print(f"\n  【{bet_name}】")
            payoff_df = method()
            if payoff_df.empty or len(payoff_df) == 0:
                print(f"    {bet_name}データなし")
                continue
            # 各カラムを順番に表示（NaNはスキップ）
            for col in payoff_df.columns:
                value = payoff_df.at[0, col]
                if pd.notna(value):
                    print(f"    {col}: {value}")

        # ラップタイム
        print("\n【ラップタイム】")
        lap_time_df = scraper.get_lap_time()
        if lap_time_df.empty:
            print("ラップタイムデータなし")
        else:
            # 各カラムを順番に表示（NaNはスキップ）
            for col in lap_time_df.columns:
                value = lap_time_df.at[0, col]
                if pd.notna(value):
                    print(f"  {col}: {value}")

    except Exception as e:
        print(f"エラーが発生しました: {e}")


if __name__ == "__main__":
    main()
