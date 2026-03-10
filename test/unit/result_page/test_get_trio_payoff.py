"""ResultPageScraper.get_trio_payoff()の単体テスト

requestsをモックし、フィクスチャHTMLを返すようにしてテストする。
3連複払い戻しの取得を検証する。
"""

import pandas as pd
import pytest

from scraping.config import TRIO_PAYOFF_COLUMNS

from .conftest import collect_result_fixture_race_ids, create_scraper_from_fixture

RESULT_RACE_IDS = collect_result_fixture_race_ids()


# ---------------------------------------------------------------------------
# 正常系: 全フィクスチャ共通テスト
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("race_id", RESULT_RACE_IDS, ids=RESULT_RACE_IDS)
def test_columns_match(race_id: str) -> None:
    """カラム構成がTRIO_PAYOFF_COLUMNSと一致すること"""
    scraper = create_scraper_from_fixture(race_id)
    df = scraper.get_trio_payoff()

    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == TRIO_PAYOFF_COLUMNS


@pytest.mark.parametrize("race_id", RESULT_RACE_IDS, ids=RESULT_RACE_IDS)
def test_single_row(race_id: str) -> None:
    """結果が1行であること"""
    scraper = create_scraper_from_fixture(race_id)
    df = scraper.get_trio_payoff()

    assert len(df) == 1


@pytest.mark.parametrize("race_id", RESULT_RACE_IDS, ids=RESULT_RACE_IDS)
def test_race_id_matches(race_id: str) -> None:
    """レースIDが一致すること"""
    scraper = create_scraper_from_fixture(race_id)
    df = scraper.get_trio_payoff()

    assert df["レースID"].iloc[0] == race_id


@pytest.mark.parametrize("race_id", RESULT_RACE_IDS, ids=RESULT_RACE_IDS)
def test_first_slot_is_not_nan(race_id: str) -> None:
    """_1の値が常に存在すること"""
    scraper = create_scraper_from_fixture(race_id)
    df = scraper.get_trio_payoff()

    assert pd.notna(df["3連複払戻金_1"].iloc[0])
    assert pd.notna(df["3連複組番_1_1"].iloc[0])
    assert pd.notna(df["3連複組番_1_2"].iloc[0])
    assert pd.notna(df["3連複組番_1_3"].iloc[0])
    assert pd.notna(df["3連複人気_1"].iloc[0])


# ---------------------------------------------------------------------------
# 正常系: 具体値の検証
# ---------------------------------------------------------------------------
def test_derby_2025_values() -> None:
    """ダービー2025の3連複払い戻しが正しいこと"""
    scraper = create_scraper_from_fixture("202505021211")
    df = scraper.get_trio_payoff()

    assert df["3連複払戻金_1"].iloc[0] == 2990
    assert df["3連複組番_1_1"].iloc[0] == 2
    assert df["3連複組番_1_2"].iloc[0] == 13
    assert df["3連複組番_1_3"].iloc[0] == 17
    assert df["3連複人気_1"].iloc[0] == 10
    assert pd.isna(df["3連複払戻金_2"].iloc[0])


def test_oaks_2010_dead_heat_first() -> None:
    """オークス2010（1着同着2頭）の3連複払い戻しが正しいこと"""
    scraper = create_scraper_from_fixture("201005030211")
    df = scraper.get_trio_payoff()

    assert df["3連複払戻金_1"].iloc[0] == 10180
    assert df["3連複組番_1_1"].iloc[0] == 2
    assert df["3連複組番_1_2"].iloc[0] == 17
    assert df["3連複組番_1_3"].iloc[0] == 18
    assert df["3連複人気_1"].iloc[0] == 28
    assert pd.isna(df["3連複払戻金_2"].iloc[0])


def test_three_way_dead_heat_third_three_trio() -> None:
    """3着同着3頭レースの3連複払い戻しが3通りであること"""
    scraper = create_scraper_from_fixture("202009050712")
    df = scraper.get_trio_payoff()

    # 1組目
    assert df["3連複払戻金_1"].iloc[0] == 1960
    assert df["3連複組番_1_1"].iloc[0] == 1
    assert df["3連複組番_1_2"].iloc[0] == 8
    assert df["3連複組番_1_3"].iloc[0] == 18
    assert df["3連複人気_1"].iloc[0] == 12
    # 2組目
    assert df["3連複払戻金_2"].iloc[0] == 2020
    assert df["3連複組番_2_1"].iloc[0] == 4
    assert df["3連複組番_2_2"].iloc[0] == 8
    assert df["3連複組番_2_3"].iloc[0] == 18
    assert df["3連複人気_2"].iloc[0] == 13
    # 3組目
    assert df["3連複払戻金_3"].iloc[0] == 1140
    assert df["3連複組番_3_1"].iloc[0] == 8
    assert df["3連複組番_3_2"].iloc[0] == 11
    assert df["3連複組番_3_3"].iloc[0] == 18
    assert df["3連複人気_3"].iloc[0] == 4
