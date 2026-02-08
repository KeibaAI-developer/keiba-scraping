# keiba-scraping 実装計画書

本書はSPEC.mdに基づき、keiba-scrapingライブラリの実装をPR単位で分割した計画書である。
各PRはレビュー可能なサイズに分割し、テスト計画も含む。


## PR一覧

| PR番号 | タイトル | 依存PR | 見積もり |
|--------|---------|--------|---------|
| PR-1 | プロジェクト基盤の構築 | なし | 小 |
| PR-2 | 設定・例外・ユーティリティの実装 | PR-1 | 中 |
| PR-3 | レース情報スクレイピングの実装 | PR-2 | 中 |
| PR-4 | レース結果スクレイピングの実装 | PR-3 | 大 |
| PR-5 | 出馬表スクレイピングの実装 | PR-3 | 中 |
| PR-6 | 馬情報・馬柱スクレイピングの実装 | PR-2 | 大 |
| PR-7 | オッズスクレイピングの実装 | PR-2 | 中 |
| PR-8 | レーススケジュール・カレンダーの実装 | PR-2 | 中 |
| PR-9 | スクレイパークラスの実装 | PR-3〜8 | 中 |
| PR-10 | 一括取得関数とREADME・サンプルコードの整備 | PR-9 | 小 |


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
3. `scraping/config.py`の`RACE_INFO_COLUMNS`を現在の仕様に合わせて更新（25カラム）
   - **カラム名の変更**: JRA公式名称に統一（条件→競争種別+競争条件、グレード→競争条件、斤量条件→重量種別）、「天気」→「天候」（netkeibaの表示に合わせる）、「発走時刻」で統一（KeibaAI側は「発走時間」使用だが将来的に統一予定）
   - **グレードカラムの追加**: 競争条件とは別にグレード（G1/G2等）を格納する独立したカラムを追加。オープンレースの場合のみグレード値が入り、それ以外は空文字列
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
- 出走取消・競争除外のあるレース
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

`scraping/result.py`を実装する。KeibaAIの結果関連スクレイピング機能を移植する。
スクレイピングロジックは`scraping_core.py`と同一にする。

### 作業内容

1. `scraping/result.py`の実装
   - `scrape_result(soup, html_text, config)`: レース結果（公開）
   - `scrape_corner(soup, config)`: コーナー通過順（公開）
   - `scrape_payoff(html_text, config)`: 払い戻し（公開）
   - `scrape_lap_time(html_text, race_type, config)`: ラップタイム（公開）
   - プライベート関数: `_format_pay_back`, `_two_split_space`, `_three_split_space`, `_add_gender_age`, `_add_id_from_table`等
2. `scraping/__init__.py`の更新

### テスト計画

#### 単体テスト

PR-3で作成したフィクスチャHTMLを使用し、パブリック関数のみテストする。
プライベートメソッドのテストは行わない。

| テストファイル | テスト対象 | ケース |
|---|---|---|
| `test/unit/result/test_scrape_result.py` | `scrape_result` | 各種レースのフィクスチャHTMLからの結果表抽出。カラム構成、着順、馬名等の検証 |
| `test/unit/result/test_scrape_corner.py` | `scrape_corner` | コーナー通過順の抽出。直線レース（アイビスSD）では空DataFrame |
| `test/unit/result/test_scrape_payoff.py` | `scrape_payoff` | 払い戻しの抽出・整形 |
| `test/unit/result/test_scrape_lap_time.py` | `scrape_lap_time` | ラップタイムの抽出。平地/直線/障害の各パターン |

#### 結合テスト

| テストファイル | テスト対象 | ケース |
|---|---|---|
| `test/integration/test_result.py` | result系関数 | 実際にnetkeibaにアクセスしてテスト |


---


## PR-5: 出馬表スクレイピングの実装

### 概要

`scraping/entry.py`を実装する。KeibaAIの出馬表関連スクレイピング機能を移植する。
スクレイピングロジックは`scraping_core.py`と同一にする。

### 作業内容

1. `scraping/entry.py`の実装
   - `scrape_entry(soup, html_text, config)`: 出馬表（公開）
   - `scrape_horse_id_list(soup, config)`: 出走馬IDリスト（公開）
   - プライベート関数: `_format_entry_df`
2. `scraping/__init__.py`の更新

### テスト計画

#### 単体テスト

PR-3で作成したフィクスチャHTMLを使用し、パブリック関数のみテストする。

| テストファイル | テスト対象 | ケース |
|---|---|---|
| `test/unit/entry/test_scrape_entry.py` | `scrape_entry` | カラム整理、馬体重分割、出走取消のあるレース |
| `test/unit/entry/test_scrape_horse_id_list.py` | `scrape_horse_id_list` | 出走馬IDの抽出 |

#### 結合テスト

| テストファイル | テスト対象 | ケース |
|---|---|---|
| `test/integration/test_entry.py` | entry系関数 | 実際にnetkeibaにアクセスしてテスト |


---


## PR-6: 馬情報・馬柱スクレイピングの実装

### 概要

`scraping/horse.py`を実装する。KeibaAIの馬情報・馬柱関連スクレイピング機能を移植する。
Seleniumを使用する関数を含むため、テストではSelenium WebDriverのモックが必要。

### 作業内容

1. `scraping/horse.py`の実装
   - `scrape_horse_info(year, page_num, session, config)`: 馬情報
   - `scrape_past_performances(horse_id, config)`: 馬柱
   - `scrape_max_page_num(url, session, config)`: 最大ページ数
   - `is_race_existence(url, session, config)`: レース存在判定
2. `scraping/__init__.py`の更新

### テスト計画

#### 単体テスト

| テストファイル | テスト対象 | ケース |
|---|---|---|
| `test/unit/horse/test_scrape_horse_info.py` | `scrape_horse_info` | 正常系: モックHTMLからの馬情報抽出 / 準正常系: デビュー前（厩舎IDなし） |
| `test/unit/horse/test_scrape_past_performances.py` | `scrape_past_performances` | 正常系: Seleniumモックで馬柱取得 / 準正常系: 新馬（馬柱なし） |
| `test/unit/horse/test_scrape_max_page_num.py` | `scrape_max_page_num` | 正常系: ページ数の取得 / 準正常系: 取得失敗 |
| `test/unit/horse/test_is_race_existence.py` | `is_race_existence` | 正常系: 存在する場合 / 準正常系: 存在しない場合 |

#### テストの注意点

- `scrape_past_performances`はSeleniumの`webdriver.Chrome`をモックする
- `pd.read_html`もモックし、テスト用のDataFrameを返すようにする


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


## PR-9: スクレイパークラスの実装

### 概要

ページごとのスクレイパークラスを実装する。
コンストラクタでHTTP取得とBeautifulSoup生成を行い、各メソッドで個別テーブルを取得する設計。
各モジュール（race_info.py、result.py等）の公開関数を呼び出す。

### 作業内容

1. `scraping/entry_page.py`の実装
   - `EntryPageScraper`クラス
   - `__init__(race_id, config)`: HTTP取得、soup生成
   - `get_race_info()`: `race_info.scrape_race_info()`を呼び出し
   - `get_entry()`: `entry.scrape_entry()`を呼び出し
2. `scraping/result_page.py`の実装
   - `ResultPageScraper`クラス
   - `__init__(race_id, config)`: HTTP取得、soup生成
   - `get_race_info()`: `race_info.scrape_race_info()`を呼び出し
   - `get_result()`: `result.scrape_result()`を呼び出し
   - `get_corner()`: `result.scrape_corner()`を呼び出し
   - `get_payoff()`: `result.scrape_payoff()`を呼び出し
   - `get_lap_time()`: `result.scrape_lap_time()`を呼び出し
3. `scraping/horse_page.py`の実装
   - `HorsePageScraper`クラス
   - `__init__(horse_id, config)`: Selenium/HTML取得
   - `get_past_performances()`: `horse.scrape_past_performances()`を呼び出し
4. `scraping/__init__.py`の更新

### テスト計画

#### 単体テスト

requestsをモックし、フィクスチャHTMLを返すようにしてテスト。

| テストファイル | テスト対象 | ケース |
|---|---|---|
| `test/unit/page/test_entry_page_scraper.py` | `EntryPageScraper` | コンストラクタ、get_race_info、get_entry |
| `test/unit/page/test_result_page_scraper.py` | `ResultPageScraper` | コンストラクタ、各getメソッド |

#### 結合テスト

| テストファイル | テスト対象 | ケース |
|---|---|---|
| `test/integration/test_page_scrapers.py` | 各スクレイパークラス | 実際にnetkeibaにアクセスしてテスト |


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
レース情報  馬情報     オッズ     スケジュール
  │
  ├──────────┐
  ▼          ▼
PR-4       PR-5
レース結果  出馬表
  │          │
  ├──────────┘
  ▼
PR-9 スクレイパークラス
  │
  ▼
PR-10 統合・ドキュメント
```


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
│   ├── result/
│   │   ├── __init__.py
│   │   ├── test_scrape_result.py
│   │   ├── test_scrape_corner.py
│   │   ├── test_scrape_payoff.py
│   │   └── test_scrape_lap_time.py
│   ├── entry/
│   │   ├── __init__.py
│   │   ├── test_scrape_entry.py
│   │   └── test_scrape_horse_id_list.py
│   ├── horse/
│   │   ├── __init__.py
│   │   ├── test_scrape_horse_info.py
│   │   ├── test_scrape_past_performances.py
│   │   ├── test_scrape_max_page_num.py
│   │   └── test_is_race_existence.py
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
    ├── test_result.py
    └── test_entry.py
```

### テスト命名規則

- テスト関数名: `test_{テスト対象の動作}_{条件}`
  - 例: `test_scrape_race_info_returns_dataframe_with_expected_columns`
  - 例: `test_scrape_race_info_arima_kinen`
- 日本語は使用しない（pytest-coding-ruleに準拠）

### テスト実装の注意事項

- テストクラスは作らない（pytest-coding-ruleに準拠）
- プライベートメソッドのテストは行わない（公開関数経由でテストする）
- `@pytest.mark.parametrize`を積極的に使用し、test_case.ymlの各レースIDに対してテストする
- 単体テストではフィクスチャHTMLを使用し、外部サービスへのモックは不要とする
- 結合テストでは実際にnetkeibaにアクセスしてテストする（ネットワーク接続必須）
- 結合テストにはCIでスキップ可能なマーカー（`@pytest.mark.network`等）を付与する
