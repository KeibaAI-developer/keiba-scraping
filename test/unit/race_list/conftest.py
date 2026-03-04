"""race_listテスト共通設定

race_listテストで使用する共通のヘルパー関数を定義する。
"""

import os
from unittest.mock import MagicMock, patch

from scraping.race_list import RaceListScraper

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


def create_scraper_with_mock(
    year: int, max_page_num: int, fixture_filenames: list[str]
) -> RaceListScraper:
    """フィクスチャHTMLからRaceListScraperを生成する

    _scrape_max_page_numをモックし、session.getがフィクスチャHTMLを返すようにする。
    fixture_filenamesはページ番号の昇順で渡す。

    Args:
        year (int): 年
        max_page_num (int): 最大ページ数
        fixture_filenames (list[str]): フィクスチャファイル名のリスト

    Returns:
        RaceListScraper: フィクスチャHTMLベースのスクレイパー
    """
    mock_session = MagicMock()

    with patch.object(RaceListScraper, "_scrape_max_page_num", return_value=max_page_num):
        scraper = RaceListScraper(year, session=mock_session)

    # session.getのside_effectを設定（呼び出し順にフィクスチャHTMLを返す）
    responses = []
    for filename in fixture_filenames:
        html_text = load_html(filename)
        mock_response = MagicMock()
        mock_response.text = html_text
        mock_response.encoding = "EUC-JP"
        responses.append(mock_response)

    mock_session.get.side_effect = responses

    return scraper
