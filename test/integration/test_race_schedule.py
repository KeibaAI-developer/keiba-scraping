"""RaceScheduleScraperの結合テスト

フィクスチャは使用せず、実際にnetkeibaにアクセスしてスクレイピングを行い、
RaceScheduleScraperの各パブリックメソッドが正しく動作することを確認する。
netkeibaのHTML構造の仕様変更に気づきやすくすることが目的。

ネットワーク接続が必要なため、@pytest.mark.networkマーカーを付与する。
環境変数 RUN_NETWORK_TESTS=1 が設定されている場合のみ実行される（opt-in）。

Seleniumを使用するため、Chrome/ChromeDriverが必要。
"""

import datetime
import os
import re
import time

import pandas as pd
import pytest

from scraping.config import RACE_SCHEDULE_COLUMNS
from scraping.race_schedule import RaceScheduleScraper

# テスト間のリクエスト間隔（秒）: Seleniumなので長めに設定
REQUEST_INTERVAL = 5.0
RUN_NETWORK_TESTS = os.environ.get("RUN_NETWORK_TESTS") == "1"

pytestmark = [
    pytest.mark.network,
    pytest.mark.skipif(
        not RUN_NETWORK_TESTS,
        reason="RUN_NETWORK_TESTS environment variable is not set",
    ),
]

# テスト対象の日付（過去の開催日を使用）
TEST_YEAR = 2025
TEST_MONTH = 5
TEST_DAY = 25


# ---------------------------------------------------------------------------
# ヘルパー
# ---------------------------------------------------------------------------
def _create_scraper() -> RaceScheduleScraper:
    """テスト用のスクレイパーを生成する"""
    return RaceScheduleScraper(TEST_YEAR, TEST_MONTH, TEST_DAY)


# ---------------------------------------------------------------------------
# 正常系: カラム構成
# ---------------------------------------------------------------------------
def test_get_race_schedule_columns() -> None:
    """get_race_scheduleがRACE_SCHEDULE_COLUMNSと一致するDataFrameを返すこと"""
    scraper = _create_scraper()
    df = scraper.get_race_schedule()

    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == RACE_SCHEDULE_COLUMNS
    assert len(df) > 0

    time.sleep(REQUEST_INTERVAL)


# ---------------------------------------------------------------------------
# 正常系: 行数
# ---------------------------------------------------------------------------
def test_get_race_schedule_row_count() -> None:
    """開催日のレーススケジュールが1行以上あること"""
    scraper = _create_scraper()
    df = scraper.get_race_schedule()

    # 通常の開催日は24レース以上（2場以上）
    assert len(df) >= 12

    time.sleep(REQUEST_INTERVAL)


# ---------------------------------------------------------------------------
# 正常系: レースIDの形式
# ---------------------------------------------------------------------------
def test_race_id_format() -> None:
    """レースIDが12桁の数字文字列であること"""
    scraper = _create_scraper()
    df = scraper.get_race_schedule()

    for race_id in df["レースID"]:
        assert (
            isinstance(race_id, str) and len(race_id) == 12 and race_id.isdigit()
        ), f"レースIDが不正: {race_id}"

    time.sleep(REQUEST_INTERVAL)


# ---------------------------------------------------------------------------
# 正常系: 日付型
# ---------------------------------------------------------------------------
def test_date_type() -> None:
    """日付カラムがdatetime.date型であること"""
    scraper = _create_scraper()
    df = scraper.get_race_schedule()

    for val in df["日付"]:
        assert isinstance(val, datetime.date), f"日付が不正: {val} ({type(val)})"

    time.sleep(REQUEST_INTERVAL)


# ---------------------------------------------------------------------------
# 正常系: 芝ダの値
# ---------------------------------------------------------------------------
def test_turf_dirt_values() -> None:
    """芝ダが芝/ダ/障のいずれかであること"""
    scraper = _create_scraper()
    df = scraper.get_race_schedule()

    valid = {"芝", "ダ", "障"}
    actual = set(df["芝ダ"].unique())
    assert actual <= valid, f"不正な芝ダ: {actual - valid}"

    time.sleep(REQUEST_INTERVAL)


# ---------------------------------------------------------------------------
# 正常系: 距離が正の整数
# ---------------------------------------------------------------------------
def test_distance_is_positive() -> None:
    """距離が正の整数であること"""
    scraper = _create_scraper()
    df = scraper.get_race_schedule()

    for dist in df["距離"]:
        assert isinstance(dist, int) and dist > 0, f"距離が不正: {dist}"

    time.sleep(REQUEST_INTERVAL)


# ---------------------------------------------------------------------------
# 正常系: 馬場の値
# ---------------------------------------------------------------------------
def test_baba_values() -> None:
    """馬場が良/稍/重/不のいずれかであること"""
    scraper = _create_scraper()
    df = scraper.get_race_schedule()

    valid = {"良", "稍", "重", "不"}
    actual = set(df["馬場"].unique())
    assert actual <= valid, f"不正な馬場: {actual - valid}"

    time.sleep(REQUEST_INTERVAL)


# ---------------------------------------------------------------------------
# 正常系: 発走時刻の形式
# ---------------------------------------------------------------------------
def test_start_time_format() -> None:
    """発走時刻がHH:MM形式（ゼロ埋め）であること"""
    scraper = _create_scraper()
    df = scraper.get_race_schedule()

    for t in df["発走時刻"]:
        assert re.match(r"^\d{2}:\d{2}$", str(t)), f"発走時刻が不正: {t}"

    time.sleep(REQUEST_INTERVAL)


# ---------------------------------------------------------------------------
# 正常系: 頭数が正の整数
# ---------------------------------------------------------------------------
def test_num_runners_is_positive() -> None:
    """頭数が正の整数であること"""
    scraper = _create_scraper()
    df = scraper.get_race_schedule()

    for n in df["頭数"]:
        assert isinstance(n, int) and n > 0, f"頭数が不正: {n}"

    time.sleep(REQUEST_INTERVAL)
