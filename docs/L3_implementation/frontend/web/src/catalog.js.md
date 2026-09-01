# `frontend/web/src/catalog.js`

## 目的・役割

`catalog.html`(学年別カテゴリ画面)のページエントリ。issue #99 で `docs/uiux/wireframe_v1.png` の画面②(学年ごとのカテゴリ・ドリル一覧)に合わせて全面書き換えした。旧絞り込みフォーム(`numberType`/`grade`/`level`/`forms`)は撤去し、`drillCatalog.js` の `buildDrillCatalog`/`filterDrillCatalog`(旧5分類の `operationGroup` タクソノミー)を経由せず、`drillPresets.js` の `presetsByGrade[grade]`(たし算/ひき算/かけ算/わり算/小数/分数/四則混合/数の性質のカテゴリマップ。`小数` は5年生専用、issue #320)を直接消費する。

## 動作の概要

- モジュール読み込み時に `mountNavShell()` を呼ぶ。
- `render()`: `location.search` から `grade` を読み、`GRADES`(1〜6)に含まれない場合は空状態(`no_drills_found` + 戻るリンク)を表示して終了する。
- ページヘッダーは共通コンポーネント `pageHeaderHtml(title, description)`([[./pageHeader.js]] 参照、issue #157)を呼び出して描画する。`title` には `t(\`grade_full_${grade}\`)`(例: 「小学1年生」)、`description` には学年ごとの指導ポイント文言 `t(\`grade_point_${grade}\`)` を渡す。アイコンとタイトルの `<h1>` を同じ `<a>` に包むことで、アイコン・タイトルどちらをクリックしても `index.html` に戻る単一のクリック領域になっている(issue #126、「戻る」というテキストラベルは廃止)。旧実装は `<a class="back-button">戻るテキスト</a>` と `<h1 class="catalog-heading">` を別要素として横に並べていた。
- issue #130: grade が確定すると `#catalog` コンテナに `grade-${grade}` クラスを付与する(`frontend/web/src/catalog.js`)。`_catalog.scss`([[./styles/_catalog.scss]] 参照)の `.grade-1`〜`.grade-6` が定義する `--color-primary`/`--color-primary-hover` カスタムプロパティをこのクラス経由でスコープし、ヘッダー背景・カテゴリ見出しの左ボーダー・ドリルカードのhover枠線(`_drillList.scss`)を学年別の `$color-grade-N` に切り替える。grade が無効/欠落の空状態では付与されないため、既定の固定色のまま表示される。
- `GET /renderer-info` を fetch して `activeRenderer` を確定する(失敗時は `reportlab` にフォールバック)。
- `CATEGORY_ORDER`(`addition`/`subtraction`/`multiplication`/`division`/`decimal`/`fraction`/`four-operations`/`number-sense` の固定順。`decimal` は5年生専用の小数セクションで `fraction` の直前、issue #320)でループし、`presetsByGrade[grade]` に存在するカテゴリだけを、各アイテムを `canUseItem(item, activeRenderer)`(`!item.latexOnly || activeRenderer === 'latex'`。`drillCatalog.js` 内の同名関数と同じロジックをこのファイル内に複製)でフィルタしたうえで描画する。`presetsByGrade` のオブジェクトキー挿入順は学年ごとに異なる(例: grade4 は division が addition より先)ため、表示順は `CATEGORY_ORDER` で固定している。
- `drillCardHtml`: ドリルカード1件を、タイトル・`item.difficultyKey` を使う難易度バッジ・`item.examples[0]` を `formatExample()`(`+`/`-`/`×`/`÷` の前後にスペースを挿入。`/` は分数の区切りとして扱いスペースを入れない)で整形した例題1件、を `<a href="preset.html?grade=<grade>&drillId=<id>&format=default">` として描画する。`DIFFICULTY_BADGE_CLASS` は `difficulty_basic`/`difficulty_standard`/`difficulty_basic_standard`/`difficulty_advanced` をそれぞれ対応するCSSクラスへ変換し、未知のキーは標準バッジへフォールバックする(`frontend/web/src/catalog.js:21-26,39-46`)。カード全体がリンク。
- URL契約(`preset.html?grade=N&drillId=ID&format=default`)は #97/#98 時点から変更していないため、`preset.js`/`presetDetail.js`/`drillCatalog.js` は無変更のまま連携する。

## 重要な設計判断とその理由

### `drillCatalog.js` の `buildDrillCatalog`/`filterDrillCatalog` を経由しなくなった理由

`drillCatalog.js` の L3 doc([[./drillCatalog.js]] 参照)が issue #98 時点で「将来的に `home.js`/`catalog.js`/`preset.js` が #99/#100 の新 UI に置き換わった時点で、本ファイル自体の削除が可能になる(issue #110)」と明記していた通り、issue #99 のスコープは `catalog.js` をその新 UI に置き換えることだった。`buildDrillCatalog` が生成する `operationGroup`(旧5分類)は wireframe が要求する7カテゴリ(`addition`/`subtraction`/... のカテゴリキーそのもの)と一致しないため、`presetsByGrade` を直接読む設計にした。`preset.js` はまだ `drillCatalog.js` に依存しているため(issue #100 のスコープ)、`drillCatalog.js` 自体は削除していない。

### `canUseItem` を `drillCatalog.js` からインポートせず複製した理由

`drillCatalog.js` の `canUseItem` は非 export のプライベート関数であり、`catalog.js` が `presetsByGrade` を直接読む設計に切り替えたことで `drillCatalog.js` への依存を全体的に減らす方針と合わせ、1行のロジックのために export を追加するより複製の方が `drillCatalog.js`(将来削除候補、issue #110)への結合を増やさずに済むと判断した。

### ヘッダーの「戻るアイコン+タイトル」を1つの `<a>` に統合した理由

旧実装は `index.html` の静的な `<header class="app-header"><h1>100マス計算ジェネレーター</h1></header>` と、`catalog.js` が描画するこの `<header class="catalog-header">` が同一ページ上に二重に存在し、`<h1>` も2つ表示されていた(issue #126 でユーザー指摘)。修正では `index.html` 側の静的ヘッダーをブランド専用に作り替え([[./home.js]] 参照)、`catalog.html` からは静的ヘッダーそのものを削除して `catalog.js` が描画するこの `<header>` に一本化した。さらに、ユーザー要望により「戻る」というテキストラベル付きの独立したリンクをやめ、wireframe と同じ「アイコンはタイトルの左、タイトルクリックでも戻る」という単一のクリック領域に変更した。

### 例題を1件・スペース整形して表示する理由

`docs/uiux/wireframe_v1.png` の画面②は各ドリルカードに例題を1件(`例）625 + 75` のようにスペース区切り)だけ表示している。`drillPresets.js` の `examples` 配列(最大3件、`'625+75'` のようにスペースなし)は元データのため、`catalog.js` 側で見た目だけ調整している。

## 統合ポイント

- 呼び出し元: `catalog.html` の `<script type="module" src="/src/catalog.js">`。
- 呼び出し先: `strings.js`(`t`)、`drillPresets.js`(`GRADES`/`presetsByGrade`)、`navShell.js`(`mountNavShell`)、`icons.js`(`ICONS.chevronLeft`、空状態のみ)、`pageHeader.js`(`pageHeaderHtml`、issue #157)、`backend`(`GET /renderer-info`)。ドリルカードのリンク遷移先は `preset.html`(ブラウザナビゲーションのみ)。
- `drillCatalog.js`/`filterDrillCatalog`/`buildDrillCatalog` への依存はなくなった。

## 注意事項・既知の制限

- 絞り込みフォーム(`numberType`/`level`/`forms`、issue #97 で追加した「問題の形式」チェックボックスを含む)は issue #99 で完全に撤去した。カテゴリ・学年を横断した検索・絞り込みの導線は現在存在しない。
- `grade` パラメータが `GRADES`(1〜6)に含まれない場合(欠落・範囲外・`ungraded` など)は一律で空状態を表示する。

## 変更履歴(git log より自動生成)

- c7260fa refactor(#320): replace grade 5 multiplication/division sections with a 小数 section
- 9b366c1 #157 Add per-grade/per-drill header descriptions via a shared page header component (#160)
- 85e58b1 #146 Add an advanced difficulty badge to the web UI (#147)
- d43d1bc #130 frontend/web: make catalog page accent color switch dynamically per grade (#131)
- 1bb0f69 #126 frontend/web: add missing wireframe icons and unify page headers (#127)
- 90864a5 refactor(frontend/web): replace hand-drawn nav/UI icons with Material Symbols
- 1bd6fa6 #99 Rebuild frontend/web top and catalog screens to match wireframe screens 1-2 (#116)
- 8007488 #97 frontend/web: rebuild nav shell, design tokens, and remove legacy features (#109)
- 25532c5 #88 Restructure into backend/+frontend/{spa,web} and add a static frontend/web implementation (#89)
