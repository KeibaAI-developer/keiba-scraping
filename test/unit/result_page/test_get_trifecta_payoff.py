"""ResultPageScraper.get_trifecta_payoff()の単体テスト

requestsをモックし、フィクスチャHTMLを返すようにしてテストする。
3連単払い戻しの取得を検証する。
"""

import pandas as pd
import pytest

from scraping.config import TRIFECTA_PAYOFF_COLUMNS

from .conftest import collect_result_fixture_race_ids, create_scraper_from_fixture

RESULT_RACE_IDS = collect_result_fixture_race_ids()


# ---------------------------------------------------------------------------
# 正常系: 全フィクスチャ共通テスト
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("race_id", RESULT_RACE_IDS, ids=RESULT_RACE_IDS)
def test_columns_match(race_id: str) -> None:
    """カラム構成がTRIFECTA_PAYOFF_COLUMNSと一致すること"""
    scraper = create_scraper_from_fixture(race_id)
    df = scraper.get_trifecta_payoff()

    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == TRIFECTA_PAYOFF_COLUMNS


@pytest.mark.parametrize("race_id", RESULT_RACE_IDS, ids=RESULT_RACE_IDS)
def test_single_row(race_id: str) -> None:
    """結果が1行であること"""
    scraper = create_scraper_from_fixture(race_id)
    df = scraper.get_trifecta_payoff()

    assert len(df) == 1


@pytest.mark.parametrize("race_id", RESULT_RACE_IDS, ids=RESULT_RACE_IDS)
def test_race_id_matches(race_id: str) -> None:
    """レースIDが一致すること"""
    scraper = create_scraper_from_fixture(race_id)
    df = scraper.get_trifecta_payoff()

    assert df["レースID"].iloc[0] == race_id


@pytest.mark.parametrize("race_id", RESULT_RACE_IDS, ids=RESULT_RACE_IDS)
def test_first_slot_is_not_nan(race_id: str) -> None:
    """_1の値が常に存在すること"""
    scraper = create_scraper_from_fixture(race_id)
    df = scraper.get_trifecta_payoff()

    assert pd.notna(df["3連単払戻金_1"].iloc[0])
    assert pd.notna(df["3連単組番_1_1"].iloc[0])
    assert pd.notna(df["3連単組番_1_2"].iloc[0])
    assert pd.notna(df["3連単組番_1_3"].iloc[0])
    assert pd.notna(df["3連単人気_1"].iloc[0])


# ---------------------------------------------------------------------------
# 正常系: 具体値の検証
# ---------------------------------------------------------------------------
def test_derby_2025_values() -> None:
    """ダービー2025の3連単払い戻しが正しいこと"""
    scraper = create_scraper_from_fixture("202505021211")
    df = scraper.get_trifecta_payoff()

    assert df["3連単払戻金_1"].iloc[0] == 8460
    assert df["3連単組番_1_1"].iloc[0] == 13
    assert df["3連単組番_1_2"].iloc[0] == 17
    assert df["3連単組番_1_3"].iloc[0] == 2
    assert df["3連単人気_1"].iloc[0] == 13
    assert pd.isna(df["3連単払戻金_2"].iloc[0])


def test_oaks_2010_dead_heat_first_two_trifecta() -> None:
    """オークス2010（1着同着2頭）の3連単払い戻しが2通りであること"""
    scraper = create_scraper_from_fixture("201005030211")
    df = scraper.get_trifecta_payoff()

    # 17→18→2
    assert df["3連単払戻金_1"].iloc[0] == 20460
    assert df["3連単組番_1_1"].iloc[0] == 17
    assert df["3連単組番_1_2"].iloc[0] == 18
    assert df["3連単組番_1_3"].iloc[0] == 2
    assert df["3連単人気_1"].iloc[0] == 101
    # 18→17→2
    assert df["3連単払戻金_2"].iloc[0] == 24290
    assert df["3連単組番_2_1"].iloc[0] == 18
    assert df["3連単組番_2_2"].iloc[0] == 17
    assert df["3連単組番_2_3"].iloc[0] == 2
    assert df["3連単人気_2"].iloc[0] == 127
    # 3通り目は無し
    assert pd.isna(df["3連単払戻金_3"].iloc[0])


def test_three_way_dead_heat_third_three_trifecta() -> None:
    """3着同着3頭レースの3連単払い戻しが3通りであること"""
    scraper = create_scraper_from_fixture("202009050712")
    df = scraper.get_trifecta_payoff()

    # 8→18→1
    assert df["3連単払戻金_1"].iloc[0] == 8030
    assert df["3連単組番_1_1"].iloc[0] == 8
    assert df["3連単組番_1_2"].iloc[0] == 18
    assert df["3連単組番_1_3"].iloc[0] == 1
    assert df["3連単人気_1"].iloc[0] == 37
    # 8→18→4
    assert df["3連単払戻金_2"].iloc[0] == 8750
    assert df["3連単組番_2_1"].iloc[0] == 8
    assert df["3連単組番_2_2"].iloc[0] == 18
    assert df["3連単組番_2_3"].iloc[0] == 4
    assert df["3連単人気_2"].iloc[0] == 45
    # 8→18→11
    assert df["3連単払戻金_3"].iloc[0] == 5410
    assert df["3連単組番_3_1"].iloc[0] == 8
    assert df["3連単組番_3_2"].iloc[0] == 18
    assert df["3連単組番_3_3"].iloc[0] == 11
    assert df["3連単人気_3"].iloc[0] == 14
    # 4通り目は無し
    assert pd.isna(df["3連単払戻金_4"].iloc[0])
