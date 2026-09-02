"""extract_id_from_href()の単体テスト"""

import pytest

from scraping.utils import extract_id_from_href

HORSE_PATTERN = r"[0-9A-Za-z]{10}"
TRAINER_PATTERN = r"[0-9A-Za-z]{5}"


# 正常系
@pytest.mark.parametrize(
    "href, id_pattern, expected",
    [
        ("https://db.netkeiba.com/horse/2022105081/", HORSE_PATTERN, "2022105081"),
        ("/horse/000a02d612/", HORSE_PATTERN, "000a02d612"),
        ("/jockey/result/recent/01140/", TRAINER_PATTERN, "01140"),
        ("https://db.netkeiba.com/trainer/race.html?id=01159", TRAINER_PATTERN, "01159"),
        ("https://db.netkeiba.com/trainer/race.html?id=a02a8", TRAINER_PATTERN, "a02a8"),
        ("https://db.netkeiba.com/owner/race.html?id=226800", r"[0-9A-Za-z]{6}", "226800"),
    ],
)
def test_extract_id_from_href_returns_id(href: str, id_pattern: str, expected: str) -> None:
    """パス末尾またはidクエリからIDを抽出できること"""
    assert extract_id_from_href(href, id_pattern) == expected


# 準正常系
@pytest.mark.parametrize(
    "href, id_pattern",
    [
        ("https://db.netkeiba.com/trainer/race.html?id=abc", TRAINER_PATTERN),
        ("/horse/2022105081/", TRAINER_PATTERN),
        ("https://db.netkeiba.com/horse/list.html?sire_id=2015101621&word=", HORSE_PATTERN),
        ("https://db.netkeiba.com/trainer/top.html", TRAINER_PATTERN),
        ("", HORSE_PATTERN),
    ],
)
def test_extract_id_from_href_returns_none_for_unexpected_format(
    href: str, id_pattern: str
) -> None:
    """URL末尾が期待する形式のIDでない場合にNoneを返すこと"""
    assert extract_id_from_href(href, id_pattern) is None
