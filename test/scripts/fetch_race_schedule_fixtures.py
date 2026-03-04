"""テスト用レーススケジュールHTMLフィクスチャ取得スクリプト

Seleniumでnetkeibaのレーススケジュールページのを取得し、
test/fixtures/html/にUTF-8で保存する。

使用方法:
    python test/scripts/fetch_race_schedule_fixtures.py
"""

import os
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# フィクスチャ保存先ディレクトリ
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures", "html")

# 取得対象の日付（YYYYMMDD形式）
TARGET_DATES = [
    "20260301",
]

# netkeibaのURL
URL_TEMPLATE = "https://race.netkeiba.com/top/race_list.html?kaisai_date={date}"

# ページ読み込み待機時間（秒）
PAGE_LOAD_WAIT = 5

# リクエスト間隔（秒）
REQUEST_INTERVAL = 2.0


def _set_chrome_options() -> Options:
    """ChromeDriverのオプションを設定する

    Returns:
        Options: ヘッドレスモード等を設定済みのChromeオプション
    """
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return options


def main() -> None:
    """テスト用レーススケジュールHTMLフィクスチャを取得して保存する"""
    fixtures_dir = os.path.normpath(FIXTURES_DIR)
    os.makedirs(fixtures_dir, exist_ok=True)

    # ChromeDriverを起動
    options = _set_chrome_options()
    chrome_driver_path = os.environ.get("CHROME_DRIVER_PATH")
    service = Service(chrome_driver_path) if chrome_driver_path else Service()
    driver = webdriver.Chrome(service=service, options=options)

    total_fetched = 0
    total_skipped = 0

    try:
        for date_str in TARGET_DATES:
            filepath = os.path.join(fixtures_dir, f"race_schedule_{date_str}.html")
            if os.path.exists(filepath):
                print(f"[{date_str}] → 既に存在")
                total_skipped += 1
                continue

            print(f"[{date_str}] → 取得中...")
            url = URL_TEMPLATE.format(date=date_str)

            try:
                driver.get(url)
                time.sleep(PAGE_LOAD_WAIT)
                html_text = driver.page_source

                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(html_text)
                print(f"[{date_str}] → 保存完了: {filepath}")
                total_fetched += 1
            except Exception as exc:
                print(f"[{date_str}] → 取得失敗: {exc}")

            if date_str != TARGET_DATES[-1]:
                time.sleep(REQUEST_INTERVAL)
    finally:
        driver.quit()

    print(f"\n完了: {total_fetched}件取得, {total_skipped}件スキップ")


if __name__ == "__main__":
    main()
