"""レース一覧テスト用HTMLフィクスチャ取得スクリプト

netkeibaのレース一覧ページのHTMLをrequestsで取得し、
test/fixtures/html/ にUTF-8で保存する。

使用方法:
    python test/scripts/fetch_race_list_fixtures.py
"""

import os

import requests

from scraping.config import ScrapingConfig
from scraping.url_builder import build_race_list_url

# フィクスチャ保存先ディレクトリ
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures", "html")

# リクエストヘッダー
HEADERS = ScrapingConfig().headers

# 取得対象
TARGETS: list[dict[str, int]] = [
    {"year": 2026, "page_num": 1},
]


def fetch_and_save(year: int, page_num: int) -> None:
    """指定した年・ページのレース一覧をフェッチしてHTMLファイルに保存する

    Args:
        year (int): 年
        page_num (int): ページ番号
    """
    url = build_race_list_url(year, page_num)
    filename = f"race_list_{year}_p{page_num}.html"
    filepath = os.path.join(FIXTURES_DIR, filename)

    print(f"取得中: {url}")
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    response.encoding = "EUC-JP"

    os.makedirs(FIXTURES_DIR, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(response.text)

    print(f"  保存: {filepath} ({len(response.text)} bytes)")


def main() -> None:
    """メイン処理"""
    print("=" * 60)
    print("レース一覧テスト用HTMLフィクスチャ取得")
    print("=" * 60)

    for target in TARGETS:
        fetch_and_save(target["year"], target["page_num"])

    print()
    print("完了")


if __name__ == "__main__":
    main()
