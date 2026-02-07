"""例外クラス定義モジュール

keiba-scrapingライブラリで使用する例外クラスを定義する。
"""


class ScrapingError(Exception):
    """keiba-scraping基底例外"""


class PageNotFoundError(ScrapingError):
    """ページが存在しない場合の例外"""


class ParseError(ScrapingError):
    """HTML解析に失敗した場合の例外"""


class NetworkError(ScrapingError):
    """ネットワークエラー"""


class DriverError(ScrapingError):
    """Selenium/Playwrightのドライバーエラー"""
