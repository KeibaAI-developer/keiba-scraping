"""PastPerformancesScraper.get_horse_basic_info()の単体テスト

Selenium WebDriverをモックし、フィクスチャHTMLを返すようにしてテストする。
馬の基本情報の取得・カラム構成・主要値を検証する。
"""

import pandas as pd
import pytest

from scraping.config import HORSE_BASIC_INFO_COLUMNS
from scraping.exceptions import ParseError
from scraping.past_performances import PastPerformancesScraper

from .conftest import create_scraper_from_fixture


# ---------------------------------------------------------------------------
# 正常系: カラムと形状
# ---------------------------------------------------------------------------
def test_columns_match_horse_basic_info_columns() -> None:
    """カラム構成がHORSE_BASIC_INFO_COLUMNSと一致すること"""
    scraper = create_scraper_from_fixture("2022105081")
    df = scraper.get_horse_basic_info()

    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == HORSE_BASIC_INFO_COLUMNS


def test_returns_single_row() -> None:
    """1行のDataFrameが返ること"""
    scraper = create_scraper_from_fixture("2022105081")
    df = scraper.get_horse_basic_info()

    assert len(df) == 1


# ---------------------------------------------------------------------------
# 正常系: ミュージアムマイル（2022105081）の具体値
# ---------------------------------------------------------------------------
def test_horse_name() -> None:
    """馬名が正しいこと"""
    scraper = create_scraper_from_fixture("2022105081")
    df = scraper.get_horse_basic_info()

    assert df.iloc[0]["馬名"] == "ミュージアムマイル"


def test_gender() -> None:
    """性別が正しいこと"""
    scraper = create_scraper_from_fixture("2022105081")
    df = scraper.get_horse_basic_info()

    assert df.iloc[0]["性別"] == "牡"


def test_age() -> None:
    """年齢が正しいこと"""
    scraper = create_scraper_from_fixture("2022105081")
    df = scraper.get_horse_basic_info()

    assert df.iloc[0]["年齢"] == 4


def test_birthday() -> None:
    """生年月日がyyyymmdd形式の整数であること"""
    scraper = create_scraper_from_fixture("2022105081")
    df = scraper.get_horse_basic_info()

    assert df.iloc[0]["生年月日"] == 20220110


def test_trainer() -> None:
    """調教師名が正しいこと"""
    scraper = create_scraper_from_fixture("2022105081")
    df = scraper.get_horse_basic_info()

    assert df.iloc[0]["調教師"] == "高柳大輔"


def test_trainer_id() -> None:
    """調教師IDが正しいこと"""
    scraper = create_scraper_from_fixture("2022105081")
    df = scraper.get_horse_basic_info()

    assert df.iloc[0]["調教師ID"] == "01159"


def test_affiliation() -> None:
    """所属が正しいこと"""
    scraper = create_scraper_from_fixture("2022105081")
    df = scraper.get_horse_basic_info()

    assert df.iloc[0]["所属"] == "栗東"


def test_owner() -> None:
    """馬主名が正しいこと"""
    scraper = create_scraper_from_fixture("2022105081")
    df = scraper.get_horse_basic_info()

    assert df.iloc[0]["馬主"] == "サンデーレーシング"


def test_owner_id() -> None:
    """馬主IDが正しいこと"""
    scraper = create_scraper_from_fixture("2022105081")
    df = scraper.get_horse_basic_info()

    assert df.iloc[0]["馬主ID"] == "226800"


def test_recruitment_info() -> None:
    """募集情報が正しいこと"""
    scraper = create_scraper_from_fixture("2022105081")
    df = scraper.get_horse_basic_info()

    assert df.iloc[0]["募集情報"] == "1口:100万円/40口"


def test_breeder() -> None:
    """生産者名が正しいこと"""
    scraper = create_scraper_from_fixture("2022105081")
    df = scraper.get_horse_basic_info()

    assert df.iloc[0]["生産者"] == "ノーザンファーム"


def test_breeder_id() -> None:
    """生産者IDが正しいこと"""
    scraper = create_scraper_from_fixture("2022105081")
    df = scraper.get_horse_basic_info()

    assert df.iloc[0]["生産者ID"] == "373126"


def test_production_area() -> None:
    """産地が正しいこと"""
    scraper = create_scraper_from_fixture("2022105081")
    df = scraper.get_horse_basic_info()

    assert df.iloc[0]["産地"] == "安平町"


def test_sale_price_is_nan() -> None:
    """セリ取引価格がNaNであること（セリ未出品の場合）"""
    scraper = create_scraper_from_fixture("2022105081")
    df = scraper.get_horse_basic_info()

    assert pd.isna(df.iloc[0]["セリ取引価格"])


def test_central_prize() -> None:
    """獲得賞金（中央）が万円単位の整数であること"""
    scraper = create_scraper_from_fixture("2022105081")
    df = scraper.get_horse_basic_info()

    assert df.iloc[0]["獲得賞金 (中央)"] == 96179


def test_local_prize() -> None:
    """獲得賞金（地方）が正しいこと"""
    scraper = create_scraper_from_fixture("2022105081")
    df = scraper.get_horse_basic_info()

    assert df.iloc[0]["獲得賞金 (地方)"] == 0


def test_career_record() -> None:
    """通算成績の形式が正しいこと"""
    scraper = create_scraper_from_fixture("2022105081")
    df = scraper.get_horse_basic_info()

    assert df.iloc[0]["通算成績"] == "5-2-1-2"


def test_notable_win() -> None:
    """主な勝鞍が正しいこと"""
    scraper = create_scraper_from_fixture("2022105081")
    df = scraper.get_horse_basic_info()

    assert df.iloc[0]["主な勝鞍"] == "25'有馬記念(G1)"


def test_related_horses() -> None:
    """近親馬が正しいこと"""
    scraper = create_scraper_from_fixture("2022105081")
    df = scraper.get_horse_basic_info()

    assert df.iloc[0]["近親馬"] == "フェスティバルヒル、ミュージアムヒルの2024"


def test_sire() -> None:
    """父馬名が正しいこと"""
    scraper = create_scraper_from_fixture("2022105081")
    df = scraper.get_horse_basic_info()

    assert df.iloc[0]["父"] == "リオンディーズ"


def test_sire_id() -> None:
    """父馬IDが正しいこと"""
    scraper = create_scraper_from_fixture("2022105081")
    df = scraper.get_horse_basic_info()

    assert df.iloc[0]["父ID"] == "2013105915"


def test_dam() -> None:
    """母馬名が正しいこと"""
    scraper = create_scraper_from_fixture("2022105081")
    df = scraper.get_horse_basic_info()

    assert df.iloc[0]["母"] == "ミュージアムヒル"


def test_dam_id() -> None:
    """母馬IDが正しいこと"""
    scraper = create_scraper_from_fixture("2022105081")
    df = scraper.get_horse_basic_info()

    assert df.iloc[0]["母ID"] == "2015105106"


def test_broodmare_sire() -> None:
    """母父馬名が正しいこと"""
    scraper = create_scraper_from_fixture("2022105081")
    df = scraper.get_horse_basic_info()

    assert df.iloc[0]["母父"] == "ハーツクライ"


def test_broodmare_sire_id() -> None:
    """母父馬IDが正しいこと"""
    scraper = create_scraper_from_fixture("2022105081")
    df = scraper.get_horse_basic_info()

    assert df.iloc[0]["母父ID"] == "2001103038"


def test_dam_dam() -> None:
    """母母馬名が正しいこと"""
    scraper = create_scraper_from_fixture("2022105081")
    df = scraper.get_horse_basic_info()

    assert df.iloc[0]["母母"] == "ロレットチャペル"


def test_dam_dam_id() -> None:
    """母母馬IDが正しいこと"""
    scraper = create_scraper_from_fixture("2022105081")
    df = scraper.get_horse_basic_info()

    assert df.iloc[0]["母母ID"] == "2003102866"


def test_sire_sire() -> None:
    """父父馬名が正しいこと"""
    scraper = create_scraper_from_fixture("2022105081")
    df = scraper.get_horse_basic_info()

    assert df.iloc[0]["父父"] == "キングカメハメハ"


def test_sire_sire_id() -> None:
    """父父馬IDが正しいこと"""
    scraper = create_scraper_from_fixture("2022105081")
    df = scraper.get_horse_basic_info()

    assert df.iloc[0]["父父ID"] == "2001103460"


def test_sire_dam() -> None:
    """父母馬名が正しいこと"""
    scraper = create_scraper_from_fixture("2022105081")
    df = scraper.get_horse_basic_info()

    assert df.iloc[0]["父母"] == "シーザリオ"


def test_sire_dam_id() -> None:
    """父母馬IDが正しいこと"""
    scraper = create_scraper_from_fixture("2022105081")
    df = scraper.get_horse_basic_info()

    assert df.iloc[0]["父母ID"] == "2002100844"


# ---------------------------------------------------------------------------
# 正常系: カランダガン（2021190001）- 外国馬のケース
# ---------------------------------------------------------------------------
def test_age_is_nan_for_retired_horse() -> None:
    """年齢情報がないページでは年齢がNaNであること"""
    scraper = create_scraper_from_fixture("2021190001")
    df = scraper.get_horse_basic_info()

    assert pd.isna(df.iloc[0]["年齢"])


def test_recruitment_info_is_nan_when_no_unit_price() -> None:
    """一口情報がないページでは募集情報がNaNであること"""
    scraper = create_scraper_from_fixture("2021190001")
    df = scraper.get_horse_basic_info()

    assert pd.isna(df.iloc[0]["募集情報"])


def test_gender_of_castrated_horse() -> None:
    """セン馬の性別が正しく取得されること"""
    scraper = create_scraper_from_fixture("2021190001")
    df = scraper.get_horse_basic_info()

    assert df.iloc[0]["性別"] == "セ"


# ---------------------------------------------------------------------------
# 正常系: ビコーズウイキャン（2021103695）- セリ取引価格あり
# ---------------------------------------------------------------------------
def test_sale_price_with_value() -> None:
    """セリ取引価格がある場合に万円単位の整数が返ること"""
    scraper = create_scraper_from_fixture("2021103695")
    df = scraper.get_horse_basic_info()

    assert df.iloc[0]["セリ取引価格"] == 176


def test_local_trainer_affiliation() -> None:
    """地方所属の調教師の所属が正しいこと"""
    scraper = create_scraper_from_fixture("2021103695")
    df = scraper.get_horse_basic_info()

    assert df.iloc[0]["所属"] == "浦和"


# ---------------------------------------------------------------------------
# 準正常系: HTML構造の欠如
# ---------------------------------------------------------------------------
def test_missing_horse_title_raises_parse_error() -> None:
    """horse_titleがない場合にParseErrorが発生すること"""
    minimal_html = (
        "<html><head></head><body>"
        "<table class='db_prof_table'><tr><th>生年月日</th><td>2022年1月1日</td></tr></table>"
        "</body></html>"
    )
    from unittest.mock import MagicMock, patch

    mock_driver = MagicMock()
    mock_driver.page_source = minimal_html
    with patch("scraping.past_performances.webdriver.Chrome", return_value=mock_driver):
        scraper = PastPerformancesScraper("9999999999")

    with pytest.raises(ParseError, match="horse_titleが見つかりません"):
        scraper.get_horse_basic_info()


def test_missing_prof_table_raises_parse_error() -> None:
    """db_prof_tableがない場合にParseErrorが発生すること"""
    minimal_html = (
        "<html><head></head><body>"
        "<div class='horse_title'><h1>テスト馬</h1><p class='txt_01'>牡4歳</p></div>"
        "</body></html>"
    )
    from unittest.mock import MagicMock, patch

    mock_driver = MagicMock()
    mock_driver.page_source = minimal_html
    with patch("scraping.past_performances.webdriver.Chrome", return_value=mock_driver):
        scraper = PastPerformancesScraper("9999999998")

    with pytest.raises(ParseError, match="db_prof_tableが見つかりません"):
        scraper.get_horse_basic_info()


def test_missing_blood_table_raises_parse_error() -> None:
    """blood_tableがない場合にParseErrorが発生すること"""
    minimal_html = (
        "<html><head></head><body>"
        "<div class='horse_title'><h1>テスト馬</h1><p class='txt_01'>牡4歳</p></div>"
        "<table class='db_prof_table'>"
        "<tr><th>生年月日</th><td>2022年1月1日</td></tr>"
        "<tr><th>調教師</th><td><a href='/trainer/01234/'>テスト師</a> (栗東)</td></tr>"
        "<tr><th>馬主</th><td><a href='/owner/12345/'>テスト馬主</a></td></tr>"
        "<tr><th>生産者</th><td><a href='/breeder/67890/'>テスト牧場</a></td></tr>"
        "<tr><th>産地</th><td>安平町</td></tr>"
        "<tr><th>セリ取引価格</th><td>-</td></tr>"
        "<tr><th>獲得賞金 (中央)</th><td>0万円</td></tr>"
        "<tr><th>獲得賞金 (地方)</th><td>0万円</td></tr>"
        "<tr><th>通算成績</th><td>[1-0-0-0]</td></tr>"
        "<tr><th>主な勝鞍</th><td><a href='/race/000/'>テストレース</a></td></tr>"
        "<tr><th>近親馬</th><td></td></tr>"
        "</table>"
        "</body></html>"
    )
    from unittest.mock import MagicMock, patch

    mock_driver = MagicMock()
    mock_driver.page_source = minimal_html
    with patch("scraping.past_performances.webdriver.Chrome", return_value=mock_driver):
        scraper = PastPerformancesScraper("9999999997")

    with pytest.raises(ParseError, match="blood_tableが見つかりません"):
        scraper.get_horse_basic_info()
