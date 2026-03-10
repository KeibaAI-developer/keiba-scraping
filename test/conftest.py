"""keiba-scrapingテスト用の共通fixture"""

from pathlib import Path

import pytest
from dotenv import load_dotenv

from scraping import __version__

# .envファイルを読み込む（統合テストのRUN_NETWORK_TESTS環境変数用）
dotenv_path = Path(__file__).parent.parent / ".env"
if dotenv_path.exists():
    load_dotenv(dotenv_path)


def pytest_configure(config: pytest.Config) -> None:
    """カスタムマーカーを登録する"""
    config.addinivalue_line("markers", "network: ネットワーク接続が必要なテスト")


@pytest.fixture()
def library_version() -> str:
    """ライブラリのバージョンを返すフィクスチャ"""
    return __version__
