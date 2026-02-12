"""ResultPageScraperの結合テスト

フィクスチャは使用せず、実際にnetkeibaにアクセスしてスクレイピングを行い、
ResultPageScraperの各パブリックメソッドが正しく動作することを確認する。
netkeibaのHTML構造の仕様変更に気づきやすくすることが目的。

ネットワーク接続が必要なため、@pytest.mark.networkマーカーを付与する。
環境変数 RUN_NETWORK_TESTS=1 が設定されている場合のみ実行される（opt-in）。
"""

import os
import time

import pandas as pd
import pytest

from scraping.config import (
    BRACKET_PAYOFF_COLUMNS,
    CORNER_COLUMNS,
    EXACTA_PAYOFF_COLUMNS,
    LAP_TIME_COLUMNS,
    QUINELLA_PAYOFF_COLUMNS,
    QUINELLA_PLACE_PAYOFF_COLUMNS,
    RACE_INFO_COLUMNS,
    RESULT_COLUMNS,
    SHOW_PAYOFF_COLUMNS,
    TRIFECTA_PAYOFF_COLUMNS,
    TRIO_PAYOFF_COLUMNS,
    WIN_PAYOFF_COLUMNS,
)
from scraping.result_page import ResultPageScraper

# テスト間のリクエスト間隔（秒）
REQUEST_INTERVAL = 1.5


# ---------------------------------------------------------------------------
# テストケース定義
# ---------------------------------------------------------------------------
LIVE_TEST_CASES = [
    {
        "race_id": "202505021211",
        "description": "日本ダービー2025（G1, 芝2400m）",
        "expected_result_count": 18,
        "has_lap_time": True,
        "is_obstacle": False,
    },
    {
        "race_id": "202306030111",
        "description": "日経賞2023（G2, 不良馬場, 芝2500m）",
        "expected_result_count": 12,
        "has_lap_time": True,
        "is_obstacle": False,
    },
    {
        "race_id": "202406050710",
        "description": "中山大障害2024（障害, 4100m）",
        "expected_result_count": 9,
        "has_lap_time": False,
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
    """get_race_infoがRACE_INFO_COLUMNSと一致する1行DataFrameを返すこと"""
    if not os.environ.get("RUN_NETWORK_TESTS"):
        pytest.skip("RUN_NETWORK_TESTS environment variable is not set")

    race_id = str(test_case["race_id"])
    scraper = ResultPageScraper(race_id)
    df = scraper.get_race_info()

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert list(df.columns) == RACE_INFO_COLUMNS
    assert df["レースID"].iloc[0] == race_id

    time.sleep(REQUEST_INTERVAL)


# ---------------------------------------------------------------------------
# 正常系: get_result
# ---------------------------------------------------------------------------
@pytest.mark.network
@pytest.mark.parametrize("test_case", LIVE_TEST_CASES, ids=LIVE_TEST_CASE_IDS)
def test_get_result_returns_valid_dataframe(test_case: dict[str, object]) -> None:
    """get_resultがRESULT_COLUMNSと一致するDataFrameを返すこと"""
    if not os.environ.get("RUN_NETWORK_TESTS"):
        pytest.skip("RUN_NETWORK_TESTS environment variable is not set")

    race_id = str(test_case["race_id"])
    expected_count = test_case["expected_result_count"]
    assert isinstance(expected_count, int)

    scraper = ResultPageScraper(race_id)
    df = scraper.get_result()

    assert isinstance(df, pd.DataFrame)
    assert len(df) == expected_count
    assert list(df.columns) == RESULT_COLUMNS
    assert (df["レースID"] == race_id).all()
    assert df["馬ID"].notna().all()

    time.sleep(REQUEST_INTERVAL)


# ---------------------------------------------------------------------------
# 正常系: get_corner
# ---------------------------------------------------------------------------
@pytest.mark.network
@pytest.mark.parametrize("test_case", LIVE_TEST_CASES, ids=LIVE_TEST_CASE_IDS)
def test_get_corner_returns_valid_dataframe(test_case: dict[str, object]) -> None:
    """get_cornerがCORNER_COLUMNSと一致する1行DataFrameを返すこと"""
    if not os.environ.get("RUN_NETWORK_TESTS"):
        pytest.skip("RUN_NETWORK_TESTS environment variable is not set")

    race_id = str(test_case["race_id"])
    scraper = ResultPageScraper(race_id)
    df = scraper.get_corner()

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert list(df.columns) == CORNER_COLUMNS
    assert df["レースID"].iloc[0] == race_id
    assert pd.notna(df["4コーナー通過順"].iloc[0])

    time.sleep(REQUEST_INTERVAL)


# ---------------------------------------------------------------------------
# 正常系: get_win_payoff
# ---------------------------------------------------------------------------
@pytest.mark.network
@pytest.mark.parametrize("test_case", LIVE_TEST_CASES, ids=LIVE_TEST_CASE_IDS)
def test_get_win_payoff_returns_valid_dataframe(test_case: dict[str, object]) -> None:
    """get_win_payoffがWIN_PAYOFF_COLUMNSと一致する1行DataFrameを返すこと"""
    if not os.environ.get("RUN_NETWORK_TESTS"):
        pytest.skip("RUN_NETWORK_TESTS environment variable is not set")

    race_id = str(test_case["race_id"])
    scraper = ResultPageScraper(race_id)
    df = scraper.get_win_payoff()

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert list(df.columns) == WIN_PAYOFF_COLUMNS
    assert df["レースID"].iloc[0] == race_id
    assert pd.notna(df["単勝払戻金_1"].iloc[0])
    assert pd.notna(df["単勝馬番_1"].iloc[0])
    assert pd.notna(df["単勝人気_1"].iloc[0])

    time.sleep(REQUEST_INTERVAL)


# ---------------------------------------------------------------------------
# 正常系: get_show_payoff
# ---------------------------------------------------------------------------
@pytest.mark.network
@pytest.mark.parametrize("test_case", LIVE_TEST_CASES, ids=LIVE_TEST_CASE_IDS)
def test_get_show_payoff_returns_valid_dataframe(test_case: dict[str, object]) -> None:
    """get_show_payoffがSHOW_PAYOFF_COLUMNSと一致する1行DataFrameを返すこと"""
    if not os.environ.get("RUN_NETWORK_TESTS"):
        pytest.skip("RUN_NETWORK_TESTS environment variable is not set")

    race_id = str(test_case["race_id"])
    scraper = ResultPageScraper(race_id)
    df = scraper.get_show_payoff()

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert list(df.columns) == SHOW_PAYOFF_COLUMNS
    assert df["レースID"].iloc[0] == race_id
    assert pd.notna(df["複勝払戻金_1"].iloc[0])
    assert pd.notna(df["複勝馬番_1"].iloc[0])
    assert pd.notna(df["複勝人気_1"].iloc[0])

    time.sleep(REQUEST_INTERVAL)


# ---------------------------------------------------------------------------
# 正常系: get_bracket_payoff
# ---------------------------------------------------------------------------
@pytest.mark.network
@pytest.mark.parametrize("test_case", LIVE_TEST_CASES, ids=LIVE_TEST_CASE_IDS)
def test_get_bracket_payoff_returns_valid_dataframe(test_case: dict[str, object]) -> None:
    """get_bracket_payoffがBRACKET_PAYOFF_COLUMNSと一致する1行DataFrameを返すこと"""
    if not os.environ.get("RUN_NETWORK_TESTS"):
        pytest.skip("RUN_NETWORK_TESTS environment variable is not set")

    race_id = str(test_case["race_id"])
    scraper = ResultPageScraper(race_id)
    df = scraper.get_bracket_payoff()

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert list(df.columns) == BRACKET_PAYOFF_COLUMNS
    assert df["レースID"].iloc[0] == race_id

    time.sleep(REQUEST_INTERVAL)


# ---------------------------------------------------------------------------
# 正常系: get_quinella_payoff
# ---------------------------------------------------------------------------
@pytest.mark.network
@pytest.mark.parametrize("test_case", LIVE_TEST_CASES, ids=LIVE_TEST_CASE_IDS)
def test_get_quinella_payoff_returns_valid_dataframe(test_case: dict[str, object]) -> None:
    """get_quinella_payoffがQUINELLA_PAYOFF_COLUMNSと一致する1行DataFrameを返すこと"""
    if not os.environ.get("RUN_NETWORK_TESTS"):
        pytest.skip("RUN_NETWORK_TESTS environment variable is not set")

    race_id = str(test_case["race_id"])
    scraper = ResultPageScraper(race_id)
    df = scraper.get_quinella_payoff()

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert list(df.columns) == QUINELLA_PAYOFF_COLUMNS
    assert df["レースID"].iloc[0] == race_id
    assert pd.notna(df["馬連払戻金_1"].iloc[0])

    time.sleep(REQUEST_INTERVAL)


# ---------------------------------------------------------------------------
# 正常系: get_quinella_place_payoff
# ---------------------------------------------------------------------------
@pytest.mark.network
@pytest.mark.parametrize("test_case", LIVE_TEST_CASES, ids=LIVE_TEST_CASE_IDS)
def test_get_quinella_place_payoff_returns_valid_dataframe(
    test_case: dict[str, object],
) -> None:
    """get_quinella_place_payoffがQUINELLA_PLACE_PAYOFF_COLUMNSと一致する1行DataFrameを返すこと"""
    if not os.environ.get("RUN_NETWORK_TESTS"):
        pytest.skip("RUN_NETWORK_TESTS environment variable is not set")

    race_id = str(test_case["race_id"])
    scraper = ResultPageScraper(race_id)
    df = scraper.get_quinella_place_payoff()

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert list(df.columns) == QUINELLA_PLACE_PAYOFF_COLUMNS
    assert df["レースID"].iloc[0] == race_id
    assert pd.notna(df["ワイド払戻金_1"].iloc[0])

    time.sleep(REQUEST_INTERVAL)


# ---------------------------------------------------------------------------
# 正常系: get_exacta_payoff
# ---------------------------------------------------------------------------
@pytest.mark.network
@pytest.mark.parametrize("test_case", LIVE_TEST_CASES, ids=LIVE_TEST_CASE_IDS)
def test_get_exacta_payoff_returns_valid_dataframe(test_case: dict[str, object]) -> None:
    """get_exacta_payoffがEXACTA_PAYOFF_COLUMNSと一致する1行DataFrameを返すこと"""
    if not os.environ.get("RUN_NETWORK_TESTS"):
        pytest.skip("RUN_NETWORK_TESTS environment variable is not set")

    race_id = str(test_case["race_id"])
    scraper = ResultPageScraper(race_id)
    df = scraper.get_exacta_payoff()

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert list(df.columns) == EXACTA_PAYOFF_COLUMNS
    assert df["レースID"].iloc[0] == race_id
    assert pd.notna(df["馬単払戻金_1"].iloc[0])

    time.sleep(REQUEST_INTERVAL)


# ---------------------------------------------------------------------------
# 正常系: get_trio_payoff
# ---------------------------------------------------------------------------
@pytest.mark.network
@pytest.mark.parametrize("test_case", LIVE_TEST_CASES, ids=LIVE_TEST_CASE_IDS)
def test_get_trio_payoff_returns_valid_dataframe(test_case: dict[str, object]) -> None:
    """get_trio_payoffがTRIO_PAYOFF_COLUMNSと一致する1行DataFrameを返すこと"""
    if not os.environ.get("RUN_NETWORK_TESTS"):
        pytest.skip("RUN_NETWORK_TESTS environment variable is not set")

    race_id = str(test_case["race_id"])
    scraper = ResultPageScraper(race_id)
    df = scraper.get_trio_payoff()

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert list(df.columns) == TRIO_PAYOFF_COLUMNS
    assert df["レースID"].iloc[0] == race_id
    assert pd.notna(df["3連複払戻金_1"].iloc[0])

    time.sleep(REQUEST_INTERVAL)


# ---------------------------------------------------------------------------
# 正常系: get_trifecta_payoff
# ---------------------------------------------------------------------------
@pytest.mark.network
@pytest.mark.parametrize("test_case", LIVE_TEST_CASES, ids=LIVE_TEST_CASE_IDS)
def test_get_trifecta_payoff_returns_valid_dataframe(test_case: dict[str, object]) -> None:
    """get_trifecta_payoffがTRIFECTA_PAYOFF_COLUMNSと一致する1行DataFrameを返すこと"""
    if not os.environ.get("RUN_NETWORK_TESTS"):
        pytest.skip("RUN_NETWORK_TESTS environment variable is not set")

    race_id = str(test_case["race_id"])
    scraper = ResultPageScraper(race_id)
    df = scraper.get_trifecta_payoff()

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert list(df.columns) == TRIFECTA_PAYOFF_COLUMNS
    assert df["レースID"].iloc[0] == race_id
    assert pd.notna(df["3連単払戻金_1"].iloc[0])

    time.sleep(REQUEST_INTERVAL)


# ---------------------------------------------------------------------------
# 正常系: get_lap_time（平地レース）
# ---------------------------------------------------------------------------
FLAT_RACE_CASES = [tc for tc in LIVE_TEST_CASES if tc["has_lap_time"]]
FLAT_RACE_IDS = [str(tc["description"]) for tc in FLAT_RACE_CASES]


@pytest.mark.network
@pytest.mark.parametrize("test_case", FLAT_RACE_CASES, ids=FLAT_RACE_IDS)
def test_get_lap_time_flat_returns_valid_dataframe(test_case: dict[str, object]) -> None:
    """平地レースでget_lap_timeがLAP_TIME_COLUMNSと一致する1行DataFrameを返すこと"""
    if not os.environ.get("RUN_NETWORK_TESTS"):
        pytest.skip("RUN_NETWORK_TESTS environment variable is not set")

    race_id = str(test_case["race_id"])
    scraper = ResultPageScraper(race_id)
    df = scraper.get_lap_time()

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert list(df.columns) == LAP_TIME_COLUMNS
    assert df["レースID"].iloc[0] == race_id
    assert pd.notna(df["ペース"].iloc[0])
    assert df["ペース"].iloc[0] in {"S", "M", "H"}

    time.sleep(REQUEST_INTERVAL)


# ---------------------------------------------------------------------------
# 正常系: get_lap_time（障害レース）
# ---------------------------------------------------------------------------
OBSTACLE_RACE_CASES = [tc for tc in LIVE_TEST_CASES if tc.get("is_obstacle")]
OBSTACLE_RACE_IDS = [str(tc["description"]) for tc in OBSTACLE_RACE_CASES]


@pytest.mark.network
@pytest.mark.parametrize("test_case", OBSTACLE_RACE_CASES, ids=OBSTACLE_RACE_IDS)
def test_get_lap_time_obstacle_returns_nan_dataframe(test_case: dict[str, object]) -> None:
    """障害レースでget_lap_timeがレースID以外NaNの1行DataFrameを返すこと"""
    if not os.environ.get("RUN_NETWORK_TESTS"):
        pytest.skip("RUN_NETWORK_TESTS environment variable is not set")

    race_id = str(test_case["race_id"])
    scraper = ResultPageScraper(race_id)
    df = scraper.get_lap_time()

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert list(df.columns) == LAP_TIME_COLUMNS
    assert df["レースID"].iloc[0] == race_id
    assert pd.isna(df["ペース"].iloc[0])

    time.sleep(REQUEST_INTERVAL)
