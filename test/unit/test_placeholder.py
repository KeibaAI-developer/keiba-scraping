"""プレースホルダーテスト.

PR-1でテストコードがない状態でもCIを通過させるための最小限のテスト。
PR-2以降で実際のテストに置き換える。
"""

import scraping


def test_package_import() -> None:
    """パッケージが正常にインポートできることを確認する."""
    assert scraping is not None


def test_version_defined() -> None:
    """__version__が定義されていることを確認する."""
    assert hasattr(scraping, "__version__")
    assert isinstance(scraping.__version__, str)
    assert len(scraping.__version__) > 0
