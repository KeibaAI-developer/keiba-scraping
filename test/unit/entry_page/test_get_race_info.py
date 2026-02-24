"""EntryPageScraper.get_race_info()の単体テスト

requestsをモックし、フィクスチャHTMLを返すようにしてテストする。
レース情報の取得を検証する。
"""

import pandas as pd
import pytest

from scraping.config import RACE_INFO_COLUMNS

from .conftest import collect_entry_fixture_race_ids, create_scraper_from_fixture

ENTRY_RACE_IDS = collect_entry_fixture_race_ids()


# ---------------------------------------------------------------------------
# 正常系: 全フィクスチャ共通テスト
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("race_id", ENTRY_RACE_IDS, ids=ENTRY_RACE_IDS)
def test_columns_match_race_info_columns(race_id: str) -> None:
    """カラム構成がRACE_INFO_COLUMNSと一致すること"""
    scraper = create_scraper_from_fixture(race_id)
    race_info_df = scraper.get_race_info()

    assert isinstance(race_info_df, pd.DataFrame)
    assert list(race_info_df.columns) == RACE_INFO_COLUMNS


@pytest.mark.parametrize("race_id", ENTRY_RACE_IDS, ids=ENTRY_RACE_IDS)
def test_race_info_is_single_row(race_id: str) -> None:
    """レース情報が1行であること"""
    scraper = create_scraper_from_fixture(race_id)
    race_info_df = scraper.get_race_info()

    assert len(race_info_df) == 1


@pytest.mark.parametrize("race_id", ENTRY_RACE_IDS, ids=ENTRY_RACE_IDS)
def test_race_id_matches(race_id: str) -> None:
    """レースIDがコンストラクタで渡したrace_idと一致すること"""
    scraper = create_scraper_from_fixture(race_id)
    race_info_df = scraper.get_race_info()

    assert race_info_df["レースID"].iloc[0] == race_id


# ---------------------------------------------------------------------------
# 正常系: 具体値の検証
# ---------------------------------------------------------------------------
def test_derby_2025_race_info() -> None:
    """ダービー2025のレース情報が正しいこと"""
    scraper = create_scraper_from_fixture("202505021211")
    race_info_df = scraper.get_race_info()

    row = race_info_df.iloc[0]
    assert row["レース名"] == "日本ダービー"
    assert row["芝ダ"] == "芝"
    assert row["距離"] == 2400
    assert row["競馬場"] == "東京"
    assert row["グレード"] == "G1"
