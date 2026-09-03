"""extract_id_from_td()の単体テスト"""

import logging

import numpy as np
import pytest
from bs4 import BeautifulSoup, Tag

from scraping.exceptions import ParseError
from scraping.utils import extract_id_from_td

HORSE_PATTERN = r"[0-9A-Za-z]{10}"
TRAINER_PATTERN = r"[0-9A-Za-z]{5}"
LOGGER = logging.getLogger(__name__)


def _make_td(inner_html: str) -> Tag:
    """td要素を生成する

    Args:
        inner_html (str): td要素の中身のHTML

    Returns:
        Tag: td要素
    """
    td_element = BeautifulSoup(f"<td>{inner_html}</td>", "html.parser").td
    assert isinstance(td_element, Tag)
    return td_element


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
def test_extract_id_from_td_returns_id(href: str, id_pattern: str, expected: str) -> None:
    """パス末尾またはidクエリからIDを抽出できること"""
    td_element = _make_td(f'<a href="{href}">名前</a>')
    assert extract_id_from_td(td_element, id_pattern, LOGGER) == expected


def test_extract_id_from_td_returns_nan_without_link() -> None:
    """リンクがない場合にNaNを返すこと"""
    td_element = _make_td("名前")
    assert np.isnan(extract_id_from_td(td_element, HORSE_PATTERN, LOGGER))


# 準正常系
@pytest.mark.parametrize(
    "href, id_pattern",
    [
        ("https://db.netkeiba.com/trainer/race.html?id=abc", TRAINER_PATTERN),
        ("/horse/2022105081/", TRAINER_PATTERN),
        ("https://db.netkeiba.com/horse/list.html?sire_id=2015101621&word=", HORSE_PATTERN),
        ("https://db.netkeiba.com/trainer/top.html", TRAINER_PATTERN),
    ],
)
def test_extract_id_from_td_raises_for_unexpected_format(href: str, id_pattern: str) -> None:
    """リンクはあるがURL末尾が期待する形式のIDでない場合にParseErrorが発生すること"""
    td_element = _make_td(f'<a href="{href}">名前</a>')
    with pytest.raises(ParseError, match="IDが期待する形式ではありません"):
        extract_id_from_td(td_element, id_pattern, LOGGER)
