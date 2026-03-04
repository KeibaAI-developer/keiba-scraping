"""レース一覧スクレイパーモジュール"""

import datetime
import logging
import re
import time
import warnings

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup, Tag

from scraping.config import AFFILIATION_MAP, RACE_LIST_COLUMNS, ScrapingConfig
from scraping.exceptions import NetworkError, PageNotFoundError, ParseError
from scraping.utils import build_race_list_url, judge_turf_dirt, race_id_to_race_info

# pandasのFutureWarningを無視する（pandas 3.0以降の警告対策）
warnings.filterwarnings("ignore", category=FutureWarning)

logger = logging.getLogger(__name__)


class RaceListScraper:
    """レース一覧スクレイパークラス

    Attributes:
        year (int): 検索対象の年
        max_page_num (int): レース一覧ページの最大ページ数
        session (requests.Session): HTTPセッション
        config (ScrapingConfig): スクレイピング設定
    """

    def __init__(
        self,
        year: int,
        session: requests.Session | None = None,
        config: ScrapingConfig | None = None,
    ) -> None:
        """初期化

        Args:
            year (int): 検索対象の年
            session (requests.Session | None): HTTPセッション。省略時は新規作成
            config (ScrapingConfig | None): 設定オブジェクト
        """
        self.year = year
        self.config = config or ScrapingConfig()
        self.session: requests.Session = session or requests.Session()

        self.max_page_num = self._scrape_max_page_num()

    def get_race_list(self, sleep: float = 1.0) -> pd.DataFrame:
        """全ページ分のレース一覧を取得する

        Args:
            sleep (float): 連続リクエスト間のスリープ秒数。デフォルト1.0秒

        Returns:
            pd.DataFrame: RACE_LIST_COLUMNSのカラムを持つDataFrame
        """
        frames: list[pd.DataFrame] = []
        for page_num in range(1, self.max_page_num + 1):
            if page_num > 1:
                time.sleep(sleep)
            page_df = self.scrape_one_page(page_num)
            frames.append(page_df)
        if frames:
            return pd.concat(frames, ignore_index=True)
        return pd.DataFrame(columns=RACE_LIST_COLUMNS)

    def scrape_one_page(self, page_num: int) -> pd.DataFrame:
        """指定ページのレース一覧を取得する

        Args:
            page_num (int): ページ番号

        Returns:
            pd.DataFrame: 1ページ分のレース一覧（RACE_LIST_COLUMNSのカラム、最大100行）

        Raises:
            NetworkError: ページの取得に失敗した場合
            PageNotFoundError: ページが見つからない場合
            ParseError: テーブルの解析に失敗した場合
        """
        url = build_race_list_url(self.year, page_num, self.config)

        # HTML取得
        try:
            html = self.session.get(
                url, headers=self.config.headers, timeout=self.config.request_timeout
            )
            html.raise_for_status()
        except requests.exceptions.HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else None
            if status_code == 404:
                raise PageNotFoundError(f"レース一覧ページが見つかりません: {url}") from exc
            raise NetworkError(f"HTTPエラーが発生しました: {exc}") from exc
        except requests.exceptions.RequestException as exc:
            raise NetworkError(f"ネットワークエラーが発生しました: {exc}") from exc

        html.encoding = "EUC-JP"
        soup = BeautifulSoup(html.text, "html.parser")

        return self._parse_race_list_page(soup)

    def _parse_race_list_page(self, soup: BeautifulSoup) -> pd.DataFrame:
        """BeautifulSoupオブジェクトからレース一覧を抽出する

        Args:
            soup (BeautifulSoup): レース一覧ページのBeautifulSoup

        Returns:
            pd.DataFrame: RACE_LIST_COLUMNSのカラムを持つDataFrame

        Raises:
            ParseError: テーブルの解析に失敗した場合
        """
        table = soup.find("table", class_="nk_tb_common race_table_01")
        if not isinstance(table, Tag):
            raise ParseError("レース一覧テーブルが見つかりません")

        trs = table.find_all("tr")
        if len(trs) <= 1:
            return pd.DataFrame(columns=RACE_LIST_COLUMNS)

        rows: list[dict[str, object]] = []
        for i in range(1, len(trs)):
            tds = trs[i].find_all("td")
            if len(tds) < 16:
                logger.warning("列数が不足しています (row=%d, columns=%d)", i, len(tds))
                continue
            row = self._parse_row(tds)
            rows.append(row)

        if not rows:
            return pd.DataFrame(columns=RACE_LIST_COLUMNS)

        result_df = pd.DataFrame(rows, columns=RACE_LIST_COLUMNS)
        return result_df

    def _parse_row(self, tds: list[Tag]) -> dict[str, object]:
        """1行分のtd要素からレース情報を抽出する

        Args:
            tds (list[Tag]): td要素のリスト

        Returns:
            dict[str, object]: RACE_LIST_COLUMNSのキーを持つ辞書

        Raises:
            ParseError: 数値項目（R、距離、頭数）のパースに失敗した場合
        """
        # レースID (td[4]: レース名のリンクから)
        race_id = _extract_race_id(tds[4])

        # レースIDからrace_id_to_race_infoで情報取得
        _, keibajo, kai, kaisai_day, race_num = race_id_to_race_info(race_id)

        # 日付 (td[0]: 開催日のリンクから "yyyy/mm/dd")
        date_text = tds[0].text.strip()
        date_obj = _parse_date(date_text)

        # 天候 (td[2])
        weather = tds[2].text.strip()

        # R (td[3])
        try:
            r_value = int(tds[3].text.strip())
        except ValueError as exc:
            raise ParseError(f"Rのパースに失敗しました: {tds[3].text.strip()}") from exc

        # レース名 (td[4])
        race_name = tds[4].text.strip()

        # 距離 (td[6]: "芝1200", "ダ1800" など)
        distance_text = tds[6].text.strip()
        turf_dirt = judge_turf_dirt(distance_text)
        distance_match = re.search(r"\d+", distance_text)
        if distance_match is None:
            raise ParseError(f"距離のパースに失敗しました: {distance_text}")
        distance = int(distance_match.group())

        # 頭数 (td[7])
        try:
            num_runners = int(tds[7].text.strip())
        except ValueError as exc:
            raise ParseError(f"頭数のパースに失敗しました: {tds[7].text.strip()}") from exc

        # 馬場 (td[8])
        baba = tds[8].text.strip()

        # タイム (td[9])
        time_text = tds[9].text.strip()

        # ペース (td[10]: "36.7-40.5" → レース前3F, レース後3F)
        pace_text = tds[10].text.strip()
        pace_first, pace_last = _parse_pace(pace_text)

        # 勝ち馬 (td[11])
        winner_name = tds[11].text.strip()
        winner_id = _extract_id_from_link(tds[11])

        # 騎手 (td[12])
        jockey_name = tds[12].text.strip()
        jockey_id = _extract_id_from_link(tds[12])

        # 調教師 (td[13]: "[東]小手川準" → 所属="美浦", 厩舎="小手川準")
        trainer_text = tds[13].text.strip()
        affiliation, trainer_name = _parse_trainer(trainer_text)
        trainer_id = _extract_id_from_link(tds[13])

        # 2着馬 (td[14])
        second_name = tds[14].text.strip()
        second_id = _extract_id_from_link(tds[14])

        # 3着馬 (td[15])
        third_name = tds[15].text.strip()
        third_id = _extract_id_from_link(tds[15])

        return {
            "レースID": race_id,
            "日付": date_obj,
            "競馬場": keibajo,
            "回": kai,
            "開催日": kaisai_day,
            "天候": weather,
            "R": r_value,
            "レース名": race_name,
            "芝ダ": turf_dirt,
            "距離": distance,
            "頭数": num_runners,
            "馬場": baba,
            "タイム": time_text,
            "レース前3F": pace_first,
            "レース後3F": pace_last,
            "勝ち馬": winner_name,
            "勝ち馬ID": winner_id,
            "騎手": jockey_name,
            "騎手ID": jockey_id,
            "所属": affiliation,
            "厩舎": trainer_name,
            "厩舎ID": trainer_id,
            "2着馬": second_name,
            "2着馬ID": second_id,
            "3着馬": third_name,
            "3着馬ID": third_id,
        }

    def _scrape_max_page_num(self) -> int:
        """レース一覧ページの最大ページ数を取得する

        Returns:
            int: 最大ページ数

        Raises:
            NetworkError: ページの取得に失敗した場合
            PageNotFoundError: ページが見つからない場合
            ParseError: 最大ページ数の取得に失敗した場合
        """
        url = build_race_list_url(self.year, 1, self.config)
        try:
            html = self.session.get(
                url, headers=self.config.headers, timeout=self.config.request_timeout
            )
            html.raise_for_status()
        except requests.exceptions.HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else None
            if status_code == 404:
                raise PageNotFoundError(f"レース一覧ページが見つかりません: {url}") from exc
            raise NetworkError(f"HTTPエラーが発生しました: {exc}") from exc
        except requests.exceptions.RequestException as exc:
            raise NetworkError(f"ネットワークエラーが発生しました: {exc}") from exc

        html.encoding = "EUC-JP"
        soup = BeautifulSoup(html.text, "html.parser")
        pager = soup.find("div", class_="pager")
        if pager is None:
            raise ParseError("ページャーが見つかりません")

        # 正規表現でカンマ付きの数値を探す（例: "594件中1~100件目" → 594）
        match = re.search(r"\d{1,3}(?:,\d{3})?", pager.text)
        if match:
            total_count = int(match.group().replace(",", ""))
        else:
            raise ParseError("レース一覧の総件数の取得に失敗しました")

        # 100件ごとに1ページなので切り上げでページ数を算出
        return (total_count + 99) // 100


def _extract_race_id(td_element: Tag) -> str:
    """td要素内のaタグからレースIDを抽出する

    Args:
        td_element (Tag): td要素

    Returns:
        str: レースID（12桁文字列）

    Raises:
        ParseError: レースIDが取得できない場合
    """
    a_tag = td_element.find("a")
    if not isinstance(a_tag, Tag):
        raise ParseError("レースIDのリンクが見つかりません")
    href = str(a_tag.get("href", ""))
    match = re.search(r"(?:race_id=|/race/)(\d{12})", href)
    if match is None:
        raise ParseError(f"レースIDが抽出できません: {href}")
    return match.group(1)


def _extract_id_from_link(td_element: Tag) -> str | float:
    """td要素内のaタグのhrefからIDを抽出する

    Args:
        td_element (Tag): td要素

    Returns:
        str | float: IDの文字列。リンクがない場合はNaN
    """
    a_tag = td_element.find("a")
    if not isinstance(a_tag, Tag):
        return np.nan
    href = str(a_tag.get("href", ""))
    match = re.search(r"/(\d{5}|\d{10})(?:/|$)", href)
    if match is None:
        return np.nan
    return match.group(1)


def _parse_date(date_text: str) -> datetime.date:
    """日付文字列をdatetime.dateに変換する

    Args:
        date_text (str): "yyyy/mm/dd" 形式の日付文字列

    Returns:
        datetime.date: 日付オブジェクト

    Raises:
        ParseError: 日付のパースに失敗した場合
    """
    try:
        return datetime.datetime.strptime(date_text, "%Y/%m/%d").date()
    except ValueError as exc:
        raise ParseError(f"日付のパースに失敗しました: {date_text}") from exc


def _parse_pace(pace_text: str) -> tuple[float, float]:
    """ペース文字列を前半3Fと後半3Fに分割する

    Args:
        pace_text (str): "36.7-40.5" 形式のペース文字列

    Returns:
        tuple[float, float]: レース前3F, レース後3F

    Raises:
        ParseError: ペース文字列のパースに失敗した場合
    """
    match = re.match(r"([\d.]+)-([\d.]+)", pace_text)
    if match:
        return float(match.group(1)), float(match.group(2))
    raise ParseError(f"ペースのパースに失敗しました: {pace_text}")


def _parse_trainer(trainer_text: str) -> tuple[str, str]:
    """調教師テキストから所属と調教師名を分離する

    Args:
        trainer_text (str): "[東]小手川準" 形式のテキスト

    Returns:
        str: 所属（"美浦","栗東","地方","海外"のいずれか）
        str: 調教師名
    """
    match = re.match(r"\[(.+?)\](.+)", trainer_text)
    if match:
        code = match.group(1)
        name = match.group(2)
        affiliation = AFFILIATION_MAP.get(code, code)
        return affiliation, name
    return "", trainer_text
