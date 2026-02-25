# keiba-scraping 実装計画書

本書はSPEC.mdに基づき、keiba-scrapingライブラリの実装をPR単位で分割した計画書である。
各PRはレビュー可能なサイズに分割し、テスト計画も含む。


## PR一覧

| PR番号 | タイトル | 依存PR | 見積もり | 状態 |
|--------|---------|--------|---------|------|
| PR-1 | プロジェクト基盤の構築 | なし | 小 | 完了 |
| PR-2 | 設定・例外・ユーティリティの実装 | PR-1 | 中 | 完了 |
| PR-3 | レース情報スクレイピングの実装 | PR-2 | 中 | 完了 |
| PR-4 | レース結果スクレイピングの実装 | PR-3 | 大 | 完了 |
| PR-5 | 出馬表スクレイピングの実装 | PR-3 | 中 | 完了 |
| PR-6 | 馬柱スクレイピングの実装 | PR-2 | 中 | 未着手 |
| PR-7 | オッズスクレイピングの実装 | PR-2 | 中 | 未着手 |
| PR-8 | レーススケジュール・カレンダーの実装 | PR-2 | 中 | 未着手 |
| PR-9 | 馬情報スクレイピング・HorsePageScraperクラスの実装 | PR-6 | 大 | 未着手 |
| PR-10 | 一括取得関数とREADME・サンプルコードの整備 | PR-6〜9 | 小 | 未着手 |


---


## PR-1: プロジェクト基盤の構築

### 概要

ライブラリとしてのプロジェクト骨格を構築する。

### 作業内容

1. `pyproject.toml`の作成
   - mykeibadb-pythonを参考に、ビルド設定・依存関係・ツール設定を記載
   - `[tool.black]`, `[tool.isort]`, `[tool.mypy]`, `[tool.pytest.ini_options]`を設定
2. `.gitignore`の作成
3. `scraping/__init__.py`の作成（空ファイル、後のPRで`__all__`を追加）
4. `scraping/py.typed`の作成（PEP 561対応）
5. `test/__init__.py`、`test/conftest.py`の作成
6. `test/unit/__init__.py`、`test/integration/__init__.py`の作成
7. `.github/workflows/ci.yml`の作成
   - isort、flake8、mypy、pytestの実行

### 成果物

```
keiba-scraping/
├── pyproject.toml
├── .gitignore
├── .github/workflows/ci.yml
├── scraping/
│   ├── __init__.py
│   └── py.typed
└── test/
    ├── __init__.py
    ├── conftest.py
    ├── unit/
    │   └── __init__.py
    └── integration/
        └── __init__.py
```

### テスト計画

- CIが正常に動作することを手動で確認


---


## PR-2: 設定・例外・ユーティリティの実装

### 概要

ライブラリ内の全モジュールが共通で使用する設定管理、例外クラス、ユーティリティ関数を実装する。

### 作業内容

1. `scraping/config.py`の実装
   - `ScrapingConfig`データクラス
   - `KEIBAJO_TO_ID_DICT` / `ID_TO_KEIBAJO_DICT`
   - `GRADE_DICT`
   - `WEIGHT_CONDITIONS`
   - `PAYBACK_COLUMNS`
   - `TWO_COMBINATION_BETS` / `THREE_COMBINATION_BETS`
   - 各種DataFrameカラム名定義
2. `scraping/exceptions.py`の実装
   - `ScrapingError`, `PageNotFoundError`, `ParseError`, `NetworkError`, `DriverError`
3. `scraping/utils.py`の実装
   - URL構築関数（`build_*_url`系）
   - `judge_turf_dirt`
   - `race_id_to_race_info`
   - `get_race_info_from_past_performances`
   - `calc_interval`
   - `set_chrome_options`
4. `scraping/__init__.py`の更新（公開APIのエクスポート追加）

### テスト計画

#### 単体テスト

| テストファイル | テスト対象 | ケース |
|---|---|---|
| `test/unit/config/test_scraping_config.py` | `ScrapingConfig` | 正常系: デフォルト値確認、カスタム値設定 |
| `test/unit/config/test_constants.py` | 定数辞書 | 正常系: 辞書の整合性確認（ID⇔競馬場の双方向変換） |
| `test/unit/utils/test_build_urls.py` | URL構築関数 | 正常系: 各URL構築関数の出力確認 |
| `test/unit/utils/test_judge_turf_dirt.py` | `judge_turf_dirt` | 正常系: "芝","ダ","障"の判定 / 準正常系: 不明な文字列 |
| `test/unit/utils/test_race_id_to_race_info.py` | `race_id_to_race_info` | 正常系: レースIDから各情報の抽出 |
| `test/unit/utils/test_get_race_info_from_past_performances.py` | `get_race_info_from_past_performances` | 正常系: 中央/地方/海外の各ケース / 準正常系: 空の馬柱 |
| `test/unit/utils/test_calc_interval.py` | `calc_interval` | 正常系: 間隔計算 / 準正常系: 同日のレース |
| `test/unit/utils/test_set_chrome_options.py` | `set_chrome_options` | 正常系: オプション設定確認 |


---


## PR-3: レース情報スクレイピングの実装

### 概要

`scraping/race_info.py`を実装する。KeibaAIの`_scrape_race_info`系の機能を移植する。
スクレイピングロジック（テキスト分割、正規表現による解析等）は`scraping_core.py`と同一にする。
KeibaAIとの依存を切りリファクタリングは行うが、スクレイピング自体の処理は変えない。

### 作業内容

1. `scraping/race_info.py`の実装
   - `scrape_race_info(soup, race_id)`: 公開関数（旧`_scrape_race_info`）
   - `_format_race_info_text(race_raw_text)`: テキスト整形（scraping_coreと同一ロジック。競走記号・重量種別・頭数・賞金を抽出）
   - `_format_race_info_list(race_filtered_list)`: リスト整形（scraping_coreと同一ロジック）
   - `_build_race_info_dict(race_id, race_info_list)`: RACE_INFO_COLUMNSへのマッピング。コース生値を左右・コース・内外に分割
   - `_update_grade_from_icon(soup, race_info_df)`: グレードアイコンからの更新（グレードカラムに格納）
   - `_judge_direction(course)`: コースから左右を判定
   - `_judge_abcd(course)`: コースからABCDコースを判定
   - `_judge_course_inout(course)`: コースから内外を判定
   - ※ soupの取得から行う旧`scrape_race_info(race_id, config)`関数は実装しない
2. `scraping/__init__.py`の更新
3. `scraping/config.py`の`RACE_INFO_COLUMNS`を現在の仕様に合わせて更新（26カラム）
   - **カラム名の変更**: JRA公式名称に統一（条件→競走種別+競走条件、グレード→競走条件、斤量条件→重量種別）、「天気」→「天候」（netkeibaの表示に合わせる）、「発走時刻」で統一（KeibaAI側は「発走時間」使用だが将来的に統一予定）
   - **グレードカラムの追加**: 競走条件とは別にグレード（G1/G2等）を格納する独立したカラムを追加。オープンレースの場合のみグレード値が入り、それ以外は空文字列
   - **競走記号カラムの追加**: "(国際)(指)"、"(混)[指]"等の競走記号を格納する新しいカラムを追加（なしは空文字列）
   - **コースカラム分割**: KeibaAIの「コース」1カラムを「左右」「コース」「内外」の3カラムに分割。`keiba_utils`の`judge_direction`/`judge_abcd`/`judge_course_inout`と同一ロジックを使用
   - **型の統一**: 左右・コース・内外カラムで該当なしの場合はNaNではなく空文字列（str型）を使用
   - **値・型の変換**: 発走時刻("HH:MM発走"→"HH:MM")、距離("2000m"→2000 int)、回("5回"→5 int)、開催日("8日目"→8 int)、賞金（万円単位のint）を適切な型に変換

### テスト計画

#### テスト用HTMLフィクスチャの作成

`config/test/test_case.yml`に定義されている各種レースIDに対して、出馬表ページと結果ページのHTMLを
pythonのrequestsでスクレイピングし、`test/fixtures/html/`に保存する。

- フィクスチャの取得は`test/scripts/fetch_fixtures.py`スクリプトで行う
- 取得したHTMLはUTF-8に変換して保存する
- 地方競馬（JavaScriptで動的にレンダリングされるページ）はrequestsでは取得できないためスキップする
- フィクスチャHTMLはPR-3で最初に作成し、以降のPRでも共用する

##### フィクスチャファイル命名規則

```
test/fixtures/html/
├── entry_{race_id}.html        # 出馬表ページ
└── result_{race_id}.html       # 結果ページ
```

##### 対象レースID（test_case.ymlより抜粋）

正常系・準正常系のレースIDのうち、中央競馬のレースを対象とする。

#### 単体テスト

HTMLフィクスチャからBeautifulSoupを生成し、パブリック関数`scrape_race_info`をテストする。
プライベートメソッドのテストは行わない。

| テストファイル | テスト対象 | ケース |
|---|---|---|
| `test/unit/race_info/test_scrape_race_info.py` | `scrape_race_info` | test_case.ymlの各レースに対して、フィクスチャHTMLからレース情報が正しく抽出されることを確認。カラム構成、主要な値（レース名、芝ダ、距離、競馬場等）の検証 |

テストでは以下のようなパターンを網羅する:
- G1〜G3、リステッド、オープン、各クラスのレース（グレード判定）
- 障害レース
- ダートレース
- 1000直
- 出走取消・競走除外のあるレース
- 出馬表ページ / 結果ページの両方

#### 結合テスト

フィクスチャは使用せず、実際にnetkeibaにアクセスしてスクレイピングを行いテストする。
これはnetkeibaのHTML構造の仕様変更に気づきやすくするのが目的。

| テストファイル | テスト対象 | ケース |
|---|---|---|
| `test/integration/test_race_info.py` | `scrape_race_info` | 実際にnetkeibaから出馬表/結果ページを取得し、scrape_race_infoが正しく動作することを確認 |

> **注意**: 結合テストはネットワーク接続が必要なため、CIではマーカーでスキップ可能にする。

---


## PR-4: レース結果スクレイピングの実装

### 概要

`scraping/result_page.py`を実装する。KeibaAIの結果関連スクレイピング機能を移植する。
スクレイピングロジックは`scraping_core.py`と同一にする。
`ResultPageScraper`クラス内にスクレイピングロジックを直接実装する（独立した`result.py`モジュールは設けない）。

### 作業内容

1. `scraping/result_page.py`の実装
   - `ResultPageScraper`クラス
   - `__init__(race_id, config)`: HTTP取得、soup生成
   - `get_race_info()`: `race_info.scrape_race_info()`を呼び出し
   - `get_result()`: レース結果テーブルの取得（RESULT_COLUMNSのカラム）
   - `get_corner()`: コーナー通過順の取得（CORNER_COLUMNSのカラム）
   - `get_win_payoff()`: 単勝払い戻し（WIN_PAYOFF_COLUMNS）
   - `get_show_payoff()`: 複勝払い戻し（SHOW_PAYOFF_COLUMNS）
   - `get_bracket_payoff()`: 枠連払い戻し（BRACKET_PAYOFF_COLUMNS）
   - `get_quinella_payoff()`: 馬連払い戻し（QUINELLA_PAYOFF_COLUMNS）
   - `get_quinella_place_payoff()`: ワイド払い戻し（QUINELLA_PLACE_PAYOFF_COLUMNS）
   - `get_exacta_payoff()`: 馬単払い戻し（EXACTA_PAYOFF_COLUMNS）
   - `get_trio_payoff()`: 3連複払い戻し（TRIO_PAYOFF_COLUMNS）
   - `get_trifecta_payoff()`: 3連単払い戻し（TRIFECTA_PAYOFF_COLUMNS）
   - `get_lap_time()`: ラップタイム（LAP_TIME_COLUMNS）
   - プライベート関数: `_classify_race_status`, `_add_gender_age`, `_add_id_from_table`, `_split_corner_passing_order`, `_validate_result`, `_parse_haraimodoshi_text`, `_parse_ninki_text`, `_parse_umaban_groups`, `_build_payoff_wide_df`等
2. `scraping/config.py`に以下の定数を追加
   - `RESULT_COLUMNS`, `CORNER_COLUMNS`, `LAP_TIME_COLUMNS`
   - 各券種の払い戻しカラム定義（`WIN_PAYOFF_COLUMNS`〜`TRIFECTA_PAYOFF_COLUMNS`）
   - `VALID_RACE_STATUSES`, `NON_NAN_COLUMNS`, `VALID_GENDERS`, `VALID_AFFILIATIONS`
3. `scraping/__init__.py`の更新

### テスト計画

#### 単体テスト

PR-3で作成したフィクスチャHTMLを使用し、`ResultPageScraper`のパブリックメソッドをテストする。
requestsをモックし、フィクスチャHTMLを返すようにしてテスト。
プライベートメソッドのテストは行わない。

| テストファイル | テスト対象 | ケース |
|---|---|---|
| `test/unit/result_page/test_get_result.py` | `ResultPageScraper.get_result` | 各種レースのフィクスチャHTMLからの結果表抽出。カラム構成、着順、馬名等の検証 |
| `test/unit/result_page/test_get_corner.py` | `ResultPageScraper.get_corner` | コーナー通過順の抽出。直線レース（アイビスSD）ではNaN |
| `test/unit/result_page/test_get_win_payoff.py` | `ResultPageScraper.get_win_payoff` | 単勝払い戻しの抽出 |
| `test/unit/result_page/test_get_show_payoff.py` | `ResultPageScraper.get_show_payoff` | 複勝払い戻しの抽出 |
| `test/unit/result_page/test_get_bracket_payoff.py` | `ResultPageScraper.get_bracket_payoff` | 枠連払い戻しの抽出 |
| `test/unit/result_page/test_get_quinella_payoff.py` | `ResultPageScraper.get_quinella_payoff` | 馬連払い戻しの抽出 |
| `test/unit/result_page/test_get_quinella_place_payoff.py` | `ResultPageScraper.get_quinella_place_payoff` | ワイド払い戻しの抽出 |
| `test/unit/result_page/test_get_exacta_payoff.py` | `ResultPageScraper.get_exacta_payoff` | 馬単払い戻しの抽出 |
| `test/unit/result_page/test_get_trio_payoff.py` | `ResultPageScraper.get_trio_payoff` | 3連複払い戻しの抽出 |
| `test/unit/result_page/test_get_trifecta_payoff.py` | `ResultPageScraper.get_trifecta_payoff` | 3連単払い戻しの抽出 |
| `test/unit/result_page/test_get_lap_time.py` | `ResultPageScraper.get_lap_time` | ラップタイムの抽出。平地/直線/障害の各パターン |

#### 結合テスト

| テストファイル | テスト対象 | ケース |
|---|---|---|
| `test/integration/test_result_page.py` | `ResultPageScraper` | 実際にnetkeibaにアクセスしてテスト |


---


## PR-5: 出馬表スクレイピングの実装

### 概要

`scraping/entry_page.py`を実装する。KeibaAIの出馬表関連スクレイピング機能を移植する。
スクレイピングロジックは`scraping_core.py`と同一にする。
`EntryPageScraper`クラス内にスクレイピングロジックを直接実装する（独立した`entry.py`モジュールは設けない）。

### 作業内容

1. `scraping/entry_page.py`の実装
   - `EntryPageScraper`クラス
   - `__init__(race_id, config)`: HTTP取得、soup生成
   - `get_race_info()`: `race_info.scrape_race_info()`を呼び出し
   - `get_entry()`: 出馬表テーブルの取得（ENTRY_COLUMNSのカラム）
   - プライベート関数: `_classify_entry_status`, `_add_id_from_table`, `_add_gender_age`, `_validate_entry`
2. `scraping/config.py`に以下の定数を追加
   - `ENTRY_COLUMNS`, `ENTRY_NON_NAN_COLUMNS`, `VALID_ENTRY_STATUSES`, `SHUTUBA_RAW_COLUMNS`
3. `scraping/__init__.py`の更新

### テスト計画

#### 単体テスト

PR-3で作成したフィクスチャHTMLを使用し、`EntryPageScraper`のパブリックメソッドをテストする。
requestsをモックし、フィクスチャHTMLを返すようにしてテスト。

| テストファイル | テスト対象 | ケース |
|---|---|---|
| `test/unit/entry_page/test_get_entry.py` | `EntryPageScraper.get_entry` | カラム整理、馬体重分割、出走取消のあるレース |
| `test/unit/entry_page/test_get_race_info.py` | `EntryPageScraper.get_race_info` | 出馬表ページからのレース情報取得 |

#### 結合テスト

| テストファイル | テスト対象 | ケース |
|---|---|---|
| `test/integration/test_entry_page.py` | `EntryPageScraper` | 実際にnetkeibaにアクセスしてテスト |


---


## PR-6: 馬柱スクレイピングの実装

### 概要

`scraping/past_performances.py`を実装する。KeibaAIの馬柱スクレイピング機能を移植し、
`PastPerformancesScraper`クラスとして実装する。
Seleniumを使用してページをレンダリングするため、テストではSelenium WebDriverのモックが必要。

### 作業内容

1. `scraping/past_performances.py`の実装
   - `PastPerformancesScraper`クラス
   - `__init__(horse_id, config)`: Selenium/HTML取得、soup生成
   - `get_past_performances()`: 馬柱データの取得（PAST_PERFORMANCES_COLUMNSのカラム）
   - KeibaAIの`scrape_umabashira`を移植
     - `scrape_umabashira`とは一部カラムの順番や名前や種類が異なるので注意。
       - 「日」→「開催日」
       - 「天気」→「天候」
       - 「オッズ」→「単勝オッズ」
       - 「距離」は"芝1200"のような文字列だったが、1200のような整数にする
       - 「距離」の芝/ダート/障害の区別は別カラム「芝ダ」で行う（"芝"、"ダ"、"障"のいずれかの文字列）
       - 「通過」は"3-4"のような文字列だったが、「1コーナー通過順」「2コーナー通過順」...のような複数カラムに分割する。分割方法はresult_page.pyのものと同様。
       - 「ペース」は"33.1-34.5"のような文字列だったが、「レース前3F」「レース後3F」に分割する
       - 「間隔」→「間隔日数」
       - 「騎手ID」は取得ロジックもKeibaAIの`scrape_umabashira`にはないので新規実装すること。
2. `scraping/config.py`に以下の定数を追加
   - `PAST_PERFORMANCES_COLUMNS`（SCHEMA.mdの馬柱スキーマに準拠）
3. `scraping/__init__.py`の更新
4. 単体テストで使用するためのhtmlを`driver.page_source`から取得、保存する。
   - 取得用スクリプトは`test/scripts/fetch_past_performances_fixtures.py`とする
   - 取得対象は以下の馬ID。これらは`test_case.yml`と同様にymlファイルに定義しておくこと
     - "2022105081": ミュージアムマイル（正常系）
     - "2011101125": オジュウチョウサン（障害経験あり）
     - "2021103695": ビコーズウイキャン（地方馬）
     - "2021190001": カランダガン（外国馬）
     - "2018103559": タイトルホルダー（海外経験あり、競走中止経験あり）
     - "2021105414": クイーンズウォーク（競走除外経験あり）
     - "2021104825": ゴンバデカーブース（出走取消経験あり）
     - "2021105727": フォーエバーヤング（中央、海外、地方経験あり）
   - フィクスチャファイル命名規則は`past_performances_{horse_id}.html`
5. 単体テストの実装
6. 結合テストの実装
7. exampleの実装

### PAST_PERFORMANCES_COLUMNSのカラム構成

SCHEMA.mdの馬柱スキーマに従う。

### テスト計画

#### 単体テスト

| テストファイル | テスト対象 | ケース |
|---|---|---|
| `test/unit/past_performances/test_get_past_performances.py` | `PastPerformancesScraper.get_past_performances` | 正常系: Seleniumモックで馬柱取得、カラム構成と主要値の検証 / 準正常系: 新馬（馬柱なし） |

#### テストの注意点

- `PastPerformancesScraper.__init__`でのSelenium `webdriver.Chrome`をモックする
- `pd.read_html`もモックし、テスト用のDataFrameを返すようにする

#### 結合テスト

| テストファイル | テスト対象 | ケース |
|---|---|---|
| `test/integration/test_past_performances.py` | `PastPerformancesScraper` | 実際にnetkeibaにアクセスしてテスト |


---


## PR-7: オッズスクレイピングの実装

### 概要

`scraping/odds.py`を実装する。netkeibaおよびJRAからのオッズ取得機能を移植する。

### 作業内容

1. `scraping/odds.py`の実装
   - `scrape_odds_from_netkeiba(race_id, config)`: netkeibaからのオッズ取得
   - `scrape_odds_from_jra(race_id, config)`: JRAからのオッズ取得（async）
2. `scraping/__init__.py`の更新

### テスト計画

#### 単体テスト

| テストファイル | テスト対象 | ケース |
|---|---|---|
| `test/unit/odds/test_scrape_odds_from_netkeiba.py` | `scrape_odds_from_netkeiba` | 正常系: Seleniumモックで予想オッズ/確定オッズの取得 |
| `test/unit/odds/test_scrape_odds_from_jra.py` | `scrape_odds_from_jra` | 正常系: Playwrightモックで単勝・複勝オッズの取得 |

#### テストの注意点

- Selenium/Playwrightは外部サービスへのアクセスを伴うため、`pytest-mock`で完全にモック化する
- 非同期関数のテストには`pytest-asyncio`を使用する


---


## PR-8: レーススケジュール・カレンダーの実装

### 概要

`scraping/schedule.py`を実装する。日別スケジュールとレース一覧の取得機能を移植する。

### 作業内容

1. `scraping/schedule.py`の実装
   - `scrape_race_schedule(year, month, day, config)`: 日別レーススケジュール
   - `scrape_race_calendar(year, page_num, session, config)`: レース一覧
2. `scraping/__init__.py`の更新

### テスト計画

#### 単体テスト

| テストファイル | テスト対象 | ケース |
|---|---|---|
| `test/unit/schedule/test_scrape_race_schedule.py` | `scrape_race_schedule` | 正常系: Seleniumモックでスケジュール取得 / 準正常系: 開催のない日 |
| `test/unit/schedule/test_scrape_race_calendar.py` | `scrape_race_calendar` | 正常系: モックHTMLからレース一覧抽出 |


---


## PR-9: 馬情報スクレイピング・HorsePageScraperクラスの実装

### 概要

`scraping/horse_info.py`を実装し、馬情報スクレイピング機能を移植する。
あわせて、馬情報ページのスクレイパークラス（`HorsePageScraper`）をまとめて実装する。
`HorsePageScraper.get_past_performances()`はPR-6で実装した`PastPerformancesScraper`を利用する。

### 作業内容

1. `scraping/horse_info.py`の実装
   - `scrape_horse_info(year, page_num, session, config)`: 馬情報ページからの馬情報スクレイピング
   - `scrape_max_page_num(url, session, config)`: 馬情報ページの最大ページ数取得
   - `is_race_existence(url, session, config)`: レース存在判定
2. `scraping/horse_page.py`の実装
   - `HorsePageScraper`クラス
   - `__init__(horse_id, config)`: Selenium/HTML取得
   - `get_past_performances()`: `PastPerformancesScraper`を利用して馬柱を返す
3. `scraping/__init__.py`の更新

### テスト計画

#### 単体テスト

| テストファイル | テスト対象 | ケース |
|---|---|---|
| `test/unit/horse_info/test_scrape_horse_info.py` | `scrape_horse_info` | 正常系: モックHTMLからの馬情報抽出 / 準正常系: デビュー前（厩舎IDなし） |
| `test/unit/horse_info/test_scrape_max_page_num.py` | `scrape_max_page_num` | 正常系: ページ数の取得 / 準正常系: 取得失敗 |
| `test/unit/horse_info/test_is_race_existence.py` | `is_race_existence` | 正常系: 存在する場合 / 準正常系: 存在しない場合 |
| `test/unit/horse_page/test_horse_page_scraper.py` | `HorsePageScraper` | コンストラクタ、get_past_performances |

#### 結合テスト

| テストファイル | テスト対象 | ケース |
|---|---|---|
| `test/integration/test_horse_page.py` | `HorsePageScraper` | 実際にnetkeibaにアクセスしてテスト |


---


## PR-10: 一括取得関数とREADME・サンプルコードの整備

### 概要

全機能の統合と公開APIの整備、ドキュメントの作成を行う。

### 作業内容

1. `scraping/__init__.py`の最終整備
   - `__all__`の定義
   - バージョン情報
   - 全公開関数のエクスポート
2. `README.md`の作成
   - 概要、インストール方法、使用方法、API一覧
3. `example/basic_usage.py`の作成
   - 各関数の使用例
4. 最終的な結合テストの追加

### テスト計画

#### 結合テスト

| テストファイル | テスト対象 | ケース |
|---|---|---|
| `test/integration/test_import.py` | パッケージインポート | 正常系: 全公開関数がインポート可能であること |


---


## 実装順序と依存関係

```
PR-1 プロジェクト基盤
  │
  ▼
PR-2 設定・例外・ユーティリティ
  │
  ├──────────┬──────────┬──────────┐
  ▼          ▼          ▼          ▼
PR-3       PR-6       PR-7       PR-8
レース情報  馬柱       オッズ     スケジュール
  │          │
  ├────┐     ▼
  ▼    ▼   PR-9
PR-4  PR-5 馬情報スクレイピング
結果   出馬表  + HorsePageScraper
(※ResultPageScraper   (※horse_info.py
 含む)  (※EntryPageScraper    + horse_page.py)
         含む)
  │    │     │
  ├────┘     │
  │          │
  ▼          ▼
PR-10 統合・ドキュメント
```

> **注**: PR-4にResultPageScraper、PR-5にEntryPageScraperの実装を含む。
> PR-6にPastPerformancesScraperの実装を含む。
> PR-9にscrape_horse_info等の馬情報スクレイピング関数とHorsePageScraperの実装を含む。


## テスト全体方針

### テスティングフレームワーク

- `pytest` + `pytest-mock` + `pytest-asyncio` + `pytest-cov`

### テストデータ

- **HTMLフィクスチャ**: `test/fixtures/html/`に配置
  - `config/test/test_case.yml`に定義されている各種レースIDに対して、出馬表ページと結果ページのHTMLをpythonのrequestsでスクレイピングして保存
  - 地方競馬のページはJavaScript動的レンダリングのためrequestsでは取得できない場合はスキップ
  - `test/scripts/fetch_fixtures.py`でフィクスチャを取得・更新できる
- **DataFrameフィクスチャ**: テスト関数内またはconftestにてpd.DataFrameを直接定義

### テスト方針

- **プライベートメソッドのテストは行わない**: 複雑な処理であっても公開関数経由でテストする
- **単体テスト**: HTMLフィクスチャからBeautifulSoupを生成し、パブリック関数をテスト
- **結合テスト**: フィクスチャは使用せず、実際にnetkeibaにアクセスしてスクレイピングを行いテスト（HTML構造の仕様変更検知が目的）
- **結合テストのCI**: ネットワーク接続が必要なため、CIではマーカー（`@pytest.mark.network`等）でスキップ可能にする

### モック方針

- **単体テスト**: requestsやSelenium等のモックは不要（HTMLフィクスチャから直接soupを生成するため）
- **結合テスト**: モックなし（実際にアクセス）
- **selenium.webdriver**: 馬柱等Selenium使用モジュールのテストではモック使用
- **playwright**: 非同期ブラウザ操作のテストではモック使用

### カバレッジ目標

- 目標: 各モジュール80%以上
- `--cov-report=term-missing`で未カバー行を可視化

### テストファイル構成

```
test/
├── __init__.py
├── conftest.py                          # 共通fixture（configオブジェクト等）
├── fixtures/
│   └── html/                            # HTMLフィクスチャ（test_case.ymlの各レース）
│       ├── entry_{race_id}.html         # 出馬表ページ
│       └── result_{race_id}.html        # 結果ページ
├── scripts/
│   └── fetch_fixtures.py               # フィクスチャHTML取得スクリプト
├── unit/
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── test_scraping_config.py
│   │   └── test_constants.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── test_build_urls.py
│   │   ├── test_judge_turf_dirt.py
│   │   ├── test_race_id_to_race_info.py
│   │   ├── test_get_race_info_from_past_performances.py
│   │   ├── test_calc_interval.py
│   │   └── test_set_chrome_options.py
│   ├── race_info/
│   │   ├── __init__.py
│   │   └── test_scrape_race_info.py
│   ├── result_page/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_get_result.py
│   │   ├── test_get_corner.py
│   │   ├── test_get_win_payoff.py
│   │   ├── test_get_show_payoff.py
│   │   ├── test_get_bracket_payoff.py
│   │   ├── test_get_quinella_payoff.py
│   │   ├── test_get_quinella_place_payoff.py
│   │   ├── test_get_exacta_payoff.py
│   │   ├── test_get_trio_payoff.py
│   │   ├── test_get_trifecta_payoff.py
│   │   └── test_get_lap_time.py
│   ├── entry_page/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_get_entry.py
│   │   └── test_get_race_info.py
   ├── past_performances/
   │   ├── __init__.py
   │   └── test_get_past_performances.py
   ├── horse_info/
   │   ├── __init__.py
   │   ├── test_scrape_horse_info.py
   │   ├── test_scrape_max_page_num.py
   │   └── test_is_race_existence.py
   ├── horse_page/
   │   ├── __init__.py
   │   └── test_horse_page_scraper.py
│   ├── odds/
│   │   ├── __init__.py
│   │   ├── test_scrape_odds_from_netkeiba.py
│   │   └── test_scrape_odds_from_jra.py
│   └── schedule/
│       ├── __init__.py
│       ├── test_scrape_race_schedule.py
│       └── test_scrape_race_calendar.py
└── integration/
    ├── __init__.py
    ├── test_import.py
    ├── test_race_info.py
    ├── test_result_page.py
    ├── test_entry_page.py
    ├── test_past_performances.py
    └── test_horse_page.py
```

### テスト命名規則

- テスト関数名: `test_{テスト対象の動作}_{条件}`
  - 例: `test_scrape_race_info_returns_dataframe_with_expected_columns`
  - 例: `test_scrape_race_info_arima_kinen`
  - 関数名に日本語は使用しない

### テスト実装の注意事項

- テストクラスは作らない
- プライベートメソッドのテストは行わない（公開関数経由でテストする）
- `@pytest.mark.parametrize`を積極的に使用し、test_case.ymlの各レースIDに対してテストする
- 単体テストではフィクスチャHTMLを使用し、外部サービスへのモックは不要とする
- 結合テストでは実際にnetkeibaにアクセスしてテストする（ネットワーク接続必須）
- 結合テストにはCIでスキップ可能なマーカー（`@pytest.mark.network`等）を付与する
