"""馬情報スクレイピングモジュール

netkeibaの競走馬一覧ページから馬情報をスクレイピングする。
"""

import logging
import re
import time

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup, Tag

from scraping.config import AFFILIATION_MAP, HORSE_INFO_COLUMNS, ScrapingConfig
from scraping.exceptions import NetworkError, PageNotFoundError, ParseError
from scraping.url_builder import build_horse_list_url
from scraping.utils import resolve_response_encoding


class HorseInfoScraper:
    """馬情報スクレイパークラス

    Attributes:
        year (int): 馬の誕生年
        max_page_num (int): 競走馬一覧ページの最大ページ数
        session (Session): HTTPセッション
        config (ScrapingConfig): スクレイピング設定
    """

    def __init__(
        self,
        year: int,
        session: requests.Session | None = None,
        config: ScrapingConfig | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """初期化

        ``_scrape_max_page_num`` を実行し、最大ページ数を ``max_page_num`` に保持する。

        Args:
            year (int): 馬の誕生年
            session (requests.Session | None): HTTPセッション。省略時は新規作成
            config (ScrapingConfig | None): 設定オブジェクト
            logger (logging.Logger | None): ロガーインスタンス
        """
        self.year = year
        self._logger = logger or logging.getLogger(__name__)
        self.config = config or ScrapingConfig()
        self._owns_session = session is None
        self.session: requests.Session = session or requests.Session()

        self.max_page_num = self._scrape_max_page_num()

    def get_all_horse_info(self, sleep: float = 1.0) -> pd.DataFrame:
        """競走馬一覧ページから全ページ分の馬情報をスクレイピングする

        Args:
            sleep (float): 連続リクエスト間のスリープ秒数。デフォルト1.0秒

        Returns:
            pd.DataFrame: HORSE_INFO_COLUMNSのカラムを持つDataFrame
        """
        frames: list[pd.DataFrame] = []
        for page_num in range(1, self.max_page_num + 1):
            if page_num > 1:
                time.sleep(sleep)
            page_df = self.scrape_one_page(page_num)
            frames.append(page_df)
        if frames:
            return pd.concat(frames, ignore_index=True)
        return pd.DataFrame(columns=HORSE_INFO_COLUMNS)

    def scrape_one_page(self, page_num: int) -> pd.DataFrame:
        """1ページ分の馬情報をスクレイピングする

        Args:
            page_num (int): ページ番号

        Returns:
            pd.DataFrame: 1ページ分の馬情報（HORSE_INFO_COLUMNSのカラム）

        Raises:
            NetworkError: ページの取得に失敗した場合
            PageNotFoundError: ページが見つからない場合
            ParseError: テーブルの解析に失敗した場合
        """
        url = build_horse_list_url(self.year, page_num, self.config)

        # HTML取得
        try:
            html = self.session.get(
                url, headers=self.config.headers, timeout=self.config.request_timeout
            )
            html.raise_for_status()
        except requests.exceptions.HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else None
            if status_code == 404:
                self._logger.error("馬情報ページが見つかりません: %s", url)
                raise PageNotFoundError(f"馬情報ページが見つかりません: {url}") from exc
            self._logger.error("HTTPエラーが発生しました: %s", exc)
            raise NetworkError(f"HTTPエラーが発生しました: {exc}") from exc
        except requests.exceptions.RequestException as exc:
            self._logger.error("ネットワークエラーが発生しました: %s", exc)
            raise NetworkError(f"ネットワークエラーが発生しました: {exc}") from exc
        html.encoding = resolve_response_encoding(html)
        soup = BeautifulSoup(html.text, "html.parser")

        # テーブル要素を取得
        horse_list_table = soup.select_one("table.nk_tb_common.race_table_01")
        if horse_list_table is None:
            self._logger.error("テーブルが見つかりません: %s", url)
            raise ParseError(f"テーブルが見つかりません: {url}")

        rows: list[dict[str, object]] = []
        trs = horse_list_table.find_all("tr")
        for i in range(1, len(trs)):  # 最初の行はヘッダーのためスキップ
            tds = trs[i].find_all("td")
            if len(tds) < 12:
                self._logger.error(
                    "テーブル列数が不足しています: %s (row=%d, columns=%d)", url, i, len(tds)
                )
                raise ParseError(
                    f"テーブル列数が不足しています: {url} (row={i}, columns={len(tds)})"
                )
            rows.append(self._parse_row(tds))

        return pd.DataFrame(rows, columns=HORSE_INFO_COLUMNS)

    def _parse_row(self, tds: list[Tag]) -> dict[str, object]:
        """1行分のtd要素から馬情報を抽出する

        Args:
            tds (list[Tag]): td要素のリスト

        Returns:
            dict[str, object]: HORSE_INFO_COLUMNSのキーを持つ辞書

        Raises:
            ParseError: 馬IDまたは総賞金のパースに失敗した場合
        """
        # 馬ID (tds[1]: 馬名カラムのリンクから)
        horse_id = _extract_id_from_td(tds[1])
        if not isinstance(horse_id, str):
            self._logger.error("馬IDのリンクが見つかりません: %s", tds[1].text.strip())
            raise ParseError(f"馬IDのリンクが見つかりません: {tds[1].text.strip()}")

        # 所属・厩舎 (tds[5]: "[西] 高柳大輔" → 所属="栗東", 厩舎="高柳大輔")
        affiliation, trainer_name = _parse_trainer(tds[5])

        # 総賞金 (tds[11]: "4226.9" のような万円単位の数値)
        prize_text = tds[11].text.strip().replace(",", "")
        try:
            prize = int(float(prize_text))
        except ValueError as exc:
            self._logger.error("総賞金のパースに失敗しました: %s", prize_text)
            raise ParseError(f"総賞金のパースに失敗しました: {prize_text}") from exc

        return {
            "馬ID": horse_id,
            "馬名": _extract_link_text(tds[1]),
            "性別": tds[2].text.strip(),
            "生年": self.year,
            "所属": affiliation,
            "厩舎": trainer_name,
            "厩舎ID": _extract_id_from_td(tds[5]),
            "父": _extract_link_text(tds[6]),
            "母": _extract_link_text(tds[7]),
            "母父": _extract_link_text(tds[8]),
            "馬主": _extract_link_text(tds[9]),
            "馬主ID": _extract_id_from_td(tds[9]),
            "生産者": _extract_link_text(tds[10]),
            "生産者ID": _extract_id_from_td(tds[10]),
            "総賞金(万円)": prize,
        }

    def _scrape_max_page_num(self) -> int:
        """競走馬一覧ページの最大ページ数を取得する

        Returns:
            int: 最大ページ数

        Raises:
            NetworkError: ページの取得に失敗した場合
            PageNotFoundError: ページが見つからない場合
            ParseError: 最大ページ数の取得に失敗した場合
        """
        url = build_horse_list_url(self.year, 1, self.config)
        try:
            html = self.session.get(
                url, headers=self.config.headers, timeout=self.config.request_timeout
            )
            html.raise_for_status()
        except requests.exceptions.HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else None
            if status_code == 404:
                self._logger.error("馬情報ページが見つかりません: %s", url)
                raise PageNotFoundError(f"馬情報ページが見つかりません: {url}") from exc
            self._logger.error("HTTPエラーが発生しました: %s", exc)
            raise NetworkError(f"HTTPエラーが発生しました: {exc}") from exc
        except requests.exceptions.RequestException as exc:
            self._logger.error("ネットワークエラーが発生しました: %s", exc)
            raise NetworkError(f"ネットワークエラーが発生しました: {exc}") from exc
        html.encoding = resolve_response_encoding(html)
        soup = BeautifulSoup(html.text, "html.parser")
        pager = soup.find("div", class_="pager")
        if pager is None:
            self._logger.error("ページャーが見つかりません")
            raise ParseError("ページャーが見つかりません")

        # 正規表現でカンマ付きの数値を探す
        match = re.search(r"\d{1,3}(?:,\d{3})?", pager.text)
        if match:
            birth_num = int(match.group().replace(",", ""))
        else:
            self._logger.error("データベースページの最大ページ数の取得に失敗しました")
            raise ParseError("データベースページの最大ページ数の取得に失敗しました")

        # 100頭ごとに1ページなので切り上げでページ数を算出
        return (birth_num + 99) // 100


def _extract_id_from_td(td_element: Tag) -> str | float:
    """tdタグ内のaタグのhrefからIDを抽出する

    馬名のリンク（例: /horse/2022105081/）はパスから、
    厩舎・馬主・生産者のリンク（例: /trainer/race.html?id=01159）はidクエリからIDを取り出す。

    Args:
        td_element (Tag): td要素

    Returns:
        str | float: IDの文字列。リンクがない場合はNaN
    """
    a_tag = td_element.find("a")
    if not isinstance(a_tag, Tag):
        return np.nan
    href = str(a_tag.get("href", ""))
    id_match = re.search(r"(?:/horse/|[?&]id=)([^/&]+)", href)
    if id_match is None:
        return np.nan
    return id_match.group(1)


def _extract_link_text(td_element: Tag) -> str | float:
    """tdタグ内の最初のaタグの文字列を抽出する

    Args:
        td_element (Tag): td要素

    Returns:
        str | float: リンクの文字列。リンクがない場合はNaN
    """
    a_tag = td_element.find("a")
    if not isinstance(a_tag, Tag):
        return np.nan
    return a_tag.get_text(strip=True)


def _parse_trainer(td_element: Tag) -> tuple[str | float, str | float]:
    """厩舎のtdタグから所属と調教師名を分離する

    Args:
        td_element (Tag): 厩舎のtd要素（"[西] 高柳大輔" 形式のテキストを持つ）

    Returns:
        str | float: 所属（"美浦","栗東","地方","海外"のいずれか）。厩舎未所属の場合はNaN
        str | float: 調教師名。厩舎未所属の場合はNaN
    """
    text = " ".join(td_element.stripped_strings)
    match = re.fullmatch(r"\[(.+?)\]\s*(.+)", text)
    if match is None:
        return np.nan, np.nan
    code = match.group(1)
    return AFFILIATION_MAP.get(code, code), match.group(2)
