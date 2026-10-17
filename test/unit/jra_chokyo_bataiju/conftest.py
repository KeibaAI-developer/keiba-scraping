"""jra_chokyo_bataijuテスト共通設定

jra_chokyo_bataijuテストで使用する共通のヘルパー関数を定義する。
"""

import os
from unittest.mock import MagicMock

from scraping.jra_chokyo_bataiju import JraChokyoBataijuScraper

# フィクスチャHTMLのディレクトリ
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "fixtures", "html")

# 2026年秋華賞のG1特設ページ（調教後馬体重）とニュースのフィクスチャ
FIXTURE_WEIGHT_PAGE = "jra_g1_weight_shuka_2026.html"
FIXTURE_NEWS = "jra_chokyo_bataiju_news_202610_101502.html"
NEWS_PATH = "/news/202610/101502.html"
# 枠順の確定後に発表された2026年日本ダービーのニュース（枠・馬番の列がある）
FIXTURE_NEWS_WITH_DRAW = "jra_chokyo_bataiju_news_202605_052803.html"
# 前走馬体重に「前走海外」がある2026年安田記念のニュース
FIXTURE_NEWS_OVERSEAS = "jra_chokyo_bataiju_news_202606_060405.html"
# 表に閉じていない空の行がある2026年オークスのニュース
FIXTURE_NEWS_UNCLOSED_ROW = "jra_chokyo_bataiju_news_202605_052108.html"


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


def make_response(html_text: str) -> MagicMock:
    """HTMLを本文に持つレスポンスのモックを生成する

    Args:
        html_text (str): HTMLテキスト

    Returns:
        MagicMock: レスポンスのモック
    """
    response = MagicMock()
    response.text = html_text
    response.headers = {}
    response.apparent_encoding = "utf-8"
    return response


def create_scraper_with_mock(
    weight_page_html: str, news_html: str
) -> tuple[JraChokyoBataijuScraper, MagicMock]:
    """G1特設ページとニュースのHTMLを返すモックからJraChokyoBataijuScraperを生成する

    session.getは1回目にG1特設ページ、2回目にニュースのHTMLを返す。

    Args:
        weight_page_html (str): G1特設ページの調教後馬体重のページのHTML
        news_html (str): ニュースのHTML

    Returns:
        tuple[JraChokyoBataijuScraper, MagicMock]: スクレイパーとsessionのモック
    """
    mock_session = MagicMock()
    mock_session.get.side_effect = [make_response(weight_page_html), make_response(news_html)]
    return JraChokyoBataijuScraper("shuka", session=mock_session), mock_session
