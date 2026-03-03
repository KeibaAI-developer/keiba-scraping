"""RaceListScraper.scrape_one_page()の単体テスト

requestsをモックし、フィクスチャHTMLを返すようにしてテストする。
レース一覧テーブルの取得・26カラム構成・主要値を検証する。
"""

import datetime
from typing import Any

import numpy as np
import pandas as pd
import pytest

from scraping.config import RACE_LIST_COLUMNS

from .conftest import create_scraper_with_mock

# ---------------------------------------------------------------------------
# テスト用定数
# ---------------------------------------------------------------------------
FIXTURE_P1 = "race_list_2026_p1.html"
YEAR = 2026


# ---------------------------------------------------------------------------
# 正常系: カラム構成の確認
# ---------------------------------------------------------------------------
def test_columns_match_race_list_columns() -> None:
    """カラム構成がRACE_LIST_COLUMNSと一致すること"""
    scraper = create_scraper_with_mock(YEAR, 1, [FIXTURE_P1])
    df = scraper.scrape_one_page(1)

    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == RACE_LIST_COLUMNS


def test_column_count_is_26() -> None:
    """カラム数が26であること"""
    scraper = create_scraper_with_mock(YEAR, 1, [FIXTURE_P1])
    df = scraper.scrape_one_page(1)

    assert len(df.columns) == 26


# ---------------------------------------------------------------------------
# 正常系: 行数の確認
# ---------------------------------------------------------------------------
def test_row_count_is_100() -> None:
    """1ページ目は100行であること"""
    scraper = create_scraper_with_mock(YEAR, 1, [FIXTURE_P1])
    df = scraper.scrape_one_page(1)

    assert len(df) == 100


# ---------------------------------------------------------------------------
# 正常系: レースIDの形式
# ---------------------------------------------------------------------------
def test_race_id_format() -> None:
    """レースIDが12桁の数字文字列であること"""
    scraper = create_scraper_with_mock(YEAR, 1, [FIXTURE_P1])
    df = scraper.scrape_one_page(1)

    for race_id in df["レースID"]:
        assert isinstance(race_id, str), f"レースIDが文字列でない: {race_id}"
        assert len(race_id) == 12, f"レースIDが12桁でない: {race_id}"
        assert race_id.isdigit(), f"レースIDが数字でない: {race_id}"


# ---------------------------------------------------------------------------
# 正常系: 日付の型
# ---------------------------------------------------------------------------
def test_date_is_datetime_date() -> None:
    """日付がdatetime.date型であること"""
    scraper = create_scraper_with_mock(YEAR, 1, [FIXTURE_P1])
    df = scraper.scrape_one_page(1)

    for date_val in df["日付"]:
        assert isinstance(date_val, datetime.date), f"日付がdate型でない: {date_val}"


# ---------------------------------------------------------------------------
# 正常系: 競馬場の値
# ---------------------------------------------------------------------------
def test_keibajo_values() -> None:
    """競馬場が中央10場のいずれかであること"""
    valid_keibajo = {"札幌", "函館", "福島", "新潟", "東京", "中山", "中京", "京都", "阪神", "小倉"}
    scraper = create_scraper_with_mock(YEAR, 1, [FIXTURE_P1])
    df = scraper.scrape_one_page(1)

    actual = set(df["競馬場"].unique())
    assert actual <= valid_keibajo, f"不正な競馬場: {actual - valid_keibajo}"


# ---------------------------------------------------------------------------
# 正常系: 回・開催日の型
# ---------------------------------------------------------------------------
def test_kai_is_int() -> None:
    """回がint型であること"""
    scraper = create_scraper_with_mock(YEAR, 1, [FIXTURE_P1])
    df = scraper.scrape_one_page(1)

    for kai in df["回"]:
        assert isinstance(kai, (int, np.integer)), f"回がint型でない: {kai}"


def test_kaisai_day_is_int() -> None:
    """開催日がint型であること"""
    scraper = create_scraper_with_mock(YEAR, 1, [FIXTURE_P1])
    df = scraper.scrape_one_page(1)

    for day in df["開催日"]:
        assert isinstance(day, (int, np.integer)), f"開催日がint型でない: {day}"


# ---------------------------------------------------------------------------
# 正常系: 天候の値
# ---------------------------------------------------------------------------
def test_weather_values() -> None:
    """天候が空文字でないこと"""
    scraper = create_scraper_with_mock(YEAR, 1, [FIXTURE_P1])
    df = scraper.scrape_one_page(1)

    for weather in df["天候"]:
        assert isinstance(weather, str), f"天候が文字列でない: {weather}"
        assert len(weather) > 0, "天候が空文字"


# ---------------------------------------------------------------------------
# 正常系: Rの値
# ---------------------------------------------------------------------------
def test_r_values() -> None:
    """Rが1〜12の整数であること"""
    scraper = create_scraper_with_mock(YEAR, 1, [FIXTURE_P1])
    df = scraper.scrape_one_page(1)

    for r_val in df["R"]:
        assert isinstance(r_val, (int, np.integer)), f"Rがint型でない: {r_val}"
        assert 1 <= r_val <= 12, f"Rが範囲外: {r_val}"


# ---------------------------------------------------------------------------
# 正常系: 芝ダの値
# ---------------------------------------------------------------------------
def test_turf_dirt_values() -> None:
    """芝ダが"芝","ダ","障"のいずれかであること"""
    valid = {"芝", "ダ", "障"}
    scraper = create_scraper_with_mock(YEAR, 1, [FIXTURE_P1])
    df = scraper.scrape_one_page(1)

    actual = set(df["芝ダ"].unique())
    assert actual <= valid, f"不正な芝ダ: {actual - valid}"


# ---------------------------------------------------------------------------
# 正常系: 距離の型と範囲
# ---------------------------------------------------------------------------
def test_distance_is_positive_int() -> None:
    """距離が正のintであること"""
    scraper = create_scraper_with_mock(YEAR, 1, [FIXTURE_P1])
    df = scraper.scrape_one_page(1)

    for dist in df["距離"]:
        assert isinstance(dist, (int, np.integer)), f"距離がint型でない: {dist}"
        assert dist > 0, f"距離が0以下: {dist}"


# ---------------------------------------------------------------------------
# 正常系: 頭数の型と範囲
# ---------------------------------------------------------------------------
def test_num_runners_is_positive_int() -> None:
    """頭数が正のintであること"""
    scraper = create_scraper_with_mock(YEAR, 1, [FIXTURE_P1])
    df = scraper.scrape_one_page(1)

    for num in df["頭数"]:
        assert isinstance(num, (int, np.integer)), f"頭数がint型でない: {num}"
        assert num > 0, f"頭数が0以下: {num}"


# ---------------------------------------------------------------------------
# 正常系: 馬場の値
# ---------------------------------------------------------------------------
def test_baba_values() -> None:
    """馬場が"良","稍","重","不"のいずれかであること"""
    valid = {"良", "稍", "重", "不"}
    scraper = create_scraper_with_mock(YEAR, 1, [FIXTURE_P1])
    df = scraper.scrape_one_page(1)

    actual = set(df["馬場"].unique())
    assert actual <= valid, f"不正な馬場: {actual - valid}"


# ---------------------------------------------------------------------------
# 正常系: タイムの形式
# ---------------------------------------------------------------------------
def test_time_format() -> None:
    """タイムが非空文字列であること"""
    scraper = create_scraper_with_mock(YEAR, 1, [FIXTURE_P1])
    df = scraper.scrape_one_page(1)

    for time_val in df["タイム"]:
        assert isinstance(time_val, str), f"タイムが文字列でない: {time_val}"
        assert len(time_val) > 0, "タイムが空文字"


# ---------------------------------------------------------------------------
# 正常系: ペース（レース前3F・レース後3F）の型
# ---------------------------------------------------------------------------
def test_pace_is_float() -> None:
    """レース前3F・レース後3Fがfloat型であること（NaN以外）"""
    scraper = create_scraper_with_mock(YEAR, 1, [FIXTURE_P1])
    df = scraper.scrape_one_page(1)

    for val in df["レース前3F"].dropna():
        assert isinstance(val, (float, np.floating)), f"レース前3Fがfloat型でない: {val}"
    for val in df["レース後3F"].dropna():
        assert isinstance(val, (float, np.floating)), f"レース後3Fがfloat型でない: {val}"


# ---------------------------------------------------------------------------
# 正常系: 勝ち馬IDの形式
# ---------------------------------------------------------------------------
def test_winner_id_format() -> None:
    """勝ち馬IDが10桁の数字文字列であること"""
    scraper = create_scraper_with_mock(YEAR, 1, [FIXTURE_P1])
    df = scraper.scrape_one_page(1)

    for horse_id in df["勝ち馬ID"].dropna():
        assert isinstance(horse_id, str), f"勝ち馬IDが文字列でない: {horse_id}"
        assert len(horse_id) == 10, f"勝ち馬IDが10桁でない: {horse_id}"
        assert horse_id.isdigit(), f"勝ち馬IDが数字でない: {horse_id}"


# ---------------------------------------------------------------------------
# 正常系: 騎手IDの形式
# ---------------------------------------------------------------------------
def test_jockey_id_format() -> None:
    """騎手IDが5桁の数字文字列であること"""
    scraper = create_scraper_with_mock(YEAR, 1, [FIXTURE_P1])
    df = scraper.scrape_one_page(1)

    for jockey_id in df["騎手ID"].dropna():
        assert isinstance(jockey_id, str), f"騎手IDが文字列でない: {jockey_id}"
        assert len(jockey_id) == 5, f"騎手IDが5桁でない: {jockey_id}"
        assert jockey_id.isdigit(), f"騎手IDが数字でない: {jockey_id}"


# ---------------------------------------------------------------------------
# 正常系: 所属の値
# ---------------------------------------------------------------------------
def test_affiliation_values() -> None:
    """所属が美浦/栗東/地方/海外/空文字のいずれかであること"""
    valid = {"美浦", "栗東", "地方", "海外", ""}
    scraper = create_scraper_with_mock(YEAR, 1, [FIXTURE_P1])
    df = scraper.scrape_one_page(1)

    actual = set(df["所属"].dropna().unique())
    assert actual <= valid, f"不正な所属: {actual - valid}"


# ---------------------------------------------------------------------------
# 正常系: 厩舎IDの形式
# ---------------------------------------------------------------------------
def test_trainer_id_format() -> None:
    """厩舎IDが5桁の数字文字列であること"""
    scraper = create_scraper_with_mock(YEAR, 1, [FIXTURE_P1])
    df = scraper.scrape_one_page(1)

    for trainer_id in df["厩舎ID"].dropna():
        assert isinstance(trainer_id, str), f"厩舎IDが文字列でない: {trainer_id}"
        assert len(trainer_id) == 5, f"厩舎IDが5桁でない: {trainer_id}"
        assert trainer_id.isdigit(), f"厩舎IDが数字でない: {trainer_id}"


# ---------------------------------------------------------------------------
# 正常系: 2着馬ID・3着馬IDの形式
# ---------------------------------------------------------------------------
def test_second_horse_id_format() -> None:
    """2着馬IDが10桁の数字文字列であること"""
    scraper = create_scraper_with_mock(YEAR, 1, [FIXTURE_P1])
    df = scraper.scrape_one_page(1)

    for horse_id in df["2着馬ID"].dropna():
        assert isinstance(horse_id, str), f"2着馬IDが文字列でない: {horse_id}"
        assert len(horse_id) == 10, f"2着馬IDが10桁でない: {horse_id}"
        assert horse_id.isdigit(), f"2着馬IDが数字でない: {horse_id}"


def test_third_horse_id_format() -> None:
    """3着馬IDが10桁の数字文字列であること"""
    scraper = create_scraper_with_mock(YEAR, 1, [FIXTURE_P1])
    df = scraper.scrape_one_page(1)

    for horse_id in df["3着馬ID"].dropna():
        assert isinstance(horse_id, str), f"3着馬IDが文字列でない: {horse_id}"
        assert len(horse_id) == 10, f"3着馬IDが10桁でない: {horse_id}"
        assert horse_id.isdigit(), f"3着馬IDが数字でない: {horse_id}"


# ---------------------------------------------------------------------------
# 正常系: 具体的な値の検証（1行目）
# ---------------------------------------------------------------------------
EXPECTED_FIRST_ROW: dict[str, Any] = {
    "レースID": "202606020201",
    "日付": datetime.date(2026, 3, 1),
    "競馬場": "中山",
    "回": 2,
    "開催日": 2,
    "天候": "晴",
    "R": 1,
    "レース名": "3歳未勝利",
    "芝ダ": "ダ",
    "距離": 1800,
    "頭数": 16,
    "馬場": "稍",
    "タイム": "1:55.2",
    "勝ち馬": "ピュアエンブレム",
    "勝ち馬ID": "2023107171",
    "騎手": "岩田康誠",
    "騎手ID": "05203",
    "所属": "美浦",
    "厩舎": "小手川準",
    "厩舎ID": "01171",
    "2着馬": "サラサチャチャチャ",
    "2着馬ID": "2023102581",
    "3着馬": "ロジマギー",
    "3着馬ID": "2023107361",
}


@pytest.mark.parametrize(
    "column, expected",
    list(EXPECTED_FIRST_ROW.items()),
    ids=list(EXPECTED_FIRST_ROW.keys()),
)
def test_first_row_values(column: str, expected: Any) -> None:
    """1行目の各カラムが期待値と一致すること"""
    scraper = create_scraper_with_mock(YEAR, 1, [FIXTURE_P1])
    df = scraper.scrape_one_page(1)

    assert df[column].iloc[0] == expected, f"{column}: {df[column].iloc[0]} != {expected}"


# ---------------------------------------------------------------------------
# 正常系: ペースの具体値（1行目）
# ---------------------------------------------------------------------------
def test_first_row_pace_values() -> None:
    """1行目のレース前3F=36.7、レース後3F=40.5であること"""
    scraper = create_scraper_with_mock(YEAR, 1, [FIXTURE_P1])
    df = scraper.scrape_one_page(1)

    assert df["レース前3F"].iloc[0] == pytest.approx(36.7)
    assert df["レース後3F"].iloc[0] == pytest.approx(40.5)


# ---------------------------------------------------------------------------
# 正常系: 具体的な値の検証（最終行: 障害レース）
# ---------------------------------------------------------------------------
EXPECTED_LAST_ROW: dict[str, Any] = {
    "レースID": "202610011004",
    "競馬場": "小倉",
    "芝ダ": "障",
    "距離": 2860,
    "頭数": 12,
    "勝ち馬": "グラニットピーク",
    "勝ち馬ID": "2020103507",
}


@pytest.mark.parametrize(
    "column, expected",
    list(EXPECTED_LAST_ROW.items()),
    ids=list(EXPECTED_LAST_ROW.keys()),
)
def test_last_row_values(column: str, expected: Any) -> None:
    """最終行（障害レース）の各カラムが期待値と一致すること"""
    scraper = create_scraper_with_mock(YEAR, 1, [FIXTURE_P1])
    df = scraper.scrape_one_page(1)

    assert df[column].iloc[-1] == expected, f"{column}: {df[column].iloc[-1]} != {expected}"


# ---------------------------------------------------------------------------
# 正常系: 10行目（アクアマリンS、芝レース）
# ---------------------------------------------------------------------------
def test_row_10_aquamarine_stakes() -> None:
    """10行目のアクアマリンSが芝1200mの中山レースであること"""
    scraper = create_scraper_with_mock(YEAR, 1, [FIXTURE_P1])
    df = scraper.scrape_one_page(1)

    row = df.iloc[9]
    assert row["レースID"] == "202606020210"
    assert row["競馬場"] == "中山"
    assert row["芝ダ"] == "芝"
    assert row["距離"] == 1200
    assert row["R"] == 10
    assert row["勝ち馬"] == "ソーダーンライト"
