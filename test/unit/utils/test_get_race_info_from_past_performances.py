"""get_race_info_from_past_performancesの単体テスト"""

import numpy as np
import pandas as pd
import pytest

from scraping.utils import get_race_info_from_past_performances


@pytest.fixture()
def central_past_performances_df() -> pd.DataFrame:
    """中央競馬の馬柱データを返すフィクスチャ"""
    return pd.DataFrame(
        {
            "日付": ["2024/06/23", "2024/05/12", "2024/03/10"],
            "競馬場": ["阪神", "東京", "中山"],
            "回": [3, 2, 1],
            "日": [4, 3, 2],
            "R": [11, 10, 5],
            "人気": [1, 3, 2],
        }
    )


@pytest.fixture()
def local_past_performances_df() -> pd.DataFrame:
    """地方競馬の馬柱データを返すフィクスチャ"""
    return pd.DataFrame(
        {
            "日付": ["2024/07/10", "2024/06/05"],
            "競馬場": ["大井", "大井"],
            "回": [np.nan, np.nan],
            "日": [np.nan, np.nan],
            "R": [8, 5],
            "人気": [2, 1],
        }
    )


@pytest.fixture()
def overseas_past_performances_df() -> pd.DataFrame:
    """海外レースの馬柱データを返すフィクスチャ"""
    return pd.DataFrame(
        {
            "日付": ["2024/10/01", "2024/06/23"],
            "競馬場": ["ロンシャン", "阪神"],
            "回": [np.nan, 3],
            "日": [np.nan, 4],
            "R": [np.nan, 11],
            "人気": [5, 1],
        }
    )


# 正常系 - 中央
def test_central_race_id(central_past_performances_df: pd.DataFrame) -> None:
    """中央競馬のレースIDが正しく構築されることを確認する"""
    race_id, organize, interval, keibajo = get_race_info_from_past_performances(
        central_past_performances_df, 0
    )
    assert race_id == "202409030411"
    assert organize == "中央"
    assert keibajo == "阪神"


def test_central_race_interval(central_past_performances_df: pd.DataFrame) -> None:
    """中央競馬のレース間隔が正しく計算されることを確認する"""
    _, _, interval, _ = get_race_info_from_past_performances(central_past_performances_df, 0)
    # 2024/06/23 - 2024/05/12 = 42日
    assert interval == 42


# 正常系 - 地方
def test_local_race_id(local_past_performances_df: pd.DataFrame) -> None:
    """地方競馬のレースIDが正しく構築されることを確認する"""
    race_id, organize, interval, keibajo = get_race_info_from_past_performances(
        local_past_performances_df, 0
    )
    # 地方: year + keibajo_id + month + day + race_num
    assert race_id == "202444071008"
    assert organize == "地方"
    assert keibajo == "大井"


def test_local_race_interval(local_past_performances_df: pd.DataFrame) -> None:
    """地方競馬のレース間隔が正しく計算されることを確認する"""
    _, _, interval, _ = get_race_info_from_past_performances(local_past_performances_df, 0)
    # 2024/07/10 - 2024/06/05 = 35日
    assert interval == 35


# 正常系 - 海外
def test_overseas_race_id(overseas_past_performances_df: pd.DataFrame) -> None:
    """海外レースのレースIDが空文字であることを確認する"""
    race_id, organize, interval, keibajo = get_race_info_from_past_performances(
        overseas_past_performances_df, 0
    )
    assert race_id == ""
    assert organize == "海外"
    assert keibajo == "ロンシャン"


# 正常系 - 最終走（前走なし）
def test_last_race_interval_is_nan(central_past_performances_df: pd.DataFrame) -> None:
    """最終走（これ以上遡れない）の間隔がNaNであることを確認する"""
    _, _, interval, _ = get_race_info_from_past_performances(central_past_performances_df, 2)
    assert np.isnan(interval)


# 準正常系 - 空の馬柱
def test_empty_past_performances_raises_error() -> None:
    """空の馬柱でValueErrorが発生することを確認する"""
    empty_df = pd.DataFrame(columns=["日付", "競馬場", "回", "日", "R", "人気"])
    with pytest.raises(ValueError, match="馬柱が1行もありません"):
        get_race_info_from_past_performances(empty_df, 0)
