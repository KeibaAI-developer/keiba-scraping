"""keiba-scrapingテスト用の共通fixture"""

import pytest

from scraping import __version__


@pytest.fixture()
def library_version() -> str:
    """ライブラリのバージョンを返すフィクスチャ"""
    return __version__
