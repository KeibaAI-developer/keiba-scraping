"""race_scheduleテスト共通設定

race_scheduleテストで使用する共通のヘルパー関数を定義する。
"""

import os
from unittest.mock import MagicMock, patch

from scraping.race_schedule import RaceScheduleScraper

# フィクスチャHTMLのディレクトリ
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "fixtures", "html")


def load_html(fixture_filename: str) -> str:
    """フィクスチャHTMLを読み込んで文字列を返す

    Args:
        fixture_filename (str): フィクスチャファイル名

    Returns:
        str: HTMLテキスト
    """
    filepath = os.path.join(FIXTURES_DIR, fixture_filename)
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def create_scraper_from_fixture(
    year: int, month: int, day: int, fixture_filename: str
) -> RaceScheduleScraper:
    """フィクスチャHTMLからRaceScheduleScraperを生成する

    Selenium WebDriverをモックし、フィクスチャHTMLのpage_sourceを返すようにする。
    time.sleepもモックして高速化する。

    Args:
        year (int): 年
        month (int): 月
        day (int): 日
        fixture_filename (str): フィクスチャファイル名

    Returns:
        RaceScheduleScraper: フィクスチャHTMLベースのスクレイパー
    """
    html_text = load_html(fixture_filename)

    mock_driver = MagicMock()
    mock_driver.page_source = html_text

    with (
        patch("scraping.race_schedule.webdriver.Chrome", return_value=mock_driver),
        patch("scraping.race_schedule.time.sleep"),
    ):
        scraper = RaceScheduleScraper(year, month, day)

    return scraper
