"""JRA調教後馬体重スクレイパーモジュール

JRA公式サイトから、G1の出走馬の調教後馬体重を取得する。
調教後馬体重はレース週の木曜17時以降にJRAニュースとして発表される。
G1特設ページの調教後馬体重のページにある「調教後馬体重」ボタンのリンク先がそのニュースで、
ニュースの表に出走馬ごとの馬体重が載る。
"""

import datetime
import logging
import re
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup, Tag

from scraping.config import JRA_CHOKYO_BATAIJU_COLUMNS, ScrapingConfig
from scraping.exceptions import (
    ChokyoBataijuUnavailableError,
    NetworkError,
    PageNotFoundError,
    ParseError,
)
from scraping.url_builder import build_jra_g1_weight_url
from scraping.utils import resolve_response_encoding

# ニュースの表の見出し -> 返すDataFrameのカラム名
_HEADER_TO_COLUMN: dict[str, str] = {
    "枠": "枠",
    "馬番": "馬番",
    "馬名": "馬名",
    "馬体重": "馬体重",
    "計量日": "計量日",
    "計量場所": "計量場所",
    "（参考）前走馬体重": "前走馬体重",
}
# 枠順の確定後に発表されたニュースにだけある列
_DRAW_COLUMNS = ("枠", "馬番")
# 前走馬体重の欄で、前走の馬体重が無いことを表す文字列
_NO_PREVIOUS_WEIGHT_TEXTS = frozenset({"", "前走海外"})
# 所属厩舎の見出しは調教師名と所属の2列にまたがる
_STABLE_HEADER = "所属厩舎"
# ニュースのURLの /news/{年}{月}/ から発表年を取る
_NEWS_YEAR_PATTERN = re.compile(r"/news/(\d{4})\d{2}/")
_DATE_PATTERN = re.compile(r"(\d{1,2})月(\d{1,2})日")


class JraChokyoBataijuScraper:
    """JRA調教後馬体重スクレイパークラス

    Attributes:
        g1_page (str): G1特設ページ名（秋華賞なら"shuka"）
        config (ScrapingConfig): スクレイピング設定
        session (requests.Session): HTTPセッション
    """

    def __init__(
        self,
        g1_page: str,
        session: requests.Session | None = None,
        config: ScrapingConfig | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """初期化

        Args:
            g1_page (str): G1特設ページ名（秋華賞なら"shuka"）
            session (requests.Session | None): HTTPセッション。省略時は新規作成
            config (ScrapingConfig | None): 設定オブジェクト
            logger (logging.Logger | None): ロガーインスタンス
        """
        self.g1_page = g1_page
        self._logger = logger or logging.getLogger(__name__)
        self.config = config or ScrapingConfig()
        self.session: requests.Session = session or requests.Session()

    def get_chokyo_bataiju(self) -> pd.DataFrame:
        """出走馬の調教後馬体重を取得する

        Returns:
            pd.DataFrame: JRA_CHOKYO_BATAIJU_COLUMNSのカラムを持つDataFrame

        Raises:
            NetworkError: ページの取得に失敗した場合
            PageNotFoundError: G1特設ページが見つからない場合（特設ページの公開前を含む）
            ChokyoBataijuUnavailableError: 調教後馬体重がまだ発表されていない場合
            ParseError: ページの解析に失敗した場合
        """
        page_url = build_jra_g1_weight_url(self.g1_page, self.config)
        news_url = self._find_news_url(self._fetch_soup(page_url), page_url)
        return self._parse_weight_table(self._fetch_soup(news_url), news_url)

    def save_to_csv(self, df: pd.DataFrame, filepath: str) -> None:
        """DataFrameをCSVファイルに保存する

        Args:
            df (pd.DataFrame): 保存するDataFrame
            filepath (str): 保存先ファイルパス
        """
        df.to_csv(filepath, index=False, encoding="utf-8-sig")
        self._logger.info("CSVファイルを保存しました: %s", filepath)

    def _fetch_soup(self, url: str) -> BeautifulSoup:
        """ページを取得してBeautifulSoupにする

        JRAは存在しないページに403を返すため、403も404と同じく見つからないものとして扱う。

        Args:
            url (str): ページのURL

        Returns:
            BeautifulSoup: ページのBeautifulSoup

        Raises:
            NetworkError: ページの取得に失敗した場合
            PageNotFoundError: ページが見つからない場合
        """
        try:
            response = self.session.get(
                url, headers=self.config.headers, timeout=self.config.request_timeout
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else None
            if status_code in (403, 404):
                self._logger.error("ページが見つかりません: %s", url)
                raise PageNotFoundError(f"ページが見つかりません: {url}") from exc
            self._logger.error("HTTPエラーが発生しました: %s", exc)
            raise NetworkError(f"HTTPエラーが発生しました: {exc}") from exc
        except requests.exceptions.RequestException as exc:
            self._logger.error("ネットワークエラーが発生しました: %s", exc)
            raise NetworkError(f"ネットワークエラーが発生しました: {exc}") from exc

        response.encoding = resolve_response_encoding(response)
        # ニュースの表には閉じていない tr が混じることがあり、html.parser では後続の行が
        # 入れ子になる。lxml は次の tr の開始で前の tr を閉じて読む
        return BeautifulSoup(response.text, "lxml")

    def _find_news_url(self, soup: BeautifulSoup, page_url: str) -> str:
        """「調教後馬体重」ボタンのリンク先のニュースのURLを返す

        Args:
            soup (BeautifulSoup): G1特設ページの調教後馬体重のページのBeautifulSoup
            page_url (str): そのページのURL

        Returns:
            str: ニュースのURL

        Raises:
            ChokyoBataijuUnavailableError: ボタンが無い場合、またはボタンがそのページ自身を指す場合
        """
        link = soup.select_one("#race_local_weight a[href]")
        news_url = urljoin(page_url, str(link["href"])) if link is not None else page_url
        if news_url == page_url:
            self._logger.error("調教後馬体重はまだ発表されていません: %s", page_url)
            raise ChokyoBataijuUnavailableError(f"調教後馬体重はまだ発表されていません: {page_url}")
        return news_url

    def _parse_weight_table(self, soup: BeautifulSoup, news_url: str) -> pd.DataFrame:
        """ニュースの表から出走馬ごとの調教後馬体重を抽出する

        Args:
            soup (BeautifulSoup): ニュースのBeautifulSoup
            news_url (str): ニュースのURL（計量日の年に使う）

        Returns:
            pd.DataFrame: JRA_CHOKYO_BATAIJU_COLUMNSのカラムを持つDataFrame

        Raises:
            ParseError: 表が見つからない場合、表に必要な列が無い場合、または値の解析に失敗した場合
        """
        year_match = _NEWS_YEAR_PATTERN.search(news_url)
        if year_match is None:
            raise ParseError(f"ニュースのURLから発表年を取得できません: {news_url}")
        year = int(year_match.group(1))

        for table in soup.find_all("table"):
            headers = _parse_headers(table)
            if "馬名" in headers and "馬体重" in headers:
                break
        else:
            self._logger.error("調教後馬体重の表が見つかりません: %s", news_url)
            raise ParseError(f"調教後馬体重の表が見つかりません: {news_url}")
        missing = [
            column
            for column in JRA_CHOKYO_BATAIJU_COLUMNS
            if column not in headers and column not in _DRAW_COLUMNS
        ]
        if missing:
            self._logger.error("調教後馬体重の表に無い列があります: %s", missing)
            raise ParseError(f"調教後馬体重の表に無い列があります: {missing}")

        rows: list[dict[str, object]] = []
        for tr in table.find_all("tr"):
            # 枠順の確定後は、枠のセルが行見出し（th）になる
            if not tr.find_all("td"):
                continue
            cells = [cell.get_text(strip=True) for cell in tr.find_all(["th", "td"])]
            if len(cells) != len(headers):
                raise ParseError(f"列数が見出しと一致しません: {cells}")
            values = dict(zip(headers, cells, strict=True))
            rows.append(
                {
                    "枠": int(values["枠"]) if "枠" in values else None,
                    "馬番": int(values["馬番"]) if "馬番" in values else None,
                    "馬名": values["馬名"],
                    "馬体重": _parse_weight(values["馬体重"]),
                    "計量日": _parse_date(values["計量日"], year),
                    "計量場所": values["計量場所"],
                    "調教師": values["調教師"],
                    "所属": values["所属"],
                    "前走馬体重": (
                        None
                        if values["前走馬体重"] in _NO_PREVIOUS_WEIGHT_TEXTS
                        else _parse_weight(values["前走馬体重"])
                    ),
                }
            )
        if not rows:
            raise ParseError(f"調教後馬体重の表に馬がいません: {news_url}")
        df = pd.DataFrame(rows, columns=JRA_CHOKYO_BATAIJU_COLUMNS)
        for column in ("枠", "馬番", "前走馬体重"):
            df[column] = df[column].astype("Int64")
        return df


def _parse_headers(table: Tag) -> list[str]:
    """表の見出しを、返すDataFrameのカラム名にして列の順に返す

    見出しは、データのセル（td）を持たない最初の行から取る。
    所属厩舎の見出しは、またがる2列を調教師・所属に分ける。

    Args:
        table (Tag): table要素

    Returns:
        list[str]: 列ごとのカラム名。対応しない見出しはそのままの文字列。見出しの行が無ければ空
    """
    header_row = next((tr for tr in table.find_all("tr") if not tr.find_all("td")), None)
    if header_row is None:
        return []
    headers: list[str] = []
    for th in header_row.find_all("th"):
        text = th.get_text(strip=True)
        if text == _STABLE_HEADER:
            headers.extend(["調教師", "所属"])
            continue
        headers.extend([_HEADER_TO_COLUMN.get(text, text)] * int(str(th.get("colspan", 1))))
    return headers


def _parse_weight(text: str) -> int:
    """馬体重の文字列を数値にする

    Args:
        text (str): 馬体重（"528" など）

    Returns:
        int: 馬体重（kg）

    Raises:
        ParseError: 数値でない場合
    """
    if not text.isdecimal():
        raise ParseError(f"馬体重のパースに失敗しました: {text}")
    return int(text)


def _parse_date(text: str, year: int) -> datetime.date:
    """計量日の文字列を日付にする

    Args:
        text (str): 計量日（"10月15日（木曜）" など）
        year (int): 発表年

    Returns:
        datetime.date: 計量日

    Raises:
        ParseError: 日付のパースに失敗した場合
    """
    match = _DATE_PATTERN.search(text)
    if match is None:
        raise ParseError(f"計量日のパースに失敗しました: {text}")
    try:
        return datetime.date(year, int(match.group(1)), int(match.group(2)))
    except ValueError as exc:
        raise ParseError(f"計量日のパースに失敗しました: {text}") from exc
