"""scrape_odds_from_jraの単体テスト

CSVフィクスチャからpd.read_htmlをモックし、
JRA公式サイトからのオッズ取得を検証する。
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd
import pytest

from scraping.config import ODDS_COLUMNS
from scraping.exceptions import DriverError, PageNotFoundError, ParseError
from scraping.odds import scrape_odds_from_jra


@pytest.fixture
def fixtures_csv_dir() -> Path:
    """CSVフィクスチャディレクトリのパスを返す"""
    return Path(__file__).parent.parent.parent / "fixtures" / "csv"


@pytest.fixture
def jra_odds_raw_df(fixtures_csv_dir: Path) -> pd.DataFrame:
    """JRAオッズCSVフィクスチャをDataFrameとして返す"""
    csv_path = fixtures_csv_dir / "odds_jra_202606020411.csv"
    return pd.read_csv(csv_path)


@pytest.fixture
def mock_playwright() -> MagicMock:
    """Playwrightのasync_playwrightをモックする"""
    # Locatorのモック（get_by_roleの返り値）
    mock_locator = MagicMock()
    mock_locator.click = AsyncMock()
    mock_locator.count = AsyncMock(return_value=1)
    mock_locator.nth.return_value = mock_locator

    # expect_navigationのモック（async context manager）
    mock_nav_cm = AsyncMock()
    mock_nav_cm.__aenter__ = AsyncMock()
    mock_nav_cm.__aexit__ = AsyncMock(return_value=False)

    # Pageのモック
    mock_page = AsyncMock()
    mock_page.goto = AsyncMock()
    mock_page.content = AsyncMock(return_value="<html>mocked</html>")
    mock_page.get_by_role = MagicMock(return_value=mock_locator)
    mock_page.expect_navigation = MagicMock(return_value=mock_nav_cm)

    mock_context = AsyncMock()
    mock_context.new_page = AsyncMock(return_value=mock_page)

    mock_browser = AsyncMock()
    mock_browser.new_context = AsyncMock(return_value=mock_context)

    mock_chromium = AsyncMock()
    mock_chromium.launch = AsyncMock(return_value=mock_browser)

    mock_pw = MagicMock()
    mock_pw.chromium = mock_chromium

    mock_async_pw = MagicMock()
    mock_async_pw.__aenter__ = AsyncMock(return_value=mock_pw)
    mock_async_pw.__aexit__ = AsyncMock(return_value=False)

    return mock_async_pw


# 正常系
def test_scrape_odds_from_jra_returns_dataframe_with_correct_columns(
    mock_playwright: MagicMock, jra_odds_raw_df: pd.DataFrame
) -> None:
    """戻り値がODDS_COLUMNSのカラムを持つDataFrameであること"""
    with (
        patch("scraping.odds.async_playwright", return_value=mock_playwright),
        patch("scraping.odds.pd.read_html", return_value=[jra_odds_raw_df]),
    ):
        result = asyncio.run(scrape_odds_from_jra("202606020411"))

    assert isinstance(result, pd.DataFrame)
    assert list(result.columns) == ODDS_COLUMNS


def test_scrape_odds_from_jra_returns_correct_row_count(
    mock_playwright: MagicMock, jra_odds_raw_df: pd.DataFrame
) -> None:
    """正しい行数のデータを返すこと"""
    with (
        patch("scraping.odds.async_playwright", return_value=mock_playwright),
        patch("scraping.odds.pd.read_html", return_value=[jra_odds_raw_df]),
    ):
        result = asyncio.run(scrape_odds_from_jra("202606020411"))

    assert len(result) == 10


def test_scrape_odds_from_jra_extracts_odds_values(
    mock_playwright: MagicMock, jra_odds_raw_df: pd.DataFrame
) -> None:
    """単勝・複勝オッズおよび人気が正しく抽出されること

    馬番6（アドマイヤクワッズ）: 単勝2.1（1番人気）、複勝1.1-1.4（1番人気）
    """
    with (
        patch("scraping.odds.async_playwright", return_value=mock_playwright),
        patch("scraping.odds.pd.read_html", return_value=[jra_odds_raw_df]),
    ):
        result = asyncio.run(scrape_odds_from_jra("202606020411"))

    umaban_6 = result[result["馬番"] == 6].iloc[0]
    assert umaban_6["単勝オッズ"] == 2.1
    assert umaban_6["単勝人気"] == 1.0
    assert umaban_6["複勝最小オッズ"] == 1.1
    assert umaban_6["複勝最大オッズ"] == 1.4
    assert umaban_6["複勝人気"] == 1.0


def test_scrape_odds_from_jra_with_2着払い_column(
    mock_playwright: MagicMock, jra_odds_raw_df: pd.DataFrame
) -> None:
    """7頭立て以下で複勝（2着払い）カラムの場合も正しく処理できること"""
    # 「3着払い」を「2着払い」にリネームしたDataFrameを作成
    df_2着 = jra_odds_raw_df.rename(columns={"複勝（3着払い）": "複勝（2着払い）"})

    with (
        patch("scraping.odds.async_playwright", return_value=mock_playwright),
        patch("scraping.odds.pd.read_html", return_value=[df_2着]),
    ):
        result = asyncio.run(scrape_odds_from_jra("202606020411"))

    assert "複勝最小オッズ" in result.columns
    assert "複勝最大オッズ" in result.columns
    assert len(result) == 10


# 準正常系
def test_scrape_odds_from_jra_kaisai_not_found_raises_page_not_found_error(
    mock_playwright: MagicMock,
) -> None:
    """該当開催が見つからない場合にPageNotFoundErrorを送出すること"""
    # count()が0を返すLocatorを取得するようにモックを書き換え
    mock_pw = mock_playwright.__aenter__.return_value
    mock_browser = mock_pw.chromium.launch.return_value
    mock_context = mock_browser.new_context.return_value
    mock_page = mock_context.new_page.return_value

    mock_not_found_locator = MagicMock()
    mock_not_found_locator.count = AsyncMock(return_value=0)

    original_get_by_role = mock_page.get_by_role

    def get_by_role_side_effect(role: str, **kwargs: str) -> MagicMock:
        name = kwargs.get("name", "")
        if "回" in name and "日" in name:
            return mock_not_found_locator
        return original_get_by_role(role, **kwargs)

    mock_page.get_by_role = MagicMock(side_effect=get_by_role_side_effect)

    with patch("scraping.odds.async_playwright", return_value=mock_playwright):
        with pytest.raises(PageNotFoundError, match="該当開催"):
            asyncio.run(scrape_odds_from_jra("202606020411"))


def test_scrape_odds_from_jra_read_html_fails_raises_parse_error(
    mock_playwright: MagicMock,
) -> None:
    """pd.read_htmlが失敗した場合にParseErrorを送出すること"""
    with (
        patch("scraping.odds.async_playwright", return_value=mock_playwright),
        patch("scraping.odds.pd.read_html", side_effect=ValueError("no tables found")),
    ):
        with pytest.raises(ParseError, match="テーブルの読み取りに失敗しました"):
            asyncio.run(scrape_odds_from_jra("202606020411"))


# 異常系
def test_scrape_odds_from_jra_playwright_error_raises_driver_error() -> None:
    """Playwrightの操作失敗時にDriverErrorを送出すること"""
    mock_async_pw = MagicMock()
    mock_async_pw.__aenter__ = AsyncMock(side_effect=Exception("browser launch failed"))
    mock_async_pw.__aexit__ = AsyncMock(return_value=False)

    with patch("scraping.odds.async_playwright", return_value=mock_async_pw):
        with pytest.raises(DriverError, match="JRAオッズページの操作に失敗しました"):
            asyncio.run(scrape_odds_from_jra("202606020411"))
