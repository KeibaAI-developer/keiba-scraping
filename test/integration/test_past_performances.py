"""PastPerformancesScraperの結合テスト

フィクスチャは使用せず、実際にnetkeibaにアクセスしてスクレイピングを行い、
PastPerformancesScraperの各パブリックメソッドが正しく動作することを確認する。
netkeibaのHTML構造の仕様変更に気づきやすくすることが目的。

ネットワーク接続が必要なため、@pytest.mark.networkマーカーを付与する。
環境変数 RUN_NETWORK_TESTS=1 が設定されている場合のみ実行される（opt-in）。
"""

import datetime
import os
import time
from typing import Any

import pandas as pd
import pytest

from scraping.config import PAST_PERFORMANCES_COLUMNS
from scraping.past_performances import PastPerformancesScraper

# テスト間のリクエスト間隔（秒）: Seleniumなので長めに設定
REQUEST_INTERVAL = 5.0
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
        "horse_id": "2022105081",
        "description": "ミュージアムマイル（中央・芝）",
        "min_rows": 5,
    },
    {
        "horse_id": "2011101125",
        "description": "オジュウチョウサン（障害経験あり）",
        "min_rows": 30,
    },
    {
        "horse_id": "2021105727",
        "description": "フォーエバーヤング（中央・海外・地方）",
        "min_rows": 10,
    },
]

LIVE_TEST_CASE_IDS = [str(tc["description"]) for tc in LIVE_TEST_CASES]


# ---------------------------------------------------------------------------
# 正常系: get_past_performances（カラム構成）
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("test_case", LIVE_TEST_CASES, ids=LIVE_TEST_CASE_IDS)
def test_get_past_performances_columns(test_case: dict[str, Any]) -> None:
    """get_past_performancesがPAST_PERFORMANCES_COLUMNSと一致するDataFrameを返すこと"""
    horse_id = str(test_case["horse_id"])
    scraper = PastPerformancesScraper(horse_id)
    df = scraper.get_past_performances()

    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == PAST_PERFORMANCES_COLUMNS

    time.sleep(REQUEST_INTERVAL)


# ---------------------------------------------------------------------------
# 正常系: get_past_performances（行数）
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("test_case", LIVE_TEST_CASES, ids=LIVE_TEST_CASE_IDS)
def test_get_past_performances_row_count(test_case: dict[str, Any]) -> None:
    """get_past_performancesが期待される最小行数以上のDataFrameを返すこと"""
    horse_id = str(test_case["horse_id"])
    min_rows = int(test_case["min_rows"])

    scraper = PastPerformancesScraper(horse_id)
    df = scraper.get_past_performances()

    assert len(df) >= min_rows

    time.sleep(REQUEST_INTERVAL)


# ---------------------------------------------------------------------------
# 正常系: get_past_performances（日付型）
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("test_case", LIVE_TEST_CASES, ids=LIVE_TEST_CASE_IDS)
def test_get_past_performances_date_type(test_case: dict[str, Any]) -> None:
    """日付カラムがdatetime.date型であること"""
    horse_id = str(test_case["horse_id"])
    scraper = PastPerformancesScraper(horse_id)
    df = scraper.get_past_performances()

    for val in df["日付"]:
        assert isinstance(val, datetime.date)

    time.sleep(REQUEST_INTERVAL)


# ---------------------------------------------------------------------------
# 正常系: get_past_performances（芝ダの値）
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("test_case", LIVE_TEST_CASES, ids=LIVE_TEST_CASE_IDS)
def test_get_past_performances_turf_dirt_values(test_case: dict[str, Any]) -> None:
    """芝ダが芝/ダ/障のいずれかであること"""
    horse_id = str(test_case["horse_id"])
    scraper = PastPerformancesScraper(horse_id)
    df = scraper.get_past_performances()

    valid = {"芝", "ダ", "障"}
    invalid = set(df["芝ダ"].dropna().unique()) - valid
    assert invalid == set(), f"不正な芝ダ値: {invalid}"

    time.sleep(REQUEST_INTERVAL)


# ---------------------------------------------------------------------------
# 正常系: get_past_performances（主催の値）
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("test_case", LIVE_TEST_CASES, ids=LIVE_TEST_CASE_IDS)
def test_get_past_performances_organize_values(test_case: dict[str, Any]) -> None:
    """主催が中央/地方/海外のいずれかであること"""
    horse_id = str(test_case["horse_id"])
    scraper = PastPerformancesScraper(horse_id)
    df = scraper.get_past_performances()

    valid = {"中央", "地方", "海外"}
    invalid = set(df["主催"].unique()) - valid
    assert invalid == set(), f"不正な主催値: {invalid}"

    time.sleep(REQUEST_INTERVAL)


# ---------------------------------------------------------------------------
# 正常系: get_past_performances（騎手IDの形式）
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("test_case", LIVE_TEST_CASES, ids=LIVE_TEST_CASE_IDS)
def test_get_past_performances_jockey_id_format(test_case: dict[str, Any]) -> None:
    """騎手IDが5桁の数字文字列であること（NaN以外）"""
    horse_id = str(test_case["horse_id"])
    scraper = PastPerformancesScraper(horse_id)
    df = scraper.get_past_performances()

    for jockey_id in df["騎手ID"].dropna():
        assert (
            isinstance(jockey_id, str) and len(jockey_id) == 5 and jockey_id.isdigit()
        ), f"騎手IDが不正: {jockey_id}"

    time.sleep(REQUEST_INTERVAL)
