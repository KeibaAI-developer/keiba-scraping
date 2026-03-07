"""共通ユーティリティモジュール

URL構築関数、データ変換関数、Chromeオプション設定など
ライブラリ内で必要なユーティリティ関数を集約する。
"""

import datetime
import re
from io import StringIO
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
from selenium.webdriver.chrome.options import Options

from scraping.config import ID_TO_KEIBAJO_DICT, KEIBAJO_TO_ID_DICT, ScrapingConfig

if TYPE_CHECKING:
    from requests import Session


# ---------------------------------------------------------------------------
# URL構築関数
# ---------------------------------------------------------------------------
def build_race_list_url(year: int, page_num: int, config: ScrapingConfig | None = None) -> str:
    """netkeibaのレース一覧ページのURLを作成する

    Args:
        year (int): 年
        page_num (int): ページ番号
        config (ScrapingConfig | None): 設定オブジェクト

    Returns:
        str: URL
    """
    cfg = config or ScrapingConfig()
    return (
        f"{cfg.netkeiba_base_url}/"
        f"?pid=race_list&word="
        f"&start_year={year}&start_mon=1"
        f"&end_year={year}&end_mon=12"
        f"&jyo%5B%5D=01&jyo%5B%5D=02&jyo%5B%5D=03&jyo%5B%5D=04"
        f"&jyo%5B%5D=05&jyo%5B%5D=06&jyo%5B%5D=07&jyo%5B%5D=08"
        f"&jyo%5B%5D=09&jyo%5B%5D=10"
        f"&kyori_min=&kyori_max=&sort=date&list=100&page={page_num}"
    )


def build_today_race_list_url(
    year: int, month: int, day: int, config: ScrapingConfig | None = None
) -> str:
    """netkeibaの日別レース一覧ページのURLを作成する

    Args:
        year (int): 年
        month (int): 月
        day (int): 日
        config (ScrapingConfig | None): 設定オブジェクト

    Returns:
        str: URL
    """
    cfg = config or ScrapingConfig()
    return f"{cfg.netkeiba_race_url}/top/race_list.html" f"?kaisai_date={year}{month:02}{day:02}"


def build_result_url(race_id: str, config: ScrapingConfig | None = None) -> str:
    """netkeibaのレース結果ページのURLを作成する

    Args:
        race_id (str): レースID
        config (ScrapingConfig | None): 設定オブジェクト

    Returns:
        str: URL
    """
    cfg = config or ScrapingConfig()
    return f"{cfg.netkeiba_race_url}/race/result.html?race_id={race_id}"


def build_entry_url(race_id: str, config: ScrapingConfig | None = None) -> str:
    """netkeibaの出馬表ページのURLを作成する

    Args:
        race_id (str): レースID
        config (ScrapingConfig | None): 設定オブジェクト

    Returns:
        str: URL
    """
    cfg = config or ScrapingConfig()
    return f"{cfg.netkeiba_race_url}/race/shutuba.html?race_id={race_id}"


def build_horse_info_url(horse_id: str, config: ScrapingConfig | None = None) -> str:
    """netkeibaの馬情報ページのURLを作成する

    Args:
        horse_id (str): 馬ID
        config (ScrapingConfig | None): 設定オブジェクト

    Returns:
        str: URL
    """
    cfg = config or ScrapingConfig()
    return f"{cfg.netkeiba_base_url}/horse/{horse_id}"


def build_horse_list_url(year: int, page_num: int, config: ScrapingConfig | None = None) -> str:
    """netkeibaの競走馬一覧ページのURLを作成する

    Args:
        year (int): 年
        page_num (int): ページ番号
        config (ScrapingConfig | None): 設定オブジェクト

    Returns:
        str: URL
    """
    cfg = config or ScrapingConfig()
    return f"{cfg.netkeiba_base_url}/?pid=horse_list&birthyear={year}&list=100&page={page_num}"


def build_odds_url(race_id: str, config: ScrapingConfig | None = None) -> str:
    """netkeibaのオッズページのURLを作成する

    Args:
        race_id (str): レースID
        config (ScrapingConfig | None): 設定オブジェクト

    Returns:
        str: URL
    """
    cfg = config or ScrapingConfig()
    return f"{cfg.netkeiba_race_url}/odds/index.html?race_id={race_id}"


def build_odds_api_url(race_id: str, config: ScrapingConfig | None = None) -> str:
    """netkeibaのオッズAPIのURLを作成する

    Args:
        race_id (str): レースID
        config (ScrapingConfig | None): 設定オブジェクト

    Returns:
        str: URL
    """
    cfg = config or ScrapingConfig()
    return f"{cfg.netkeiba_race_url}/api/api_get_jra_odds.html?race_id={race_id}&type=1"


# ---------------------------------------------------------------------------
# データ変換関数
# ---------------------------------------------------------------------------
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


def get_race_info_from_past_performances(
    past_performances_df: pd.DataFrame, race_index: int
) -> tuple[str, str, int | float, str]:
    """馬柱からレースIDなどの情報を取得する

    KeibaAIの``get_race_info_from_umabashira``に対応する関数。
    日付IDは含まない。

    Args:
        past_performances_df (pd.DataFrame): 馬柱のデータフレーム
        race_index (int): データフレームのインデックス。race_index+1走前の情報を取得する

    Returns:
        str: race_index行目のレースID
        str: 主催（"中央","地方","海外"のいずれか）
        int | float: レース間隔日数（前走が存在しなければNaN）
        str: 競馬場

    Raises:
        ValueError: 馬柱が1行もなかった場合、または未知の競馬場名が指定された場合
    """
    if len(past_performances_df) == 0:
        raise ValueError("馬柱が1行もありません")

    # レース日
    race_date = past_performances_df["日付"].iloc[race_index]  # "yyyy/mm/dd"
    year = race_date[0:4]
    month = race_date[5:7]
    day = race_date[8:10]

    # 開催日
    kai = past_performances_df["回"].iloc[race_index]
    kaisai_day = past_performances_df["開催日"].iloc[race_index]

    # R
    r_value = past_performances_df["R"].iloc[race_index]
    if not pd.isna(r_value):
        race_num = r_value
    else:
        race_num = "00"

    # 競馬場
    raw_keibajo: str = past_performances_df["競馬場"].iloc[race_index]
    keibajo: str = raw_keibajo.strip() if isinstance(raw_keibajo, str) else raw_keibajo

    # レースIDと主催の作成
    if _is_katakana(keibajo):
        # 海外の場合（競馬場がカタカナ表記）
        race_id = ""
        organize = "海外"
    else:
        # 国内の場合は競馬場名が辞書に存在することを要求する
        try:
            keibajo_id = KEIBAJO_TO_ID_DICT[keibajo]
        except KeyError as exc:
            raise ValueError(f"未知の競馬場名です: {keibajo!r}") from exc

        if pd.isna(kai):
            # 地方の場合
            race_id = f"{year}{keibajo_id}{month}{day}{int(race_num):02}"
            organize = "地方"
        else:
            # 中央の場合
            race_id = f"{year}{keibajo_id}{int(kai):02}{int(kaisai_day):02}{int(race_num):02}"
            organize = "中央"

    # レース間隔
    interval: int | float = np.nan
    for i in range(race_index + 1, len(past_performances_df)):
        if not pd.isna(past_performances_df["人気"].iloc[i]):
            date1 = past_performances_df["日付"].iloc[race_index]
            date2 = past_performances_df["日付"].iloc[i]
            interval = calc_interval(date1, date2)
            break

    return race_id, organize, interval, keibajo


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

    ``<table>`` 要素が1つ以上含まれていればページが存在すると判定する。

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


# ---------------------------------------------------------------------------
# プライベート関数
# ---------------------------------------------------------------------------
def _is_katakana(text: str) -> bool:
    """文字列が全てカタカナかどうかを判定する

    Args:
        text (str): 判定対象の文字列

    Returns:
        bool: 全てカタカナならTrue
    """
    katakana_pattern = r"^[ァ-ヶー]+$"
    return re.match(katakana_pattern, text) is not None
