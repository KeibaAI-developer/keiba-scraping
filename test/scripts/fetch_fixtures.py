"""テスト用HTMLフィクスチャ取得スクリプト

test/fixtures/test_case.ymlに定義されているレースIDに対して、
netkeibaの出馬表ページと結果ページのHTMLをrequestsで取得し、
test/fixtures/html/にUTF-8で保存する。

地方競馬（JavaScriptで動的にレンダリングされるページ）はスキップする。

使用方法:
    python test/scripts/fetch_fixtures.py
"""

import os
import sys
import time

import requests
import yaml

# テストケースYAMLファイルのパス
TEST_CASE_YML_PATH = os.path.join(os.path.dirname(__file__), "..", "fixtures", "test_case.yml")

# フィクスチャ保存先ディレクトリ
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures", "html")

# netkeibaのURL
ENTRY_URL_TEMPLATE = "https://race.netkeiba.com/race/shutuba.html?race_id={race_id}"
RESULT_URL_TEMPLATE = "https://race.netkeiba.com/race/result.html?race_id={race_id}"

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

# 地方競馬の競馬場IDプレフィックス（30以上は地方）
LOCAL_KEIBAJO_ID_MIN = 30


def _is_local_race(race_id: str) -> bool:
    """地方競馬のレースかどうかを判定する

    レースIDの5〜6桁目が競馬場IDを表し、30以上なら地方競馬。

    Args:
        race_id (str): レースID（12桁文字列）

    Returns:
        bool: 地方競馬ならTrue
    """
    keibajo_id = int(race_id[4:6])
    return keibajo_id >= LOCAL_KEIBAJO_ID_MIN


def _fetch_page(url: str) -> str | None:
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
        print(f"  [ERROR] 取得失敗: {exc}")
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


def main() -> None:
    """テスト用HTMLフィクスチャを取得して保存する"""
    # test_case.ymlを読み込む
    yml_path = os.path.normpath(TEST_CASE_YML_PATH)
    if not os.path.exists(yml_path):
        print(f"[ERROR] test_case.ymlが見つかりません: {yml_path}")
        sys.exit(1)

    with open(yml_path, encoding="utf-8") as f:
        races = yaml.safe_load(f)

    if not races:
        print("[ERROR] test_case.ymlにレース情報がありません")
        sys.exit(1)

    fixtures_dir = os.path.normpath(FIXTURES_DIR)
    total_fetched = 0
    total_skipped = 0

    for race in races:
        race_id = race["race_id"]
        race_name = race.get("race_name", "不明")

        # 地方競馬はスキップ
        if _is_local_race(race_id):
            print(f"[{race_name}] ({race_id}) → 地方競馬のためスキップ")
            total_skipped += 1
            continue

        print(f"[{race_name}] ({race_id})")

        # 出馬表ページの取得
        entry_path = os.path.join(fixtures_dir, f"entry_{race_id}.html")
        if not os.path.exists(entry_path):
            entry_url = ENTRY_URL_TEMPLATE.format(race_id=race_id)
            html = _fetch_page(entry_url)
            if html:
                _save_html(html, entry_path)
                print("  出馬表: 保存しました")
                total_fetched += 1
            time.sleep(REQUEST_INTERVAL)
        else:
            print("  出馬表: 既に存在")

        # 結果ページの取得
        result_path = os.path.join(fixtures_dir, f"result_{race_id}.html")
        if not os.path.exists(result_path):
            result_url = RESULT_URL_TEMPLATE.format(race_id=race_id)
            html = _fetch_page(result_url)
            if html:
                _save_html(html, result_path)
                print("  結果:   保存しました")
                total_fetched += 1
            time.sleep(REQUEST_INTERVAL)
        else:
            print("  結果:   既に存在")

    print(f"\n完了: {total_fetched}件取得, {total_skipped}件スキップ")


if __name__ == "__main__":
    main()
