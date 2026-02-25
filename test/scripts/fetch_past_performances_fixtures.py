"""テスト用馬柱HTMLフィクスチャ取得スクリプト

test/fixtures/test_horse_case.ymlに定義されている馬IDに対して、
SeleniumでnetkeibaのページをレンダリングしたHTMLを
test/fixtures/html/にUTF-8で保存する。

使用方法:
    python test/scripts/fetch_past_performances_fixtures.py
"""

import os
import sys
import time

import yaml
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# テストケースYAMLファイルのパス
TEST_HORSE_CASE_YML_PATH = os.path.join(
    os.path.dirname(__file__), "..", "fixtures", "test_horse_case.yml"
)

# フィクスチャ保存先ディレクトリ
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures", "html")

# netkeibaのURL
HORSE_URL_TEMPLATE = "https://db.netkeiba.com/horse/{horse_id}"

# ページ読み込み待機時間（秒）
PAGE_LOAD_WAIT = 5

# リクエスト間隔（秒）
REQUEST_INTERVAL = 2.0


def main() -> None:
    """テスト用馬柱HTMLフィクスチャを取得して保存する"""
    yml_path = os.path.normpath(TEST_HORSE_CASE_YML_PATH)
    if not os.path.exists(yml_path):
        print(f"[ERROR] test_horse_case.ymlが見つかりません: {yml_path}")
        sys.exit(1)

    with open(yml_path, encoding="utf-8") as f:
        horses = yaml.safe_load(f)

    if not horses:
        print("[ERROR] test_horse_case.ymlに馬情報がありません")
        sys.exit(1)

    fixtures_dir = os.path.normpath(FIXTURES_DIR)
    os.makedirs(fixtures_dir, exist_ok=True)

    # ChromeDriverを起動
    options = _set_chrome_options()
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    total_fetched = 0
    total_skipped = 0

    try:
        for horse in horses:
            horse_id = horse["horse_id"]
            horse_name = horse.get("horse_name", "不明")

            filepath = os.path.join(fixtures_dir, f"past_performances_{horse_id}.html")
            if os.path.exists(filepath):
                print(f"[{horse_name}] ({horse_id}) → 既に存在")
                total_skipped += 1
                continue

            print(f"[{horse_name}] ({horse_id}) → 取得中...")
            url = HORSE_URL_TEMPLATE.format(horse_id=horse_id)

            try:
                driver.get(url)
                time.sleep(PAGE_LOAD_WAIT)
                html_text = driver.page_source
                _save_html(html_text, filepath)
                print(f"  保存しました: {filepath}")
                total_fetched += 1
            except Exception as exc:
                print(f"  [ERROR] 取得失敗: {exc}")

            time.sleep(REQUEST_INTERVAL)
    finally:
        driver.quit()

    print(f"\n完了: {total_fetched}件取得, {total_skipped}件スキップ")


def _set_chrome_options() -> Options:
    """ChromeDriverのオプション設定を返す

    Returns:
        Options: ヘッドレスモード等を設定済みのChromeオプション
    """
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return options


def _save_html(html_text: str, filepath: str) -> None:
    """HTMLをUTF-8で保存する

    Args:
        html_text (str): HTMLテキスト
        filepath (str): 保存先ファイルパス
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_text)


if __name__ == "__main__":
    main()
