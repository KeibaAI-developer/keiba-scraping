# keiba-scraping

## 概要

`keiba-scraping`は、[netkeiba](https://www.netkeiba.com/)および[JRA公式サイト](https://www.jra.go.jp/)から競馬データをスクレイピングし、`pandas.DataFrame`として取得するためのPythonライブラリです。

以下のデータを取得できます：

- レース情報（レース名、距離、コース、天候、馬場状態等）
- 出馬表（出走馬の枠番、馬番、騎手、斤量等）
- レース結果（着順、タイム、払い戻し、ラップタイム等）
- 馬柱（過去の競走成績）
- 馬基本情報（生年月日、血統、調教師、通算成績等）
- 馬情報（馬名、血統、厩舎、総賞金等）
- オッズ（単勝・複勝オッズ、予想オッズ）
- レース一覧（年間のレース検索結果）
- レーススケジュール（日別の開催レース一覧）
- JRA重賞レース一覧（年間の重賞レース一覧）


## 動作要件

- Python 3.12以上
- Google Chrome / Chromiumがインストールされていること（Selenium使用機能のみ）
- Playwrightがインストールされていること（JRAオッズ取得機能のみ）


## 依存パッケージ

- `pandas>=2.0.0,<3.0.0`
- `requests>=2.28.0`
- `beautifulsoup4>=4.12.0`
- `lxml>=4.9.0`
- `selenium>=4.10.0`
- `playwright>=1.30.0`
- `numpy>=1.24.0`


## インストール

```bash
pip install -e /path/to/keiba-scraping
```

Selenium使用機能を利用する場合は、ChromeDriverがPATHに含まれているか、環境変数`CHROME_DRIVER_PATH`で指定してください。

Playwright使用機能（JRAオッズ取得）を利用する場合は、追加で以下を実行してください：

```bash
playwright install chromium
```


## セットアップ

### 環境変数の設定（任意）

`.env.example`を`.env`にコピーし、必要に応じて編集します。

```dotenv
# ChromeDriverのパス（未設定の場合はSeleniumがPATHから自動検出）
# CHROME_DRIVER_PATH=/usr/local/bin/chromedriver
```


## 使い方

### 出馬表ページ

- **サンプルURL**: `https://race.netkeiba.com/race/shutuba.html?race_id=202505021211`
- **API**: `EntryPageScraper(race_id: str)`
- **サンプルコード**: [example/example_entry_page.py](example/example_entry_page.py)

| 関数 | 説明 | カラム定義 |
|------|------|------------|
| `get_race_info()` | レース情報 | [SCHEMA.md#レース情報](doc/SCHEMA.md#レース情報) |
| `get_entry()` | 出馬表 | [SCHEMA.md#出馬表](doc/SCHEMA.md#出馬表) |

---

### 結果ページ

- **サンプルURL**: `https://race.netkeiba.com/race/result.html?race_id=202505021211`
- **API**: `ResultPageScraper(race_id: str)`
- **サンプルコード**: [example/example_result_page.py](example/example_result_page.py)

| 関数 | 説明 | カラム定義 |
|------|------|------------|
| `get_race_info()` | レース情報 | [SCHEMA.md#レース情報](doc/SCHEMA.md#レース情報) |
| `get_result()` | レース結果 | [SCHEMA.md#レース結果](doc/SCHEMA.md#レース結果) |
| `get_corner()` | コーナー通過順 | [SCHEMA.md#コーナー通過順](doc/SCHEMA.md#コーナー通過順) |
| `get_win_payoff()` | 単勝払い戻し | [SCHEMA.md#単勝払い戻し](doc/SCHEMA.md#単勝払い戻し) |
| `get_show_payoff()` | 複勝払い戻し | [SCHEMA.md#複勝払い戻し](doc/SCHEMA.md#複勝払い戻し) |
| `get_bracket_payoff()` | 枠連払い戻し | [SCHEMA.md#枠連払い戻し](doc/SCHEMA.md#枠連払い戻し) |
| `get_quinella_payoff()` | 馬連払い戻し | [SCHEMA.md#馬連払い戻し](doc/SCHEMA.md#馬連払い戻し) |
| `get_quinella_place_payoff()` | ワイド払い戻し | [SCHEMA.md#ワイド払い戻し](doc/SCHEMA.md#ワイド払い戻し) |
| `get_exacta_payoff()` | 馬単払い戻し | [SCHEMA.md#馬単払い戻し](doc/SCHEMA.md#馬単払い戻し) |
| `get_trio_payoff()` | 3連複払い戻し | [SCHEMA.md#3連複払い戻し](doc/SCHEMA.md#3連複払い戻し) |
| `get_trifecta_payoff()` | 3連単払い戻し | [SCHEMA.md#3連単払い戻し](doc/SCHEMA.md#3連単払い戻し) |
| `get_lap_time()` | ラップタイム | [SCHEMA.md#ラップタイム](doc/SCHEMA.md#ラップタイム) |

---

### 馬情報ページ

- **サンプルURL**: `https://db.netkeiba.com/horse/2022105081`
- **API**: `HorsePageScraper(horse_id: str)` （Selenium使用）
- **サンプルコード**: [example/example_horse_page.py](example/example_horse_page.py)

| 関数 | 説明 | カラム定義 |
|------|------|------------|
| `get_past_performances()` | 馬柱 | [SCHEMA.md#馬柱](doc/SCHEMA.md#馬柱) |
| `get_horse_basic_info()` | 馬基本情報 | [SCHEMA.md#馬基本情報](doc/SCHEMA.md#馬基本情報) |

---

### 馬情報一覧ページ

- **サンプルURL**: `https://db.netkeiba.com/?pid=horse_list&birthyear=2022&list=100&page=1`
- **API**: `HorseInfoScraper(year: int)`
- **サンプルコード**: [example/example_horse_info.py](example/example_horse_info.py)

| 関数 | 説明 | カラム定義 |
|------|------|------------|
| `scrape_one_page(page_num: int)` | 指定ページの馬情報を取得 | [SCHEMA.md#馬情報](doc/SCHEMA.md#馬情報) |
| `get_all_horse_info()` | 全ページ分を一括取得 | [SCHEMA.md#馬情報](doc/SCHEMA.md#馬情報) |

---

### オッズ

- **サンプルURL**: `https://race.netkeiba.com/odds/index.html?race_id=202505021211`
- **サンプルコード**:
  - [example/example_odds_netkeiba.py](example/example_odds_netkeiba.py)
  - [example/example_yoso_odds_netkeiba.py](example/example_yoso_odds_netkeiba.py)
  - [example/example_odds_jra.py](example/example_odds_jra.py)

| 関数 | 説明 | カラム定義 |
|------|------|------------|
| `scrape_odds_from_netkeiba(race_id: str)` | netkeibaから現在のオッズを取得 | [SCHEMA.md#オッズ](doc/SCHEMA.md#オッズ) |
| `scrape_odds_from_jra(race_id: str)` | JRAから現在のオッズを取得（Playwright） | [SCHEMA.md#オッズ](doc/SCHEMA.md#オッズ) |
| `scrape_yoso_odds_from_netkeiba(race_id: str)` | netkeibaから予想オッズを取得（Selenium） | [SCHEMA.md#予想オッズ](doc/SCHEMA.md#予想オッズ) |

---

### レース一覧ページ

- **サンプルURL**: `https://db.netkeiba.com/?pid=race_list&word=&start_year=2025&start_mon=1&end_year=2025&end_mon=12&...&page=1`
- **API**: `RaceListScraper(year: int)`
- **サンプルコード**: [example/example_race_list.py](example/example_race_list.py)

| 関数 | 説明 | カラム定義 |
|------|------|------------|
| `scrape_one_page(page_num: int)` | 指定ページのレース一覧を取得 | [SCHEMA.md#レース一覧](doc/SCHEMA.md#レース一覧) |
| `get_race_list(sleep: float = 1.0)` | 全ページ分を一括取得 | [SCHEMA.md#レース一覧](doc/SCHEMA.md#レース一覧) |

---

### 日別レーススケジュールページ

- **サンプルURL**: `https://race.netkeiba.com/top/race_list.html?kaisai_date=20250601`
- **API**: `RaceScheduleScraper(year: int, month: int, day: int)` （Selenium使用）
- **サンプルコード**: [example/example_race_schedule.py](example/example_race_schedule.py)

| 関数 | 説明 | カラム定義 |
|------|------|------------|
| `get_race_schedule()` | レーススケジュール | [SCHEMA.md#レーススケジュール](doc/SCHEMA.md#レーススケジュール) |

---

### JRA重賞レース一覧ページ

- **サンプルURL**: `https://www.jra.go.jp/datafile/seiseki/replay/2025/jyusyo.html`
- **API**: `JraGradedRaceScraper(year: int)`
- **サンプルコード**: [example/example_jra_graded_race.py](example/example_jra_graded_race.py)

| 関数 | 説明 | カラム定義 |
|------|------|------------|
| `get_graded_races()` | JRA重賞レース一覧 | [SCHEMA.md#jra重賞レース一覧](doc/SCHEMA.md#jra重賞レース一覧) |

---

### ユーティリティ関数

| 関数 | 説明 |
|------|------|
| `is_race_existence(url: str, session: requests.Session)` | 指定URLのレースが存在するか確認 |
