"""EntryPageScraper.get_entry()の単体テスト

requestsをモックし、フィクスチャHTMLを返すようにしてテストする。
出馬表テーブルの取得・バリデーションを検証する。
"""

from typing import Any
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from scraping.config import ENTRY_COLUMNS

from .conftest import collect_entry_fixture_race_ids, create_scraper_from_fixture

ENTRY_RACE_IDS = collect_entry_fixture_race_ids()


# ---------------------------------------------------------------------------
# 正常系: 全フィクスチャ共通テスト
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("race_id", ENTRY_RACE_IDS, ids=ENTRY_RACE_IDS)
def test_columns_match_entry_columns(race_id: str) -> None:
    """カラム構成がENTRY_COLUMNSと一致すること"""
    scraper = create_scraper_from_fixture(race_id)
    entry_df = scraper.get_entry()

    assert isinstance(entry_df, pd.DataFrame)
    assert list(entry_df.columns) == ENTRY_COLUMNS


@pytest.mark.parametrize("race_id", ENTRY_RACE_IDS, ids=ENTRY_RACE_IDS)
def test_race_id_matches(race_id: str) -> None:
    """全行のレースIDがコンストラクタで渡したrace_idと一致すること"""
    scraper = create_scraper_from_fixture(race_id)
    entry_df = scraper.get_entry()

    assert (entry_df["レースID"] == race_id).all()


@pytest.mark.parametrize("race_id", ENTRY_RACE_IDS, ids=ENTRY_RACE_IDS)
def test_non_nan_columns_valid(race_id: str) -> None:
    """NaN不可カラムにNaNが含まれないこと"""
    scraper = create_scraper_from_fixture(race_id)
    entry_df = scraper.get_entry()

    non_nan_columns = [
        "レースID",
        "出走区分",
        "枠",
        "馬番",
        "馬名",
        "性別",
        "年齢",
        "斤量",
        "騎手",
        "所属",
        "厩舎",
        "馬ID",
        "騎手ID",
        "厩舎ID",
    ]
    for col in non_nan_columns:
        assert entry_df[col].notna().all(), f"'{col}'にNaNが含まれています"


@pytest.mark.parametrize("race_id", ENTRY_RACE_IDS, ids=ENTRY_RACE_IDS)
def test_gender_enum(race_id: str) -> None:
    """性別が牡/牝/セのいずれかであること"""
    scraper = create_scraper_from_fixture(race_id)
    entry_df = scraper.get_entry()

    valid_genders = {"牡", "牝", "セ"}
    actual_genders = set(entry_df["性別"].unique())
    assert actual_genders <= valid_genders, f"不正な性別: {actual_genders - valid_genders}"


@pytest.mark.parametrize("race_id", ENTRY_RACE_IDS, ids=ENTRY_RACE_IDS)
def test_affiliation_enum(race_id: str) -> None:
    """所属が美浦/栗東/地方/海外のいずれかであること"""
    scraper = create_scraper_from_fixture(race_id)
    entry_df = scraper.get_entry()

    valid_affiliations = {"美浦", "栗東", "地方", "海外"}
    actual = set(entry_df["所属"].unique())
    assert actual <= valid_affiliations, f"不正な所属: {actual - valid_affiliations}"


@pytest.mark.parametrize("race_id", ENTRY_RACE_IDS, ids=ENTRY_RACE_IDS)
def test_entry_status_enum(race_id: str) -> None:
    """出走区分が出走/取消/除外のいずれかであること"""
    scraper = create_scraper_from_fixture(race_id)
    entry_df = scraper.get_entry()

    valid_statuses = {"出走", "取消", "除外"}
    actual = set(entry_df["出走区分"].unique())
    assert actual <= valid_statuses, f"不正な出走区分: {actual - valid_statuses}"


@pytest.mark.parametrize("race_id", ENTRY_RACE_IDS, ids=ENTRY_RACE_IDS)
def test_horse_id_10_digits(race_id: str) -> None:
    """馬IDが10桁の文字列であること"""
    scraper = create_scraper_from_fixture(race_id)
    entry_df = scraper.get_entry()

    for horse_id in entry_df["馬ID"]:
        assert len(str(horse_id)) == 10, f"馬IDが10桁ではありません: {horse_id}"


@pytest.mark.parametrize("race_id", ENTRY_RACE_IDS, ids=ENTRY_RACE_IDS)
def test_jockey_id_5_digits(race_id: str) -> None:
    """騎手IDが5桁の文字列であること"""
    scraper = create_scraper_from_fixture(race_id)
    entry_df = scraper.get_entry()

    for jockey_id in entry_df["騎手ID"]:
        assert len(str(jockey_id)) == 5, f"騎手IDが5桁ではありません: {jockey_id}"


@pytest.mark.parametrize("race_id", ENTRY_RACE_IDS, ids=ENTRY_RACE_IDS)
def test_trainer_id_5_digits(race_id: str) -> None:
    """厩舎IDが5桁の文字列であること"""
    scraper = create_scraper_from_fixture(race_id)
    entry_df = scraper.get_entry()

    for trainer_id in entry_df["厩舎ID"]:
        assert len(str(trainer_id)) == 5, f"厩舎IDが5桁ではありません: {trainer_id}"


@pytest.mark.parametrize("race_id", ENTRY_RACE_IDS, ids=ENTRY_RACE_IDS)
def test_trainer_name_has_no_leading_space(race_id: str) -> None:
    """厩舎名に先頭の空白がないこと"""
    scraper = create_scraper_from_fixture(race_id)
    entry_df = scraper.get_entry()

    for trainer in entry_df["厩舎"]:
        assert not trainer.startswith(" "), f"厩舎名に先頭空白があります: '{trainer}'"


# ---------------------------------------------------------------------------
# 正常系: 具体値の検証
# ---------------------------------------------------------------------------
EXPECTED_VALUES: list[dict[str, Any]] = [
    # ダービー2025 1着（クロワデュノール）
    {
        "race_id": "202505021211",
        "馬番": 13,
        "馬名": "クロワデュノール",
        "出走区分": "出走",
        "枠": 7,
        "性別": "牡",
        "年齢": 3,
        "斤量": 57.0,
        "騎手": "北村友",
        "所属": "栗東",
        "厩舎": "斉藤崇",
        "馬体重": 504,
        "増減": 4,
        "馬ID": "2022105102",
        "騎手ID": "01102",
        "厩舎ID": "01151",
    },
    # ダービー2025 18番（サトノシャイニング）
    {
        "race_id": "202505021211",
        "馬番": 18,
        "馬名": "サトノシャイニング",
        "出走区分": "出走",
        "枠": 8,
        "性別": "牡",
        "年齢": 3,
        "斤量": 57.0,
        "騎手": "武豊",
        "所属": "栗東",
        "厩舎": "杉山晴",
        "馬ID": "2022101420",
        "騎手ID": "00666",
        "厩舎ID": "01157",
    },
    # 5頭立て 1番（シンハナーダ）
    {
        "race_id": "202505020607",
        "馬番": 1,
        "馬名": "シンハナーダ",
        "出走区分": "出走",
        "所属": "美浦",
    },
    # 障害レース（中山大障害2024）
    {
        "race_id": "202406050710",
        "馬番": 8,
        "馬名": "ニシノデイジー",
        "出走区分": "出走",
    },
]


@pytest.mark.parametrize(
    "expected",
    EXPECTED_VALUES,
    ids=[f"{e['race_id']}_{e['馬名']}" for e in EXPECTED_VALUES],
)
def test_expected_values(expected: dict[str, Any]) -> None:
    """代表的なレースの具体的な値を検証する"""
    scraper = create_scraper_from_fixture(expected["race_id"])
    entry_df = scraper.get_entry()

    row = entry_df[entry_df["馬番"] == expected["馬番"]].iloc[0]
    for key, value in expected.items():
        if key == "race_id":
            assert row["レースID"] == value
            continue
        actual = row[key]
        if isinstance(value, float) and np.isnan(value):
            assert np.isnan(actual), f"{key}: {actual} != NaN"
        elif isinstance(value, float):
            assert actual == pytest.approx(value), f"{key}: {actual} != {value}"
        else:
            assert actual == value, f"{key}: {actual} != {value}"


# ---------------------------------------------------------------------------
# 正常系: 行数の検証
# ---------------------------------------------------------------------------
EXPECTED_ROW_COUNTS: list[dict[str, Any]] = [
    {"race_id": "202505021211", "expected_rows": 18},
    {"race_id": "202505020607", "expected_rows": 5},
    {"race_id": "202406050710", "expected_rows": 9},
    {"race_id": "202306030111", "expected_rows": 12},
    {"race_id": "202306050911", "expected_rows": 18},
    {"race_id": "202504030411", "expected_rows": 17},
    {"race_id": "202009050712", "expected_rows": 18},
    {"race_id": "201005030211", "expected_rows": 18},
]


@pytest.mark.parametrize(
    "case",
    EXPECTED_ROW_COUNTS,
    ids=[c["race_id"] for c in EXPECTED_ROW_COUNTS],
)
def test_row_count(case: dict[str, Any]) -> None:
    """行数が出走頭数と一致すること"""
    scraper = create_scraper_from_fixture(case["race_id"])
    entry_df = scraper.get_entry()

    assert len(entry_df) == case["expected_rows"]


# ---------------------------------------------------------------------------
# 正常系: 出走区分
# ---------------------------------------------------------------------------
def test_status_normal_race() -> None:
    """通常レース（ダービー2025）では全馬の出走区分が"出走"であること"""
    scraper = create_scraper_from_fixture("202505021211")
    entry_df = scraper.get_entry()

    assert (entry_df["出走区分"] == "出走").all()


def test_status_torikeshi() -> None:
    """鳴尾記念2023で出走取消馬が2頭いること"""
    scraper = create_scraper_from_fixture("202306050911")
    entry_df = scraper.get_entry()

    cancel = entry_df[entry_df["出走区分"] == "取消"]
    assert len(cancel) == 2
    assert set(cancel["馬名"].tolist()) == {"ゴンバデカーブース", "サンライズアース"}


def test_status_torikeshi_count() -> None:
    """鳴尾記念2023で取消2頭・出走16頭であること"""
    scraper = create_scraper_from_fixture("202306050911")
    entry_df = scraper.get_entry()

    assert (entry_df["出走区分"] == "出走").sum() == 16
    assert (entry_df["出走区分"] == "取消").sum() == 2


def test_status_jogai() -> None:
    """ラジオNIKKEI賞2025で競走除外馬（クイーンズウォーク）がいること"""
    scraper = create_scraper_from_fixture("202504030411")
    entry_df = scraper.get_entry()

    jogai = entry_df[entry_df["出走区分"] == "除外"]
    assert len(jogai) == 1
    assert jogai.iloc[0]["馬名"] == "クイーンズウォーク"


# ---------------------------------------------------------------------------
# 正常系: 出走取消馬のNaN条件
# ---------------------------------------------------------------------------
def test_torikeshi_has_nan_weight() -> None:
    """出走取消馬（ゴンバデカーブース）は馬体重がNaNであること"""
    scraper = create_scraper_from_fixture("202306050911")
    entry_df = scraper.get_entry()

    gonba = entry_df[entry_df["馬名"] == "ゴンバデカーブース"].iloc[0]
    assert pd.isna(gonba["馬体重"])
    assert pd.isna(gonba["増減"])


# ---------------------------------------------------------------------------
# 正常系: 競走除外馬のNaN条件
# ---------------------------------------------------------------------------
def test_jogai_has_nan_weight() -> None:
    """競走除外馬（クイーンズウォーク）は馬体重がNaNであること"""
    scraper = create_scraper_from_fixture("202504030411")
    entry_df = scraper.get_entry()

    queen = entry_df[entry_df["馬名"] == "クイーンズウォーク"].iloc[0]
    assert pd.isna(queen["馬体重"])
    assert pd.isna(queen["増減"])


# ---------------------------------------------------------------------------
# 正常系: 所属
# ---------------------------------------------------------------------------
def test_overseas_horse_affiliation() -> None:
    """NHKマイルC2023（海外馬イレジン）の所属が海外であること"""
    scraper = create_scraper_from_fixture("202305050812")
    entry_df = scraper.get_entry()

    irezin = entry_df[entry_df["馬名"] == "イレジン"].iloc[0]
    assert irezin["所属"] == "海外"


def test_local_horse_affiliation() -> None:
    """NHKマイルC2023（地方馬）の所属が地方であること"""
    scraper = create_scraper_from_fixture("202305050812")
    entry_df = scraper.get_entry()

    kurino = entry_df[entry_df["馬名"] == "クリノメガミエース"].iloc[0]
    assert kurino["所属"] == "地方"

    chestnut = entry_df[entry_df["馬名"] == "チェスナットコート"].iloc[0]
    assert chestnut["所属"] == "地方"


# ---------------------------------------------------------------------------
# 正常系: セン馬
# ---------------------------------------------------------------------------
def test_gelding_gender() -> None:
    """NHKマイルC2023のイレジンとフォワードアゲンがセン馬であること"""
    scraper = create_scraper_from_fixture("202305050812")
    entry_df = scraper.get_entry()

    irezin = entry_df[entry_df["馬名"] == "イレジン"].iloc[0]
    assert irezin["性別"] == "セ"

    forward = entry_df[entry_df["馬名"] == "フォワードアゲン"].iloc[0]
    assert forward["性別"] == "セ"


# ---------------------------------------------------------------------------
# 準正常系: バリデーションエラー
# ---------------------------------------------------------------------------
def test_validation_error_on_invalid_gender() -> None:
    """性別が不正な場合にParseErrorが発生すること"""
    from scraping.exceptions import ParseError

    scraper = create_scraper_from_fixture("202505021211")

    scraper.html_text = scraper.html_text.replace("牡3", "X3", 1)
    scraper.soup = __import__("bs4").BeautifulSoup(scraper.html_text, "html.parser")

    with pytest.raises(ParseError, match="性別が不正です"):
        scraper.get_entry()


def test_validation_error_on_invalid_affiliation() -> None:
    """所属が不正な場合にParseErrorが発生すること"""
    from scraping.exceptions import ParseError

    scraper = create_scraper_from_fixture("202505021211")

    scraper.html_text = scraper.html_text.replace(
        '<span class="Label2">栗東</span>', '<span class="Label2">XX</span>', 1
    )
    scraper.soup = __import__("bs4").BeautifulSoup(scraper.html_text, "html.parser")

    with pytest.raises(ParseError, match="所属が不正です"):
        scraper.get_entry()


def test_validation_error_on_invalid_entry_status() -> None:
    """出走区分が不正な場合にParseErrorが発生すること"""
    from scraping.exceptions import ParseError

    scraper = create_scraper_from_fixture("202505021211")

    with patch(
        "scraping.entry_page._classify_entry_status",
        new=lambda _: "不明",
    ):
        with pytest.raises(ParseError, match="出走区分が不正です"):
            scraper.get_entry()
