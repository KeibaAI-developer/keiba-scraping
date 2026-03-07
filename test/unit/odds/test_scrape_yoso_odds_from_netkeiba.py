"""scrape_yoso_odds_from_netkeibaの単体テスト"""

from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from scraping.config import YOSO_ODDS_COLUMNS
from scraping.exceptions import NetworkError
from scraping.odds import scrape_yoso_odds_from_netkeiba


@pytest.fixture
def mock_horse_elements() -> list[MagicMock]:
    """馬情報要素のモックを返す"""
    elements = []
    test_data = [
        ("1", "アドマイヤクワッズ", "1.8"),
        ("2", "ライヒスアドラー", "3.9"),
        ("3", "バステール", "4.2"),
    ]
    for umaban, horse_name, odds in test_data:
        row = MagicMock()
        # tds
        tds = [MagicMock() for _ in range(11)]
        tds[1].text.strip.return_value = umaban
        tds[9].text.strip.return_value = odds
        row.find_elements.return_value = tds
        # HorseName
        horse_name_elem = MagicMock()
        horse_name_elem.text.strip.return_value = horse_name
        row.find_element.return_value = horse_name_elem
        elements.append(row)
    return elements


# 正常系
def test_scrape_yoso_odds_from_netkeiba_returns_correct_columns(
    mock_horse_elements: list[MagicMock],
) -> None:
    """戻り値がYOSO_ODDS_COLUMNSのカラムを持つDataFrameであること"""
    with patch("scraping.odds.webdriver.Chrome") as mock_chrome:
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        mock_driver.find_elements.return_value = mock_horse_elements

        result = scrape_yoso_odds_from_netkeiba("202606020411")

        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == YOSO_ODDS_COLUMNS


def test_scrape_yoso_odds_from_netkeiba_extracts_horse_name(
    mock_horse_elements: list[MagicMock],
) -> None:
    """馬名が正しく抽出されること"""
    with patch("scraping.odds.webdriver.Chrome") as mock_chrome:
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        mock_driver.find_elements.return_value = mock_horse_elements

        result = scrape_yoso_odds_from_netkeiba("202606020411")

        assert "アドマイヤクワッズ" in result["馬名"].values
        assert "ライヒスアドラー" in result["馬名"].values
        assert "バステール" in result["馬名"].values


def test_scrape_yoso_odds_from_netkeiba_extracts_umaban(
    mock_horse_elements: list[MagicMock],
) -> None:
    """馬番が正しく抽出されること"""
    with patch("scraping.odds.webdriver.Chrome") as mock_chrome:
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        mock_driver.find_elements.return_value = mock_horse_elements

        result = scrape_yoso_odds_from_netkeiba("202606020411")

        umaban_values = result["馬番"].tolist()
        assert 1 in umaban_values
        assert 2 in umaban_values
        assert 3 in umaban_values


def test_scrape_yoso_odds_from_netkeiba_extracts_yoso_odds(
    mock_horse_elements: list[MagicMock],
) -> None:
    """予想単勝オッズが正しく抽出されること"""
    with patch("scraping.odds.webdriver.Chrome") as mock_chrome:
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        mock_driver.find_elements.return_value = mock_horse_elements

        result = scrape_yoso_odds_from_netkeiba("202606020411")

        odds_values = result["予想単勝オッズ"].tolist()
        assert 1.8 in odds_values
        assert 3.9 in odds_values
        assert 4.2 in odds_values


def test_scrape_yoso_odds_from_netkeiba_row_count(
    mock_horse_elements: list[MagicMock],
) -> None:
    """取得した行数が馬の数と一致すること"""
    with patch("scraping.odds.webdriver.Chrome") as mock_chrome:
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        mock_driver.find_elements.return_value = mock_horse_elements

        result = scrape_yoso_odds_from_netkeiba("202606020411")

        assert len(result) == 3


# 準正常系
def test_scrape_yoso_odds_from_netkeiba_no_horses_returns_empty() -> None:
    """馬情報がない場合は空のDataFrameを返すこと"""
    with patch("scraping.odds.webdriver.Chrome") as mock_chrome:
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        mock_driver.find_elements.return_value = []

        result = scrape_yoso_odds_from_netkeiba("202606020411")

        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == YOSO_ODDS_COLUMNS
        assert len(result) == 0


def test_scrape_yoso_odds_from_netkeiba_invalid_odds_returns_nan() -> None:
    """オッズが無効な場合はNaNになること"""
    with patch("scraping.odds.webdriver.Chrome") as mock_chrome:
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver

        # 無効なオッズ
        row = MagicMock()
        tds = [MagicMock() for _ in range(11)]
        tds[1].text.strip.return_value = "1"  # 馬番
        tds[9].text.strip.return_value = "---"  # 無効なオッズ
        row.find_elements.return_value = tds
        horse_name_elem = MagicMock()
        horse_name_elem.text.strip.return_value = "テスト馬"
        row.find_element.return_value = horse_name_elem
        mock_driver.find_elements.return_value = [row]

        result = scrape_yoso_odds_from_netkeiba("202606020411")

        assert len(result) == 1
        assert np.isnan(result["予想単勝オッズ"].iloc[0])


def test_scrape_yoso_odds_from_netkeiba_empty_umaban_returns_nan() -> None:
    """馬番が空の場合はNaNになること(枠順未確定時)"""
    with patch("scraping.odds.webdriver.Chrome") as mock_chrome:
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver

        # 馬番が空
        row = MagicMock()
        tds = [MagicMock() for _ in range(11)]
        tds[1].text.strip.return_value = ""  # 馬番が空
        tds[9].text.strip.return_value = "2.5"
        row.find_elements.return_value = tds
        horse_name_elem = MagicMock()
        horse_name_elem.text.strip.return_value = "テスト馬"
        row.find_element.return_value = horse_name_elem
        mock_driver.find_elements.return_value = [row]

        result = scrape_yoso_odds_from_netkeiba("202606020411")

        assert len(result) == 1
        assert np.isnan(result["馬番"].iloc[0])
        assert result["予想単勝オッズ"].iloc[0] == 2.5


def test_scrape_yoso_odds_from_netkeiba_exception_raises_network_error() -> None:
    """ページ取得時の例外はNetworkErrorを送出すること"""
    with patch("scraping.odds.webdriver.Chrome") as mock_chrome:
        mock_chrome.side_effect = Exception("Driver error")

        with pytest.raises(NetworkError, match="予想オッズページの取得に失敗しました"):
            scrape_yoso_odds_from_netkeiba("202606020411")
