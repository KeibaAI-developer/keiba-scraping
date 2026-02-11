"""ResultPageScraper.get_show_payoff()の単体テスト

requestsをモックし、フィクスチャHTMLを返すようにしてテストする。
複勝払い戻しの取得を検証する。
"""

import pandas as pd
import pytest

from scraping.config import SHOW_PAYOFF_COLUMNS

from .conftest import collect_result_fixture_race_ids, create_scraper_from_fixture

RESULT_RACE_IDS = collect_result_fixture_race_ids()


# ---------------------------------------------------------------------------
# 正常系: 全フィクスチャ共通テスト
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("race_id", RESULT_RACE_IDS, ids=RESULT_RACE_IDS)
def test_columns_match(race_id: str) -> None:
    """カラム構成がSHOW_PAYOFF_COLUMNSと一致すること"""
    scraper = create_scraper_from_fixture(race_id)
    df = scraper.get_show_payoff()

    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == SHOW_PAYOFF_COLUMNS


@pytest.mark.parametrize("race_id", RESULT_RACE_IDS, ids=RESULT_RACE_IDS)
def test_single_row(race_id: str) -> None:
    """結果が1行であること"""
    scraper = create_scraper_from_fixture(race_id)
    df = scraper.get_show_payoff()

    assert len(df) == 1


@pytest.mark.parametrize("race_id", RESULT_RACE_IDS, ids=RESULT_RACE_IDS)
def test_race_id_matches(race_id: str) -> None:
    """レースIDが一致すること"""
    scraper = create_scraper_from_fixture(race_id)
    df = scraper.get_show_payoff()

    assert df["レースID"].iloc[0] == race_id


@pytest.mark.parametrize("race_id", RESULT_RACE_IDS, ids=RESULT_RACE_IDS)
def test_first_slot_is_not_nan(race_id: str) -> None:
    """_1の値が常に存在すること"""
    scraper = create_scraper_from_fixture(race_id)
    df = scraper.get_show_payoff()

    assert pd.notna(df["複勝払戻金_1"].iloc[0])
    assert pd.notna(df["複勝馬番_1"].iloc[0])
    assert pd.notna(df["複勝人気_1"].iloc[0])


# ---------------------------------------------------------------------------
# 正常系: 具体値の検証
# ---------------------------------------------------------------------------
def test_derby_2025_values() -> None:
    """ダービー2025の複勝払い戻しが正しいこと（通常3頭）"""
    scraper = create_scraper_from_fixture("202505021211")
    df = scraper.get_show_payoff()

    assert df["複勝払戻金_1"].iloc[0] == 110
    assert df["複勝馬番_1"].iloc[0] == 13
    assert df["複勝人気_1"].iloc[0] == 1
    assert df["複勝払戻金_2"].iloc[0] == 190
    assert df["複勝馬番_2"].iloc[0] == 17
    assert df["複勝人気_2"].iloc[0] == 3
    assert df["複勝払戻金_3"].iloc[0] == 300
    assert df["複勝馬番_3"].iloc[0] == 2
    assert df["複勝人気_3"].iloc[0] == 6
    assert pd.isna(df["複勝払戻金_4"].iloc[0])
    assert pd.isna(df["複勝払戻金_5"].iloc[0])


def test_five_runners_two_show() -> None:
    """5頭立ての場合は複勝が2頭のみであること"""
    scraper = create_scraper_from_fixture("202505020607")
    df = scraper.get_show_payoff()

    assert df["複勝払戻金_1"].iloc[0] == 110
    assert df["複勝馬番_1"].iloc[0] == 1
    assert df["複勝人気_1"].iloc[0] == 1
    assert df["複勝払戻金_2"].iloc[0] == 260
    assert df["複勝馬番_2"].iloc[0] == 5
    assert df["複勝人気_2"].iloc[0] == 4
    assert pd.isna(df["複勝払戻金_3"].iloc[0])


def test_three_way_dead_heat_third_five_show() -> None:
    """3着同着3頭レースの複勝払い戻しが5頭分であること"""
    scraper = create_scraper_from_fixture("202009050712")
    df = scraper.get_show_payoff()

    assert df["複勝払戻金_1"].iloc[0] == 110
    assert df["複勝馬番_1"].iloc[0] == 8
    assert df["複勝人気_1"].iloc[0] == 1
    assert df["複勝払戻金_2"].iloc[0] == 150
    assert df["複勝馬番_2"].iloc[0] == 18
    assert df["複勝人気_2"].iloc[0] == 6
    assert df["複勝払戻金_3"].iloc[0] == 140
    assert df["複勝馬番_3"].iloc[0] == 1
    assert df["複勝人気_3"].iloc[0] == 4
    assert df["複勝払戻金_4"].iloc[0] == 130
    assert df["複勝馬番_4"].iloc[0] == 4
    assert df["複勝人気_4"].iloc[0] == 3
    assert df["複勝払戻金_5"].iloc[0] == 110
    assert df["複勝馬番_5"].iloc[0] == 11
    assert df["複勝人気_5"].iloc[0] == 2


def test_oaks_2010_dead_heat_first() -> None:
    """オークス2010（1着同着2頭）の複勝払い戻しが正しいこと"""
    scraper = create_scraper_from_fixture("201005030211")
    df = scraper.get_show_payoff()

    assert df["複勝払戻金_1"].iloc[0] == 180
    assert df["複勝馬番_1"].iloc[0] == 17
    assert df["複勝人気_1"].iloc[0] == 1
    assert df["複勝払戻金_2"].iloc[0] == 270
    assert df["複勝馬番_2"].iloc[0] == 18
    assert df["複勝人気_2"].iloc[0] == 4
    assert df["複勝払戻金_3"].iloc[0] == 450
    assert df["複勝馬番_3"].iloc[0] == 2
    assert df["複勝人気_3"].iloc[0] == 8
    assert pd.isna(df["複勝払戻金_4"].iloc[0])
