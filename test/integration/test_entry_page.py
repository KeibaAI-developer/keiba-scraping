"""EntryPageScraperの結合テスト

フィクスチャは使用せず、実際にnetkeibaにアクセスしてスクレイピングを行い、
EntryPageScraperの各パブリックメソッドが正しく動作することを確認する。
netkeibaのHTML構造の仕様変更に気づきやすくすることが目的。

ネットワーク接続が必要なため、@pytest.mark.networkマーカーを付与する。
環境変数 RUN_NETWORK_TESTS=1 が設定されている場合のみ実行される（opt-in）。
"""

import os
import time

import pandas as pd
import pytest

from scraping.config import (
    ENTRY_COLUMNS,
    ENTRY_NON_NAN_COLUMNS,
    RACE_INFO_COLUMNS,
    VALID_AFFILIATIONS,
    VALID_ENTRY_STATUSES,
    VALID_GENDERS,
)
from scraping.entry_page import EntryPageScraper

# テスト間のリクエスト間隔（秒）
REQUEST_INTERVAL = 1.5


# ---------------------------------------------------------------------------
# テストケース定義
# ---------------------------------------------------------------------------
LIVE_TEST_CASES = [
    {
        "race_id": "202505021211",
        "description": "日本ダービー2025（G1, 芝2400m, 18頭）",
        "expected_entry_count": 18,
        "is_obstacle": False,
    },
    {
        "race_id": "202306030111",
        "description": "鳴尾記念2023（G3, 芝2000m, 12頭）",
        "expected_entry_count": 12,
        "is_obstacle": False,
    },
    {
        "race_id": "202406050710",
        "description": "中山大障害2024（障害, 4100m）",
        "expected_entry_count": 9,
        "is_obstacle": True,
    },
]

LIVE_TEST_CASE_IDS = [str(tc["description"]) for tc in LIVE_TEST_CASES]


# ---------------------------------------------------------------------------
# 正常系: get_race_info
# ---------------------------------------------------------------------------
@pytest.mark.network
@pytest.mark.parametrize("test_case", LIVE_TEST_CASES, ids=LIVE_TEST_CASE_IDS)
def test_get_race_info_returns_valid_dataframe(test_case: dict[str, object]) -> None:
    """get_race_infoがRACE_INFO_COLUMNSと一致する1行DataFrameを返すこと."""
    if not os.environ.get("RUN_NETWORK_TESTS"):
        pytest.skip("RUN_NETWORK_TESTS environment variable is not set")

    race_id = str(test_case["race_id"])
    scraper = EntryPageScraper(race_id)
    df = scraper.get_race_info()

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert list(df.columns) == RACE_INFO_COLUMNS
    assert df["レースID"].iloc[0] == race_id

    time.sleep(REQUEST_INTERVAL)


# ---------------------------------------------------------------------------
# 正常系: get_entry（カラム・行数）
# ---------------------------------------------------------------------------
@pytest.mark.network
@pytest.mark.parametrize("test_case", LIVE_TEST_CASES, ids=LIVE_TEST_CASE_IDS)
def test_get_entry_returns_valid_dataframe(test_case: dict[str, object]) -> None:
    """get_entryがENTRY_COLUMNSと一致するDataFrameを返すこと."""
    if not os.environ.get("RUN_NETWORK_TESTS"):
        pytest.skip("RUN_NETWORK_TESTS environment variable is not set")

    race_id = str(test_case["race_id"])
    expected_count = test_case["expected_entry_count"]
    assert isinstance(expected_count, int)

    scraper = EntryPageScraper(race_id)
    df = scraper.get_entry()

    assert isinstance(df, pd.DataFrame)
    assert len(df) == expected_count
    assert list(df.columns) == ENTRY_COLUMNS
    assert (df["レースID"] == race_id).all()

    time.sleep(REQUEST_INTERVAL)


# ---------------------------------------------------------------------------
# 正常系: get_entry（NaN不可カラム）
# ---------------------------------------------------------------------------
@pytest.mark.network
@pytest.mark.parametrize("test_case", LIVE_TEST_CASES, ids=LIVE_TEST_CASE_IDS)
def test_get_entry_non_nan_columns_have_no_nan(test_case: dict[str, object]) -> None:
    """get_entryのNaN不可カラムにNaN値が含まれないこと."""
    if not os.environ.get("RUN_NETWORK_TESTS"):
        pytest.skip("RUN_NETWORK_TESTS environment variable is not set")

    race_id = str(test_case["race_id"])
    scraper = EntryPageScraper(race_id)
    df = scraper.get_entry()

    for col in ENTRY_NON_NAN_COLUMNS:
        assert df[col].notna().all(), f"'{col}'にNaN値が含まれています"

    time.sleep(REQUEST_INTERVAL)


# ---------------------------------------------------------------------------
# 正常系: get_entry（性別の値）
# ---------------------------------------------------------------------------
@pytest.mark.network
@pytest.mark.parametrize("test_case", LIVE_TEST_CASES, ids=LIVE_TEST_CASE_IDS)
def test_get_entry_gender_values_are_valid(test_case: dict[str, object]) -> None:
    """get_entryの性別がVALID_GENDERSに含まれること."""
    if not os.environ.get("RUN_NETWORK_TESTS"):
        pytest.skip("RUN_NETWORK_TESTS environment variable is not set")

    race_id = str(test_case["race_id"])
    scraper = EntryPageScraper(race_id)
    df = scraper.get_entry()

    invalid = set(df["性別"].unique()) - VALID_GENDERS
    assert invalid == set(), f"不正な性別値: {invalid}"

    time.sleep(REQUEST_INTERVAL)


# ---------------------------------------------------------------------------
# 正常系: get_entry（所属の値）
# ---------------------------------------------------------------------------
@pytest.mark.network
@pytest.mark.parametrize("test_case", LIVE_TEST_CASES, ids=LIVE_TEST_CASE_IDS)
def test_get_entry_affiliation_values_are_valid(test_case: dict[str, object]) -> None:
    """get_entryの所属がVALID_AFFILIATIONSに含まれること."""
    if not os.environ.get("RUN_NETWORK_TESTS"):
        pytest.skip("RUN_NETWORK_TESTS environment variable is not set")

    race_id = str(test_case["race_id"])
    scraper = EntryPageScraper(race_id)
    df = scraper.get_entry()

    invalid = set(df["所属"].unique()) - VALID_AFFILIATIONS
    assert invalid == set(), f"不正な所属値: {invalid}"

    time.sleep(REQUEST_INTERVAL)


# ---------------------------------------------------------------------------
# 正常系: get_entry（出走区分の値）
# ---------------------------------------------------------------------------
@pytest.mark.network
@pytest.mark.parametrize("test_case", LIVE_TEST_CASES, ids=LIVE_TEST_CASE_IDS)
def test_get_entry_status_values_are_valid(test_case: dict[str, object]) -> None:
    """get_entryの出走区分がVALID_ENTRY_STATUSESに含まれること."""
    if not os.environ.get("RUN_NETWORK_TESTS"):
        pytest.skip("RUN_NETWORK_TESTS environment variable is not set")

    race_id = str(test_case["race_id"])
    scraper = EntryPageScraper(race_id)
    df = scraper.get_entry()

    invalid = set(df["出走区分"].unique()) - VALID_ENTRY_STATUSES
    assert invalid == set(), f"不正な出走区分値: {invalid}"

    time.sleep(REQUEST_INTERVAL)


# ---------------------------------------------------------------------------
# 正常系: get_entry（IDカラムの形式）
# ---------------------------------------------------------------------------
@pytest.mark.network
@pytest.mark.parametrize("test_case", LIVE_TEST_CASES, ids=LIVE_TEST_CASE_IDS)
def test_get_entry_id_columns_are_digit_strings(test_case: dict[str, object]) -> None:
    """get_entryの馬ID・騎手ID・厩舎IDが数字のみの文字列であること."""
    if not os.environ.get("RUN_NETWORK_TESTS"):
        pytest.skip("RUN_NETWORK_TESTS environment variable is not set")

    race_id = str(test_case["race_id"])
    scraper = EntryPageScraper(race_id)
    df = scraper.get_entry()

    for col in ["馬ID", "騎手ID", "厩舎ID"]:
        non_nan = df[col].dropna()
        assert non_nan.str.match(r"^\d+$").all(), f"'{col}'に数字以外の値が含まれています"

    time.sleep(REQUEST_INTERVAL)
