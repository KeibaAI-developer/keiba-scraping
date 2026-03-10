"""JRAオッズスクレイパーのサンプルスクリプト

指定したrace_idのオッズをJRA公式サイトから取得して表示する。
"""

import asyncio

import pandas as pd

from scraping.config import ScrapingConfig
from scraping.odds import scrape_odds_from_jra


async def main() -> None:
    """メイン処理

    race_idを指定してJRA公式サイトからオッズを取得し、結果を表示する。

    Raises:
        Exception: オッズ取得中にエラーが発生した場合
    """
    # スクレイピング対象のrace_id
    race_id = "202606020411"

    # 設定を初期化
    config = ScrapingConfig()

    print(f"レースID: {race_id}")
    print("=" * 80)

    try:
        # JRAからオッズを取得
        print("\n【JRAオッズ情報取得中...】")
        odds_df = await scrape_odds_from_jra(race_id, config)

        if len(odds_df) == 0:
            print("オッズ情報がありません")
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

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
