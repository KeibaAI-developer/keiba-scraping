"""scrape_race_infoの単体テスト

HTMLフィクスチャからBeautifulSoupを生成し、パブリック関数scrape_race_infoの出力を検証する。
"""

import glob
import os
import re
from datetime import date
from typing import Any

import numpy as np
import pandas as pd
import pytest
from bs4 import BeautifulSoup

from scraping.config import RACE_INFO_COLUMNS
from scraping.race_info import scrape_race_info

# フィクスチャHTMLのディレクトリ
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "fixtures", "html")


# ---------------------------------------------------------------------------
# ヘルパー関数
# ---------------------------------------------------------------------------
def _load_soup(fixture_filename: str) -> BeautifulSoup:
    """フィクスチャHTMLを読み込んでBeautifulSoupを返す

    Args:
        fixture_filename (str): フィクスチャファイル名（例: result_202505021211.html）

    Returns:
        BeautifulSoup: パース済みのBeautifulSoupオブジェクト
    """
    filepath = os.path.join(FIXTURES_DIR, fixture_filename)
    with open(filepath, "r", encoding="utf-8") as f:
        html = f.read()
    return BeautifulSoup(html, "html.parser")


def _load_soup_with_replacements(
    fixture_filename: str, replacements: dict[str, str]
) -> BeautifulSoup:
    """フィクスチャHTMLを読み込み、文字列置換してBeautifulSoupを返す

    Args:
        fixture_filename (str): フィクスチャファイル名
        replacements (dict[str, str]): {置換前: 置換後} の辞書

    Returns:
        BeautifulSoup: 置換済みHTMLのBeautifulSoupオブジェクト
    """
    filepath = os.path.join(FIXTURES_DIR, fixture_filename)
    with open(filepath, "r", encoding="utf-8") as f:
        html = f.read()
    for old, new in replacements.items():
        html = html.replace(old, new)
    return BeautifulSoup(html, "html.parser")


def _collect_fixture_params() -> list[tuple[str, str, str]]:
    """フィクスチャHTMLから(page_type, race_id, fixture_filename)のリストを生成する

    Returns:
        list[tuple[str, str, str]]: テストパラメータのリスト
    """
    params: list[tuple[str, str, str]] = []
    fixture_dir = os.path.normpath(FIXTURES_DIR)
    for filepath in sorted(glob.glob(os.path.join(fixture_dir, "*.html"))):
        basename = os.path.basename(filepath)
        # entry_202505021211.html -> ("entry", "202505021211")
        parts = basename.replace(".html", "").split("_", 1)
        if len(parts) == 2:
            page_type = parts[0]
            race_id = parts[1]
            params.append((page_type, race_id, basename))
    return params


FIXTURE_PARAMS = _collect_fixture_params()


# ---------------------------------------------------------------------------
# 正常系
# ---------------------------------------------------------------------------


# 全フィクスチャに対するカラム構成・行数テスト
@pytest.mark.parametrize(
    "page_type, race_id, fixture_filename",
    FIXTURE_PARAMS,
    ids=[f"{p[0]}_{p[1]}" for p in FIXTURE_PARAMS],
)
def test_scrape_race_info_returns_valid_dataframe(
    page_type: str, race_id: str, fixture_filename: str
) -> None:
    """全フィクスチャでDataFrameのカラムと行数が正しいことを確認する"""
    soup = _load_soup(fixture_filename)
    result = scrape_race_info(soup, race_id)

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 1
    assert list(result.columns) == RACE_INFO_COLUMNS


@pytest.mark.parametrize(
    "page_type, race_id, fixture_filename",
    FIXTURE_PARAMS,
    ids=[f"{p[0]}_{p[1]}" for p in FIXTURE_PARAMS],
)
def test_scrape_race_info_race_id_matches(
    page_type: str, race_id: str, fixture_filename: str
) -> None:
    """レースIDが入力と一致することを確認する"""
    soup = _load_soup(fixture_filename)
    result = scrape_race_info(soup, race_id)

    assert result["レースID"].iloc[0] == race_id


@pytest.mark.parametrize(
    "page_type, race_id, fixture_filename",
    FIXTURE_PARAMS,
    ids=[f"{p[0]}_{p[1]}" for p in FIXTURE_PARAMS],
)
def test_scrape_race_info_has_non_empty_values(
    page_type: str, race_id: str, fixture_filename: str
) -> None:
    """必須項目（レース名、芝ダ、距離、競馬場）が空でないことを確認する"""
    soup = _load_soup(fixture_filename)
    result = scrape_race_info(soup, race_id)
    row = result.iloc[0]

    assert row["レース名"] != ""
    assert row["芝ダ"] in ["芝", "ダ", "障"]
    assert isinstance(row["距離"], (int, np.integer))
    assert row["距離"] > 0
    assert row["競馬場"] != ""
    assert row["競走記号"] != ""
    assert isinstance(row["頭数"], (int, np.integer))
    assert row["頭数"] > 0
    assert isinstance(row["1着賞金"], (int, np.integer))
    assert row["1着賞金"] > 0
    assert isinstance(row["日付"], date)
    assert row["曜日"] in ["月", "火", "水", "木", "金", "土", "日"]
    assert isinstance(row["発走時刻"], str)
    assert re.fullmatch(r"\d{1,2}:\d{2}", row["発走時刻"])


# 代表的なレースの具体的な値を検証
EXPECTED_VALUES: list[dict[str, Any]] = [
    {
        "race_id": "202505021211",
        "page_type": "result",
        "レース名": "日本ダービー",
        "日付": date(2025, 6, 1),
        "曜日": "日",
        "発走時刻": "15:40",
        "芝ダ": "芝",
        "距離": 2400,
        "左右": "左",
        "コース": "C",
        "競馬場": "東京",
        "天候": "晴",
        "馬場": "良",
        "回": 2,
        "開催日": 12,
        "競争条件": "オープン",
        "グレード": "G1",
        "競走記号": "(国際) 牡・牝(指)",
        "重量種別": "馬齢",
        "頭数": 18,
        "1着賞金": 30000,
        "2着賞金": 12000,
        "3着賞金": 7500,
        "4着賞金": 4500,
        "5着賞金": 3000,
    },
    {
        "race_id": "202306030111",
        "page_type": "result",
        "レース名": "日経賞",
        "日付": date(2023, 3, 25),
        "曜日": "土",
        "発走時刻": "15:45",
        "芝ダ": "芝",
        "距離": 2500,
        "左右": "右",
        "コース": "A",
        "競馬場": "中山",
        "天候": "曇",
        "馬場": "不",
        "回": 3,
        "開催日": 1,
        "競争条件": "オープン",
        "グレード": "G2",
        "競走記号": "(国際)(指)",
        "重量種別": "別定",
        "頭数": 12,
        "1着賞金": 6700,
        "5着賞金": 670,
    },
    {
        "race_id": "202407020811",
        "page_type": "result",
        "レース名": "小倉2歳S",
        "芝ダ": "芝",
        "距離": 1200,
        "左右": "左",
        "コース": "A",
        "競馬場": "中京",
        "天候": "曇",
        "馬場": "重",
        "競争条件": "オープン",
        "グレード": "G3",
        "競走記号": "(国際)(特指)",
        "重量種別": "馬齢",
    },
    {
        "race_id": "202508030111",
        "page_type": "result",
        "レース名": "オパールS",
        "日付": date(2025, 10, 4),
        "曜日": "土",
        "発走時刻": "15:30",
        "芝ダ": "芝",
        "距離": 1200,
        "競馬場": "京都",
        "馬場": "重",
        "競争条件": "オープン",
        "グレード": "L",
        "競走記号": "(国際)(特指)",
    },
    {
        "race_id": "202506040609",
        "page_type": "result",
        "レース名": "カンナS",
        "日付": date(2025, 9, 20),
        "曜日": "土",
        "発走時刻": "14:31",
        "芝ダ": "芝",
        "距離": 1200,
        "競馬場": "中山",
        "競争条件": "オープン",
        "グレード": "OP",
        "競走記号": "(国際)(特指)",
    },
    {
        "race_id": "202501020310",
        "page_type": "result",
        "レース名": "千歳特別",
        "芝ダ": "ダ",
        "距離": 1700,
        "競馬場": "札幌",
        "馬場": "重",
        "競争種別": "サラ系３歳以上",
        "競争条件": "２勝クラス",
        "グレード": "",
        "競走記号": "(混)[指]",
        "重量種別": "定量",
    },
    {
        "race_id": "202406050710",
        "page_type": "result",
        "レース名": "中山大障害",
        "芝ダ": "障",
        "距離": 4100,
        "競馬場": "中山",
        "競争条件": "オープン",
        "グレード": "JG1",
        "競走記号": "(国際)",
        "重量種別": "定量",
        "頭数": 9,
        "1着賞金": 6600,
    },
    {
        "race_id": "202504020407",
        "page_type": "result",
        "レース名": "アイビスSD",
        "芝ダ": "芝",
        "距離": 1000,
        "左右": "直",
        "コース": "A",
        "競馬場": "新潟",
        "競争条件": "オープン",
        "グレード": "G3",
        "競走記号": "(国際)(特指)",
        "重量種別": "別定",
    },
    {
        "race_id": "202507030402",
        "page_type": "result",
        "レース名": "2歳新馬",
        "芝ダ": "ダ",
        "距離": 1800,
        "競馬場": "中京",
        "競争種別": "サラ系２歳",
        "競争条件": "新馬",
        "グレード": "",
        "競走記号": "(混)[指]",
        "重量種別": "馬齢",
    },
    {
        "race_id": "202505020607",
        "page_type": "result",
        "レース名": "4歳以上2勝クラス",
        "芝ダ": "芝",
        "距離": 2000,
        "競馬場": "東京",
        "競争種別": "サラ系４歳以上",
        "競争条件": "２勝クラス",
        "グレード": "",
        "競走記号": "(混)(特指)",
        "頭数": 5,
        "1着賞金": 1140,
    },
]


@pytest.mark.parametrize(
    "expected",
    EXPECTED_VALUES,
    ids=[f"{e['page_type']}_{e['race_id']}_{e['レース名']}" for e in EXPECTED_VALUES],
)
def test_scrape_race_info_expected_values(expected: dict[str, Any]) -> None:
    """代表的なレースの具体的な値が正しいことを確認する"""
    race_id = expected["race_id"]
    page_type = expected["page_type"]
    fixture_filename = f"{page_type}_{race_id}.html"

    soup = _load_soup(fixture_filename)
    result = scrape_race_info(soup, race_id)
    row = result.iloc[0]

    # expected辞書からrace_id, page_typeを除いたキーを検証
    for key, expected_value in expected.items():
        if key in ("race_id", "page_type"):
            continue
        actual = row[key]
        assert actual == expected_value, (
            f"{key}: expected={expected_value!r}, actual={actual!r} " f"(race_id={race_id})"
        )


# 出馬表と結果ページで同じレースの出力が一致することを確認
BOTH_PAGE_RACE_IDS = [
    "202505021211",  # 日本ダービー2025
    "202306030111",  # 日経賞2023
    "202407020811",  # 小倉2歳S2024
]


@pytest.mark.parametrize("race_id", BOTH_PAGE_RACE_IDS)
def test_scrape_race_info_entry_and_result_match(race_id: str) -> None:
    """出馬表ページと結果ページで同じレース情報が抽出されることを確認する"""
    entry_soup = _load_soup(f"entry_{race_id}.html")
    result_soup = _load_soup(f"result_{race_id}.html")

    entry_df = scrape_race_info(entry_soup, race_id)
    result_df = scrape_race_info(result_soup, race_id)

    pd.testing.assert_frame_equal(entry_df, result_df)


# 準正常系: HTML構造エラー
def test_scrape_race_info_parse_error_on_missing_datelist() -> None:
    """RaceList_DateListが存在しないHTMLでParseErrorが発生することを確認する"""
    from scraping.exceptions import ParseError

    soup = BeautifulSoup("<html><body></body></html>", "html.parser")
    with pytest.raises(ParseError, match="RaceList_DateListが見つかりませんでした。"):
        scrape_race_info(soup, "000000000000")


def test_scrape_race_info_parse_error_on_missing_race_item() -> None:
    """RaceList_Item02が存在しないHTMLでParseErrorが発生することを確認する"""
    from scraping.exceptions import ParseError

    # RaceList_DateListは存在するがRaceList_Item02が存在しない
    html = """
    <html><body>
        <dl id="RaceList_DateList">
            <dd class="Active">
                <a href="?kaisai_date=20250601" title="6/1(日)">
                    <span class="Sun">(日)</span>
                </a>
            </dd>
        </dl>
    </body></html>
    """
    soup = BeautifulSoup(html, "html.parser")
    with pytest.raises(ParseError, match="RaceList_Item02が見つかりませんでした"):
        scrape_race_info(soup, "202505021211")


def test_scrape_race_info_parse_error_on_missing_active_date() -> None:
    """Active日付が存在しないHTMLでParseErrorが発生することを確認する"""
    from scraping.exceptions import ParseError

    html = """
    <html><body>
        <dl id="RaceList_DateList">
            <dd><a href="?kaisai_date=20250601">6/1</a></dd>
        </dl>
        <div class="RaceList_Item02">発走15:40</div>
    </body></html>
    """
    soup = BeautifulSoup(html, "html.parser")
    with pytest.raises(ParseError, match="Active日付が見つかりませんでした。"):
        scrape_race_info(soup, "202505021211")


def test_scrape_race_info_parse_error_on_missing_kaisai_date() -> None:
    """kaisai_dateパラメータが存在しないHTMLでParseErrorが発生することを確認する"""
    from scraping.exceptions import ParseError

    html = """
    <html><body>
        <dl id="RaceList_DateList">
            <dd class="Active">
                <a href="?invalid_param=20250601" title="6/1(日)">
                    <span class="Sun">(日)</span>
                </a>
            </dd>
        </dl>
        <div class="RaceList_Item02">発走15:40</div>
    </body></html>
    """
    soup = BeautifulSoup(html, "html.parser")
    with pytest.raises(ParseError, match="kaisai_dateパラメータが見つかりませんでした。"):
        scrape_race_info(soup, "202505021211")


# 準正常系: バリデーションエラー
def test_scrape_race_info_validation_error_on_invalid_race_id() -> None:
    """レースIDが12桁でない場合にParseErrorが発生することを確認する"""
    from scraping.exceptions import ParseError

    soup = _load_soup("result_202505021211.html")
    with pytest.raises(ParseError, match="レースIDが12桁の数字ではありません"):
        scrape_race_info(soup, "12345")  # 5桁のID


def test_scrape_race_info_validation_error_on_invalid_day_of_week() -> None:
    """曜日が不正な場合にParseErrorが発生することを確認する"""
    from scraping.exceptions import ParseError

    # フィクスチャHTMLのtitle属性の曜日を不正な値に置換
    soup = _load_soup_with_replacements(
        "result_202505021211.html",
        {"6月1日(日)": "6月1日(X)", "(日)</span>": "(X)</span>"},
    )
    with pytest.raises(ParseError, match="曜日が不正です"):
        scrape_race_info(soup, "202505021211")


def test_scrape_race_info_validation_error_on_invalid_start_time() -> None:
    """発走時刻が不正なフォーマットの場合にParseErrorが発生することを確認する"""
    from scraping.exceptions import ParseError

    # フィクスチャHTMLの発走時刻を不正な値に置換
    soup = _load_soup_with_replacements(
        "result_202505021211.html",
        {"15:40発走": "abc発走"},
    )
    with pytest.raises(ParseError, match="発走時刻がHH:MM形式ではありません"):
        scrape_race_info(soup, "202505021211")


def test_scrape_race_info_validation_error_on_invalid_weather() -> None:
    """天候が不正な値の場合にParseErrorが発生することを確認する"""
    from scraping.exceptions import ParseError

    # フィクスチャHTMLの天候を不正な値に置換
    soup = _load_soup_with_replacements(
        "result_202505021211.html",
        {"天候:晴": "天候:台風"},
    )
    with pytest.raises(ParseError, match="天候が不正です"):
        scrape_race_info(soup, "202505021211")


def test_scrape_race_info_validation_error_on_invalid_track_condition() -> None:
    """馬場が不正な値の場合にParseErrorが発生することを確認する"""
    from scraping.exceptions import ParseError

    # フィクスチャHTMLの馬場を不正な値に置換
    soup = _load_soup_with_replacements(
        "result_202505021211.html",
        {"馬場:良": "馬場:最悪"},
    )
    with pytest.raises(ParseError, match="馬場が不正です"):
        scrape_race_info(soup, "202505021211")
