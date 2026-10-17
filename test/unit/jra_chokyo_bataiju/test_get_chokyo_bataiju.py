"""JraChokyoBataijuScraper.get_chokyo_bataiju()の単体テスト

フィクスチャHTMLを使用して正常系・準正常系のテストを行う。
"""

import datetime
import os
import tempfile
from unittest.mock import MagicMock

import pandas as pd
import pytest
import requests

from scraping.config import JRA_CHOKYO_BATAIJU_COLUMNS
from scraping.exceptions import (
    ChokyoBataijuUnavailableError,
    NetworkError,
    PageNotFoundError,
    ParseError,
)
from scraping.jra_chokyo_bataiju import JraChokyoBataijuScraper

from .conftest import (
    FIXTURE_NEWS,
    FIXTURE_WEIGHT_PAGE,
    NEWS_PATH,
    create_scraper_with_mock,
    load_html,
)


# ---------------------------------------------------------------------------
# 正常系
# ---------------------------------------------------------------------------
def test_get_chokyo_bataiju_follows_weight_button() -> None:
    """G1特設ページの調教後馬体重ボタンのリンク先のニュースを取得すること"""
    scraper, mock_session = create_scraper_with_mock(
        load_html(FIXTURE_WEIGHT_PAGE), load_html(FIXTURE_NEWS)
    )
    scraper.get_chokyo_bataiju()

    urls = [call.args[0] for call in mock_session.get.call_args_list]
    assert urls == [
        "https://www.jra.go.jp/keiba/g1/shuka/weight.html",
        f"https://www.jra.go.jp{NEWS_PATH}",
    ]


def test_get_chokyo_bataiju_columns_and_rows() -> None:
    """カラムがJRA_CHOKYO_BATAIJU_COLUMNSと一致し、表の全17頭を取得すること"""
    scraper, _ = create_scraper_with_mock(load_html(FIXTURE_WEIGHT_PAGE), load_html(FIXTURE_NEWS))
    df = scraper.get_chokyo_bataiju()

    assert list(df.columns) == JRA_CHOKYO_BATAIJU_COLUMNS
    assert len(df) == 17


def test_get_chokyo_bataiju_first_row_values() -> None:
    """先頭行の値が正しいこと（エンネ）"""
    scraper, _ = create_scraper_with_mock(load_html(FIXTURE_WEIGHT_PAGE), load_html(FIXTURE_NEWS))
    df = scraper.get_chokyo_bataiju()

    first = df.iloc[0]
    assert first["馬名"] == "エンネ"
    assert first["馬体重"] == 528
    assert first["計量日"] == datetime.date(2026, 10, 15)
    assert first["計量場所"] == "栗東"
    assert first["調教師"] == "吉岡　辰弥"
    assert first["所属"] == "栗東"
    assert first["前走馬体重"] == 522


def test_get_chokyo_bataiju_empty_previous_weight() -> None:
    """前走馬体重が空欄の馬はNAになること"""
    news_html = load_html(FIXTURE_NEWS).replace("<td>522</td>", "<td></td>", 1)
    scraper, _ = create_scraper_with_mock(load_html(FIXTURE_WEIGHT_PAGE), news_html)
    df = scraper.get_chokyo_bataiju()

    assert str(df["前走馬体重"].dtype) == "Int64"
    assert pd.isna(df.iloc[0]["前走馬体重"])


def test_save_to_csv() -> None:
    """CSVファイルが正しく保存されること"""
    scraper, _ = create_scraper_with_mock(load_html(FIXTURE_WEIGHT_PAGE), load_html(FIXTURE_NEWS))
    df = scraper.get_chokyo_bataiju()

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        scraper.save_to_csv(df, tmp_path)

        saved_df = pd.read_csv(tmp_path, encoding="utf-8-sig")
        assert list(saved_df.columns) == JRA_CHOKYO_BATAIJU_COLUMNS
        assert len(saved_df) == 17
    finally:
        os.remove(tmp_path)


# ---------------------------------------------------------------------------
# 準正常系: 調教後馬体重が未発表
# ---------------------------------------------------------------------------
def test_get_chokyo_bataiju_button_points_to_itself() -> None:
    """ボタンが調教後馬体重のページ自身を指す場合にChokyoBataijuUnavailableErrorが発生すること"""
    weight_page_html = load_html(FIXTURE_WEIGHT_PAGE).replace(
        NEWS_PATH, "/keiba/g1/shuka/weight.html"
    )
    scraper, _ = create_scraper_with_mock(weight_page_html, load_html(FIXTURE_NEWS))

    with pytest.raises(ChokyoBataijuUnavailableError, match="まだ発表されていません"):
        scraper.get_chokyo_bataiju()


def test_get_chokyo_bataiju_no_button() -> None:
    """ボタンが無い場合にChokyoBataijuUnavailableErrorが発生すること"""
    scraper, _ = create_scraper_with_mock("<html><body></body></html>", load_html(FIXTURE_NEWS))

    with pytest.raises(ChokyoBataijuUnavailableError):
        scraper.get_chokyo_bataiju()


# ---------------------------------------------------------------------------
# 準正常系: ニュースを解析できない
# ---------------------------------------------------------------------------
def test_get_chokyo_bataiju_no_table() -> None:
    """ニュースに調教後馬体重の表が無い場合にParseErrorが発生すること"""
    scraper, _ = create_scraper_with_mock(
        load_html(FIXTURE_WEIGHT_PAGE), "<html><body><p>表なし</p></body></html>"
    )

    with pytest.raises(ParseError, match="調教後馬体重の表が見つかりません"):
        scraper.get_chokyo_bataiju()


def test_get_chokyo_bataiju_missing_column() -> None:
    """表に必要な列の見出しが無い場合にParseErrorが発生すること"""
    news_html = load_html(FIXTURE_NEWS).replace("計量場所", "計量地", 1)
    scraper, _ = create_scraper_with_mock(load_html(FIXTURE_WEIGHT_PAGE), news_html)

    with pytest.raises(ParseError, match="計量場所"):
        scraper.get_chokyo_bataiju()


@pytest.mark.parametrize("date_text", ["未定", "10月32日（金曜）", "13月1日（日曜）"])
def test_get_chokyo_bataiju_invalid_date(date_text: str) -> None:
    """計量日が日付として解釈できない場合にParseErrorが発生すること"""
    news_html = load_html(FIXTURE_NEWS).replace("10月15日（木曜）", date_text, 1)
    scraper, _ = create_scraper_with_mock(load_html(FIXTURE_WEIGHT_PAGE), news_html)

    with pytest.raises(ParseError, match="計量日のパースに失敗しました"):
        scraper.get_chokyo_bataiju()


def test_get_chokyo_bataiju_invalid_weight() -> None:
    """馬体重が数値でない場合にParseErrorが発生すること"""
    news_html = load_html(FIXTURE_NEWS).replace("<td>528</td>", "<td>計不</td>", 1)
    scraper, _ = create_scraper_with_mock(load_html(FIXTURE_WEIGHT_PAGE), news_html)

    with pytest.raises(ParseError, match="馬体重のパースに失敗しました"):
        scraper.get_chokyo_bataiju()


# ---------------------------------------------------------------------------
# 準正常系: HTTPエラー・ネットワークエラー
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("status_code", [403, 404])
def test_get_chokyo_bataiju_page_not_found(status_code: int) -> None:
    """G1特設ページが403・404の場合にPageNotFoundErrorが発生すること"""
    mock_session = MagicMock()
    scraper = JraChokyoBataijuScraper("kikuka", session=mock_session)

    mock_response = MagicMock()
    mock_response.status_code = status_code
    http_error = requests.exceptions.HTTPError(response=mock_response)
    mock_session.get.return_value.raise_for_status.side_effect = http_error

    with pytest.raises(PageNotFoundError):
        scraper.get_chokyo_bataiju()


def test_get_chokyo_bataiju_server_error() -> None:
    """500エラーの場合にNetworkErrorが発生すること"""
    mock_session = MagicMock()
    scraper = JraChokyoBataijuScraper("shuka", session=mock_session)

    mock_response = MagicMock()
    mock_response.status_code = 500
    http_error = requests.exceptions.HTTPError(response=mock_response)
    mock_session.get.return_value.raise_for_status.side_effect = http_error

    with pytest.raises(NetworkError, match="HTTPエラーが発生しました"):
        scraper.get_chokyo_bataiju()


def test_get_chokyo_bataiju_network_error() -> None:
    """ネットワークエラーの場合にNetworkErrorが発生すること"""
    mock_session = MagicMock()
    scraper = JraChokyoBataijuScraper("shuka", session=mock_session)

    mock_session.get.side_effect = requests.exceptions.ConnectionError("接続エラー")

    with pytest.raises(NetworkError, match="ネットワークエラーが発生しました"):
        scraper.get_chokyo_bataiju()
