"""calc_intervalの単体テスト"""

import numpy as np
import pytest

from scraping.utils import calc_interval


# 正常系
@pytest.mark.parametrize(
    "date1, date2, expected",
    [
        ("2024/06/23", "2024/05/12", 42),
        ("2024/01/01", "2024/12/31", 365),
        ("2023/03/01", "2023/03/01", 0),
        ("2024/05/12", "2024/06/23", 42),  # 逆順でも同じ結果
    ],
)
def test_calc_interval_normal(date1: str, date2: str, expected: int) -> None:
    """日付間隔が正しく計算されることを確認する"""
    assert calc_interval(date1, date2) == expected


# 正常系 - 同日のレース
def test_calc_interval_same_day() -> None:
    """同日の場合に0が返ることを確認する"""
    assert calc_interval("2024/06/23", "2024/06/23") == 0


# 準正常系 - 不正なフォーマット
@pytest.mark.parametrize(
    "date1, date2",
    [
        ("invalid", "2024/06/23"),
        ("2024/06/23", "invalid"),
        ("20240623", "2024/06/23"),
    ],
)
def test_calc_interval_invalid_format_returns_nan(date1: str, date2: str) -> None:
    """不正な日付フォーマットの場合にNaNが返ることを確認する"""
    result = calc_interval(date1, date2)
    assert np.isnan(result)
