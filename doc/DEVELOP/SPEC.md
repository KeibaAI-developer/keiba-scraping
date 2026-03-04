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
| `PastPerformancesScraper` | `past_performances.py` | 馬情報ページ（馬柱） | `get_past_performances()` |
| `HorseInfoScraper` | `horse_info.py` | 馬情報一覧ページ | `scrape_one_page()`, `get_all_horse_info()` |
| `RaceListScraper` | `race_list.py` | レース一覧ページ | `scrape_one_page()`, `get_race_list()` |
| `RaceScheduleScraper` | `race_schedule.py` | 日別レーススケジュールページ | `get_race_schedule()` |

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
│   ├── past_performances.py  # 馬柱スクレイパークラス（Selenium使用）
│   ├── horse_info.py      # 馬情報スクレイパークラス
│   ├── odds.py            # オッズの抽出・整形
│   ├── race_list.py       # レース一覧スクレイパークラス
│   ├── race_schedule.py   # レーススケジュールスクレイパークラス（Selenium使用）
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
    │   ├── past_performances/
    │   ├── horse_info/
    │   ├── odds/
    │   ├── race_list/
    │   ├── race_schedule/
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


### 5.6. `past_performances.py` — 馬柱スクレイピング

KeibaAIの`scrape_umabashira`に対応する。
スクレイパークラス`PastPerformancesScraper`内にスクレイピングロジックを直接実装する。
ページのレンダリングにSeleniumを使用する。

#### スクレイパークラス: `PastPerformancesScraper`

`past_performances.py`に定義。Seleniumで馬情報ページのHTMLを取得し、馬柱テーブルをスクレイピングする。

##### コンストラクタ: `__init__(self, horse_id: str, config: ScrapingConfig | None = None)`

Seleniumでページを取得しBeautifulSoup生成を行う。

- **引数**: `horse_id`（netkeibaの馬ID、10桁文字列）, `config`
- **例外**: `DriverError`（ChromeDriverの起動・ページ取得に失敗した場合）
- **処理**: `build_horse_info_url`でURL構築 → ChromeDriver起動 → ページ取得（3秒待機） → `page_source`取得 → BeautifulSoup生成

##### `get_past_performances() -> pd.DataFrame`

馬情報ページのHTMLから馬柱テーブルをスクレイピングする。

- **戻り値**: 馬柱のDataFrame（PAST_PERFORMANCES_COLUMNSのカラム）。新馬（戦績なし）の場合は0行のDataFrame
- **カラム**: レースID、日付、競馬場、回、開催日、R、レース名、天候、頭数、枠、馬番、単勝オッズ、人気、着順、騎手、騎手ID、斤量、芝ダ、距離、馬場、タイム、着差、1コーナー通過順、2コーナー通過順、3コーナー通過順、4コーナー通過順、レース前3F、レース後3F、後3F、馬体重、増減、勝ち馬(2着馬)、賞金、主催、間隔日数
- **データ整形**:
  - `pd.read_html()`で馬柱テーブルの基本データを取得
  - 「距離」カラムの分割: "芝1200" → 芝ダ="芝", 距離=1200（int）。種別は"芝","ダ","障"のいずれか
  - 「通過」カラムの分割: "3-4" → 1コーナー通過順〜4コーナー通過順の個別カラム。分割方法は`result_page.py`と同様
  - 「ペース」カラムの分割: "33.1-34.5" → レース前3F=33.1, レース後3F=34.5
  - 騎手IDの追加: HTMLのaタグhrefから抽出（KeibaAIの`scrape_umabashira`にはないロジックを新規実装）
  - レース情報の付加: レースIDから競馬場・回・開催日・R・主催を構築
  - 間隔日数の計算: `calc_interval`で前走からの間隔を算出
- **KeibaAIとのカラム名の差異**:
  - 「日」→「開催日」
  - 「天気」→「天候」
  - 「オッズ」→「単勝オッズ」
  - 「間隔」→「間隔日数」


### 5.7. `horse_info.py` — 馬情報スクレイピング

KeibaAIの`scrape_horse_info_page`に対応する。馬柱スクレイピング（KeibaAIの`scrape_umabashira`に対応）は`past_performances.py`の`PastPerformancesScraper`に実装済みのため、本モジュールでは馬情報のみを扱う。

#### スクレイパークラス: `HorseInfoScraper`

`horse_info.py`に定義。コンストラクタで生年を受け取り、最大ページ数を取得してメンバ変数に保持する。`scrape_one_page()`メソッドで1ページ分の馬情報を取得し、`get_all_horse_info()`メソッドで全ページ分の馬情報を取得する。

##### コンストラクタ: `__init__(self, year: int, session: Session | None = None, config: ScrapingConfig | None = None)`

初期化時に`_scrape_max_page_num`を実行し、最大ページ数をメンバ変数`max_page_num`に保持する。

- 最大ページ数は、ページャーから取得した対象頭数を100頭単位で切り上げて算出する（例: 100頭→1ページ、101頭→2ページ）。

- **引数**: `year`（馬の誕生年）, `session`（省略時は新規作成）, `config`
- **メンバ変数**:
  - `year`: 馬の誕生年
  - `max_page_num`: 競走馬一覧ページの最大ページ数（初期化時に`_scrape_max_page_num`で取得）
  - `session`: HTTPセッション
  - `config`: スクレイピング設定
- **例外**: `NetworkError`, `PageNotFoundError`

##### `scrape_one_page(page_num: int) -> pd.DataFrame`

1ページ分の馬情報をスクレイピングする。

- **引数**: `page_num`（ページ番号）
- **戻り値**: 1ページ分の馬情報DataFrame（HORSE_INFO_COLUMNSのカラム）
- **例外**: `NetworkError`, `ParseError`

##### `get_all_horse_info(sleep: float = 1.0) -> pd.DataFrame`

競走馬一覧ページから全ページ分の馬情報をスクレイピングする。内部で`scrape_one_page()`を全ページ分呼び出す。KeibaAIの`scrape_horse_info_page`と基本的に同じスクレイピングロジック。

- **引数**: `sleep`（連続リクエスト間のスリープ秒数、デフォルト1.0秒）
- **戻り値**: 馬情報のDataFrame（HORSE_INFO_COLUMNSのカラム）
- **カラム**: 馬ID、馬名、性別、生年、所属、厩舎、厩舎ID、父、母、母父、馬主、馬主ID、生産者、生産者ID、総賞金(万円)（15カラム）
- **スクレイピングロジック**（1ページ分の処理）:
  - `pd.read_html()`でテーブルの基本カラム（馬名、性別、厩舎、父、母、母父、馬主、生産者、総賞金）を取得
  - HTMLの`<table class="nk_tb_common race_table_01">`からaタグhrefを解析して各種IDを抽出:
    - 馬ID: 馬名リンクのhrefから10桁IDを抽出
    - 厩舎ID: 厩舎リンクのhrefから5桁IDを抽出（デビュー前はNaN）
    - 馬主ID: 馬主リンクのhrefから6桁IDを抽出
    - 生産者ID: 生産者リンクのhrefから6桁IDを抽出
    - 父ID/母ID/母父ID: 馬一覧テーブルの父/母/母父のリンクは馬検索URLであり馬IDを含まないため取得不可
  - 馬一覧テーブルの行に期待列数が不足している場合は、HTML構造変更とみなして`ParseError`を送出する
  - 馬IDリンクが存在しない場合、馬IDは文字列`"nan"`に変換せずNaNのまま保持する
  - 厩舎カラムを所属と厩舎に分割（"[西]友道康夫" → 所属="栗東", 厩舎="友道康夫"）
  - 所属の値を変換: "東"→"美浦"、"西"→"栗東"、"地"→"地方"、"外"→"海外"
  - 生年はコンストラクタの`year`引数から取得
  - 総賞金はテーブルから万円単位のintとして取得
- **KeibaAIとの差異**:
  - コンストラクタで最大ページ数を自動取得しメンバ変数に保持（`_scrape_max_page_num`はプライベート）
  - `scrape_one_page()`をパブリックメソッドとして提供（1ページ単位での取得・テストが可能）
  - `get_all_horse_info()`の`sleep`引数でリクエスト間隔を制御（`ScrapingConfig`に`request_interval`は持たない）
  - 所属の値を変換（KeibaAIでは"東","西","地","外"の略称のまま保持）
  - 総賞金を追加（KeibaAIでは取得していない）
  - 父ID・母ID・母父IDは非対応（馬一覧テーブルの父/母/母父リンクが馬検索URLのため抽出不可）
  - 生年カラムを追加（KeibaAIでは引数のyearから暗黙的に把握、カラムとしては持っていない）
  - `param`不使用、`ScrapingConfig`を使用
  - `session`を省略可能（省略時は新規作成）


### 5.8. `odds.py` — オッズスクレイピング

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


### 5.9. `race_list.py` — レース一覧スクレイピング

KeibaAIの`scrape_calender_page`（KeibaAI側の関数名。"calender" は原文ママのタイポ）に対応する。
スクレイパークラス`RaceListScraper`内にスクレイピングロジックを直接実装する。

#### スクレイパークラス: `RaceListScraper`

`race_list.py`に定義。コンストラクタで取得したい年を受け取り、最大ページ数を取得してメンバ変数に保持する。`scrape_one_page()`メソッドで指定ページのレース一覧を取得し、`get_race_list()`メソッドで全ページ分のレース一覧を取得する。

##### コンストラクタ: `__init__(self, year: int, session: Session | None = None, config: ScrapingConfig | None = None)`

初期化時に`_scrape_max_page_num`を実行し、最大ページ数をメンバ変数`max_page_num`に保持する。

- **引数**: `year`（取得対象年）, `session`（省略時は新規作成）, `config`
- **メンバ変数**:
  - `year`: 取得対象年
  - `max_page_num`: レース一覧ページの最大ページ数（初期化時に取得）
  - `session`: HTTPセッション
  - `config`: スクレイピング設定
- **例外**: `NetworkError`, `PageNotFoundError`

##### `scrape_one_page(page_num: int) -> pd.DataFrame`

指定ページのレース一覧をスクレイピングする。

- **引数**: `page_num`（ページ番号）
- **戻り値**: 1ページ分のレース一覧DataFrame（RACE_LIST_COLUMNSのカラム、最大100行）
- **例外**: `NetworkError`, `ParseError`
- **スクレイピングロジック**:
  - `build_race_list_url`でURL構築 → HTTP取得 → BeautifulSoup生成
  - `<table class="nk_tb_common race_table_01">`のtdからレース情報を抽出
  - 各行（レース）からレースID、日付、競馬場、回、開催日、天候、R、レース名、芝ダ、距離、頭数、馬場、タイム、レース前3F、レース後3F、勝ち馬、勝ち馬ID、騎手、騎手ID、所属、厩舎、厩舎ID、2着馬、2着馬ID、3着馬、3着馬IDを抽出
  - レースIDからrace_id_to_race_infoで競馬場・回・開催日・Rを構築

##### `get_race_list(sleep: float = 1.0) -> pd.DataFrame`

指定年の全ページ分のレース一覧を取得する。内部で`scrape_one_page()`を全ページ分呼び出す。

- **引数**: `sleep`（連続リクエスト間のスリープ秒数、デフォルト1.0秒）
- **戻り値**: レース一覧のDataFrame（RACE_LIST_COLUMNSのカラム）
- **カラム**: SCHEMA.mdのレース一覧スキーマに準拠（26カラム）

##### プライベートメソッド

- `_scrape_max_page_num()`: レース一覧ページの最大ページ数を取得。ページャーから全件数を取得し、100件単位で切り上げて算出

- **KeibaAIとの差異**:
  - スクレイパークラス化（KeibaAIでは関数`scrape_calender_page`）
  - `date_id`カラムを含まない
  - KeibaAIでは「年」「月」「日」「競馬場」「回」「日目」「レースID」の7カラムだったが、SCHEMA.mdに準拠した26カラムに拡張
  - `param`不使用、`ScrapingConfig`を使用
  - `session`を省略可能（省略時は新規作成）
  - 最大ページ数をコンストラクタで自動取得
  - `scrape_one_page()`をパブリックメソッドとして提供（1ページ単位での取得が可能）
  - レースIDリストは戻り値に含まない（DataFrameのレースIDカラムから取得可能）


### 5.10. `race_schedule.py` — レーススケジュールスクレイピング

KeibaAIの`scrape_today_race_info`に対応する。
スクレイパークラス`RaceScheduleScraper`内にスクレイピングロジックを直接実装する。
ページのレンダリングにSeleniumを使用する。

#### スクレイパークラス: `RaceScheduleScraper`

`race_schedule.py`に定義。コンストラクタで日付を受け取り、SeleniumでページのHTMLを取得する。`get_race_schedule()`メソッドでレーススケジュールを取得する。

##### コンストラクタ: `__init__(self, year: int, month: int, day: int, config: ScrapingConfig | None = None)`

Seleniumでページを取得しHTMLを保持する。

- **引数**: `year`, `month`, `day`, `config`
- **例外**: `DriverError`（ChromeDriverの起動・ページ取得に失敗した場合）
- **処理**: `build_today_race_list_url`でURL構築 → ChromeDriver起動 → ページ取得 → HTML保持

##### `get_race_schedule() -> pd.DataFrame`

日別レーススケジュールページのHTMLからレーススケジュールを抽出する。

- **戻り値**: レーススケジュールのDataFrame（RACE_SCHEDULE_COLUMNSのカラム）。開催のない日は0行のDataFrame
- **カラム**: SCHEMA.mdのレーススケジュールスキーマに準拠（12カラム）
- **スクレイピングロジック**:
  - `RaceList_DataItem`からレースIDを抽出（aタグhrefの`race_id=(\d{12})`部分）
  - `RaceList_ItemTitle`からレース名を抽出
  - `RaceData`から発走時刻、芝ダ、距離、頭数を正規表現`^(\d{1,2}):(\d{2}) .*?(\d+)m (\d+)頭`で抽出
  - レースIDからrace_id_to_race_infoで競馬場・回・開催日・Rを構築
  - 芝ダは`judge_turf_dirt`で判定
  - 日付はコンストラクタの`year`, `month`, `day`から`datetime.date`として構築
  - 馬場はページから取得（取得可能な場合）
  - 発走時刻は`str`型（HH:MM形式）

- **KeibaAIとの差異**:
  - スクレイパークラス化（KeibaAIでは関数`scrape_today_race_info`）
  - `date_id`カラムを含まない
  - KeibaAIでは「レースID」「日付ID」「レース名」「競馬場」「出走時刻」「芝ダ」「距離」「頭数」の8カラムだったが、SCHEMA.mdに準拠した12カラムに拡張
  - 発走時刻は`str`型（HH:MM形式）
  - ファイルへの保存は行わない
  - `param`不使用、`ScrapingConfig`を使用


### 5.11. `utils.py` — 共通ユーティリティ

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
- `is_race_existence(url, session, config)`: レース結果ページが存在するかを判定


## 6. KeibaAIからの移植マッピング

| KeibaAIの関数/概念 | keiba-scrapingの関数/概念 | 変更点 |
|---|---|---|
| `scrape_shutuba_page` | `EntryPageScraper` | スクレイパークラス化、スクレイピングロジックをクラス内に直接実装、馬柱取得を含まない、date_id不使用 |
| `scrape_result_page` | `ResultPageScraper` | スクレイパークラス化、スクレイピングロジックをクラス内に直接実装、date_id不使用 |
| `_scrape_race_info` | `race_info.scrape_race_info` | 公開関数化、soupを外部から受け取る |
| `_scrape_pay_back` | `ResultPageScraper.get_win_payoff()`等 | 券種ごとに個別メソッド化、横持ちDataFrame返却 |
| `scrape_horse_info_page` | `HorseInfoScraper` | スクレイパークラス化、param不使用、コンストラクタで最大ページ数を自動取得、所属値変換（東→美浦等）、総賞金・生年を追加（父ID・母ID・母父IDは馬一覧テーブルから取得不可のため非対応） |
| `scrape_max_page_num` | `HorseInfoScraper._scrape_max_page_num` | プライベート化、コンストラクタから内部的に呼び出し |
| `is_race_existence` | `utils.is_race_existence` | utils.pyに移動 |
| `scrape_umabashira` | `PastPerformancesScraper` | スクレイパークラス化、日付ID不使用、カラム名変更（日→開催日、天気→天候、オッズ→単勝オッズ、間隔→間隔日数）、距離を芝ダと距離(int)に分割、通過を1〜4コーナー通過順に分割、ペースをレース前3F・レース後3Fに分割、騎手ID追加 |
| `scrape_today_race_info` | `RaceScheduleScraper` | スクレイパークラス化、日付ID不使用、保存しない、発走時刻はstr型、SCHEMA.mdに準拠した12カラムに拡張 |
| `scrape_calender_page`（KeibaAI側の関数名。"calender" は原文ママのタイポ） | `RaceListScraper` | スクレイパークラス化、日付ID不使用、SCHEMA.mdに準拠した26カラムに拡張、最大ページ数を自動取得、scrape_one_page()をパブリック提供 |
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
- （`horse_info.py`）馬一覧テーブルの列数不足など、復旧不能な構造不整合は`ParseError`を送出
- Selenium/Playwrightの起動失敗 → `DriverError`を送出
- 個別関数内での軽微なエラー（カラム欠損等）は可能な限り処理を続行し、NaN等で補完する


## 8. 設計上の注意事項

### 8.1. セッション管理

- `requests.Session`を引数で受け取れるようにし、外部からセッションを再利用可能にする
- 省略時はライブラリ内で新規セッションを作成し、関数終了時にクローズする

### 8.2. Selenium/Playwright

- Selenium（ChromeDriver）は馬柱、レーススケジュール（`race_schedule.py`）、netkeibaオッズの取得に使用
- Playwright（Chromium）はJRAオッズの取得に使用
- ドライバーのライフサイクルは各関数内で完結させる（起動→操作→終了）

### 8.3. スリープ

- KeibaAIではスクレイピング間のスリープが`scraping_main.py`（呼び出し側）で管理されている
- ライブラリ側では個別関数内にスリープを持たない（Seleniumのページ読み込み待ち等の技術的なスリープを除く）
- 呼び出し側が適切にスリープを挟む責任を持つ

### 8.4. 型アノテーション

- すべての公開関数・プライベート関数に型アノテーションを付与する（PEP8準拠）
- `typing`の使用は最小限にし、`str | None`等のunion型を使用する
