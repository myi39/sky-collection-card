# Special Card Reveal — Design Spec
Date: 2026-05-08

## Overview

カルーセルの最後のカード（07）の右に秘密の「もう一枚」を仕込む。ユーザーが右スワイプの流れで発見し、`image999.jpg` が上からゆっくり降ってきて着地する演出。

---

## ヒント要素（Ghost Slot）

- カルーセルtrack内の `players.length`（= index 7）番目の位置にゴーストスロットを配置
- スロットの幅はカード幅と同じ（位置計算を既存ロジックに合わせる）
- 内容は `and...` テキスト ＋ `▶` 三角のみ（カードなし）
- スタイル：
  - `▶` はほんのり金色（`rgba(255, 230, 120, 0.55)` 程度）で薄ぼんやり光る
  - パルスアニメーションは控えめ（`box-shadow` の opacity 変化のみ、glow 小さめ）
  - 全体 opacity は低め（0.5〜0.6）— 押しつけがましくない

---

## トリガー

- `nearestCard()` と `startInertia()` の上限を `players.length`（index 7）まで拡張
- `current === players.length` になった瞬間に `triggerReveal()` を呼び出す
- `render()` が `current === players.length` のとき info-panel・dots は非表示
- **重複防止**: `let revealing = false` フラグを用意し、`triggerReveal()` 呼び出し時に `true` にセット、カルーセル復帰完了後に `false` へ戻す。`updateHighlight()` 内では `if (!revealing)` の場合のみ呼ぶ

---

## シーン遷移（reveal）

### フェーズ1：フェードアウト（約1.2s）

- カルーセル・info-panel・dots・flip-hint を `opacity: 0` へトランジション
- 背景色（`#080810`）はそのまま — 暗転ではなく「溶けて消える」感覚
- フェードが完了したら carousel を `visibility: hidden` に

### フェーズ2：落下＋回転（約2.8s）

- `special-card` 要素（`image999.jpg` 表示、カードと同サイズ）を画面上部 `translateY(-110vh)` に配置
- アニメーション：
  - **落下**: `translateY(-110vh)` → `translateY(0)` — `cubic-bezier(0.12, 0.8, 0.3, 1)`（ゆっくり落ちる、終端でやわらかく止まる）
  - **回転**: Y軸で `rotateY(0deg)` → `rotateY(1080deg)`（3回転）— 落下と同じ duration
  - duration: `2.8s`
- 着地位置はカルーセルの通常カード高さと同じ（`carousel-wrap` の縦中央）

### フェーズ3：着地後の静止（約1.2s待機）

- アニメーション完了後、1.2秒間そのまま静止

### フェーズ4：カルーセル復帰（約0.8s）

- `carousel`・info-panel・dots・flip-hint を `opacity: 0 → 1` でぼんやり浮かび上がらせる
- このとき `current === players.length` のままなので、**special-card スロットがセンター**に来た状態でカルーセルが現れる
- オーバーレイ用の `#special-card-overlay` は `opacity: 0` にフェード → 非表示にする（カルーセル内スロットに切り替わる）
- 左スワイプでカード07へ戻れる、右スワイプで special-card に戻れる

---

## 復帰後のカルーセル状態

- カルーセルは合計 `players.length + 1` 枚構成になる（07 までのカード ＋ special-card）
- `players.length` 番目のスロットは通常カードと同じ見た目で `image999.jpg` を表示
- **タップでフリップ**（半回転）：他のカードと同じ `doFlip()` 挙動。裏面は別途定義（emoji・名前・説明）
- ゴーストスロットのヒント（`and... ▶`）は演出完了後は非表示になる
- navdots には special-card 分の1点が追加される

---

## 変更スコープ

| 対象 | 変更内容 |
|------|----------|
| CSS | ゴーストスロット・パルス・`#special-card-overlay` のスタイル追加 |
| HTML | `carousel-wrap` 内に `#special-card-overlay` div 追加 |
| JS `players` / `specialCard` | special-card データを別定数で定義、reveal 後にカルーセルへ追加 |
| JS `nearestCard()` | 上限を `players.length`（reveal後は `players.length + 1 - 1`）に変更 |
| JS `startInertia()` | `minOff` の計算対象を動的上限に変更 |
| JS `buildDots()` | reveal前はゴーストスロット分を除いた数でドット描画 |
| JS `render()` | `current === players.length`（reveal前）のとき info-panel を空にする |
| JS `doFlip()` | 変更なし（special-card スロットも同じロジックで動く） |
| JS `triggerReveal()` | 新規追加：フェーズ1〜4を制御 |
| JS `updateHighlight()` | `current === players.length` かつ `!revealing` でトリガー呼び出し |

---

## Special Card のデータ定義

```js
const specialCard = {
  num: "??",
  name: "&You",          // 画像上部の文字から
  desc: "",              // 裏面の説明文（未定ならブランク可）
  emoji: "✦",
  frontImg: "images/image999.jpg"
};
```

---

## 対象外（スコープ外）

- 複数回 reveal できるかの制御 — 今回は毎回トリガー可（`revealing` フラグでアニメ重複は防ぐ）
