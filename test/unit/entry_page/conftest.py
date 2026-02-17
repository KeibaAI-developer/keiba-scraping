"""entry_pageテスト共通設定

entry_pageテストで使用する共通のヘルパー関数を定義する。
"""

import glob
import os
from unittest.mock import MagicMock, patch

from scraping.entry_page import EntryPageScraper

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


def create_scraper_from_fixture(race_id: str) -> EntryPageScraper:
    """フィクスチャHTMLからEntryPageScraperを生成する

    Args:
        race_id (str): レースID

    Returns:
        EntryPageScraper: フィクスチャHTMLベースのスクレイパー
    """
    fixture_filename = f"entry_{race_id}.html"
    html_text = load_html(fixture_filename)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = html_text
    mock_response.encoding = "utf-8"
    mock_response.raise_for_status = MagicMock()

    with patch("scraping.entry_page.requests.get", return_value=mock_response):
        scraper = EntryPageScraper(race_id)

    return scraper


def collect_entry_fixture_race_ids() -> list[str]:
    """利用可能な出馬表フィクスチャのレースIDリストを返す

    Returns:
        list[str]: レースIDのリスト
    """
    fixture_dir = os.path.normpath(FIXTURES_DIR)
    race_ids: list[str] = []
    for filepath in sorted(glob.glob(os.path.join(fixture_dir, "entry_*.html"))):
        basename = os.path.basename(filepath)
        race_id = basename.replace("entry_", "").replace(".html", "")
        race_ids.append(race_id)
    return race_ids
