# `web/frontend/src/drillPresets.test.js`

## 目的・役割

学年別プリセットのID、パラメータ、LaTeX専用フラグをNode標準テストランナーで検証する。

## 動作概要

比較カードについて、4年生の同分母・同分子、5年生の異分母と各発展カードが `compare` と正しい `comparison_pattern` を使うことを確認する。さらに全カードのタイトル・説明キーが日英翻訳辞書に存在することを検証する（`web/frontend/src/drillPresets.test.js:160-191`）。

## 統合ポイント

対象は `drillPresets.js` と `public/locales/{ja,en}/translation.json` である。
