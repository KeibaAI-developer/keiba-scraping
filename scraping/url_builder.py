"""URL構築モジュール

netkeibaおよびJRAのURL構築関数を集約する。
"""

from scraping.config import ScrapingConfig


def build_race_list_url(year: int, page_num: int, config: ScrapingConfig | None = None) -> str:
    """netkeibaのレース一覧ページのURLを作成する

    Args:
        year (int): 年
        page_num (int): ページ番号
        config (ScrapingConfig | None): 設定オブジェクト

    Returns:
        str: URL
    """
    cfg = config or ScrapingConfig()
    jyo_query = "&".join(f"jyo%5B%5D={jyo_id:02}" for jyo_id in range(1, 11))  # 中央10場
    return (
        f"{cfg.netkeiba_base_url}/race/list.html"
        f"?word=&yf={year}&mf=1&yt={year}&mt=12&{jyo_query}"
        f"&sort=date-desc&limit=100&page={page_num}"
    )


def build_today_race_list_url(
    year: int, month: int, day: int, config: ScrapingConfig | None = None
) -> str:
    """netkeibaの日別レース一覧ページのURLを作成する

    Args:
        year (int): 年
        month (int): 月
        day (int): 日
        config (ScrapingConfig | None): 設定オブジェクト

    Returns:
        str: URL
    """
    cfg = config or ScrapingConfig()
    return f"{cfg.netkeiba_race_url}/top/race_list.html" f"?kaisai_date={year}{month:02}{day:02}"


def build_result_url(race_id: str, config: ScrapingConfig | None = None) -> str:
    """netkeibaのレース結果ページのURLを作成する

    Args:
        race_id (str): レースID
        config (ScrapingConfig | None): 設定オブジェクト

    Returns:
        str: URL
    """
    cfg = config or ScrapingConfig()
    return f"{cfg.netkeiba_race_url}/race/result.html?race_id={race_id}"


def build_entry_url(race_id: str, config: ScrapingConfig | None = None) -> str:
    """netkeibaの出馬表ページのURLを作成する

    Args:
        race_id (str): レースID
        config (ScrapingConfig | None): 設定オブジェクト

    Returns:
        str: URL
    """
    cfg = config or ScrapingConfig()
    return f"{cfg.netkeiba_race_url}/race/shutuba.html?race_id={race_id}"


def build_horse_info_url(horse_id: str, config: ScrapingConfig | None = None) -> str:
    """netkeibaの馬情報ページのURLを作成する

    Args:
        horse_id (str): 馬ID
        config (ScrapingConfig | None): 設定オブジェクト

    Returns:
        str: URL
    """
    cfg = config or ScrapingConfig()
    return f"{cfg.netkeiba_base_url}/horse/{horse_id}"


def build_horse_list_url(year: int, page_num: int, config: ScrapingConfig | None = None) -> str:
    """netkeibaの競走馬一覧ページのURLを作成する

    Args:
        year (int): 年
        page_num (int): ページ番号
        config (ScrapingConfig | None): 設定オブジェクト

    Returns:
        str: URL
    """
    cfg = config or ScrapingConfig()
    return f"{cfg.netkeiba_base_url}/horse/list.html?year={year}&limit=100&page={page_num}"


def build_odds_api_url(race_id: str, config: ScrapingConfig | None = None) -> str:
    """netkeibaのオッズAPIのURLを作成する

    Args:
        race_id (str): レースID
        config (ScrapingConfig | None): 設定オブジェクト

    Returns:
        str: URL
    """
    cfg = config or ScrapingConfig()
    return f"{cfg.netkeiba_race_url}/api/api_get_jra_odds.html?race_id={race_id}&type=1"


def build_jra_graded_race_url(year: int, config: ScrapingConfig | None = None) -> str:
    """JRAの重賞レース一覧ページのURLを作成する

    Args:
        year (int): 年
        config (ScrapingConfig | None): 設定オブジェクト

    Returns:
        str: URL
    """
    cfg = config or ScrapingConfig()
    return f"{cfg.jra_url}/datafile/seiseki/replay/{year}/jyusyo.html"
