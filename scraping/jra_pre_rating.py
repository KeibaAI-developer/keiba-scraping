"""JRAプレレーティングスクレイパーモジュール

JRA公式サイトから、G1の登録馬のプレレーティングを取得する。
"""

import logging
import re
import unicodedata
from dataclasses import dataclass

import pandas as pd
import requests
from bs4 import BeautifulSoup, Tag

from scraping.config import JRA_PRE_RATING_COLUMNS, ScrapingConfig
from scraping.exceptions import NetworkError, PageNotFoundError, ParseError
from scraping.url_builder import build_jra_pre_rating_url
from scraping.utils import resolve_response_encoding

# 表の先頭の4列の見出し（空白を除いたもの）
_LEADING_HEADERS = ("馬名", "性", "年齢", "調教師")
# 前年のJPNランキングの列の見出しに含まれる文字列
_PREVIOUS_HEADER_MARK = "JPN"
# 最後の列の見出しに含まれる文字列。外国馬の表は該当レースの代わりに調教国が載る
_RACE_HEADER_MARK = "該当レース"
_COUNTRY_HEADER_MARK = "調教国"
# レーティングの値が無いことを表すセルの文字列
_NO_VALUE_TEXTS = frozenset({"", "-", "ー", "―"})
# 「111 E」や「113」のように、数値と距離区分が1つのセルに入る値
_RATING_PATTERN = re.compile(r"^(\d+)\s*(.*)$")
# 馬名の後ろに付く産地の略号や欧字の馬名の始まり
_NAME_SUFFIX_PATTERN = re.compile(r"[（(\s]")


@dataclass(frozen=True)
class _Rating:
    """レーティングの値1つ。

    Attributes:
        value (int | None): レーティングの数値。値が無い場合は None。
        category (str | None): 距離区分。値が無い場合と、距離区分が付かない場合は None。
    """

    value: int | None
    category: str | None


@dataclass(frozen=True)
class _Layout:
    """プレレーティングの表の列の並び。

    Attributes:
        has_previous (bool): 前年のJPNランキングの列があるか。
        is_race (bool): 最後の列が該当レースか（False は調教国）。
        split_cells (bool): 数値と距離区分が別のセルに分かれる形か。
    """

    has_previous: bool
    is_race: bool
    split_cells: bool


class JraPreRatingScraper:
    """JRAプレレーティングスクレイパークラス

    Attributes:
        year (int): 開催年
        g1_page (str): プレレーティングのページ名（エリザベス女王杯なら"eliza"）
        config (ScrapingConfig): スクレイピング設定
        session (requests.Session): HTTPセッション
    """

    def __init__(
        self,
        year: int,
        g1_page: str,
        session: requests.Session | None = None,
        config: ScrapingConfig | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """初期化

        Args:
            year (int): 開催年
            g1_page (str): プレレーティングのページ名（エリザベス女王杯なら"eliza"）
            session (requests.Session | None): HTTPセッション。省略時は新規作成
            config (ScrapingConfig | None): 設定オブジェクト
            logger (logging.Logger | None): ロガーインスタンス
        """
        self.year = year
        self.g1_page = g1_page
        self._logger = logger or logging.getLogger(__name__)
        self.config = config or ScrapingConfig()
        self.session: requests.Session = session or requests.Session()

    def get_pre_rating(self) -> pd.DataFrame:
        """登録馬のプレレーティングを取得する

        Returns:
            pd.DataFrame: JRA_PRE_RATING_COLUMNSのカラムを持つDataFrame

        Raises:
            NetworkError: ページの取得に失敗した場合
            PageNotFoundError: ページが見つからない場合（プレレーティングの公開前を含む）
            ParseError: ページの解析に失敗した場合
        """
        url = build_jra_pre_rating_url(self.year, self.g1_page, self.config)
        return _parse_page(self._fetch_soup(url), url)

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
                self._logger.error("プレレーティングのページが見つかりません: %s", url)
                raise PageNotFoundError(f"プレレーティングのページが見つかりません: {url}") from exc
            self._logger.error("HTTPエラーが発生しました: %s", exc)
            raise NetworkError(f"HTTPエラーが発生しました: {exc}") from exc
        except requests.exceptions.RequestException as exc:
            self._logger.error("ネットワークエラーが発生しました: %s", exc)
            raise NetworkError(f"ネットワークエラーが発生しました: {exc}") from exc

        response.encoding = resolve_response_encoding(response)
        # 古い年のページは表が入れ子で、閉じていないタグも混じるため lxml で読む
        return BeautifulSoup(response.text, "lxml")


def _parse_page(soup: BeautifulSoup, url: str) -> pd.DataFrame:
    """ページ内のプレレーティングの表をすべて読み、表の順につなぐ

    Args:
        soup (BeautifulSoup): ページのBeautifulSoup
        url (str): ページのURL（エラーメッセージに使う）

    Returns:
        pd.DataFrame: JRA_PRE_RATING_COLUMNSのカラムを持つDataFrame

    Raises:
        ParseError: 表が無い場合、表に馬がいない場合、または値の解析に失敗した場合
    """
    rows: list[dict[str, object]] = []
    found = False
    # 古い年のページは表が入れ子になり、外側の表も同じ行を含むため、最も内側の表だけを読む
    for table in soup.find_all("table"):
        if table.find("table") is not None:
            continue
        trs = table.find_all("tr")
        if not trs or _header_texts(trs[0])[:1] != [_LEADING_HEADERS[0]]:
            continue
        found = True
        layout = _parse_layout(trs[0], url)
        for tr in trs[1:]:
            cells = tr.find_all(["th", "td"])
            if all(not cell.get_text(strip=True) for cell in cells):
                continue
            rows.append(_parse_row(cells, layout))
    if not found:
        raise ParseError(f"プレレーティングの表が見つかりません: {url}")
    if not rows:
        raise ParseError(f"プレレーティングの表に馬がいません: {url}")
    df = pd.DataFrame(rows, columns=JRA_PRE_RATING_COLUMNS)
    for column in ("レーティング", "前年レーティング"):
        df[column] = df[column].astype("Int64")
    return df


def _header_texts(tr: Tag) -> list[str]:
    """見出しの行のセルの文字列を、空白を除いて返す"""
    return [re.sub(r"\s", "", _normalize(cell.get_text())) for cell in tr.find_all(["th", "td"])]


def _parse_layout(header: Tag, url: str) -> _Layout:
    """見出しの行から、表の列の並びを判定する

    Raises:
        ParseError: 見出しが想定と異なる場合
    """
    texts = _header_texts(header)
    if tuple(texts[: len(_LEADING_HEADERS)]) != _LEADING_HEADERS:
        raise ParseError(f"プレレーティングの表の見出しが想定と異なります: {texts} ({url})")
    rating_headers = texts[len(_LEADING_HEADERS) : -1]
    last = texts[-1]
    is_race = _RACE_HEADER_MARK in last
    if not (is_race or _COUNTRY_HEADER_MARK in last):
        raise ParseError(f"プレレーティングの表の最後の列が想定と異なります: {last!r} ({url})")
    has_previous = any(_PREVIOUS_HEADER_MARK in text for text in rating_headers)
    if len(rating_headers) != (2 if has_previous else 1):
        raise ParseError(f"プレレーティングの表の列が想定と異なります: {texts} ({url})")
    if has_previous and _PREVIOUS_HEADER_MARK not in rating_headers[0]:
        raise ParseError(f"前年のJPNランキングの列の位置が想定と異なります: {texts} ({url})")
    # 数値と距離区分が別のセルに分かれる形は、レーティングの見出しが2列分の幅を持つ
    rating_cell = header.find_all(["th", "td"])[len(_LEADING_HEADERS)]
    split_cells = str(rating_cell.get("colspan", "1")) == "2"
    return _Layout(has_previous=has_previous, is_race=is_race, split_cells=split_cells)


def _parse_row(cells: list[Tag], layout: _Layout) -> dict[str, object]:
    """馬1頭の行を読む

    Raises:
        ParseError: 列数が見出しと合わない場合、または値を読めない場合
    """
    texts = [_normalize(cell.get_text(" ", strip=True)) for cell in cells]
    if len(texts) < len(_LEADING_HEADERS) + 2:
        raise ParseError(f"プレレーティングの表の列が足りません: {texts}")
    position = len(_LEADING_HEADERS)
    ratings: list[_Rating] = []
    for _ in range(2 if layout.has_previous else 1):
        rating, used = _read_rating(cells[position:], layout.split_cells)
        ratings.append(rating)
        position += used
    if position != len(cells) - 1:
        raise ParseError(f"プレレーティングの表の列数が見出しと一致しません: {texts}")
    previous = ratings[0] if layout.has_previous else _Rating(None, None)
    current = ratings[-1]
    last = texts[-1]
    return {
        "馬名": _parse_name(cells[0].get_text(" ", strip=True)),
        "性": texts[1],
        "年齢": _parse_int(texts[2]),
        "調教師": cells[3].get_text(strip=True),
        "レーティング": current.value,
        "距離区分": current.category,
        "前年レーティング": previous.value,
        "前年距離区分": previous.category,
        "該当レース": cells[-1].get_text(strip=True) if layout.is_race and last else None,
    }


def _read_rating(cells: list[Tag], split_cells: bool) -> tuple[_Rating, int]:
    """行の先頭のセルからレーティングの値を1つ読み、読んだセルの数とともに返す

    Raises:
        ParseError: 値を読めない場合
    """
    if not cells:
        raise ParseError("レーティングのセルが足りません")
    first = cells[0]
    text = _normalize(first.get_text(" ", strip=True))
    if not split_cells:
        return _parse_rating(text), 1
    # 数値と距離区分が別のセルに分かれる形でも、値が無い馬は2列分の幅の1セルになる
    if str(first.get("colspan", "1")) == "2":
        if text not in _NO_VALUE_TEXTS:
            raise ParseError(f"値が無い馬のレーティングのセルに文字があります: {text!r}")
        return _Rating(None, None), 1
    if len(cells) < 2:
        raise ParseError(f"距離区分のセルがありません: {text!r}")
    category = _normalize(cells[1].get_text(strip=True))
    if text in _NO_VALUE_TEXTS:
        return _Rating(None, None), 2
    return _Rating(_parse_int(text), category or None), 2


def _parse_rating(text: str) -> _Rating:
    """「111 E」「113」の形のセルを読む

    Raises:
        ParseError: 数値を読めない場合
    """
    if text in _NO_VALUE_TEXTS:
        return _Rating(None, None)
    match = _RATING_PATTERN.match(text)
    if match is None:
        raise ParseError(f"レーティングの値を読めません: {text!r}")
    category = match.group(2).strip()
    return _Rating(int(match.group(1)), category or None)


def _parse_name(text: str) -> str:
    """馬名のセルから、産地の略号と欧字の馬名を除いた馬名を返す

    Raises:
        ParseError: 馬名が空の場合
    """
    name = _NAME_SUFFIX_PATTERN.split(text.strip(), maxsplit=1)[0]
    if not name:
        raise ParseError(f"馬名を読めません: {text!r}")
    return name


def _parse_int(text: str) -> int:
    """全角を含む数字の文字列を整数にする

    Raises:
        ParseError: 整数として読めない場合
    """
    normalized = _normalize(text)
    if not normalized.isdigit():
        raise ParseError(f"数値を読めません: {text!r}")
    return int(normalized)


def _normalize(text: str) -> str:
    """全角の英数字・記号を半角にし、前後の空白を除く

    NFKC で半角にならないマイナス記号（U+2212）も、半角のハイフンにする。
    """
    return unicodedata.normalize("NFKC", text).replace("\u2212", "-").strip()
