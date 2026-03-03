"""RaceListScraperの結合テスト

フィクスチャは使用せず、実際にnetkeibaにアクセスしてスクレイピングを行い、
RaceListScraperの各パブリックメソッドが正しく動作することを確認する。
netkeibaのHTML構造の仕様変更に気づきやすくすることが目的。

ネットワーク接続が必要なため、@pytest.mark.networkマーカーを付与する。
環境変数 RUN_NETWORK_TESTS=1 が設定されている場合のみ実行される（opt-in）。

負荷軽減のため、scrape_one_pageで1ページ分のみテストする。
"""

import os
import time
from typing import Any

import pandas as pd
import pytest

from scraping.config import RACE_LIST_COLUMNS
from scraping.race_list import RaceListScraper

# テスト間のリクエスト間隔（秒）
REQUEST_INTERVAL = 3.0
RUN_NETWORK_TESTS = os.environ.get("RUN_NETWORK_TESTS") == "1"

pytestmark = [
    pytest.mark.network,
    pytest.mark.skipif(
        not RUN_NETWORK_TESTS,
        reason="RUN_NETWORK_TESTS environment variable is not set",
    ),
]


# ---------------------------------------------------------------------------
# テストケース定義
# ---------------------------------------------------------------------------
LIVE_TEST_CASES: list[dict[str, Any]] = [
    {
        "year": 2025,
        "description": "2025年（直近年）",
        "min_pages": 3,
    },
    {
        "year": 2023,
        "description": "2023年（過去年）",
        "min_pages": 5,
    },
]

LIVE_TEST_CASE_IDS = [str(tc["description"]) for tc in LIVE_TEST_CASES]


# ---------------------------------------------------------------------------
# 正常系: max_page_numの取得
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("test_case", LIVE_TEST_CASES, ids=LIVE_TEST_CASE_IDS)
def test_max_page_num_is_positive(test_case: dict[str, Any]) -> None:
    """max_page_numが正の整数であること"""
    year = int(test_case["year"])
    scraper = RaceListScraper(year)

    assert scraper.max_page_num > 0
    assert scraper.max_page_num >= test_case["min_pages"]

    time.sleep(REQUEST_INTERVAL)


# ---------------------------------------------------------------------------
# 正常系: scrape_one_page（カラム構成）
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("test_case", LIVE_TEST_CASES, ids=LIVE_TEST_CASE_IDS)
def test_scrape_one_page_columns(test_case: dict[str, Any]) -> None:
    """scrape_one_pageがRACE_LIST_COLUMNSと一致するDataFrameを返すこと"""
    year = int(test_case["year"])
    scraper = RaceListScraper(year)

    df = scraper.scrape_one_page(1)

    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == RACE_LIST_COLUMNS
    assert len(df) > 0

    time.sleep(REQUEST_INTERVAL)


# ---------------------------------------------------------------------------
# 正常系: scrape_one_page（レースIDの形式）
# ---------------------------------------------------------------------------
def test_scrape_one_page_race_id_format() -> None:
    """レースIDが12桁の数字文字列であること"""
    scraper = RaceListScraper(2025)
    df = scraper.scrape_one_page(1)

    for race_id in df["レースID"]:
        assert (
            isinstance(race_id, str) and len(race_id) == 12 and race_id.isdigit()
        ), f"レースIDが不正: {race_id}"

    time.sleep(REQUEST_INTERVAL)


# ---------------------------------------------------------------------------
# 正常系: scrape_one_page（所属の値）
# ---------------------------------------------------------------------------
def test_scrape_one_page_affiliation_values() -> None:
    """所属が美浦/栗東/地方/海外/NaNのいずれかであること"""
    scraper = RaceListScraper(2025)
    df = scraper.scrape_one_page(1)

    valid = {"美浦", "栗東", "地方", "海外"}
    actual = set(df["所属"].dropna().unique())
    assert actual <= valid, f"不正な所属: {actual - valid}"

    time.sleep(REQUEST_INTERVAL)


# ---------------------------------------------------------------------------
# 正常系: scrape_one_page（芝ダの値）
# ---------------------------------------------------------------------------
def test_scrape_one_page_turf_dirt_values() -> None:
    """芝ダが芝/ダ/障のいずれかであること"""
    scraper = RaceListScraper(2025)
    df = scraper.scrape_one_page(1)

    valid = {"芝", "ダ", "障"}
    actual = set(df["芝ダ"].dropna().unique())
    assert actual <= valid, f"不正な芝ダ: {actual - valid}"

    time.sleep(REQUEST_INTERVAL)
