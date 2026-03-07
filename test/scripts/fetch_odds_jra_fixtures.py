"""JRAオッズページのCSVフィクスチャ取得スクリプト

JRA公式サイトからPlaywrightでオッズページを操作し、
pd.read_htmlの結果をCSVファイルとして保存する。

JRAはページ操作が複雑でHTMLフィクスチャの静的保存が困難なため、
テーブルデータをCSVとして保存する。

使用方法:
    python test/scripts/fetch_odds_jra_fixtures.py
"""

import asyncio
import os
from dataclasses import dataclass
from io import StringIO

import pandas as pd
from playwright.async_api import async_playwright

# フィクスチャ保存先ディレクトリ
FIXTURES_DIR_CSV = os.path.join(os.path.dirname(__file__), "..", "fixtures", "csv")

# JRA公式サイトのURL
JRA_URL = "https://www.jra.go.jp"


@dataclass
class TargetRace:
    """フィクスチャ取得対象のレース情報"""

    race_id: str
    description: str
    kai: int
    keibajo: str
    day: int
    race: int


# 取得対象のレースID
TARGET_RACES: list[TargetRace] = [
    TargetRace(
        race_id="202606020411",
        description="正常系",
        kai=2,
        keibajo="中山",
        day=4,
        race=11,
    ),
]


async def fetch_odds_from_jra(
    kai: int,
    keibajo: str,
    day: int,
    race: int,
) -> pd.DataFrame:
    """JRA公式サイトからオッズテーブルを取得する

    Args:
        kai (int): 開催回
        keibajo (str): 競馬場名
        day (int): 開催日
        race (int): レース番号

    Returns:
        pd.DataFrame: pd.read_htmlで取得したオッズテーブル
    """
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto(JRA_URL)
        await page.get_by_role("link", name="オッズ", exact=True).click()
        await page.get_by_role("link", name=f"{kai}回{keibajo}{day}日").click()

        async with page.expect_navigation():
            await page.get_by_role("link", name=f"{race}レース", exact=True).nth(0).click()

        html = await page.content()
        raw_df = pd.read_html(StringIO(html))[0]

        await context.close()
        await browser.close()

    return raw_df


async def main() -> None:
    """メイン処理"""
    os.makedirs(FIXTURES_DIR_CSV, exist_ok=True)

    for target in TARGET_RACES:
        race_id = target.race_id
        description = target.description
        print(f"取得中: {race_id} ({description})")

        raw_df = await fetch_odds_from_jra(
            kai=target.kai,
            keibajo=target.keibajo,
            day=target.day,
            race=target.race,
        )

        csv_path = os.path.join(FIXTURES_DIR_CSV, f"odds_jra_{race_id}.csv")
        raw_df.to_csv(csv_path, index=False, encoding="utf-8")
        print(f"  保存完了: {csv_path}")
        print(f"  カラム: {list(raw_df.columns)}")
        print(f"  行数: {len(raw_df)}")
        print(raw_df.head())
        print()


if __name__ == "__main__":
    asyncio.run(main())
