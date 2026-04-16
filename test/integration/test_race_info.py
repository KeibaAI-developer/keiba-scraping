"""scrape_race_infoの結合テスト

フィクスチャは使用せず、実際にnetkeibaにアクセスしてスクレイピングを行い、
scrape_race_infoが正しく動作することを確認する。
netkeibaのHTML構造の仕様変更に気づきやすくすることが目的。

ネットワーク接続が必要なため、@pytest.mark.networkマーカーを付与する。
環境変数 RUN_NETWORK_TESTS=1 が設定されている場合のみ実行される（opt-in）。
"""

import os
import time
from datetime import date

import pandas as pd
import pytest
import requests
from bs4 import BeautifulSoup

from scraping.config import RACE_INFO_COLUMNS
from scraping.race_info import scrape_race_info

# テスト間のリクエスト間隔（秒）
REQUEST_INTERVAL = 1.0

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/58.0.3029.110 Safari/537.3"
    )
}


def _fetch_soup(url: str) -> BeautifulSoup:
    """netkeibaからHTMLを取得してBeautifulSoupを返す

    Args:
        url (str): 取得するURL

    Returns:
        BeautifulSoup: パース済みのBeautifulSoupオブジェクト
    """
    response = requests.get(url, headers=HEADERS, timeout=10)
    response.encoding = "EUC-JP"
    return BeautifulSoup(response.text, "html.parser")


# 正常系
LIVE_TEST_CASES = [
    {
        "race_id": "202505021211",
        "url": "https://race.netkeiba.com/race/result.html?race_id=202505021211",
        "description": "日本ダービー2025（G1, 結果ページ）",
        "expected": {
            "日付": date(2025, 6, 1),
            "曜日": "日",
            "発走時刻": "15:40",
            "レース名": "日本ダービー",
            "芝ダ": "芝",
            "距離": 2400,
            "競馬場": "東京",
            "競走条件": "オープン",
            "グレード": "G1",
        },
    },
    {
        "race_id": "202306030111",
        "url": "https://race.netkeiba.com/race/result.html?race_id=202306030111",
        "description": "日経賞2023（G2, 不良馬場, 結果ページ）",
        "expected": {
            "日付": date(2023, 3, 25),
            "曜日": "土",
            "発走時刻": "15:45",
            "レース名": "日経賞",
            "芝ダ": "芝",
            "距離": 2500,
            "競馬場": "中山",
            "馬場": "不",
            "競走条件": "オープン",
            "グレード": "G2",
        },
    },
    {
        "race_id": "202406050710",
        "url": "https://race.netkeiba.com/race/result.html?race_id=202406050710",
        "description": "中山大障害2024（障害, 結果ページ）",
        "expected": {
            "日付": date(2024, 12, 21),
            "曜日": "土",
            "発走時刻": "15:05",
            "レース名": "中山大障害",
            "レース種別": "障害",
            "芝ダ": "芝",
            "距離": 4100,
            "競馬場": "中山",
            "競走条件": "オープン",
            "グレード": "JG1",
        },
    },
    {
        "race_id": "202505021211",
        "url": "https://race.netkeiba.com/race/shutuba.html?race_id=202505021211",
        "description": "日本ダービー2025（G1, 出馬表ページ）",
        "expected": {
            "日付": date(2025, 6, 1),
            "曜日": "日",
            "発走時刻": "15:40",
            "レース名": "日本ダービー",
            "芝ダ": "芝",
            "距離": 2400,
            "競馬場": "東京",
            "競走条件": "オープン",
            "グレード": "G1",
        },
    },
]


LIVE_TEST_CASE_IDS = [str(tc["description"]) for tc in LIVE_TEST_CASES]


@pytest.mark.network
@pytest.mark.parametrize(
    "test_case",
    LIVE_TEST_CASES,
    ids=LIVE_TEST_CASE_IDS,
)
def test_scrape_race_info_live(test_case: dict[str, object]) -> None:
    """実際にnetkeibaからスクレイピングしてscrape_race_infoが動作することを確認する"""
    if not os.environ.get("RUN_NETWORK_TESTS"):
        pytest.skip("RUN_NETWORK_TESTS environment variable is not set")

    race_id = str(test_case["race_id"])
    url = str(test_case["url"])
    expected = test_case["expected"]
    assert isinstance(expected, dict)

    soup = _fetch_soup(url)
    result = scrape_race_info(soup, race_id)

    # DataFrameの構造チェック
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 1
    assert list(result.columns) == RACE_INFO_COLUMNS

    # レースIDの一致
    assert result["レースID"].iloc[0] == race_id

    # 期待値の検証
    row = result.iloc[0]
    for key, expected_value in expected.items():
        actual = row[key]
        assert actual == expected_value, (
            f"{key}: expected={expected_value!r}, actual={actual!r} " f"(race_id={race_id})"
        )

    # リクエスト間隔を空ける
    time.sleep(REQUEST_INTERVAL)


# 準正常系
@pytest.mark.network
def test_scrape_race_info_live_parse_error_on_nonexistent_race() -> None:
    """存在しないレースIDでParseErrorが発生することを確認する"""
    if not os.environ.get("RUN_NETWORK_TESTS"):
        pytest.skip("RUN_NETWORK_TESTS environment variable is not set")

    from scraping.exceptions import ParseError

    race_id = "202306010911"
    url = f"https://race.netkeiba.com/race/result.html?race_id={race_id}"
    soup = _fetch_soup(url)

    with pytest.raises(ParseError):
        scrape_race_info(soup, race_id)
