"""馬柱スクレイパーモジュール

netkeibaの馬情報ページをSeleniumでスクレイピングし、
馬柱（過去の出走成績）を取得する。
"""

import logging
import re
import time
import warnings
from io import StringIO

import numpy as np
import pandas as pd
from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

from scraping.config import KEIBAJO_TO_ID_DICT, PAST_PERFORMANCES_COLUMNS, ScrapingConfig
from scraping.exceptions import DriverError, ParseError
from scraping.utils import build_horse_info_url, calc_interval, set_chrome_options

# pandasのFutureWarningを無視する（pandas 3.0以降の警告対策）
warnings.filterwarnings("ignore", category=FutureWarning)

logger = logging.getLogger(__name__)


class PastPerformancesScraper:
    """馬柱のスクレイパー

    コンストラクタでSeleniumを使用してページを取得し、
    get_past_performances()メソッドで馬柱データを取得する。

    Attributes:
        horse_id (str): netkeibaの馬ID（10桁文字列）
        html_text (str): 馬情報ページのHTMLテキスト
        soup (BeautifulSoup): 馬情報ページのBeautifulSoupインスタンス
    """

    def __init__(self, horse_id: str, config: ScrapingConfig | None = None) -> None:
        """Seleniumで馬情報ページを取得してBeautifulSoup生成を行う

        Args:
            horse_id (str): netkeibaの馬ID（10桁文字列）
            config (ScrapingConfig | None): 設定オブジェクト

        Raises:
            DriverError: Selenium WebDriverの起動・ページ取得に失敗した場合
        """
        self.horse_id = horse_id
        cfg = config or ScrapingConfig()

        url = build_horse_info_url(horse_id, cfg)

        options = set_chrome_options()
        try:
            if cfg.chrome_driver_path:
                service = Service(cfg.chrome_driver_path)
            else:
                service = Service()
            driver = webdriver.Chrome(service=service, options=options)
        except Exception as exc:
            raise DriverError(f"ChromeDriverの起動に失敗しました: {exc}") from exc

        try:
            driver.get(url)
            time.sleep(3)  # JavaScriptの実行を待つ
            self.html_text = driver.page_source
        except Exception as exc:
            raise DriverError(f"ページの取得に失敗しました: {url} ({exc})") from exc
        finally:
            driver.quit()

        self.soup = BeautifulSoup(self.html_text, "html.parser")

    def get_past_performances(self) -> pd.DataFrame:
        """馬柱データを取得する

        馬情報ページのHTMLから馬柱テーブルをスクレイピングし、
        PAST_PERFORMANCES_COLUMNSのカラムを持つDataFrameを返す。
        新馬（戦績なし）の場合は0行のDataFrameを返す。

        Returns:
            pd.DataFrame: 馬柱のDataFrame（PAST_PERFORMANCES_COLUMNSのカラム）
        """
        return self._scrape_past_performances()

    def _scrape_past_performances(self) -> pd.DataFrame:
        """馬柱テーブルをスクレイピングする

        Returns:
            pd.DataFrame: 馬柱のDataFrame（PAST_PERFORMANCES_COLUMNSのカラム）

        Raises:
            ParseError: HTML解析や必要なカラム検証に失敗した場合
        """
        # テーブルの取得
        try:
            tables = pd.read_html(StringIO(self.html_text))
        except (ValueError, ImportError) as exc:
            raise ParseError("HTML内にテーブルが見つかりません") from exc

        # 馬柱テーブルを特定
        umabashira_df = pd.DataFrame()
        for table in tables:
            if (
                "日付" in str(table.columns)
                and "騎手" in str(table.columns)
                and table.shape[0] > 0
                and table.shape[1] >= 15
            ):
                umabashira_df = table
                break

        if umabashira_df.empty:
            logger.info("馬柱データが見つかりません。新馬の可能性があります。")
            return pd.DataFrame(columns=PAST_PERFORMANCES_COLUMNS)

        # カラム名の半角スペースを除去
        umabashira_df = umabashira_df.rename(columns=lambda col: col.replace(" ", ""))

        _validate_required_columns(
            umabashira_df,
            {
                "開催",
                "馬体重",
                "距離",
                "通過",
                "ペース",
                "上り",
                "オッズ",
                "枠番",
                "日付",
                "R",
                "頭数",
                "馬番",
                "人気",
                "着順",
                "斤量",
                "賞金",
            },
            "馬柱テーブルの解析に失敗しました。",
        )

        # 不要な列を削除（存在する場合のみ）
        columns_to_drop = ["映像", "馬場指数", "ﾀｲﾑ指数", "厩舎ｺﾒﾝﾄ", "備考"]
        existing_drops = [col for col in columns_to_drop if col in umabashira_df.columns]
        if existing_drops:
            umabashira_df = umabashira_df.drop(columns=existing_drops)

        # 天候カラムの追加（距離カラムの前に「天気」カラムがある場合に処理）
        if "天気" in umabashira_df.columns:
            umabashira_df = umabashira_df.rename(columns={"天気": "天候"})
        else:
            umabashira_df["天候"] = np.nan
        # 開催を回と開催日と競馬場に分ける
        umabashira_df["回"] = np.nan
        umabashira_df["開催日"] = np.nan
        for idx in umabashira_df.index:
            try:
                kaisai_str = str(umabashira_df.at[idx, "開催"])
                # 開催の1文字目が数字なら中央（例: "5東京8"）
                kai = int(kaisai_str[0])
                umabashira_df.at[idx, "回"] = kai
                rest = kaisai_str[1:]  # "東京8"
                umabashira_df.at[idx, "開催日"] = rest[2:]  # "8"
                umabashira_df.at[idx, "開催"] = rest[:2]  # "東京"
            except (ValueError, IndexError):
                # 地方や海外はそのまま
                pass
        umabashira_df = umabashira_df.rename(columns={"開催": "競馬場"})
        # 馬体重と増減の処理
        umabashira_df["増減"] = umabashira_df["馬体重"].str.extract(r"\(([-+]?\d+)\)")
        pattern = r"\(\+\d+\)|\(-\d+\)|\(0\)|\([^)]*\)"
        umabashira_df["馬体重"] = umabashira_df["馬体重"].str.replace(pattern, "", regex=True)
        # 芝ダカラムと距離の分割（"芝1200" → 芝ダ="芝", 距離=1200）
        umabashira_df["芝ダ"] = umabashira_df["距離"].apply(_extract_turf_dirt)
        umabashira_df["距離"] = umabashira_df["距離"].apply(_extract_distance)
        # 通過順を1〜4コーナーに分割
        umabashira_df = _split_passing_order(umabashira_df)
        # ペースを前3F/後3Fに分割
        umabashira_df = _split_pace(umabashira_df)
        # カラム名の改名
        umabashira_df = umabashira_df.rename(columns={"上り": "後3F"})
        umabashira_df = umabashira_df.rename(columns={"オッズ": "単勝オッズ"})
        umabashira_df = umabashira_df.rename(columns={"枠番": "枠"})
        # 騎手IDの追加
        umabashira_df = self._add_jockey_id(umabashira_df)
        # レースID・主催・間隔日数の追加
        umabashira_df = _add_race_info(umabashira_df)

        # 型変換
        umabashira_df["回"] = pd.to_numeric(umabashira_df["回"], errors="coerce")
        umabashira_df["開催日"] = pd.to_numeric(umabashira_df["開催日"], errors="coerce")
        umabashira_df["R"] = pd.to_numeric(umabashira_df["R"], errors="coerce")
        umabashira_df["頭数"] = pd.to_numeric(umabashira_df["頭数"], errors="coerce")
        umabashira_df["枠"] = pd.to_numeric(umabashira_df["枠"], errors="coerce")
        umabashira_df["馬番"] = pd.to_numeric(umabashira_df["馬番"], errors="coerce")
        umabashira_df["単勝オッズ"] = pd.to_numeric(umabashira_df["単勝オッズ"], errors="coerce")
        umabashira_df["人気"] = pd.to_numeric(umabashira_df["人気"], errors="coerce")
        umabashira_df["着順"] = pd.to_numeric(umabashira_df["着順"], errors="coerce")
        umabashira_df["斤量"] = pd.to_numeric(umabashira_df["斤量"], errors="coerce").astype(float)
        umabashira_df["距離"] = pd.to_numeric(umabashira_df["距離"], errors="coerce")
        umabashira_df["後3F"] = pd.to_numeric(umabashira_df["後3F"], errors="coerce")
        umabashira_df["馬体重"] = pd.to_numeric(umabashira_df["馬体重"], errors="coerce")
        umabashira_df["増減"] = pd.to_numeric(umabashira_df["増減"], errors="coerce")
        umabashira_df["賞金"] = pd.to_numeric(umabashira_df["賞金"], errors="coerce")
        try:
            umabashira_df["日付"] = pd.to_datetime(umabashira_df["日付"], format="%Y/%m/%d").dt.date
        except (ValueError, TypeError) as exc:
            raise ParseError("日付カラムの変換に失敗しました") from exc

        # PAST_PERFORMANCES_COLUMNSの順序に並べ替え
        missing_cols = set(PAST_PERFORMANCES_COLUMNS) - set(umabashira_df.columns)
        if missing_cols:
            raise ParseError(f"必要なカラムが不足しています: {sorted(missing_cols)}")
        umabashira_df = umabashira_df[PAST_PERFORMANCES_COLUMNS]

        # インデックスをリセット
        umabashira_df = umabashira_df.reset_index(drop=True)

        return umabashira_df

    def _add_jockey_id(self, df: pd.DataFrame) -> pd.DataFrame:
        """馬柱テーブルに騎手IDカラムを追加する

        Args:
            df (pd.DataFrame): 馬柱のDataFrame

        Returns:
            pd.DataFrame: 騎手IDカラムが追加されたDataFrame
        """
        jockey_id_list: list[str | float] = []

        # 戦績テーブルの行を取得
        table = self.soup.find("table", class_="db_h_race_results")
        if not isinstance(table, Tag):
            # テーブルが見つからない場合はNaNで埋める
            df["騎手ID"] = np.nan
            return df

        rows = table.find_all("tr")[1:]  # ヘッダー行をスキップ
        for row in rows:
            tds = row.find_all("td")
            # 騎手のtdは通常11番目（0-indexed=10）
            jockey_td = None
            for td in tds:
                a_tag = td.find("a")
                if a_tag and "jockey" in str(a_tag.get("href", "")):
                    jockey_td = a_tag
                    break

            if jockey_td is not None:
                try:
                    href: str = jockey_td["href"]
                    # /jockey/xxxxx/ or /jockey/result/recent/xxxxx/ → xxxxx
                    match = re.search(r"/jockey/(?:result/recent/)?(\d+)", href)
                    if match:
                        jockey_id_list.append(match.group(1).zfill(5))
                    else:
                        jockey_id_list.append(np.nan)
                except (KeyError, TypeError):
                    jockey_id_list.append(np.nan)
            else:
                jockey_id_list.append(np.nan)

        # pd.read_htmlの行数とhtml行数の不一致に対応
        if len(jockey_id_list) >= len(df):
            df["騎手ID"] = jockey_id_list[: len(df)]
        else:
            # 足りない分はNaNで埋める
            jockey_id_list.extend([np.nan] * (len(df) - len(jockey_id_list)))
            df["騎手ID"] = jockey_id_list

        return df


def _extract_turf_dirt(distance_text: str) -> str:
    """距離テキストから芝/ダ/障を抽出する

    Args:
        distance_text (str): "芝1200", "ダ1600", "障3000" 等

    Returns:
        str: "芝", "ダ", "障" のいずれか

    Raises:
        ParseError: 芝/ダ/障のいずれにも該当しない場合
    """
    text = str(distance_text)
    if "障" in text:
        return "障"
    elif "芝" in text:
        return "芝"
    elif "ダ" in text:
        return "ダ"
    raise ParseError(f"芝/ダ/障を判定できません: {distance_text}")


def _extract_distance(distance_text: str) -> int | float:
    """距離テキストから距離（メートル数）を抽出する

    Args:
        distance_text (str): "芝1200", "ダ1600", "障3000" 等

    Returns:
        int | float: 距離の整数値。抽出できない場合はNaN
    """
    text = str(distance_text)
    match = re.search(r"(\d+)", text)
    if match:
        return int(match.group(1))
    return np.nan


def _split_passing_order(df: pd.DataFrame) -> pd.DataFrame:
    """通過順を1〜4コーナーの個別カラムに分割する

    "3-4" → 3コーナー=3, 4コーナー=4
    "11-11-10-11" → 1コーナー=11, 2コーナー=11, 3コーナー=10, 4コーナー=11

    Args:
        df (pd.DataFrame): 通過カラムを持つDataFrame

    Returns:
        pd.DataFrame: 1〜4コーナー通過順カラムが追加されたDataFrame（元の通過カラムは削除）

    Raises:
        ParseError: 通過カラムが存在しない場合
    """
    if "通過" not in df.columns:
        raise ParseError("通過カラムが存在しません")

    corner_names = ["1コーナー通過順", "2コーナー通過順", "3コーナー通過順", "4コーナー通過順"]

    for col_name in corner_names:
        df[col_name] = np.nan

    mask = df["通過"].notna()
    if mask.any():
        parts_series = df.loc[mask, "通過"].astype(str).str.split("-")
        for idx in parts_series.index:
            parts = parts_series[idx]
            for i, corner_name in enumerate(reversed(corner_names)):
                pos = len(parts) - 1 - i
                if pos >= 0:
                    df.loc[idx, corner_name] = parts[pos]

    for col_name in corner_names:
        df[col_name] = pd.to_numeric(df[col_name], errors="coerce")

    df = df.drop(columns=["通過"])

    return df


def _split_pace(df: pd.DataFrame) -> pd.DataFrame:
    """ペースを前3F/後3Fに分割する

    "33.1-34.5" → レース前3F=33.1, レース後3F=34.5

    Args:
        df (pd.DataFrame): ペースカラムを持つDataFrame

    Returns:
        pd.DataFrame: レース前3F/レース後3Fカラムが追加されたDataFrame（元のペースは削除）

    Raises:
        ParseError: ペースカラムが存在しない場合
    """
    if "ペース" not in df.columns:
        raise ParseError("ペースカラムが存在しません")

    df["レース前3F"] = np.nan
    df["レース後3F"] = np.nan

    mask = df["ペース"].notna()
    if mask.any():
        pace_str = df.loc[mask, "ペース"].astype(str)
        parts = pace_str.str.split("-", expand=True)
        if parts.shape[1] >= 2:
            df.loc[mask, "レース前3F"] = pd.to_numeric(parts[0], errors="coerce")
            df.loc[mask, "レース後3F"] = pd.to_numeric(parts[1], errors="coerce")

    df = df.drop(columns=["ペース"])

    return df


def _add_race_info(df: pd.DataFrame) -> pd.DataFrame:
    """馬柱にレースID・主催・間隔日数カラムを追加する

    Args:
        df (pd.DataFrame): 馬柱のDataFrame

    Returns:
        pd.DataFrame: レースID, 主催, 間隔日数カラムが追加されたDataFrame
    """
    race_id_list: list[str] = []
    organize_list: list[str] = []
    interval_list: list[int | float] = []

    for idx in range(len(df)):
        # 日付情報
        race_date = str(df["日付"].iloc[idx])  # "yyyy/mm/dd"
        year = race_date[0:4]
        month = race_date[5:7]
        day = race_date[8:10]

        # 開催情報
        kai = df["回"].iloc[idx]
        kaisai_day = df["開催日"].iloc[idx]

        # R
        r_value = df["R"].iloc[idx]
        race_num = r_value if not pd.isna(r_value) else "00"

        # 競馬場
        raw_keibajo = str(df["競馬場"].iloc[idx]).strip()

        # レースIDと主催の作成
        if _is_katakana(raw_keibajo):
            race_id_list.append("")
            organize_list.append("海外")
        elif raw_keibajo in KEIBAJO_TO_ID_DICT:
            keibajo_id = KEIBAJO_TO_ID_DICT[raw_keibajo]
            if pd.isna(kai):
                # 地方
                race_id_list.append(f"{year}{keibajo_id}{month}{day}{int(race_num):02}")
                organize_list.append("地方")
            else:
                # 中央
                race_id = f"{year}{keibajo_id}{int(kai):02}{int(kaisai_day):02}{int(race_num):02}"
                race_id_list.append(race_id)
                organize_list.append("中央")
        else:
            # 未知の競馬場（海外扱い）
            race_id_list.append("")
            organize_list.append("海外")

        # レース間隔日数
        interval: int | float = np.nan
        for j in range(idx + 1, len(df)):
            if not pd.isna(df["人気"].iloc[j]):
                date1 = str(df["日付"].iloc[idx])
                date2 = str(df["日付"].iloc[j])
                interval = calc_interval(date1, date2)
                break
        interval_list.append(interval)

    df["レースID"] = race_id_list
    df["主催"] = organize_list
    df["間隔日数"] = interval_list

    return df


def _is_katakana(text: str) -> bool:
    """文字列が全てカタカナかどうかを判定する

    Args:
        text (str): 判定対象の文字列

    Returns:
        bool: 全てカタカナならTrue
    """
    return re.match(r"^[ァ-ヶー]+$", text) is not None


def _validate_required_columns(df: pd.DataFrame, required_columns: set[str], context: str) -> None:
    """DataFrameに必須カラムが存在することを検証する。

    Args:
        df (pd.DataFrame): 検証対象のDataFrame
        required_columns (set[str]): 必須カラム名の集合
        context (str): 例外メッセージに含める文脈情報

    Raises:
        ParseError: 必須カラムが不足している場合
    """
    missing_columns = sorted(required_columns - set(df.columns))
    if missing_columns:
        raise ParseError(f"{context} 必須カラムが不足しています: {missing_columns}")
