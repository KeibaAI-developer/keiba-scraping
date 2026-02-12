"""ResultPageScraper.get_bracket_payoff()の単体テスト

requestsをモックし、フィクスチャHTMLを返すようにしてテストする。
枠連払い戻しの取得を検証する。
"""

import pandas as pd
import pytest

from scraping.config import BRACKET_PAYOFF_COLUMNS

from .conftest import collect_result_fixture_race_ids, create_scraper_from_fixture

RESULT_RACE_IDS = collect_result_fixture_race_ids()


# ---------------------------------------------------------------------------
# 正常系: 全フィクスチャ共通テスト
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("race_id", RESULT_RACE_IDS, ids=RESULT_RACE_IDS)
def test_columns_match(race_id: str) -> None:
    """カラム構成がBRACKET_PAYOFF_COLUMNSと一致すること"""
    scraper = create_scraper_from_fixture(race_id)
    df = scraper.get_bracket_payoff()

    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == BRACKET_PAYOFF_COLUMNS


@pytest.mark.parametrize("race_id", RESULT_RACE_IDS, ids=RESULT_RACE_IDS)
def test_single_row(race_id: str) -> None:
    """結果が1行であること"""
    scraper = create_scraper_from_fixture(race_id)
    df = scraper.get_bracket_payoff()

    assert len(df) == 1


@pytest.mark.parametrize("race_id", RESULT_RACE_IDS, ids=RESULT_RACE_IDS)
def test_race_id_matches(race_id: str) -> None:
    """レースIDが一致すること"""
    scraper = create_scraper_from_fixture(race_id)
    df = scraper.get_bracket_payoff()

    assert df["レースID"].iloc[0] == race_id


# ---------------------------------------------------------------------------
# 正常系: 具体値の検証
# ---------------------------------------------------------------------------
def test_derby_2025_values() -> None:
    """ダービー2025の枠連払い戻しが正しいこと"""
    scraper = create_scraper_from_fixture("202505021211")
    df = scraper.get_bracket_payoff()

    assert df["枠連払戻金_1"].iloc[0] == 420
    assert df["枠連組番_1_1"].iloc[0] == 7
    assert df["枠連組番_1_2"].iloc[0] == 8
    assert df["枠連人気_1"].iloc[0] == 1
    assert pd.isna(df["枠連払戻金_2"].iloc[0])


def test_five_runners_no_bracket() -> None:
    """5頭立てレースでは枠連不成立で全NaNであること"""
    scraper = create_scraper_from_fixture("202505020607")
    df = scraper.get_bracket_payoff()

    assert df["レースID"].iloc[0] == "202505020607"
    assert pd.isna(df["枠連払戻金_1"].iloc[0])
    assert pd.isna(df["枠連組番_1_1"].iloc[0])
    assert pd.isna(df["枠連組番_1_2"].iloc[0])
    assert pd.isna(df["枠連人気_1"].iloc[0])


def test_oaks_2010_dead_heat_first() -> None:
    """オークス2010（1着同着2頭）の枠連払い戻しが正しいこと"""
    scraper = create_scraper_from_fixture("201005030211")
    df = scraper.get_bracket_payoff()

    assert df["枠連払戻金_1"].iloc[0] == 1750
    assert df["枠連組番_1_1"].iloc[0] == 8
    assert df["枠連組番_1_2"].iloc[0] == 8
    assert df["枠連人気_1"].iloc[0] == 9
    assert pd.isna(df["枠連払戻金_2"].iloc[0])


def test_three_way_dead_heat_third() -> None:
    """3着同着3頭レースの枠連払い戻しが正しいこと"""
    scraper = create_scraper_from_fixture("202009050712")
    df = scraper.get_bracket_payoff()

    assert df["枠連払戻金_1"].iloc[0] == 1710
    assert df["枠連組番_1_1"].iloc[0] == 4
    assert df["枠連組番_1_2"].iloc[0] == 8
    assert df["枠連人気_1"].iloc[0] == 9
