"""レース情報スクレイピングモジュール

netkeibaのレースページからレースの基本情報をスクレイピングする。
"""

import logging
import re
from datetime import date

import pandas as pd
from bs4 import BeautifulSoup, NavigableString, Tag
from keiba_domain import parse_inout

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

    race_list_item = soup.find("div", attrs={"class": "RaceList_Item02"})
    if race_list_item is None or not isinstance(race_list_item, Tag):
        _logger.error("RaceList_Item02が見つかりませんでした")
        raise ParseError("RaceList_Item02が見つかりませんでした")

    race_name = _parse_race_name(race_list_item, _logger)
    race_data01 = _parse_race_data01(_find_div(race_list_item, "RaceData01", _logger), _logger)
    race_data02 = _parse_race_data02(_find_div(race_list_item, "RaceData02", _logger), _logger)

    # RACE_INFO_COLUMNSの順でDataFrameを構築
    race_info_dict = _build_race_info_dict(
        race_id, race_name, race_data01, race_data02, race_date, day_of_week
    )
    _validate_race_info_dict(race_info_dict, _logger)
    race_info_df = pd.DataFrame([race_info_dict], columns=RACE_INFO_COLUMNS)

    # オープンの場合グレードアイコンを読み取る
    if race_info_df.at[0, "競走条件"] == "オープン":
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


def _find_div(parent: Tag, class_name: str, logger: logging.Logger) -> Tag:
    """指定したclassのdiv要素を取得する

    Args:
        parent (Tag): 検索対象の親要素
        class_name (str): divのclass名
        logger (logging.Logger): ロガーインスタンス

    Returns:
        Tag: 見つかったdiv要素

    Raises:
        ParseError: div要素が見つからない場合
    """
    div = parent.find("div", class_=class_name)
    if div is None or not isinstance(div, Tag):
        logger.error("%sが見つかりませんでした", class_name)
        raise ParseError(f"{class_name}が見つかりませんでした")
    return div


def _parse_race_name(race_list_item: Tag, logger: logging.Logger) -> str:
    """RaceList_Item02からレース名を取得する

    Args:
        race_list_item (Tag): class:RaceList_Item02の要素
        logger (logging.Logger): ロガーインスタンス

    Returns:
        str: レース名

    Raises:
        ParseError: レース名が見つからない場合
    """
    race_name_tag = race_list_item.find("h1", class_="RaceName")
    if race_name_tag is None or not isinstance(race_name_tag, Tag):
        logger.error("RaceNameが見つかりませんでした")
        raise ParseError("RaceNameが見つかりませんでした")
    return race_name_tag.get_text(strip=True)


def _parse_race_data01(race_data01: Tag, logger: logging.Logger) -> dict[str, str]:
    """RaceData01から発走時刻・芝ダ・距離・コース・天候・馬場を取得する

    天候はアイコンのtitle属性、馬場はItem03（芝）・Item04（ダート）の要素から取得する。
    出走確定前は天候・馬場の要素がないため空文字列になる。

    Args:
        race_data01 (Tag): class:RaceData01の要素
        logger (logging.Logger): ロガーインスタンス

    Returns:
        dict[str, str]: キーは発走時刻・芝ダ・距離・コース・天候・馬場。
            障害の場合、芝ダは"障"、コースは"芝"や"芝 ダート"になる。

    Raises:
        ParseError: 距離・コースが取得できない場合
    """
    # 先頭のテキストは「15:40発走 /」
    start_time = str(race_data01.contents[0]).split("/")[0].strip().removesuffix("発走")

    # 「芝2400m」のように芝ダと距離がclassなしのspanに入っている
    distance_span = race_data01.find("span", class_=False)
    if distance_span is None or not isinstance(distance_span, Tag):
        logger.error("距離が見つかりませんでした")
        raise ParseError("距離が見つかりませんでした")
    distance_text = distance_span.get_text(strip=True)
    distance_match = re.fullmatch(r"(\D+)(\d+)m", distance_text)
    if distance_match is None:
        logger.error("距離の表記が不正です: %s", distance_text)
        raise ParseError(f"距離の表記が不正です: {distance_text}")

    # 距離のspanの直後から次の「/」までがコース（例: "左 C", "右 外 B", "芝 ダート"）
    course_text = distance_span.next_sibling
    if not isinstance(course_text, NavigableString):
        logger.error("コースが見つかりませんでした")
        raise ParseError("コースが見つかりませんでした")
    course = " ".join(course_text.split("/")[0].split())

    # アイコンのclassは"Icon_Weather Weather01"と"Icon_Weather02 Icon_W01"の2通りある
    weather_icon = race_data01.find("span", class_=re.compile(r"^Icon_Weather"))
    weather = str(weather_icon.get("title", "")) if isinstance(weather_icon, Tag) else ""

    # 障害の芝ダートはItem03とItem04の両方が表示される
    baba_spans = race_data01.find_all("span", class_=["Item03", "Item04"])
    baba = " ".join(span.get_text(strip=True) for span in baba_spans)

    return {
        "発走時刻": start_time,
        "芝ダ": distance_match.group(1),
        "距離": distance_match.group(2),
        "コース": course,
        "天候": weather,
        "馬場": baba,
    }


def _parse_race_data02(race_data02: Tag, logger: logging.Logger) -> dict[str, str]:
    """RaceData02から開催・競走条件・斤量条件・頭数・賞金を取得する

    spanは回、競馬場、開催日、競走種別、競走条件、競走記号、斤量条件、頭数、本賞金の順に並ぶ。

    Args:
        race_data02 (Tag): class:RaceData02の要素
        logger (logging.Logger): ロガーインスタンス

    Returns:
        dict[str, str]: キーは回・競馬場・開催日・競走種別・競走条件・競走記号・重量種別・頭数・
            1着賞金〜5着賞金。回・開催日・頭数・賞金は数字のみの文字列。

    Raises:
        ParseError: いずれかの項目が取得できない場合
    """
    items = [span.get_text(strip=True) for span in race_data02.find_all("span")]
    if len(items) < 5:
        logger.error("RaceData02の要素数が不足しています: %s", items)
        raise ParseError(f"RaceData02の要素数が不足しています: {items}")
    kai, keibajo, kaisai_day, race_kind, race_condition = items[:5]
    rest = items[5:]

    def _find_one(label: str, candidates: list[str]) -> str:
        """候補が1つだけであることを確認して返す

        Args:
            label (str): エラーメッセージに使う項目名
            candidates (list[str]): 候補のリスト

        Returns:
            str: 唯一の候補

        Raises:
            ParseError: 候補が1つでない場合
        """
        if len(candidates) != 1:
            logger.error("%sを特定できませんでした: %s", label, rest)
            raise ParseError(f"{label}を特定できませんでした: {rest}")
        return candidates[0]

    race_symbol = _find_one("競走記号", [i for i in rest if "(" in i or "[" in i])
    weight_type = _find_one("斤量条件", [i for i in rest if i in WEIGHT_CONDITIONS])
    head_count = _find_one("頭数", [i for i in rest if re.fullmatch(r"\d+頭", i)])
    prize_text = _find_one("本賞金", [i for i in rest if i.startswith("本賞金:")])

    # "本賞金:30000,12000,7500,4500,3000万円" → 1〜5着の賞金
    prizes = prize_text.removeprefix("本賞金:").removesuffix("万円").split(",")
    if len(prizes) != 5:
        logger.error("本賞金の表記が不正です: %s", prize_text)
        raise ParseError(f"本賞金の表記が不正です: {prize_text}")

    return {
        "回": kai.removesuffix("回"),
        "競馬場": keibajo,
        "開催日": kaisai_day.removesuffix("日目"),
        "競走種別": race_kind,
        "競走条件": race_condition,
        "競走記号": race_symbol,
        "重量種別": weight_type,
        "頭数": head_count.removesuffix("頭"),
        **{f"{rank}着賞金": prize for rank, prize in enumerate(prizes, start=1)},
    }


def _build_race_info_dict(
    race_id: str,
    race_name: str,
    race_data01: dict[str, str],
    race_data02: dict[str, str],
    race_date: date,
    day_of_week: str,
) -> dict[str, str | int | date | None]:
    """取得した値をRACE_INFO_COLUMNSに対応するdictに変換する

    グレードは netkeiba のアイコン情報から別途更新される（辞書の"グレード"は空文字列で初期化）。
    コース生値（例: "左 C", "右 外 B", "直線 A"）を「左右」「コース」「内外」に分割して
    辞書に格納する。

    障害レースの場合:
        芝ダには"障"が入り、コース生値には芝/ダの情報（例: "芝"）が入る。
        "レース種別"を"障害"に設定し、"芝ダ"にはコース生値から抽出した"芝"または"ダ"を格納する。
        左右・コース・内外は空文字列になる。

    Args:
        race_id (str): レースID
        race_name (str): レース名
        race_data01 (dict[str, str]): _parse_race_data01の出力
        race_data02 (dict[str, str]): _parse_race_data02の出力
        race_date (date): レース開催日（date型）
        day_of_week (str): 曜日（漢字1文字、例: "日"）

    Returns:
        dict[str, str | int | date | None]: RACE_INFO_COLUMNSに対応する辞書
    """
    turf_dirt_raw = race_data01["芝ダ"]
    course_raw = race_data01["コース"]

    # 障害レースの判定: 芝ダの生値に「障」が含まれる場合は障害レース
    if "障" in turf_dirt_raw:
        race_type = "障害"
        # 障害レースの場合、実際の芝/ダはcourse_rawに格納されている（例: "芝", "芝 ダート"）
        if "芝" in course_raw:
            turf_dirt = "芝"
        elif "ダ" in course_raw:
            turf_dirt = "ダ"
        else:
            turf_dirt = turf_dirt_raw
        # 障害レースにはコース方向情報がないため空にする
        course_for_direction = ""
    else:
        race_type = "平地"
        turf_dirt = turf_dirt_raw
        course_for_direction = course_raw

    return {
        "レースID": race_id,
        "日付": race_date,
        "曜日": day_of_week,
        "レース名": race_name,
        "発走時刻": race_data01["発走時刻"],
        "天候": race_data01["天候"] or None,
        "馬場": race_data01["馬場"] or None,
        "レース種別": race_type,
        "芝ダ": turf_dirt,
        "距離": int(race_data01["距離"]),
        "左右": _judge_direction(course_for_direction),
        "コース": _judge_abcd(course_for_direction),
        "内外": _judge_course_inout(course_for_direction),
        "競馬場": race_data02["競馬場"],
        "回": int(race_data02["回"]),
        "開催日": int(race_data02["開催日"]),
        "競走種別": race_data02["競走種別"],
        "競走条件": race_data02["競走条件"],
        "グレード": "",
        "競走記号": race_data02["競走記号"],
        "重量種別": race_data02["重量種別"],
        "頭数": int(race_data02["頭数"]),
        **{f"{rank}着賞金": int(race_data02[f"{rank}着賞金"]) for rank in range(1, 6)},
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
        logger (logging.Logger): ロガーインスタンス

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

    # レース種別: 平地、障害のいずれか
    race_type = race_info.get("レース種別", "")
    if race_type not in ("平地", "障害"):
        errors.append(f"レース種別が不正です: {race_type}")

    # 芝ダ: 芝、ダのいずれか、もしくは空文字列
    track_type = race_info.get("芝ダ", "")
    if isinstance(track_type, str) and track_type != "":
        if track_type not in ("芝", "ダ"):
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
        str: "内","外","内-外","外-内"のいずれか。いずれでもない場合は空文字列
    """
    inout = parse_inout(course)
    return str(inout) if inout is not None else ""
