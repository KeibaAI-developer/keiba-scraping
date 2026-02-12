"""ResultPageScraper.get_corner()の単体テスト

requestsをモックし、フィクスチャHTMLを返すようにしてテストする。
コーナー通過順位の取得を検証する。
"""

from typing import Any

import numpy as np
import pandas as pd
import pytest

from scraping.config import CORNER_COLUMNS

from .conftest import collect_result_fixture_race_ids, create_scraper_from_fixture

RESULT_RACE_IDS = collect_result_fixture_race_ids()


# ---------------------------------------------------------------------------
# 正常系: 全フィクスチャ共通テスト
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("race_id", RESULT_RACE_IDS, ids=RESULT_RACE_IDS)
def test_columns_match_corner_columns(race_id: str) -> None:
    """カラム構成がCORNER_COLUMNSと一致すること"""
    scraper = create_scraper_from_fixture(race_id)
    corner_df = scraper.get_corner()

    assert isinstance(corner_df, pd.DataFrame)
    assert list(corner_df.columns) == CORNER_COLUMNS


@pytest.mark.parametrize("race_id", RESULT_RACE_IDS, ids=RESULT_RACE_IDS)
def test_returns_single_row(race_id: str) -> None:
    """常に1行のDataFrameを返すこと"""
    scraper = create_scraper_from_fixture(race_id)
    corner_df = scraper.get_corner()

    assert len(corner_df) == 1


@pytest.mark.parametrize("race_id", RESULT_RACE_IDS, ids=RESULT_RACE_IDS)
def test_race_id_matches(race_id: str) -> None:
    """レースIDがコンストラクタで渡したrace_idと一致すること"""
    scraper = create_scraper_from_fixture(race_id)
    corner_df = scraper.get_corner()

    assert corner_df["レースID"].iloc[0] == race_id


@pytest.mark.parametrize("race_id", RESULT_RACE_IDS, ids=RESULT_RACE_IDS)
def test_four_corner_not_nan(race_id: str) -> None:
    """4コーナー通過順はすべてのレースでNaNにならないこと（直線レースを除く）"""
    # 直線レースはコーナーがないため除外
    if race_id == "202504020407":
        pytest.skip("直線レースはコーナーなし")

    scraper = create_scraper_from_fixture(race_id)
    corner_df = scraper.get_corner()

    assert pd.notna(corner_df["4コーナー通過順"].iloc[0])


@pytest.mark.parametrize("race_id", RESULT_RACE_IDS, ids=RESULT_RACE_IDS)
def test_corner_values_are_str_or_nan(race_id: str) -> None:
    """コーナー通過順の値がstrまたはNaNであること"""
    scraper = create_scraper_from_fixture(race_id)
    corner_df = scraper.get_corner()

    for col in ["1コーナー通過順", "2コーナー通過順", "3コーナー通過順", "4コーナー通過順"]:
        value = corner_df[col].iloc[0]
        assert isinstance(value, str) or (isinstance(value, float) and np.isnan(value))


# ---------------------------------------------------------------------------
# 正常系: 4コーナーすべてある場合
# ---------------------------------------------------------------------------
EXPECTED_4_CORNERS: list[dict[str, Any]] = [
    # 日本ダービー2025: 4コーナーすべてあり
    {
        "race_id": "202505021211",
        "1コーナー通過順": "(18,*14)-2,13(6,8,16)-(9,17)1,7,5,12(3,11)4,10=15",
        "2コーナー通過順": "14-18(2,13)16(6,8)(1,9,17)(5,7)-12(3,11)4,10=15",
        "3コーナー通過順": "14=(18,13)(2,16)8(6,17)(1,9)7,5,12-(3,11)(4,10)15",
        "4コーナー通過順": "14-18,13(2,16)8(6,17)9(1,7)(5,12)-(3,11)(4,10)15",
    },
    # NHKマイルC2023: 4コーナーすべてあり
    {
        "race_id": "202305050812",
        "1コーナー通過順": "8-3-2-(1,17)(5,14)(7,4,15)(10,13)9,6(11,12)-16-18",
        "2コーナー通過順": "8=3-2-(1,17)(5,14)(7,4,15)-(10,13)-9-6(11,12)-16-18",
        "3コーナー通過順": "8=3,2(1,17)(5,14)(4,15)7(10,13)9,6,11-(16,12)-18",
        "4コーナー通過順": "8=3,2(1,17)(5,14,15)4,7(9,10)13,6(11,16)-12-18",
    },
    # 中山大障害2024（障害レース）: 4コーナーすべてあり
    {
        "race_id": "202406050710",
        "1コーナー通過順": "1-(5,9)-(4,8)2,6-7=3",
        "2コーナー通過順": "1,5(4,8,9)2-6-7=3",
        "3コーナー通過順": "(5,*8)1-(4,2)-6-7-9=3",
        "4コーナー通過順": "8-5=(4,2)=7=9   1,3,6",
    },
    # 3歳未勝利2025: 4コーナーすべてあり
    {
        "race_id": "202504030203",
        "1コーナー通過順": "(*7,11)-4,10(3,14)(8,16)(6,12)(1,9)17,15-2,5,13",
        "2コーナー通過順": "7,11-(4,10)(3,14)(8,16)(6,12)1,9,17,15-2,5-13",
        "3コーナー通過順": "(*7,11,10)(4,14,12)(3,8,16,6)1(17,15)(9,2)5,13",
        "4コーナー通過順": "(*7,11)10(4,14,12)(3,8,16,6)(1,15)(17,2)(9,5)13",
    },
]


@pytest.mark.parametrize(
    "expected",
    EXPECTED_4_CORNERS,
    ids=[e["race_id"] for e in EXPECTED_4_CORNERS],
)
def test_expected_4_corner_values(expected: dict[str, Any]) -> None:
    """4コーナーすべてある場合の具体的な値を検証する"""
    scraper = create_scraper_from_fixture(expected["race_id"])
    corner_df = scraper.get_corner()

    for col in ["1コーナー通過順", "2コーナー通過順", "3コーナー通過順", "4コーナー通過順"]:
        assert (
            corner_df[col].iloc[0] == expected[col]
        ), f"{col}: '{corner_df[col].iloc[0]}' != '{expected[col]}'"


# ---------------------------------------------------------------------------
# 正常系: コーナーが一部NaNの場合
# ---------------------------------------------------------------------------
EXPECTED_PARTIAL_CORNERS: list[dict[str, Any]] = [
    # フェアリーS2023（1200m）: 3・4コーナーのみ
    {
        "race_id": "202301020809",
        "1コーナー通過順": np.nan,
        "2コーナー通過順": np.nan,
        "3コーナー通過順": "(*3,13)1,11(9,5)(2,14)-12(10,6)(8,7)4",
        "4コーナー通過順": "(*3,13)1,11,9,5,14(8,2,6)-(12,10)=7,4",
    },
    # 5頭立て（1200m）: 2・3・4コーナーのみ
    {
        "race_id": "202505020607",
        "1コーナー通過順": np.nan,
        "2コーナー通過順": "5,1(2,4)3",
        "3コーナー通過順": "(*5,1)-4,2,3",
        "4コーナー通過順": "(*5,1)(4,3)-2",
    },
    # ラジオNIKKEI賞2025（1800m）: 3・4コーナーのみ
    {
        "race_id": "202504030411",
        "1コーナー通過順": np.nan,
        "2コーナー通過順": np.nan,
        "3コーナー通過順": "11(4,10)17(1,7,15)2(5,14)(9,12)(8,16)13,3   6",
        "4コーナー通過順": "11(4,10)15(17,1,7)(2,14)(9,5)12(8,16)13,3   6",
    },
    # 目黒記念2025（2500m）: 2・3・4コーナーのみ
    {
        "race_id": "202505040109",
        "1コーナー通過順": np.nan,
        "2コーナー通過順": "(*5,12)(4,6)(9,10)7-(2,11)8-1-3",
        "3コーナー通過順": "(*5,12)-(4,6)-(9,10)7-2,11-(8,1)-3",
        "4コーナー通過順": "(*5,12)=6,4-(9,10)7-2-11(8,1)-3",
    },
    # 3着同着3頭（1200m）: 3・4コーナーのみ
    {
        "race_id": "202009050712",
        "1コーナー通過順": np.nan,
        "2コーナー通過順": np.nan,
        "3コーナー通過順": "17-(11,15)(4,16)12,18(2,14)(8,13)(1,6)10,5(3,7)-9",
        "4コーナー通過順": "17-(11,16)(15,18)(4,12)(8,13)14(2,6)(1,10)7(5,3)9",
    },
]


@pytest.mark.parametrize(
    "expected",
    EXPECTED_PARTIAL_CORNERS,
    ids=[e["race_id"] for e in EXPECTED_PARTIAL_CORNERS],
)
def test_expected_partial_corner_values(expected: dict[str, Any]) -> None:
    """コーナーが一部NaNの場合の具体的な値を検証する"""
    scraper = create_scraper_from_fixture(expected["race_id"])
    corner_df = scraper.get_corner()

    for col in ["1コーナー通過順", "2コーナー通過順", "3コーナー通過順", "4コーナー通過順"]:
        expected_value = expected[col]
        actual_value = corner_df[col].iloc[0]
        if isinstance(expected_value, float) and np.isnan(expected_value):
            assert isinstance(actual_value, float) and np.isnan(
                actual_value
            ), f"{col}: '{actual_value}'がNaNではありません"
        else:
            assert actual_value == expected_value, f"{col}: '{actual_value}' != '{expected_value}'"


# ---------------------------------------------------------------------------
# 正常系: 直線レース（コーナーなし）
# ---------------------------------------------------------------------------
def test_straight_race_all_corners_nan() -> None:
    """直線レース（アイビスSD2025）はすべてのコーナーがNaNになること"""
    scraper = create_scraper_from_fixture("202504020407")
    corner_df = scraper.get_corner()

    assert len(corner_df) == 1
    assert list(corner_df.columns) == CORNER_COLUMNS
    assert corner_df["レースID"].iloc[0] == "202504020407"

    for col in ["1コーナー通過順", "2コーナー通過順", "3コーナー通過順", "4コーナー通過順"]:
        assert pd.isna(corner_df[col].iloc[0]), f"{col}がNaNではありません"
