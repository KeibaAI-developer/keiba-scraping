"""keiba-scrapingテスト用の共通fixture"""

import pytest

from scraping import __version__


def pytest_configure(config: pytest.Config) -> None:
    """カスタムマーカーを登録する"""
    config.addinivalue_line("markers", "network: ネットワーク接続が必要なテスト")


@pytest.fixture()
def library_version() -> str:
    """ライブラリのバージョンを返すフィクスチャ"""
    return __version__
