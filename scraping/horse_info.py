"""馬情報スクレイピングモジュール

netkeibaの競走馬一覧ページから馬情報をスクレイピングする。
KeibaAIの``scrape_horse_info_page``に対応する。
"""

import logging
import re
import time
from io import StringIO

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup, Tag

from scraping.config import AFFILIATION_MAP, HORSE_INFO_COLUMNS, ScrapingConfig
from scraping.exceptions import NetworkError, PageNotFoundError, ParseError
from scraping.url_builder import build_horse_list_url


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
            if html.status_code == 404:
                self._logger.error("馬情報ページが見つかりません: %s", url)
                raise PageNotFoundError(f"馬情報ページが見つかりません: {url}") from exc
            self._logger.error("HTTPエラーが発生しました: %s", exc)
            raise NetworkError(f"HTTPエラーが発生しました: {exc}") from exc
        except requests.exceptions.RequestException as exc:
            self._logger.error("ネットワークエラーが発生しました: %s", exc)
            raise NetworkError(f"ネットワークエラーが発生しました: {exc}") from exc
        html.encoding = "EUC-JP"
        soup = BeautifulSoup(html.text, "html.parser")

        # テーブル要素を取得
        race_table_01 = soup.find("table", class_="nk_tb_common race_table_01")
        if not isinstance(race_table_01, Tag):
            self._logger.error("テーブルが見つかりません: %s", url)
            raise ParseError(f"テーブルが見つかりません: {url}")

        # 各種IDを行ごとに抽出
        horse_id_list: list[str | float] = []
        trainer_id_list: list[str | float] = []
        owner_id_list: list[str | float] = []
        breeder_id_list: list[str | float] = []

        trs = race_table_01.find_all("tr")
        for i in range(1, len(trs)):  # 最初の行はヘッダーのためスキップ
            tds = trs[i].find_all("td")
            if len(tds) <= 10:
                self._logger.error(
                    "テーブル列数が不足しています: %s (row=%d, columns=%d)", url, i, len(tds)
                )
                raise ParseError(
                    f"テーブル列数が不足しています: {url} (row={i}, columns={len(tds)})"
                )

            # 馬ID (tds[1]: 馬名カラム)
            horse_id = _extract_id_from_td(tds[1])
            horse_id_list.append(horse_id)
            # 厩舎ID (tds[5]: 厩舎カラム)
            trainer_id_list.append(_extract_id_from_td(tds[5]))
            # 馬主ID (tds[9]: 馬主カラム)
            owner_id_list.append(_extract_id_from_td(tds[9]))
            # 生産者ID (tds[10]: 生産者カラム)
            breeder_id_list.append(_extract_id_from_td(tds[10]))

        # pd.read_htmlでテーブルの基本カラムを取得
        read_html_columns = [
            "馬名",
            "性",
            "厩舎",
            "父",
            "母",
            "母父",
            "馬主",
            "生産者",
            "総賞金(万円)",
        ]
        try:
            tables = pd.read_html(StringIO(html.text))
            horse_info_df = tables[0][read_html_columns].copy()
        except Exception as exc:
            self._logger.error("テーブルの読み込みに失敗しました: %s", url, exc_info=True)
            raise ParseError(f"テーブルの読み込みに失敗しました: {url}") from exc

        # カラム名を変換
        horse_info_df = horse_info_df.rename(columns={"性": "性別"})

        # カラムを追加・整形
        horse_info_df.insert(0, "馬ID", horse_id_list)
        horse_info_df.insert(2, "生年", self.year)
        horse_info_df.insert(3, "所属", "")
        horse_info_df["厩舎ID"] = trainer_id_list
        horse_info_df["馬主ID"] = owner_id_list
        horse_info_df["生産者ID"] = breeder_id_list

        # 所属と厩舎を分割（"[西]友道康夫" → 所属="栗東", 厩舎="友道康夫"）
        try:
            horse_info_df[["所属", "厩舎"]] = horse_info_df["厩舎"].str.extract(r"\[(.*?)\](.*)")
        except Exception:
            # 厩舎列のすべての行がNaNだった場合何もしない
            pass

        # 所属の値を変換（"東"→"美浦"、"西"→"栗東"、"地"→"地方"、"外"→"海外"）
        horse_info_df["所属"] = horse_info_df["所属"].map(
            lambda x: AFFILIATION_MAP.get(str(x), x) if pd.notna(x) else x
        )

        # 総賞金を万円単位のintに変換（NaNは0）
        horse_info_df["総賞金(万円)"] = (
            pd.to_numeric(
                horse_info_df["総賞金(万円)"].astype(str).str.replace(",", ""),
                errors="coerce",
            )
            .fillna(0)
            .astype(int)
        )

        # HORSE_INFO_COLUMNSの順序でカラムを並び替え
        horse_info_df = horse_info_df[HORSE_INFO_COLUMNS]

        return horse_info_df

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
            if html.status_code == 404:
                self._logger.error("馬情報ページが見つかりません: %s", url)
                raise PageNotFoundError(f"馬情報ページが見つかりません: {url}") from exc
            self._logger.error("HTTPエラーが発生しました: %s", exc)
            raise NetworkError(f"HTTPエラーが発生しました: {exc}") from exc
        except requests.exceptions.RequestException as exc:
            self._logger.error("ネットワークエラーが発生しました: %s", exc)
            raise NetworkError(f"ネットワークエラーが発生しました: {exc}") from exc
        html.encoding = "EUC-JP"
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
    """tdタグからaタグのhrefを解析してIDを抽出する

    Args:
        td_element: BeautifulSoupのtd要素

    Returns:
        str | float: IDの文字列。リンクがない場合はNaN
    """
    try:
        a_tag = td_element.find("a")
        if not isinstance(a_tag, Tag):
            return np.nan
        href = str(a_tag["href"])
        # URLの末尾からIDを抽出（末尾の/を除く）
        # 例: /horse/2022105081/ → 2022105081
        id_match = re.search(r"/(\d+)/?$", href)
        if id_match:
            return id_match.group(1)
        return np.nan
    except Exception:
        return np.nan
