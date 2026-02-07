"""URL構築関数の単体テスト"""

import pytest

from scraping.config import ScrapingConfig
from scraping.utils import (
    build_entry_url,
    build_horse_info_url,
    build_horse_list_url,
    build_race_list_url,
    build_result_url,
    build_today_race_list_url,
)


@pytest.fixture()
def default_config() -> ScrapingConfig:
    """デフォルト設定を返すフィクスチャ"""
    return ScrapingConfig()


@pytest.fixture()
def custom_config() -> ScrapingConfig:
    """カスタム設定を返すフィクスチャ"""
    return ScrapingConfig(
        netkeiba_base_url="https://custom-db.netkeiba.com",
        netkeiba_race_url="https://custom-race.netkeiba.com",
    )


# 正常系
def test_build_race_list_url_default(default_config: ScrapingConfig) -> None:
    """デフォルト設定でレース一覧URLが正しく構築されることを確認する"""
    url = build_race_list_url(2024, 1, default_config)
    assert "db.netkeiba.com" in url
    assert "start_year=2024" in url
    assert "end_year=2024" in url
    assert "page=1" in url


def test_build_race_list_url_none_config() -> None:
    """configがNoneでもデフォルト値でURLが構築されることを確認する"""
    url = build_race_list_url(2024, 1)
    assert "db.netkeiba.com" in url
    assert "start_year=2024" in url


def test_build_race_list_url_custom(custom_config: ScrapingConfig) -> None:
    """カスタム設定でレース一覧URLが正しく構築されることを確認する"""
    url = build_race_list_url(2024, 3, custom_config)
    assert "custom-db.netkeiba.com" in url
    assert "page=3" in url


def test_build_today_race_list_url_default(default_config: ScrapingConfig) -> None:
    """日別レース一覧URLが正しく構築されることを確認する"""
    url = build_today_race_list_url(2024, 6, 15, default_config)
    assert "race.netkeiba.com" in url
    assert "kaisai_date=20240615" in url


@pytest.mark.parametrize(
    "month, day, expected_date",
    [
        (1, 5, "20240105"),
        (12, 31, "20241231"),
        (3, 1, "20240301"),
    ],
)
def test_build_today_race_list_url_date_formatting(
    month: int, day: int, expected_date: str
) -> None:
    """月日が0埋め2桁で正しくフォーマットされることを確認する"""
    url = build_today_race_list_url(2024, month, day)
    assert f"kaisai_date={expected_date}" in url


def test_build_result_url_default(default_config: ScrapingConfig) -> None:
    """結果ページURLが正しく構築されることを確認する"""
    url = build_result_url("202409030411", default_config)
    assert "race.netkeiba.com" in url
    assert "race_id=202409030411" in url
    assert "result.html" in url


def test_build_entry_url_default(default_config: ScrapingConfig) -> None:
    """出馬表ページURLが正しく構築されることを確認する"""
    url = build_entry_url("202409030411", default_config)
    assert "race.netkeiba.com" in url
    assert "race_id=202409030411" in url
    assert "shutuba.html" in url


def test_build_horse_info_url_default(default_config: ScrapingConfig) -> None:
    """馬情報ページURLが正しく構築されることを確認する"""
    url = build_horse_info_url("2021104956", default_config)
    assert "db.netkeiba.com" in url
    assert "horse/2021104956" in url


def test_build_horse_list_url_default(default_config: ScrapingConfig) -> None:
    """競走馬一覧ページURLが正しく構築されることを確認する"""
    url = build_horse_list_url(2021, 2, default_config)
    assert "db.netkeiba.com" in url
    assert "birthyear=2021" in url
    assert "page=2" in url


def test_build_horse_info_url_custom(custom_config: ScrapingConfig) -> None:
    """カスタム設定で馬情報ページURLが構築されることを確認する"""
    url = build_horse_info_url("2021104956", custom_config)
    assert "custom-db.netkeiba.com" in url
