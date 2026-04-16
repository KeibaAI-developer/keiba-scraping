"""異常区分カラムの単体テスト

着順カラムの値から異常区分（中止・取消・除外・失格・降着）を正しく判定できることを検証する。
"""

from typing import Any

import pytest

from .conftest import create_scraper_from_fixture

# ---------------------------------------------------------------------------
# 正常系: 異常区分の値が正しいこと
# ---------------------------------------------------------------------------
ABNORMALITY_CASES: list[dict[str, Any]] = [
    # タイトルホルダー: 天皇賞(春)で競走中止 (index=3)
    {
        "horse_id": "2018103559",
        "row_index": 3,
        "expected_abnormality": "中止",
        "description": "タイトルホルダー_中止",
    },
    # ゴンバデカーブース: ホープフルSで出走取消 (index=6)
    {
        "horse_id": "2021104825",
        "row_index": 6,
        "expected_abnormality": "取消",
        "description": "ゴンバデカーブース_取消",
    },
    # クイーンズウォーク: 競走除外 (index=2)
    {
        "horse_id": "2021105414",
        "row_index": 2,
        "expected_abnormality": "除外",
        "description": "クイーンズウォーク_除外",
    },
    # マウントシャスタ: 失格 (index=16)
    {
        "horse_id": "2009106130",
        "row_index": 16,
        "expected_abnormality": "失格",
        "description": "マウントシャスタ_失格",
    },
    # マウントシャスタ: 中止 (index=6)
    {
        "horse_id": "2009106130",
        "row_index": 6,
        "expected_abnormality": "中止",
        "description": "マウントシャスタ_中止",
    },
    # クリノガイディー: 降着 (index=20)
    {
        "horse_id": "2016103690",
        "row_index": 20,
        "expected_abnormality": "降着",
        "description": "クリノガイディー_降着",
    },
]


@pytest.mark.parametrize(
    "case",
    ABNORMALITY_CASES,
    ids=[c["description"] for c in ABNORMALITY_CASES],
)
def test_abnormality_value(case: dict[str, Any]) -> None:
    """異常区分が正しく判定されること"""
    scraper = create_scraper_from_fixture(case["horse_id"])
    df = scraper.get_past_performances()

    row = df.iloc[case["row_index"]]
    assert (
        row["異常区分"] == case["expected_abnormality"]
    ), f"異常区分が不正: {row['異常区分']} != {case['expected_abnormality']}"


# ---------------------------------------------------------------------------
# 正常系: 異常なしの場合は空文字であること
# ---------------------------------------------------------------------------
NORMAL_CASES: list[dict[str, Any]] = [
    # ミュージアムマイル: 全レース正常
    {
        "horse_id": "2022105081",
        "row_index": 0,
        "description": "ミュージアムマイル_正常",
    },
    # タイトルホルダー: 正常レース (index=0)
    {
        "horse_id": "2018103559",
        "row_index": 0,
        "description": "タイトルホルダー_正常",
    },
    # クリノガイディー: 正常レース (index=0)
    {
        "horse_id": "2016103690",
        "row_index": 0,
        "description": "クリノガイディー_正常",
    },
    # マウントシャスタ: 正常レース (index=0)
    {
        "horse_id": "2009106130",
        "row_index": 0,
        "description": "マウントシャスタ_正常",
    },
]


@pytest.mark.parametrize(
    "case",
    NORMAL_CASES,
    ids=[c["description"] for c in NORMAL_CASES],
)
def test_normal_order_has_empty_abnormality(case: dict[str, Any]) -> None:
    """正常な着順の場合、異常区分が空文字であること"""
    scraper = create_scraper_from_fixture(case["horse_id"])
    df = scraper.get_past_performances()

    row = df.iloc[case["row_index"]]
    assert row["異常区分"] == "", f"異常区分が空文字でない: {row['異常区分']}"


# ---------------------------------------------------------------------------
# 正常系: 全レースが正常な馬では異常区分がすべて空文字であること
# ---------------------------------------------------------------------------
def test_all_normal_horse_has_no_abnormality() -> None:
    """ミュージアムマイルは全レースで異常区分が空文字であること"""
    scraper = create_scraper_from_fixture("2022105081")
    df = scraper.get_past_performances()

    assert (df["異常区分"] == "").all(), "異常区分に空文字でない値があります"


# ---------------------------------------------------------------------------
# 正常系: 降着時の着順が数値として正しく取得できること
# ---------------------------------------------------------------------------
def test_kouchaku_order_is_numeric() -> None:
    """クリノガイディーの降着レース(index=20)の着順が数値4であること"""
    scraper = create_scraper_from_fixture("2016103690")
    df = scraper.get_past_performances()

    row = df.iloc[20]
    assert row["着順"] == 4, f"降着時の着順が不正: {row['着順']}"
    assert row["異常区分"] == "降着"


# ---------------------------------------------------------------------------
# 正常系: 異常区分の値がenum的に正しいこと
# ---------------------------------------------------------------------------
VALID_ABNORMALITY_VALUES = {"", "中止", "取消", "除外", "失格", "降着"}


@pytest.mark.parametrize(
    "horse_id",
    [
        "2022105081",
        "2018103559",
        "2021105414",
        "2021104825",
        "2016103690",
        "2009106130",
    ],
    ids=[
        "ミュージアムマイル",
        "タイトルホルダー",
        "クイーンズウォーク",
        "ゴンバデカーブース",
        "クリノガイディー",
        "マウントシャスタ",
    ],
)
def test_abnormality_values_are_valid(horse_id: str) -> None:
    """異常区分の値が許容される値のいずれかであること"""
    scraper = create_scraper_from_fixture(horse_id)
    df = scraper.get_past_performances()

    actual = set(df["異常区分"].unique())
    assert (
        actual <= VALID_ABNORMALITY_VALUES
    ), f"不正な異常区分: {actual - VALID_ABNORMALITY_VALUES}"
