"""ResultPageScraper.get_result()の単体テスト

requestsをモックし、フィクスチャHTMLを返すようにしてテストする。
結果テーブルの取得・バリデーションを検証する。
"""

from typing import Any
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from scraping.config import RESULT_COLUMNS

from .conftest import collect_result_fixture_race_ids, create_scraper_from_fixture

RESULT_RACE_IDS = collect_result_fixture_race_ids()


# ---------------------------------------------------------------------------
# 正常系: 全フィクスチャ共通テスト
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("race_id", RESULT_RACE_IDS, ids=RESULT_RACE_IDS)
def test_columns_match_result_columns(race_id: str) -> None:
    """カラム構成がRESULT_COLUMNSと一致すること"""
    scraper = create_scraper_from_fixture(race_id)
    result_df = scraper.get_result()

    assert isinstance(result_df, pd.DataFrame)
    assert list(result_df.columns) == RESULT_COLUMNS


@pytest.mark.parametrize("race_id", RESULT_RACE_IDS, ids=RESULT_RACE_IDS)
def test_race_id_matches(race_id: str) -> None:
    """全行のレースIDがコンストラクタで渡したrace_idと一致すること"""
    scraper = create_scraper_from_fixture(race_id)
    result_df = scraper.get_result()

    assert (result_df["レースID"] == race_id).all()


@pytest.mark.parametrize("race_id", RESULT_RACE_IDS, ids=RESULT_RACE_IDS)
def test_non_nan_columns_valid(race_id: str) -> None:
    """NaN不可カラムにNaNが含まれないこと"""
    scraper = create_scraper_from_fixture(race_id)
    result_df = scraper.get_result()

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
        assert result_df[col].notna().all(), f"'{col}'にNaNが含まれています"


@pytest.mark.parametrize("race_id", RESULT_RACE_IDS, ids=RESULT_RACE_IDS)
def test_weight_non_nan_except_cancel(race_id: str) -> None:
    """出走取消以外の馬の馬体重にNaNが含まれないこと"""
    scraper = create_scraper_from_fixture(race_id)
    result_df = scraper.get_result()

    non_cancel = result_df[result_df["出走区分"] != "取消"]
    assert non_cancel["馬体重"].notna().all(), "出走取消以外の馬体重にNaNがあります"


@pytest.mark.parametrize("race_id", RESULT_RACE_IDS, ids=RESULT_RACE_IDS)
def test_gender_enum(race_id: str) -> None:
    """性別が牡/牝/セのいずれかであること"""
    scraper = create_scraper_from_fixture(race_id)
    result_df = scraper.get_result()

    valid_genders = {"牡", "牝", "セ"}
    actual_genders = set(result_df["性別"].unique())
    assert actual_genders <= valid_genders, f"不正な性別: {actual_genders - valid_genders}"


@pytest.mark.parametrize("race_id", RESULT_RACE_IDS, ids=RESULT_RACE_IDS)
def test_affiliation_enum(race_id: str) -> None:
    """所属が美浦/栗東/地方/海外のいずれかであること"""
    scraper = create_scraper_from_fixture(race_id)
    result_df = scraper.get_result()

    valid_affiliations = {"美浦", "栗東", "地方", "海外"}
    actual = set(result_df["所属"].unique())
    assert actual <= valid_affiliations, f"不正な所属: {actual - valid_affiliations}"


@pytest.mark.parametrize("race_id", RESULT_RACE_IDS, ids=RESULT_RACE_IDS)
def test_horse_id_10_digits(race_id: str) -> None:
    """馬IDが10桁の文字列であること"""
    scraper = create_scraper_from_fixture(race_id)
    result_df = scraper.get_result()

    for horse_id in result_df["馬ID"]:
        assert len(str(horse_id)) == 10, f"馬IDが10桁ではありません: {horse_id}"


@pytest.mark.parametrize("race_id", RESULT_RACE_IDS, ids=RESULT_RACE_IDS)
def test_jockey_id_5_digits(race_id: str) -> None:
    """騎手IDが5桁の文字列であること"""
    scraper = create_scraper_from_fixture(race_id)
    result_df = scraper.get_result()

    for jockey_id in result_df["騎手ID"]:
        assert len(str(jockey_id)) == 5, f"騎手IDが5桁ではありません: {jockey_id}"


@pytest.mark.parametrize("race_id", RESULT_RACE_IDS, ids=RESULT_RACE_IDS)
def test_trainer_id_5_digits(race_id: str) -> None:
    """厩舎IDが5桁の文字列であること"""
    scraper = create_scraper_from_fixture(race_id)
    result_df = scraper.get_result()

    for trainer_id in result_df["厩舎ID"]:
        assert len(str(trainer_id)) == 5, f"厩舎IDが5桁ではありません: {trainer_id}"


# ---------------------------------------------------------------------------
# 正常系: 具体値の検証
# ---------------------------------------------------------------------------
EXPECTED_VALUES: list[dict[str, Any]] = [
    # ダービー2025 1着
    {
        "race_id": "202505021211",
        "馬番": 13,
        "馬名": "クロワデュノール",
        "出走区分": "出走",
        "着順": 1,
        "枠": 7,
        "性別": "牡",
        "年齢": 3,
        "斤量": 57.0,
        "騎手": "北村友",
        "タイム": "2:23.7",
        "人気": 1,
        "単勝オッズ": 2.1,
        "後3F": 34.2,
        "1コーナー通過順": 4,
        "2コーナー通過順": 3,
        "3コーナー通過順": 2,
        "4コーナー通過順": 3,
        "所属": "栗東",
        "厩舎": "斉藤崇",
        "馬体重": 504,
        "増減": 4,
        "馬ID": "2022105102",
        "騎手ID": "01102",
        "厩舎ID": "01151",
    },
    # ダービー2025 18着
    {
        "race_id": "202505021211",
        "馬番": 15,
        "馬名": "ファウストラーゼン",
        "出走区分": "出走",
        "着順": 18,
        "枠": 7,
        "性別": "牡",
        "年齢": 3,
        "斤量": 57.0,
        "騎手": "Ｍデム",
        "人気": 13,
        "単勝オッズ": 85.2,
        "後3F": 37.6,
        "所属": "栗東",
        "厩舎": "西村",
        "馬体重": 458,
        "増減": 2,
        "馬ID": "2022104218",
        "騎手ID": "05212",
        "厩舎ID": "01148",
    },
    # 鳴尾記念2023 1着
    {
        "race_id": "202306050911",
        "馬番": 13,
        "馬名": "レガレイラ",
        "出走区分": "出走",
        "着順": 1,
        "枠": 7,
        "性別": "牝",
        "年齢": 2,
        "所属": "美浦",
    },
    # 5頭立て 1着
    {
        "race_id": "202505020607",
        "馬番": 1,
        "馬名": "シンハナーダ",
        "出走区分": "出走",
        "着順": 1,
        "所属": "美浦",
    },
    # 障害レース 1着(中山大障害2024)
    {
        "race_id": "202406050710",
        "馬番": 8,
        "馬名": "ニシノデイジー",
        "出走区分": "出走",
        "着順": 1,
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
    result_df = scraper.get_result()

    row = result_df[result_df["馬番"] == expected["馬番"]].iloc[0]
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
    result_df = scraper.get_result()

    assert len(result_df) == case["expected_rows"]


# ---------------------------------------------------------------------------
# 正常系: 出走区分
# ---------------------------------------------------------------------------
def test_status_normal_race() -> None:
    """通常レース（ダービー2025）では全馬の出走区分が"出走"であること"""
    scraper = create_scraper_from_fixture("202505021211")
    result_df = scraper.get_result()

    assert (result_df["出走区分"] == "出走").all()


def test_status_chuushi() -> None:
    """鳴尾記念2023で競争中止馬（タリフライン）の出走区分が"中止"であること"""
    scraper = create_scraper_from_fixture("202306050911")
    result_df = scraper.get_result()

    tari = result_df[result_df["馬名"] == "タリフライン"].iloc[0]
    assert tari["出走区分"] == "中止"


def test_status_torikeshi() -> None:
    """鳴尾記念2023で出走取消馬の出走区分が"取消"であること"""
    scraper = create_scraper_from_fixture("202306050911")
    result_df = scraper.get_result()

    gonba = result_df[result_df["馬名"] == "ゴンバデカーブース"].iloc[0]
    assert gonba["出走区分"] == "取消"

    sunrise = result_df[result_df["馬名"] == "サンライズアース"].iloc[0]
    assert sunrise["出走区分"] == "取消"


def test_status_jogai() -> None:
    """ラジオNIKKEI賞2025で競走除外馬（クイーンズウォーク）の出走区分が"除外"であること"""
    scraper = create_scraper_from_fixture("202504030411")
    result_df = scraper.get_result()

    queen = result_df[result_df["馬名"] == "クイーンズウォーク"].iloc[0]
    assert queen["出走区分"] == "除外"


def test_status_count_chuushi_torikeshi() -> None:
    """鳴尾記念2023で中止1頭・取消2頭・出走15頭であること"""
    scraper = create_scraper_from_fixture("202306050911")
    result_df = scraper.get_result()

    assert (result_df["出走区分"] == "出走").sum() == 15
    assert (result_df["出走区分"] == "取消").sum() == 2
    assert (result_df["出走区分"] == "中止").sum() == 1


# ---------------------------------------------------------------------------
# 正常系: 競争中止馬のNaN条件
# ---------------------------------------------------------------------------
def test_chuushi_has_weight_but_nan_time() -> None:
    """競争中止馬（タリフライン）は馬体重ありだがタイム・後3FがNaNであること"""
    scraper = create_scraper_from_fixture("202306050911")
    result_df = scraper.get_result()

    tari = result_df[result_df["馬名"] == "タリフライン"].iloc[0]
    assert tari["馬体重"] == 470
    assert tari["増減"] == 8
    assert pd.isna(tari["タイム"])
    assert pd.isna(tari["後3F"])
    assert pd.isna(tari["着順"])


def test_chuushi_has_popularity_and_odds() -> None:
    """競争中止馬（タリフライン）は人気・オッズが存在すること"""
    scraper = create_scraper_from_fixture("202306050911")
    result_df = scraper.get_result()

    tari = result_df[result_df["馬名"] == "タリフライン"].iloc[0]
    assert tari["人気"] == 8
    assert tari["単勝オッズ"] == pytest.approx(27.6)


def test_chuushi_has_corner_positions() -> None:
    """競争中止馬（タリフライン）はコーナー通過順が存在すること"""
    scraper = create_scraper_from_fixture("202306050911")
    result_df = scraper.get_result()

    tari = result_df[result_df["馬名"] == "タリフライン"].iloc[0]
    assert tari["1コーナー通過順"] == 6
    assert tari["2コーナー通過順"] == 7
    assert tari["3コーナー通過順"] == 5
    assert tari["4コーナー通過順"] == 10


# ---------------------------------------------------------------------------
# 正常系: 出走取消馬のNaN条件
# ---------------------------------------------------------------------------
def test_torikeshi_has_nan_weight() -> None:
    """出走取消馬（ゴンバデカーブース）は馬体重がNaNであること"""
    scraper = create_scraper_from_fixture("202306050911")
    result_df = scraper.get_result()

    gonba = result_df[result_df["馬名"] == "ゴンバデカーブース"].iloc[0]
    assert pd.isna(gonba["馬体重"])
    assert pd.isna(gonba["増減"])


def test_torikeshi_has_nan_odds_and_popularity() -> None:
    """出走取消馬（ゴンバデカーブース）は人気・オッズがNaNであること"""
    scraper = create_scraper_from_fixture("202306050911")
    result_df = scraper.get_result()

    gonba = result_df[result_df["馬名"] == "ゴンバデカーブース"].iloc[0]
    assert pd.isna(gonba["人気"])
    assert pd.isna(gonba["単勝オッズ"])
    assert pd.isna(gonba["タイム"])
    assert pd.isna(gonba["着順"])


def test_torikeshi_has_nan_corner_positions() -> None:
    """出走取消馬（ゴンバデカーブース）はコーナー通過順がNaNであること"""
    scraper = create_scraper_from_fixture("202306050911")
    result_df = scraper.get_result()

    gonba = result_df[result_df["馬名"] == "ゴンバデカーブース"].iloc[0]
    assert pd.isna(gonba["1コーナー通過順"])
    assert pd.isna(gonba["2コーナー通過順"])
    assert pd.isna(gonba["3コーナー通過順"])
    assert pd.isna(gonba["4コーナー通過順"])


# ---------------------------------------------------------------------------
# 正常系: 競走除外馬のNaN条件
# ---------------------------------------------------------------------------
def test_jogai_has_weight_but_nan_time() -> None:
    """競走除外馬（クイーンズウォーク）は馬体重ありだがタイムがNaNであること"""
    scraper = create_scraper_from_fixture("202504030411")
    result_df = scraper.get_result()

    queen = result_df[result_df["馬名"] == "クイーンズウォーク"].iloc[0]
    assert queen["馬体重"] == 540
    assert queen["増減"] == 4
    assert pd.isna(queen["タイム"])
    assert pd.isna(queen["着順"])
    assert pd.isna(queen["人気"])
    assert pd.isna(queen["単勝オッズ"])


# ---------------------------------------------------------------------------
# 正常系: 所属
# ---------------------------------------------------------------------------
def test_overseas_horse_affiliation() -> None:
    """安田記念2023（海外馬イレジン）の所属が海外であること"""
    scraper = create_scraper_from_fixture("202305050812")
    result_df = scraper.get_result()

    irezin = result_df[result_df["馬名"] == "イレジン"].iloc[0]
    assert irezin["所属"] == "海外"
    assert irezin["厩舎"] == "ゴーヴァン"


def test_local_horse_affiliation() -> None:
    """安田記念2023（地方馬）の所属が地方であること"""
    scraper = create_scraper_from_fixture("202305050812")
    result_df = scraper.get_result()

    kurino = result_df[result_df["馬名"] == "クリノメガミエース"].iloc[0]
    assert kurino["所属"] == "地方"
    assert kurino["厩舎"] == "石橋満"

    chestnut = result_df[result_df["馬名"] == "チェスナットコート"].iloc[0]
    assert chestnut["所属"] == "地方"
    assert chestnut["厩舎"] == "田中一"


def test_trainer_name_has_no_leading_space() -> None:
    """厩舎名に先頭の空白がないこと"""
    scraper = create_scraper_from_fixture("202505021211")
    result_df = scraper.get_result()

    for trainer in result_df["厩舎"]:
        assert not trainer.startswith(" "), f"厩舎名に先頭空白があります: '{trainer}'"


# ---------------------------------------------------------------------------
# 正常系: セン馬
# ---------------------------------------------------------------------------
def test_gelding_gender() -> None:
    """安田記念2023のイレジンとフォワードアゲンがセン馬であること"""
    scraper = create_scraper_from_fixture("202305050812")
    result_df = scraper.get_result()

    irezin = result_df[result_df["馬名"] == "イレジン"].iloc[0]
    assert irezin["性別"] == "セ"

    forward = result_df[result_df["馬名"] == "フォワードアゲン"].iloc[0]
    assert forward["性別"] == "セ"


# ---------------------------------------------------------------------------
# 正常系: 同着
# ---------------------------------------------------------------------------
def test_first_place_tie() -> None:
    """オークス2010で1着同着が2頭であること"""
    scraper = create_scraper_from_fixture("201005030211")
    result_df = scraper.get_result()

    first_place = result_df[result_df["着順"] == 1]
    assert len(first_place) == 2
    assert set(first_place["馬名"].tolist()) == {"アパパネ", "サンテミリオン"}
    assert set(first_place["馬番"].tolist()) == {17, 18}


def test_third_place_tie() -> None:
    """3歳以上1勝クラス(202009050712)で3着同着が3頭であること"""
    scraper = create_scraper_from_fixture("202009050712")
    result_df = scraper.get_result()

    third_place = result_df[result_df["着順"] == 3]
    assert len(third_place) == 3
    expected_names = {"ミッドサマーハウス", "フリークアウト", "ドゥーベ"}
    assert set(third_place["馬名"].tolist()) == expected_names
    assert set(third_place["馬番"].tolist()) == {1, 4, 11}


# ---------------------------------------------------------------------------
# 正常系: 障害レース
# ---------------------------------------------------------------------------
def test_steeplechase_chuushi() -> None:
    """中山大障害2024で競争中止馬が3頭いること"""
    scraper = create_scraper_from_fixture("202406050710")
    result_df = scraper.get_result()

    chuushi = result_df[result_df["出走区分"] == "中止"]
    assert len(chuushi) == 3
    expected_names = {"マイネルグロン", "ダイシンクローバー", "ロードトゥフェイム"}
    assert set(chuushi["馬名"].tolist()) == expected_names


# ---------------------------------------------------------------------------
# 準正常系: バリデーションエラー
# ---------------------------------------------------------------------------
def test_validation_error_on_invalid_gender() -> None:
    """性別が不正な場合にParseErrorが発生すること"""
    from scraping.exceptions import ParseError

    scraper = create_scraper_from_fixture("202505021211")

    with patch.object(type(scraper), "get_result", wraps=scraper.get_result):
        # get_result内部で性別が検証されるため、
        # HTMLテキストを直接書き換えてテストする
        scraper.html_text = scraper.html_text.replace("牡3", "X3", 1)
        scraper.soup = __import__("bs4").BeautifulSoup(scraper.html_text, "html.parser")

        with pytest.raises(ParseError, match="性別が不正です"):
            scraper.get_result()


def test_validation_error_on_invalid_affiliation() -> None:
    """所属が不正な場合にParseErrorが発生すること"""
    from scraping.exceptions import ParseError

    scraper = create_scraper_from_fixture("202505021211")

    # HTMLのLabelスパンテキストを不正な所属に置換
    scraper.html_text = scraper.html_text.replace(
        '<span class="Label2">栗東</span>', '<span class="Label2">XX</span>', 1
    )
    scraper.soup = __import__("bs4").BeautifulSoup(scraper.html_text, "html.parser")

    with pytest.raises(ParseError, match="所属が不正です"):
        scraper.get_result()


def test_validation_error_on_invalid_race_status() -> None:
    """出走区分が不正な場合にParseErrorが発生すること"""
    from scraping.exceptions import ParseError

    scraper = create_scraper_from_fixture("202505021211")

    with patch(
        "scraping.result_page._classify_race_status",
        new=lambda _: "不明",
    ):
        with pytest.raises(ParseError, match="出走区分が不正です"):
            scraper.get_result()
