"""set_chrome_optionsの単体テスト"""

from scraping.utils import set_chrome_options


# 正常系
def test_set_chrome_options_returns_options() -> None:
    """Optionsオブジェクトが返ることを確認する"""
    options = set_chrome_options()
    assert options is not None


def test_set_chrome_options_headless() -> None:
    """ヘッドレスモードが有効であることを確認する"""
    options = set_chrome_options()
    assert "--headless" in options.arguments


def test_set_chrome_options_no_sandbox() -> None:
    """--no-sandboxが設定されていることを確認する"""
    options = set_chrome_options()
    assert "--no-sandbox" in options.arguments


def test_set_chrome_options_disable_gpu() -> None:
    """--disable-gpuが設定されていることを確認する"""
    options = set_chrome_options()
    assert "--disable-gpu" in options.arguments


def test_set_chrome_options_disable_dev_shm_usage() -> None:
    """--disable-dev-shm-usageが設定されていることを確認する"""
    options = set_chrome_options()
    assert "--disable-dev-shm-usage" in options.arguments
