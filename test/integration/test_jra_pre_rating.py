"""JraPreRatingScraperの結合テスト

フィクスチャは使用せず、実際にJRA公式サイトにアクセスしてスクレイピングを行い、
JraPreRatingScraper.get_pre_rating()が正しく動作することを確認する。
JRAサイトのHTML構造の仕様変更に気づきやすくすることが目的。

ネットワーク接続が必要なため、@pytest.mark.networkマーカーを付与する。
環境変数 RUN_NETWORK_TESTS=1 が設定されている場合のみ実行される（opt-in）。
"""

import os
import time
from typing import Any

import pandas as pd
import pytest

from scraping.config import JRA_PRE_RATING_COLUMNS
from scraping.jra_pre_rating import JraPreRatingScraper

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
        "g1_page": "eliza",
        "description": "2017年以降の形（2025年エリザベス女王杯）",
        "rows": 19,
        "has_previous": False,
    },
    {
        "year": 2025,
        "g1_page": "osaka",
        "description": "2017年以降の形で前年のJPNランキングあり（2025年大阪杯）",
        "rows": None,
        "has_previous": True,
    },
    {
        "year": 2016,
        "g1_page": "eliza",
        "description": "2016年以前の形（2016年エリザベス女王杯）",
        "rows": 16,
        "has_previous": False,
    },
]

LIVE_TEST_CASE_IDS = [str(tc["description"]) for tc in LIVE_TEST_CASES]


# ---------------------------------------------------------------------------
# 正常系
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("test_case", LIVE_TEST_CASES, ids=LIVE_TEST_CASE_IDS)
def test_get_pre_rating(test_case: dict[str, Any]) -> None:
    """公開済みのページから、列が揃い、レーティングを持つ馬がいるDataFrameを取得できること"""
    scraper = JraPreRatingScraper(int(test_case["year"]), str(test_case["g1_page"]))
    df = scraper.get_pre_rating()

    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == JRA_PRE_RATING_COLUMNS
    if test_case["rows"] is not None:
        assert len(df) == test_case["rows"]
    assert df["レーティング"].notna().any()
    assert df["前年レーティング"].notna().any() == test_case["has_previous"]

    time.sleep(REQUEST_INTERVAL)
