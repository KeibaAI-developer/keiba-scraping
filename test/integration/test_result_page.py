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

from scraping.config import PAYBACK_COLUMNS, RACE_INFO_COLUMNS, RESULT_COLUMNS
from scraping.result_page import ResultPageScraper

# テスト間のリクエスト間隔（秒）
REQUEST_INTERVAL = 1.5


# ---------------------------------------------------------------------------
# 正常系
# ---------------------------------------------------------------------------
LIVE_TEST_CASES = [
    {
        "race_id": "202505021211",
        "description": "日本ダービー2025（G1, 芝2400m）",
        "expected_result_count": 18,
        "has_corner": True,
        "has_lap_time": True,
    },
    {
        "race_id": "202306030111",
        "description": "日経賞2023（G2, 不良馬場, 芝2500m）",
        "expected_result_count": 14,
        "has_corner": True,
        "has_lap_time": True,
    },
    {
        "race_id": "202406050710",
        "description": "中山大障害2024（障害, 4100m）",
        "expected_result_count": 16,
        "has_corner": True,
        "has_lap_time": False,  # 障害レースはラップタイムなし
    },
]

LIVE_TEST_CASE_IDS = [str(tc["description"]) for tc in LIVE_TEST_CASES]


@pytest.mark.network
@pytest.mark.parametrize("test_case", LIVE_TEST_CASES, ids=LIVE_TEST_CASE_IDS)
def test_result_page_scraper_get_race_info_live(test_case: dict[str, object]) -> None:
    """実際にnetkeibaからスクレイピングしてget_race_infoが動作することを確認する"""
    if not os.environ.get("RUN_NETWORK_TESTS"):
        pytest.skip("RUN_NETWORK_TESTS environment variable is not set")

    race_id = str(test_case["race_id"])
    scraper = ResultPageScraper(race_id)
    race_info_df = scraper.get_race_info()

    assert isinstance(race_info_df, pd.DataFrame)
    assert len(race_info_df) == 1
    assert list(race_info_df.columns) == RACE_INFO_COLUMNS
    assert race_info_df["レースID"].iloc[0] == race_id

    time.sleep(REQUEST_INTERVAL)


@pytest.mark.network
@pytest.mark.parametrize("test_case", LIVE_TEST_CASES, ids=LIVE_TEST_CASE_IDS)
def test_result_page_scraper_get_result_live(test_case: dict[str, object]) -> None:
    """実際にnetkeibaからスクレイピングしてget_resultが動作することを確認する"""
    if not os.environ.get("RUN_NETWORK_TESTS"):
        pytest.skip("RUN_NETWORK_TESTS environment variable is not set")

    race_id = str(test_case["race_id"])
    expected_count = test_case["expected_result_count"]
    assert isinstance(expected_count, int)

    scraper = ResultPageScraper(race_id)
    result_df = scraper.get_result()

    assert isinstance(result_df, pd.DataFrame)
    assert not result_df.empty

    # RESULT_COLUMNSの全カラムが含まれること
    for col in RESULT_COLUMNS:
        assert col in result_df.columns

    # 馬IDが存在すること
    assert result_df["馬ID"].notna().any()

    time.sleep(REQUEST_INTERVAL)


@pytest.mark.network
@pytest.mark.parametrize("test_case", LIVE_TEST_CASES, ids=LIVE_TEST_CASE_IDS)
def test_result_page_scraper_get_corner_live(test_case: dict[str, object]) -> None:
    """実際にnetkeibaからスクレイピングしてget_cornerが動作することを確認する"""
    if not os.environ.get("RUN_NETWORK_TESTS"):
        pytest.skip("RUN_NETWORK_TESTS environment variable is not set")

    race_id = str(test_case["race_id"])
    has_corner = test_case["has_corner"]

    scraper = ResultPageScraper(race_id)
    corner_df = scraper.get_corner()

    assert isinstance(corner_df, pd.DataFrame)
    if has_corner:
        assert not corner_df.empty
        assert len(corner_df) == 4
        assert "コーナー" in corner_df.columns
        assert "通過順" in corner_df.columns

    time.sleep(REQUEST_INTERVAL)


@pytest.mark.network
@pytest.mark.parametrize("test_case", LIVE_TEST_CASES, ids=LIVE_TEST_CASE_IDS)
def test_result_page_scraper_get_payoff_live(test_case: dict[str, object]) -> None:
    """実際にnetkeibaからスクレイピングしてget_payoffが動作することを確認する"""
    if not os.environ.get("RUN_NETWORK_TESTS"):
        pytest.skip("RUN_NETWORK_TESTS environment variable is not set")

    race_id = str(test_case["race_id"])
    scraper = ResultPageScraper(race_id)
    payoff_df = scraper.get_payoff()

    assert isinstance(payoff_df, pd.DataFrame)
    assert not payoff_df.empty

    for col in PAYBACK_COLUMNS:
        assert col in payoff_df.columns

    # 単勝・複勝が含まれること
    bet_types = payoff_df["券種"].unique().tolist()
    assert "単勝" in bet_types
    assert "複勝" in bet_types

    # 払戻が正の整数であること
    assert (payoff_df["払戻"] > 0).all()

    time.sleep(REQUEST_INTERVAL)


@pytest.mark.network
@pytest.mark.parametrize("test_case", LIVE_TEST_CASES, ids=LIVE_TEST_CASE_IDS)
def test_result_page_scraper_get_lap_time_live(test_case: dict[str, object]) -> None:
    """実際にnetkeibaからスクレイピングしてget_lap_timeが動作することを確認する"""
    if not os.environ.get("RUN_NETWORK_TESTS"):
        pytest.skip("RUN_NETWORK_TESTS environment variable is not set")

    race_id = str(test_case["race_id"])
    has_lap_time = test_case["has_lap_time"]

    scraper = ResultPageScraper(race_id)
    lap_time_df = scraper.get_lap_time()

    assert isinstance(lap_time_df, pd.DataFrame)
    if has_lap_time:
        assert not lap_time_df.empty
        assert len(lap_time_df) == 2
        assert "ペース" in lap_time_df.columns
    else:
        assert lap_time_df.empty

    time.sleep(REQUEST_INTERVAL)
