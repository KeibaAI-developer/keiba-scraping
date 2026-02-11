"""ResultPageScraper.get_quinella_place_payoff()の単体テスト

requestsをモックし、フィクスチャHTMLを返すようにしてテストする。
ワイド払い戻しの取得を検証する。
"""

import pandas as pd
import pytest

from scraping.config import QUINELLA_PLACE_PAYOFF_COLUMNS

from .conftest import collect_result_fixture_race_ids, create_scraper_from_fixture

RESULT_RACE_IDS = collect_result_fixture_race_ids()


# ---------------------------------------------------------------------------
# 正常系: 全フィクスチャ共通テスト
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("race_id", RESULT_RACE_IDS, ids=RESULT_RACE_IDS)
def test_columns_match(race_id: str) -> None:
    """カラム構成がQUINELLA_PLACE_PAYOFF_COLUMNSと一致すること"""
    scraper = create_scraper_from_fixture(race_id)
    df = scraper.get_quinella_place_payoff()

    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == QUINELLA_PLACE_PAYOFF_COLUMNS


@pytest.mark.parametrize("race_id", RESULT_RACE_IDS, ids=RESULT_RACE_IDS)
def test_single_row(race_id: str) -> None:
    """結果が1行であること"""
    scraper = create_scraper_from_fixture(race_id)
    df = scraper.get_quinella_place_payoff()

    assert len(df) == 1


@pytest.mark.parametrize("race_id", RESULT_RACE_IDS, ids=RESULT_RACE_IDS)
def test_race_id_matches(race_id: str) -> None:
    """レースIDが一致すること"""
    scraper = create_scraper_from_fixture(race_id)
    df = scraper.get_quinella_place_payoff()

    assert df["レースID"].iloc[0] == race_id


@pytest.mark.parametrize("race_id", RESULT_RACE_IDS, ids=RESULT_RACE_IDS)
def test_first_three_slots_are_not_nan(race_id: str) -> None:
    """ワイドは通常3組的中するため_1〜_3の値が存在すること"""
    scraper = create_scraper_from_fixture(race_id)
    df = scraper.get_quinella_place_payoff()

    assert pd.notna(df["ワイド払戻金_1"].iloc[0])
    assert pd.notna(df["ワイド払戻金_2"].iloc[0])
    assert pd.notna(df["ワイド払戻金_3"].iloc[0])


# ---------------------------------------------------------------------------
# 正常系: 具体値の検証
# ---------------------------------------------------------------------------
def test_derby_2025_values() -> None:
    """ダービー2025のワイド払い戻しが正しいこと"""
    scraper = create_scraper_from_fixture("202505021211")
    df = scraper.get_quinella_place_payoff()

    assert df["ワイド払戻金_1"].iloc[0] == 280
    assert df["ワイド組番_1_1"].iloc[0] == 13
    assert df["ワイド組番_1_2"].iloc[0] == 17
    assert df["ワイド人気_1"].iloc[0] == 1
    assert df["ワイド払戻金_2"].iloc[0] == 620
    assert df["ワイド組番_2_1"].iloc[0] == 2
    assert df["ワイド組番_2_2"].iloc[0] == 13
    assert df["ワイド人気_2"].iloc[0] == 7
    assert df["ワイド払戻金_3"].iloc[0] == 1310
    assert df["ワイド組番_3_1"].iloc[0] == 2
    assert df["ワイド組番_3_2"].iloc[0] == 17
    assert df["ワイド人気_3"].iloc[0] == 14
    assert pd.isna(df["ワイド払戻金_4"].iloc[0])


def test_oaks_2010_dead_heat_first() -> None:
    """オークス2010（1着同着2頭）のワイド払い戻しが正しいこと"""
    scraper = create_scraper_from_fixture("201005030211")
    df = scraper.get_quinella_place_payoff()

    assert df["ワイド払戻金_1"].iloc[0] == 900
    assert df["ワイド組番_1_1"].iloc[0] == 17
    assert df["ワイド組番_1_2"].iloc[0] == 18
    assert df["ワイド人気_1"].iloc[0] == 5
    assert df["ワイド払戻金_2"].iloc[0] == 2020
    assert df["ワイド組番_2_1"].iloc[0] == 2
    assert df["ワイド組番_2_2"].iloc[0] == 17
    assert df["ワイド人気_2"].iloc[0] == 24
    assert df["ワイド払戻金_3"].iloc[0] == 2020
    assert df["ワイド組番_3_1"].iloc[0] == 2
    assert df["ワイド組番_3_2"].iloc[0] == 18
    assert df["ワイド人気_3"].iloc[0] == 25
    assert pd.isna(df["ワイド払戻金_4"].iloc[0])


def test_three_way_dead_heat_third_seven_wide() -> None:
    """3着同着3頭レースのワイド払い戻しが7組であること"""
    scraper = create_scraper_from_fixture("202009050712")
    df = scraper.get_quinella_place_payoff()

    assert df["ワイド払戻金_1"].iloc[0] == 360
    assert df["ワイド組番_1_1"].iloc[0] == 8
    assert df["ワイド組番_1_2"].iloc[0] == 18
    assert df["ワイド人気_1"].iloc[0] == 8
    assert df["ワイド払戻金_2"].iloc[0] == 320
    assert df["ワイド組番_2_1"].iloc[0] == 1
    assert df["ワイド組番_2_2"].iloc[0] == 8
    assert df["ワイド人気_2"].iloc[0] == 5
    assert df["ワイド払戻金_3"].iloc[0] == 260
    assert df["ワイド組番_3_1"].iloc[0] == 4
    assert df["ワイド組番_3_2"].iloc[0] == 8
    assert df["ワイド人気_3"].iloc[0] == 2
    assert df["ワイド払戻金_4"].iloc[0] == 190
    assert df["ワイド組番_4_1"].iloc[0] == 8
    assert df["ワイド組番_4_2"].iloc[0] == 11
    assert df["ワイド人気_4"].iloc[0] == 1
    assert df["ワイド払戻金_5"].iloc[0] == 530
    assert df["ワイド組番_5_1"].iloc[0] == 1
    assert df["ワイド組番_5_2"].iloc[0] == 18
    assert df["ワイド人気_5"].iloc[0] == 15
    assert df["ワイド払戻金_6"].iloc[0] == 580
    assert df["ワイド組番_6_1"].iloc[0] == 4
    assert df["ワイド組番_6_2"].iloc[0] == 18
    assert df["ワイド人気_6"].iloc[0] == 19
    assert df["ワイド払戻金_7"].iloc[0] == 370
    assert df["ワイド組番_7_1"].iloc[0] == 11
    assert df["ワイド組番_7_2"].iloc[0] == 18
    assert df["ワイド人気_7"].iloc[0] == 9


def test_five_runners_three_wide() -> None:
    """5頭立てレースのワイド払い戻しが3組であること"""
    scraper = create_scraper_from_fixture("202505020607")
    df = scraper.get_quinella_place_payoff()

    assert df["ワイド払戻金_1"].iloc[0] == 220
    assert df["ワイド組番_1_1"].iloc[0] == 1
    assert df["ワイド組番_1_2"].iloc[0] == 5
    assert df["ワイド人気_1"].iloc[0] == 4
    assert df["ワイド払戻金_2"].iloc[0] == 180
    assert df["ワイド組番_2_1"].iloc[0] == 1
    assert df["ワイド組番_2_2"].iloc[0] == 4
    assert df["ワイド人気_2"].iloc[0] == 2
    assert df["ワイド払戻金_3"].iloc[0] == 320
    assert df["ワイド組番_3_1"].iloc[0] == 4
    assert df["ワイド組番_3_2"].iloc[0] == 5
    assert df["ワイド人気_3"].iloc[0] == 6
    assert pd.isna(df["ワイド払戻金_4"].iloc[0])
