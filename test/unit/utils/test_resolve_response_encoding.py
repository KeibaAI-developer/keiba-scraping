"""resolve_response_encoding関数の単体テスト

requests.Responseを実際のバイト列から組み立ててテストする。
"""

import pytest
from requests import Response
from requests.utils import get_encoding_from_headers

from scraping.utils import resolve_response_encoding

# 検出に十分な長さを持つ日本語のHTML本文
SAMPLE_TEXT = (
    "<html><body>"
    + "東京優駿は日本ダービーとも呼ばれる中央競馬の重賞競走。" * 20
    + "</body></html>"
)


def _build_response(body: bytes, content_type: str) -> Response:
    """Content-Typeヘッダとバイト列からResponseを組み立てる

    requestsがレスポンス受信時に行うのと同じ手順で ``encoding`` を設定する。

    Args:
        body (bytes): レスポンス本文
        content_type (str): Content-Typeヘッダの値

    Returns:
        Response: encoding設定済みのレスポンス
    """
    response = Response()
    response._content = body
    response.headers["Content-Type"] = content_type
    response.encoding = get_encoding_from_headers(response.headers)
    return response


# ---------------------------------------------------------------------------
# 正常系: ヘッダにcharsetが指定されている場合
# ---------------------------------------------------------------------------
def test_prefers_charset_in_header() -> None:
    """ヘッダのcharset指定をそのまま採用し、本文が正しくデコードされること"""
    response = _build_response(SAMPLE_TEXT.encode("utf-8"), "text/html; charset=UTF-8")

    result = resolve_response_encoding(response)

    assert result == "UTF-8"
    response.encoding = result
    assert response.text == SAMPLE_TEXT


def test_header_charset_takes_priority_over_detection() -> None:
    """ヘッダにcharsetがあれば本文からの推定を行わないこと"""
    # 本文はEUC-JPだが、ヘッダの指定（Shift_JIS）が優先される
    response = _build_response(SAMPLE_TEXT.encode("euc_jp"), "text/html; charset=Shift_JIS")

    result = resolve_response_encoding(response)

    assert result == "Shift_JIS"


# ---------------------------------------------------------------------------
# 正常系: ヘッダにcharsetが無い場合
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "encoding", ["euc_jp", "shift_jis", "utf-8"], ids=["euc_jp", "shift_jis", "utf-8"]
)
def test_falls_back_to_detection_when_header_has_no_charset(encoding: str) -> None:
    """charset未指定のtext/htmlでは本文から推定し、正しくデコードされること"""
    # requestsはcharsetを持たないtext/*にISO-8859-1を設定する
    response = _build_response(SAMPLE_TEXT.encode(encoding), "text/html")
    assert response.encoding == "ISO-8859-1"

    result = resolve_response_encoding(response)

    assert result is not None
    assert result.lower() != "iso-8859-1"
    response.encoding = result
    assert response.text == SAMPLE_TEXT


def test_falls_back_to_detection_when_encoding_is_none() -> None:
    """encodingがNoneの場合に本文から推定すること"""
    response = _build_response(SAMPLE_TEXT.encode("euc_jp"), "text/html")
    response.encoding = None

    result = resolve_response_encoding(response)

    assert result is not None
    response.encoding = result
    assert response.text == SAMPLE_TEXT


# ---------------------------------------------------------------------------
# 準正常系: 本文が空の場合
# ---------------------------------------------------------------------------
def test_empty_body_does_not_raise() -> None:
    """本文が空でも例外を投げず、textが空文字になること"""
    response = _build_response(b"", "text/html")

    result = resolve_response_encoding(response)

    response.encoding = result
    assert response.text == ""
