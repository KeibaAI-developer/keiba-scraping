"""jra_pre_ratingテスト共通設定

jra_pre_ratingテストで使用する共通のヘルパー関数を定義する。
"""

import os
from unittest.mock import MagicMock

from scraping.jra_pre_rating import JraPreRatingScraper

# フィクスチャHTMLのディレクトリ
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "fixtures", "html")

# 2017年以降の形の、2026年エリザベス女王杯のページ
FIXTURE_CURRENT = "jra_pre_rating_2026_eliza.html"
# 2017年以降の形で前年のJPNランキングの列がある、2026年大阪杯のページ
FIXTURE_CURRENT_WITH_PREVIOUS = "jra_pre_rating_2026_osaka.html"
# 2017年以降の形で外国馬の表がある、2022年エリザベス女王杯のページ
FIXTURE_CURRENT_WITH_FOREIGN = "jra_pre_rating_2022_eliza.html"
# 2016年以前の形の、2016年エリザベス女王杯のページ
FIXTURE_OLD = "jra_pre_rating_2016_eliza.html"
# 2016年以前の形で前年のJPNランキングの列がある、2014年フェブラリーSのページ
FIXTURE_OLD_WITH_PREVIOUS = "jra_pre_rating_2014_feb.html"
# 2016年以前の形で外国馬の表がある、2011年エリザベス女王杯のページ
FIXTURE_OLD_WITH_FOREIGN = "jra_pre_rating_2011_eliza.html"


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


def create_scraper_with_mock(html_text: str) -> tuple[JraPreRatingScraper, MagicMock]:
    """HTMLを返すモックから2026年エリザベス女王杯のJraPreRatingScraperを生成する

    Args:
        html_text (str): ページのHTML

    Returns:
        tuple[JraPreRatingScraper, MagicMock]: スクレイパーとsessionのモック
    """
    response = MagicMock()
    response.text = html_text
    response.headers = {}
    response.apparent_encoding = "utf-8"
    mock_session = MagicMock()
    mock_session.get.return_value = response
    return JraPreRatingScraper(2026, "eliza", session=mock_session), mock_session
