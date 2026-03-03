"""定数辞書の単体テスト"""

import pytest

from scraping.config import (
    ENTRY_COLUMNS,
    GRADE_DICT,
    HORSE_INFO_COLUMNS,
    ID_TO_KEIBAJO_DICT,
    KEIBAJO_TO_ID_DICT,
    PAST_PERFORMANCES_COLUMNS,
    PAYBACK_COLUMNS,
    RACE_INFO_COLUMNS,
    RACE_SCHEDULE_COLUMNS,
    RESULT_COLUMNS,
    THREE_COMBINATION_BETS,
    TWO_COMBINATION_BETS,
    WEIGHT_CONDITIONS,
)


# 正常系 - 競馬場辞書
def test_keibajo_to_id_dict_contains_central_tracks() -> None:
    """中央10競馬場がすべて含まれていることを確認する"""
    central_tracks = [
        "札幌",
        "函館",
        "福島",
        "新潟",
        "東京",
        "中山",
        "中京",
        "京都",
        "阪神",
        "小倉",
    ]
    for track in central_tracks:
        assert track in KEIBAJO_TO_ID_DICT


def test_keibajo_to_id_dict_central_ids() -> None:
    """中央10競馬場のIDが01～10であることを確認する"""
    central_tracks = [
        "札幌",
        "函館",
        "福島",
        "新潟",
        "東京",
        "中山",
        "中京",
        "京都",
        "阪神",
        "小倉",
    ]
    expected_ids = [f"{i:02}" for i in range(1, 11)]
    actual_ids = [KEIBAJO_TO_ID_DICT[t] for t in central_tracks]
    assert actual_ids == expected_ids


def test_id_to_keibajo_dict_reverse_consistency() -> None:
    """ID→競馬場辞書が競馬場→ID辞書の逆引きと一致することを確認する"""
    for keibajo, keibajo_id in KEIBAJO_TO_ID_DICT.items():
        assert ID_TO_KEIBAJO_DICT[keibajo_id] == keibajo


def test_id_to_keibajo_dict_same_length() -> None:
    """双方向辞書の要素数が一致することを確認する"""
    assert len(KEIBAJO_TO_ID_DICT) == len(ID_TO_KEIBAJO_DICT)


@pytest.mark.parametrize(
    "keibajo_id, expected_keibajo",
    [
        ("01", "札幌"),
        ("05", "東京"),
        ("10", "小倉"),
        ("44", "大井"),
    ],
)
def test_id_to_keibajo_dict_lookup(keibajo_id: str, expected_keibajo: str) -> None:
    """ID→競馬場の個別変換が正しいことを確認する"""
    assert ID_TO_KEIBAJO_DICT[keibajo_id] == expected_keibajo


# 正常系 - グレード辞書
def test_grade_dict_values() -> None:
    """グレード辞書の値が正しいことを確認する"""
    assert GRADE_DICT["1"] == "G1"
    assert GRADE_DICT["2"] == "G2"
    assert GRADE_DICT["3"] == "G3"


def test_grade_dict_length() -> None:
    """グレード辞書が12要素であることを確認する"""
    assert len(GRADE_DICT) == 12


# 正常系 - 斤量条件
def test_weight_conditions_contains_all() -> None:
    """斤量条件が4種類すべて含まれていることを確認する"""
    assert "定量" in WEIGHT_CONDITIONS
    assert "別定" in WEIGHT_CONDITIONS
    assert "ハンデ" in WEIGHT_CONDITIONS
    assert "馬齢" in WEIGHT_CONDITIONS
    assert len(WEIGHT_CONDITIONS) == 4


# 正常系 - 払い戻し表カラム
def test_payback_columns() -> None:
    """払い戻し表のカラムが正しいことを確認する"""
    assert PAYBACK_COLUMNS == ["券種", "馬番", "払戻", "人気"]


# 正常系 - 馬券名称リスト
def test_two_combination_bets() -> None:
    """2連系馬券が正しく定義されていることを確認する"""
    assert TWO_COMBINATION_BETS == ["枠連", "馬連", "ワイド", "馬単"]


def test_three_combination_bets() -> None:
    """3連系馬券が正しく定義されていることを確認する"""
    assert THREE_COMBINATION_BETS == ["3連複", "3連単"]


# 正常系 - カラム定義のデータ型と空でないこと
@pytest.mark.parametrize(
    "columns",
    [
        RESULT_COLUMNS,
        ENTRY_COLUMNS,
        RACE_INFO_COLUMNS,
        PAST_PERFORMANCES_COLUMNS,
        HORSE_INFO_COLUMNS,
        RACE_SCHEDULE_COLUMNS,
    ],
)
def test_column_definitions_are_non_empty_list_of_str(columns: list[str]) -> None:
    """各カラム定義がstr要素の非空リストであることを確認する"""
    assert isinstance(columns, list)
    assert len(columns) > 0
    assert all(isinstance(col, str) for col in columns)


# 正常系 - カラム定義の重複チェック
@pytest.mark.parametrize(
    "columns",
    [
        RESULT_COLUMNS,
        ENTRY_COLUMNS,
        RACE_INFO_COLUMNS,
        PAST_PERFORMANCES_COLUMNS,
        HORSE_INFO_COLUMNS,
        RACE_SCHEDULE_COLUMNS,
    ],
)
def test_column_definitions_have_no_duplicates(columns: list[str]) -> None:
    """各カラム定義に重複がないことを確認する"""
    assert len(columns) == len(set(columns))
