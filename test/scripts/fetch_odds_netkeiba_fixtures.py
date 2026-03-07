"""netkeibaオッズページのHTMLおよびAPIレスポンスのフィクスチャ取得スクリプト

netkeibaのオッズページのHTMLとオッズAPIのJSONレスポンスを取得し、
test/fixtures/に保存する。

使用方法:
    python test/scripts/fetch_odds_netkeiba_fixtures.py
"""

import json
import os
import time
from typing import Any

import requests

# フィクスチャ保存先ディレクトリ
FIXTURES_DIR_HTML = os.path.join(os.path.dirname(__file__), "..", "fixtures", "html")
FIXTURES_DIR_JSON = os.path.join(os.path.dirname(__file__), "..", "fixtures", "json")

# netkeibaオッズページのURL
ODDS_URL_TEMPLATE = "https://race.netkeiba.com/odds/index.html?race_id={race_id}"
ODDS_API_URL_TEMPLATE = (
    "https://race.netkeiba.com/api/api_get_jra_odds.html?race_id={race_id}&type=1"
)

# リクエストヘッダー
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/58.0.3029.110 Safari/537.3"
    )
}

# リクエスト間隔（秒）
REQUEST_INTERVAL = 1.0

# 取得対象のレースID
# - 馬券発売前: 未来のレース（予想オッズテーブルが表示される）
# - 馬券発売後・正常系: 過去のレース（単勝・複勝テーブルが表示される）
# - 馬券発売後・出走取消あり: 出走取消馬がいるレース
TARGET_RACES = [
    {"race_id": "202606020411", "description": "馬券発売前（未来のレース）"},
    {"race_id": "202606020211", "description": "馬券発売後・正常系"},
    {"race_id": "202306050911", "description": "馬券発売後・出走取消あり"},
]


def main() -> None:
    """netkeibaオッズページのHTMLおよびAPIレスポンスのフィクスチャを取得して保存する"""
    os.makedirs(os.path.normpath(FIXTURES_DIR_HTML), exist_ok=True)
    os.makedirs(os.path.normpath(FIXTURES_DIR_JSON), exist_ok=True)

    total_fetched = 0
    total_skipped = 0
    total_failed = 0

    for race in TARGET_RACES:
        race_id = race["race_id"]
        description = race["description"]

        print(f"[{description}] ({race_id})")

        # HTMLオッズページの取得
        html_path = os.path.join(FIXTURES_DIR_HTML, f"odds_netkeiba_{race_id}.html")
        if os.path.exists(html_path):
            print("  HTML: 既に存在")
            total_skipped += 1
        else:
            html_url = ODDS_URL_TEMPLATE.format(race_id=race_id)
            html = _fetch_html_page(html_url)
            if html:
                _save_html(html, html_path)
                print("  HTML: 保存しました")
                total_fetched += 1
            else:
                print("  HTML: 取得失敗")
                total_failed += 1
            time.sleep(REQUEST_INTERVAL)

        # オッズAPIの取得
        json_path = os.path.join(FIXTURES_DIR_JSON, f"odds_netkeiba_{race_id}.json")
        if os.path.exists(json_path):
            print("  JSON: 既に存在")
            total_skipped += 1
        else:
            api_url = ODDS_API_URL_TEMPLATE.format(race_id=race_id)
            json_data = _fetch_json_api(api_url)
            if json_data is not None:
                _save_json(json_data, json_path)
                print("  JSON: 保存しました")
                total_fetched += 1
            else:
                print("  JSON: 取得失敗")
                total_failed += 1
            time.sleep(REQUEST_INTERVAL)

    print(f"\n完了: {total_fetched}件取得, {total_skipped}件スキップ, {total_failed}件失敗")


def _fetch_html_page(url: str) -> str | None:
    """ページのHTMLを取得する

    Args:
        url (str): 取得するURL

    Returns:
        str | None: HTMLテキスト（UTF-8）。取得失敗時はNone
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.encoding = "EUC-JP"
        return response.text
    except requests.RequestException as exc:
        print(f"  [ERROR] HTML取得失敗: {exc}")
        return None


def _fetch_json_api(url: str) -> dict[str, Any] | None:
    """APIからJSONを取得する

    Args:
        url (str): 取得するURL

    Returns:
        dict[str, Any] | None: JSONデータ。取得失敗時はNone
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        print(f"  [ERROR] JSON取得失敗: {exc}")
        return None


def _save_html(html_text: str, filepath: str) -> None:
    """HTMLをUTF-8で保存する

    Args:
        html_text (str): HTMLテキスト
        filepath (str): 保存先ファイルパス
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_text)


def _save_json(data: dict[str, Any], filepath: str) -> None:
    """JSONをファイルに保存する

    Args:
        data (dict[str, Any]): JSONデータ
        filepath (str): 保存先ファイルパス
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
