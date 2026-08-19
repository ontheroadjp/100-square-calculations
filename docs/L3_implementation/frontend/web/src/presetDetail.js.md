# `frontend/web/src/presetDetail.js`

## 目的・役割

`preset.html`(ドリル詳細ページ)の中身を実装するマウント可能なウィジェット。issue #100 で、`docs/uiux/wireframe_v1.png` の画面③④⑤(設定 → 完了 → プレビュー)に合わせた3状態ビューへ全面書き換えした。旧実装(issue #88〜#99時点)は単一画面で、マウント直後に自動でPDFを生成し、設定フォームと常時表示iframeを同居させていた。

## 動作の概要

- `mountPresetDetail(container, { grade, item, onBack })`: `item` は `drillPresets.js` の生アイテム(`settings`/`buildParams`/`supportLevel`/`difficultyKey`/`examples` 等、[[./drillPresets.js]] 参照)をそのまま受け取る。`screen`(`'settings' | 'done' | 'preview'`)を含む状態を持つクロージャを構築するが、マウント時に自動生成は行わない(`screen: 'settings'` で開始)。マウント直後に `container.classList.add(\`grade-${grade}\`)` を実行し(issue #132)、以後全画面の再描画(`container.innerHTML` の丸ごと差し替え)を通じてこのクラスを保持する。`catalog.js` と同じ `.grade-N` カスタムプロパティ(`_base.scss` 参照)経由で、ヘッダー・選択中ボタン・PDF作成ボタン等が学年色に切り替わる。
- 設定画面(`screen === 'settings'`):
  - ページヘッダーは `catalog.js` と共通の `pageHeaderHtml(title, description)` コンポーネント([[./pageHeader.js]] 参照、issue #157)を呼び出して描画する。`title` には `${t(item.titleKey)}(${t(\`grade_full_${grade}\`)})`、`description` にはドリルごとの指導ポイント文言 `t(item.pointKey)`([[./drillPresets.js]] 参照)を渡す。学年アクセントカラーの背景は `_catalog.scss` の `.catalog-header-title` スタイルをそのまま共用する。
  - 例題チップは `currentExamples()`(非export、issue #139)が返す配列を、`isVerticalOperation(item.buildParams(state.settingsState))`(issue #134)が真なら `renderWrittenExampleHtml()`、そうでなければ `renderExampleHtml()`(いずれも非export)で描画する。前者は「出題形式:筆算」選択時の筆算モックアップ、後者は従来通りの横書きKaTeX式。`renderExampleHtml()`/`buildExampleSegments()`(export、issue #132)の役割自体は変更していない。
  - 出題形式:筆算(issue #134)のモックアップは `buildWrittenExampleTex(example)`(export)が生成する: `÷` を含む例題は `buildWrittenDivTex()`、それ以外は `buildWrittenAddSubMulTex()`(いずれもexport)に委譲する。詳細は後述の設計判断セクション参照。
  - `currentExamples()` は `item.buildParams(state.settingsState)` が `isLivePreviewSupported(params)`(export、issue #139。`command_type === 'ope'` かつ `backend/problem_generation.py` の `UNSUPPORTED_OPE_VARIANT_FLAGS`(`use_parentheses`/`missing_value`/`terms`/`terms_min`/`terms_max`/`mixed_operators`)を含まないかを判定する純粋関数で、同ファイルの実装をそのままミラーしている)を満たし、かつ `state.liveExamples` が取得済みならそれを、そうでなければ `selectExamples(item, state.settingsState)`(export、issue #135。`item.examplesFor` があればそれを `state.settingsState` で呼んだ結果を、無ければ `item.examples` をそのまま返す)を返す。`isLivePreviewSupported` は状態依存(九九プリセットの `dan` 設定など、同一アイテムでも設定値によって `command_type` が `'ope'`/`'99'` に切り替わる場合がある、[[./drillPresets.js]] 参照)なため、アイテム単位ではなく毎回 `buildParams(state.settingsState)` の結果で判定し直す。
  - Live 対象の場合、マウント時と設定(choice)変更時に `scheduleLiveExampleFetch()` が 300ms デバウンスの `POST /generate-problems` を発火する(`num: LIVE_EXAMPLE_COUNT`=3、既存の静的 `examples` 配列の長さに合わせた値)。レスポンスの `{a, operator, b, a_decimal_places, b_decimal_places}` を `buildLiveExampleStrings()`(export)で `"a+b"` 形式の文字列(`OPERATOR_SYMBOLS` で `add/sub/mul/div` → `+/-/×/÷`)へ変換し `state.liveExamples` に格納、以後は `currentExamples()` 経由で表示される。`a`/`b` は `backend/nuts_calc_tex.py` の `format_decimal_value()` と同じロジックのローカル関数 `formatDecimalValue()`(非export)で `a_decimal_places`/`b_decimal_places` を反映した小数文字列へ変換してから連結する(issue #134 で発見・修正した既存バグ: 元は `a`/`b` を生のスケール整数のまま連結しており、小数系プリセット(`g3-decimal-addsub` 等、`isLivePreviewSupported` は小数系フラグを除外しないため live 対象になる)のライブ例題が誤った値(例: 本来`0.2+0.4`のところ`2+4`)を表示していた)。取得中の再設定変更や非対象への切り替わりで古い応答が反映されないよう、`liveExampleFetchToken` をインクリメントして比較するトークンガードを持つ。fetch 失敗時(backend未到達等)は `state.liveExamples = null` に戻し、`currentExamples()` が自動的に `selectExamples()` の静的表示へフォールバックする(クラッシュさせない・ユーザーにエラーを出さない設計、Done Criteria参照)。
  - 分数・帯分数・演算子(`×`→`\times`、`÷`→`\div`)を数式トークンとして抽出し、日本語(`奇数`/`最大公約数` 等)や矢印はプレーンテキストのまま残す(KaTeX 自身のフォントに CJK グリフが無いため)。`exampleWithEquals()` が矢印を含まない例題の末尾へ `=` を補い(未解決の問題として表示)、矢印を含む例題(frac2dec/simplify/evenodd 等、既に結果を示している)はそのまま。
  - `supportLevel === 'partial'` の制限注記
  - `item.settings` を `.specific-setting-block` 内へ動的レンダリング: `type: 'choice'` は segmented control(選択中の値に対応する `option.hintKey` があればその下にヒント文を表示、issue #132 で `value === 'mixed'` ハードコードから汎用化)、`type: 'fixed'` は読み取り専用表示。choice が任意の `disabledWhen(settingsState)` を持つ場合は全ボタンへ `disabled` を付けて表示したまま操作不能にし、`resolveValue(settingsState)` があれば保持値ではなくその解決値を選択表示と完了サマリに使う(`frontend/web/src/presetDetail.js:31-37,114-124,155-176`)。
  - 「詳細設定(共通設定)」disclosure(初期折りたたみ)に問題数 segmented control(10/20/30問。`layoutForProblemCount()` で `nuts_calc.py` の `rows`/`columns` に変換。20問が旧実装の標準密度=10行×2列と同値)・用紙サイズ・ページ数を格納(issue #132 で問題数をここへ移動。旧実装は `.specific-setting-block` の外、disclosure の手前に独立表示していた)
  - 「名前をつける」トグル: 状態は保持するが `buildParams()` の出力には混ぜない(issue A3 でパラメータが用意されるまでUIのみ)
  - `supportLevel === 'none'` は「PDFを作成する」を無効化し「準備中」表示に切り替える(現行 `drillPresets.js` に `none` のアイテムは存在しないが、issue要求に従い汎用実装)
- `generatePdf()`: `item.buildParams(state.settingsState)` で request body の演算パラメータを得て、`POST /generate-pdf` を叩く。`isVerticalOperation(params)` が真の場合のみ `getVerticalRows`/`VERTICAL_COLUMNS` を使う(issue #134 で「出題形式(式/筆算)」設定が `vertical: true` を返すプリセット(18項目、[[./drillPresets.js]] 参照)を追加したことで、この分岐が実際に使われるようになった。それ以前は到達不能なデッドコードとして存在していた)。成功時は `screen = 'done'` に遷移し、古い `pdfUrl` があれば `URL.revokeObjectURL()` で解放する。失敗時は `screen = 'settings'` に留まりエラーメッセージを表示する。
- 完了画面(`screen === 'done'`): チェックマーク+静的CSS confetti、`buildSummaryParts()` によるサマリ文(例:「20問・基礎・繰り上がり：まぜる」)、4アクション(PDFを開く→`screen='preview'`、ダウンロードする→`<a download>`、同じ条件でもう1枚作る→`generatePdf()` 再実行、トップに戻る→`index.html`)。
- プレビュー画面(`screen === 'preview'`): `<iframe src="${pdfUrl}#navpanes=0">`。ズーム等はブラウザ内蔵PDFビューアのツールバーに委ね、自前実装しない。戻る操作は `history.back()` ではなく `screen = 'done'` への内部遷移(ブラウザ履歴を消費しない)。ヘッダーは設定画面と同じ `<header class="preview-header"><button class="page-header-row" data-action="back-to-done">${ICONS.chevronLeft}<h3 class="preset-detail-title">${t('preview_heading')}</h3></button></header>` パターン(issue #126。旧実装は `<div class="preview-header">` + `<span>` タイトルで、`<header>` タグではなかった)。
- `layoutForProblemCount(problemCount)`・`buildSummaryParts(..., translate)`・`buildExampleSegments(example)`・`exampleWithEquals(example)`・`selectExamples(item, settingsState)`・`selectedSettingValue(setting, settingsState)`・`isSettingDisabled(setting, settingsState)` はエクスポートされた純粋関数。`buildSummaryParts` は `translate` を引数で受け取る設計にしており、`presetDetail.test.js` から `strings.ja.json` の実際の日本語文言に依存せずアサーションできる。`buildExampleSegments`/`exampleWithEquals` は文字列変換のみ行い、実際の `katex.renderToString()` 呼び出しは非公開の `renderExampleHtml()` が担う(DOM/KaTeX 依存部分をテスト対象から切り離すため、issue #132)。依存設定の値解決と非活性判定もDOMから分離した2関数を直接テストする(`frontend/web/src/presetDetail.js:31-37`)。

## 重要な設計判断とその理由

### `drillCatalog.js` を経由しない直接消費に変更した理由

旧実装は `drillCatalog.js`(`catalog.js` が issue #99 で経由をやめた後も `preset.js` だけが使い続けていた)経由でプリセットを取得していたが、`drillCatalog.js` の `createCatalogEntries()` はカタログ構築時点でデフォルト状態の `item.buildParams(defaultState)` を1回だけ呼んで結果を凍結する([[./drillCatalog.js]] 参照)。設定画面でユーザー操作のたびに `buildParams(state)` を呼び直す必要があるインタラクティブなUIとは根本的に非互換なため、`item` を生のまま受け取る形に変更した(`preset.js` 側の変更は [[./preset.js]] 参照)。

### KaTeX の CSS import を `preset.js` 側に置いた理由

`frontend/web` の node:test 群(`test_frontend_web` = `node --test frontend/web/src/drillPresets.test.js frontend/web/src/presetDetail.test.js`)は Vite を経由せず素の Node ESM ローダーで `presetDetail.js` を直接 import する。plain CSS の `import 'katex/dist/katex.min.css'` を `presetDetail.js` に書くと `ERR_UNKNOWN_FILE_EXTENSION` でテストが即失敗するため、CSS import は Vite バンドル経由でのみ読み込まれる `preset.js`(`preset.html` のページエントリ)側に置いた。JS 本体の `import katex from 'katex'` は katex パッケージが `exports.import` に ESM ビルド(`dist/katex.mjs`)を持つため `presetDetail.js` 内のままで node:test からも問題なく解決できる。

### 出題形式:筆算の例題チップモックアップ(issue #134)

- `buildWrittenExampleTex(example)` は `WRITTEN_EXAMPLE_RE`(`/^(\d+(?:\.\d+)?)([+\-×÷])(\d+(?:\.\d+)?)$/`)で例題文字列を `a`/演算子/`b` に分解する。この形は「出題形式」設定を持つ全18項目の `examples`/`examplesFor`/ライブ例題文字列が共通して従う形であるため(`drillPresets.js` 参照)、他の記法(分数・矢印付きなど)への対応は不要。
- `buildWrittenAddSubMulTex(example)`(add/sub/mul用): 単一の右揃え列(`\begin{array}{r} a \\ opb \\ \hline \end{array}`)を使い、小数の場合も int/frac に分割した専用列は作らない。理由: (1) add/sub は `a_decimal_places === b_decimal_places` が常に保証される(`drillPresets.js` 側で対称にしか使っていない)ため、文字列全体をそのまま右揃えするだけで両オペランドの末尾(=小数部の最終桁)が揃い、結果として小数点も自動的に揃う。(2) mul の筆算の慣習はそもそも小数点揃えではなく末尾(一の位)揃えであり、これも単純な右揃えと一致する。当初は KaTeX `array` の3列(整数部/`.`/小数部)構成で小数点を明示的に揃える実装を試みたが、KaTeX は LaTeX の `r@{.}l`(カスタム列区切り `@{...}`)に非対応で、独立した `.` 列にすると標準の列間余白のせいで「整数+.+小数」がバラバラの記号に見える見た目になり(実機確認・ユーザー指摘により)不採用とした。
- `buildWrittenDivTex(example)`(div用): `${b} \overline{\big)\,${a}}`(除数、大きめの右括弧、被除数の上に横線)で長除法の枠を近似する。KaTeX は MathJax 拡張の `\enclose{longdiv}{...}` に非対応(`Undefined control sequence` を実機確認済み)なため、`\overline`+`\big)` の組み合わせで代替した。この近似は例題チップ(プレビュー)専用で、実際に生成される PDF は `backend/nuts_calc_tex.py` が vendor済み `longdivision` パッケージで独立に描画する([[../../../../backend/nuts_calc_tex.py]] 参照)。
- `renderWrittenExampleHtml(example)`(非export)は `buildWrittenExampleTex()` の結果を `katex.renderToString(tex, { throwOnError: false })`(横書き同様インラインモード)で描画し、`null`(未知の形)の場合のみ `renderExampleHtml()` にフォールバックする(対象18項目では理論上発生しない防御的分岐)。

## 統合ポイント

- 呼び出し元: `preset.js`(`preset.html` のページエントリ。KaTeX の CSS も `preset.js` 側で import する、上記参照)。
- 呼び出し先: `katex`(`katex.renderToString()`、issue #132)、`strings.js`(`t`)、`verticalLayout.js`(`isVerticalOperation`。`generatePdf()` の PDF レイアウト分岐と、設定画面の例題チップ表示分岐の両方から呼ばれる、issue #134)、`icons.js`(`ICONS.chevronLeft`、プレビュー画面ヘッダーのみ、issue #126)、`pageHeader.js`(`pageHeaderHtml`、設定画面ヘッダー、issue #157)、`backend`(`POST /generate-pdf`、`POST /generate-problems`(issue #139。対象アイテムの例題チップ取得のみ、リクエストボディの構築は `item.buildParams` の出力に `paper_size`/`num` を足すだけで `POST /generate-pdf` と共有)、`http://127.0.0.1:5000` 固定)、`item.examplesFor`/`item.buildParams`/`item.pointKey`(`drillPresets.js` 側の項目定義、[[./drillPresets.js]] 参照)。

## 注意事項・既知の制限

- backend の URL がハードコードされている点は `frontend/spa` と同じ既知の制約([[../../frontend/spa/src/CustomGenerator.jsx]] 参照)。
- `preset.html` は元々静的な `<header class="app-header"><h1>100マス計算ジェネレーター</h1></header>` を持っていたが、このファイルが描画する設定画面の見出し(旧: 独立した `<h3 class="preset-detail-title">`)と重複していた(issue #126)ため、静的ヘッダーを削除し本ファイル側の `<header>` に一本化した([[./home.js]] 参照)。設定画面の見出しはその後 issue #132 で `.catalog-header` パターンへ再度差し替わっている(上記「動作の概要」参照)。
- 完了画面のPDFサムネイルは実PDFレンダリングではなく静的なCSS装飾(`.completion-thumbnail`)。confettiも静的CSS(アニメーションなし)。例題チップは1行表示(wireframeは2行)。いずれもissue #100のスコープ簡略化として意図的に採用した。
- `frontend/web` は複数ページ構成(issue #88、ユーザー要望)。本モジュールは `preset.html` 用の独立した「マウント可能なウィジェット」として設計されている(`customGenerator.js` と同じパターン、issue #97 で `customGenerator.js` 自体は削除済み)。
- 非活性な設定ボタンはHTMLの `disabled` 属性とクリックハンドラ双方で変更を拒否する(`frontend/web/src/presetDetail.js:169-172,374-383`)。
- `POST /generate-problems` は `backend/problem_generation.py` の実装上 `command_type: 'ope'` の素の二項演算のみ対応(issue #138)のため、`frac`/`mixed`/`gcd`/`lcm`/`divisors`/`multiples`/`evenodd`/`divfrac`/`frac2dec`/`dec2frac`/`squ`/`aBc`/`99`(dan指定あり)系アイテムは `isLivePreviewSupported()` が常に false を返し、#135 由来の静的 `examples`/`examplesFor` のまま変わらない。これらコマンド種別を live 化する場合は issue #166 の子issue(#167-#174、`command_type` ごとの別コマンド)側でバックエンドを対応させてから、本ファイルの `isLivePreviewSupported()` の許可条件を広げる形になる想定(issue #139 での意図的なスコープ分割)。

## 変更履歴（git log より自動生成）

- aca0f4f feat(#134): add 出題形式 (式/筆算) setting to add/sub/mul/div preset detail pages
- 81e0b2d #139 frontend/web: switch preset detail example previews to live backend generation (#177)
- 9b366c1 #157 Add per-grade/per-drill header descriptions via a shared page header component (#160)
- 06870bb #148 Add multiplication-table question-order options (#150)
- 1d8ee60 #135 frontend/web: switch preset detail page example problems based on selected settings (#141)
- 2d9ee47 #132 frontend/web: dynamic grade accent, KaTeX fraction examples, generalized setting hints, and move problem count into common settings on preset detail page (#136)
- 1bb0f69 #126 frontend/web: add missing wireframe icons and unify page headers (#127)
- 90864a5 refactor(frontend/web): replace hand-drawn nav/UI icons with Material Symbols
- 9d1371e #100 frontend/web: rebuild preset detail settings/completion/preview screens (#118)
- 25532c5 #88 Restructure into backend/+frontend/{spa,web} and add a static frontend/web implementation (#89)
