"""HorseInfoScraperの結合テスト

フィクスチャは使用せず、実際にnetkeibaにアクセスしてスクレイピングを行い、
HorseInfoScraperの各パブリックメソッドが正しく動作することを確認する。
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

from scraping.config import HORSE_INFO_COLUMNS
from scraping.horse_info import HorseInfoScraper

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
        "year": 2022,
        "description": "2022年生まれ（通常年）",
        "min_pages": 50,
    },
    {
        "year": 2020,
        "description": "2020年生まれ（引退馬多数）",
        "min_pages": 50,
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
    scraper = HorseInfoScraper(year)

    assert scraper.max_page_num > 0
    assert scraper.max_page_num >= test_case["min_pages"]

    time.sleep(REQUEST_INTERVAL)


# ---------------------------------------------------------------------------
# 正常系: scrape_one_page（カラム構成）
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("test_case", LIVE_TEST_CASES, ids=LIVE_TEST_CASE_IDS)
def test_scrape_one_page_columns(test_case: dict[str, Any]) -> None:
    """scrape_one_pageがHORSE_INFO_COLUMNSと一致するDataFrameを返すこと"""
    year = int(test_case["year"])
    scraper = HorseInfoScraper(year)

    df = scraper.scrape_one_page(1)

    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == HORSE_INFO_COLUMNS
    assert len(df) > 0

    time.sleep(REQUEST_INTERVAL)


# ---------------------------------------------------------------------------
# 正常系: scrape_one_page（所属の値）
# ---------------------------------------------------------------------------
def test_scrape_one_page_affiliation_values() -> None:
    """所属が美浦/栗東/地方/海外/NaNのいずれかであること"""
    scraper = HorseInfoScraper(2022)
    df = scraper.scrape_one_page(1)

    valid = {"美浦", "栗東", "地方", "海外"}
    actual = set(df["所属"].dropna().unique())
    assert actual <= valid, f"不正な所属: {actual - valid}"

    time.sleep(REQUEST_INTERVAL)


# ---------------------------------------------------------------------------
# 正常系: scrape_one_page（馬IDの形式）
# ---------------------------------------------------------------------------
def test_scrape_one_page_horse_id_format() -> None:
    """馬IDが10桁の数字文字列であること"""
    scraper = HorseInfoScraper(2022)
    df = scraper.scrape_one_page(1)

    for horse_id in df["馬ID"]:
        assert (
            isinstance(horse_id, str) and len(horse_id) == 10 and horse_id.isdigit()
        ), f"馬IDが不正: {horse_id}"

    time.sleep(REQUEST_INTERVAL)


# ---------------------------------------------------------------------------
# 正常系: scrape_one_page（生年の一致）
# ---------------------------------------------------------------------------
def test_scrape_one_page_birth_year() -> None:
    """全行の生年がコンストラクタで指定した年と一致すること"""
    year = 2022
    scraper = HorseInfoScraper(year)
    df = scraper.scrape_one_page(1)

    assert (df["生年"] == year).all()

    time.sleep(REQUEST_INTERVAL)
