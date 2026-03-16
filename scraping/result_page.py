"""結果ページスクレイパーモジュール

netkeibaのレース結果ページをスクレイピングし、
レース結果・コーナー通過順・払い戻し・ラップタイムを取得する。
"""

import logging
import re
from io import StringIO

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup, Tag

from scraping.config import (
    BRACKET_PAYOFF_COLUMNS,
    EXACTA_PAYOFF_COLUMNS,
    LAP_TIME_COLUMNS,
    NON_NAN_COLUMNS,
    PAYBACK_COLUMNS,
    QUINELLA_PAYOFF_COLUMNS,
    QUINELLA_PLACE_PAYOFF_COLUMNS,
    RESULT_COLUMNS,
    SHOW_PAYOFF_COLUMNS,
    TRIFECTA_PAYOFF_COLUMNS,
    TRIO_PAYOFF_COLUMNS,
    VALID_AFFILIATIONS,
    VALID_GENDERS,
    VALID_IJO_KUBUN,
    WIN_PAYOFF_COLUMNS,
    ScrapingConfig,
)
from scraping.exceptions import NetworkError, PageNotFoundError, ParseError
from scraping.race_info import scrape_race_info
from scraping.url_builder import build_result_url


class ResultPageScraper:
    """レース結果ページのスクレイパー

    コンストラクタでHTTP取得とBeautifulSoup生成を行い、
    各パブリックメソッドでレース結果・コーナー通過順・払い戻し・ラップタイムを取得する。

    Attributes:
        race_id (str): netkeibaのレースID（12桁文字列）
        soup (BeautifulSoup): 結果ページのBeautifulSoupインスタンス
        html_text (str): 結果ページのHTMLテキスト
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

        url = build_result_url(race_id, cfg)
        try:
            response = requests.get(
                url, headers=cfg.headers, allow_redirects=True, timeout=cfg.request_timeout
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 404:
                self._logger.error("レース結果ページが見つかりません: %s", url)
                raise PageNotFoundError(f"レース結果ページが見つかりません: {url}") from e
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

    def get_result(self) -> pd.DataFrame:
        """レース結果の表を取得する

        結果ページのHTMLからレース結果テーブルをスクレイピングし、
        RESULT_COLUMNSのカラムを持つDataFrameを返す。

        Returns:
            pd.DataFrame: レース結果のDataFrame（RESULT_COLUMNSのカラム）。
                開催中止の場合は1行で値がすべてNaN

        Raises:
            ValueError: 必要なカラムが不足している場合
            ParseError: バリデーション違反がある場合
        """
        return self._scrape_result()

    def get_corner(self) -> pd.DataFrame:
        """コーナー通過順を取得する

        結果ページからコーナー通過順位を抽出してDataFrameで返す。
        直線レースや掲載のないレースではコーナー通過順がすべてNaNの1行DataFrameを返す。

        Returns:
            pd.DataFrame: コーナー通過順のDataFrame（CORNER_COLUMNSのカラム、1行）
        """
        return self._scrape_corner()

    def get_win_payoff(self) -> pd.DataFrame:
        """単勝払い戻しを取得する

        結果ページから単勝の払い戻し情報を抽出し、
        WIN_PAYOFF_COLUMNSのカラムを持つ1行DataFrameを返す。

        Returns:
            pd.DataFrame: 単勝払い戻しのDataFrame（WIN_PAYOFF_COLUMNS、1行）
        """
        return self._scrape_payoff_by_type("単勝", WIN_PAYOFF_COLUMNS, 1, "馬番")

    def get_show_payoff(self) -> pd.DataFrame:
        """複勝払い戻しを取得する

        結果ページから複勝の払い戻し情報を抽出し、
        SHOW_PAYOFF_COLUMNSのカラムを持つ1行DataFrameを返す。

        Returns:
            pd.DataFrame: 複勝払い戻しのDataFrame（SHOW_PAYOFF_COLUMNS、1行）
        """
        return self._scrape_payoff_by_type("複勝", SHOW_PAYOFF_COLUMNS, 1, "馬番")

    def get_bracket_payoff(self) -> pd.DataFrame:
        """枠連払い戻しを取得する

        結果ページから枠連の払い戻し情報を抽出し、
        BRACKET_PAYOFF_COLUMNSのカラムを持つ1行DataFrameを返す。
        7頭以下のレースなど枠連不成立時は全カラムNaN（レースIDを除く）。

        Returns:
            pd.DataFrame: 枠連払い戻しのDataFrame（BRACKET_PAYOFF_COLUMNS、1行）
        """
        return self._scrape_payoff_by_type("枠連", BRACKET_PAYOFF_COLUMNS, 2, "組番")

    def get_quinella_payoff(self) -> pd.DataFrame:
        """馬連払い戻しを取得する

        結果ページから馬連の払い戻し情報を抽出し、
        QUINELLA_PAYOFF_COLUMNSのカラムを持つ1行DataFrameを返す。

        Returns:
            pd.DataFrame: 馬連払い戻しのDataFrame（QUINELLA_PAYOFF_COLUMNS、1行）
        """
        return self._scrape_payoff_by_type("馬連", QUINELLA_PAYOFF_COLUMNS, 2, "組番")

    def get_quinella_place_payoff(self) -> pd.DataFrame:
        """ワイド払い戻しを取得する

        結果ページからワイドの払い戻し情報を抽出し、
        QUINELLA_PLACE_PAYOFF_COLUMNSのカラムを持つ1行DataFrameを返す。

        Returns:
            pd.DataFrame: ワイド払い戻しのDataFrame（QUINELLA_PLACE_PAYOFF_COLUMNS、1行）
        """
        return self._scrape_payoff_by_type("ワイド", QUINELLA_PLACE_PAYOFF_COLUMNS, 2, "組番")

    def get_exacta_payoff(self) -> pd.DataFrame:
        """馬単払い戻しを取得する

        結果ページから馬単の払い戻し情報を抽出し、
        EXACTA_PAYOFF_COLUMNSのカラムを持つ1行DataFrameを返す。

        Returns:
            pd.DataFrame: 馬単払い戻しのDataFrame（EXACTA_PAYOFF_COLUMNS、1行）
        """
        return self._scrape_payoff_by_type("馬単", EXACTA_PAYOFF_COLUMNS, 2, "組番")

    def get_trio_payoff(self) -> pd.DataFrame:
        """3連複払い戻しを取得する

        結果ページから3連複の払い戻し情報を抽出し、
        TRIO_PAYOFF_COLUMNSのカラムを持つ1行DataFrameを返す。

        Returns:
            pd.DataFrame: 3連複払い戻しのDataFrame（TRIO_PAYOFF_COLUMNS、1行）
        """
        return self._scrape_payoff_by_type("3連複", TRIO_PAYOFF_COLUMNS, 3, "組番")

    def get_trifecta_payoff(self) -> pd.DataFrame:
        """3連単払い戻しを取得する

        結果ページから3連単の払い戻し情報を抽出し、
        TRIFECTA_PAYOFF_COLUMNSのカラムを持つ1行DataFrameを返す。

        Returns:
            pd.DataFrame: 3連単払い戻しのDataFrame（TRIFECTA_PAYOFF_COLUMNS、1行）
        """
        return self._scrape_payoff_by_type("3連単", TRIFECTA_PAYOFF_COLUMNS, 3, "組番")

    def get_lap_time(self) -> pd.DataFrame:
        """ラップタイムを取得する

        結果ページからラップタイム情報を抽出し、
        LAP_TIME_COLUMNSのカラムを持つ1行DataFrameで返す。
        障害レースではレースID以外がすべてNaNの1行DataFrameを返す。

        Returns:
            pd.DataFrame: ラップタイムのDataFrame（LAP_TIME_COLUMNS、1行）。
                障害レースではレースID以外がNaN
        """
        # レース情報を取得してレースタイプを判定
        race_info_df = self.get_race_info()
        shiba_da = str(race_info_df["芝ダ"].iloc[0])
        direction = str(race_info_df["左右"].iloc[0])

        if "障" in shiba_da:
            # 障害レースにはラップタイムなし（レースID以外はNaN）
            data: dict[str, object] = {"レースID": self.race_id}
            result_df = pd.DataFrame([data])
            result_df = result_df.reindex(columns=LAP_TIME_COLUMNS)
            return result_df

        if direction == "直":
            # 直線レースはコーナーがないのでテーブルインデックスがずれる
            return self._scrape_lap_time(race_type="直線")
        else:
            return self._scrape_lap_time()

    def _scrape_result(self) -> pd.DataFrame:
        """レース結果の表を取得する

        結果ページのHTMLからレース結果テーブルをスクレイピングし、
        RESULT_COLUMNSのカラムを持つDataFrameを返す。

        Returns:
            pd.DataFrame: レース結果のDataFrame（RESULT_COLUMNSのカラム）。
                開催中止の場合は1行でレースID以外がすべてNaN

        Raises:
            ValueError: 必要なカラムが不足している場合
            ParseError: バリデーション違反がある場合
        """
        # 結果の表を取得
        tables = pd.read_html(StringIO(self.html_text))
        result_df = tables[0]

        # コンディション不良で開催中止の場合
        if result_df.iloc[0, 0] == "単勝":
            nan_values: list[object] = [np.nan] * len(RESULT_COLUMNS)
            cancel_df = pd.DataFrame([nan_values], columns=RESULT_COLUMNS)
            cancel_df["レースID"] = self.race_id
            return cancel_df

        # 列名に半角スペースがあれば除去する
        result_df = result_df.rename(columns=lambda col: col.replace(" ", ""))

        # カラムの追加
        result_df["異常区分"] = result_df["着順"].apply(_classify_ijo_kubun)
        result_df["レースID"] = self.race_id

        # 所属カラムの追加（厩舎の先頭2文字=所属）
        trainer_col_loc = result_df.columns.get_loc("厩舎")
        assert isinstance(trainer_col_loc, int), "厩舎カラムが重複しています"
        result_df.insert(trainer_col_loc, "所属", result_df["厩舎"].str[:2])
        # 厩舎カラムから所属を削除し、先頭の空白を除去
        result_df["厩舎"] = result_df["厩舎"].str[2:].str.strip()

        # 馬体重と増減の処理
        if pd.isna(result_df["馬体重(増減)"].iloc[0]):
            # 地方で馬体重表記がない場合
            result_df["増減"] = result_df["馬体重(増減)"]
        else:
            # 増減カラムの追加（前計不の場合はNaN）
            result_df["増減"] = result_df["馬体重(増減)"].str.extract(r"\(([-+]?\d+)\)")
            # 馬体重カラムから増減と前計不を削除
            pattern = r"\(\+\d+\)|\(-\d+\)|\(0\)|\((.*?)\)"
            result_df["馬体重(増減)"] = result_df["馬体重(増減)"].str.replace(
                pattern, "", regex=True
            )
        result_df = result_df.rename(columns={"馬体重(増減)": "馬体重"})  # 馬体重カラムの改名

        # 馬ID,騎手ID,厩舎IDの追加
        result_df = _add_id_from_table(self.soup, result_df)
        # 性齢の分割追加
        result_df = _add_gender_age(result_df)
        # コーナー通過順を1〜4コーナーに分割
        result_df = _split_corner_passing_order(result_df)

        # RESULT_COLUMNSに必要なカラムが揃っているか確認
        missing_cols = set(RESULT_COLUMNS) - set(result_df.columns)
        if missing_cols:
            self._logger.error("必要なカラムが不足しています: %s", sorted(missing_cols))
            raise ValueError(f"必要なカラムが不足しています: {sorted(missing_cols)}")
        # 型変換
        result_df["着順"] = pd.to_numeric(result_df["着順"], errors="coerce")
        result_df["斤量"] = pd.to_numeric(result_df["斤量"], errors="coerce").astype(float)
        result_df["人気"] = pd.to_numeric(result_df["人気"], errors="coerce")
        result_df["単勝オッズ"] = pd.to_numeric(result_df["単勝オッズ"], errors="coerce")
        result_df["後3F"] = pd.to_numeric(result_df["後3F"], errors="coerce")
        result_df["馬体重"] = pd.to_numeric(result_df["馬体重"], errors="coerce")
        result_df["増減"] = pd.to_numeric(result_df["増減"], errors="coerce")
        # 着差から降着を検出して異常区分に反映
        kochaku_pattern = r"^\d+位降着$"
        kochaku_mask = result_df["着差"].str.match(kochaku_pattern, na=False)
        result_df.loc[kochaku_mask, "異常区分"] = "降着"
        result_df = result_df[RESULT_COLUMNS]  # RESULT_COLUMNSの順序に並べ替え

        # バリデーション
        self._validate_result(result_df)

        return result_df

    def _scrape_corner(self) -> pd.DataFrame:
        """コーナー通過順位を取得する

        Returns:
            pd.DataFrame: コーナー通過順位のDataFrame（CORNER_COLUMNS、1行）
        """
        corner_names = ["1コーナー通過順", "2コーナー通過順", "3コーナー通過順", "4コーナー通過順"]
        corner_values: list[str | float] = [np.nan, np.nan, np.nan, np.nan]

        corner_html = self.soup.find("div", class_="ResultPayBackRightWrap")
        if corner_html is not None and isinstance(corner_html, Tag):
            race_common_table = corner_html.find("table", class_="RaceCommon_Table Corner_Num")
            if race_common_table is not None and isinstance(race_common_table, Tag):
                trs = race_common_table.find_all("tr")
                raw_list: list[str] = []
                for row in trs:
                    td = row.find("td")
                    if td is not None:
                        raw_list.append(td.text.strip())

                # 表示されてないコーナーはNaNで埋める（先頭に挿入）
                while len(raw_list) < 4:
                    raw_list.insert(0, "")

                # テキストをセット（空文字列はNaN）
                for i, text in enumerate(raw_list):
                    if text:
                        corner_values[i] = text

        corner_data: dict[str, list[object]] = {"レースID": [self.race_id]}
        for name, value in zip(corner_names, corner_values):
            corner_data[name] = [value]

        return pd.DataFrame(corner_data)

    def _scrape_payoff_by_type(
        self,
        bet_name: str,
        columns: list[str],
        combination_size: int,
        number_label: str,
    ) -> pd.DataFrame:
        """特定の券種の払い戻しをDataFrameで返す

        Args:
            bet_name (str): 券種名（"単勝", "複勝", "枠連"など）
            columns (list[str]): 出力DataFrameのカラム定義
            combination_size (int): 組み合わせサイズ（1=単複, 2=2連系, 3=3連系）
            number_label (str): 番号カラムのラベル（"馬番" or "組番"）

        Returns:
            pd.DataFrame: 払い戻しのDataFrame（1行）
        """
        tables = pd.read_html(StringIO(self.html_text))

        df1 = tables[1]
        df1.columns = pd.Index(PAYBACK_COLUMNS)
        df2 = tables[2]
        df2.columns = pd.Index(PAYBACK_COLUMNS)
        raw_df = pd.concat([df1, df2], ignore_index=True)

        row = raw_df[raw_df["券種"] == bet_name]

        if row.empty:
            nan_values = [np.nan] * (len(columns) - 1)
            return pd.DataFrame([[self.race_id] + nan_values], columns=columns)

        row_data = row.iloc[0]
        return _build_payoff_wide_df(
            self.race_id,
            bet_name,
            columns,
            combination_size,
            number_label,
            str(row_data["馬番"]),
            str(row_data["払戻"]),
            str(row_data["人気"]),
        )

    def _scrape_lap_time(self, race_type: str = "平地") -> pd.DataFrame:
        """ラップタイムをスクレイピングしてLAP_TIME_COLUMNSのDataFrameを返す

        HTMLテーブルからラップタイム（区間タイム）を取得し、
        100mごとのカラムに展開した1行DataFrameを返す。

        Args:
            race_type (str): レースの種類。"平地" or "直線"

        Returns:
            pd.DataFrame: LAP_TIME_COLUMNSのカラムを持つ1行DataFrame。
                取得失敗時はレースIDのみが設定されその他のカラムがNaNの1行DataFrameを返す。
        """
        table_index = 3 if race_type == "直線" else 5

        try:
            tables = pd.read_html(StringIO(self.html_text))
            lap_tmp_df = tables[table_index]
        except (IndexError, AttributeError):
            self._logger.warning("ラップタイムの表が存在しません")
            nan_data: dict[str, object] = {"レースID": self.race_id}
            lap_df = pd.DataFrame([nan_data])
            lap_df = lap_df.reindex(columns=LAP_TIME_COLUMNS)
            return lap_df

        # 行1がラップタイム（区間タイム）
        section_times = lap_tmp_df.iloc[1]
        source_columns = list(lap_tmp_df.columns)  # 例: ["200m", "400m", ..., "2400m"]

        # ペースを取得
        pace_element = self.soup.find("div", attrs={"class": "RapPace_Title"})
        pace: str | float = pace_element.text[-1] if pace_element is not None else np.nan

        # データ構築
        data: dict[str, object] = {"レースID": self.race_id, "ペース": pace}
        for col in source_columns:
            data[col] = float(pd.to_numeric(section_times[col], errors="coerce"))

        # LAP_TIME_COLUMNSの順序で1行DataFrameを作成（該当しないカラムはNaN）
        lap_df = pd.DataFrame([data])
        lap_df = lap_df.reindex(columns=LAP_TIME_COLUMNS)

        return lap_df

    def _validate_result(self, df: pd.DataFrame) -> None:
        """結果DataFrameのバリデーションを行う

        Args:
            df (pd.DataFrame): RESULT_COLUMNSのカラムを持つDataFrame

        Raises:
            ParseError: バリデーション違反がある場合
        """
        # NaN不可カラムの検証（全行）
        for col in NON_NAN_COLUMNS:
            nan_rows = df[df[col].isna()]
            if not nan_rows.empty:
                umaban_list = nan_rows["馬番"].tolist()
                self._logger.error("'%s'にNaNが含まれています: 馬番%s", col, umaban_list)
                raise ParseError(f"'{col}'にNaNが含まれています: 馬番{umaban_list}")

        # 異常区分のバリデーション
        invalid_statuses = set(df["異常区分"].unique()) - VALID_IJO_KUBUN
        if invalid_statuses:
            self._logger.error("異常区分が不正です: %s", invalid_statuses)
            raise ParseError(f"異常区分が不正です: {invalid_statuses}")

        # 馬体重は出走取消以外はNaN不可
        non_cancel_mask = df["異常区分"] != "取消"
        weight_nan = df.loc[non_cancel_mask, "馬体重"].isna()
        if weight_nan.any():
            umaban_list = df.loc[non_cancel_mask & df["馬体重"].isna(), "馬番"].tolist()
            self._logger.error("'馬体重'にNaNが含まれています: 馬番%s", umaban_list)
            raise ParseError(f"'馬体重'にNaNが含まれています: 馬番{umaban_list}")

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


def _classify_ijo_kubun(chakujun: object) -> str:
    """着順テキストから異常区分を判定する

    Args:
        chakujun (object): 着順の値（数字 or "取消"/"除外"/"中止"/"失格"）

    Returns:
        str: 異常区分（"", "取消", "除外", "中止", "失格"のいずれか）
    """
    text = str(chakujun)
    return text if text in {"取消", "除外", "中止", "失格"} else ""


def _add_id_from_table(soup: BeautifulSoup, df: pd.DataFrame) -> pd.DataFrame:
    """結果テーブルにスクレイピングで取得できるID（馬、騎手、厩舎）を追加する

    Args:
        soup (BeautifulSoup): 結果ページのBeautifulSoupインスタンス
        df (pd.DataFrame): IDを追加するDataFrame

    Returns:
        pd.DataFrame: 馬ID,騎手ID,厩舎IDを追加したDataFrame
    """
    add_df = pd.DataFrame(index=df.index, columns=["馬ID", "騎手ID", "厩舎ID"])

    # 馬IDを追加
    horse_list = soup.find_all("tr", class_="HorseList")
    horse_id_list: list[str] = []
    for horse_row in horse_list:
        horse_name_span = horse_row.find("span", class_="Horse_Name")
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


def _add_gender_age(df: pd.DataFrame) -> pd.DataFrame:
    """結果テーブルに性別・年齢カラムを追加する

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


def _split_corner_passing_order(df: pd.DataFrame) -> pd.DataFrame:
    """コーナー通過順を1〜4コーナーの個別カラムに分割する

    "11-11-10-11" → 1コーナー=11, 2コーナー=11, 3コーナー=10, 4コーナー=11
    "14-15" → 1コーナー=NaN, 2コーナー=NaN, 3コーナー=14, 4コーナー=15

    Args:
        df (pd.DataFrame): コーナー通過順カラムを持つDataFrame

    Returns:
        pd.DataFrame: 1〜4コーナー通過順カラムが追加されたDataFrame（元のコーナー通過順は削除）
    """
    corner_names = ["1コーナー通過順", "2コーナー通過順", "3コーナー通過順", "4コーナー通過順"]

    # 初期化
    for col_name in corner_names:
        df[col_name] = pd.Series(np.nan, index=df.index, dtype=object)

    # NaNでない行だけ処理
    mask = df["コーナー通過順"].notna()
    if mask.any():
        parts_series = df.loc[mask, "コーナー通過順"].astype(str).str.split("-")
        for idx in parts_series.index:
            parts = parts_series[idx]
            # 右から順に4コーナー, 3コーナー, 2コーナー, 1コーナーの順に埋める
            for i, corner_name in enumerate(reversed(corner_names)):
                pos = len(parts) - 1 - i
                if pos >= 0:
                    df.loc[idx, corner_name] = parts[pos]

    # 数値型に変換
    for col_name in corner_names:
        df[col_name] = pd.to_numeric(df[col_name], errors="coerce")

    # 元のコーナー通過順カラムを削除
    df = df.drop(columns=["コーナー通過順"])

    return df


def _parse_haraimodoshi_text(text: str) -> list[int]:
    """払戻テキストから金額リストを取得する

    Args:
        text (str): "210円" or "110円 190円 300円" or "1,310円"

    Returns:
        list[int]: 払戻金額のリスト
    """
    cleaned = text.replace("円", "").replace(",", "")
    parts = cleaned.split()
    return [int(p) for p in parts if p]


def _parse_ninki_text(text: str) -> list[int]:
    """人気テキストから人気順リストを取得する

    Args:
        text (str): "1人気" or "1人気3人気6人気"

    Returns:
        list[int]: 人気順のリスト
    """
    return [int(m) for m in re.findall(r"(\d+)人気", text)]


def _parse_umaban_groups(text: str, combination_size: int) -> list[list[int]]:
    """馬番テキストからグループ化された馬番リストを取得する

    combination_size=1: "13" → [[13]], "13 17 2" → [[13], [17], [2]]
    combination_size=2: "13 17" → [[13, 17]]
    combination_size=3: "2 13 17" → [[2, 13, 17]]

    Args:
        text (str): スペース区切りの馬番テキスト
        combination_size (int): 1組あたりの馬番数

    Returns:
        list[list[int]]: グループ化された馬番リスト
    """
    parts = text.split()
    nums = [int(p) for p in parts]
    groups = []
    for i in range(0, len(nums), combination_size):
        groups.append(nums[i : i + combination_size])
    return groups


def _build_payoff_wide_df(
    race_id: str,
    bet_name: str,
    columns: list[str],
    combination_size: int,
    number_label: str,
    umaban_text: str,
    haraimodoshi_text: str,
    ninki_text: str,
) -> pd.DataFrame:
    """払い戻し情報から横持ちDataFrameを構築する

    Args:
        race_id (str): レースID
        bet_name (str): 券種名
        columns (list[str]): 出力カラム定義
        combination_size (int): 組み合わせサイズ
        number_label (str): 番号カラムのラベル
        umaban_text (str): 馬番テキスト
        haraimodoshi_text (str): 払戻テキスト
        ninki_text (str): 人気テキスト

    Returns:
        pd.DataFrame: 横持ちの払い戻しDataFrame（1行）
    """
    umaban_groups = _parse_umaban_groups(umaban_text, combination_size)
    haraimodoshi_list = _parse_haraimodoshi_text(haraimodoshi_text)
    ninki_list = _parse_ninki_text(ninki_text)

    data: dict[str, object] = {"レースID": race_id}

    zipped = zip(umaban_groups, haraimodoshi_list, ninki_list)
    for i, (uma, hari, nin) in enumerate(zipped):
        n = i + 1
        data[f"{bet_name}払戻金_{n}"] = hari
        if combination_size == 1:
            data[f"{bet_name}{number_label}_{n}"] = uma[0]
        else:
            for j, u in enumerate(uma):
                data[f"{bet_name}{number_label}_{n}_{j + 1}"] = u
        data[f"{bet_name}人気_{n}"] = nin

    payoff_df = pd.DataFrame([data])
    payoff_df = payoff_df.reindex(columns=columns)

    return payoff_df
