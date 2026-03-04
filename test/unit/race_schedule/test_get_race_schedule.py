"""RaceScheduleScraper.get_race_schedule()の単体テスト

Selenium WebDriverをモックし、フィクスチャHTMLを返すようにしてテストする。
レーススケジュールの取得・12カラム構成・主要値を検証する。
"""

import datetime
import re
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd

from scraping.config import RACE_SCHEDULE_COLUMNS
from scraping.race_schedule import RaceScheduleScraper

from .conftest import create_scraper_from_fixture

# ---------------------------------------------------------------------------
# テスト用定数
# ---------------------------------------------------------------------------
FIXTURE_20260301 = "race_schedule_20260301.html"
YEAR = 2026
MONTH = 3
DAY = 1


# ---------------------------------------------------------------------------
# 正常系: カラム構成の確認
# ---------------------------------------------------------------------------
def test_columns_match_race_schedule_columns() -> None:
    """カラム構成がRACE_SCHEDULE_COLUMNSと一致すること"""
    scraper = create_scraper_from_fixture(YEAR, MONTH, DAY, FIXTURE_20260301)
    df = scraper.get_race_schedule()

    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == RACE_SCHEDULE_COLUMNS


def test_column_count_is_12() -> None:
    """カラム数が12であること"""
    scraper = create_scraper_from_fixture(YEAR, MONTH, DAY, FIXTURE_20260301)
    df = scraper.get_race_schedule()

    assert len(df.columns) == 12


# ---------------------------------------------------------------------------
# 正常系: 行数の確認
# ---------------------------------------------------------------------------
def test_row_count_is_36() -> None:
    """2026年3月1日は3場開催（各12レース）で36行であること"""
    scraper = create_scraper_from_fixture(YEAR, MONTH, DAY, FIXTURE_20260301)
    df = scraper.get_race_schedule()

    assert len(df) == 36


# ---------------------------------------------------------------------------
# 正常系: レースIDの形式
# ---------------------------------------------------------------------------
def test_race_id_format() -> None:
    """レースIDが12桁の数字文字列であること"""
    scraper = create_scraper_from_fixture(YEAR, MONTH, DAY, FIXTURE_20260301)
    df = scraper.get_race_schedule()

    for race_id in df["レースID"]:
        assert isinstance(race_id, str), f"レースIDが文字列でない: {race_id}"
        assert len(race_id) == 12, f"レースIDが12桁でない: {race_id}"
        assert race_id.isdigit(), f"レースIDが数字でない: {race_id}"


def test_race_id_year_prefix() -> None:
    """レースIDが2026で始まること"""
    scraper = create_scraper_from_fixture(YEAR, MONTH, DAY, FIXTURE_20260301)
    df = scraper.get_race_schedule()

    for race_id in df["レースID"]:
        assert race_id.startswith("2026"), f"レースIDが2026で始まらない: {race_id}"


# ---------------------------------------------------------------------------
# 正常系: 日付の型と値
# ---------------------------------------------------------------------------
def test_date_is_datetime_date() -> None:
    """日付がdatetime.date型であること"""
    scraper = create_scraper_from_fixture(YEAR, MONTH, DAY, FIXTURE_20260301)
    df = scraper.get_race_schedule()

    for date_val in df["日付"]:
        assert isinstance(date_val, datetime.date), f"日付がdate型でない: {date_val}"


def test_date_is_march_1st() -> None:
    """日付が全て2026年3月1日であること"""
    scraper = create_scraper_from_fixture(YEAR, MONTH, DAY, FIXTURE_20260301)
    df = scraper.get_race_schedule()

    expected = datetime.date(2026, 3, 1)
    for date_val in df["日付"]:
        assert date_val == expected, f"日付が2026/03/01でない: {date_val}"


# ---------------------------------------------------------------------------
# 正常系: 競馬場の値
# ---------------------------------------------------------------------------
def test_keibajo_three_venues() -> None:
    """3場開催（中山・阪神・小倉）であること"""
    scraper = create_scraper_from_fixture(YEAR, MONTH, DAY, FIXTURE_20260301)
    df = scraper.get_race_schedule()

    actual = set(df["競馬場"].unique())
    assert actual == {"中山", "阪神", "小倉"}, f"競馬場が異なる: {actual}"


# ---------------------------------------------------------------------------
# 正常系: 回・開催日の型
# ---------------------------------------------------------------------------
def test_kai_is_int() -> None:
    """回がint型であること"""
    scraper = create_scraper_from_fixture(YEAR, MONTH, DAY, FIXTURE_20260301)
    df = scraper.get_race_schedule()

    for kai in df["回"]:
        assert isinstance(kai, (int, np.integer)), f"回がint型でない: {kai}"


def test_kaisai_day_is_int() -> None:
    """開催日がint型であること"""
    scraper = create_scraper_from_fixture(YEAR, MONTH, DAY, FIXTURE_20260301)
    df = scraper.get_race_schedule()

    for day_val in df["開催日"]:
        assert isinstance(day_val, (int, np.integer)), f"開催日がint型でない: {day_val}"


# ---------------------------------------------------------------------------
# 正常系: Rの値
# ---------------------------------------------------------------------------
def test_r_values() -> None:
    """Rが1〜12の整数であること"""
    scraper = create_scraper_from_fixture(YEAR, MONTH, DAY, FIXTURE_20260301)
    df = scraper.get_race_schedule()

    for r_val in df["R"]:
        assert isinstance(r_val, (int, np.integer)), f"Rがint型でない: {r_val}"
        assert 1 <= r_val <= 12, f"Rが範囲外: {r_val}"


def test_r_covers_1_to_12_per_venue() -> None:
    """各競馬場でRが1〜12をカバーすること"""
    scraper = create_scraper_from_fixture(YEAR, MONTH, DAY, FIXTURE_20260301)
    df = scraper.get_race_schedule()

    for keibajo in df["競馬場"].unique():
        venue_df = df[df["競馬場"] == keibajo]
        r_set = set(venue_df["R"].tolist())
        expected = set(range(1, 13))
        assert r_set == expected, f"{keibajo}のRが1〜12でない: {r_set}"


# ---------------------------------------------------------------------------
# 正常系: レース名
# ---------------------------------------------------------------------------
def test_race_name_not_empty() -> None:
    """レース名が空でないこと"""
    scraper = create_scraper_from_fixture(YEAR, MONTH, DAY, FIXTURE_20260301)
    df = scraper.get_race_schedule()

    for name in df["レース名"]:
        assert isinstance(name, str), f"レース名が文字列でない: {name}"
        assert len(name) > 0, "レース名が空文字"


# ---------------------------------------------------------------------------
# 正常系: 芝ダの値
# ---------------------------------------------------------------------------
def test_turf_dirt_values() -> None:
    """芝ダが"芝","ダ","障"のいずれかであること"""
    valid = {"芝", "ダ", "障"}
    scraper = create_scraper_from_fixture(YEAR, MONTH, DAY, FIXTURE_20260301)
    df = scraper.get_race_schedule()

    actual = set(df["芝ダ"].unique())
    assert actual <= valid, f"不正な芝ダ: {actual - valid}"


# ---------------------------------------------------------------------------
# 正常系: 距離の型と範囲
# ---------------------------------------------------------------------------
def test_distance_is_positive_int() -> None:
    """距離が正のintであること"""
    scraper = create_scraper_from_fixture(YEAR, MONTH, DAY, FIXTURE_20260301)
    df = scraper.get_race_schedule()

    for dist in df["距離"]:
        assert isinstance(dist, (int, np.integer)), f"距離がint型でない: {dist}"
        assert dist > 0, f"距離が0以下: {dist}"


# ---------------------------------------------------------------------------
# 正常系: 頭数の型と範囲
# ---------------------------------------------------------------------------
def test_num_runners_is_positive_int() -> None:
    """頭数が正のintであること"""
    scraper = create_scraper_from_fixture(YEAR, MONTH, DAY, FIXTURE_20260301)
    df = scraper.get_race_schedule()

    for num in df["頭数"]:
        assert isinstance(num, (int, np.integer)), f"頭数がint型でない: {num}"
        assert num > 0, f"頭数が0以下: {num}"


# ---------------------------------------------------------------------------
# 正常系: 馬場の値
# ---------------------------------------------------------------------------
def test_baba_values() -> None:
    """馬場が良/稍/重/不のいずれかであること"""
    valid = {"良", "稍", "重", "不"}
    scraper = create_scraper_from_fixture(YEAR, MONTH, DAY, FIXTURE_20260301)
    df = scraper.get_race_schedule()

    actual = set(df["馬場"].unique())
    assert actual <= valid, f"不正な馬場: {actual - valid}"


def test_baba_not_empty() -> None:
    """馬場が空でないこと"""
    scraper = create_scraper_from_fixture(YEAR, MONTH, DAY, FIXTURE_20260301)
    df = scraper.get_race_schedule()

    for baba in df["馬場"]:
        assert isinstance(baba, str), f"馬場が文字列でない: {baba}"
        assert len(baba) > 0, "馬場が空文字"


# ---------------------------------------------------------------------------
# 正常系: 発走時刻の形式
# ---------------------------------------------------------------------------
def test_start_time_format() -> None:
    """発走時刻がHH:MM形式であること"""
    scraper = create_scraper_from_fixture(YEAR, MONTH, DAY, FIXTURE_20260301)
    df = scraper.get_race_schedule()

    for time_val in df["発走時刻"]:
        assert isinstance(time_val, str), f"発走時刻が文字列でない: {time_val}"
        assert re.match(r"^\d{1,2}:\d{2}$", time_val), f"発走時刻の形式が不正: {time_val}"


def test_start_time_not_empty() -> None:
    """発走時刻が空でないこと"""
    scraper = create_scraper_from_fixture(YEAR, MONTH, DAY, FIXTURE_20260301)
    df = scraper.get_race_schedule()

    for time_val in df["発走時刻"]:
        assert len(time_val) > 0, "発走時刻が空文字"


# ---------------------------------------------------------------------------
# 正常系: 先頭レースの具体値検証
# ---------------------------------------------------------------------------
def test_first_race_values() -> None:
    """先頭レース（中山1R）の具体値を検証する"""
    scraper = create_scraper_from_fixture(YEAR, MONTH, DAY, FIXTURE_20260301)
    df = scraper.get_race_schedule()

    first = df.iloc[0]
    assert first["レースID"] == "202606020201"
    assert first["日付"] == datetime.date(2026, 3, 1)
    assert first["競馬場"] == "中山"
    assert first["回"] == 2
    assert first["開催日"] == 2
    assert first["R"] == 1
    assert first["レース名"] == "3歳未勝利"
    assert first["芝ダ"] == "ダ"
    assert first["距離"] == 1800
    assert first["頭数"] == 16
    assert first["馬場"] == "良"
    assert first["発走時刻"] == "10:05"


# ---------------------------------------------------------------------------
# 正常系: 馬場状態が芝ダに応じて正しく設定されること
# ---------------------------------------------------------------------------
def test_baba_turf_race() -> None:
    """芝レースには芝の馬場状態が設定されること"""
    scraper = create_scraper_from_fixture(YEAR, MONTH, DAY, FIXTURE_20260301)
    df = scraper.get_race_schedule()

    # 小倉の芝レースがある場合、小倉の馬場状態を確認
    ogura_turf = df[(df["競馬場"] == "小倉") & (df["芝ダ"] == "芝")]
    if len(ogura_turf) > 0:
        for baba in ogura_turf["馬場"]:
            assert baba == "良", f"小倉芝の馬場が良でない: {baba}"


def test_baba_dirt_race_ogura() -> None:
    """小倉のダートレースにはダートの馬場状態(稍)が設定されること"""
    scraper = create_scraper_from_fixture(YEAR, MONTH, DAY, FIXTURE_20260301)
    df = scraper.get_race_schedule()

    ogura_dirt = df[(df["競馬場"] == "小倉") & (df["芝ダ"] == "ダ")]
    if len(ogura_dirt) > 0:
        for baba in ogura_dirt["馬場"]:
            assert baba == "稍", f"小倉ダの馬場が稍でない: {baba}"


# ---------------------------------------------------------------------------
# 準正常系: 開催のない日は0行のDataFrameを返す
# ---------------------------------------------------------------------------
def test_no_race_day_returns_empty_dataframe() -> None:
    """開催のない日は0行のDataFrameを返すこと"""
    # 空のHTMLをモック
    empty_html = "<html><body></body></html>"
    mock_driver = MagicMock()
    mock_driver.page_source = empty_html

    with (
        patch("scraping.race_schedule.webdriver.Chrome", return_value=mock_driver),
        patch("scraping.race_schedule.time.sleep"),
    ):
        scraper = RaceScheduleScraper(2026, 12, 25)

    df = scraper.get_race_schedule()

    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == RACE_SCHEDULE_COLUMNS
    assert len(df) == 0
