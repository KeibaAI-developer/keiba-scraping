"""past_performancesテスト共通設定

past_performancesテストで使用する共通のヘルパー関数を定義する。
"""

import glob
import os
from unittest.mock import MagicMock, patch

from scraping.past_performances import PastPerformancesScraper

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


def create_scraper_from_fixture(horse_id: str) -> PastPerformancesScraper:
    """フィクスチャHTMLからPastPerformancesScraperを生成する

    Selenium WebDriverをモックし、フィクスチャHTMLのpage_sourceを返すようにする。

    Args:
        horse_id (str): 馬ID

    Returns:
        PastPerformancesScraper: フィクスチャHTMLベースのスクレイパー
    """
    fixture_filename = f"past_performances_{horse_id}.html"
    html_text = load_html(fixture_filename)

    mock_driver = MagicMock()
    mock_driver.page_source = html_text

    with patch("scraping.past_performances.webdriver.Chrome", return_value=mock_driver):
        scraper = PastPerformancesScraper(horse_id)

    return scraper


def collect_fixture_horse_ids() -> list[str]:
    """利用可能な馬柱フィクスチャの馬IDリストを返す

    Returns:
        list[str]: 馬IDのリスト
    """
    fixture_dir = os.path.normpath(FIXTURES_DIR)
    horse_ids: list[str] = []
    for filepath in sorted(glob.glob(os.path.join(fixture_dir, "past_performances_*.html"))):
        basename = os.path.basename(filepath)
        horse_id = basename.replace("past_performances_", "").replace(".html", "")
        horse_ids.append(horse_id)
    return horse_ids
