# `backend/problem_generation.py`

## 目的・役割

`backend/app.py` の `POST /generate-problems` エンドポイント(issue #138)が呼び出す、PDF/LaTeX を一切生成しない「問題データのみ生成」ロジック。`renderers.py`(サブプロセス経由で `nuts_calc.py`/`nuts_calc_tex.py` を実行し PDF を作る、プレゼンテーション層)とは責務を分離した、データ層のモジュール。issue #166「データ層とプレゼンテーション層の分離」の最初の実装であり、以降の他コマンド対応は同issue配下の native sub-issue(#167-#174)で扱う。

`command_type == 'ope'`(素の2項四則演算 + issue #168 の `--use-parentheses`/`--missing-value`/`--terms`系(`terms`/`terms_min`/`terms_max`/`mixed_operators`)3亜種)に加え、issue #169 で `com`/`99`/`aBc`/`squ`/`pi`、issue #170 で `frac`/`mixed`、issue #171 で `compare`、issue #172 で `evenodd`/`multiples`/`divisors`/`lcm`/`gcd` を実装した。`100` は意図的に対象外のまま(下記「`100` を対象外のままにしている理由」参照)。それ以外の `command_type`(`simplify`/`commondenom`/`frac2dec`/`dec2frac`/`divfrac` の残り5コマンド)は `ValueError` を送出する(issue #166 の残り sub-issue #173 で対応予定)。

## 動作の概要

- `generate_problems(params, renderer_name=None)`(公開関数): `renderer_name` 省略時は `renderers.get_renderer_name()` で解決。`num`(生成する問題数)が正の整数でない場合は `command_type` に関わらず `ValueError` を送出する(`problem_generation.py:58-60`)。`command_type == 'ope'` は `_generate_ope_problems()` へ委譲する。それ以外は `_COMMAND_GENERATORS`(`command_type` 文字列 → 生成関数の dict、`problem_generation.py:466-474`)を引き、未登録の `command_type`(`100` を含む)は `ValueError` を送出する(`problem_generation.py:65-71`)。
- `com`/`99`(kuku)/`aBc`/`squ`/`pi` はそれぞれ `_generate_com_problems`/`_generate_kuku_problems`/`_generate_abc_problems`/`_generate_squ_problems`/`_generate_pi_problems` が対応する。`nuts_calc_tex.py` の同名 `generate_*_problems()` を直接呼び出すだけの薄いラッパーで、reportlab/latex の分岐を持たない(下記「新規 family が reportlab 分岐を持たない理由」参照)。`a_value` が必須なコマンド(`com`/`99`/`squ`/`pi`)は未指定を明示的な `ValueError` で拒否し、`com` はさらに `nuts_calc_tex.MIN_COMPLEMENT_TARGET` 未満の `a_value` を拒否する(いずれも `nuts_calc_tex.py` の `_init()` が CLI 引数に対して行うバリデーションと同じ制約をリクエストパラメータに対して再現したもの)。`99`/`squ`/`pi` の `descend`/`shuffle` はどちらも既定 `False`。いずれも `_dataclass_to_dict()` で dict 化してから返す(`problem_generation.py:288-333`)。
- `frac`/`mixed`(issue #170)はそれぞれ `_generate_frac_problems`/`_generate_mixed_problems` が対応する。この2コマンドはエンドポイントが argparse を経由しないため、`nuts_calc_tex.py` の `_init()` が CLI 引数に対して行うバリデーションをリクエストパラメータに対して再現している(`ope` 亜種の `_determine_ope_variant()` と同じパターン、下記「`frac`/`mixed` の CLI バリデーションを再現している理由」参照)。両コマンド共通の `numerator_digits`/`denominator_digits` 範囲チェックは `_validate_fraction_digits()` に、`reducible_mode` の operator 制約チェックは `_validate_reducible_operators()` に共通化している(`problem_generation.py:336-353`)。
    - `_generate_frac_problems`: `same_denominator`×`different_denominators` 排他、`proper_operands` 指定時の `numerator_digits <= denominator_digits` 制約、`a_fraction_form`/`b_fraction_form` が `'proper'` でない場合の operator(`['add']`/`['sub']` のみ)・`'improper'` 不可制約、`reducible_mode` 指定時の operator(`{mul,div}` の部分集合)制約を検証したうえで `nuts_calc_tex.generate_fraction_problems(...)` を呼び出す(`problem_generation.py:355-393`)。
    - `_generate_mixed_problems`: `decimal_places` 範囲チェック、`_determine_mixed_terms()`(`terms`/`terms_min`/`terms_max`/`mixed_operators` から `nuts_calc_tex.resolve_term_range(..., use_parentheses=False)` で範囲を解決 — `mixed` に `--use-parentheses` 相当のオプションはないため常に `False` を渡す)、`reducible_mode` 指定時の operator 制約・`terms` 系との併用禁止・`{a_kind, b_kind}` が `{('fraction',), ('int',)}` である制約を検証したうえで `nuts_calc_tex.generate_mixed_problems(...)` を呼び出す(`_determine_mixed_terms`: `problem_generation.py:396-417`、`_generate_mixed_problems`: `problem_generation.py:420-458`)。
- `compare`(issue #171)は `_generate_compare_problems` が対応する。`numerator_digits`/`denominator_digits` 範囲チェックは `frac`/`mixed` と同じ `_validate_fraction_digits()` を再利用する。`decimal_places`(既定1)の範囲チェックは `mixed` と同じ値域(`MIN_DECIMAL_PLACES`〜`MAX_DECIMAL_PLACES`)。`a_kind`/`b_kind`(既定 `['fraction']`、`mixed` と異なり compare は分数のみが既定 — 後方互換のため)を解決したうえで、`comparison_pattern`(既定 `'different-denominators'`)が非既定でありながら `a_kind`/`b_kind` のどちらかが `['fraction']` でない場合は `ValueError` にする(`nuts_calc_tex.py` の `_init()` と同じ制約、下記「`compare` の kind 混在バリデーションを再現している理由」参照)。`nuts_calc_tex.generate_fraction_comparison_problems(...)` を呼び出した後、各 `FractionComparisonProblem` を `_dataclass_to_dict()` で dict 化し、`relation`(`@property`、`FractionComparisonProblem` の実フィールドではない)を明示的に追加してから返す(`intermediate_memo` と同じ「計算プロパティは明示キーで追加」パターン、`problem_generation.py:461-505` 付近)。
- `evenodd`/`multiples`/`divisors`(issue #172)はそれぞれ `_generate_evenodd_problems`/`_generate_multiples_problems`/`_generate_divisors_problems` が対応する。3コマンドとも `a_min`/`a_max`(既定1/9、`a_value` ショートハンドは非対応 — `nuts_calc_tex.py` の `_init()` 側でもこの3コマンドは `set_min_max_value()` 変換の対象コマンドリストに含まれていないため)から `nums_a` を組み立て、`nuts_calc_tex.generate_evenodd_problems`/`generate_multiples_problems`/`generate_divisors_problems` を直接呼び出す。`multiples`/`divisors` は `a_min < 1` を `ValueError` で拒否する(`nuts_calc_tex.py` の `_init()` と同じ制約)。`multiples` はさらに `multiples_count`(既定 `nuts_calc_tex.DEFAULT_MULTIPLES_COUNT`)が `nuts_calc_tex.MIN_MULTIPLES_COUNT` 未満なら拒否する。`lcm`/`gcd`(issue #172)は共有ヘルパー `_generate_number_pair_problems(params, num, compute)` の薄いラッパー `_generate_lcm_problems`/`_generate_gcd_problems`(`compute=math.lcm`/`math.gcd`)が対応する。この2コマンドは `nuts_calc_tex.py` 側で `a_value`/`b_value` ショートハンドの対象コマンドに含まれるため、`_resolve_ope_range()` を再利用して `a_min`/`a_max`/`b_min`/`b_max` を解決したうえで `nuts_calc_tex.generate_number_pair_problems(compute, nums_a, nums_b, num, 1)` を呼び出す(下記「`lcm`/`gcd` で生成関数を1つ共有している理由」参照)。いずれの5コマンドも `_dataclass_to_dict()` で dict 化してから返す(`problem_generation.py:507-565`)。
- `_determine_ope_variant(params)` で `use_parentheses`/`missing_value`/`terms`系フラグから対象亜種(`'tree'`/`'missing_value'`/`'multi_term'`/`None`)を判定する。この関数はエンドポイントが argparse を経由しないため、`nuts_calc_tex.py` の `_init()` が CLI 引数に対して行う相互排他バリデーション(`--missing-value` は `--use-parentheses`/`--terms`系と併用不可)と `resolve_term_range()` による term数レンジのフロー・クランプ(`--use-parentheses` はフロア3、それ以外はフロア2、上限は `MAX_OPE_TERMS`)を、リクエストパラメータに対して再現する(`problem_generation.py:93-137`)。
- 亜種が判定された場合(`variant is not None`)、`renderer_name == 'reportlab'` なら即座に `ValueError`(`nuts_calc.py` に対応実装がないため)。それ以外は以下へディスパッチする(`_generate_ope_problems()`、`problem_generation.py:74-90`):
    - `'tree'` → `_generate_tree_ope_problems`: `nuts_calc_tex.generate_tree_ope_problems(...)` を直接呼び出し、`TreeOpeProblem` dataclass のリストを返す。
    - `'missing_value'` → `_generate_missing_value_problems`: `nuts_calc_tex.generate_missing_value_problems(...)` を直接呼び出し、`MissingValueProblem` dataclass のリストを返す。
    - `'multi_term'` → `_generate_multi_term_ope_problems`: `nuts_calc_tex.generate_multi_term_ope_problems(...)` を直接呼び出し、`MultiTermOpeProblem` dataclass のリストを返す。
    - いずれも `_dataclass_to_dict()`(後述の JSON contract 節を実装する汎用コンバータ、`problem_generation.py:140-153`)で dict 化してから返す。
- 亜種が判定されなかった場合(素の2項 `ope`)は既存どおりレンダラーごとに `_generate_ope_problems_reportlab`/`_generate_ope_problems_latex` に分岐する。
    - reportlab: `nuts_calc.get_operation_data(nums_a, nums_b, operator, order=num, print_index=1, intermediate=intermediate)` をそのまま呼び出し、戻り値のタプル(`data_index, vals_a, operator_mark, vals_b, equal_marks, vals_c`、`intermediate=True` 時はさらに `vals_aabb` を含む8要素)を1問題1dictへ変換する。演算子記号(`+`/`-`/`×`/`÷`)は `SYMBOL_TO_OPERATOR_NAME` で `add`/`sub`/`mul`/`div` へ正規化する(latex側の表現と統一するための表示用マッピングであり、生成ロジックの複製ではない)。
    - latex: `nuts_calc_tex.generate_ope_problems(...)` を呼び出し、返る `OpeProblem` dataclass のリストをそのままdictへ変換する。`intermediate=True` の場合は `nuts_calc_tex.build_intermediate_memo(a, b)`(既存の純粋関数、LaTeXマークアップを含まないプレーンテキストを返す)を再利用してメモ文字列を追加する。
- `a_value`/`b_value`(桁数指定のショートハンド)は `nuts_calc.set_min_max_value()`(後述、両レンダラーで共用)経由で `a_min`/`a_max`/`b_min`/`b_max` に変換する。指定がなければ `a_min=1`/`a_max=9`/`b_min=1`/`b_max=9`(両CLIのデフォルトと同値)を使う。この解決は3亜種の生成関数でも共通利用する。
- `intermediate=True` の場合(素の2項 `ope` のみ)、`operator == ['mul']` かつ `b_max <= SINGLE_DIGIT_MAX`(reportlab)/`INTERMEDIATE_SINGLE_DIGIT_MAX`(latex、いずれも値は9)であることを検証し、`_init()` の CLI バリデーションと同じ制約を(`exit(1)` ではなく)`ValueError` として再現する。

## 重要な設計判断とその理由

### サブプロセス+`--csv`読み取りではなく、プロセス内直接呼び出しを選んだ理由

当初は `--csv` フラグを付けてサブプロセス実行し、生成された PDF を破棄して CSV だけ読み取る案を検討したが、「データ層とプレゼンテーション層を完全に分離したい」という将来方針(issue #166)に反する(PDFを一度実際に生成してから捨てる無駄が残り、CSVの列構成もコマンドごとにバラバラで意味づけできない)ため却下した。`get_operation_data()`/`generate_ope_problems()` がどちらも PDF/LaTeX 非依存の純粋関数だったため、プロセス内直接呼び出しが可能だった。

### `nuts_calc.set_min_max_value()` を両レンダラーで共用している理由

`nuts_calc.py`/`nuts_calc_tex.py` は元々それぞれ独立に同一の桁数→範囲テーブルを `_init()` 内にネストした関数として持っていた(コード共有なしの2スクリプトのため)。今回 `nuts_calc.py` 側だけをモジュールレベル関数に抽出し(`nuts_calc.py:90-95`)、`nuts_calc_tex.py` は変更していない。latex分岐でも同じ関数を再利用しているのは、2つの完全に同一のテーブルを本ファイルに二重に持つよりも、既存の(モジュールレベル化済みの)実装を再利用する方が「複製しない」原則に合うと判断したため。`nuts_calc_tex.py` 自身の `_init()` 内の同名ネスト関数はそのまま残っている(CLIパスは変更していない)。

### `ope` 以外を明示的に `ValueError` で拒否している理由

`evenodd`/`multiples` 等、`ope` 以外の残り約19コマンド(issue #167 決定時点)は、それぞれ別の生成関数を使い、出力の型(fraction・真偽値・リスト等)も `ope` の a/b/operator/result 形とは異なる。1つのissue(#138)でこれら全てを実装すると、データ層のレスポンス形状(envelope)の設計判断を全コマンド分一度に確定させることになりスコープが過大になるため、issue #166 のsub-issue群(#167でアーキテクチャ決定、#168で `ope` 亜種、#169-#173で残りコマンド群)へ意図的に分割した(`frac`/`mixed` は #170、`compare` は #171 で実装済み、残り10コマンドは #172-#173 で対応予定)。未対応の呼び出しは黙って無視/変換せず、明示的なエラーメッセージで失敗させる。

### `ope` 亜種の相互排他バリデーション・term数レンジ解決を `nuts_calc_tex.py` から再現している理由(issue #168)

`POST /generate-problems` は argparse を経由しないため、`nuts_calc_tex.py` の `_init()` が担う「`--missing-value` は `--use-parentheses`/`--terms`系と併用不可」「`terms_min` <= `terms_max`」「`--use-parentheses` は term数フロアが3」等のバリデーション・デフォルト解決を、`_determine_ope_variant()` がリクエストパラメータに対して独自に再現する必要がある。ロジックを複製せず、フロア・上限のクランプ計算自体は `nuts_calc_tex.resolve_term_range()`(モジュールレベル関数、`TERM_COUNT_FLOOR_DEFAULT`/`TERM_COUNT_FLOOR_PARENTHESES`/`MAX_OPE_TERMS` を使用)をそのまま再利用している(`problem_generation.py:129`)。

### `frac`/`mixed` の CLI バリデーションを再現している理由(issue #170)

`ope` 亜種と同じ事情で、`frac`/`mixed` も argparse を経由しないため、`nuts_calc_tex.py` の `_init()` が担うバリデーション(`frac`: `same_denominator`×`different_denominators` 排他、`proper_operands` の digit 制約、`a/b_fraction_form` の operator/improper 制約。`mixed`: `decimal_places` 範囲、`terms` 系のクランプ、`reducible_mode` の operand-kind 制約)を `_generate_frac_problems`/`_generate_mixed_problems` が独自に再現する。両コマンドに共通する `numerator_digits`/`denominator_digits` 範囲チェックと `reducible_mode` の operator 制約チェックは、`_determine_ope_variant()` 同様ロジックを複製しないよう `_validate_fraction_digits()`/`_validate_reducible_operators()` として1箇所に集約し、`_generate_frac_problems`/`_generate_mixed_problems` の双方から呼び出している(`problem_generation.py:336-353`)。`mixed` の `_determine_mixed_terms()` は `terms`/`terms_min`/`terms_max`/`mixed_operators` から `terms_options_given` を判定し、`nuts_calc_tex.resolve_term_range()` を再利用する点も `_determine_ope_variant()` と同じパターンだが、`mixed` に `--use-parentheses` 相当のオプションは存在しないため `resolve_term_range()` の `use_parentheses` 引数は常に `False` を渡す。

### `compare` の kind 混在バリデーションを再現している理由(issue #171)

`nuts_calc_tex.py` の `_init()` は、`compare` の `--a-kind`/`--b-kind` が `['fraction']`(既定)以外のとき、`--comparison-pattern`(`same-denominator`/`same-numerator`)を明示的に拒否する(int の分母は常に1、decimal の分母は常に `10**decimal_places` のため、この2パターンは分数vs分数の場合しか意味を持たない)。この endpoint は argparse を経由しないため、`_generate_compare_problems` が同じ制約(`a_kind`/`b_kind` が既定 `['fraction']` から外れているのに `comparison_pattern` も非既定なら `ValueError`)をリクエストパラメータに対して再現する。`different-denominators`(既定パターン)のまま kind 混在する場合はエラーにしない — `nuts_calc_tex.generate_fraction_comparison_problems()` 自身が kind 混在時にパターンフィルタを内部でスキップするため(`nuts_calc_tex.py.md` の `compare` セクション参照)、int vs int のような組み合わせでも無限リトライにならない。

### `command_type` ディスパッチを if/elif から dict テーブルへ置き換えた理由(issue #169)

issue #167 の JSON contract 規約が事前に決定していた設計(下記「非-`ope` コマンド群向け JSON contract 規約」節の「`command_type` の許可判定」箇所)を issue #169 で初めて適用した。`_COMMAND_GENERATORS: dict[str, Callable]` に `command_type` 文字列と生成関数を1行ずつ追加するだけで新規コマンドを登録でき、共有の分岐チェーンを編集しないため、残り sub-issue(#172-#173)が並行作業してもコンフリクトしにくい。`ope` だけは `_determine_ope_variant`/`renderer_name` 分岐を持つため、`_generate_ope_problems()` として `generate_problems()` 内に個別の早期分岐を残し、テーブルには含めていない。

### `100` を対象外のままにしている理由(issue #169)

`nuts_calc_tex.generate_hundred_square()` は「`num` 個の問題」ではなく単一の `HundredSquareTable`(`left_values`/`top_values`、`answers` プロパティで加算表を計算)を返す。既存の `{"problems": [...]}` envelope は「`num` 個の同型 item のリスト」を前提としており、単一テーブルはこの意味論に合わない。`HundredSquareTable` 用に別 envelope 形状を新設する案もあるが、それは issue #167 相当のスコープを持つ契約決定であり、本 issue 単体で決めるには重すぎると判断した。両フロントエンド(`frontend/spa`/`frontend/web`)とも現状 `command_type: 'ope'` のプリセットにしか `/generate-problems` を呼んでおらず、実利用の圧力もない。既存の「未対応の組み合わせは黙って無視せず明示的に `ValueError` で失敗させる」慣習を踏襲し、`_COMMAND_GENERATORS` に `100` のエントリを追加せず、`generate_problems()` の「not yet supported」`ValueError` にフォールスルーさせている(`problem_generation.py:65-71`)。別 envelope 形状での対応が必要になった場合は、別 issue として起票する。

### `ope` 亜種の reportlab 対応を持たない理由

`nuts_calc.py` は `--use-parentheses`/`--missing-value`/`--terms`系のいずれにも対応実装がないため、亜種フラグが判定された状態で `renderer_name == 'reportlab'` の場合は生成関数を呼ばずに `ValueError` を送出する(`problem_generation.py:76-81`)。素の2項 `ope` のみ reportlab/latex 両対応を維持する。

### `lcm`/`gcd` で生成関数を1つ共有している理由(issue #172)

`nuts_calc_tex.py` 自身が `lcm`/`gcd` の2コマンドを `generate_number_pair_problems(compute, nums_a, nums_b, order, start_index)` 1関数(`compute=math.lcm`/`math.gcd` で呼び分け、`nuts_calc_tex.py:3909-3925`)に集約しており、CLI側の `build_number_pair_pages(ini, compute, label)`(`nuts_calc_tex.py:3959-3969`)も同じパターンを踏襲している。`problem_generation.py` 側でも `_generate_com_problems`/`_generate_kuku_problems` のように2つの独立した関数を書くのではなく、共有ヘルパー `_generate_number_pair_problems(params, num, compute)` + `compute` だけを固定する薄いラッパー2つ(`_generate_lcm_problems`/`_generate_gcd_problems`)にした。これは issue #169 の「非-`ope` コマンド群向け JSON contract 規約」節が事前に想定していた設計(下記「`command_type` の許可判定」箇所)でもある。

### `evenodd`/`multiples`/`divisors` が `a_value` ショートハンドに対応しない理由(issue #172)

`nuts_calc_tex.py` の `_init()` は `a_value`/`b_value` → `set_min_max_value()` による桁数ショートハンド変換を `command in ('ope', '100', 'lcm', 'gcd', 'divfrac')` のときのみ適用しており(`nuts_calc_tex.py:530`)、`evenodd`/`multiples`/`divisors` はこの対象コマンドリストに含まれていない(CLIでは `--a-min`/`--a-max` を直接指定する)。エンドポイント側もこの挙動をそのまま再現し、3コマンドとも `_resolve_ope_range()`(`a_value` ショートハンド対応)ではなく `params.get("a_min", ...)`/`params.get("a_max", ...)` を直接読む。

### 非-`ope` コマンド群向け JSON contract 規約(issue #167 決定、issue #168 で `ope` 亜種として初実装、issue #169 で `com`/`99`/`aBc`/`squ`/`pi`、issue #170 で `frac`/`mixed`、issue #171 で `compare`、issue #172 で `evenodd`/`multiples`/`divisors`/`lcm`/`gcd` に適用)

issue #166 の sub-issue #167 で、残り約19個の `nuts_calc_tex.py` コマンド生成関数(`generate_com_problems`/`generate_kuku_problems`/`generate_abc_problems`/`generate_squ_problems`/`generate_pi_problems`/`generate_evenodd_problems`/`generate_multiples_problems`/`generate_divisors_problems`/`generate_fraction_problems`/`generate_fraction_comparison_problems`/`generate_mixed_problems`/`generate_number_pair_problems`/`generate_simplify_problems`/`generate_commondenom_problems`/`generate_frac2dec_problems`/`generate_dec2frac_problems`/`generate_divfrac_problems`)を `backend/problem_generation.py` へ本実装する #169-#173 が従う契約を以下のとおり決定した。issue #168(`ope` 亜種の `generate_tree_ope_problems`/`generate_multi_term_ope_problems`/`generate_missing_value_problems`)がこの契約の最初の実装であり、`_dataclass_to_dict()`(`problem_generation.py:140-153`)として汎用コンバータ化した。issue #169 で `com`/`99`/`aBc`/`squ`/`pi` の5コマンドがこの契約の2件目の実装として加わった(`ComProblem`/`KukuProblem`/`AbcProblem`/`SquProblem`/`PiProblem`はいずれも `Fraction`/ネスト dataclass フィールドを持たないため、下記の Fraction 変換分岐はこの時点ではまだ未実装だった)。issue #170 で `frac`/`mixed` の2コマンドが3件目の実装として加わり、`FractionProblem.c`/`MixedProblem.result`/`MixedOperand.value` が標準 `Fraction` フィールドを初めて持ち込んだため、下記の Fraction 変換分岐を実装した。issue #171 で `compare` が4件目の実装として加わり、`FractionComparisonProblem.relation`(`@property`)を明示キーで追加するパターンと、`FractionComparisonOperand` の `kind`/`decimal_places` フィールド追加(5キーへの拡張、下記参照)が発生した。issue #172 で `evenodd`/`multiples`/`divisors`/`lcm`/`gcd` の5コマンドが5件目の実装として加わったが、`EvenOddProblem`/`MultiplesProblem`/`DivisorsProblem`/`NumberPairProblem` はいずれも `int`/`list[int]` フィールドのみで `Fraction`/ネスト dataclass を持たないため、既存の変換分岐(Fraction/`FractionOperand`/`FractionComparisonOperand`/ネストdataclass)は素通りする(`list[int]` 変換のみ利用)。残り5コマンド(`simplify`/`commondenom`/`frac2dec`/`dec2frac`/`divfrac`)は #173 で対応予定。

- **envelope**: `{"problems": [...]}` を変更しない(#138 踏襲)。item の形状はコマンド群ごとに異なってよい(単一の汎用スキーマには寄せない)。`TreeOpeProblem`/`MultiTermOpeProblem`/`MissingValueProblem` はそれぞれ独自の形状(`{index, operands, operators, tree, result}`/`{index, operands, operators, mixed, result}`/`{index, a, b, operator, c, blank}`)で返る。
- **item マッピング**: dataclass のフィールド名をそのまま JSON key として使う(`dataclasses.fields()` 相当の1:1変換、`_dataclass_to_dict()` が実装)。非JSONネイティブな値型は以下のとおり変換する:
    - 標準 `Fraction`(`fractions` モジュール) → `{"numerator": f.numerator, "denominator": f.denominator}`(2キー、`whole` は持たない)。issue #170 で実装(`_dataclass_to_dict()` に `isinstance(value, Fraction)` 分岐を追加、`problem_generation.py:151-152`)。`FractionProblem.c`/`MixedProblem.result`/`MixedOperand.value` がこの分岐を通る。
    - `FractionOperand`(`nuts_calc_tex.py:3207-3216`。`numerator`/`denominator`/`whole`(既定0)を持つ) → そのフィールドをそのまま JSON へ写す(3キー)。issue #170 で `FractionProblem.a`/`b`(`FractionOperand`)が最初の実例となった(dataclass の汎用再帰変換のため専用コードは不要)。
    - `FractionComparisonOperand`(`nuts_calc_tex.py:3497-3515` 付近。issue #171 で `kind`/`decimal_places` フィールドを追加) → 同じく全フィールドをそのまま JSON へ写す(`numerator`/`denominator`/`whole`/`kind`/`decimal_places` の5キー、`FractionOperand` より2キー多い)。`kind` が `'int'`/`'fraction'` の場合は `decimal_places` が常に `null`。
    - ネストした dataclass(例: `TreeOpeProblem.tree: ExprTreeNode`、`nuts_calc_tex.py:1668-1686`)は同じ規則を再帰適用する(`left`/`right` が `None` なら `null`、`ExprTreeNode` ならネストした dict)。専用の木シリアライズ形式は起こさない。`_dataclass_to_dict()` は dataclass 判定(`dataclasses.is_dataclass`)とリスト判定を再帰する汎用実装のため、この規則も含め自然に満たす。
    - `list[int]`/`list[str]` フィールド(`MultiTermOpeProblem.operands`/`TreeOpeProblem.operands` 等)はそのまま JSON 配列にする。
- **計算プロパティ(`@property`)の扱い**: 上記の汎用変換は dataclass の実フィールドのみを対象とし、派生プロパティは**自動では含めない**(`_dataclass_to_dict()` は `dataclasses.fields()` のみを走査するため、`@property` は自然に除外される)。#168 の3型(`TreeOpeProblem`/`MultiTermOpeProblem`/`MissingValueProblem`)は計算プロパティを持たないため、この規則は影響しない。既存の `OpeProblemData.intermediate_memo`(`problem_generation.py:46`、`_generate_ope_problems_latex` が `nuts_calc_tex.build_intermediate_memo` を再利用して追加)が、必要に応じて明示キーを追加するパターンの先例。
- **未対応の組み合わせのエラー**: 「issue番号付き `ValueError`」パターンを継続する。新規 family もサポート外のフラグ組み合わせを黙って無視・変換せず、明示的に失敗させる。
- **`command_type` の許可判定**: `command_type` → 生成関数のディスパッチテーブル(`_COMMAND_GENERATORS`)を issue #169 で実装した(`problem_generation.py:573-587`)。各 sub-issue は「関数を1つ追加し、テーブルに1エントリ追加する」だけで済み、共有の分岐チェーンを編集しない(#172-#173 が並行作業してもコンフリクトしにくい)。`nuts_calc_tex.py` 側で既にジェネレータを共有しているコマンド群(`lcm`/`gcd` は `generate_number_pair_problems(compute, nums_a, nums_b, order, start_index)` を `compute=math.lcm`/`math.gcd` で呼び分けるだけ、`nuts_calc_tex.py:3909-3925`)は、`problem_generation.py` 側でも1関数を共有してよい、という想定どおり issue #172 で `_generate_number_pair_problems()` として実際に共有した(詳細は上記「`lcm`/`gcd` で生成関数を1つ共有している理由」参照)。`100` はこのテーブルに意図的にエントリを持たない(上記「`100` を対象外のままにしている理由」参照)。
- **reportlab 分岐は持たない**: `nuts_calc.py` は `['ope', 'com', '100', '99', 'aBc', 'squ', 'pi']` の7コマンドのみを実装しており(`nuts_calc.py:131`)、#167-#173 が対象とする残りコマンドは元から reportlab 側に存在しない。加えて `renderers.get_renderer_name()`(`renderers.py:90-108`)は `NUTS_CALC_RENDERER=reportlab` が明示指定された場合、`problem_generation.generate_problems()` に到達する前(`app.py`の`generate_problems`ハンドラ内)に `ValueError` を送出する(issue #186 以降)。したがって本番の HTTP 経路で `problem_generation.generate_problems()` に渡る `renderer_name` は常に `'latex'` であり、新規 family の生成関数は `_generate_ope_problems_reportlab`/`_generate_ope_problems_latex` のような二重実装を持たず、`nuts_calc_tex.py` を直接呼び出すだけでよい。
- **ファイル構成**: 当面は `problem_generation.py` を単一ファイルのまま維持する(パッケージ分割は本ファイルが概ね800行を超えた時点で再検討する)。

## 統合ポイント

- 呼び出し元: `backend/app.py` の `POST /generate-problems` ルートハンドラ。
- 呼び出し先: `backend/nuts_calc.py`(`get_operation_data`/`set_min_max_value`/`SINGLE_DIGIT_MAX`)、`backend/nuts_calc_tex.py`(`generate_ope_problems`/`generate_tree_ope_problems`/`generate_multi_term_ope_problems`/`generate_missing_value_problems`/`resolve_term_range`/`build_intermediate_memo`/`MIN_DECIMAL_PLACES`/`INTERMEDIATE_SINGLE_DIGIT_MAX`/`TERM_COUNT_FLOOR_DEFAULT`/`generate_com_problems`/`generate_kuku_problems`/`generate_abc_problems`/`generate_squ_problems`/`generate_pi_problems`/`MIN_COMPLEMENT_TARGET`/`generate_fraction_problems`/`generate_mixed_problems`/`generate_fraction_comparison_problems`/`MIN_FRACTION_DIGITS`/`MAX_FRACTION_DIGITS`/`MAX_DECIMAL_PLACES`/`MIXED_OPERAND_KINDS`/`generate_evenodd_problems`/`generate_multiples_problems`/`generate_divisors_problems`/`generate_number_pair_problems`/`DEFAULT_MULTIPLES_COUNT`/`MIN_MULTIPLES_COUNT`)、`backend/renderers.py`(`get_renderer_name`、`RendererRequest` 型)。加えて標準ライブラリ `fractions.Fraction`(`_dataclass_to_dict()` の型判定用、issue #170)、`math`(`math.lcm`/`math.gcd`、issue #172)。

## 注意事項・既知の制限

- `carry_mode`/`remainder_mode`/`result_max`/`a_decimal_places`/`b_decimal_places` は latex レンダラー専用パラメータ(`nuts_calc.py` に対応実装がない)。reportlab選択時にこれらが送られても本モジュールは無視する(`renderers.py`の`build_command`と同じ「呼び出し元がレンダラー情報に基づいて送信可否を制御する」契約を踏襲、明示的なエラーにはしていない)。
- reportlab側の `remainder` は常に `0`(`nuts_calc.py`の`calc_div`は正確に割り切れる組み合わせしか生成しないため、余り制御の概念がない)。latex側は `remainder_mode` 指定に応じて非ゼロになりうる。
- `nuts_calc.py`/`nuts_calc_tex.py` は完全に独立したスクリプトのままで、本ファイルはその両方を `import` する(サブプロセスではなく通常のPythonインポート)。両スクリプトとも `if __name__ == '__main__':` ガード済みのため、importしただけではCLI実行や副作用は発生しない。
- `ope` 亜種(`tree`/`missing_value`/`multi_term`)は `intermediate`/`a_decimal_places`/`b_decimal_places` を一切参照しない(`nuts_calc_tex.generate_tree_ope_problems`/`generate_multi_term_ope_problems`/`generate_missing_value_problems` がいずれもこれらのパラメータを受け付けないため)。これらのフラグが亜種フラグと同時に送られても明示的な `ValueError` にはならず、単に無視される(上記の reportlab 専用パラメータと同じ「未対応パラメータは黙って無視」の既存慣習を踏襲)。
- `com`/`99`/`aBc`/`squ`/`pi`/`frac`/`mixed`/`compare`/`evenodd`/`multiples`/`divisors`/`lcm`/`gcd` は `renderer_name` を一切参照しない(`_COMMAND_GENERATORS` の生成関数は `params`/`num` のみを受け取る)。`reportlab` を明示指定して呼び出しても常に `nuts_calc_tex.py` の実装が動く(`nuts_calc.py` 側にこれらのコマンドはそもそも存在しない)。本番の HTTP 経路では `renderer_name` は常に `'latex'` に解決されるため実害はない(上記「非-`ope` コマンド群向け JSON contract 規約」節の「reportlab 分岐は持たない」箇所参照)。
- `100` は `POST /generate-problems` からは呼び出せない(`ValueError`)。CLI(`nuts_calc_tex.py 100 ...`)や `POST /generate-pdf` からは引き続き利用できる — 本モジュールのみの制限。
- `compare` の `a_kind`/`b_kind`(既定 `['fraction']`)は `mixed` の `MIXED_OPERAND_KINDS` 既定(3種類全て)と異なる。issue #171 以前の分数vs分数のみの挙動を後方互換のまま保つための意図的な非対称で、明示的に `a_kind`/`b_kind` を指定しない限り既存の呼び出し元(両フロントエンドとも現状未使用)の挙動は変わらない。

## 変更履歴(git log より自動生成)

- eb4faa5 feat(#172): support evenodd/multiples/divisors/lcm/gcd in POST /generate-problems
- 490f44b #171 compare: support int/decimal/fraction kind mixing, expose via POST /generate-problems (#192)
- 20b9462 #170 backend: support frac/mixed in POST /generate-problems (#191)
- 2ebbe96 #169 problem_generation.py: support com/99/aBc/squ/pi (and 100's disposition) (#190)
- caedeac #168 problem_generation.py: support ope --use-parentheses/--missing-value/--terms variants (#189)
- 13bef63 #138 backend: add POST /generate-problems for PDF-free ope problem generation (#175)
