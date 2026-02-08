"""race_id_to_race_infoの単体テスト"""

import pytest

from scraping.utils import race_id_to_race_info


# 正常系
@pytest.mark.parametrize(
    "race_id, expected_year, expected_keibajo, expected_kai, expected_day, expected_race",
    [
        ("202409030411", 2024, "阪神", 3, 4, 11),
        ("202305050112", 2023, "東京", 5, 1, 12),
        ("202501010101", 2025, "札幌", 1, 1, 1),
        ("202010010201", 2020, "小倉", 1, 2, 1),
    ],
)
def test_race_id_to_race_info_normal(
    race_id: str,
    expected_year: int,
    expected_keibajo: str,
    expected_kai: int,
    expected_day: int,
    expected_race: int,
) -> None:
    """レースIDから年・競馬場・回・日・Rが正しく抽出されることを確認する"""
    year, keibajo, kai, day, race = race_id_to_race_info(race_id)
    assert year == expected_year
    assert keibajo == expected_keibajo
    assert kai == expected_kai
    assert day == expected_day
    assert race == expected_race


def test_race_id_to_race_info_returns_tuple() -> None:
    """戻り値がタプルであることを確認する"""
    result = race_id_to_race_info("202409030411")
    assert isinstance(result, tuple)
    assert len(result) == 5


# 準正常系
def test_race_id_to_race_info_unknown_keibajo() -> None:
    """存在しない競馬場IDの場合にKeyErrorが発生することを確認する"""
    with pytest.raises(KeyError):
        race_id_to_race_info("202499010101")
