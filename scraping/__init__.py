"""keiba-scraping: netkeibaおよびJRAから競馬データをスクレイピングするライブラリ

このライブラリは、netkeibaおよびJRAの公式サイトから競馬データを
スクレイピングし、pandas.DataFrameとして取得するためのインターフェースを提供します。
"""

try:
    from importlib.metadata import PackageNotFoundError, version

    __version__ = version("keiba-scraping")
except (PackageNotFoundError, ImportError):
    __version__ = "unknown"

from scraping.config import (
    AFFILIATION_MAP,
    ENTRY_COLUMNS,
    ENTRY_NON_NAN_COLUMNS,
    GRADE_DICT,
    HORSE_INFO_COLUMNS,
    ID_TO_KEIBAJO_DICT,
    JRA_GRADED_RACE_COLUMNS,
    KEIBAJO_TO_ID_DICT,
    ODDS_COLUMNS,
    PAST_PERFORMANCES_COLUMNS,
    PAYBACK_COLUMNS,
    RACE_INFO_COLUMNS,
    RACE_LIST_COLUMNS,
    RACE_SCHEDULE_COLUMNS,
    RESULT_COLUMNS,
    THREE_COMBINATION_BETS,
    TWO_COMBINATION_BETS,
    VALID_ENTRY_STATUSES,
    WEIGHT_CONDITIONS,
    YOSO_ODDS_COLUMNS,
    ScrapingConfig,
)
from scraping.entry_page import EntryPageScraper
from scraping.exceptions import (
    DriverError,
    NetworkError,
    PageNotFoundError,
    ParseError,
    ScrapingError,
)
from scraping.horse_info import HorseInfoScraper
from scraping.jra_graded_race import JraGradedRaceScraper
from scraping.odds import (
    scrape_odds_from_jra,
    scrape_odds_from_netkeiba,
    scrape_yoso_odds_from_netkeiba,
)
from scraping.past_performances import PastPerformancesScraper
from scraping.race_info import scrape_race_info
from scraping.race_list import RaceListScraper
from scraping.race_schedule import RaceScheduleScraper
from scraping.result_page import ResultPageScraper
from scraping.utils import (
    build_entry_url,
    build_horse_info_url,
    build_horse_list_url,
    build_jra_graded_race_url,
    build_odds_api_url,
    build_odds_url,
    build_race_list_url,
    build_result_url,
    build_today_race_list_url,
    calc_interval,
    get_race_info_from_past_performances,
    is_race_existence,
    judge_turf_dirt,
    race_id_to_race_info,
    set_chrome_options,
)

__all__ = [
    # config
    "ScrapingConfig",
    "KEIBAJO_TO_ID_DICT",
    "ID_TO_KEIBAJO_DICT",
    "GRADE_DICT",
    "WEIGHT_CONDITIONS",
    "PAYBACK_COLUMNS",
    "TWO_COMBINATION_BETS",
    "THREE_COMBINATION_BETS",
    "RESULT_COLUMNS",
    "ENTRY_COLUMNS",
    "RACE_INFO_COLUMNS",
    "PAST_PERFORMANCES_COLUMNS",
    "HORSE_INFO_COLUMNS",
    "AFFILIATION_MAP",
    "RACE_LIST_COLUMNS",
    "RACE_SCHEDULE_COLUMNS",
    "JRA_GRADED_RACE_COLUMNS",
    "ODDS_COLUMNS",
    "YOSO_ODDS_COLUMNS",
    # exceptions
    "ScrapingError",
    "PageNotFoundError",
    "ParseError",
    "NetworkError",
    "DriverError",
    # utils
    "build_race_list_url",
    "build_today_race_list_url",
    "build_result_url",
    "build_entry_url",
    "build_horse_info_url",
    "build_horse_list_url",
    "build_odds_url",
    "build_jra_graded_race_url",
    "build_odds_api_url",
    "judge_turf_dirt",
    "race_id_to_race_info",
    "get_race_info_from_past_performances",
    "calc_interval",
    "set_chrome_options",
    "is_race_existence",
    # race_info
    "scrape_race_info",
    # entry_page
    "EntryPageScraper",
    "ENTRY_NON_NAN_COLUMNS",
    "VALID_ENTRY_STATUSES",
    # result_page
    "ResultPageScraper",
    # past_performances
    "PastPerformancesScraper",
    # race_list
    "RaceListScraper",
    # race_schedule
    "RaceScheduleScraper",
    # jra_graded_race
    "JraGradedRaceScraper",
    # horse_info
    "HorseInfoScraper",
    # odds
    "scrape_odds_from_netkeiba",
    "scrape_yoso_odds_from_netkeiba",
    "scrape_odds_from_jra",
]
