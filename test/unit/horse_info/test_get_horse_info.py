"""HorseInfoScraper.get_all_horse_info() / scrape_one_page()の単体テスト

requestsをモックし、フィクスチャHTMLを返すようにしてテストする。
馬情報テーブルの取得・カラム構成・主要値を検証する。
"""

from typing import Any
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from scraping.config import HORSE_INFO_COLUMNS
from scraping.exceptions import ParseError
from scraping.horse_info import HorseInfoScraper

from .conftest import create_scraper_with_mock

# ---------------------------------------------------------------------------
# テスト用定数
# ---------------------------------------------------------------------------
FIXTURE_P1 = "horse_info_2022_p1.html"
FIXTURE_P80 = "horse_info_2022_p80.html"
YEAR = 2022


# ---------------------------------------------------------------------------
# 正常系: カラム構成の確認
# ---------------------------------------------------------------------------
def test_columns_match_horse_info_columns_p1() -> None:
    """1ページ目のカラム構成がHORSE_INFO_COLUMNSと一致すること"""
    scraper = create_scraper_with_mock(YEAR, 1, [FIXTURE_P1])
    df = scraper.scrape_one_page(1)

    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == HORSE_INFO_COLUMNS


def test_columns_match_horse_info_columns_p80() -> None:
    """最終ページのカラム構成がHORSE_INFO_COLUMNSと一致すること"""
    scraper = create_scraper_with_mock(YEAR, 1, [FIXTURE_P80])
    df = scraper.scrape_one_page(1)

    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == HORSE_INFO_COLUMNS


# ---------------------------------------------------------------------------
# 正常系: 行数の確認
# ---------------------------------------------------------------------------
def test_row_count_p1() -> None:
    """1ページ目は100行であること"""
    scraper = create_scraper_with_mock(YEAR, 1, [FIXTURE_P1])
    df = scraper.scrape_one_page(1)

    assert len(df) == 100


def test_row_count_p80() -> None:
    """最終ページは75行であること"""
    scraper = create_scraper_with_mock(YEAR, 1, [FIXTURE_P80])
    df = scraper.scrape_one_page(1)

    assert len(df) == 75


# ---------------------------------------------------------------------------
# 正常系: 生年の検証
# ---------------------------------------------------------------------------
def test_birth_year_is_consistent() -> None:
    """全行の生年がコンストラクタで指定した年と一致すること"""
    scraper = create_scraper_with_mock(YEAR, 1, [FIXTURE_P1])
    df = scraper.scrape_one_page(1)

    assert (df["生年"] == YEAR).all()


# ---------------------------------------------------------------------------
# 正常系: 馬IDの形式
# ---------------------------------------------------------------------------
def test_horse_id_format() -> None:
    """馬IDが10桁の数字文字列であること"""
    scraper = create_scraper_with_mock(YEAR, 1, [FIXTURE_P1])
    df = scraper.scrape_one_page(1)

    for horse_id in df["馬ID"]:
        assert isinstance(horse_id, str), f"馬IDが文字列でない: {horse_id}"
        assert len(horse_id) == 10, f"馬IDが10桁でない: {horse_id}"
        assert horse_id.isdigit(), f"馬IDが数字でない: {horse_id}"


# ---------------------------------------------------------------------------
# 正常系: 所属の変換
# ---------------------------------------------------------------------------
def test_affiliation_values() -> None:
    """所属が美浦/栗東/地方/海外/NaNのいずれかであること"""
    scraper = create_scraper_with_mock(YEAR, 1, [FIXTURE_P1])
    df = scraper.scrape_one_page(1)

    valid = {"美浦", "栗東", "地方", "海外"}
    actual = set(df["所属"].dropna().unique())
    assert actual <= valid, f"不正な所属: {actual - valid}"


def test_affiliation_contains_kuritto_and_miho() -> None:
    """1ページ目に栗東と美浦の両方が含まれること"""
    scraper = create_scraper_with_mock(YEAR, 1, [FIXTURE_P1])
    df = scraper.scrape_one_page(1)

    affiliations = set(df["所属"].dropna().unique())
    assert "栗東" in affiliations
    assert "美浦" in affiliations


# ---------------------------------------------------------------------------
# 正常系: 厩舎IDの形式
# ---------------------------------------------------------------------------
def test_trainer_id_format() -> None:
    """厩舎IDが5桁の数字文字列であること（NaN以外）"""
    scraper = create_scraper_with_mock(YEAR, 1, [FIXTURE_P1])
    df = scraper.scrape_one_page(1)

    for trainer_id in df["厩舎ID"].dropna():
        assert isinstance(trainer_id, str), f"厩舎IDが文字列でない: {trainer_id}"
        assert len(trainer_id) == 5, f"厩舎IDが5桁でない: {trainer_id}"
        assert trainer_id.isdigit(), f"厩舎IDが数字でない: {trainer_id}"


# ---------------------------------------------------------------------------
# 正常系: 馬主IDの形式
# ---------------------------------------------------------------------------
def test_owner_id_format() -> None:
    """馬主IDが6桁の数字文字列であること（NaN以外）"""
    scraper = create_scraper_with_mock(YEAR, 1, [FIXTURE_P1])
    df = scraper.scrape_one_page(1)

    for owner_id in df["馬主ID"].dropna():
        assert isinstance(owner_id, str), f"馬主IDが文字列でない: {owner_id}"
        assert len(owner_id) == 6, f"馬主IDが6桁でない: {owner_id}"
        assert owner_id.isdigit(), f"馬主IDが数字でない: {owner_id}"


# ---------------------------------------------------------------------------
# 正常系: 生産者IDの形式
# ---------------------------------------------------------------------------
def test_breeder_id_format() -> None:
    """生産者IDが6桁の数字文字列であること（NaN以外）"""
    scraper = create_scraper_with_mock(YEAR, 1, [FIXTURE_P1])
    df = scraper.scrape_one_page(1)

    for breeder_id in df["生産者ID"].dropna():
        assert isinstance(breeder_id, str), f"生産者IDが文字列でない: {breeder_id}"
        assert len(breeder_id) == 6, f"生産者IDが6桁でない: {breeder_id}"
        assert breeder_id.isdigit(), f"生産者IDが数字でない: {breeder_id}"


# ---------------------------------------------------------------------------
# 正常系: 総賞金の検証
# ---------------------------------------------------------------------------
def test_prize_money_is_non_negative_int() -> None:
    """総賞金(万円)が0以上のintであること"""
    scraper = create_scraper_with_mock(YEAR, 1, [FIXTURE_P1])
    df = scraper.scrape_one_page(1)

    assert df["総賞金(万円)"].dtype in (np.int64, np.int32, int)
    assert (df["総賞金(万円)"] >= 0).all()


def test_prize_money_has_positive_values() -> None:
    """1ページ目に賞金が0より大きい馬が存在すること"""
    scraper = create_scraper_with_mock(YEAR, 1, [FIXTURE_P1])
    df = scraper.scrape_one_page(1)

    assert (df["総賞金(万円)"] > 0).any()


# ---------------------------------------------------------------------------
# 正常系: 具体的な値の検証
# ---------------------------------------------------------------------------
EXPECTED_VALUES: list[dict[str, Any]] = [
    # ミュージアムマイル（1ページ目の先頭）
    {
        "fixture": FIXTURE_P1,
        "馬ID": "2022105081",
        "馬名": "ミュージアムマイル",
        "性別": "牡",
        "所属": "栗東",
        "厩舎": "高柳大輔",
        "厩舎ID": "01159",
        "馬主ID": "226800",
        "生産者ID": "373126",
    },
]


@pytest.mark.parametrize(
    "expected",
    EXPECTED_VALUES,
    ids=[e["馬ID"] for e in EXPECTED_VALUES],
)
def test_expected_specific_values(expected: dict[str, Any]) -> None:
    """代表的な馬の具体的な値を検証する"""
    fixture = expected["fixture"]
    scraper = create_scraper_with_mock(YEAR, 1, [fixture])
    df = scraper.scrape_one_page(1)

    target_id = expected["馬ID"]
    matched = df[df["馬ID"] == target_id]
    assert len(matched) == 1, f"馬ID {target_id} が見つからないか複数存在する"

    row = matched.iloc[0]
    for key, value in expected.items():
        if key == "fixture":
            continue
        actual = row[key]
        assert actual == value, f"{key}: {actual} != {value}"


# ---------------------------------------------------------------------------
# 正常系: 複数ページの全馬取得
# ---------------------------------------------------------------------------
def test_get_all_horse_info_multiple_pages() -> None:
    """複数ページの場合、全ページ分のデータが結合されること"""
    scraper = create_scraper_with_mock(YEAR, 2, [FIXTURE_P1, FIXTURE_P80])
    df = scraper.get_all_horse_info()

    assert len(df) == 100 + 75
    assert list(df.columns) == HORSE_INFO_COLUMNS
    # インデックスがリセットされていること
    assert list(df.index) == list(range(175))


# ---------------------------------------------------------------------------
# 正常系: デビュー前の馬（厩舎ID/所属/厩舎がNaN）
# ---------------------------------------------------------------------------
def test_debut_before_horse_has_nan_trainer_id() -> None:
    """デビュー前の馬は厩舎IDがNaNであること"""
    scraper = create_scraper_with_mock(YEAR, 1, [FIXTURE_P80])
    df = scraper.scrape_one_page(1)

    nan_trainer = df[df["厩舎ID"].isna()]
    assert len(nan_trainer) > 0, "最終ページにデビュー前の馬が存在するはず"


def test_debut_before_horse_has_nan_affiliation() -> None:
    """デビュー前の馬は所属がNaNであること"""
    scraper = create_scraper_with_mock(YEAR, 1, [FIXTURE_P80])
    df = scraper.scrape_one_page(1)

    nan_affiliation = df[df["所属"].isna()]
    assert len(nan_affiliation) > 0, "最終ページにデビュー前の馬が存在するはず"


# ---------------------------------------------------------------------------
# 正常系: 性の値
# ---------------------------------------------------------------------------
def test_sex_values() -> None:
    """性別が牡/牝/セのいずれかであること"""
    scraper = create_scraper_with_mock(YEAR, 1, [FIXTURE_P1])
    df = scraper.scrape_one_page(1)

    valid = {"牡", "牝", "セ"}
    actual = set(df["性別"].dropna().unique())
    assert actual <= valid, f"不正な性別: {actual - valid}"


# ---------------------------------------------------------------------------
# 正常系: 父/母/母父の値
# ---------------------------------------------------------------------------
def test_sire_dam_broodmare_sire_not_all_nan() -> None:
    """父/母/母父が全てNaNではないこと"""
    scraper = create_scraper_with_mock(YEAR, 1, [FIXTURE_P1])
    df = scraper.scrape_one_page(1)

    assert df["父"].notna().any(), "父が全てNaN"
    assert df["母"].notna().any(), "母が全てNaN"
    assert df["母父"].notna().any(), "母父が全てNaN"


# ---------------------------------------------------------------------------
# 正常系: max_page_numの境界値
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("birth_num_text", "expected_pages"),
    [
        ("100", 1),
        ("0", 0),
        ("101", 2),
    ],
)
def test_max_page_num_boundary_values(birth_num_text: str, expected_pages: int) -> None:
    """max_page_numが境界値で正しく計算されること"""
    pager_html = f"""
    <html>
        <body>
            <div class="pager">該当馬: {birth_num_text}頭</div>
        </body>
    </html>
    """

    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.text = pager_html
    mock_response.encoding = "EUC-JP"
    mock_session.get.return_value = mock_response

    scraper = HorseInfoScraper(YEAR, session=mock_session)

    assert scraper.max_page_num == expected_pages


# ---------------------------------------------------------------------------
# 準正常系: テーブルが見つからない場合
# ---------------------------------------------------------------------------
def test_no_table_raises_parse_error() -> None:
    """HTMLにrace_table_01が存在しない場合にParseErrorが発生すること"""
    no_table_html = (
        "<html><head><title>Test</title></head><body>" "<div>no table here</div>" "</body></html>"
    )

    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.text = no_table_html
    mock_response.encoding = "EUC-JP"
    mock_session.get.return_value = mock_response

    with patch.object(HorseInfoScraper, "_scrape_max_page_num", return_value=1):
        scraper = HorseInfoScraper(YEAR, session=mock_session)

    with pytest.raises(ParseError, match="テーブルが見つかりません"):
        scraper.scrape_one_page(1)


def test_insufficient_td_columns_raises_parse_error() -> None:
    """行内のtd列数が不足している場合にParseErrorが発生すること"""
    insufficient_columns_html = """
    <html>
        <body>
            <table class="nk_tb_common race_table_01">
                <tr>
                    <th>順位</th><th>馬名</th><th>性</th><th>厩舎</th><th>父</th><th>母</th>
                    <th>母父</th><th>馬主</th><th>生産者</th><th>総賞金(万円)</th>
                </tr>
                <tr>
                    <td>1</td><td><a href="/horse/2022105081/">ミュージアムマイル</a></td>
                    <td>牡</td><td>[西]高柳大輔</td><td>父A</td><td>母A</td>
                    <td>母父A</td><td><a href="/owner/226800/">馬主A</a></td>
                    <td><a href="/breeder/373126/">生産者A</a></td>
                </tr>
            </table>
        </body>
    </html>
    """

    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.text = insufficient_columns_html
    mock_response.encoding = "EUC-JP"
    mock_session.get.return_value = mock_response

    with patch.object(HorseInfoScraper, "_scrape_max_page_num", return_value=1):
        scraper = HorseInfoScraper(YEAR, session=mock_session)

    with pytest.raises(ParseError, match="テーブル列数が不足しています"):
        scraper.scrape_one_page(1)
