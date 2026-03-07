"""出馬表ページスクレイパーモジュール

netkeibaの出馬表ページをスクレイピングし、
レース情報・出馬表を取得する。
"""

import logging
from io import StringIO

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup

from scraping.config import (
    ENTRY_COLUMNS,
    ENTRY_NON_NAN_COLUMNS,
    SHUTUBA_RAW_COLUMNS,
    VALID_AFFILIATIONS,
    VALID_ENTRY_STATUSES,
    VALID_GENDERS,
    ScrapingConfig,
)
from scraping.exceptions import NetworkError, PageNotFoundError, ParseError
from scraping.race_info import scrape_race_info
from scraping.utils import build_entry_url


class EntryPageScraper:
    """出馬表ページのスクレイパー

    コンストラクタでHTTP取得とBeautifulSoup生成を行い、
    各パブリックメソッドでレース情報・出馬表を取得する。

    Attributes:
        race_id (str): netkeibaのレースID（12桁文字列）
        soup (BeautifulSoup): 出馬表ページのBeautifulSoupインスタンス
        html_text (str): 出馬表ページのHTMLテキスト
    """

    def __init__(
        self,
        race_id: str,
        config: ScrapingConfig | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """HTTP取得とBeautifulSoup生成を行う

        Args:
            race_id (str): netkeibaのレースID（12桁文字列）
            config (ScrapingConfig | None): 設定オブジェクト
            logger (logging.Logger | None): ロガーインスタンス

        Raises:
            NetworkError: HTTPリクエストに失敗した場合
            PageNotFoundError: ページが見つからない場合
        """
        self.race_id = race_id
        self._logger = logger or logging.getLogger(__name__)
        cfg = config or ScrapingConfig()

        url = build_entry_url(race_id, cfg)
        try:
            response = requests.get(
                url, headers=cfg.headers, allow_redirects=True, timeout=cfg.request_timeout
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 404:
                self._logger.error("出馬表ページが見つかりません: %s", url)
                raise PageNotFoundError(f"出馬表ページが見つかりません: {url}") from e
            self._logger.error("HTTPエラーが発生しました: %s", e)
            raise NetworkError(f"HTTPエラーが発生しました: {e}") from e
        except requests.exceptions.RequestException as e:
            self._logger.error("ネットワークエラーが発生しました: %s", e)
            raise NetworkError(f"ネットワークエラーが発生しました: {e}") from e

        response.encoding = "EUC-JP"
        self.html_text = response.text
        self.soup = BeautifulSoup(self.html_text, "html.parser")

    def get_race_info(self) -> pd.DataFrame:
        """レース情報を取得する

        race_info.scrape_race_info()を呼び出してレース基本情報を返す。

        Returns:
            pd.DataFrame: レース基本情報のDataFrame（1行、RACE_INFO_COLUMNSのカラム）
        """
        return scrape_race_info(self.soup, self.race_id, logger=self._logger)

    def get_entry(self) -> pd.DataFrame:
        """出馬表を取得する

        出馬表ページのHTMLから出馬表テーブルをスクレイピングし、
        ENTRY_COLUMNSのカラムを持つDataFrameを返す。

        Returns:
            pd.DataFrame: 出馬表のDataFrame（ENTRY_COLUMNSのカラム）

        Raises:
            ValueError: 必要なカラムが不足している場合
            ParseError: バリデーション違反がある場合
        """
        return self._scrape_entry()

    def _scrape_entry(self) -> pd.DataFrame:
        """出馬表テーブルをスクレイピングする

        Returns:
            pd.DataFrame: 出馬表のDataFrame（ENTRY_COLUMNSのカラム）

        Raises:
            ValueError: 必要なカラムが不足している場合
            ParseError: バリデーション違反がある場合
        """
        # 出馬表テーブルを取得
        tables = pd.read_html(StringIO(self.html_text))
        entry_df = tables[0]

        # カラム名を設定（MultiIndex → フラット）
        entry_df.columns = pd.Index(SHUTUBA_RAW_COLUMNS)

        # 出走区分を「印」列（削除列の1つ目）から判定
        # SHUTUBA_RAW_COLUMNSでは3番目（index=2）が「削除」=実際の「印」列
        # 取消/除外の場合はそのテキストが入り、通常はNaN
        mark_col = entry_df.iloc[:, 2]
        entry_df["出走区分"] = mark_col.apply(_classify_entry_status)

        # 不要な列の削除
        entry_df = entry_df.drop(columns=["削除"])

        # レースIDを追加
        entry_df["レースID"] = self.race_id

        # 所属カラムの追加（厩舎の先頭2文字=所属）
        trainer_col_loc = entry_df.columns.get_loc("厩舎")
        assert isinstance(trainer_col_loc, int), "厩舎カラムが重複しています"
        entry_df.insert(trainer_col_loc, "所属", entry_df["厩舎"].str[:2])
        # 厩舎カラムから所属を削除し、先頭の空白を除去
        entry_df["厩舎"] = entry_df["厩舎"].str[2:].str.strip()

        # 馬体重と増減の処理
        if entry_df["馬体重(増減)"].astype(str).str.contains(r"\d", regex=True).any():
            # 増減カラムの追加（前計不の場合はNaN）
            entry_df["増減"] = entry_df["馬体重(増減)"].str.extract(r"\(([-+]?\d+)\)")
            # 馬体重カラムから増減と括弧部分を削除
            pattern = r"\([^)]*\)"
            entry_df["馬体重(増減)"] = entry_df["馬体重(増減)"].str.replace(pattern, "", regex=True)
        else:
            # 馬体重未発表の場合
            entry_df["増減"] = np.nan
            entry_df["馬体重(増減)"] = np.nan
        entry_df = entry_df.rename(columns={"馬体重(増減)": "馬体重"})

        # 馬ID,騎手ID,厩舎IDの追加
        entry_df = self._add_id_from_table(entry_df)

        # 性齢の分割追加
        entry_df = _add_gender_age(entry_df)

        # 型変換
        entry_df["枠"] = pd.to_numeric(entry_df["枠"], errors="coerce")
        entry_df["馬番"] = pd.to_numeric(entry_df["馬番"], errors="coerce")
        entry_df["斤量"] = pd.to_numeric(entry_df["斤量"], errors="coerce").astype(float)
        entry_df["馬体重"] = pd.to_numeric(entry_df["馬体重"], errors="coerce")
        entry_df["増減"] = pd.to_numeric(entry_df["増減"], errors="coerce")

        # ENTRY_COLUMNSに必要なカラムが揃っているか確認
        missing_cols = set(ENTRY_COLUMNS) - set(entry_df.columns)
        if missing_cols:
            self._logger.error("必要なカラムが不足しています: %s", sorted(missing_cols))
            raise ValueError(f"必要なカラムが不足しています: {sorted(missing_cols)}")
        entry_df = entry_df[ENTRY_COLUMNS]

        # バリデーション
        self._validate_entry(entry_df)

        return entry_df

    def _add_id_from_table(self, df: pd.DataFrame) -> pd.DataFrame:
        """出馬表テーブルにスクレイピングで取得できるID（馬、騎手、厩舎）を追加する

        Args:
            df (pd.DataFrame): IDを追加するDataFrame

        Returns:
            pd.DataFrame: 馬ID,騎手ID,厩舎IDを追加したDataFrame
        """
        add_df = pd.DataFrame(index=df.index, columns=["馬ID", "騎手ID", "厩舎ID"])

        # 馬IDを追加
        # NOTE: soup.find_all("tr", class_="HorseList") は出走馬の行だけでなく
        # フッター行（枠順展示リンク行・空行）も含む。これらのフッター行には
        # HorseName/Jockey/Trainer要素が存在しないため、要素が見つからない行は
        # スキップすることでpd.read_htmlが返す行数と一致させている。
        horse_list = self.soup.find_all("tr", class_="HorseList")
        horse_id_list: list[str] = []
        for horse_row in horse_list:
            horse_name_span = horse_row.find("span", class_="HorseName")
            if horse_name_span is not None:
                horse_url: str = horse_name_span.a["href"]
                horse_id_list.append(horse_url[-10:])
        add_df["馬ID"] = horse_id_list

        # 騎手IDを追加
        jockey_id_list: list[str | float] = []
        for horse_row in horse_list:
            jockey_td = horse_row.find("td", class_="Jockey")
            if jockey_td is not None:
                try:
                    jockey_url: str = jockey_td.a["href"]
                    jockey_id_list.append(jockey_url[-6:-1])
                except (TypeError, KeyError):
                    jockey_id_list.append(np.nan)
        add_df["騎手ID"] = jockey_id_list

        # 厩舎IDを追加
        trainer_id_list: list[str] = []
        for horse_row in horse_list:
            trainer_td = horse_row.find("td", class_="Trainer")
            if trainer_td is not None:
                trainer_url: str = trainer_td.a["href"]
                trainer_id_list.append(trainer_url[-6:-1])
        add_df["厩舎ID"] = trainer_id_list

        # 元のデータフレームと結合
        df = pd.concat([df, add_df], axis=1)

        return df

    def _validate_entry(self, df: pd.DataFrame) -> None:
        """出馬表DataFrameのバリデーションを行う

        Args:
            df (pd.DataFrame): ENTRY_COLUMNSのカラムを持つDataFrame

        Raises:
            ParseError: バリデーション違反がある場合
        """
        # NaN不可カラムの検証（全行）
        for col in ENTRY_NON_NAN_COLUMNS:
            nan_rows = df[df[col].isna()]
            if not nan_rows.empty:
                umaban_list = nan_rows["馬番"].tolist()
                self._logger.error("'%s'にNaNが含まれています: 馬番%s", col, umaban_list)
                raise ParseError(f"'{col}'にNaNが含まれています: 馬番{umaban_list}")

        # 出走区分のバリデーション
        invalid_statuses = set(df["出走区分"].unique()) - VALID_ENTRY_STATUSES
        if invalid_statuses:
            self._logger.error("出走区分が不正です: %s", invalid_statuses)
            raise ParseError(f"出走区分が不正です: {invalid_statuses}")

        # 性別のバリデーション
        invalid_genders = set(df["性別"].unique()) - VALID_GENDERS
        if invalid_genders:
            self._logger.error("性別が不正です: %s", invalid_genders)
            raise ParseError(f"性別が不正です: {invalid_genders}")

        # 所属のバリデーション
        invalid_affiliations = set(df["所属"].unique()) - VALID_AFFILIATIONS
        if invalid_affiliations:
            self._logger.error("所属が不正です: %s", invalid_affiliations)
            raise ParseError(f"所属が不正です: {invalid_affiliations}")


def _classify_entry_status(mark: object) -> str:
    """印テキストから出走区分を判定する

    Args:
        mark (object): 印の値（NaN or "取消" or "除外"）

    Returns:
        str: 出走区分（"出走", "取消", "除外"のいずれか）
    """
    text = str(mark)
    if text in {"取消", "除外"}:
        return text
    return "出走"


def _add_gender_age(df: pd.DataFrame) -> pd.DataFrame:
    """出馬表テーブルに性別・年齢カラムを追加する

    性齢カラム（例: "牡3"）を性別（"牡"）と年齢（3）に分割して追加する。

    Args:
        df (pd.DataFrame): 性齢カラムを持つDataFrame

    Returns:
        pd.DataFrame: 性別・年齢カラムが追加されたDataFrame
    """
    gender_age_df = pd.DataFrame(
        {"性別": df["性齢"].str[0], "年齢": df["性齢"].str[1:].astype(int)},
        index=df.index,
    )
    df = pd.concat([df, gender_age_df], axis=1)

    return df
