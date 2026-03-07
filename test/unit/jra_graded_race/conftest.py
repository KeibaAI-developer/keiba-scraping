"""jra_graded_raceテスト共通設定

jra_graded_raceテストで使用する共通のヘルパー関数を定義する。
"""

import os
from unittest.mock import MagicMock

from scraping.jra_graded_race import JraGradedRaceScraper

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


def create_scraper_with_mock(year: int, fixture_filename: str) -> JraGradedRaceScraper:
    """フィクスチャHTMLからJraGradedRaceScraperを生成する

    session.getがフィクスチャHTMLを返すようにモックする。

    Args:
        year (int): 年
        fixture_filename (str): フィクスチャファイル名

    Returns:
        JraGradedRaceScraper: フィクスチャHTMLベースのスクレイパー
    """
    mock_session = MagicMock()
    scraper = JraGradedRaceScraper(year, session=mock_session)

    html_text = load_html(fixture_filename)
    mock_response = MagicMock()
    mock_response.text = html_text
    mock_response.apparent_encoding = "utf-8"
    mock_session.get.return_value = mock_response

    return scraper
