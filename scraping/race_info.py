"""レース情報スクレイピングモジュール

netkeibaのレースページからレースの基本情報をスクレイピングする。
"""

import logging
import re
from datetime import date

import pandas as pd
from bs4 import BeautifulSoup, Tag

from scraping.config import GRADE_DICT, RACE_INFO_COLUMNS, WEIGHT_CONDITIONS
from scraping.exceptions import ParseError


def scrape_race_info(
    soup: BeautifulSoup,
    race_id: str,
    logger: logging.Logger | None = None,
) -> pd.DataFrame:
    """BeautifulSoupからレースの基本情報を抽出する

    soupを外部から受け取り、レース基本情報のDataFrameを返す。

    Args:
        soup (BeautifulSoup): 出馬表or結果ページのBeautifulSoupインスタンス
        race_id (str): netkeibaのレースID（12桁文字列）
        logger (logging.Logger | None): ロガーインスタンス

    Returns:
        pd.DataFrame: レース基本情報のDataFrame（1行、RACE_INFO_COLUMNSのカラム）

    Raises:
        ParseError: HTMLの解析に失敗した場合
    """
    # RaceList_DateListからActiveな日付を取得
    _logger = logger or logging.getLogger(__name__)
    race_date, day_of_week = _extract_date_from_datelist(soup, _logger)

    # class:RaceList_Item02のテキストを取得
    race_list_item = soup.find("div", attrs={"class": "RaceList_Item02"})
    if race_list_item is None:
        _logger.error("RaceList_Item02が見つかりませんでした")
        raise ParseError("RaceList_Item02が見つかりませんでした")
    race_raw_text: str = race_list_item.text

    # テキストを整形
    race_filtered_list = _format_race_info_text(race_raw_text, _logger)

    # 地方重賞の場合
    grade_icon = False
    local_grade = ""

    # 必要な要素数をチェック
    if len(race_filtered_list) < 2:
        error_message = "レース情報の要素数が不足しています。HTML構造が変更された可能性があります。"
        _logger.error(error_message)
        raise ParseError(error_message)

    if "発走" not in race_filtered_list[1]:  # 2つ目の要素に"発走"が含まれていない場合
        local_grade = race_filtered_list[1]
        del race_filtered_list[1]  # 2つ目の要素を削除
        grade_icon = True

    # 情報をリストにまとめる
    try:
        race_info_list = _format_race_info_list(race_filtered_list, _logger)
    except ValueError as e:
        _logger.error("レース情報の整形に失敗しました: %s", e)
        raise ParseError(f"レース情報の整形に失敗しました: {e}") from e

    # RACE_INFO_COLUMNSの順でDataFrameを構築
    race_info_dict = _build_race_info_dict(race_id, race_info_list, race_date, day_of_week)
    _validate_race_info_dict(race_info_dict, _logger)
    race_info_df = pd.DataFrame([race_info_dict], columns=RACE_INFO_COLUMNS)

    # 地方重賞の場合グレードを更新
    if grade_icon:
        race_info_df.at[0, "グレード"] = local_grade
    elif race_info_df.at[0, "競争条件"] == "オープン":
        # 中央オープンの場合グレードアイコンを読み取る
        race_info_df = _update_grade_from_icon(soup, race_info_df)

    return race_info_df


def _extract_date_from_datelist(soup: BeautifulSoup, logger: logging.Logger) -> tuple[date, str]:
    """RaceList_DateListのActive要素からレース開催日と曜日を取得する

    RaceList_DateListのdd要素のうちclass="Active"のものを探し、
    その中のaタグのhrefに含まれるkaisai_dateパラメータ（YYYYMMDD形式）から
    date型の日付を生成する。曜日はtitle属性またはspanのテキストから取得する。

    Args:
        soup (BeautifulSoup): ページのBeautifulSoupインスタンス
        logger (logging.Logger): ロガーインスタンス

    Returns:
        date: レース開催日
        str: 曜日（漢字1文字、例: "日"）

    Raises:
        ParseError: RaceList_DateListまたはActive要素、kaisai_dateパラメータが見つからない場合
    """
    datelist = soup.find("dl", id="RaceList_DateList")
    if datelist is None or not isinstance(datelist, Tag):
        logger.error("RaceList_DateListが見つかりませんでした。")
        raise ParseError("RaceList_DateListが見つかりませんでした。")

    active_dd = datelist.find("dd", class_="Active")
    if active_dd is None or not isinstance(active_dd, Tag):
        logger.error("Active日付が見つかりませんでした。")
        raise ParseError("Active日付が見つかりませんでした。")

    # Active要素内のaタグを取得
    anchor = active_dd.find("a")
    if anchor is None or not isinstance(anchor, Tag):
        logger.error("Active日付のaタグが見つかりませんでした。")
        raise ParseError("Active日付のaタグが見つかりませんでした。")

    # kaisai_dateパラメータから日付を取得
    href = anchor.get("href", "")
    if isinstance(href, list):
        href = href[0] if href else ""
    date_match = re.search(r"kaisai_date=(\d{8})", href)
    if date_match is None:
        logger.error("kaisai_dateパラメータが見つかりませんでした。")
        raise ParseError("kaisai_dateパラメータが見つかりませんでした。")

    date_str = date_match.group(1)
    try:
        race_date = date(int(date_str[:4]), int(date_str[4:6]), int(date_str[6:8]))
    except ValueError as e:
        logger.error("不正なkaisai_dateパラメータ値です: %s", date_str)
        raise ParseError(f"不正なkaisai_dateパラメータ値です: {date_str}") from e

    # 曜日をtitle属性またはspanテキストから取得
    day_of_week = ""
    title = anchor.get("title", "")
    if isinstance(title, list):
        title = title[0] if title else ""
    dow_match = re.search(r"\((.)\)", title)
    if dow_match:
        day_of_week = dow_match.group(1)
    else:
        # spanタグのテキストから曜日を取得（例: <span class="Sat">(土)</span>）
        span = anchor.find("span")
        if span is not None:
            span_text = span.get_text(strip=True)
            span_match = re.search(r"\((.)\)", span_text)
            if span_match:
                day_of_week = span_match.group(1)

    return race_date, day_of_week


def _format_race_info_text(race_raw_text: str, logger: logging.Logger) -> list[str]:
    """スクレイピングした生のテキストを整形してリストにする

    RaceList_Item02のテキストを改行やスラッシュで分割し、斤量条件・頭数・賞金までの情報を抽出する。

    Args:
        race_raw_text (str): class:RaceList_Item02のテキスト

    Returns:
        list[str]: 整形したリスト
    """
    # \xa0をスペースに置換
    race_raw_text = race_raw_text.replace("\xa0", " ")

    # 区切り文字(\nと/)でテキストを分割してリストにする
    split_text = re.split(r"[\n/]+", race_raw_text.strip())
    split_text = [item for item in split_text if item]  # 空の要素を除去する

    # 最後の空白より前の要素を追加し、空白以降は競走記号・斤量条件・頭数・賞金を抽出する
    race_filtered_list: list[str] = []
    space_count = 1
    space_num = sum(1 for item in split_text if item.isspace())  # 空白の数を数える
    for i, item in enumerate(split_text):
        if item.isspace():  # 空白のみの場合
            if space_count == space_num:  # 最後のスペースの場合
                # 最後の空白以降から競走記号・斤量条件・頭数・賞金を抽出する
                weight_added = False
                kyoso_kigo_added = False
                for j in range(i + 1, len(split_text)):
                    remaining = split_text[j].strip()
                    if remaining in WEIGHT_CONDITIONS:
                        if not kyoso_kigo_added:
                            race_filtered_list.append("")  # 競走記号なし
                            kyoso_kigo_added = True
                        race_filtered_list.append(remaining)
                        weight_added = True
                    elif remaining.endswith("頭"):
                        race_filtered_list.append(remaining)
                    elif remaining.startswith("本賞金:"):
                        race_filtered_list.append(remaining)
                    elif "(" in remaining or "[" in remaining:
                        race_filtered_list.append(remaining)  # 競走記号
                        kyoso_kigo_added = True
                if not kyoso_kigo_added:
                    logger.warning("競走記号が見つかりませんでした。")
                    race_filtered_list.append("")  # 競走記号なし
                if not weight_added:
                    logger.warning("斤量条件が見つかりませんでした。")
                    race_filtered_list.append("")
                break
            else:
                space_count += 1  # 空白をカウント
        else:  # 空白でない場合
            race_filtered_list.append(item.strip())  # リストに追加

    return race_filtered_list


def _format_race_info_list(race_filtered_list: list[str], logger: logging.Logger) -> list[str]:
    """レース情報を整形してリストにまとめる

    整形したリストから各要素を解析してレース情報のリストを作成する。

    Args:
        race_filtered_list (list[str]): _format_race_info_textの出力リスト

    Returns:
        list[str]: レース情報を整形したリスト
            順序: [レース名, 発走時刻, 芝ダ, 距離, コース, 天候, 馬場,
                   回, 競馬場, 開催日, 競走種別, 競走条件, 競走記号, 斤量条件,
                   頭数, 1着賞金, 2着賞金, 3着賞金, 4着賞金, 5着賞金]

            ※ グレード（G1/G2/G3/JpnI など）は netkeiba のアイコン情報から別途更新され、
               本関数が返すリストには含まれない。

    Raises:
        ValueError: レース情報のフォーマットが不正な場合
    """
    race_info_list: list[str] = []
    course = ""
    for i, item in enumerate(race_filtered_list):
        if i == 3:
            if "天候:" in item:
                race_info_list.append(item.split(":")[1])  # 天候:を削除して追加
            elif "馬場:" in item:  # レース前日で天候と馬場が不明な場合（地方）
                race_info_list.append("")  # 空の要素を追加（天候分）
                race_info_list.append("")  # 空の要素を追加（馬場分）
            else:  # 出走確定前で天候と馬場が不明な場合（中央）
                race_info_list.append("")  # 空の要素を追加（天候分）
                race_info_list.append("")  # 空の要素を追加（馬場分）
                # 「1回」等の接尾辞を除去してから追加
                value = (
                    item.replace("発走", "").replace("回", "").replace("日目", "").replace("頭", "")
                )
                race_info_list.append(value)
        elif "馬場:" in item:
            race_info_list.append(item.split(":")[1])  # 馬場:を削除して追加
        elif i != 0 and "m" in item:  # レース名にmが含まれる場合を回避
            # 芝2000m(左 A) などを表す正規表現パターンを定義
            pattern = r"([^\d]+)(\d+)\s*m\s*(?:\(([^)]+)\))?"
            # テキストからマッチする部分を抽出
            matches = re.match(pattern, item)
            if matches:
                turf_dirt = matches.group(1).strip()  # 芝orダor障
                distance = matches.group(2).strip()  # 距離
                course = matches.group(3).strip() if matches.group(3) else ""  # 左右，内外，コース
            else:
                logger.error("レース情報のフォーマットが不正です")
                raise ValueError("レース情報のフォーマットが不正です")
            # リストに追加
            race_info_list.append(turf_dirt)
            race_info_list.append(distance)
            race_info_list.append(course)
        elif i != 0 and ("回" in item or "日目" in item or "発走" in item or "頭" in item):
            # 不要な接尾辞を除去
            value = item.replace("発走", "").replace("回", "").replace("日目", "").replace("頭", "")
            race_info_list.append(value)
        elif item.startswith("本賞金:"):
            # 本賞金: "本賞金:50000,20000,12500,7500,5000万円" → 5つの要素に分解
            prize_str = item.replace("本賞金:", "").replace("万円", "")
            parts = prize_str.split(",")
            # 1〜5着の賞金を追加（不足分は"0"）
            for j in range(5):
                if j < len(parts) and parts[j].strip():
                    race_info_list.append(parts[j].strip())
                else:
                    race_info_list.append("0")
        elif i == len(race_filtered_list) - 1 and " " in item:  # 最後の要素でスペースがあったら
            race_info_list.append(item.split(" ")[0])  # スペースで区切ってグレードとして追加
            race_info_list.append(item.split(" ")[1])
        else:
            # その他の要素はそのまま追加
            race_info_list.append(item)

    # 障害で芝ダート両方の場合馬場が2種類表記されるので1つにまとめる
    if course == "芝 ダート":
        race_info_list[6] = " ".join([race_info_list[6], race_info_list[7]])  # 馬場をまとめる
        del race_info_list[7]

    # 地方で最後の要素グレード表記がない場合
    if len(race_info_list) < 13:
        race_info_list.append("")  # グレード要素なしを追加

    # 頭数・賞金が取得できなかった場合のフォールバック（基本13 + 競走記号1 + 頭数1 + 賞金5 = 20要素）
    while len(race_info_list) < 20:
        race_info_list.append("")

    return race_info_list


def _build_race_info_dict(
    race_id: str, race_info_list: list[str], race_date: date, day_of_week: str
) -> dict[str, str | int | date | None]:
    """_format_race_info_listの出力をRACE_INFO_COLUMNSに対応するdictに変換する

    _format_race_info_listの出力順序（20要素）:
        [レース名(0), 発走時刻(1), 芝ダ(2), 距離(3), コース生値(4),
         天候(5), 馬場(6), 回(7), 競馬場(8), 開催日(9),
         競走種別(10), 競走条件(11), 競走記号(12), 斤量条件(13), 頭数(14),
         1着賞金(15), 2着賞金(16), 3着賞金(17), 4着賞金(18), 5着賞金(19)]

    グレードは netkeiba のアイコン情報から別途更新される（辞書の"グレード"は空文字列で初期化）。
    コース生値（例: "左 C", "右 外 B", "直線 A"）を「左右」「コース」「内外」に分割して辞書に格納する。
    距離・回・開催日は_format_race_info_listで整形済みの数値文字列をintに変換する。

    Args:
        race_id (str): レースID
        race_info_list (list[str]): _format_race_info_listの出力
        race_date (date): レース開催日（date型）
        day_of_week (str): 曜日（漢字1文字、例: "日"）

    Returns:
        dict[str, str | int | date | None]: RACE_INFO_COLUMNSに対応する辞書
    """

    def _safe_get(lst: list[str], idx: int) -> str:
        """リストから安全に値を取得する"""
        return lst[idx] if idx < len(lst) else ""

    def _to_int(value: str) -> int:
        """数値文字列をintに変換する。空文字の場合は0"""
        return int(value) if value else 0

    course_raw = _safe_get(race_info_list, 4)

    return {
        "レースID": race_id,
        "日付": race_date,
        "曜日": day_of_week,
        "レース名": _safe_get(race_info_list, 0),
        "発走時刻": _safe_get(race_info_list, 1),
        "天候": _safe_get(race_info_list, 5) or None,
        "馬場": _safe_get(race_info_list, 6) or None,
        "芝ダ": _safe_get(race_info_list, 2),
        "距離": _to_int(_safe_get(race_info_list, 3)),
        "左右": _judge_direction(course_raw),
        "コース": _judge_abcd(course_raw),
        "内外": _judge_course_inout(course_raw),
        "競馬場": _safe_get(race_info_list, 8),
        "回": _to_int(_safe_get(race_info_list, 7)),
        "開催日": _to_int(_safe_get(race_info_list, 9)),
        "競争種別": _safe_get(race_info_list, 10),
        "競争条件": _safe_get(race_info_list, 11),
        "グレード": "",
        "競走記号": _safe_get(race_info_list, 12),
        "重量種別": _safe_get(race_info_list, 13),
        "頭数": _to_int(_safe_get(race_info_list, 14)),
        "1着賞金": _to_int(_safe_get(race_info_list, 15)),
        "2着賞金": _to_int(_safe_get(race_info_list, 16)),
        "3着賞金": _to_int(_safe_get(race_info_list, 17)),
        "4着賞金": _to_int(_safe_get(race_info_list, 18)),
        "5着賞金": _to_int(_safe_get(race_info_list, 19)),
    }


def _validate_race_info_dict(
    race_info: dict[str, str | int | date | None],
    logger: logging.Logger,
) -> None:
    """レース情報辞書の値をスキーマに基づいて検証する

    各カラムの値が期待するフォーマット・範囲に収まっているかを確認し、
    不正な値があればParseErrorを送出する。

    Args:
        race_info (dict[str, str | int | date | None]): レース情報辞書

    Raises:
        ParseError: 値がスキーマに適合しない場合
    """
    errors: list[str] = []

    # レースID: 12桁
    race_id = race_info.get("レースID", "")
    if not isinstance(race_id, str) or not re.fullmatch(r"\d{12}", race_id):
        errors.append(f"レースIDが12桁の数字ではありません: {race_id}")

    # 曜日: 月火水木金土日のいずれか
    day_of_week = race_info.get("曜日", "")
    if day_of_week not in ("月", "火", "水", "木", "金", "土", "日"):
        errors.append(f"曜日が不正です: {day_of_week}")

    # 発走時刻: HH:MM形式
    start_time = race_info.get("発走時刻", "")
    if not isinstance(start_time, str) or not re.fullmatch(r"\d{1,2}:\d{2}", start_time):
        errors.append(f"発走時刻がHH:MM形式ではありません: {start_time}")

    # 天候: 晴、曇、雨、小雨、雪、小雪、None（出走確定前）
    weather = race_info.get("天候")
    if weather is not None and weather not in ("晴", "曇", "雨", "小雨", "雪", "小雪"):
        errors.append(f"天候が不正です: {weather}")

    # 馬場: 良、稍重、稍、重、不、不良、None（出走確定前）
    track_condition = race_info.get("馬場")
    if track_condition is not None and track_condition not in (
        "良",
        "稍重",
        "稍",
        "重",
        "不",
        "不良",
    ):
        errors.append(f"馬場が不正です: {track_condition}")

    # 芝ダ: 芝、ダ、障を含む、もしくは空文字列
    track_type = race_info.get("芝ダ", "")
    if isinstance(track_type, str) and track_type != "":
        if "芝" not in track_type and "ダ" not in track_type and "障" not in track_type:
            errors.append(f"芝ダが不正です: {track_type}")

    # 距離、回、開催日、頭数: 正であること
    for key in ("距離", "回", "開催日", "頭数"):
        value = race_info.get(key, 0)
        if not isinstance(value, int) or value <= 0:
            errors.append(f"{key}が正の整数ではありません: {value}")

    # 賞金: 0以上であること
    for key in ("1着賞金", "2着賞金", "3着賞金", "4着賞金", "5着賞金"):
        value = race_info.get(key, 0)
        if not isinstance(value, int) or value < 0:
            errors.append(f"{key}が0以上の整数ではありません: {value}")

    # 重量種別: 定量、別定、ハンデ、馬齢、空文字列
    weight_type = race_info.get("重量種別", "")
    if weight_type not in ("定量", "別定", "ハンデ", "馬齢", ""):
        errors.append(f"重量種別が不正です: {weight_type}")

    if errors:
        logger.error("レース情報の検証に失敗しました:\n%s", "\n".join(errors))
        raise ParseError("レース情報の検証に失敗しました:\n" + "\n".join(errors))


def _update_grade_from_icon(soup: BeautifulSoup, race_info_df: pd.DataFrame) -> pd.DataFrame:
    """グレードアイコンからグレード情報を更新する

    中央オープンの場合、RaceNameのspan要素からグレード情報を読み取る。

    Args:
        soup (BeautifulSoup): ページのBeautifulSoupインスタンス
        race_info_df (pd.DataFrame): レース情報のDataFrame

    Returns:
        pd.DataFrame: グレードを更新したDataFrame
    """
    # クラスRaceNameを取得（2024/04/21以降h1に変更）
    class_race_name = soup.find("h1", class_="RaceName")
    if class_race_name is None or not isinstance(class_race_name, Tag):
        return race_info_df

    # RaceNameの下にある<span>に挟まれたclass名を取得
    spans_with_class = class_race_name.find_all("span", class_=True)
    if not spans_with_class:
        return race_info_df

    icon_grade_type = [el["class"] for el in spans_with_class]
    grade_num = re.findall(r"\d+", icon_grade_type[0][1])[0]  # クラス名に含まれる数字を取得
    race_info_df.at[0, "グレード"] = GRADE_DICT[grade_num]  # グレードを更新

    return race_info_df


def _judge_direction(course: str) -> str:
    """コースから左右（方向）を判定する

    Args:
        course (str): コースの生値（例: "左 C", "右 外 B", "直線 A"）

    Returns:
        str: "左","右","直"のいずれか。いずれでもない場合は空文字列
    """
    if "左" in course:
        return "左"
    elif "右" in course:
        return "右"
    elif "直" in course:
        return "直"
    else:
        return ""


def _judge_abcd(course: str) -> str:
    """コースからABCDコースを判定する

    Args:
        course (str): コースの生値（例: "左 C", "右 外 B"）

    Returns:
        str: "A","B","C","D"のいずれか。いずれでもない場合は空文字列
    """
    if "A" in course:
        return "A"
    elif "B" in course:
        return "B"
    elif "C" in course:
        return "C"
    elif "D" in course:
        return "D"
    else:
        return ""


def _judge_course_inout(course: str) -> str:
    """コースから内外を判定する

    Args:
        course (str): コースの生値（例: "右 外 B"）

    Returns:
        str: "内","外","外-内"のいずれか。いずれでもない場合は空文字列
    """
    if "内" in course and "外" in course:  # 阪神芝3200mのみ外回りと内回り両方使用
        return "外-内"
    elif "内" in course:
        return "内"
    elif "外" in course:
        return "外"
    else:
        return ""
