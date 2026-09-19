"""scrape_yoso_odds_from_netkeibaの単体テスト"""

from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from selenium.webdriver.common.by import By

from scraping.config import YOSO_ODDS_COLUMNS
from scraping.exceptions import ExpectedOddsUnavailableError, NetworkError, ParseError
from scraping.odds import scrape_yoso_odds_from_netkeiba

# 予想オッズが掲載されているときの出馬表の見出し（10列目がオッズ列）
_YOSO_HEADERS = [
    "枠",
    "馬番",
    "印",
    "馬名",
    "性齢",
    "斤量",
    "騎手",
    "厩舎",
    "馬体重(増減)",
    "予想オッズ",
    "人気",
]
# 馬券発売開始後の見出し（同じ列が実オッズの表示に変わる）
_SOLD_HEADERS = [*_YOSO_HEADERS[:9], "オッズ更新", "人気"]


def _make_row(umaban: str, horse_name: str, odds: str) -> MagicMock:
    """出馬表の1行の要素のモックを返す"""
    row = MagicMock()
    tds = [MagicMock() for _ in range(11)]
    tds[1].text.strip.return_value = umaban
    tds[9].text.strip.return_value = odds
    row.find_elements.return_value = tds
    horse_name_elem = MagicMock()
    horse_name_elem.text.strip.return_value = horse_name
    row.find_element.return_value = horse_name_elem
    return row


def _make_driver(rows: list[MagicMock], headers: list[str] | None = None) -> MagicMock:
    """見出しと馬情報を返すドライバーのモックを返す"""
    header_cells = []
    for text in _YOSO_HEADERS if headers is None else headers:
        cell = MagicMock()
        cell.text.strip.return_value = text
        header_cells.append(cell)

    def find_elements(by: str, value: str) -> list[MagicMock]:
        return header_cells if by == By.CSS_SELECTOR else rows

    driver = MagicMock()
    driver.find_elements.side_effect = find_elements
    return driver


@pytest.fixture
def mock_horse_elements() -> list[MagicMock]:
    """馬情報要素のモックを返す"""
    return [
        _make_row("1", "アドマイヤクワッズ", "1.8"),
        _make_row("2", "ライヒスアドラー", "3.9"),
        _make_row("3", "バステール", "4.2"),
    ]


# 正常系
def test_scrape_yoso_odds_from_netkeiba_returns_correct_columns(
    mock_horse_elements: list[MagicMock],
) -> None:
    """戻り値がYOSO_ODDS_COLUMNSのカラムを持つDataFrameであること"""
    with patch("scraping.odds.webdriver.Chrome", return_value=_make_driver(mock_horse_elements)):
        result = scrape_yoso_odds_from_netkeiba("202606020411")

    assert isinstance(result, pd.DataFrame)
    assert list(result.columns) == YOSO_ODDS_COLUMNS


def test_scrape_yoso_odds_from_netkeiba_extracts_horse_name(
    mock_horse_elements: list[MagicMock],
) -> None:
    """馬名が正しく抽出されること"""
    with patch("scraping.odds.webdriver.Chrome", return_value=_make_driver(mock_horse_elements)):
        result = scrape_yoso_odds_from_netkeiba("202606020411")

    assert "アドマイヤクワッズ" in result["馬名"].values
    assert "ライヒスアドラー" in result["馬名"].values
    assert "バステール" in result["馬名"].values


def test_scrape_yoso_odds_from_netkeiba_extracts_umaban(
    mock_horse_elements: list[MagicMock],
) -> None:
    """馬番が正しく抽出されること"""
    with patch("scraping.odds.webdriver.Chrome", return_value=_make_driver(mock_horse_elements)):
        result = scrape_yoso_odds_from_netkeiba("202606020411")

    umaban_values = result["馬番"].tolist()
    assert 1 in umaban_values
    assert 2 in umaban_values
    assert 3 in umaban_values


def test_scrape_yoso_odds_from_netkeiba_extracts_yoso_odds(
    mock_horse_elements: list[MagicMock],
) -> None:
    """予想単勝オッズが正しく抽出されること"""
    with patch("scraping.odds.webdriver.Chrome", return_value=_make_driver(mock_horse_elements)):
        result = scrape_yoso_odds_from_netkeiba("202606020411")

    odds_values = result["予想単勝オッズ"].tolist()
    assert 1.8 in odds_values
    assert 3.9 in odds_values
    assert 4.2 in odds_values


def test_scrape_yoso_odds_from_netkeiba_row_count(
    mock_horse_elements: list[MagicMock],
) -> None:
    """取得した行数が馬の数と一致すること"""
    with patch("scraping.odds.webdriver.Chrome", return_value=_make_driver(mock_horse_elements)):
        result = scrape_yoso_odds_from_netkeiba("202606020411")

    assert len(result) == 3


def test_scrape_yoso_odds_from_netkeiba_before_waku_confirmed_returns_horse_name() -> None:
    """枠順確定前は馬番が欠損し、馬名と予想単勝オッズを返すこと"""
    rows = [_make_row("", "テスト馬1", "2.5"), _make_row("", "テスト馬2", "7.1")]
    with patch("scraping.odds.webdriver.Chrome", return_value=_make_driver(rows)):
        result = scrape_yoso_odds_from_netkeiba("202606020411")

    assert len(result) == 2
    assert result["馬番"].isna().all()
    assert result["馬名"].tolist() == ["テスト馬1", "テスト馬2"]
    assert result["予想単勝オッズ"].tolist() == [2.5, 7.1]


# 準正常系
def test_scrape_yoso_odds_from_netkeiba_sold_raises_expected_odds_unavailable(
    mock_horse_elements: list[MagicMock],
) -> None:
    """オッズ列が予想オッズでない場合はExpectedOddsUnavailableErrorを送出すること"""
    driver = _make_driver(mock_horse_elements, headers=_SOLD_HEADERS)
    with (
        patch("scraping.odds.webdriver.Chrome", return_value=driver),
        pytest.raises(ExpectedOddsUnavailableError, match="オッズ更新"),
    ):
        scrape_yoso_odds_from_netkeiba("202606020411")


def test_scrape_yoso_odds_from_netkeiba_missing_header_raises_parse_error(
    mock_horse_elements: list[MagicMock],
) -> None:
    """オッズ列の見出しが読み取れない場合はParseErrorを送出すること"""
    driver = _make_driver(mock_horse_elements, headers=_YOSO_HEADERS[:5])
    with (
        patch("scraping.odds.webdriver.Chrome", return_value=driver),
        pytest.raises(ParseError, match="見出しを読み取れませんでした"),
    ):
        scrape_yoso_odds_from_netkeiba("202606020411")


def test_scrape_yoso_odds_from_netkeiba_no_horses_returns_empty() -> None:
    """馬情報がない場合は空のDataFrameを返すこと"""
    with patch("scraping.odds.webdriver.Chrome", return_value=_make_driver([])):
        result = scrape_yoso_odds_from_netkeiba("202606020411")

    assert isinstance(result, pd.DataFrame)
    assert list(result.columns) == YOSO_ODDS_COLUMNS
    assert len(result) == 0


def test_scrape_yoso_odds_from_netkeiba_invalid_odds_returns_nan() -> None:
    """オッズが無効な場合はNaNになること"""
    with patch(
        "scraping.odds.webdriver.Chrome",
        return_value=_make_driver([_make_row("1", "テスト馬", "---")]),
    ):
        result = scrape_yoso_odds_from_netkeiba("202606020411")

    assert len(result) == 1
    assert np.isnan(result["予想単勝オッズ"].iloc[0])


def test_scrape_yoso_odds_from_netkeiba_empty_umaban_returns_nan() -> None:
    """馬番が空の場合はNaNになること(枠順未確定時)"""
    with patch(
        "scraping.odds.webdriver.Chrome",
        return_value=_make_driver([_make_row("", "テスト馬", "2.5")]),
    ):
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
