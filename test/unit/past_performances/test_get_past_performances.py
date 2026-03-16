"""PastPerformancesScraper.get_past_performances()の単体テスト

Selenium WebDriverをモックし、フィクスチャHTMLを返すようにしてテストする。
馬柱テーブルの取得・カラム構成・主要値を検証する。
"""

import datetime
from typing import Any
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from scraping.config import PAST_PERFORMANCES_COLUMNS
from scraping.exceptions import DriverError, ParseError
from scraping.past_performances import PastPerformancesScraper

from .conftest import collect_fixture_horse_ids, create_scraper_from_fixture

HORSE_IDS = collect_fixture_horse_ids()


# ---------------------------------------------------------------------------
# 正常系: 全フィクスチャ共通テスト
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("horse_id", HORSE_IDS, ids=HORSE_IDS)
def test_columns_match_past_performances_columns(horse_id: str) -> None:
    """カラム構成がPAST_PERFORMANCES_COLUMNSと一致すること"""
    scraper = create_scraper_from_fixture(horse_id)
    df = scraper.get_past_performances()

    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == PAST_PERFORMANCES_COLUMNS


@pytest.mark.parametrize("horse_id", HORSE_IDS, ids=HORSE_IDS)
def test_dataframe_is_not_empty(horse_id: str) -> None:
    """戦績が1行以上あること"""
    scraper = create_scraper_from_fixture(horse_id)
    df = scraper.get_past_performances()

    assert len(df) > 0


@pytest.mark.parametrize("horse_id", HORSE_IDS, ids=HORSE_IDS)
def test_date_column_is_date_type(horse_id: str) -> None:
    """日付カラムがdatetime.date型であること"""
    scraper = create_scraper_from_fixture(horse_id)
    df = scraper.get_past_performances()

    for val in df["日付"]:
        assert isinstance(val, datetime.date), f"日付が不正: {val} (type={type(val).__name__})"


@pytest.mark.parametrize("horse_id", HORSE_IDS, ids=HORSE_IDS)
def test_turf_dirt_enum(horse_id: str) -> None:
    """芝ダが芝/ダ/障のいずれかであること"""
    scraper = create_scraper_from_fixture(horse_id)
    df = scraper.get_past_performances()

    valid = {"芝", "ダ", "障"}
    actual = set(df["芝ダ"].dropna().unique())
    assert actual <= valid, f"不正な芝ダ: {actual - valid}"


@pytest.mark.parametrize("horse_id", HORSE_IDS, ids=HORSE_IDS)
def test_distance_is_positive(horse_id: str) -> None:
    """距離が正の整数であること"""
    scraper = create_scraper_from_fixture(horse_id)
    df = scraper.get_past_performances()

    valid = df["距離"].dropna()
    assert (valid > 0).all(), "距離に0以下の値があります"


@pytest.mark.parametrize("horse_id", HORSE_IDS, ids=HORSE_IDS)
def test_organize_enum(horse_id: str) -> None:
    """主催が中央/地方/海外のいずれかであること"""
    scraper = create_scraper_from_fixture(horse_id)
    df = scraper.get_past_performances()

    valid = {"中央", "地方", "海外"}
    actual = set(df["主催"].unique())
    assert actual <= valid, f"不正な主催: {actual - valid}"


@pytest.mark.parametrize("horse_id", HORSE_IDS, ids=HORSE_IDS)
def test_jockey_column_is_not_all_nan(horse_id: str) -> None:
    """騎手カラムが全てNaNではないこと"""
    scraper = create_scraper_from_fixture(horse_id)
    df = scraper.get_past_performances()

    assert df["騎手"].notna().any(), "騎手が全てNaN"


@pytest.mark.parametrize("horse_id", HORSE_IDS, ids=HORSE_IDS)
def test_jockey_id_format(horse_id: str) -> None:
    """騎手IDが数字5桁の文字列であること（NaN以外）"""
    scraper = create_scraper_from_fixture(horse_id)
    df = scraper.get_past_performances()

    for jockey_id in df["騎手ID"].dropna():
        assert (
            isinstance(jockey_id, str) and len(jockey_id) == 5 and jockey_id.isdigit()
        ), f"騎手IDが不正: {jockey_id}"


@pytest.mark.parametrize("horse_id", HORSE_IDS, ids=HORSE_IDS)
def test_race_name_is_not_empty(horse_id: str) -> None:
    """レース名が空でないこと"""
    scraper = create_scraper_from_fixture(horse_id)
    df = scraper.get_past_performances()

    assert df["レース名"].notna().all(), "レース名にNaNがあります"
    for name in df["レース名"]:
        assert len(str(name)) > 0, "レース名が空文字列です"


@pytest.mark.parametrize("horse_id", HORSE_IDS, ids=HORSE_IDS)
def test_corner_passing_order_range(horse_id: str) -> None:
    """コーナー通過順が1以上の整数であること"""
    scraper = create_scraper_from_fixture(horse_id)
    df = scraper.get_past_performances()

    for col in ["1コーナー通過順", "2コーナー通過順", "3コーナー通過順", "4コーナー通過順"]:
        valid = df[col].dropna()
        if len(valid) > 0:
            assert (valid >= 1).all(), f"{col}に1未満の値があります"


@pytest.mark.parametrize("horse_id", HORSE_IDS, ids=HORSE_IDS)
def test_index_is_sequential(horse_id: str) -> None:
    """インデックスが0から連番であること"""
    scraper = create_scraper_from_fixture(horse_id)
    df = scraper.get_past_performances()

    assert list(df.index) == list(range(len(df)))


# ---------------------------------------------------------------------------
# 正常系: 行数の検証
# ---------------------------------------------------------------------------
EXPECTED_ROW_COUNTS: list[dict[str, Any]] = [
    {"horse_id": "2022105081", "expected_rows": 10},
    {"horse_id": "2011101125", "expected_rows": 40},
    {"horse_id": "2021103695", "expected_rows": 30},
    {"horse_id": "2021190001", "expected_rows": 14},
    {"horse_id": "2018103559", "expected_rows": 19},
    {"horse_id": "2021105414", "expected_rows": 12},
    {"horse_id": "2021104825", "expected_rows": 9},
    {"horse_id": "2021105727", "expected_rows": 14},
    {"horse_id": "2016103690", "expected_rows": 33},
    {"horse_id": "2009106130", "expected_rows": 20},
]


@pytest.mark.parametrize(
    "case",
    EXPECTED_ROW_COUNTS,
    ids=[c["horse_id"] for c in EXPECTED_ROW_COUNTS],
)
def test_row_count(case: dict[str, Any]) -> None:
    """行数が期待値と一致すること"""
    scraper = create_scraper_from_fixture(case["horse_id"])
    df = scraper.get_past_performances()

    assert len(df) == case["expected_rows"]


# ---------------------------------------------------------------------------
# 正常系: 具体値の検証
# ---------------------------------------------------------------------------
EXPECTED_VALUES: list[dict[str, Any]] = [
    # ミュージアムマイル 有馬記念1着
    {
        "horse_id": "2022105081",
        "row_index": 0,
        "レースID": "202506050811",
        "日付": datetime.date(2025, 12, 28),
        "競馬場": "中山",
        "レース名": "有馬記念(GI)",
        "着順": 1,
        "騎手": "Ｃ．デム",
        "騎手ID": "05473",
        "芝ダ": "芝",
        "距離": 2500,
        "馬場": "良",
        "主催": "中央",
        "賞金": 50352.8,
    },
    # オジュウチョウサン 中山大障害（障害レース）
    {
        "horse_id": "2011101125",
        "row_index": 0,
        "レースID": "202206050710",
        "日付": datetime.date(2022, 12, 24),
        "レース名": "中山大障害(JGI)",
        "着順": 6,
        "騎手": "石神深一",
        "騎手ID": "01059",
        "芝ダ": "障",
        "距離": 4100,
        "主催": "中央",
    },
    # カランダガン ジャパンカップ1着
    {
        "horse_id": "2021190001",
        "row_index": 0,
        "レースID": "202505050812",
        "日付": datetime.date(2025, 11, 30),
        "レース名": "ジャパンC(GI)",
        "着順": 1,
        "騎手": "バルザロ",
        "騎手ID": "05504",
        "芝ダ": "芝",
        "距離": 2400,
        "主催": "中央",
    },
    # フォーエバーヤング サウジカップ（海外）
    {
        "horse_id": "2021105727",
        "row_index": 0,
        "日付": datetime.date(2026, 2, 15),
        "レース名": "サウジC(GI)",
        "着順": 1,
        "騎手": "坂井瑠星",
        "騎手ID": "01163",
        "芝ダ": "ダ",
        "距離": 1800,
        "主催": "海外",
    },
    # ビコーズウイキャン 地方レース
    {
        "horse_id": "2021103695",
        "row_index": 0,
        "日付": datetime.date(2026, 2, 23),
        "競馬場": "浦和",
        "騎手ID": "05611",
        "芝ダ": "ダ",
        "距離": 1400,
        "主催": "地方",
    },
]


@pytest.mark.parametrize(
    "expected",
    EXPECTED_VALUES,
    ids=[
        f"{e['horse_id']}_{e.get('レース名', 'row' + str(e['row_index']))}" for e in EXPECTED_VALUES
    ],
)
def test_expected_values(expected: dict[str, Any]) -> None:
    """代表的なレースの具体的な値を検証する"""
    scraper = create_scraper_from_fixture(expected["horse_id"])
    df = scraper.get_past_performances()

    row = df.iloc[expected["row_index"]]
    for key, value in expected.items():
        if key in ("horse_id", "row_index"):
            continue
        actual = row[key]
        if isinstance(value, float) and np.isnan(value):
            assert np.isnan(actual), f"{key}: {actual} != NaN"
        elif isinstance(value, float):
            assert actual == pytest.approx(value), f"{key}: {actual} != {value}"
        else:
            assert actual == value, f"{key}: {actual} != {value}"


# ---------------------------------------------------------------------------
# 正常系: 主催の分布
# ---------------------------------------------------------------------------
def test_organize_central_only() -> None:
    """ミュージアムマイルは全レースが中央であること"""
    scraper = create_scraper_from_fixture("2022105081")
    df = scraper.get_past_performances()

    assert (df["主催"] == "中央").all()


def test_organize_includes_local() -> None:
    """ビコーズウイキャンのレースに地方が含まれること"""
    scraper = create_scraper_from_fixture("2021103695")
    df = scraper.get_past_performances()

    assert (df["主催"] == "地方").sum() >= 20
    assert "地方" in df["主催"].values


def test_organize_mixed() -> None:
    """フォーエバーヤングは中央・海外・地方が混在すること"""
    scraper = create_scraper_from_fixture("2021105727")
    df = scraper.get_past_performances()

    organizers = set(df["主催"].unique())
    assert organizers == {"中央", "海外", "地方"}


def test_organize_has_overseas() -> None:
    """フォーエバーヤングの海外レースが8件であること"""
    scraper = create_scraper_from_fixture("2021105727")
    df = scraper.get_past_performances()

    assert (df["主催"] == "海外").sum() == 8


# ---------------------------------------------------------------------------
# 正常系: 障害レース
# ---------------------------------------------------------------------------
def test_obstacle_race_turf_dirt() -> None:
    """オジュウチョウサンに障害レース（芝ダ="障"）が含まれること"""
    scraper = create_scraper_from_fixture("2011101125")
    df = scraper.get_past_performances()

    assert "障" in df["芝ダ"].values


# ---------------------------------------------------------------------------
# 正常系: 着順がNaN（中止・除外・取消）
# ---------------------------------------------------------------------------
def test_chushi_has_nan_order() -> None:
    """タイトルホルダーの天皇賞(春)（競走中止）は着順がNaNであること"""
    scraper = create_scraper_from_fixture("2018103559")
    df = scraper.get_past_performances()

    tensho = df[df["レース名"].str.contains("天皇賞")]
    nan_rows = tensho[tensho["着順"].isna()]
    assert len(nan_rows) >= 1, "天皇賞(春)の中止レースが見つかりません"


def test_torikeshi_has_nan_ninki() -> None:
    """ゴンバデカーブースのホープフルS（出走取消）は人気がNaNであること"""
    scraper = create_scraper_from_fixture("2021104825")
    df = scraper.get_past_performances()

    hopeful = df[df["レース名"].str.contains("ホープフルS")]
    assert len(hopeful) == 1
    assert pd.isna(hopeful.iloc[0]["人気"])
    assert pd.isna(hopeful.iloc[0]["着順"])


# ---------------------------------------------------------------------------
# 正常系: 間隔日数
# ---------------------------------------------------------------------------
def test_interval_last_row_is_nan() -> None:
    """最後のレースの間隔日数はNaNであること"""
    scraper = create_scraper_from_fixture("2022105081")
    df = scraper.get_past_performances()

    assert pd.isna(df.iloc[-1]["間隔日数"])


def test_interval_first_row_is_not_nan() -> None:
    """最初のレースの間隔日数はNaNでないこと（最終行でない限り）"""
    scraper = create_scraper_from_fixture("2022105081")
    df = scraper.get_past_performances()

    if len(df) > 1:
        assert pd.notna(df.iloc[0]["間隔日数"])


def test_interval_value() -> None:
    """ミュージアムマイルの先頭行の間隔日数が56日であること"""
    scraper = create_scraper_from_fixture("2022105081")
    df = scraper.get_past_performances()

    assert df.iloc[0]["間隔日数"] == pytest.approx(56.0)


# ---------------------------------------------------------------------------
# 正常系: レースIDの形式
# ---------------------------------------------------------------------------
def test_central_race_id_format() -> None:
    """中央レースのレースIDが12桁であること"""
    scraper = create_scraper_from_fixture("2022105081")
    df = scraper.get_past_performances()

    for race_id in df["レースID"]:
        assert len(str(race_id)) == 12, f"レースIDが12桁ではありません: {race_id}"


def test_overseas_race_id_is_empty() -> None:
    """海外レースのレースIDが空文字列であること"""
    scraper = create_scraper_from_fixture("2021105727")
    df = scraper.get_past_performances()

    overseas = df[df["主催"] == "海外"]
    for race_id in overseas["レースID"]:
        assert race_id == "", f"海外レースのレースIDが空でない: {race_id}"


# ---------------------------------------------------------------------------
# 正常系: 通過順の分割
# ---------------------------------------------------------------------------
def test_corner_passing_split() -> None:
    """ミュージアムマイル先頭行のコーナー通過順が正しく分割されていること"""
    scraper = create_scraper_from_fixture("2022105081")
    df = scraper.get_past_performances()

    row = df.iloc[0]
    # 3コーナー・4コーナーに値があること
    assert pd.notna(row["3コーナー通過順"])
    assert pd.notna(row["4コーナー通過順"])


# ---------------------------------------------------------------------------
# 正常系: ペースの分割
# ---------------------------------------------------------------------------
def test_pace_split() -> None:
    """レース前3F/レース後3Fが数値で格納されていること"""
    scraper = create_scraper_from_fixture("2022105081")
    df = scraper.get_past_performances()

    row = df.iloc[0]
    assert pd.notna(row["レース前3F"])
    assert pd.notna(row["レース後3F"])
    assert isinstance(row["レース前3F"], float)
    assert isinstance(row["レース後3F"], float)


# ---------------------------------------------------------------------------
# 正常系: 馬体重・増減
# ---------------------------------------------------------------------------
def test_horse_weight_is_numeric() -> None:
    """馬体重が数値であること"""
    scraper = create_scraper_from_fixture("2022105081")
    df = scraper.get_past_performances()

    valid = df["馬体重"].dropna()
    assert len(valid) > 0
    assert (valid > 300).all(), "馬体重が300kg未満の異常値があります"


# ---------------------------------------------------------------------------
# 正常系: 天候カラム
# ---------------------------------------------------------------------------
def test_weather_values() -> None:
    """天候が晴/曇/雨/小雨/雪/NaNなどの既知の値であること"""
    scraper = create_scraper_from_fixture("2022105081")
    df = scraper.get_past_performances()

    valid_weather = {"晴", "曇", "雨", "小雨", "小雪", "雪"}
    actual = set(df["天候"].dropna().unique())
    assert actual <= valid_weather, f"不正な天候: {actual - valid_weather}"


# ---------------------------------------------------------------------------
# 正常系: 新馬（戦績なし）の場合
# ---------------------------------------------------------------------------
def test_new_horse_returns_empty_dataframe() -> None:
    """新馬（戦績なし）のHTMLの場合に空DataFrameが返ること"""
    # 馬柱テーブルがないHTMLを模擬する（pd.read_htmlがパース可能な最小限のHTML）
    empty_html = (
        "<html><head><title>Test</title></head><body>"
        "<table><tr><th>名前</th></tr><tr><td>テスト</td></tr></table>"
        "</body></html>"
    )
    mock_driver = MagicMock()
    mock_driver.page_source = empty_html

    with patch("scraping.past_performances.webdriver.Chrome", return_value=mock_driver):
        scraper = PastPerformancesScraper("9999999999")

    df = scraper.get_past_performances()

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 0
    assert list(df.columns) == PAST_PERFORMANCES_COLUMNS


# ---------------------------------------------------------------------------
# 準正常系: WebDriverの起動エラー
# ---------------------------------------------------------------------------
def test_driver_error_on_startup_failure() -> None:
    """ChromeDriverの起動に失敗した場合にDriverErrorが発生すること"""
    with patch(
        "scraping.past_performances.webdriver.Chrome",
        side_effect=Exception("ChromeDriver not found"),
    ):
        with pytest.raises(DriverError, match="ChromeDriverの起動に失敗しました"):
            PastPerformancesScraper("2022105081")


# ---------------------------------------------------------------------------
# 準正常系: HTML構造の変化（テーブルがない、必須カラムがない）
# ---------------------------------------------------------------------------
def test_no_html_table_raises_parse_error() -> None:
    """HTMLにtable要素が存在しない場合にParseErrorが発生すること"""
    no_table_html = "<html><head><title>Test</title></head><body><div>no table</div></body></html>"
    mock_driver = MagicMock()
    mock_driver.page_source = no_table_html

    with patch("scraping.past_performances.webdriver.Chrome", return_value=mock_driver):
        scraper = PastPerformancesScraper("9999999998")

    with pytest.raises(ParseError, match="HTML内にテーブルが見つかりません"):
        scraper.get_past_performances()


def test_missing_required_columns_raises_parse_error() -> None:
    """馬柱テーブルの必須カラムが不足している場合にParseErrorが発生すること"""
    missing_cols_html = (
        "<html><head><title>Test</title></head><body>"
        "<table>"
        "<tr>"
        "<th>日付</th><th>騎手</th><th>A1</th><th>A2</th><th>A3</th><th>A4</th><th>A5</th>"
        "<th>A6</th><th>A7</th><th>A8</th><th>A9</th><th>A10</th><th>A11</th><th>A12</th>"
        "<th>A13</th>"
        "</tr>"
        "<tr>"
        "<td>2026/01/01</td><td>テスト騎手</td><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td>"
        "<td>6</td><td>7</td><td>8</td><td>9</td><td>10</td><td>11</td><td>12</td><td>13</td>"
        "</tr>"
        "</table>"
        "</body></html>"
    )
    mock_driver = MagicMock()
    mock_driver.page_source = missing_cols_html

    with patch("scraping.past_performances.webdriver.Chrome", return_value=mock_driver):
        scraper = PastPerformancesScraper("9999999997")

    with pytest.raises(ParseError, match="必須カラムが不足しています"):
        scraper.get_past_performances()


# ---------------------------------------------------------------------------
# 準正常系: 距離カラムに芝/ダ/障のいずれも含まない値がある場合
# ---------------------------------------------------------------------------
def test_invalid_turf_dirt_raises_parse_error() -> None:
    """距離カラムに芝/ダ/障を含まない値がある場合にParseErrorが発生すること"""
    invalid_distance_html = (
        "<html><head><title>Test</title></head><body>"
        "<table class='db_h_race_results'>"
        "<tr>"
        "<th>日付</th><th>開催</th><th>天気</th><th>R</th><th>レース名</th>"
        "<th>映像</th><th>頭数</th><th>枠番</th><th>馬番</th><th>オッズ</th>"
        "<th>人気</th><th>着順</th><th>騎手</th><th>斤量</th><th>距離</th>"
        "<th>馬場</th><th>タイム</th><th>着差</th><th>通過</th><th>ペース</th>"
        "<th>上り</th><th>馬体重</th><th>賞金</th>"
        "</tr>"
        "<tr>"
        "<td>2026/01/01</td><td>5東京8</td><td>晴</td><td>11</td>"
        "<td>テストレース</td><td></td><td>16</td><td>3</td><td>5</td>"
        "<td>10.0</td><td>3</td><td>1</td>"
        "<td><a href='/jockey/result/recent/01234/'>テスト騎手</a></td>"
        "<td>57.0</td><td>X1200</td><td>良</td><td>1:12.0</td><td>1/2</td>"
        "<td>3-3</td><td>34.5-35.0</td><td>34.0</td><td>480(+2)</td><td>1000</td>"
        "</tr>"
        "</table>"
        "</body></html>"
    )
    mock_driver = MagicMock()
    mock_driver.page_source = invalid_distance_html

    with patch("scraping.past_performances.webdriver.Chrome", return_value=mock_driver):
        scraper = PastPerformancesScraper("9999999996")

    with pytest.raises(ParseError, match="芝/ダ/障を判定できません"):
        scraper.get_past_performances()
