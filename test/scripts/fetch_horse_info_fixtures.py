"""馬情報テスト用HTMLフィクスチャ取得スクリプト

netkeibaの競走馬一覧ページのHTMLをrequestsで取得し、
test/fixtures/html/ にUTF-8で保存する。

使用方法:
    python test/scripts/fetch_horse_info_fixtures.py
"""

import os
import time

import requests

# フィクスチャ保存先ディレクトリ
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures", "html")

# netkeibaの競走馬一覧ページURL
HORSE_LIST_URL_TEMPLATE = (
    "https://db.netkeiba.com/?pid=horse_list&birthyear={year}&list=100&page={page_num}"
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
REQUEST_INTERVAL = 3.0

# 取得対象
TARGETS: list[dict[str, int]] = [
    {"year": 2022, "page_num": 1},  # 正常系: 通常の馬情報が取得できるページ
]


def fetch_and_save(year: int, page_num: int) -> None:
    """指定した年・ページの馬情報一覧をフェッチしてHTMLファイルに保存する

    Args:
        year (int): 生年
        page_num (int): ページ番号
    """
    url = HORSE_LIST_URL_TEMPLATE.format(year=year, page_num=page_num)
    filename = f"horse_info_{year}_p{page_num}.html"
    filepath = os.path.join(FIXTURES_DIR, filename)

    print(f"取得中: {url}")
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.encoding = "EUC-JP"

    os.makedirs(FIXTURES_DIR, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(response.text)

    print(f"  保存: {filepath} ({len(response.text)} bytes)")


def fetch_last_page(year: int) -> None:
    """最後のページ番号を取得してフェッチする

    Args:
        year (int): 生年
    """
    import re

    from bs4 import BeautifulSoup

    # まず1ページ目のHTMLからページ数を取得
    url = HORSE_LIST_URL_TEMPLATE.format(year=year, page_num=1)
    print(f"最大ページ数を取得中: {url}")
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.encoding = "EUC-JP"

    soup = BeautifulSoup(response.text, "html.parser")
    pager = soup.find("div", class_="pager")
    if pager is None:
        print("  ページャーが見つかりません。スキップします。")
        return

    match = re.search(r"\d{1,3}(?:,\d{3})?", pager.text)
    if match:
        birth_num = int(match.group().replace(",", ""))
        max_page_num = birth_num // 100 + 1
        print(f"  最大ページ数: {max_page_num} (生産頭数: {birth_num})")
    else:
        print("  ページ数の取得に失敗しました。スキップします。")
        return

    time.sleep(REQUEST_INTERVAL)
    fetch_and_save(year, max_page_num)


def main() -> None:
    """メイン処理"""
    print("=" * 60)
    print("馬情報テスト用HTMLフィクスチャ取得")
    print("=" * 60)

    # 固定ターゲットの取得
    for target in TARGETS:
        fetch_and_save(target["year"], target["page_num"])
        time.sleep(REQUEST_INTERVAL)

    # 最後のページを取得
    fetch_last_page(2022)

    print()
    print("完了")


if __name__ == "__main__":
    main()
