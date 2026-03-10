"""netkeibaオッズスクレイパーのサンプルスクリプト

指定したrace_idのオッズをnetkeibaから取得して表示する。
"""

import pandas as pd

from scraping.config import ScrapingConfig
from scraping.odds import scrape_odds_from_netkeiba


def main() -> None:
    """メイン処理

    race_idを指定してnetkeibaからオッズを取得し、結果を表示する。

    Raises:
        Exception: オッズ取得中にエラーが発生した場合
    """
    # スクレイピング対象のrace_id
    race_id = "202606020211"

    # 設定を初期化
    config = ScrapingConfig()

    print(f"レースID: {race_id}")
    print("=" * 80)

    try:
        # netkeibaからオッズを取得
        print("\n【オッズ情報取得中...】")
        odds_df = scrape_odds_from_netkeiba(race_id, config)

        if len(odds_df) == 0:
            print("馬券発売前のため、オッズ情報がありません")
            return

        print("\n【オッズ一覧】")
        pd.set_option("display.max_rows", None)
        pd.set_option("display.max_columns", None)
        pd.set_option("display.width", None)
        print(odds_df.to_string(index=False))

        # 統計情報
        print("\n【統計情報】")
        print(f"  頭数: {len(odds_df)}")
        valid_odds = odds_df["単勝オッズ"].dropna()
        print(f"  有効オッズ数: {len(valid_odds)}")
        if len(valid_odds) > 0:
            print(f"  単勝オッズ最小: {valid_odds.min():.1f}")
            print(f"  単勝オッズ最大: {valid_odds.max():.1f}")

        # 出走取消馬
        cancel_count = odds_df["単勝オッズ"].isna().sum()
        if cancel_count > 0:
            print(f"\n【出走取消/除外馬】{cancel_count}頭")
            cancel_df = odds_df[odds_df["単勝オッズ"].isna()]
            for _, row in cancel_df.iterrows():
                print(f"  馬番{int(row['馬番'])}")

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        raise


if __name__ == "__main__":
    main()
