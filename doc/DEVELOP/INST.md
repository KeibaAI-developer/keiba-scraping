# keiba-scrapingライブラリの実装

## 概要

KeibaAIのmodulesとして実装されているスクレイピング機能に関して、純粋なスクレイピング機能のみを抽出してKeibaAIとの依存をなくしライブラリとして実装したい

## 現状

- KeibaAI/modules/scraping/scraping_main.pyおよびKeibaAI/modules/scraping/scraping_core.pyにスクレイピング機能が実装されている
- utilsやparamなどに依存している

## 仕様

### KeibaAIとの依存関係

- KeibaAIはcsvファイルでデータを保存することを前提としているが、ライブラリとしてはデータフレームを取得するのみに留めたい
- KeibaAIには日付ID(date_id)という概念があるが、ライブラリでは使用したくない
- KeibaAIのparamやutilsに依存しないようにする
- KeibaAIではコース何日目かの情報をrace_infoに追加する処理を実装しているが、これはスクレイピングのみでは実装できず過去のデータの蓄積が必要になるため、ライブラリでは実装しない

### API

欲しい関数は以下の通り。
実装済みのデータ整形やカラムの追加（コース何日目情報を除く）処理はライブラリに残しておくこと

- レース情報（race_info）のスクレイピングをする関数
- レース結果（result）のスクレイピングをする関数
- コーナー通過順位（corner）のスクレイピングをする関数
- 払い戻し情報（payoff）のスクレイピングをする関数（KeibaAIではpay_backと言っている）
- ラップタイム（lap_time）のスクレイピングをする関数（KeibaAIではrapと言っているが誤字）
- 出馬表（entry）のスクレイピングをする関数（KeibaAIではshutubaと言っている）
- 馬の所属情報など（horse_info）をスクレイピングする関数
- 馬柱（past_performances）のスクレイピングをする関数（KeibaAIではumabashiraと言っている）
- その日のレーススケジュール（race_schedule）のスクレイピングをする関数（KeibaAIではtoday_race_infoと言っている）
- レース一覧（race_calender）のスクレイピングをする関数
- オッズをnetkeibaからスクレイピングする関数
- オッズをJRAからスクレイピングする関数

### ライブラリ

ライブラリとしての仕様はmykeibadb-pythonライブラリを参考にしてください

## 作業内容

以下の手順で最初の作業を行ってください。
実際の実装に関してはPLAN.mdをもとにあとで行うため、ここでは仕様検討と設計に留めてください。

1. KeibaAI/modules/scraping/を確認して現状の仕様を把握する
2. `keiba-scraping/doc/DEVELOP/SPEC.md`に機能仕様書を作成する
3. SPEC.mdをベースに`keiba-scraping/doc/DEVELOP/PLAN.md`に実装計画書を記載する
   - 人がレビュー可能なレベルに分割し、PR単位でタスクを記載する
   - テスト計画も作って実装計画に盛り込む
     - テスト実装は`.github/skills/pytest-coding-rule/SKILL.md`のルールに従うこと