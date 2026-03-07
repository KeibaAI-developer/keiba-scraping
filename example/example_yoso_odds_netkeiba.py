"""netkeiba予想オッズスクレイパーのサンプルスクリプト

指定したrace_idの予想オッズをnetkeibaから取得して表示する。
馬券発売前のレースで使用する。Seleniumを使用してJavaScript生成のオッズを取得する。
"""

import pandas as pd

from scraping.config import ScrapingConfig
from scraping.odds import scrape_yoso_odds_from_netkeiba


def main() -> None:
    """メイン処理

    race_idを指定してnetkeibaから予想オッズを取得し、結果を表示する。

    Raises:
        Exception: オッズ取得中にエラーが発生した場合
    """
    # スクレイピング対象のrace_id（馬券発売前のレースIDを指定）
    race_id = "202606020411"

    # 設定を初期化
    config = ScrapingConfig()

    print(f"レースID: {race_id}")
    print("=" * 80)

    try:
        # netkeibaから予想オッズを取得
        print("\n【予想オッズ情報取得中...（Selenium使用）】")
        yoso_odds_df = scrape_yoso_odds_from_netkeiba(race_id, config)

        if len(yoso_odds_df) == 0:
            print("予想オッズ情報がありません")
            return

        print("\n【予想オッズ一覧】")
        pd.set_option("display.max_rows", None)
        pd.set_option("display.max_columns", None)
        pd.set_option("display.width", None)
        print(yoso_odds_df.to_string(index=False))

        # 統計情報
        print("\n【統計情報】")
        print(f"  頭数: {len(yoso_odds_df)}")
        valid_odds = yoso_odds_df["予想単勝オッズ"].dropna()
        print(f"  有効オッズ数: {len(valid_odds)}")
        if len(valid_odds) > 0:
            print(f"  予想オッズ最小: {valid_odds.min():.1f}")
            print(f"  予想オッズ最大: {valid_odds.max():.1f}")

        # 馬番情報
        valid_umaban = yoso_odds_df["馬番"].dropna()
        if len(valid_umaban) > 0:
            print(f"\n【枠順確定状況】確定済み（{len(valid_umaban)}頭）")
        else:
            print("\n【枠順確定状況】未確定（馬番がNaN）")

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        raise


if __name__ == "__main__":
    main()
