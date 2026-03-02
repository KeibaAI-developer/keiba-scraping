"""is_race_existence関数の単体テスト

requestsをモックしてテストする。
"""

from unittest.mock import MagicMock

from scraping.config import ScrapingConfig
from scraping.utils import is_race_existence


# ---------------------------------------------------------------------------
# 正常系: ページが存在する場合
# ---------------------------------------------------------------------------
def test_returns_true_when_table_exists() -> None:
    """HTMLにtable要素が存在する場合にTrueを返すこと"""
    html_with_table = (
        "<html><body>" "<table><tr><th>A</th></tr><tr><td>1</td></tr></table>" "</body></html>"
    )
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.text = html_with_table
    mock_response.encoding = "EUC-JP"
    mock_session.get.return_value = mock_response

    result = is_race_existence("https://example.com/race", mock_session)

    assert result is True


# ---------------------------------------------------------------------------
# 準正常系: ページが存在しない場合
# ---------------------------------------------------------------------------
def test_returns_false_when_no_table() -> None:
    """HTMLにtable要素が存在しない場合にFalseを返すこと"""
    html_without_table = "<html><body><div>no table</div></body></html>"
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.text = html_without_table
    mock_response.encoding = "EUC-JP"
    mock_session.get.return_value = mock_response

    result = is_race_existence("https://example.com/race", mock_session)

    assert result is False


def test_returns_false_when_empty_html() -> None:
    """空のHTMLの場合にFalseを返すこと"""
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.text = ""
    mock_response.encoding = "EUC-JP"
    mock_session.get.return_value = mock_response

    result = is_race_existence("https://example.com/race", mock_session)

    assert result is False


# ---------------------------------------------------------------------------
# 正常系: configを指定した場合
# ---------------------------------------------------------------------------
def test_uses_custom_config() -> None:
    """カスタムconfigを渡した場合に正常に動作すること"""
    html_with_table = (
        "<html><body>" "<table><tr><th>A</th></tr><tr><td>1</td></tr></table>" "</body></html>"
    )
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.text = html_with_table
    mock_response.encoding = "EUC-JP"
    mock_session.get.return_value = mock_response

    config = ScrapingConfig()
    result = is_race_existence("https://example.com/race", mock_session, config)

    assert result is True
