# keiba-scraping 機能仕様書

## 1. 概要

`keiba-scraping`は、netkeibaおよびJRAの公式サイトから競馬データをスクレイピングし、`pandas.DataFrame`として返すPythonライブラリである。KeibaAIプロジェクトから純粋なスクレイピング機能のみを抽出し、KeibaAIへの依存を排除した独立したライブラリとして実装する。

### 1.1. 設計方針

- **スクレイピングロジックの同一性**: `scraping_core.py`のスクレイピング処理と同じロジックを実装する。KeibaAIとの依存を切ったりリファクタリングは行うが、スクレイピング自体の処理は変えない
- **KeibaAIとの依存排除**: `param`、`modules.utils`（`file_io`、`keiba_utils`等）に依存しない
- **データ取得のみ**: CSVファイルへの保存機能は持たない。データフレームを返すのみ
- **date_id不使用**: KeibaAI固有の日付ID概念は使用しない
- **コース何日目不使用**: 過去データの蓄積が必要な `calc_course_days` はライブラリに含めない
- **データ整形は維持**: スクレイピングで取得したデータの整形処理（カラム名変更、型変換、分割等）は残す
- **ページ単位のスクレイパークラス設計**: 同じページにある複数の表を取得する際に毎回スクレイピングするのは負荷が大きいため、ページごとにスクレイパークラスを設計する
- **mykeibadb-pythonを参考**: ライブラリ構成・テスト構成・pyproject.tomlの設計を参考にする

### 1.2. 命名統一に関する注記

- **発走時刻**: keiba-scrapingでは「発走時刻」で統一。KeibaAI側では「発走時間」を使用していたが、将来的に「発走時刻」に統一する予定
- **天候**: netkeibaの表示に合わせて「天候」を使用（KeibaAI側で「天気」と表記されている箇所があるが、netkeibaの原始データに合わせる）

### 1.3. アーキテクチャ

ページごとにスクレイパークラスを設けて、コンストラクタでHTTPリクエストとBeautifulSoupの生成を行い、各メソッドでテーブルを取得する。

- `race_info.py`のみ独立モジュールとしてパブリック関数`scrape_race_info()`を提供し、スクレイパークラスおよび外部から直接呼び出し可能
- `result_page.py`と`entry_page.py`はスクレイパークラス内にスクレイピングロジックを直接実装し、独立したモジュール（`result.py`や`entry.py`）は設けない

```
呼び出し元
  ↓
スクレイパークラス (entry_page.py, result_page.py 等)
  │ コンストラクタ: HTTP取得 → soup生成
  │ get_race_info(): race_info.scrape_race_info(soup, ...) を呼び出し
  │ get_result(): 内部のプライベートメソッドを呼び出し
  │ ...
  ↓
pd.DataFrame
```

```
呼び出し元（race_infoのみ直接呼び出し可能）
  ↓
race_info.scrape_race_info(soup, race_id)
  ↓
pd.DataFrame
```

#### スクレイパークラス一覧

| クラス名 | ファイル | 対応ページ | 取得メソッド |
|---|---|---|---|
| `EntryPageScraper` | `entry_page.py` | 出馬表ページ | `get_race_info()`, `get_entry()` |
| `ResultPageScraper` | `result_page.py` | 結果ページ | `get_race_info()`, `get_result()`, `get_corner()`, `get_win_payoff()`, `get_show_payoff()`, `get_bracket_payoff()`, `get_quinella_payoff()`, `get_quinella_place_payoff()`, `get_exacta_payoff()`, `get_trio_payoff()`, `get_trifecta_payoff()`, `get_lap_time()` |
| `HorsePageScraper` | `horse_page.py` | 馬情報ページ | `get_past_performances()` |

`race_info.py`のパブリック関数`scrape_race_info()`は、スクレイパークラスからだけでなく直接soupを渡して呼び出すことも可能。これにより単体テストではスクレイパークラスを経由せずにテストできる。


## 2. 動作要件

- Python 3.12以上
- Google Chrome / Chromiumがインストールされていること（Selenium使用機能のみ）


## 3. 依存パッケージ

```
pandas>=2.0.0
requests>=2.28.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
selenium>=4.10.0
playwright>=1.30.0
numpy>=1.24.0
```


## 4. パッケージ構成

```
keiba-scraping/
├── LICENSE
├── README.md
├── pyproject.toml
├── .gitignore
├── .github/
│   └── workflows/
│       └── ci.yml
├── doc/
│   └── DEVELOP/
│       ├── INST.md
│       ├── SPEC.md
│       └── PLAN.md
├── example/
│   └── basic_usage.py
├── scraping/
│   ├── __init__.py
│   ├── config.py          # 設定管理（URL定数、HTTPヘッダー等）
│   ├── exceptions.py      # 例外クラス定義
│   ├── race_info.py       # レース情報の抽出・整形（公開関数として提供）
│   ├── entry_page.py      # 出馬表ページスクレイパークラス（出馬表の抽出・整形を含む）
│   ├── result_page.py     # 結果ページスクレイパークラス（結果・コーナー・払い戻し・ラップタイムの抽出・整形を含む）
│   ├── horse.py           # 馬情報・馬柱の抽出・整形
│   ├── odds.py            # オッズの抽出・整形
│   ├── schedule.py        # レーススケジュール・カレンダー
│   ├── horse_page.py      # 馬情報ページスクレイパークラス
│   ├── utils.py           # ライブラリ内共通ユーティリティ
│   └── py.typed
└── test/
    ├── __init__.py
    ├── conftest.py
    ├── fixtures/
    │   └── html/              # テスト用HTMLフィクスチャ（test_case.ymlの各レース）
    ├── scripts/
    │   └── fetch_fixtures.py  # フィクスチャHTML取得スクリプト
    ├── unit/
    │   ├── __init__.py
    │   ├── race_info/
    │   ├── result_page/
    │   ├── entry_page/
    │   ├── horse/
    │   ├── odds/
    │   ├── schedule/
    │   └── utils/
    └── integration/
        ├── __init__.py
        └── ...
```


## 5. モジュール詳細

### 5.1. `config.py` — 設定管理

KeibaAIでは`param.py`と各種`.yml`ファイルで管理していた定数類を、ライブラリ独自に管理する。

#### クラス: `ScrapingConfig`

ライブラリ全体の設定を保持するデータクラス。

| 属性名 | 型 | 説明 | デフォルト値 |
|---|---|---|---|
| `netkeiba_base_url` | `str` | netkeibaのベースURL | `"https://db.netkeiba.com"` |
| `netkeiba_race_url` | `str` | netkeibaのレースURL | `"https://race.netkeiba.com"` |
| `jra_url` | `str` | JRAのURL | `"https://www.jra.go.jp"` |
| `headers` | `dict[str, str]` | HTTPリクエストヘッダー | User-Agent設定済み |
| `chrome_driver_path` | `str \| None` | ChromeDriverのパス（`None`の場合はSelenium自動検出） | 環境変数 `CHROME_DRIVER_PATH` または `None` |
| `request_timeout` | `int` | HTTPリクエストのタイムアウト(秒) | `10` |

#### 定数

KeibaAIの`param`で管理されていた以下の定数をライブラリ内に移植する。

- `KEIBAJO_TO_ID_DICT` / `ID_TO_KEIBAJO_DICT`: 競馬場名⇔ID変換辞書
- `GRADE_DICT`: グレード番号⇔グレード名変換辞書
- `WEIGHT_CONDITIONS`: 斤量条件リスト
- `PAYBACK_COLUMNS`: 払い戻し表のカラム名
- `TWO_COMBINATION_BETS` / `THREE_COMBINATION_BETS`: 2連系・3連系馬券の名称リスト
- 各種DataFrameカラム名定義（後述）


### 5.2. `exceptions.py` — 例外クラス

```python
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
```


### 5.3. `race_info.py` — レース情報スクレイピング

KeibaAIの`_scrape_race_info`、`_format_race_info_text`、`_format_race_info_list`に対応する。
スクレイピングロジック（テキスト分割、正規表現による解析等）は`scraping_core.py`と同一にする。

#### 公開関数

##### `scrape_race_info(soup: BeautifulSoup, race_id: str) -> pd.DataFrame`

BeautifulSoupからレースの基本情報を抽出する。KeibaAIの`_scrape_race_info`に対応する。
スクレイパークラスのメソッドから呼び出されることを想定するが、直接呼び出しも可能。

- **引数**:
  - `soup`: 出馬表or結果ページのBeautifulSoupインスタンス
  - `race_id`: netkeibaのレースID（12桁文字列）
- **戻り値**: レース基本情報のDataFrame（1行）
- **カラム**: `RACE_INFO_COLUMNS`に定義（26カラム）

| カラム名 | 型 | 説明 |
|---|---|---|
| レースID | str | レースID |
| 日付 | date | レース開催日 |
| 曜日 | str | 曜日（漢字1文字、例: "日", "土"） |
| レース名 | str | レース名 |
| 発走時刻 | str | 発走時刻（HH:MM形式の文字列） |
| 天候 | str | 天候（"晴"等、不明時は空文字） |
| 馬場 | str | "良","稍","重","不"（不明時は空文字） |
| 芝ダ | str | "芝","ダ","障" |
| 距離 | int | 2000等 |
| 左右 | str | "左","右","直"(該当なしは空文字列) |
| コース | str | "A","B","C","D"(該当なしは空文字列) |
| 内外 | str | "内","外","外-内"(該当なしは空文字列) |
| 競馬場 | str | 競馬場名 |
| 回 | int | 開催回（5等） |
| 開催日 | int | 開催日目（8等） |
| 競争種別 | str | "サラ系３歳以上"等（条件戦の場合） |
| 競争条件 | str | "オープン","２勝クラス","新馬"等 |
| グレード | str | "G1","G2","G3","L","OP","JG1"等（オープン以外は空文字列） |
| 競走記号 | str | "(国際)(指)","(混)[指]"等（括弧付き、なしは空文字列） |
| 重量種別 | str | "定量","別定","ハンデ","馬齢" |
| 頭数 | int | 出走頭数（不明時は0） |
| 1着賞金 | int | 1着賞金（万円、不明時は0） |
| 2着賞金 | int | 2着賞金（万円、不明時は0） |
| 3着賞金 | int | 3着賞金（万円、不明時は0） |
| 4着賞金 | int | 4着賞金（万円、不明時は0） |
| 5着賞金 | int | 5着賞金（万円、不明時は0） |

- **KeibaAIとの差異**:
  - `date_id`引数がない
  - `calc_course_days`による「Xコース何日目」カラムを追加しない
  - soupを外部から受け取る（HTTP取得はスクレイパークラスが担当）
  - **カラム名の変更**: JRA公式名称に統一（条件→競争種別+競争条件、グレード→競争条件、斤量条件→重量種別）
  - **グレードカラムの追加**: 競争条件とは別にグレード（G1/G2等）を格納する独立したカラムを追加。オープンレースの場合のみグレード値が入り、それ以外は空文字列
  - **競走記号カラムの追加**: "(国際)(指)"、"(混)[指]"等の競走記号を格納する新しいカラムを追加
  - **コースカラム分割**: KeibaAIでは「コース」1カラム("左 C"等)だが、keiba-scrapingでは「左右」「コース」「内外」の3カラムに分割。`keiba_utils`の`judge_direction`/`judge_abcd`/`judge_course_inout`と同一ロジック
  - **型の統一**: 左右・コース・内外カラムで該当なしの場合はNaNではなく空文字列（str型）を使用
  - **値・型の変換**: KeibaAIでは文字列のまま保持しているカラムを、keiba-scrapingでは適切な型に変換。発走時刻: "HH:MM発走"→"HH:MM"、距離: "2000m"→2000(int)、回: "5回"→5(int)、開催日: "8日目"→8(int)、賞金: 万円単位のint

- **備考**: soupを直接受け取る設計のため、HTTP取得を行う`scrape_race_info(race_id, ...)`関数は提供しない。HTTP取得はスクレイパークラス（`EntryPageScraper`、`ResultPageScraper`等）が担当する。

#### プライベート関数

scraping_core.pyと同一のロジックを実装する。

- `_extract_date_from_datelist(soup)`: RaceList_DateListのActive要素からレース開催日と曜日を取得
- `_format_race_info_text(race_raw_text)`: テキスト整形（`\xa0`の置換、区切り文字での分割、競走記号・重量種別・頭数・賞金の抽出）
- `_format_race_info_list(race_filtered_list)`: リスト整形（芝ダ・距離・コースの分離、天候・馬場の抽出、障害時の馬場結合等）
- `_build_race_info_dict(race_id, race_info_list, race_date, day_of_week)`: リストからRACE_INFO_COLUMNSに対応するdictに変換。コース生値を左右・コース・内外に分割し、数値文字列をint型に変換
- `_validate_race_info_dict(race_info)`: レース情報辞書の値をスキーマに基づいて検証
- `_update_grade_from_icon(soup, race_info_df)`: RaceNameのグレードアイコンからグレード情報を更新
- `_judge_direction(course)`: コースから左右（方向）を判定（"左","右","直"または空文字列）
- `_judge_abcd(course)`: コースからABCDコースを判定（"A","B","C","D"または空文字列）
- `_judge_course_inout(course)`: コースから内外を判定（"内","外","外-内"または空文字列）


### 5.4. `result_page.py` — レース結果スクレイピング

KeibaAIの`scrape_result_page`、`_scrape_result`、`_scrape_corner`、`_scrape_pay_back`、`_scrape_rap`等に対応する。
スクレイパークラス`ResultPageScraper`内にスクレイピングロジックを直接実装する（独立した`result.py`モジュールは設けない）。

#### スクレイパークラス: `ResultPageScraper`

`result_page.py`に定義。結果ページのHTML取得とBeautifulSoup生成をコンストラクタで行い、各メソッドでテーブルを取得する。

##### コンストラクタ: `__init__(self, race_id: str, config: ScrapingConfig | None = None)`

HTTP取得とBeautifulSoup生成を行う。

- **引数**: `race_id`, `config`
- **例外**: `NetworkError`, `PageNotFoundError`

##### `get_race_info() -> pd.DataFrame`

`race_info.scrape_race_info()` を呼び出してレース基本情報を返す。

##### `get_result() -> pd.DataFrame`

結果ページのHTMLからレース結果テーブルをスクレイピングする。

- **戻り値**: レース結果のDataFrame（RESULT_COLUMNSのカラム）。開催中止の場合はレースID以外がすべてNaNの1行DataFrame
- **カラム**: レースID、出走区分、着順、枠、馬番、馬名、性別、年齢、斤量、騎手、タイム、着差、人気、単勝オッズ、後3F、1コーナー通過順、2コーナー通過順、3コーナー通過順、4コーナー通過順、所属、厩舎、馬体重、増減、馬ID、騎手ID、厩舎ID
- **データ整形**:
  - 性齢を「性別」と「年齢」に分割
  - 馬体重から増減を分離
  - 所属と厩舎の分割
  - コーナー通過順を1〜4コーナーの個別カラムに分割
  - 馬ID、騎手ID、厩舎IDの追加
  - 出走区分（"出走","取消","除外","中止"）の追加

##### `get_corner() -> pd.DataFrame`

結果ページからコーナー通過順位を抽出する。

- **戻り値**: コーナー通過順位のDataFrame（CORNER_COLUMNSのカラム、1行）。直線レースや掛載のないレースではコーナー通過順がすべてNaNの1行DataFrame
- **カラム**: レースID、1コーナー通過順、2コーナー通過順、3コーナー通過順、4コーナー通過順

##### 払い戻しメソッド

各券種ごとに個別のメソッドを提供し、それぞれ横持ち（ワイド）形式の1行DataFrameを返す。同着は3頭まで考慮。

- `get_win_payoff() -> pd.DataFrame`: 単勝払い戻し（WIN_PAYOFF_COLUMNS）
- `get_show_payoff() -> pd.DataFrame`: 複勝払い戻し（SHOW_PAYOFF_COLUMNS）
- `get_bracket_payoff() -> pd.DataFrame`: 枠連払い戻し（BRACKET_PAYOFF_COLUMNS）
- `get_quinella_payoff() -> pd.DataFrame`: 馬連払い戻し（QUINELLA_PAYOFF_COLUMNS）
- `get_quinella_place_payoff() -> pd.DataFrame`: ワイド払い戻し（QUINELLA_PLACE_PAYOFF_COLUMNS）
- `get_exacta_payoff() -> pd.DataFrame`: 馬単払い戻し（EXACTA_PAYOFF_COLUMNS）
- `get_trio_payoff() -> pd.DataFrame`: 3連複払い戻し（TRIO_PAYOFF_COLUMNS）
- `get_trifecta_payoff() -> pd.DataFrame`: 3連単払い戻し（TRIFECTA_PAYOFF_COLUMNS）

各カラム定義は`config.py`で定義。詳細は`SCHEMA.md`を参照。

##### `get_lap_time() -> pd.DataFrame`

HTMLからラップタイムを抽出する（KeibaAIでの`rap`に対応、名前を修正）。

- **戻り値**: ラップタイムのDataFrame（LAP_TIME_COLUMNSのカラム、1行）。障害レースではレースID以外がNaN
- **カラム**: レースID、ペース、100m、200m、...、5000m（100m刻み）


### 5.5. `entry_page.py` — 出馬表スクレイピング

KeibaAIの`scrape_shutuba_page`、`_format_shutuba_df`等に対応する。
スクレイパークラス`EntryPageScraper`内にスクレイピングロジックを直接実装する（独立した`entry.py`モジュールは設けない）。

#### スクレイパークラス: `EntryPageScraper`

`entry_page.py`に定義。出馬表ページのHTML取得とBeautifulSoup生成をコンストラクタで行い、各メソッドでテーブルを取得する。

##### コンストラクタ: `__init__(self, race_id: str, config: ScrapingConfig | None = None)`

HTTP取得とBeautifulSoup生成を行う。

- **引数**: `race_id`, `config`
- **例外**: `NetworkError`, `PageNotFoundError`

##### `get_race_info() -> pd.DataFrame`

`race_info.scrape_race_info()` を呼び出してレース基本情報を返す。

##### `get_entry() -> pd.DataFrame`

出馬表ページのHTMLから出馬表テーブルをスクレイピングする。

- **戻り値**: 出馬表のDataFrame（ENTRY_COLUMNSのカラム）
- **カラム**: レースID、出走区分、枠、馬番、馬名、性別、年齢、斤量、騎手、所属、厩舎、馬体重、増減、馬ID、騎手ID、厩舎ID
- **データ整形**:
  - カラム名の整理
  - 出走区分（"出走","取消","除外"）の追加
  - 馬体重と増減の分離
  - 所属と厩舎の分割
  - 性齢の「性別」「年齢」への分割
  - 馬ID、騎手ID、厩舎IDの追加


### 5.6. `horse.py` — 馬情報・馬柱スクレイピング

KeibaAIの`scrape_horse_info_page`、`scrape_umabashira`に対応する。

#### 公開関数

##### `scrape_horse_info(year: int, page_num: int, session: Session | None = None, config: ScrapingConfig | None = None) -> pd.DataFrame`

指定された年に生まれた競走馬の情報をスクレイピングする。

- **引数**: `year`, `page_num`, `session`（省略時は新規作成）, `config`
- **戻り値**: 競走馬情報のDataFrame
- **カラム**: 馬ID、馬名、性別、所属、厩舎、生年月日、父馬、母馬、母の父、厩舎ID、馬主ID、生産者ID
- **データ整形**: 所属と厩舎の分割等

##### `scrape_past_performances(horse_id: str, config: ScrapingConfig | None = None) -> pd.DataFrame`

馬柱（過去の競走成績）をスクレイピングする（KeibaAIでの`umabashira`に対応）。

- **引数**: `horse_id`, `config`
- **戻り値**: 馬柱のDataFrame
- **カラム**: 日付、競馬場、回、日、R、レース名、天候、頭数、枠番、馬番、オッズ、人気、着順、騎手、斤量、距離、馬場、タイム、着差、通過、ペース、上り、馬体重、増減、勝ち馬(2着馬)、賞金、レースID、主催、間隔
- **データ整形**:
  - 「開催」を「回」「日」「競馬場」に分割
  - 馬体重から増減を分離
  - レースID、主催、間隔の計算・追加
  - 不要カラム（映像、馬場指数等）の削除
- **KeibaAIとの差異**:
  - `日付ID`カラムを追加しない
  - `param.UMABASHIRA_COLUMN`ではなくライブラリ内定義のカラムで並べ替え

##### `scrape_max_page_num(url: str, session: Session | None = None, config: ScrapingConfig | None = None) -> int`

データベースページの最大ページ数を取得する。

- **引数**: `url`, `session`, `config`
- **戻り値**: 最大ページ数

##### `is_race_existence(url: str, session: Session | None = None, config: ScrapingConfig | None = None) -> bool`

レース結果ページが存在するかを判定する。

- **引数**: `url`, `session`, `config`
- **戻り値**: ページが存在すれば`True`


### 5.7. `odds.py` — オッズスクレイピング

KeibaAIの`_scrape_odds_from_netkeiba`、`_scrape_odds_from_jra`に対応する。

#### 公開関数

##### `scrape_odds_from_netkeiba(race_id: str, config: ScrapingConfig | None = None) -> pd.DataFrame`

netkeibaから単勝オッズ・人気をスクレイピングする。

- **引数**: `race_id`, `config`
- **戻り値**: オッズ情報のDataFrame
- **カラム**: 馬番、単勝オッズ、人気、オッズ種別（"予想"または"確定"）

##### `scrape_odds_from_jra(race_id: str, config: ScrapingConfig | None = None) -> pd.DataFrame`

JRAから単勝・複勝オッズをスクレイピングする（async関数）。

- **引数**: `race_id`, `config`
- **戻り値**: オッズ情報のDataFrame
- **カラム**: 馬番、単勝、人気、複勝、複勝min、複勝max、複勝人気


### 5.8. `schedule.py` — レーススケジュール・カレンダー

KeibaAIの`scrape_today_race_info`、`scrape_calender_page`（KeibaAI側の関数名。"calender" は原文ママのタイポ）に対応する。

#### 公開関数

##### `scrape_race_schedule(year: int, month: int, day: int, config: ScrapingConfig | None = None) -> pd.DataFrame`

指定日のレーススケジュールをスクレイピングする（KeibaAIでの`today_race_info`に対応）。

- **引数**: `year`, `month`, `day`, `config`
- **戻り値**: レーススケジュールのDataFrame
- **カラム**: レースID、レース名、競馬場、出走時刻、芝ダ、距離、頭数
- **KeibaAIとの差異**: 日付IDカラムを含まない。ファイルへの保存は行わない

##### `scrape_race_calendar(year: int, page_num: int, session: Session | None = None, config: ScrapingConfig | None = None) -> tuple[pd.DataFrame, list[str]]`

レース一覧ページをスクレイピングする。

- **引数**: `year`, `page_num`, `session`, `config`
- **戻り値**: (レース一覧DataFrame, レースIDリスト)
- **カラム**: 年、月、日、競馬場、回、日目、レースID
- **KeibaAIとの差異**: 日付IDカラムを含まない


### 5.9. `utils.py` — 共通ユーティリティ

ライブラリ内で必要なユーティリティ関数を集約する。KeibaAIの`keiba_utils.py`、`url_builder.py`等から必要な機能のみを移植する。

#### URL構築関数

- `build_race_list_url(year, page_num, config)`: レース一覧ページURL
- `build_today_race_list_url(year, month, day, config)`: 日別レース一覧URL
- `build_result_url(race_id, config)`: 結果ページURL
- `build_entry_url(race_id, config)`: 出馬表ページURL
- `build_horse_info_url(horse_id, config)`: 馬情報ページURL
- `build_horse_list_url(year, page_num, config)`: 競走馬一覧ページURL

#### データ変換関数

- `judge_turf_dirt(text)`: "芝","ダ","障"を判定
- `race_id_to_race_info(race_id)`: レースIDから年・競馬場・回・日・R情報を抽出
- `get_race_info_from_past_performances(df, index)`: 馬柱からレースID等を構築（`get_race_info_from_umabashira`に対応。日付IDは含まない）
- `calc_interval(date1, date2)`: 2つの日付間のレース間隔(日数)を計算
- `set_chrome_options()`: ChromeDriverのオプション設定


## 6. KeibaAIからの移植マッピング

| KeibaAIの関数/概念 | keiba-scrapingの関数/概念 | 変更点 |
|---|---|---|
| `scrape_shutuba_page` | `EntryPageScraper` | スクレイパークラス化、スクレイピングロジックをクラス内に直接実装、馬柱取得を含まない、date_id不使用 |
| `scrape_result_page` | `ResultPageScraper` | スクレイパークラス化、スクレイピングロジックをクラス内に直接実装、date_id不使用 |
| `_scrape_race_info` | `race_info.scrape_race_info` | 公開関数化、soupを外部から受け取る |
| `_scrape_pay_back` | `ResultPageScraper.get_win_payoff()`等 | 券種ごとに個別メソッド化、横持ちDataFrame返却 |
| `scrape_horse_info_page` | `scrape_horse_info` | param不使用 |
| `scrape_umabashira` | `scrape_past_performances` | 日付ID不使用 |
| `scrape_today_race_info` | `scrape_race_schedule` | 日付ID不使用、保存しない |
| `scrape_calender_page`（KeibaAI側の関数名。"calender" は原文ママのタイポ） | `scrape_race_calendar` | 日付ID不使用 |
| `_scrape_odds_from_netkeiba` | `scrape_odds_from_netkeiba` | DataFrame返却 |
| `_scrape_odds_from_jra` | `scrape_odds_from_jra` | 変更なし |
| `update_odds` | （提供しない） | KeibaAIのビジネスロジック |
| `calc_course_days` | （提供しない） | 過去データの蓄積が必要 |
| `date_id` | （使用しない） | KeibaAI固有の概念 |
| `ParamConfig` | `ScrapingConfig` | 最小限の設定のみ |
| `file_io` | （使用しない） | ファイル保存は行わない |


## 7. エラーハンドリング方針

- ネットワークエラー → `NetworkError`を送出
- ページが存在しない → `PageNotFoundError`を送出
- HTML構造が想定と異なる → `ParseError`を送出
- Selenium/Playwrightの起動失敗 → `DriverError`を送出
- 個別関数内での軽微なエラー（カラム欠損等）は可能な限り処理を続行し、NaN等で補完する


## 8. 設計上の注意事項

### 8.1. セッション管理

- `requests.Session`を引数で受け取れるようにし、外部からセッションを再利用可能にする
- 省略時はライブラリ内で新規セッションを作成し、関数終了時にクローズする

### 8.2. Selenium/Playwright

- Selenium（ChromeDriver）は馬柱、レーススケジュール、netkeibaオッズの取得に使用
- Playwright（Chromium）はJRAオッズの取得に使用
- ドライバーのライフサイクルは各関数内で完結させる（起動→操作→終了）

### 8.3. スリープ

- KeibaAIではスクレイピング間のスリープが`scraping_main.py`（呼び出し側）で管理されている
- ライブラリ側では個別関数内にスリープを持たない（Seleniumのページ読み込み待ち等の技術的なスリープを除く）
- 呼び出し側が適切にスリープを挟む責任を持つ

### 8.4. 型アノテーション

- すべての公開関数・プライベート関数に型アノテーションを付与する（PEP8準拠）
- `typing`の使用は最小限にし、`str | None`等のunion型を使用する
