# Reference documents

## Elementary mathematics Course of Study

- File: `elementary-course-of-study-mathematics-2017.pdf`
- Title: 小学校学習指導要領（平成29年告示）解説 算数編
- Publisher: 文部科学省
- Published: July 2017
- Source: https://www.mext.go.jp/content/20211102-mxt_kyoiku02-100002607_04.pdf
- Retrieved: 2026-08-06
- SHA-256: `5eebb7f4ddc516aa47451999659596523a888eb68d49ed7dadeb489c2cd27129`

The grade-based fraction presets use the progression summarized on PDF page
48 and explained in each grade chapter:

- Grade 3: simple fraction addition and subtraction (PDF pages 48-49).
- Grade 4: addition and subtraction of fractions with a common denominator
  (PDF page 48).
- Grade 5: addition and subtraction of fractions with unlike denominators
  (PDF page 48).
- Grade 6: multiplication and division of fractions (PDF pages 48 and 292-294).

The grade-based decimal-arithmetic presets (`ope --a-decimal-places`/
`--b-decimal-places`, issue #76) use:

- Grade 3: simple one-decimal-place (1/10 unit) addition and subtraction
  (PDF page 156, unit A(5) 小数の意味と表し方).
- Grade 4: multi-place (1/100 unit) addition and subtraction, plus decimal x
  integer / decimal / integer multiplication and division (PDF page 196,
  unit A(4) 小数の仕組みとその計算).
- Grade 5: decimal x decimal multiplication and division (PDF page 245).

The grade-6 integer/decimal/fraction "mixed" presets (the `mixed` command,
issue #76) use PDF pages 293-294: the "内容の取扱い" note that integer and
decimal multiplication/division shall also be handled by unifying them into
fraction-form calculation, with the worked example "5÷2×0.3" converted to a
fraction product.

This directory stores the authoritative source used to decide curriculum
placement; it is not application runtime data.
