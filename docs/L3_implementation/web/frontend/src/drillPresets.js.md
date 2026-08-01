# `web/frontend/src/drillPresets.js`

## 目的・役割

「学年(1〜6)」を `POST /generate-pdf`(`web/backend/app.py`)へのリクエストパラメータにマッピングする静的な設定データ。UI ロジックを一切持たず、`GRADES`・`CUSTOM_GRADE`・`presetsByGrade` の3つを export するのみ。

## 動作の概要

- `presetsByGrade[grade]` は `{ normal: [...], written: [...] }` の形。`normal` は横書き(`a + b = c`)形式、`written` は筆算(縦書き/`vertical: true`)形式のプリセット配列。各 preset は `{ id, titleKey, descKey, params, numberInput? }` の形。
  - `params`: `/generate-pdf` にそのまま渡す固定パラメータ(例: `{ command_type: 'ope', operator: ['add','sub'], a_min: 1, a_max: 9, b_min: 1, b_max: 9 }`)。
  - `numberInput`: ユーザーがカードごとに変更できる追加パラメータがある場合のみ存在。`{ param, labelKey, min, max, default }` で、`param` が `params` にマージされる対象キー(例: 九九の「段」は `a_value`)。
- `titleKey`/`descKey` は `public/locales/{en,ja}/translation.json` のキー。

## 重要な設計判断

- **学年は概算のガイドであり厳密なカリキュラム対応ではない**: `nuts_calc.py` は整数の四則演算・九九(`99`)・100マス(`100`)・平方数(`squ`)・円周率3.14倍(`pi`)・aBc暗算(`aBc`)・補数(`com`)のみをサポートし、小数・分数は非対応。そのため4〜6年生で本来学ぶ小数計算・分数・円の面積などは、桁数を増やした四則混合(`operator: ['mix']`)や `pi`/`squ` コマンドで難易度的に近似している。UI (`GradeDrills.jsx`) 側で「学年の目安は概算」である旨を明記することでこの制約を利用者に伝えている。
- `com` コマンドの `a_value` は「桁数」ではなく補数の対象(target)そのもの(`nuts_calc.py` の `main()` 内 `target = ini.a_value` を参照)。そのため `g1-complement10` は `a_value: 10`、`g2-complement100` は `a_value: 100` としている(桁数ではない点に注意)。
- `99`/`squ`/`pi` コマンドの `a_value` は「開始する数」(`nuts_calc.py` の `get_fixed_format_data` で `start_num = ini.a_value` として使われる)。九九は段そのもの(1〜9)なので `numberInput.default: 2` かつ `max: 9`、`squ`/`pi` は連番の開始位置なので `numberInput.default: 1` かつ `max: 20`(実用上妥当な範囲として設定、`nuts_calc.py` 側に上限のバリデーションはない)。
- **`written`(筆算)は `nuts_calc.py --vertical` が対応する組み合わせに限定している**: `--vertical` は `ope` コマンドの `add`/`sub`/`mul`(mul は掛ける数の桁数を問わず対応。issue #10 で複数桁乗数の部分積表示に対応済み)をサポートし、`div`/`mix` のみ CLI 側のバリデーションで `exit(1)` になる(`docs/L3_implementation/nuts_calc.py.md` 参照)。ただし本ファイル(`drillPresets.js`)の `written` プリセット定義自体はこの CLI 側の対応拡張にまだ追随しておらず、含めているのは各学年の `add`/`sub`(桁数を学年に応じて増やして近似)と、3年生の `mul`(2桁×1桁)のみ。4〜6年生の掛け算(複数桁乗数、CLI 側は対応済み)・わり算の筆算(長除法、issue #11)を `written` プリセットに追加するのはフロントエンド側の別途対応が必要。
- **6年生の `written` の `addsub` プリセットは桁数を揃えていない(`a_value: 5, b_value: 3`)**: 5年生で既に `a_value: 5, b_value: 5` を使っているため、6年生をさらに大きい桁数にすると `nuts_calc.py` の `a_value`/`b_value` 桁数ショートカット(`set_min_max_value` は1〜5桁までしか定義されていない)の上限に達してしまう。桁数の異なる数どうしの位取りの練習という、実際の学習内容としても妥当な差別化を採用した。

## 統合ポイント

- 呼び出し元: `GradeDrills.jsx`(`GRADES`/`CUSTOM_GRADE` でナビゲーションを描画、`presetsByGrade[selectedGrade][formatCategory]` でカードを描画)
- 呼び出し先: なし(純粋なデータモジュール)

## 注意事項・既知の制限

- `nuts_calc.py`/`web/backend/app.py` 側にパラメータの許可リストバリデーションが薄いため(`docs/L3_implementation/specification_summary.md` 既知の制約)、ここで不正な組み合わせを作らないよう注意する。
- `written` の掛け算プリセットは3年生の1件のみ(理由は上記)。

## 変更履歴(git log より自動生成)

- f0201d6 feat(#13): add grade-based written-calculation (hissan) drill menu
- 0631cf9 feat(#5): add grade-based drill PDF picker to web/frontend
