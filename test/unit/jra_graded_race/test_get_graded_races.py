"""JraGradedRaceScraper.get_graded_races()の単体テスト

フィクスチャHTMLを使用して正常系・準正常系のテストを行う。
"""

import datetime
import os
import tempfile
from unittest.mock import MagicMock

import pandas as pd
import pytest

from scraping.config import JRA_GRADED_RACE_COLUMNS
from scraping.exceptions import NetworkError, PageNotFoundError, ParseError
from scraping.jra_graded_race import JraGradedRaceScraper

from .conftest import create_scraper_with_mock

# ---------------------------------------------------------------------------
# テスト用定数
# ---------------------------------------------------------------------------
FIXTURE_NORMAL = "jra_graded_race_2025.html"
FIXTURE_SPECIAL = "jra_graded_race_2025_special.html"
YEAR = 2025


# ---------------------------------------------------------------------------
# 正常系: 基本的なデータ取得
# ---------------------------------------------------------------------------
def test_get_graded_races_returns_dataframe() -> None:
    """get_graded_racesがDataFrameを返すこと"""
    scraper = create_scraper_with_mock(YEAR, FIXTURE_NORMAL)
    df = scraper.get_graded_races()

    assert isinstance(df, pd.DataFrame)


def test_get_graded_races_columns() -> None:
    """取得結果のカラムがJRA_GRADED_RACE_COLUMNSと一致すること"""
    scraper = create_scraper_with_mock(YEAR, FIXTURE_NORMAL)
    df = scraper.get_graded_races()

    assert list(df.columns) == JRA_GRADED_RACE_COLUMNS


def test_get_graded_races_row_count() -> None:
    """フィクスチャ（10行、うち同着1組）から11行取得できること"""
    scraper = create_scraper_with_mock(YEAR, FIXTURE_NORMAL)
    df = scraper.get_graded_races()

    # HTMLは10行だが小倉牝馬S（同着）で2行に展開されるため11行
    assert len(df) == 11


def test_get_graded_races_first_row_values() -> None:
    """先頭行の値が正しいこと（中山金杯 2025年1月5日）"""
    scraper = create_scraper_with_mock(YEAR, FIXTURE_NORMAL)
    df = scraper.get_graded_races()

    first = df.iloc[0]
    assert first["日付"] == datetime.date(2025, 1, 5)
    assert first["グレード"] == "GⅢ"
    assert first["レース名"] == "中山金杯"
    assert first["競馬場"] == "中山"
    assert first["性齢"] == "4歳以上"
    assert first["芝ダ"] == "芝"
    assert first["距離"] == 2000
    assert first["優勝馬"] == "アルナシーム"
    assert first["騎手"] == "藤岡\u3000佑介"


def test_get_graded_races_dirt_race() -> None:
    """ダートレース（プロキオンS）が正しくパースされること"""
    scraper = create_scraper_with_mock(YEAR, FIXTURE_NORMAL)
    df = scraper.get_graded_races()

    # 10行目（index=9）がプロキオンS
    prokion = df[df["レース名"] == "プロキオンS"]
    assert len(prokion) == 1
    assert prokion.iloc[0]["芝ダ"] == "ダ"
    assert prokion.iloc[0]["距離"] == 1800


# ---------------------------------------------------------------------------
# 正常系: 同着のパース
# ---------------------------------------------------------------------------
def test_get_graded_races_dead_heat() -> None:
    """同着の場合に複数行が生成されること"""
    scraper = create_scraper_with_mock(YEAR, FIXTURE_SPECIAL)
    df = scraper.get_graded_races()

    # 同着行(小倉牝馬S) → 2行に展開される
    ogura = df[df["レース名"] == "小倉牝馬S"]
    assert len(ogura) == 2
    assert ogura.iloc[0]["優勝馬"] == "フェアエールング"
    assert ogura.iloc[1]["優勝馬"] == "シンティレーション"
    assert ogura.iloc[0]["騎手"] == "丹内\u3000祐次"
    assert ogura.iloc[1]["騎手"] == "杉原\u3000誠人"


# ---------------------------------------------------------------------------
# 正常系: 障害レースのパース
# ---------------------------------------------------------------------------
def test_get_graded_races_obstacle_race() -> None:
    """障害レースが正しくパースされること"""
    scraper = create_scraper_with_mock(YEAR, FIXTURE_SPECIAL)
    df = scraper.get_graded_races()

    obstacle = df[df["レース名"] == "小倉ジャンプS"]
    assert len(obstacle) == 1
    assert obstacle.iloc[0]["芝ダ"] == "障"
    assert obstacle.iloc[0]["距離"] == 3390
    assert obstacle.iloc[0]["グレード"] == "J・GⅢ"


# ---------------------------------------------------------------------------
# 正常系: G1レース（リンク付き）のパース
# ---------------------------------------------------------------------------
def test_get_graded_races_g1_with_link() -> None:
    """G1レース（リンク付き）が正しくパースされること"""
    scraper = create_scraper_with_mock(YEAR, FIXTURE_SPECIAL)
    df = scraper.get_graded_races()

    g1 = df[df["レース名"] == "フェブラリーS"]
    assert len(g1) == 1
    assert g1.iloc[0]["グレード"] == "GⅠ"
    assert g1.iloc[0]["芝ダ"] == "ダ"
    assert g1.iloc[0]["距離"] == 1600


# ---------------------------------------------------------------------------
# 正常系: 祝日の日付パース
# ---------------------------------------------------------------------------
def test_get_graded_races_holiday_date() -> None:
    """祝日の日付が正しくパースされること"""
    scraper = create_scraper_with_mock(YEAR, FIXTURE_SPECIAL)
    df = scraper.get_graded_races()

    feb_s = df[df["レース名"] == "フェブラリーS"]
    assert feb_s.iloc[0]["日付"] == datetime.date(2025, 2, 23)


# ---------------------------------------------------------------------------
# 正常系: CSV保存
# ---------------------------------------------------------------------------
def test_save_to_csv() -> None:
    """CSVファイルが正しく保存されること"""
    scraper = create_scraper_with_mock(YEAR, FIXTURE_NORMAL)
    df = scraper.get_graded_races()

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        scraper.save_to_csv(df, tmp_path)

        saved_df = pd.read_csv(tmp_path, encoding="utf-8-sig")
        assert list(saved_df.columns) == JRA_GRADED_RACE_COLUMNS
        assert len(saved_df) == 11
    finally:
        os.remove(tmp_path)


# ---------------------------------------------------------------------------
# 準正常系: テーブルが見つからない場合
# ---------------------------------------------------------------------------
def test_get_graded_races_no_table() -> None:
    """テーブルがないHTMLの場合にParseErrorが発生すること"""
    mock_session = MagicMock()
    scraper = JraGradedRaceScraper(YEAR, session=mock_session)

    mock_response = MagicMock()
    mock_response.text = "<html><body><p>テーブルなし</p></body></html>"
    mock_response.apparent_encoding = "utf-8"
    mock_session.get.return_value = mock_response

    with pytest.raises(ParseError, match="重賞レース一覧テーブルが見つかりません"):
        scraper.get_graded_races()


# ---------------------------------------------------------------------------
# 準正常系: 404エラー
# ---------------------------------------------------------------------------
def test_get_graded_races_404() -> None:
    """404エラーの場合にPageNotFoundErrorが発生すること"""
    import requests

    mock_session = MagicMock()
    scraper = JraGradedRaceScraper(YEAR, session=mock_session)

    mock_response = MagicMock()
    mock_response.status_code = 404
    http_error = requests.exceptions.HTTPError(response=mock_response)
    mock_session.get.return_value.raise_for_status.side_effect = http_error

    with pytest.raises(PageNotFoundError):
        scraper.get_graded_races()


# ---------------------------------------------------------------------------
# 準正常系: ネットワークエラー
# ---------------------------------------------------------------------------
def test_get_graded_races_network_error() -> None:
    """ネットワークエラーの場合にNetworkErrorが発生すること"""
    import requests

    mock_session = MagicMock()
    scraper = JraGradedRaceScraper(YEAR, session=mock_session)

    mock_session.get.side_effect = requests.exceptions.ConnectionError("接続エラー")

    with pytest.raises(NetworkError, match="ネットワークエラーが発生しました"):
        scraper.get_graded_races()
