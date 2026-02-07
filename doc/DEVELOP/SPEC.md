# keiba-scraping 機能仕様書

## 1. 概要

`keiba-scraping`は、netkeibaおよびJRAの公式サイトから競馬データをスクレイピングし、`pandas.DataFrame`として返すPythonライブラリである。KeibaAIプロジェクトから純粋なスクレイピング機能のみを抽出し、KeibaAIへの依存を排除した独立したライブラリとして実装する。

### 1.1. 設計方針

- **KeibaAIとの依存排除**: `param`、`modules.utils`（`file_io`、`keiba_utils`等）に依存しない
- **データ取得のみ**: CSVファイルへの保存機能は持たない。データフレームを返すのみ
- **date_id不使用**: KeibaAI固有の日付ID概念は使用しない
- **コース何日目不使用**: 過去データの蓄積が必要な `calc_course_days` はライブラリに含めない
- **データ整形は維持**: スクレイピングで取得したデータの整形処理（カラム名変更、型変換、分割等）は残す
- **mykeibadb-pythonを参考**: ライブラリ構成・テスト構成・pyproject.tomlの設計を参考にする


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
│   ├── race_info.py       # レース情報のスクレイピング
│   ├── result.py          # レース結果のスクレイピング
│   ├── entry.py           # 出馬表のスクレイピング
│   ├── horse.py           # 馬情報・馬柱のスクレイピング
│   ├── odds.py            # オッズのスクレイピング
│   ├── schedule.py        # レーススケジュール・カレンダーのスクレイピング
│   ├── utils.py           # ライブラリ内共通ユーティリティ
│   └── py.typed
└── test/
    ├── __init__.py
    ├── conftest.py
    ├── unit/
    │   ├── __init__.py
    │   ├── race_info/
    │   ├── result/
    │   ├── entry/
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
| `chrome_driver_path` | `str` | ChromeDriverのパス | `"/usr/bin/chromedriver"` |
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

KeibaAIの`_scrape_race_info`、`_format_race_info_text`、`_format_race_info_list`、`scrape_race_info`に対応する。

#### 公開関数

##### `scrape_race_info(race_id: str, config: ScrapingConfig | None = None) -> pd.DataFrame`

レースの基本情報をスクレイピングする。

- **引数**:
  - `race_id`: netkeibaのレースID（12桁文字列）
  - `config`: 設定オブジェクト（省略時はデフォルト設定）
- **戻り値**: レース基本情報のDataFrame（1行）
- **カラム**:

| カラム名 | 型 | 説明 |
|---|---|---|
| レースID | str | レースID |
| レース名 | str | レース名 |
| 発走時刻 | str | "HH:MM発走" |
| 天気 | str | 天気（不明時は空文字） |
| 馬場 | str | "良","稍","重","不"（不明時は空文字） |
| 芝ダ | str | "芝","ダ","障" |
| 距離 | str | "2000m"等 |
| コース | str | "右 外 B"等 |
| 競馬場 | str | 競馬場名 |
| 条件 | str | "3歳以上 オープン"等 |
| 頭数 | str | 出走頭数 |
| グレード | str | グレード |
| 斤量条件 | str | 斤量条件 |

- **KeibaAIとの差異**:
  - `date_id`引数がない
  - `calc_course_days`による「Xコース何日目」カラムを追加しない
  - `param`ではなく`config`を使用

#### プライベート関数

- `_scrape_race_info(soup, race_id, config)`: BeautifulSoupから情報を抽出
- `_format_race_info_text(race_raw_text, config)`: テキスト整形
- `_format_race_info_list(race_filtered_list)`: リスト整形


### 5.4. `result.py` — レース結果スクレイピング

KeibaAIの`scrape_result_page`、`_scrape_result`、`_scrape_corner`、`_scrape_pay_back`、`_scrape_rap`等に対応する。

#### 公開関数

##### `scrape_result(race_id: str, config: ScrapingConfig | None = None) -> pd.DataFrame`

レース結果の表をスクレイピングする。

- **引数**: `race_id`, `config`
- **戻り値**: レース結果のDataFrame
- **カラム**: 着順、枠番、馬番、馬名、性齢、斤量、騎手、タイム、着差、通過、上り、馬体重、増減、所属、厩舎、単勝オッズ、人気、馬ID、騎手ID、厩舎ID、性別、齢
- **データ整形**:
  - 性齢を「性別」と「齢」に分割
  - 馬体重から増減を分離
  - 所属と厩舎の分割
  - 馬ID、騎手ID、厩舎IDの追加

##### `scrape_corner(race_id: str, config: ScrapingConfig | None = None) -> pd.DataFrame`

コーナー通過順位をスクレイピングする。

- **引数**: `race_id`, `config`
- **戻り値**: コーナー通過順位のDataFrame（直線レースの場合は空のDataFrame）
- **カラム**: コーナー（1〜4コーナー）、通過順

##### `scrape_payoff(race_id: str, config: ScrapingConfig | None = None) -> pd.DataFrame`

払い戻し情報をスクレイピングする（KeibaAIでの`pay_back`に対応）。

- **引数**: `race_id`, `config`
- **戻り値**: 払い戻しのDataFrame
- **カラム**: 券種、馬番、払戻、人気
- **データ整形**: 2連系・3連系のハイフン結合、複数的中の展開等の整形処理を維持

##### `scrape_lap_time(race_id: str, config: ScrapingConfig | None = None) -> pd.DataFrame`

ラップタイムをスクレイピングする（KeibaAIでの`rap`に対応、名前を修正）。

- **引数**: `race_id`, `config`
- **戻り値**: ラップタイムのDataFrame（障害レースの場合は空のDataFrame）
- **カラム**: ラップタイム、ペース

##### `scrape_result_page(race_id: str, config: ScrapingConfig | None = None) -> dict[str, pd.DataFrame]`

結果ページの全データを一括取得する。

- **引数**: `race_id`, `config`
- **戻り値**: キーが`"race_info"`, `"result"`, `"corner"`, `"payoff"`, `"lap_time"`の辞書
- **備考**: 内部で`scrape_race_info`、`scrape_result`、`scrape_corner`、`scrape_payoff`、`scrape_lap_time`を呼び出す


### 5.5. `entry.py` — 出馬表スクレイピング

KeibaAIの`scrape_shutuba_page`、`_format_shutuba_df`等に対応する。

#### 公開関数

##### `scrape_entry(race_id: str, config: ScrapingConfig | None = None) -> pd.DataFrame`

出馬表をスクレイピングする（KeibaAIでの`shutuba`に対応）。

- **引数**: `race_id`, `config`
- **戻り値**: 出馬表のDataFrame
- **カラム**: 枠、馬番、馬名、性齢、斤量、騎手、厩舎、所属、馬体重、増減、単勝オッズ、人気、馬ID、騎手ID、厩舎ID、性別、齢
- **データ整形**:
  - カラム名の整理
  - 馬体重と増減の分離
  - 性齢の分割
  - 馬ID、騎手ID、厩舎IDの追加

##### `scrape_entry_page(race_id: str, config: ScrapingConfig | None = None) -> dict[str, pd.DataFrame]`

出馬表ページの全データを一括取得する。

- **引数**: `race_id`, `config`
- **戻り値**: キーが`"race_info"`, `"entry"`の辞書


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
- **カラム**: 日付、競馬場、回、日、R、レース名、天気、頭数、枠番、馬番、オッズ、人気、着順、騎手、斤量、距離、馬場、タイム、着差、通過、ペース、上り、馬体重、増減、勝ち馬(2着馬)、賞金、レースID、主催、間隔
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

KeibaAIの`scrape_today_race_info`、`scrape_calender_page`に対応する。

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
| `scrape_shutuba_page` | `scrape_entry_page` | 馬柱取得を含まない、date_id不使用 |
| `scrape_result_page` | `scrape_result_page` | date_id不使用、dict形式で返す |
| `scrape_horse_info_page` | `scrape_horse_info` | param不使用 |
| `scrape_umabashira` | `scrape_past_performances` | 日付ID不使用 |
| `scrape_today_race_info` | `scrape_race_schedule` | 日付ID不使用、保存しない |
| `scrape_calender_page` | `scrape_race_calendar` | 日付ID不使用 |
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
