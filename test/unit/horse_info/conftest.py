"""horse_infoテスト共通設定

horse_infoテストで使用する共通のヘルパー関数を定義する。
"""

import glob
import os
from unittest.mock import MagicMock, patch

from scraping.horse_info import HorseInfoScraper

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
) -> HorseInfoScraper:
    """フィクスチャHTMLからHorseInfoScraperを生成する

    _scrape_max_page_numをモックし、session.getがフィクスチャHTMLを返すようにする。
    fixture_filenamesはページ番号の昇順で渡す。

    Args:
        year (int): 生年
        max_page_num (int): 最大ページ数
        fixture_filenames (list[str]): フィクスチャファイル名のリスト

    Returns:
        HorseInfoScraper: フィクスチャHTMLベースのスクレイパー
    """
    mock_session = MagicMock()

    with patch.object(HorseInfoScraper, "_scrape_max_page_num", return_value=max_page_num):
        scraper = HorseInfoScraper(year, session=mock_session)

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


def collect_fixture_years_pages() -> list[tuple[int, int]]:
    """利用可能な馬情報フィクスチャの(year, page_num)リストを返す

    Returns:
        list[tuple[int, int]]: (year, page_num)のリスト
    """
    fixture_dir = os.path.normpath(FIXTURES_DIR)
    results: list[tuple[int, int]] = []
    for filepath in sorted(glob.glob(os.path.join(fixture_dir, "horse_info_*.html"))):
        basename = os.path.basename(filepath)
        # horse_info_2022_p1.html → year=2022, page=1
        parts = basename.replace("horse_info_", "").replace(".html", "").split("_p")
        if len(parts) == 2:
            results.append((int(parts[0]), int(parts[1])))
    return results
