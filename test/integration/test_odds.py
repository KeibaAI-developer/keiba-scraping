"""scrape_odds_from_netkeibaおよびscrape_odds_from_jraの結合テスト

フィクスチャは使用せず、実際にnetkeiba/JRAにアクセスしてスクレイピングを行い、
オッズ取得関数が正しく動作することを確認する。
netkeibaおよびJRAのHTML構造の仕様変更に気づきやすくすることが目的。

ネットワーク接続が必要なため、@pytest.mark.networkマーカーを付与する。
環境変数 RUN_NETWORK_TESTS=1 が設定されている場合のみ実行される（opt-in）。
"""

import asyncio
import os
import time
from typing import Any

import pandas as pd
import pytest

from scraping.config import ODDS_COLUMNS
from scraping.exceptions import DriverError
from scraping.odds import scrape_odds_from_jra, scrape_odds_from_netkeiba

# テスト間のリクエスト間隔（秒）
REQUEST_INTERVAL = 1.0


def pytest_configure(config: pytest.Config) -> None:
    """pytestの設定"""
    config.addinivalue_line("markers", "network: marks tests as requiring network access")


# 正常系
LIVE_TEST_CASES: list[dict[str, Any]] = [
    {
        "race_id": "202306050911",
        "description": "ホープフルステークス2023（G1, 出走取消あり）",
        "tousuu": 18,  # 出走取消2頭含む
        "expected_umaban_2_tansho_odds": 14.3,
        "cancel_umaban": [1, 17],  # 出走取消の馬番
    },
    {
        "race_id": "202505021211",
        "description": "日本ダービー2025（G1）",
        "tousuu": 18,
        "expected_umaban_2_tansho_odds": None,  # 期待値なし（変動するため）
        "cancel_umaban": [],
    },
]


@pytest.fixture(scope="module", autouse=True)
def slow_down_tests() -> None:
    """テスト間にインターバルを設ける"""
    time.sleep(REQUEST_INTERVAL)


pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_NETWORK_TESTS") != "1",
    reason="RUN_NETWORK_TESTS=1 が設定されていません（ネットワークテストはopt-in）",
)


@pytest.mark.network
@pytest.mark.parametrize(
    "test_case",
    LIVE_TEST_CASES,
    ids=[tc["description"] for tc in LIVE_TEST_CASES],
)
def test_scrape_odds_from_netkeiba_returns_correct_columns(test_case: dict[str, Any]) -> None:
    """ODDS_COLUMNSのカラムを持つDataFrameを返すこと"""
    race_id = test_case["race_id"]

    result = scrape_odds_from_netkeiba(race_id)

    assert isinstance(result, pd.DataFrame)
    assert list(result.columns) == ODDS_COLUMNS


@pytest.mark.network
@pytest.mark.parametrize(
    "test_case",
    LIVE_TEST_CASES,
    ids=[tc["description"] for tc in LIVE_TEST_CASES],
)
def test_scrape_odds_from_netkeiba_returns_correct_tousuu(test_case: dict[str, Any]) -> None:
    """正しい頭数のデータを返すこと"""
    race_id = test_case["race_id"]
    expected_tousuu = test_case["tousuu"]

    result = scrape_odds_from_netkeiba(race_id)

    assert len(result) == expected_tousuu


@pytest.mark.network
def test_scrape_odds_from_netkeiba_cancel_horse_has_nan_odds() -> None:
    """出走取消馬のオッズがNaNであること"""
    # ホープフルステークス2023（馬番1と17が出走取消）
    race_id = "202306050911"
    cancel_umaban = [1, 17]

    result = scrape_odds_from_netkeiba(race_id)

    for umaban in cancel_umaban:
        row = result[result["馬番"] == umaban].iloc[0]
        assert pd.isna(row["単勝オッズ"]), f"馬番{umaban}の単勝オッズがNaNではありません"
        assert pd.isna(row["単勝人気"]), f"馬番{umaban}の単勝人気がNaNではありません"


# ---------------------------------------------------------------------------
# scrape_odds_from_jra
# ---------------------------------------------------------------------------
# JRAのオッズページは今週開催中のレースしか掲載されないため、
# 毎週 race_id を当週の開催レースに手動で書き換える必要がある。
# 古い race_id のままテストを実行すると DriverError が発生し、スキップされる。
JRA_LIVE_TEST_CASES: list[dict[str, Any]] = [
    {
        "race_id": "202606020411",
        "description": "2回中山4日11R",
        "min_tousuu": 5,
    },
]


@pytest.mark.network
@pytest.mark.parametrize(
    "test_case",
    JRA_LIVE_TEST_CASES,
    ids=[tc["description"] for tc in JRA_LIVE_TEST_CASES],
)
def test_scrape_odds_from_jra_returns_correct_columns(test_case: dict[str, Any]) -> None:
    """ODDS_COLUMNSのカラムを持つDataFrameを返すこと"""
    race_id = test_case["race_id"]

    try:
        result = asyncio.run(scrape_odds_from_jra(race_id))
    except DriverError:
        pytest.skip(
            f"JRAにレース {race_id} が見つかりません。race_idを当週の開催レースに更新してください。"
        )

    assert isinstance(result, pd.DataFrame)
    assert list(result.columns) == ODDS_COLUMNS


@pytest.mark.network
@pytest.mark.parametrize(
    "test_case",
    JRA_LIVE_TEST_CASES,
    ids=[tc["description"] for tc in JRA_LIVE_TEST_CASES],
)
def test_scrape_odds_from_jra_returns_rows(test_case: dict[str, Any]) -> None:
    """データが存在すること"""
    race_id = test_case["race_id"]
    min_tousuu = test_case["min_tousuu"]

    try:
        result = asyncio.run(scrape_odds_from_jra(race_id))
    except DriverError:
        pytest.skip(
            f"JRAにレース {race_id} が見つかりません。race_idを当週の開催レースに更新してください。"
        )

    assert len(result) >= min_tousuu


@pytest.mark.network
@pytest.mark.parametrize(
    "test_case",
    JRA_LIVE_TEST_CASES,
    ids=[tc["description"] for tc in JRA_LIVE_TEST_CASES],
)
def test_scrape_odds_from_jra_tansho_odds_are_positive(test_case: dict[str, Any]) -> None:
    """単勝オッズが正の値であること"""
    race_id = test_case["race_id"]

    try:
        result = asyncio.run(scrape_odds_from_jra(race_id))
    except DriverError:
        pytest.skip(
            f"JRAにレース {race_id} が見つかりません。race_idを当週の開催レースに更新してください。"
        )

    valid_odds = result["単勝オッズ"].dropna()
    assert (valid_odds > 0).all()
