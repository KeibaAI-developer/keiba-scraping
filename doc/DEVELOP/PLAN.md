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
| PR-9 | 一括取得関数とREADME・サンプルコードの整備 | PR-3〜8 | 小 |


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

### 作業内容

1. `scraping/race_info.py`の実装
   - `scrape_race_info(race_id, config)`: 公開関数
   - `_scrape_race_info(soup, race_id, config)`: BeautifulSoupからの抽出
   - `_format_race_info_text(race_raw_text, config)`: テキスト整形
   - `_format_race_info_list(race_filtered_list)`: リスト整形
2. `scraping/__init__.py`の更新

### テスト計画

#### 単体テスト

HTMLのモックを使用する。実際のnetkeibaからHTMLを取得してテストフィクスチャとして保存する。

| テストファイル | テスト対象 | ケース |
|---|---|---|
| `test/unit/race_info/test_format_race_info_text.py` | `_format_race_info_text` | 正常系: 中央/地方の各パターン |
| `test/unit/race_info/test_format_race_info_list.py` | `_format_race_info_list` | 正常系: 通常レース、地方重賞、障害レース / 準正常系: フォーマット不正 |
| `test/unit/race_info/test_scrape_race_info.py` | `_scrape_race_info` | 正常系: モックHTMLからの情報抽出 |

#### 結合テスト

| テストファイル | テスト対象 | ケース |
|---|---|---|
| `test/integration/test_race_info.py` | `scrape_race_info` | 正常系: 実際のHTMLモック（requestsをモック）で一連の処理を検証 |

### テスト用HTMLフィクスチャ

- `test/fixtures/html/result_page_central.html`: 中央競馬の結果ページ
- `test/fixtures/html/result_page_local.html`: 地方競馬の結果ページ
- `test/fixtures/html/entry_page.html`: 出馬表ページ

> **方針**: フィクスチャHTMLはPR-3で最初に作成し、以降のPRでも共用する。
> 実際のnetkeibaから取得したHTMLを使用するが、個人情報に該当する箇所は適宜マスクする。


---


## PR-4: レース結果スクレイピングの実装

### 概要

`scraping/result.py`を実装する。KeibaAIの結果関連スクレイピング機能を移植する。

### 作業内容

1. `scraping/result.py`の実装
   - `scrape_result(race_id, config)`: レース結果
   - `scrape_corner(race_id, config)`: コーナー通過順
   - `scrape_payoff(race_id, config)`: 払い戻し
   - `scrape_lap_time(race_id, config)`: ラップタイム
   - `scrape_result_page(race_id, config)`: 一括取得
   - プライベート関数: `_scrape_result`, `_scrape_corner`, `_scrape_pay_back`, `_scrape_rap`, `_scrape_rap_main`, `_format_pay_back`, `_two_split_space`, `_three_split_space`, `_add_gender_age`, `_add_id_from_table`
2. `scraping/__init__.py`の更新

### テスト計画

#### 単体テスト

| テストファイル | テスト対象 | ケース |
|---|---|---|
| `test/unit/result/test_scrape_result.py` | `_scrape_result` | 正常系: モックHTMLからの結果表抽出 / 準正常系: 開催中止のケース |
| `test/unit/result/test_scrape_corner.py` | `_scrape_corner` | 正常系: 4コーナーすべてある場合 / 準正常系: コーナー情報がない場合、直線レース |
| `test/unit/result/test_scrape_payoff.py` | `_scrape_pay_back` | 正常系: 全券種が存在する場合 |
| `test/unit/result/test_format_payoff.py` | `_format_pay_back` | 正常系: 複数的中の展開、枠連がないケース |
| `test/unit/result/test_two_split_space.py` | `_two_split_space` | 正常系: 2連系の変換 |
| `test/unit/result/test_three_split_space.py` | `_three_split_space` | 正常系: 3連系の変換（同着含む） |
| `test/unit/result/test_scrape_lap_time.py` | `_scrape_rap` | 正常系: 平地/直線 / 準正常系: 障害、ラップなし |
| `test/unit/result/test_add_gender_age.py` | `_add_gender_age` | 正常系: 性齢の分割 |
| `test/unit/result/test_add_id_from_table.py` | `_add_id_from_table` | 正常系: 出馬表/結果の各パターン / 準正常系: 不正なpage_type |

#### 結合テスト

| テストファイル | テスト対象 | ケース |
|---|---|---|
| `test/integration/test_result.py` | `scrape_result_page` | 正常系: モックHTMLで一連の処理を検証 |


---


## PR-5: 出馬表スクレイピングの実装

### 概要

`scraping/entry.py`を実装する。KeibaAIの出馬表関連スクレイピング機能を移植する。

### 作業内容

1. `scraping/entry.py`の実装
   - `scrape_entry(race_id, config)`: 出馬表
   - `scrape_entry_page(race_id, config)`: 一括取得
   - プライベート関数: `_format_entry_df`, `_scrape_horse_id_list_from_entry`
2. `scraping/__init__.py`の更新

### テスト計画

#### 単体テスト

| テストファイル | テスト対象 | ケース |
|---|---|---|
| `test/unit/entry/test_format_entry_df.py` | `_format_entry_df` | 正常系: カラム整理、馬体重分割 / 準正常系: 馬体重未計量 |
| `test/unit/entry/test_scrape_horse_id_list.py` | `_scrape_horse_id_list_from_entry` | 正常系: 出走馬IDの抽出 |

#### 結合テスト

| テストファイル | テスト対象 | ケース |
|---|---|---|
| `test/integration/test_entry.py` | `scrape_entry_page` | 正常系: モックHTMLで一連の処理を検証 |


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


## PR-9: 一括取得関数とREADME・サンプルコードの整備

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
PR-9 統合・ドキュメント
```


## テスト全体方針

### テスティングフレームワーク

- `pytest` + `pytest-mock` + `pytest-asyncio` + `pytest-cov`

### テストデータ

- HTMLフィクスチャ: `test/fixtures/html/`に配置
  - 実際のnetkeibaから取得したHTMLを使用
  - 個人情報に該当する箇所はマスク
- DataFrameフィクスチャ: テスト関数内またはconftestにてpd.DataFrameを直接定義

### モック方針

- **requests.get**: `pytest-mock`でレスポンスをモック
- **selenium.webdriver**: `pytest-mock`でWebDriverをモック
- **playwright**: `pytest-mock`で非同期ブラウザ操作をモック
- **pd.read_html**: 必要に応じてモック

### カバレッジ目標

- 目標: 各モジュール80%以上
- `--cov-report=term-missing`で未カバー行を可視化

### テストファイル構成

```
test/
├── __init__.py
├── conftest.py                          # 共通fixture（configオブジェクト等）
├── fixtures/
│   └── html/                            # HTMLフィクスチャ
│       ├── result_page_central.html
│       ├── result_page_local.html
│       ├── entry_page.html
│       ├── horse_info_page.html
│       ├── horse_past_performances.html
│       ├── race_calendar_page.html
│       └── race_schedule_page.html
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
│   │   ├── test_format_race_info_text.py
│   │   ├── test_format_race_info_list.py
│   │   └── test_scrape_race_info.py
│   ├── result/
│   │   ├── __init__.py
│   │   ├── test_scrape_result.py
│   │   ├── test_scrape_corner.py
│   │   ├── test_scrape_payoff.py
│   │   ├── test_format_payoff.py
│   │   ├── test_two_split_space.py
│   │   ├── test_three_split_space.py
│   │   ├── test_scrape_lap_time.py
│   │   ├── test_add_gender_age.py
│   │   └── test_add_id_from_table.py
│   ├── entry/
│   │   ├── __init__.py
│   │   ├── test_format_entry_df.py
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
  - 例: `test_format_race_info_text_handles_local_race`
- 日本語は使用しない（pytest-coding-ruleに準拠）

### テスト実装の注意事項

- テストクラスは作らない（pytest-coding-ruleに準拠）
- プライベート関数のうちデータ整形処理（`_format_*`系）はロジックが複雑なため、例外的にテスト対象とする
  - ただし公開関数経由のテストで十分にカバーできる場合はプライベート関数のテストは省略可
- `@pytest.mark.parametrize`を積極的に使用し、中央/地方/海外等の複数パターンを1ケースでカバーする
- 外部サービス（netkeiba、JRA）へのアクセスは全てモック化する
