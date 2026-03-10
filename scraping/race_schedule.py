"""レーススケジュールスクレイパーモジュール

netkeibaの日別レーススケジュールページをSeleniumでスクレイピングし、
その日に行われるレースのスケジュール情報を取得する。
"""

import datetime
import logging
import re
import time

import pandas as pd
from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

from scraping.config import RACE_SCHEDULE_COLUMNS, ScrapingConfig
from scraping.exceptions import DriverError
from scraping.url_builder import build_today_race_list_url
from scraping.utils import judge_turf_dirt, race_id_to_race_info, set_chrome_options


class RaceScheduleScraper:
    """レーススケジュールスクレイパークラス

    コンストラクタでSeleniumを使用してページを取得し、
    get_race_schedule()メソッドでレーススケジュールを取得する。

    Attributes:
        year (int): 年
        month (int): 月
        day (int): 日
        html_text (str): レーススケジュールページのHTMLテキスト
        soup (BeautifulSoup): レーススケジュールページのBeautifulSoupインスタンス
    """

    def __init__(
        self,
        year: int,
        month: int,
        day: int,
        config: ScrapingConfig | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """Seleniumでレーススケジュールページを取得してBeautifulSoupを生成する

        Args:
            year (int): 年
            month (int): 月
            day (int): 日
            config (ScrapingConfig | None): 設定オブジェクト
            logger (logging.Logger | None): ロガーインスタンス

        Raises:
            DriverError: Selenium WebDriverの起動・ページ取得に失敗した場合
        """
        self.year = year
        self.month = month
        self.day = day
        self._logger = logger or logging.getLogger(__name__)
        cfg = config or ScrapingConfig()

        url = build_today_race_list_url(year, month, day, cfg)

        options = set_chrome_options()
        try:
            if cfg.chrome_driver_path:
                service = Service(cfg.chrome_driver_path)
            else:
                service = Service()
            driver = webdriver.Chrome(service=service, options=options)
        except Exception as exc:
            self._logger.error("ChromeDriverの起動に失敗しました: %s", exc)
            raise DriverError(f"ChromeDriverの起動に失敗しました: {exc}") from exc

        try:
            driver.get(url)
            time.sleep(3)  # JavaScriptの実行を待つ
            self.html_text = driver.page_source
        except Exception as exc:
            self._logger.error("ページの取得に失敗しました: %s (%s)", url, exc)
            raise DriverError(f"ページの取得に失敗しました: {url} ({exc})") from exc
        finally:
            driver.quit()

        self.soup = BeautifulSoup(self.html_text, "html.parser")

    def get_race_schedule(self) -> pd.DataFrame:
        """レーススケジュールを取得する

        RACE_SCHEDULE_COLUMNSに定義された12カラムのDataFrameを返す。
        開催のない日は0行のDataFrameを返す。

        Returns:
            pd.DataFrame: レーススケジュール（RACE_SCHEDULE_COLUMNSのカラム）
        """
        data_lists = self.soup.find_all("dl", class_="RaceList_DataList")
        if not data_lists:
            return pd.DataFrame(columns=RACE_SCHEDULE_COLUMNS)

        date_obj = datetime.date(self.year, self.month, self.day)
        rows: list[dict[str, object]] = []

        for dl in data_lists:
            if not isinstance(dl, Tag):
                continue

            # ヘッダーから馬場状態を取得
            baba_turf, baba_dirt = _extract_baba_from_header(dl)

            # 各レース項目を処理
            items = dl.find_all(class_="RaceList_DataItem")
            for item in items:
                if not isinstance(item, Tag):
                    continue
                row = self._parse_race_item(item, date_obj, baba_turf, baba_dirt)
                if row is not None:
                    rows.append(row)

        if not rows:
            return pd.DataFrame(columns=RACE_SCHEDULE_COLUMNS)

        return pd.DataFrame(rows, columns=RACE_SCHEDULE_COLUMNS)

    def _parse_race_item(
        self,
        item: Tag,
        date_obj: datetime.date,
        baba_turf: str,
        baba_dirt: str,
    ) -> dict[str, object] | None:
        """1件のレース項目を解析する

        Args:
            item (Tag): RaceList_DataItemのli要素
            date_obj (datetime.date): 開催日
            baba_turf (str): 芝の馬場状態
            baba_dirt (str): ダートの馬場状態

        Returns:
            dict[str, object] | None: レース情報の辞書。解析失敗時はNone
        """
        # レースIDを抽出（aタグのhrefから）
        a_tag = item.find("a")
        if not isinstance(a_tag, Tag):
            self._logger.warning("レースリンクが見つかりません")
            return None

        href = str(a_tag.get("href", ""))
        race_id_match = re.search(r"race_id=(\d{12})", href)
        if race_id_match is None:
            self._logger.warning("レースIDが抽出できません: %s", href)
            return None

        race_id = race_id_match.group(1)

        # レースIDから競馬場・回・開催日・Rを構築
        _, keibajo, kai, kaisai_day, r_value = race_id_to_race_info(race_id)

        # レース名を抽出
        title_tag = item.find(class_="RaceList_ItemTitle")
        race_name = ""
        if isinstance(title_tag, Tag):
            race_name = title_tag.text.strip()

        # RaceDataから発走時刻・芝ダ・距離・頭数を抽出
        race_data = item.find(class_="RaceData")
        if not isinstance(race_data, Tag):
            self._logger.warning("RaceDataが見つかりません: race_id=%s", race_id)
            return None

        # 発走時刻
        time_span = race_data.find(class_="RaceList_Itemtime")
        start_time = ""
        if isinstance(time_span, Tag):
            time_text = time_span.text.strip()
            time_match = re.match(r"(\d{1,2}):(\d{2})", time_text)
            if time_match:
                hour = int(time_match.group(1))
                minute = time_match.group(2)
                start_time = f"{hour:02d}:{minute}"

        # 芝ダ・距離
        # RaceList_ItemLong クラスを持つspanを探す。障害レースではclass=""の場合がある
        item_long = race_data.find(class_=re.compile(r"RaceList_ItemLong"))
        turf_dirt = ""
        distance = 0
        if isinstance(item_long, Tag):
            long_text = item_long.text.strip()
            turf_dirt = judge_turf_dirt(long_text)
            distance_match = re.search(r"\d+", long_text)
            if distance_match:
                distance = int(distance_match.group())
        else:
            # フォールバック: クラスなしのspanから芝ダ距離パターンを探す
            for span in race_data.find_all("span"):
                span_text = span.text.strip() if isinstance(span, Tag) else ""
                if re.match(r"^(芝|ダ|障)\d+m$", span_text):
                    turf_dirt = judge_turf_dirt(span_text)
                    dist_match = re.search(r"\d+", span_text)
                    if dist_match:
                        distance = int(dist_match.group())
                    break

        # 頭数
        num_span = race_data.find(class_="RaceList_Itemnumber")
        num_runners = 0
        if isinstance(num_span, Tag):
            num_text = num_span.text.strip()
            num_match = re.search(r"(\d+)", num_text)
            if num_match:
                num_runners = int(num_match.group(1))

        # 馬場状態は芝ダに応じて決定
        if turf_dirt == "芝":
            baba = baba_turf
        elif turf_dirt == "ダ":
            baba = baba_dirt
        elif turf_dirt == "障":
            # 障害は芝の馬場状態を使用
            baba = baba_turf
        else:
            baba = ""

        return {
            "レースID": race_id,
            "日付": date_obj,
            "競馬場": keibajo,
            "回": kai,
            "開催日": kaisai_day,
            "R": r_value,
            "レース名": race_name,
            "芝ダ": turf_dirt,
            "距離": distance,
            "頭数": num_runners,
            "馬場": baba,
            "発走時刻": start_time,
        }


def _extract_baba_from_header(dl: Tag) -> tuple[str, str]:
    """RaceList_DataListのヘッダーから馬場状態を抽出する

    Args:
        dl (Tag): RaceList_DataListのdl要素

    Returns:
        tuple[str, str]: (芝の馬場状態, ダートの馬場状態)
    """
    dt = dl.find("dt", class_="RaceList_DataHeader")
    if not isinstance(dt, Tag):
        return "", ""

    desc = dt.find(class_="RaceList_DataDesc")
    if not isinstance(desc, Tag):
        return "", ""

    baba_turf = ""
    shiba_span = desc.find(class_="Shiba")
    if isinstance(shiba_span, Tag):
        # "芝(A)：良" → "良"
        shiba_text = shiba_span.text.strip()
        match = re.search(r"[：:](.+)$", shiba_text)
        if match:
            baba_turf = match.group(1).strip()

    baba_dirt = ""
    da_span = desc.find(class_="Da")
    if isinstance(da_span, Tag):
        # "ダ：良" → "良"
        da_text = da_span.text.strip()
        match = re.search(r"[：:](.+)$", da_text)
        if match:
            baba_dirt = match.group(1).strip()

    return baba_turf, baba_dirt
