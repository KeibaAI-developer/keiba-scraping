"""共通ユーティリティモジュール

データ変換関数、Chromeオプション設定など
ライブラリ内で必要なユーティリティ関数を集約する。
"""

import datetime
from io import StringIO
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
from selenium.webdriver.chrome.options import Options

from scraping.config import ID_TO_KEIBAJO_DICT, ScrapingConfig

if TYPE_CHECKING:
    from requests import Session


def judge_turf_dirt(turf_dirt_text: str) -> str:
    """芝かダートか障害か判定する

    Args:
        turf_dirt_text (str): "芝","ダ","障"を含む文字列

    Returns:
        str: "芝","ダ","障"のいずれか。判定不能の場合は空文字
    """
    if "障" in turf_dirt_text:
        return "障"
    elif "芝" in turf_dirt_text:
        return "芝"
    elif "ダ" in turf_dirt_text:
        return "ダ"
    else:
        return ""


def race_id_to_race_info(race_id: str) -> tuple[int, str, int, int, int]:
    """レースIDから年・競馬場・回・日・Rの情報を抽出する

    Args:
        race_id (str): netkeibaのレースID（12桁文字列）

    Returns:
        int: 年
        str: 競馬場名
        int: 回
        int: 日
        int: R
    """
    race_id = str(race_id)
    year = int(race_id[0:4])
    keibajo = ID_TO_KEIBAJO_DICT[race_id[4:6]]
    kai = int(race_id[6:8])
    day = int(race_id[8:10])
    race = int(race_id[10:12])
    return year, keibajo, kai, day, race


def calc_interval(date1: str, date2: str) -> int | float:
    """2つの日付間のレース間隔（日数）を計算する

    Args:
        date1 (str): "YYYY/MM/DD"の日付文字列
        date2 (str): "YYYY/MM/DD"の日付文字列

    Returns:
        int | float: date1とdate2の間隔日数（絶対値）。パース失敗時はNaN
    """
    try:
        date_format = "%Y/%m/%d"
        date1_dt = datetime.datetime.strptime(date1, date_format)
        date2_dt = datetime.datetime.strptime(date2, date_format)
        return abs((date1_dt - date2_dt).days)
    except (ValueError, TypeError):
        return np.nan


def set_chrome_options() -> Options:
    """ChromeDriverのオプション設定を返す

    Returns:
        Options: ヘッドレスモード等を設定済みのChromeオプション
    """
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return options


def is_race_existence(url: str, session: "Session", config: ScrapingConfig | None = None) -> bool:
    """レース結果ページが存在するかを判定する

    <table> 要素が1つ以上含まれていればページが存在すると判定する。

    Args:
        url (str): 結果払い戻しのページのURL
        session (Session): requests.Sessionのインスタンス
        config (ScrapingConfig | None): 設定オブジェクト

    Returns:
        bool: ページが存在すればTrue
    """
    cfg = config or ScrapingConfig()
    html = session.get(url, headers=cfg.headers, timeout=cfg.request_timeout)
    html.encoding = "EUC-JP"

    try:
        tables = pd.read_html(StringIO(html.text))
        return len(tables) > 0
    except Exception:
        return False
