# `frontend/web/src/drillCatalog.js`

## 目的・役割

`drillPresets.js`(issue #98 で grade → category → menu-item の階層データモデルへ全面刷新済み。[[./drillPresets.js]] 参照)から、`home.js`/`catalog.js`/`preset.js`(issue #97/PR #109 で構築、変更なし)が要求するフラットなカタログ形状を組み立てるアダプター。issue #88 時点では `frontend/spa/src/drillCatalog.js` の単純コピーだったが、#98 で内部実装を新データモデル対応へ書き換え、コピー関係は終了した。公開 API(`buildDrillCatalog`/`filterDrillCatalog`/`addSearchText`/`NUMBER_TYPES`/`OPERATION_GROUPS`/`DRILL_FORMS`)は #97 時点から変更していない。

## 動作の概要

`buildDrillCatalog(renderer)` は `presetsByGrade` の各カテゴリ内の menu item を1件ずつ、`item.buildParams(defaultSettingsState(item.settings))`(`choice` 設定はその `default` 値、`fixed` 設定は無視)で実際の request params に変換し、以下の形のカタログエントリへ変換する:

```
{ id, grade, numberType, operationGroup, forms: [], level, titleKey, descKey, supportLevel, presets: { default: { titleKey, descKey, params } } }
```

- `numberType`/`operationGroup` は #97 以前と同じ**paramsベースの分類ロジック**(`getNumberType`/`getOperationGroup`)で算出する。`catalog.js` の `NUMBER_TYPE_GROUPS` が `'addition-subtraction'`/`'multiplication-division'`/`'four-operations'`/`'comparison'` という旧分類名をハードコードしているため、`drillPresets.js` 側の新カテゴリ名(`addition`/`subtraction`/...)をそのまま出力せず、このアダプターが旧分類名へ変換する。新設された数論系コマンド(`evenodd`/`multiples`/`divisors`/`lcm`/`gcd`/`simplify`/`commondenom`/`frac2dec`/`dec2frac`/`divfrac`)は `number-sense` に分類する。
- `forms` は常に空配列(#98 で筆算/虫食い算の format 区別を廃止したため。[[./drillPresets.js]] の「ドキュメントにない既存機能の扱い」参照)。`DRILL_FORMS` も空配列で export しており、`home.js` の「出題形式・目的で選ぶ」セクションは常に非表示になる。
- `level` は `item.difficultyKey` を `catalog.js` が使う `level_<slug>` 形式の短いスラグ(`basic`/`standard`)へ変換する(`LEVEL_BY_DIFFICULTY_KEY`)。`difficulty_basic_standard` は `standard` にフォールバックする。
- `presets` は単一キー `default` のみを持つ(#98 で `written`/`horizontal` の複数フォーマットを廃止したため)。`catalog.js`/`preset.js` は `Object.entries(drill.presets)` の件数が1件なら `t('generate_pdf')` を、複数なら `t(\`format_${format}\`)` をボタンラベルにする分岐を持つため、この変更で自動的に単一ボタン表示になる(`catalog.js` 自体は無変更)。

## 重要な設計判断とその理由

### 公開 API を変えずに内部実装だけ差し替えた理由

`home.js`/`catalog.js`/`preset.js` を無変更に保つため(issue #98 のスコープはデータモデルに限定し、UI 刷新は #99/#100 が担う)。`drillCatalog.js` を削除せず存続させる判断の背景は [[./drillPresets.js]] および issue #110(将来の削除タスク)を参照。

### `settings`/`buildParams` はデフォルト状態のみ消費

現状 `home.js`/`catalog.js`/`preset.js` にはセグメントコントロール等の設定 UI が存在しないため、本ファイルは `item.settings` の `choice` 設定について常に `default` 値を使って `buildParams()` を呼ぶ。ユーザーが `carryMode`/`remainderMode`/`denominator` 等を選べるようになるのは #99/#100 以降。

## 統合ポイント

- 呼び出し元: `home.js`(利用可能な出題形式の算出。`DRILL_FORMS` が空のため実質常に非表示)、`catalog.js`(カタログ構築・絞り込み)、`preset.js`(URLパラメータからのプリセット特定)。
- 呼び出し先: `drillPresets.js`(`GRADES`/`UNGRADED`/`presetsByGrade`)。

## 注意事項・既知の制限

- `frontend/spa/src/drillCatalog.js` とはもはや無関係(#98 で分岐)。
- `catalog.js` の `NUMBER_TYPE_GROUPS`(`fractions: ['addition-subtraction', 'multiplication-division', 'comparison']` 等)は `'four-operations'` を含まないため、`operationGroup` が `'four-operations'` に分類される分数項目(例: `g6-fraction-muldiv-mixed`)は、数の種類で絞り込んだグループ表示には現れない(学年のみの通常カタログ表示には現れる)。#97 以前から存在する `catalog.js` 側の制約で、本アダプターでは解消していない。
- 将来的に `home.js`/`catalog.js`/`preset.js` が #99/#100 の新 UI に置き換わった時点で、本ファイル自体の削除が可能になる(issue #110)。
