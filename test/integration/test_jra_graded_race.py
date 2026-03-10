"""JraGradedRaceScraperの結合テスト

フィクスチャは使用せず、実際にJRA公式サイトにアクセスしてスクレイピングを行い、
JraGradedRaceScraperの各パブリックメソッドが正しく動作することを確認する。
JRAサイトのHTML構造の仕様変更に気づきやすくすることが目的。

ネットワーク接続が必要なため、@pytest.mark.networkマーカーを付与する。
環境変数 RUN_NETWORK_TESTS=1 が設定されている場合のみ実行される（opt-in）。
"""

import datetime
import os
import tempfile
import time
from typing import Any

import pandas as pd
import pytest

from scraping.config import JRA_GRADED_RACE_COLUMNS
from scraping.jra_graded_race import JraGradedRaceScraper

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

# グレードの許容値（ローマ数字Ⅰ/Ⅱ/Ⅲ = U+2160/2161/2162、障害はJ・プレフィックス）
VALID_GRADES = {"GⅠ", "GⅡ", "GⅢ", "J・GⅠ", "J・GⅡ", "J・GⅢ"}

# 芝ダの許容値
VALID_TURF_DIRT = {"芝", "ダ", "障"}

# JRA競馬場名
VALID_PLACES = {"札幌", "函館", "福島", "新潟", "東京", "中山", "中京", "京都", "阪神", "小倉"}


# ---------------------------------------------------------------------------
# テストケース定義
# ---------------------------------------------------------------------------
LIVE_TEST_CASES: list[dict[str, Any]] = [
    {
        "year": 2024,
        "description": "2024年（確定済み年）",
        "min_rows": 100,
    },
    {
        "year": 2023,
        "description": "2023年（過去年）",
        "min_rows": 100,
    },
]

LIVE_TEST_CASE_IDS = [str(tc["description"]) for tc in LIVE_TEST_CASES]


# ---------------------------------------------------------------------------
# 正常系: カラム構成
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("test_case", LIVE_TEST_CASES, ids=LIVE_TEST_CASE_IDS)
def test_get_graded_races_columns(test_case: dict[str, Any]) -> None:
    """get_graded_racesがJRA_GRADED_RACE_COLUMNSと一致するDataFrameを返すこと"""
    year = int(test_case["year"])
    scraper = JraGradedRaceScraper(year)
    df = scraper.get_graded_races()

    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == JRA_GRADED_RACE_COLUMNS

    time.sleep(REQUEST_INTERVAL)


# ---------------------------------------------------------------------------
# 正常系: 行数
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("test_case", LIVE_TEST_CASES, ids=LIVE_TEST_CASE_IDS)
def test_get_graded_races_row_count(test_case: dict[str, Any]) -> None:
    """確定済み年のデータが最低行数以上取得できること"""
    year = int(test_case["year"])
    min_rows = int(test_case["min_rows"])
    scraper = JraGradedRaceScraper(year)
    df = scraper.get_graded_races()

    assert len(df) >= min_rows, f"{year}年のデータが{min_rows}行未満: {len(df)}行"

    time.sleep(REQUEST_INTERVAL)


# ---------------------------------------------------------------------------
# 正常系: 日付カラムの型と範囲
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("test_case", LIVE_TEST_CASES, ids=LIVE_TEST_CASE_IDS)
def test_get_graded_races_date_values(test_case: dict[str, Any]) -> None:
    """日付カラムがdatetime.date型で対象年の範囲内であること"""
    year = int(test_case["year"])
    scraper = JraGradedRaceScraper(year)
    df = scraper.get_graded_races()

    for date_val in df["日付"]:
        assert isinstance(date_val, datetime.date)
        assert date_val.year == year

    time.sleep(REQUEST_INTERVAL)


# ---------------------------------------------------------------------------
# 正常系: グレードの値
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("test_case", LIVE_TEST_CASES, ids=LIVE_TEST_CASE_IDS)
def test_get_graded_races_grade_values(test_case: dict[str, Any]) -> None:
    """グレードカラムが許容値のいずれかであること"""
    year = int(test_case["year"])
    scraper = JraGradedRaceScraper(year)
    df = scraper.get_graded_races()

    invalid = set(df["グレード"].unique()) - VALID_GRADES
    assert invalid == set(), f"不正なグレード値: {invalid}"

    time.sleep(REQUEST_INTERVAL)


# ---------------------------------------------------------------------------
# 正常系: 競馬場の値
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("test_case", LIVE_TEST_CASES, ids=LIVE_TEST_CASE_IDS)
def test_get_graded_races_place_values(test_case: dict[str, Any]) -> None:
    """競馬場カラムがJRAの10場のいずれかであること"""
    year = int(test_case["year"])
    scraper = JraGradedRaceScraper(year)
    df = scraper.get_graded_races()

    invalid = set(df["競馬場"].unique()) - VALID_PLACES
    assert invalid == set(), f"不正な競馬場値: {invalid}"

    time.sleep(REQUEST_INTERVAL)


# ---------------------------------------------------------------------------
# 正常系: 芝ダの値
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("test_case", LIVE_TEST_CASES, ids=LIVE_TEST_CASE_IDS)
def test_get_graded_races_turf_dirt_values(test_case: dict[str, Any]) -> None:
    """芝ダカラムが許容値のいずれかであること"""
    year = int(test_case["year"])
    scraper = JraGradedRaceScraper(year)
    df = scraper.get_graded_races()

    invalid = set(df["芝ダ"].unique()) - VALID_TURF_DIRT
    assert invalid == set(), f"不正な芝ダ値: {invalid}"

    time.sleep(REQUEST_INTERVAL)


# ---------------------------------------------------------------------------
# 正常系: 距離の値
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("test_case", LIVE_TEST_CASES, ids=LIVE_TEST_CASE_IDS)
def test_get_graded_races_distance_values(test_case: dict[str, Any]) -> None:
    """距離カラムがint型で妥当な範囲（800m〜4500m）であること"""
    year = int(test_case["year"])
    scraper = JraGradedRaceScraper(year)
    df = scraper.get_graded_races()

    for distance in df["距離"]:
        assert isinstance(distance, int)
        assert 800 <= distance <= 4500, f"距離が異常値: {distance}"

    time.sleep(REQUEST_INTERVAL)


# ---------------------------------------------------------------------------
# 正常系: NaN値がないこと
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("test_case", LIVE_TEST_CASES, ids=LIVE_TEST_CASE_IDS)
def test_get_graded_races_no_nan(test_case: dict[str, Any]) -> None:
    """全カラムにNaN値が含まれないこと"""
    year = int(test_case["year"])
    scraper = JraGradedRaceScraper(year)
    df = scraper.get_graded_races()

    for col in JRA_GRADED_RACE_COLUMNS:
        assert df[col].notna().all(), f"'{col}'にNaN値が含まれています"

    time.sleep(REQUEST_INTERVAL)


# ---------------------------------------------------------------------------
# 正常系: 優勝馬・騎手が空文字でないこと
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("test_case", LIVE_TEST_CASES, ids=LIVE_TEST_CASE_IDS)
def test_get_graded_races_winner_jockey_not_empty(test_case: dict[str, Any]) -> None:
    """優勝馬と騎手が空文字でないこと"""
    year = int(test_case["year"])
    scraper = JraGradedRaceScraper(year)
    df = scraper.get_graded_races()

    for col in ["優勝馬", "騎手"]:
        assert (df[col].str.strip() != "").all(), f"'{col}'に空文字が含まれています"

    time.sleep(REQUEST_INTERVAL)


# ---------------------------------------------------------------------------
# 正常系: save_to_csvでCSVファイルが作成されること
# ---------------------------------------------------------------------------
def test_save_to_csv_creates_file() -> None:
    """save_to_csvでCSVファイルが正しく作成・復元できること"""
    scraper = JraGradedRaceScraper(2024)
    df = scraper.get_graded_races()

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
        filepath = f.name

    try:
        scraper.save_to_csv(df, filepath)

        loaded = pd.read_csv(filepath)
        assert len(loaded) == len(df)
        assert list(loaded.columns) == JRA_GRADED_RACE_COLUMNS
    finally:
        os.unlink(filepath)

    time.sleep(REQUEST_INTERVAL)
