"""ResultPageScraper.get_lap_time()の単体テスト

requestsをモックし、フィクスチャHTMLを返すようにしてテストする。
ラップタイムの取得を検証する。
"""

import pandas as pd
import pytest

from scraping.config import LAP_TIME_COLUMNS

from .conftest import collect_result_fixture_race_ids, create_scraper_from_fixture

RESULT_RACE_IDS = collect_result_fixture_race_ids()

# 障害レースのID
OBSTACLE_RACE_IDS: list[str] = ["202406050710"]

# 障害レース以外のID（ラップタイムが取得できるレース）
NON_OBSTACLE_RACE_IDS: list[str] = [
    race_id for race_id in RESULT_RACE_IDS if race_id not in OBSTACLE_RACE_IDS
]


# ---------------------------------------------------------------------------
# 正常系: 全フィクスチャ共通テスト（障害レース以外）
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("race_id", NON_OBSTACLE_RACE_IDS, ids=NON_OBSTACLE_RACE_IDS)
def test_columns_match_lap_time_columns(race_id: str) -> None:
    """カラム構成がLAP_TIME_COLUMNSと一致すること"""
    scraper = create_scraper_from_fixture(race_id)
    df = scraper.get_lap_time()

    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == LAP_TIME_COLUMNS


@pytest.mark.parametrize("race_id", NON_OBSTACLE_RACE_IDS, ids=NON_OBSTACLE_RACE_IDS)
def test_single_row(race_id: str) -> None:
    """結果が1行であること"""
    scraper = create_scraper_from_fixture(race_id)
    df = scraper.get_lap_time()

    assert len(df) == 1


@pytest.mark.parametrize("race_id", NON_OBSTACLE_RACE_IDS, ids=NON_OBSTACLE_RACE_IDS)
def test_race_id_matches(race_id: str) -> None:
    """レースIDが一致すること"""
    scraper = create_scraper_from_fixture(race_id)
    df = scraper.get_lap_time()

    assert df["レースID"].iloc[0] == race_id


@pytest.mark.parametrize("race_id", NON_OBSTACLE_RACE_IDS, ids=NON_OBSTACLE_RACE_IDS)
def test_pace_is_valid(race_id: str) -> None:
    """ペースがS/M/Hのいずれかであること"""
    scraper = create_scraper_from_fixture(race_id)
    df = scraper.get_lap_time()

    pace = df["ペース"].iloc[0]
    if pd.notna(pace):
        assert pace in {"S", "M", "H"}, f"不正なペース: {pace}"


@pytest.mark.parametrize("race_id", NON_OBSTACLE_RACE_IDS, ids=NON_OBSTACLE_RACE_IDS)
def test_lap_times_are_positive_float(race_id: str) -> None:
    """ラップタイムの値が正の浮動小数点であること"""
    scraper = create_scraper_from_fixture(race_id)
    df = scraper.get_lap_time()

    distance_cols = [c for c in LAP_TIME_COLUMNS if c not in ("レースID", "ペース")]
    for col in distance_cols:
        val = df[col].iloc[0]
        if pd.notna(val):
            assert isinstance(val, float), f"{col}がfloatではありません: {type(val)}"
            assert val > 0, f"{col}が正の値ではありません: {val}"


@pytest.mark.parametrize("race_id", NON_OBSTACLE_RACE_IDS, ids=NON_OBSTACLE_RACE_IDS)
def test_at_least_one_lap_time_exists(race_id: str) -> None:
    """少なくとも1つのラップタイムが存在すること"""
    scraper = create_scraper_from_fixture(race_id)
    df = scraper.get_lap_time()

    distance_cols = [c for c in LAP_TIME_COLUMNS if c not in ("レースID", "ペース")]
    non_nan_count = sum(1 for c in distance_cols if pd.notna(df[c].iloc[0]))
    assert non_nan_count > 0, "ラップタイムが1つも存在しません"


# ---------------------------------------------------------------------------
# 正常系: 障害レース
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("race_id", OBSTACLE_RACE_IDS, ids=OBSTACLE_RACE_IDS)
def test_obstacle_race_returns_nan_dataframe(race_id: str) -> None:
    """障害レースではレースID以外がNaNの1行DataFrameを返すこと"""
    scraper = create_scraper_from_fixture(race_id)
    df = scraper.get_lap_time()

    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == LAP_TIME_COLUMNS
    assert len(df) == 1
    assert df["レースID"].iloc[0] == race_id

    # レースID以外はすべてNaN
    distance_cols = [c for c in LAP_TIME_COLUMNS if c != "レースID"]
    for col in distance_cols:
        assert pd.isna(df[col].iloc[0]), f"{col}がNaNではありません"


# ---------------------------------------------------------------------------
# 正常系: 200mで割り切れる距離のレース
# ---------------------------------------------------------------------------
def test_derby_2025_even_distance() -> None:
    """ダービー2025（2400m）のラップタイムが正しいこと

    200mで割り切れる距離のため、200m刻みのカラムのみに値が入る。
    """
    scraper = create_scraper_from_fixture("202505021211")
    df = scraper.get_lap_time()

    assert df["ペース"].iloc[0] == "S"

    # 200m刻みのラップタイム
    assert df["200m"].iloc[0] == 12.6
    assert df["400m"].iloc[0] == 11.4
    assert df["600m"].iloc[0] == 11.7
    assert df["800m"].iloc[0] == 12.1
    assert df["1000m"].iloc[0] == 12.2
    assert df["1200m"].iloc[0] == 12.1
    assert df["1400m"].iloc[0] == 12.1
    assert df["1600m"].iloc[0] == 12.5
    assert df["1800m"].iloc[0] == 12.2
    assert df["2000m"].iloc[0] == 11.8
    assert df["2200m"].iloc[0] == 11.3
    assert df["2400m"].iloc[0] == 11.7

    # 100m刻み（奇数距離）のカラムはNaN
    assert pd.isna(df["100m"].iloc[0])
    assert pd.isna(df["300m"].iloc[0])
    assert pd.isna(df["500m"].iloc[0])

    # 距離を超えるカラムはNaN
    assert pd.isna(df["2500m"].iloc[0])
    assert pd.isna(df["2600m"].iloc[0])


def test_kokura_nisai_s_1200m() -> None:
    """小倉2歳S（1200m）のラップタイムが正しいこと

    短距離の200mで割り切れるレース。
    """
    scraper = create_scraper_from_fixture("202407020811")
    df = scraper.get_lap_time()

    assert df["ペース"].iloc[0] == "M"

    assert df["200m"].iloc[0] == 12.2
    assert df["400m"].iloc[0] == 10.6
    assert df["600m"].iloc[0] == 11.7
    assert df["800m"].iloc[0] == 11.8
    assert df["1000m"].iloc[0] == 11.0
    assert df["1200m"].iloc[0] == 11.7

    # 1200mを超えるカラムはNaN
    assert pd.isna(df["1300m"].iloc[0])
    assert pd.isna(df["1400m"].iloc[0])


# ---------------------------------------------------------------------------
# 正常系: 200mで割り切れない距離のレース
# ---------------------------------------------------------------------------
def test_chitose_tokubetsu_1700m() -> None:
    """千歳特別2025（1700m ダート）のラップタイムが正しいこと

    200mで割り切れない距離のため、100m刻み（奇数距離）のカラムに値が入る。
    """
    scraper = create_scraper_from_fixture("202501020310")
    df = scraper.get_lap_time()

    assert df["ペース"].iloc[0] == "H"

    # 100m刻みのラップタイム
    assert df["100m"].iloc[0] == 6.8
    assert df["300m"].iloc[0] == 11.0
    assert df["500m"].iloc[0] == 11.5
    assert df["700m"].iloc[0] == 11.8
    assert df["900m"].iloc[0] == 12.1
    assert df["1100m"].iloc[0] == 12.1
    assert df["1300m"].iloc[0] == 12.3
    assert df["1500m"].iloc[0] == 12.3
    assert df["1700m"].iloc[0] == 13.0

    # 200m刻み（偶数距離）のカラムはNaN
    assert pd.isna(df["200m"].iloc[0])
    assert pd.isna(df["400m"].iloc[0])
    assert pd.isna(df["600m"].iloc[0])

    # 距離を超えるカラムはNaN
    assert pd.isna(df["1800m"].iloc[0])
    assert pd.isna(df["1900m"].iloc[0])


def test_nikkei_sho_2500m() -> None:
    """日経賞2023（2500m）のラップタイムが正しいこと

    長距離で200mで割り切れないレース。
    """
    scraper = create_scraper_from_fixture("202306030111")
    df = scraper.get_lap_time()

    assert df["ペース"].iloc[0] == "S"

    assert df["100m"].iloc[0] == 6.9
    assert df["300m"].iloc[0] == 11.7
    assert df["500m"].iloc[0] == 12.0
    assert df["700m"].iloc[0] == 12.9
    assert df["900m"].iloc[0] == 12.6
    assert df["1100m"].iloc[0] == 13.1
    assert df["1300m"].iloc[0] == 12.9
    assert df["1500m"].iloc[0] == 12.7
    assert df["1700m"].iloc[0] == 12.8
    assert df["1900m"].iloc[0] == 12.4
    assert df["2100m"].iloc[0] == 12.5
    assert df["2300m"].iloc[0] == 11.9
    assert df["2500m"].iloc[0] == 12.4

    # 偶数距離カラムはNaN
    assert pd.isna(df["200m"].iloc[0])
    assert pd.isna(df["2400m"].iloc[0])

    # 距離を超えるカラムはNaN
    assert pd.isna(df["2600m"].iloc[0])
    assert pd.isna(df["2700m"].iloc[0])


# ---------------------------------------------------------------------------
# 正常系: 直線レース
# ---------------------------------------------------------------------------
def test_ibis_sd_2025_straight_1000m() -> None:
    """アイビスSD2025（1000m直線）のラップタイムが正しいこと

    直線レースかつ200mで割り切れる距離。
    """
    scraper = create_scraper_from_fixture("202504020407")
    df = scraper.get_lap_time()

    assert df["ペース"].iloc[0] == "M"

    assert df["200m"].iloc[0] == 11.7
    assert df["400m"].iloc[0] == 10.0
    assert df["600m"].iloc[0] == 10.3
    assert df["800m"].iloc[0] == 10.6
    assert df["1000m"].iloc[0] == 11.1

    # 100m刻みのカラムはNaN
    assert pd.isna(df["100m"].iloc[0])
    assert pd.isna(df["300m"].iloc[0])

    # 距離を超えるカラムはNaN
    assert pd.isna(df["1100m"].iloc[0])
    assert pd.isna(df["1200m"].iloc[0])


# ---------------------------------------------------------------------------
# 正常系: 長距離レース（3200m）
# ---------------------------------------------------------------------------
def test_long_distance_3200m() -> None:
    """3200mレースのラップタイムが正しいこと

    200mで割り切れる長距離レースの全カラムが正しく設定されること。
    """
    scraper = create_scraper_from_fixture("202308010411")
    df = scraper.get_lap_time()

    assert df["ペース"].iloc[0] == "S"

    # 先頭と末尾の値を検証
    assert df["200m"].iloc[0] == 12.3
    assert df["400m"].iloc[0] == 10.8
    assert df["3000m"].iloc[0] == 11.5
    assert df["3200m"].iloc[0] == 11.9

    # 距離を超えるカラムはNaN
    assert pd.isna(df["3300m"].iloc[0])
    assert pd.isna(df["3400m"].iloc[0])

    # 100m刻みのカラムはNaN
    assert pd.isna(df["100m"].iloc[0])
    assert pd.isna(df["300m"].iloc[0])


# ---------------------------------------------------------------------------
# 正常系: 競争中止・出走取消があるレース
# ---------------------------------------------------------------------------
def test_race_with_cancellation_has_lap_time() -> None:
    """競争中止・出走取消があるレースでもラップタイムが取得できること"""
    scraper = create_scraper_from_fixture("202306050911")
    df = scraper.get_lap_time()

    assert not df.empty
    assert list(df.columns) == LAP_TIME_COLUMNS
    assert df["レースID"].iloc[0] == "202306050911"
    assert df["ペース"].iloc[0] == "M"

    # 2000mレースの値を検証
    assert df["200m"].iloc[0] == 12.5
    assert df["2000m"].iloc[0] == 11.5
    assert pd.isna(df["2100m"].iloc[0])
