"""result_pageテスト共通設定

result_pageテストで使用する共通のヘルパー関数とフィクスチャを定義する。
"""

import glob
import os
from unittest.mock import MagicMock, patch

from scraping.result_page import ResultPageScraper

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


def create_scraper_from_fixture(race_id: str) -> ResultPageScraper:
    """フィクスチャHTMLからResultPageScraperを生成する

    Args:
        race_id (str): レースID

    Returns:
        ResultPageScraper: フィクスチャHTMLベースのスクレイパー
    """
    fixture_filename = f"result_{race_id}.html"
    html_text = load_html(fixture_filename)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = html_text
    mock_response.encoding = "utf-8"
    mock_response.raise_for_status = MagicMock()

    with patch("scraping.result_page.requests.get", return_value=mock_response):
        scraper = ResultPageScraper(race_id)

    return scraper


def collect_result_fixture_race_ids() -> list[str]:
    """利用可能な結果フィクスチャのレースIDリストを返す

    Returns:
        list[str]: レースIDのリスト
    """
    fixture_dir = os.path.normpath(FIXTURES_DIR)
    race_ids: list[str] = []
    for filepath in sorted(glob.glob(os.path.join(fixture_dir, "result_*.html"))):
        basename = os.path.basename(filepath)
        race_id = basename.replace("result_", "").replace(".html", "")
        race_ids.append(race_id)
    return race_ids
