"""judge_turf_dirtの単体テスト"""

import pytest

from scraping.utils import judge_turf_dirt


# 正常系
@pytest.mark.parametrize(
    "input_text, expected",
    [
        ("芝1600m", "芝"),
        ("ダ1200m", "ダ"),
        ("障3000m", "障"),
        ("芝", "芝"),
        ("ダ", "ダ"),
        ("障", "障"),
        ("芝右 2000m", "芝"),
        ("ダ左 1800m", "ダ"),
        ("障芝3380m", "障"),
    ],
)
def test_judge_turf_dirt_normal(input_text: str, expected: str) -> None:
    """芝・ダ・障が正しく判定されることを確認する"""
    assert judge_turf_dirt(input_text) == expected


# 準正常系
def test_judge_turf_dirt_unknown_text() -> None:
    """不明な文字列の場合に空文字が返ることを確認する"""
    assert judge_turf_dirt("不明な文字列") == ""


def test_judge_turf_dirt_empty_string() -> None:
    """空文字の場合に空文字が返ることを確認する"""
    assert judge_turf_dirt("") == ""


# 正常系 - 優先順位
def test_judge_turf_dirt_steeplechase_priority() -> None:
    """障が芝より優先されることを確認する"""
    assert judge_turf_dirt("障芝") == "障"
