"""JRA重賞レース一覧スクレイパーモジュール

JRA公式サイトから年間の重賞レース一覧を取得する。
"""

import datetime
import logging
import re

import pandas as pd
import requests
from bs4 import BeautifulSoup, Tag

from scraping.config import JRA_GRADED_RACE_COLUMNS, ScrapingConfig
from scraping.exceptions import NetworkError, PageNotFoundError, ParseError
from scraping.utils import build_jra_graded_race_url, judge_turf_dirt


class JraGradedRaceScraper:
    """JRA重賞レース一覧スクレイパークラス

    Attributes:
        year (int): 検索対象の年
        config (ScrapingConfig): スクレイピング設定
        session (requests.Session): HTTPセッション
    """

    def __init__(
        self,
        year: int,
        session: requests.Session | None = None,
        config: ScrapingConfig | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """初期化

        Args:
            year (int): 検索対象の年
            session (requests.Session | None): HTTPセッション。省略時は新規作成
            config (ScrapingConfig | None): 設定オブジェクト
            logger (logging.Logger | None): ロガーインスタンス
        """
        self.year = year
        self._logger = logger or logging.getLogger(__name__)
        self.config = config or ScrapingConfig()
        self.session: requests.Session = session or requests.Session()

    def get_graded_races(self) -> pd.DataFrame:
        """重賞レース一覧を取得する

        Returns:
            pd.DataFrame: JRA_GRADED_RACE_COLUMNSのカラムを持つDataFrame

        Raises:
            NetworkError: ページの取得に失敗した場合
            PageNotFoundError: ページが見つからない場合
            ParseError: テーブルの解析に失敗した場合
        """
        url = build_jra_graded_race_url(self.year, self.config)

        try:
            response = self.session.get(
                url, headers=self.config.headers, timeout=self.config.request_timeout
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else None
            if status_code == 404:
                self._logger.error("JRA重賞レース一覧ページが見つかりません: %s", url)
                raise PageNotFoundError(f"JRA重賞レース一覧ページが見つかりません: {url}") from exc
            self._logger.error("HTTPエラーが発生しました: %s", exc)
            raise NetworkError(f"HTTPエラーが発生しました: {exc}") from exc
        except requests.exceptions.RequestException as exc:
            self._logger.error("ネットワークエラーが発生しました: %s", exc)
            raise NetworkError(f"ネットワークエラーが発生しました: {exc}") from exc

        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, "html.parser")

        return self._parse_graded_race_table(soup)

    def save_to_csv(self, df: pd.DataFrame, filepath: str) -> None:
        """DataFrameをCSVファイルに保存する

        Args:
            df (pd.DataFrame): 保存するDataFrame
            filepath (str): 保存先ファイルパス
        """
        df.to_csv(filepath, index=False, encoding="utf-8-sig")
        self._logger.info("CSVファイルを保存しました: %s", filepath)

    def _parse_graded_race_table(self, soup: BeautifulSoup) -> pd.DataFrame:
        """BeautifulSoupオブジェクトから重賞レース一覧を抽出する

        Args:
            soup (BeautifulSoup): JRA重賞レース一覧ページのBeautifulSoup

        Returns:
            pd.DataFrame: JRA_GRADED_RACE_COLUMNSのカラムを持つDataFrame

        Raises:
            ParseError: テーブルの解析に失敗した場合
        """
        table = soup.find("table")
        if not isinstance(table, Tag):
            self._logger.error("重賞レース一覧テーブルが見つかりません")
            raise ParseError("重賞レース一覧テーブルが見つかりません")

        trs = table.find_all("tr")
        if len(trs) <= 1:
            return pd.DataFrame(columns=JRA_GRADED_RACE_COLUMNS)

        rows: list[dict[str, object]] = []
        for i in range(1, len(trs)):
            tds = trs[i].find_all("td")
            if len(tds) < 7:
                self._logger.warning("列数が不足しています (row=%d, columns=%d)", i, len(tds))
                continue
            parsed_rows = self._parse_row(tds)
            rows.extend(parsed_rows)

        if not rows:
            return pd.DataFrame(columns=JRA_GRADED_RACE_COLUMNS)

        return pd.DataFrame(rows, columns=JRA_GRADED_RACE_COLUMNS)

    def _parse_row(self, tds: list[Tag]) -> list[dict[str, object]]:
        """1行分のtd要素からレース情報を抽出する

        同着の場合は複数行を返す。

        Args:
            tds (list[Tag]): td要素のリスト

        Returns:
            list[dict[str, object]]: JRA_GRADED_RACE_COLUMNSのキーを持つ辞書のリスト
        """
        # 日付 (td[0]: "1月5日日曜" → datetime.date)
        date_obj = self._parse_date(tds[0])

        # グレード・レース名 (td[1])
        grade, race_name = self._parse_grade_and_race_name(tds[1])

        # 競馬場 (td[2])
        place = tds[2].text.strip()

        # 性齢 (td[3])
        age = tds[3].text.strip()

        # コース (td[4]: "芝2,000メートル" → 芝ダ, 距離)
        turf_dirt, distance = self._parse_course(tds[4])

        # 優勝馬・騎手 (td[5], td[6]) - 同着の場合は複数
        winners = self._parse_multi_value(tds[5])
        jockeys = self._parse_multi_value(tds[6])

        results: list[dict[str, object]] = []
        for idx in range(len(winners)):
            jockey = jockeys[idx] if idx < len(jockeys) else ""
            results.append(
                {
                    "日付": date_obj,
                    "グレード": grade,
                    "レース名": race_name,
                    "競馬場": place,
                    "性齢": age,
                    "芝ダ": turf_dirt,
                    "距離": distance,
                    "優勝馬": winners[idx],
                    "騎手": jockey,
                }
            )
        return results

    def _parse_date(self, td: Tag) -> datetime.date:
        """日付セルからdatetime.dateを抽出する

        Args:
            td (Tag): 日付のtd要素（"1月5日日曜", "1月13日祝日・月曜" など）

        Returns:
            datetime.date: 日付

        Raises:
            ParseError: 日付のパースに失敗した場合
        """
        # テキストノードのみ取得（spanタグ内の曜日は無視）
        date_parts: list[str] = []
        for child in td.children:
            if isinstance(child, str):
                date_parts.append(child.strip())

        date_text = "".join(date_parts)
        match = re.search(r"(\d{1,2})月(\d{1,2})日", date_text)
        if match is None:
            self._logger.error("日付のパースに失敗しました: %s", td.text.strip())
            raise ParseError(f"日付のパースに失敗しました: {td.text.strip()}")

        month = int(match.group(1))
        day = int(match.group(2))
        return datetime.date(self.year, month, day)

    def _parse_grade_and_race_name(self, td: Tag) -> tuple[str, str]:
        """レース名セルからグレードとレース名を抽出する

        Args:
            td (Tag): レース名のtd要素

        Returns:
            tuple[str, str]: (グレード, レース名)
        """
        span = td.find("span", class_="grade_icon")
        if isinstance(span, Tag):
            grade = span.text.strip()
            # spanの後のテキストがレース名
            race_name_parts: list[str] = []
            for sibling in span.next_siblings:
                if isinstance(sibling, str):
                    race_name_parts.append(sibling.strip())
                elif isinstance(sibling, Tag) and sibling.name == "a":
                    race_name_parts.append(sibling.text.strip())
            race_name = "".join(race_name_parts)
        else:
            grade = ""
            race_name = td.text.strip()

        return grade, race_name

    def _parse_course(self, td: Tag) -> tuple[str, int]:
        """コースセルから芝ダートと距離を抽出する

        Args:
            td (Tag): コースのtd要素（"芝2,000メートル", "ダ1,800メートル" など）

        Returns:
            tuple[str, int]: (芝ダ, 距離)

        Raises:
            ParseError: 距離のパースに失敗した場合
        """
        text = td.text.strip()
        turf_dirt = judge_turf_dirt(text)

        # カンマ入り数字を抽出 ("2,000" → "2000")
        distance_match = re.search(r"[\d,]+", text)
        if distance_match is None:
            self._logger.error("距離のパースに失敗しました: %s", text)
            raise ParseError(f"距離のパースに失敗しました: {text}")
        distance = int(distance_match.group().replace(",", ""))

        return turf_dirt, distance

    def _parse_multi_value(self, td: Tag) -> list[str]:
        """同着を考慮して複数値を抽出する

        通常は1馬/1騎手だが、同着の場合は<br/>区切りで複数ある。
        「注記：同着」のstrongタグは除外する。

        Args:
            td (Tag): td要素

        Returns:
            list[str]: 値のリスト
        """
        values: list[str] = []
        current: list[str] = []

        for child in td.children:
            if isinstance(child, Tag):
                if child.name == "br":
                    text = "".join(current).strip()
                    if text:
                        values.append(text)
                    current = []
                elif child.name == "strong":
                    # 「注記：同着」などは無視
                    continue
                else:
                    current.append(child.text.strip())
            elif isinstance(child, str):
                current.append(child.strip())

        # 最後の要素を追加
        text = "".join(current).strip()
        if text:
            values.append(text)

        return values if values else [td.text.strip()]
