"""RaceListScraper.get_race_list()の単体テスト

全ページ取得のモックテスト。sleepが正しく呼ばれることの検証。
"""

from unittest.mock import MagicMock, patch

import pandas as pd

from scraping.config import RACE_LIST_COLUMNS

from .conftest import create_scraper_with_mock

# ---------------------------------------------------------------------------
# テスト用定数
# ---------------------------------------------------------------------------
FIXTURE_P1 = "race_list_2026_p1.html"
YEAR = 2026


# ---------------------------------------------------------------------------
# 正常系: 全ページ取得（1ページのみ）
# ---------------------------------------------------------------------------
def test_get_race_list_single_page() -> None:
    """1ページのみの場合、scrape_one_pageが1回呼ばれること"""
    scraper = create_scraper_with_mock(YEAR, 1, [FIXTURE_P1])

    with patch.object(scraper, "scrape_one_page", wraps=scraper.scrape_one_page) as mock_method:
        df = scraper.get_race_list(sleep=0.0)

    mock_method.assert_called_once_with(1)
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == RACE_LIST_COLUMNS
    assert len(df) == 100


# ---------------------------------------------------------------------------
# 正常系: 全ページ取得（複数ページ、モック）
# ---------------------------------------------------------------------------
def test_get_race_list_multiple_pages() -> None:
    """2ページの場合、scrape_one_pageが2回呼ばれること"""
    # 2ページ分のフィクスチャ（同じHTMLを再利用）
    scraper = create_scraper_with_mock(YEAR, 2, [FIXTURE_P1, FIXTURE_P1])

    with patch.object(scraper, "scrape_one_page", wraps=scraper.scrape_one_page) as mock_method:
        df = scraper.get_race_list(sleep=0.0)

    assert mock_method.call_count == 2
    mock_method.assert_any_call(1)
    mock_method.assert_any_call(2)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 200  # 100行 x 2ページ


# ---------------------------------------------------------------------------
# 正常系: sleepが正しく呼ばれること
# ---------------------------------------------------------------------------
@patch("scraping.race_list.time.sleep")
def test_get_race_list_sleep_called(mock_sleep: MagicMock) -> None:
    """2ページの場合、sleepが1回呼ばれること（ページ間のみ）"""
    scraper = create_scraper_with_mock(YEAR, 2, [FIXTURE_P1, FIXTURE_P1])

    scraper.get_race_list(sleep=1.5)

    mock_sleep.assert_called_once_with(1.5)


@patch("scraping.race_list.time.sleep")
def test_get_race_list_sleep_not_called_for_single_page(mock_sleep: MagicMock) -> None:
    """1ページの場合、sleepは呼ばれないこと"""
    scraper = create_scraper_with_mock(YEAR, 1, [FIXTURE_P1])

    scraper.get_race_list(sleep=1.0)

    mock_sleep.assert_not_called()


@patch("scraping.race_list.time.sleep")
def test_get_race_list_sleep_count_for_three_pages(mock_sleep: MagicMock) -> None:
    """3ページの場合、sleepが2回呼ばれること"""
    scraper = create_scraper_with_mock(YEAR, 3, [FIXTURE_P1, FIXTURE_P1, FIXTURE_P1])

    scraper.get_race_list(sleep=0.5)

    assert mock_sleep.call_count == 2


# ---------------------------------------------------------------------------
# 正常系: カラム構成の一致
# ---------------------------------------------------------------------------
def test_get_race_list_columns() -> None:
    """get_race_listの結果がRACE_LIST_COLUMNSと一致すること"""
    scraper = create_scraper_with_mock(YEAR, 1, [FIXTURE_P1])
    df = scraper.get_race_list(sleep=0.0)

    assert list(df.columns) == RACE_LIST_COLUMNS


# ---------------------------------------------------------------------------
# 正常系: インデックスのリセット
# ---------------------------------------------------------------------------
def test_get_race_list_index_reset() -> None:
    """複数ページ結合後のインデックスが0始まりの連番であること"""
    scraper = create_scraper_with_mock(YEAR, 2, [FIXTURE_P1, FIXTURE_P1])
    df = scraper.get_race_list(sleep=0.0)

    assert list(df.index) == list(range(len(df)))
