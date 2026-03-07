"""オッズスクレイピングモジュール

netkeibaおよびJRAからオッズを取得する関数を提供する。
"""

from typing import Any

import numpy as np
import pandas as pd
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

from scraping.config import ODDS_COLUMNS, YOSO_ODDS_COLUMNS, ScrapingConfig
from scraping.exceptions import NetworkError, ParseError
from scraping.utils import build_odds_api_url


def scrape_odds_from_netkeiba(
    race_id: str,
    config: ScrapingConfig | None = None,
) -> pd.DataFrame:
    """netkeibaからオッズを取得する

    netkeibaのオッズAPIからJSON形式でオッズを取得し、DataFrameとして返す。
    馬券発売前は空のDataFrame（カラムのみ）を返す。

    Args:
        race_id (str): レースID
        config (ScrapingConfig | None): 設定オブジェクト

    Returns:
        pd.DataFrame: オッズデータ（ODDS_COLUMNSのカラム）
            馬番順にソートされている
            馬券発売前は0行のDataFrame

    Raises:
        NetworkError: HTTPリクエストに失敗した場合
        ParseError: JSONの解析に失敗した場合
    """
    cfg = config or ScrapingConfig()

    # APIからオッズを取得
    odds_data = _fetch_odds_api(race_id, cfg)

    # JSONをDataFrameに変換
    odds_df = _parse_odds_response(odds_data)

    return odds_df


def scrape_yoso_odds_from_netkeiba(
    race_id: str,
    config: ScrapingConfig | None = None,
) -> pd.DataFrame:
    """netkeibaから予想オッズを取得する（馬券発売前用）

    netkeibaの出馬表ページからJavaScriptで生成される予想オッズを取得する。
    馬名と予想単勝オッズを取得する。

    Args:
        race_id (str): レースID
        config (ScrapingConfig | None): 設定オブジェクト

    Returns:
        pd.DataFrame: 予想オッズデータ（YOSO_ODDS_COLUMNSのカラム）
            馬名順（出馬表の登録順）

    Raises:
        NetworkError: ページの取得に失敗した場合
        ParseError: ページ解析に失敗した場合
    """
    cfg = config or ScrapingConfig()

    # 出馬表ページのURLを構築
    url = f"{cfg.netkeiba_race_url}/race/shutuba.html?race_id={race_id}"

    # ChromeDriverを起動
    options = _set_chrome_options()
    service = Service(cfg.chrome_driver_path) if cfg.chrome_driver_path else Service()
    driver = None

    try:
        try:
            driver = webdriver.Chrome(service=service, options=options)
            driver.get(url)
        except Exception as exc:
            raise NetworkError(f"予想オッズページの取得に失敗しました: {exc}") from exc

        # HorseListから馬名とオッズを取得
        horse_list = driver.find_elements(By.CLASS_NAME, "HorseList")
        if not horse_list:
            return pd.DataFrame(columns=YOSO_ODDS_COLUMNS)

        rows = []
        for row in horse_list:
            tds = row.find_elements(By.TAG_NAME, "td")
            if len(tds) > 10:
                # 馬番を取得（枠順確定前は空の場合がある）
                umaban_text = tds[1].text.strip() if len(tds) > 1 else ""
                try:
                    umaban = int(umaban_text) if umaban_text else np.nan
                except ValueError:
                    umaban = np.nan

                # 馬名を取得
                horse_name_elem = row.find_element(By.CLASS_NAME, "HorseName")
                horse_name = horse_name_elem.text.strip() if horse_name_elem else ""

                # オッズを取得
                odds_text = tds[9].text.strip()

                # オッズをパース
                try:
                    odds_val = float(odds_text) if odds_text else np.nan
                except ValueError:
                    odds_val = np.nan

                if horse_name:
                    rows.append(
                        {
                            "馬番": umaban,
                            "馬名": horse_name,
                            "予想単勝オッズ": odds_val,
                        }
                    )

        if not rows:
            return pd.DataFrame(columns=YOSO_ODDS_COLUMNS)

        df = pd.DataFrame(rows, columns=YOSO_ODDS_COLUMNS)
        return df

    except (NetworkError, ParseError):
        raise
    except Exception as exc:
        raise ParseError(f"予想オッズの解析に失敗しました: {exc}") from exc
    finally:
        if driver is not None:
            driver.quit()


def _fetch_odds_api(race_id: str, config: ScrapingConfig) -> dict[str, Any]:
    """netkeibaのオッズAPIからJSONを取得する

    Args:
        race_id (str): レースID
        config (ScrapingConfig): 設定オブジェクト

    Returns:
        dict[str, Any]: APIレスポンスのJSON

    Raises:
        NetworkError: HTTPリクエストに失敗した場合
        ParseError: JSONの解析に失敗した場合
    """
    url = build_odds_api_url(race_id, config)

    try:
        response = requests.get(url, headers=config.headers, timeout=config.request_timeout)
        response.raise_for_status()
    except requests.RequestException as e:
        raise NetworkError(f"オッズAPIの取得に失敗しました: {e}") from e

    try:
        return response.json()
    except ValueError as e:
        raise ParseError(f"オッズAPIレスポンスのJSON解析に失敗しました: {e}") from e


def _parse_odds_response(data: dict[str, Any]) -> pd.DataFrame:
    """APIレスポンスをDataFrameに変換する

    Args:
        data (dict[str, Any]): APIレスポンスのJSON

    Returns:
        pd.DataFrame: オッズデータ（ODDS_COLUMNSのカラム）

    Raises:
        ParseError: JSONの解析に失敗した場合
    """
    # APIにオッズデータがない場合は空のDataFrameを返す
    # statusが"result"（確定オッズ）または"middle"（予想オッズ）でもdataがあればパース
    raw_data = data.get("data", "")
    if not raw_data or not isinstance(raw_data, dict):
        return pd.DataFrame(columns=ODDS_COLUMNS)

    try:
        odds_json = raw_data.get("odds", {})
        if not odds_json:
            return pd.DataFrame(columns=ODDS_COLUMNS)

        # 単勝オッズ（type=1）
        tan_odds = odds_json.get("1", {})
        # 複勝オッズ（type=2）
        fuku_odds = odds_json.get("2", {})

        # 全馬番を取得
        all_umaban = set(tan_odds.keys()) | set(fuku_odds.keys())
        if not all_umaban:
            return pd.DataFrame(columns=ODDS_COLUMNS)

        rows = []
        for umaban in sorted(all_umaban, key=int):
            umaban_int = int(umaban)

            # 単勝オッズ [オッズ, ?, 人気]
            tan_data = tan_odds.get(umaban, [None, None, None])
            tan_odds_val = _parse_odds_value(tan_data[0])
            tan_ninki = _parse_ninki_value(tan_data[2] if len(tan_data) > 2 else None)

            # 複勝オッズ [最小オッズ, 最大オッズ, 人気]
            fuku_data = fuku_odds.get(umaban, [None, None, None])
            fuku_min = _parse_odds_value(fuku_data[0])
            fuku_max = _parse_odds_value(fuku_data[1] if len(fuku_data) > 1 else None)
            fuku_ninki = _parse_ninki_value(fuku_data[2] if len(fuku_data) > 2 else None)

            rows.append(
                {
                    "馬番": umaban_int,
                    "単勝オッズ": tan_odds_val,
                    "単勝人気": tan_ninki,
                    "複勝最小オッズ": fuku_min,
                    "複勝最大オッズ": fuku_max,
                    "複勝人気": fuku_ninki,
                }
            )

        df = pd.DataFrame(rows, columns=ODDS_COLUMNS)
        return df

    except (KeyError, TypeError, ValueError) as e:
        raise ParseError(f"オッズJSONの解析に失敗しました: {e}") from e


def _parse_odds_value(value: str | None) -> float | None:
    """オッズ値を数値に変換する

    出走取消・除外の場合は負の値が設定されるためNaNを返す。

    Args:
        value (str | None): オッズ文字列

    Returns:
        float | None: オッズ値（NaNの場合はnp.nan）
    """
    if value is None or value == "":
        return np.nan
    try:
        odds = float(value)
        # 負の値は出走取消・除外
        if odds < 0:
            return np.nan
        return odds
    except ValueError:
        return np.nan


def _parse_ninki_value(value: str | None) -> float:
    """人気を数値に変換する

    Args:
        value (str | None): 人気文字列

    Returns:
        float: 人気（NaNの場合はnp.nan）
    """
    if value is None or value == "":
        return np.nan
    try:
        ninki = int(value)
        # 9999は出走取消・除外のマーカー
        if ninki >= 9999:
            return np.nan
        return ninki
    except ValueError:
        return np.nan


def _set_chrome_options() -> Options:
    """ChromeDriverの初期設定を行う

    Returns:
        Options: Chromeの起動オプション
    """
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return options
