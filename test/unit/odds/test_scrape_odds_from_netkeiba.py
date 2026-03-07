"""scrape_odds_from_netkeibaの単体テスト"""

import json
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
import pytest

from scraping.config import ODDS_COLUMNS
from scraping.odds import scrape_odds_from_netkeiba


@pytest.fixture
def fixtures_json_dir() -> Path:
    """JSONフィクスチャディレクトリのパスを返す"""
    return Path(__file__).parent.parent.parent / "fixtures" / "json"


@pytest.fixture
def odds_json_after_sale(fixtures_json_dir: Path) -> dict[str, Any]:
    """馬券発売後のオッズJSONフィクスチャ（出走取消あり）"""
    json_path = fixtures_json_dir / "odds_netkeiba_202306050911.json"
    with open(json_path, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def odds_json_before_sale(fixtures_json_dir: Path) -> dict[str, Any]:
    """馬券発売前のオッズJSONフィクスチャ"""
    json_path = fixtures_json_dir / "odds_netkeiba_202606020411.json"
    with open(json_path, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def odds_json_normal(fixtures_json_dir: Path) -> dict[str, Any]:
    """馬券発売後・正常系のオッズJSONフィクスチャ"""
    json_path = fixtures_json_dir / "odds_netkeiba_202606020211.json"
    with open(json_path, encoding="utf-8") as f:
        return json.load(f)


# 正常系
def test_scrape_odds_from_netkeiba_returns_dataframe_with_correct_columns(
    odds_json_after_sale: dict[str, Any],
) -> None:
    """戻り値がODDS_COLUMNSのカラムを持つDataFrameであること"""
    with patch("scraping.odds.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = odds_json_after_sale
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = scrape_odds_from_netkeiba("202306050911")

        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ODDS_COLUMNS


def test_scrape_odds_from_netkeiba_extracts_tansho_odds(
    odds_json_after_sale: dict[str, Any],
) -> None:
    """単勝オッズが正しく抽出されること"""
    with patch("scraping.odds.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = odds_json_after_sale
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = scrape_odds_from_netkeiba("202306050911")

        # 馬番2の単勝オッズは14.3
        umaban_2 = result[result["馬番"] == 2].iloc[0]
        assert umaban_2["単勝オッズ"] == 14.3


def test_scrape_odds_from_netkeiba_extracts_fukusho_odds(
    odds_json_after_sale: dict[str, Any],
) -> None:
    """複勝オッズが正しく抽出されること"""
    with patch("scraping.odds.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = odds_json_after_sale
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = scrape_odds_from_netkeiba("202306050911")

        # 馬番2の複勝オッズは2.6-4.3
        umaban_2 = result[result["馬番"] == 2].iloc[0]
        assert umaban_2["複勝最小オッズ"] == 2.6
        assert umaban_2["複勝最大オッズ"] == 4.3


def test_scrape_odds_from_netkeiba_extracts_ninki(
    odds_json_after_sale: dict[str, Any],
) -> None:
    """人気が正しく抽出されること"""
    with patch("scraping.odds.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = odds_json_after_sale
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = scrape_odds_from_netkeiba("202306050911")

        # 馬番2の単勝人気は5
        umaban_2 = result[result["馬番"] == 2].iloc[0]
        assert umaban_2["単勝人気"] == 5


def test_scrape_odds_from_netkeiba_rows_sorted_by_umaban(
    odds_json_after_sale: dict[str, Any],
) -> None:
    """馬番順にソートされていること"""
    with patch("scraping.odds.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = odds_json_after_sale
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = scrape_odds_from_netkeiba("202306050911")

        umaban_list = result["馬番"].tolist()
        assert umaban_list == sorted(umaban_list)


def test_scrape_odds_from_netkeiba_no_data_returns_empty_dataframe(
    odds_json_before_sale: dict[str, Any],
) -> None:
    """馬券発売前は空のDataFrameを返すこと"""
    with patch("scraping.odds.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = odds_json_before_sale
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = scrape_odds_from_netkeiba("202606020411")

        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ODDS_COLUMNS
        assert len(result) == 0


# 準正常系
def test_scrape_odds_from_netkeiba_cancel_horse_has_nan_odds(
    odds_json_after_sale: dict[str, Any],
) -> None:
    """出走取消馬のオッズがNaNであること"""
    with patch("scraping.odds.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = odds_json_after_sale
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = scrape_odds_from_netkeiba("202306050911")

        # 馬番1は出走取消（オッズが-3.0）
        umaban_1 = result[result["馬番"] == 1].iloc[0]
        assert np.isnan(umaban_1["単勝オッズ"])
        assert np.isnan(umaban_1["複勝最小オッズ"])
        assert np.isnan(umaban_1["複勝最大オッズ"])


def test_scrape_odds_from_netkeiba_cancel_horse_has_nan_ninki(
    odds_json_after_sale: dict[str, Any],
) -> None:
    """出走取消馬の人気がNaNであること"""
    with patch("scraping.odds.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = odds_json_after_sale
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = scrape_odds_from_netkeiba("202306050911")

        # 馬番1は出走取消（人気が9999）
        umaban_1 = result[result["馬番"] == 1].iloc[0]
        assert np.isnan(umaban_1["単勝人気"])
        assert np.isnan(umaban_1["複勝人気"])
