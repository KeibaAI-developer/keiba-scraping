"""JraPreRatingScraper.get_pre_rating()の単体テスト

フィクスチャHTMLを使用して正常系・準正常系のテストを行う。
"""

import os
import tempfile
from unittest.mock import MagicMock

import pandas as pd
import pytest
import requests

from scraping.config import JRA_PRE_RATING_COLUMNS
from scraping.exceptions import NetworkError, PageNotFoundError, ParseError
from scraping.jra_pre_rating import JraPreRatingScraper

from .conftest import (
    FIXTURE_CURRENT,
    FIXTURE_CURRENT_WITH_FOREIGN,
    FIXTURE_CURRENT_WITH_PREVIOUS,
    FIXTURE_OLD,
    FIXTURE_OLD_WITH_FOREIGN,
    FIXTURE_OLD_WITH_PREVIOUS,
    create_scraper_with_mock,
    load_html,
)


def _row(df: pd.DataFrame, name: str) -> pd.Series:
    """馬名の行を返す"""
    rows = df[df["馬名"] == name]
    assert len(rows) == 1
    return rows.iloc[0]


# ---------------------------------------------------------------------------
# 正常系
# ---------------------------------------------------------------------------
def test_get_pre_rating_requests_rating_page() -> None:
    """開催年とページ名から作ったプレレーティングのページを取得すること"""
    scraper, mock_session = create_scraper_with_mock(load_html(FIXTURE_CURRENT))
    scraper.get_pre_rating()

    url = mock_session.get.call_args.args[0]
    assert url == "https://www.jra.go.jp/datafile/ranking/g1/2026/eliza.html"


def test_get_pre_rating_columns_and_rows() -> None:
    """カラムがJRA_PRE_RATING_COLUMNSと一致し、表の全23頭を取得すること"""
    scraper, _ = create_scraper_with_mock(load_html(FIXTURE_CURRENT))
    df = scraper.get_pre_rating()

    assert list(df.columns) == JRA_PRE_RATING_COLUMNS
    assert len(df) == 23
    assert df["レーティング"].dtype == "Int64"
    assert df["前年レーティング"].dtype == "Int64"


def test_get_pre_rating_current_layout_values() -> None:
    """2017年以降の形の値を読めること（アクアヴァーナル）"""
    scraper, _ = create_scraper_with_mock(load_html(FIXTURE_CURRENT))
    row = scraper.get_pre_rating().iloc[0]

    assert row["馬名"] == "アクアヴァーナル"
    assert row["性"] == "牝"
    assert row["年齢"] == 5
    assert row["調教師"] == "四位　洋文"
    assert row["レーティング"] == 111
    assert row["距離区分"] == "E"
    assert pd.isna(row["前年レーティング"])
    assert pd.isna(row["前年距離区分"])
    assert row["該当レース"] == "天皇賞（春）4着"


def test_get_pre_rating_current_layout_no_value() -> None:
    """値が「−」の馬はレーティング・距離区分・該当レースが欠損になること（アマイ）"""
    scraper, _ = create_scraper_with_mock(load_html(FIXTURE_CURRENT))
    row = _row(scraper.get_pre_rating(), "アマイ")

    assert pd.isna(row["レーティング"])
    assert pd.isna(row["距離区分"])
    assert pd.isna(row["該当レース"])


def test_get_pre_rating_current_layout_with_previous() -> None:
    """前年のJPNランキングの列がある形で、両方の値を読めること（エコロヴァルツ）"""
    scraper, _ = create_scraper_with_mock(load_html(FIXTURE_CURRENT_WITH_PREVIOUS))
    df = scraper.get_pre_rating()
    row = _row(df, "エコロヴァルツ")

    assert len(df) == 16
    assert row["レーティング"] == 111
    assert row["距離区分"] == "M"
    assert row["前年レーティング"] == 114
    assert row["前年距離区分"] == "M,I"
    assert row["該当レース"] == "中山記念3着（中山記念2着、大阪杯4着）"


def test_get_pre_rating_current_layout_previous_only() -> None:
    """前年の値だけがある馬は、開催年のレーティングが欠損になること（クロワデュノール）"""
    scraper, _ = create_scraper_with_mock(load_html(FIXTURE_CURRENT_WITH_PREVIOUS))
    row = _row(scraper.get_pre_rating(), "クロワデュノール")

    assert pd.isna(row["レーティング"])
    assert row["前年レーティング"] == 122
    assert row["前年距離区分"] == "L"


def test_get_pre_rating_current_layout_foreign_horse() -> None:
    """外国馬の表の馬は、欧字の馬名を除き、該当レースが欠損になること（マジカルラグーン）"""
    scraper, _ = create_scraper_with_mock(load_html(FIXTURE_CURRENT_WITH_FOREIGN))
    df = scraper.get_pre_rating()
    row = df.iloc[-1]

    assert len(df) == 23
    assert row["馬名"] == "マジカルラグーン"
    assert row["調教師"] == "Mrs.J.ハリントン"
    assert row["レーティング"] == 111
    assert row["距離区分"] == "L"
    assert pd.isna(row["該当レース"])


def test_get_pre_rating_old_layout_values() -> None:
    """2016年以前の形の、全角の数値と別のセルの距離区分を読めること（シュンドルボン）"""
    scraper, _ = create_scraper_with_mock(load_html(FIXTURE_OLD))
    df = scraper.get_pre_rating()
    row = _row(df, "シュンドルボン")

    assert len(df) == 16
    assert row["年齢"] == 5
    assert row["レーティング"] == 105
    assert row["距離区分"] == "M,I"
    assert row["該当レース"] == "中山牝馬Ｓ１着、マーメイドＳ４着"


def test_get_pre_rating_old_layout_no_value() -> None:
    """2016年以前の形で値が無い馬は、レーティングが欠損になること（シングウィズジョイ）"""
    scraper, _ = create_scraper_with_mock(load_html(FIXTURE_OLD))
    row = _row(scraper.get_pre_rating(), "シングウィズジョイ")

    assert pd.isna(row["レーティング"])
    assert pd.isna(row["距離区分"])
    assert pd.isna(row["該当レース"])


def test_get_pre_rating_old_layout_with_previous() -> None:
    """2016年以前の形で前年のJPNランキングの列がある場合に、両方の値を読めること"""
    scraper, _ = create_scraper_with_mock(load_html(FIXTURE_OLD_WITH_PREVIOUS))
    df = scraper.get_pre_rating()
    both = _row(df, "グランドシチー")
    previous_only = _row(df, "エーシントップ")

    assert len(df) == 20
    assert both["レーティング"] == 107
    assert both["距離区分"] == "M"
    assert both["前年レーティング"] == 110
    assert both["前年距離区分"] == "M"
    assert pd.isna(previous_only["レーティング"])
    assert previous_only["前年レーティング"] == 108
    assert previous_only["前年距離区分"] == "M(T)"


def test_get_pre_rating_old_layout_foreign_horses() -> None:
    """2016年以前の形の外国馬の表を、日本馬の表の後ろにつなぐこと"""
    scraper, _ = create_scraper_with_mock(load_html(FIXTURE_OLD_WITH_FOREIGN))
    df = scraper.get_pre_rating()

    assert len(df) == 22
    assert df["馬名"].tolist()[-2:] == ["スノーフェアリー", "ダンシングレイン"]
    assert df.iloc[-2]["レーティング"] == 122
    assert df.iloc[-2]["距離区分"] == "I"
    assert pd.isna(df.iloc[-2]["該当レース"])


def test_save_to_csv() -> None:
    """取得したDataFrameをCSVに保存できること"""
    scraper, _ = create_scraper_with_mock(load_html(FIXTURE_CURRENT))
    df = scraper.get_pre_rating()

    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = os.path.join(tmpdir, "pre_rating.csv")
        scraper.save_to_csv(df, filepath)
        saved = pd.read_csv(filepath, encoding="utf-8-sig")

    assert list(saved.columns) == JRA_PRE_RATING_COLUMNS
    assert len(saved) == 23


# ---------------------------------------------------------------------------
# 準正常系: 解析エラー
# ---------------------------------------------------------------------------
def test_get_pre_rating_no_table() -> None:
    """プレレーティングの表が無い場合にParseErrorが発生すること"""
    scraper, _ = create_scraper_with_mock("<html><body><p>準備中</p></body></html>")

    with pytest.raises(ParseError, match="プレレーティングの表が見つかりません"):
        scraper.get_pre_rating()


def test_get_pre_rating_no_horse() -> None:
    """表に馬がいない場合にParseErrorが発生すること"""
    html = (
        "<table><tr><th>馬名</th><th>性</th><th>年齢</th><th>調教師</th>"
        "<th>2026年度レーティングの最高値</th><th>2026年度レーティング該当レース</th></tr></table>"
    )
    scraper, _ = create_scraper_with_mock(html)

    with pytest.raises(ParseError, match="プレレーティングの表に馬がいません"):
        scraper.get_pre_rating()


def test_get_pre_rating_unexpected_last_header() -> None:
    """最後の列の見出しが該当レースでも調教国でもない場合にParseErrorが発生すること"""
    html = load_html(FIXTURE_CURRENT).replace("レーティング該当レース", "備考", 1)
    scraper, _ = create_scraper_with_mock(html)

    with pytest.raises(ParseError, match="最後の列が想定と異なります"):
        scraper.get_pre_rating()


@pytest.mark.parametrize("num_text", ["未定", "111.5"])
def test_get_pre_rating_invalid_rating(num_text: str) -> None:
    """レーティングの数値を整数として読めない場合にParseErrorが発生すること"""
    html = load_html(FIXTURE_CURRENT).replace('<span class="num">111</span>', num_text, 1)
    scraper, _ = create_scraper_with_mock(html)

    with pytest.raises(ParseError, match="レーティングの値を読めません"):
        scraper.get_pre_rating()


def test_get_pre_rating_invalid_category() -> None:
    """距離区分を読めない場合にParseErrorが発生すること"""
    html = load_html(FIXTURE_CURRENT).replace("<span>E</span>", "<span>X</span>", 1)
    scraper, _ = create_scraper_with_mock(html)

    with pytest.raises(ParseError, match="レーティングの値を読めません"):
        scraper.get_pre_rating()


def test_get_pre_rating_old_layout_invalid_category() -> None:
    """2016年以前の形で距離区分を読めない場合にParseErrorが発生すること"""
    html = load_html(FIXTURE_OLD).replace(">Ｍ，Ｉ<", ">ＭＩＸ<", 1)
    scraper, _ = create_scraper_with_mock(html)

    with pytest.raises(ParseError, match="距離区分を読めません"):
        scraper.get_pre_rating()


def test_get_pre_rating_logs_parse_error() -> None:
    """解析に失敗した場合に、注入したロガーへ記録してからParseErrorを送出すること"""
    scraper, _ = create_scraper_with_mock("<html><body><p>準備中</p></body></html>")
    scraper._logger = MagicMock()

    with pytest.raises(ParseError):
        scraper.get_pre_rating()

    scraper._logger.error.assert_called_once()


# ---------------------------------------------------------------------------
# 準正常系: HTTPエラー・ネットワークエラー
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("status_code", [403, 404])
def test_get_pre_rating_page_not_found(status_code: int) -> None:
    """ページが403・404の場合にPageNotFoundErrorが発生すること"""
    mock_session = MagicMock()
    scraper = JraPreRatingScraper(2026, "japanc", session=mock_session)

    mock_response = MagicMock()
    mock_response.status_code = status_code
    http_error = requests.exceptions.HTTPError(response=mock_response)
    mock_session.get.return_value.raise_for_status.side_effect = http_error

    with pytest.raises(PageNotFoundError):
        scraper.get_pre_rating()


def test_get_pre_rating_server_error() -> None:
    """500エラーの場合にNetworkErrorが発生すること"""
    mock_session = MagicMock()
    scraper = JraPreRatingScraper(2026, "eliza", session=mock_session)

    mock_response = MagicMock()
    mock_response.status_code = 500
    http_error = requests.exceptions.HTTPError(response=mock_response)
    mock_session.get.return_value.raise_for_status.side_effect = http_error

    with pytest.raises(NetworkError, match="HTTPエラーが発生しました"):
        scraper.get_pre_rating()


def test_get_pre_rating_network_error() -> None:
    """ネットワークエラーの場合にNetworkErrorが発生すること"""
    mock_session = MagicMock()
    scraper = JraPreRatingScraper(2026, "eliza", session=mock_session)

    mock_session.get.side_effect = requests.exceptions.ConnectionError("接続エラー")

    with pytest.raises(NetworkError, match="ネットワークエラーが発生しました"):
        scraper.get_pre_rating()
