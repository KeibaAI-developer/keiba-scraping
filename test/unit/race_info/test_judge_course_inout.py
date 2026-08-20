"""_judge_course_inoutの単体テスト."""

import pytest

from scraping.race_info import _judge_course_inout


# 正常系
@pytest.mark.parametrize(
    "course, expected",
    [
        ("右 内 B", "内"),
        ("右 外 B", "外"),
        ("右 内-外 A", "内-外"),
        ("右 外-内 A", "外-内"),
        # 判定不能時は空文字
        ("右 B", ""),
        ("", ""),
    ],
)
def test_judge_course_inout(course: str, expected: str) -> None:
    """コースの生値から内外を判定できる."""
    assert _judge_course_inout(course) == expected
