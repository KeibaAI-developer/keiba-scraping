"""共通ユーティリティモジュール

データ変換関数、Chromeオプション設定など
ライブラリ内で必要なユーティリティ関数を集約する。
"""

import datetime
import logging
import re
from email.message import Message
from io import StringIO
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
from bs4 import Tag
from keiba_domain import parse_turf_dirt
from selenium.webdriver.chrome.options import Options

from scraping.config import ID_TO_KEIBAJO_DICT, ScrapingConfig
from scraping.exceptions import ParseError

if TYPE_CHECKING:
    from requests import Response, Session


def judge_turf_dirt(turf_dirt_text: str) -> str:
    """芝かダートか障害か判定する

    芝ダ（keiba_domainの ``TurfDirt``）と平地/障害（``RaceShubetsu``）はドメイン上
    別概念だが、netkeibaのHTMLは障害レースの距離欄を「障2880m」と表記し芝ダの位置に
    「障」が入る。この関数はnetkeiba表記のパースとして3値を返す。

    Args:
        turf_dirt_text (str): "芝","ダ","障"を含む文字列

    Returns:
        str: "芝","ダ","障"のいずれか。判定不能の場合は空文字
    """
    if "障" in turf_dirt_text:  # netkeibaは障害レースの距離欄を「障2880m」と表記する
        return "障"
    turf_dirt = parse_turf_dirt(turf_dirt_text)
    return str(turf_dirt) if turf_dirt is not None else ""


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


def extract_id_from_td(td_element: Tag, id_pattern: str, logger: logging.Logger) -> str | float:
    """td要素内のaタグのhrefからnetkeibaのIDを抽出する

    パス末尾のID（例: /horse/2022105081/）と、
    idクエリのID（例: /trainer/race.html?id=01159）に対応する。

    Args:
        td_element (Tag): td要素
        id_pattern (str): IDの形式を表す正規表現
        logger (logging.Logger): エラー出力先のロガー

    Returns:
        str | float: IDの文字列。リンクがない場合はNaN

    Raises:
        ParseError: リンクはあるがIDが期待する形式でない場合
    """
    a_tag = td_element.find("a")
    if not isinstance(a_tag, Tag):
        return np.nan
    href = str(a_tag.get("href", ""))
    match = re.search(rf"(?:/|[?&]id=)({id_pattern})/?$", href)
    if match is None:
        logger.error("IDが期待する形式ではありません: %s", href)
        raise ParseError(f"IDが期待する形式ではありません: {href}")
    return match.group(1)


def resolve_response_encoding(response: "Response") -> str | None:
    """レスポンスのデコードに使うエンコーディングを決定する

    Content-Typeヘッダのcharset指定を優先し、指定が無い場合のみ本文から推定する。
    requestsはcharsetを持たない ``text/*`` にISO-8859-1を既定値として設定し、
    明示指定と区別できなくなるため、``response.encoding`` ではなく
    Content-Typeヘッダを直接解析してcharsetの有無を判定する。

    netkeibaはrace配下がUTF-8をヘッダで通知する一方、db配下とJRAはcharsetを
    通知せずそれぞれEUC-JP、Shift_JISを返すため、両者を区別せず扱える。

    Args:
        response (Response): requestsのレスポンス

    Returns:
        str | None: 使用すべきエンコーディング名。推定できない場合はNone
    """
    content_type = Message()
    content_type["Content-Type"] = response.headers.get("Content-Type", "")
    header_encoding = content_type.get_content_charset()
    if header_encoding is not None:
        return header_encoding
    return response.apparent_encoding


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
    html.encoding = resolve_response_encoding(html)

    try:
        tables = pd.read_html(StringIO(html.text))
        return len(tables) > 0
    except Exception:
        return False
