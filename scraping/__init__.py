"""keiba-scraping: netkeibaおよびJRAから競馬データをスクレイピングするライブラリ

このライブラリは、netkeibaおよびJRAの公式サイトから競馬データを
スクレイピングし、pandas.DataFrameとして取得するためのインターフェースを提供します。
"""

try:
    from importlib.metadata import version

    __version__ = version("keiba-scraping")
except Exception:
    __version__ = "unknown"
