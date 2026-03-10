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
        non_id_cols = [c for c in result_df.columns if c != "レースID"]
        if result_df[non_id_cols].iloc[0].isna().all():
            print("開催中止のためレース結果なし")
        else:
            print(result_df)

        # コーナー通過順
        print("\n【コーナー通過順】")
        corner_df = scraper.get_corner()
        corner_cols = ["1コーナー通過順", "2コーナー通過順", "3コーナー通過順", "4コーナー通過順"]
        if corner_df[corner_cols].iloc[0].isna().all():
            print("コーナー通過順データなし（直線レース等）")
        else:
            for col in corner_cols:
                value = corner_df.at[0, col]
                if pd.notna(value):
                    print(f"{col}: {value}")

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
            non_id_cols = [c for c in payoff_df.columns if c != "レースID"]
            if payoff_df[non_id_cols].iloc[0].isna().all():
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
        non_id_cols = [c for c in lap_time_df.columns if c != "レースID"]
        if lap_time_df[non_id_cols].iloc[0].isna().all():
            print("ラップタイムデータなし（障害レース等）")
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
