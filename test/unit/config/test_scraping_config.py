"""ScrapingConfigの単体テスト"""

from scraping.config import ScrapingConfig


# 正常系
def test_default_values() -> None:
    """デフォルト値が正しく設定されることを確認する"""
    config = ScrapingConfig()
    assert config.netkeiba_base_url == "https://db.netkeiba.com"
    assert config.netkeiba_race_url == "https://race.netkeiba.com"
    assert config.jra_url == "https://www.jra.go.jp"
    assert config.chrome_driver_path == "/usr/bin/chromedriver"
    assert config.request_timeout == 10
    assert "User-Agent" in config.headers


def test_custom_values() -> None:
    """カスタム値を設定できることを確認する"""
    config = ScrapingConfig(
        netkeiba_base_url="https://custom.netkeiba.com",
        netkeiba_race_url="https://custom-race.netkeiba.com",
        jra_url="https://custom.jra.go.jp",
        headers={"User-Agent": "CustomAgent/1.0"},
        chrome_driver_path="/custom/path/chromedriver",
        request_timeout=30,
    )
    assert config.netkeiba_base_url == "https://custom.netkeiba.com"
    assert config.netkeiba_race_url == "https://custom-race.netkeiba.com"
    assert config.jra_url == "https://custom.jra.go.jp"
    assert config.headers == {"User-Agent": "CustomAgent/1.0"}
    assert config.chrome_driver_path == "/custom/path/chromedriver"
    assert config.request_timeout == 30


def test_partial_custom_values() -> None:
    """一部のみカスタム値を設定した場合、残りがデフォルト値になることを確認する"""
    config = ScrapingConfig(request_timeout=60)
    assert config.netkeiba_base_url == "https://db.netkeiba.com"
    assert config.request_timeout == 60


def test_headers_default_not_shared() -> None:
    """異なるインスタンスのheadersが独立していることを確認する"""
    config1 = ScrapingConfig()
    config2 = ScrapingConfig()
    config1.headers["X-Custom"] = "test"
    assert "X-Custom" not in config2.headers
