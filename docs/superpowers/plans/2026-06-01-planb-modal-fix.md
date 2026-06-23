# Plan B Modal Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Plan B の3Dモーダルを (1) カード画像と同サイズにし、(2) モーダル表示中はカード操作を完全にブロックする。

**Architecture:**
- Issue 1: `#modal-3d-canvas` の CSS サイズを CSS変数 `var(--card-w)` / `var(--card-h)` に切り替える。`openModal3d` は既に `getBoundingClientRect()` でサイズ取得しているためJS変更不要。
- Issue 2: モーダルが開いている間 & 閉じた直後350ms は `modalInteractionBlock` フラグでカード全インタラクションをガードする。閉じた直後のブロックは「tap-through」問題（モーダル閉鎖時の合成clickがカードに届く）への対策。

**Tech Stack:** Vanilla JS, Three.js (OrbitControls), HTML/CSS — ビルドなし

---

**対象ファイル:** `sky_collection_card_plan_b.html` のみ（1ファイル完結）

修正箇所:
- L383-387: `#modal-3d-canvas` CSS
- L1017付近: グローバル変数宣言に `modalInteractionBlock` 追加
- L1075付近: `closeModal3d()` にブロックフラグ設定を追加
- L543-548: `buildCard` 内カードクリックハンドラ
- L817-819: `init` 内 ghostSlot クリックハンドラ
- L860付近: `carousel.addEventListener("touchend", ...)` ハンドラ

---

### Task 1: モーダルキャンバスをカードサイズに変更

**Files:**
- Modify: `sky_collection_card_plan_b.html:383-387`

- [ ] **Step 1: CSS変更**

`#modal-3d-canvas` のCSSを以下に置き換える:

変更前:
```css
#modal-3d-canvas {
  width: min(80vw, 80vh, 500px);
  height: min(80vw, 80vh, 500px);
  border-radius: 14px;
  display: block;
}
```

変更後:
```css
#modal-3d-canvas {
  width: var(--card-w);
  height: var(--card-h);
  border-radius: 11px;
  display: block;
}
```

変更点:
- `width`/`height`: 正方形の `min(...)` → カードと同じCSS変数
- `border-radius`: 14px → 11px（カードと統一）

`openModal3d` 関数内の `canvas.getBoundingClientRect()` は自動的に新サイズを取得するため、JS変更不要。

- [ ] **Step 2: ブラウザで目視確認**

`sky_collection_card_plan_b.html` をブラウザで開き、案B選択状態でカードの「3D で見る ›」をタップ。
期待: モーダルキャンバスがカード画像と同じ縦長サイズで表示される。

- [ ] **Step 3: コミット**

```
git add sky_collection_card_plan_b.html
git commit -m "fix(plan-b): resize 3D modal canvas to match card dimensions"
```

---

### Task 2: モーダル表示中のカード操作ブロック

**Files:**
- Modify: `sky_collection_card_plan_b.html` — 変数宣言・closeModal3d・3箇所のイベントハンドラ

- [ ] **Step 1: グローバルフラグ変数を追加**

`let viewMode = 'image';` の行の直下に以下を追加:

```javascript
let modalInteractionBlock = false;
```

- [ ] **Step 2: closeModal3d にブロック設定を追加**

`closeModal3d` 関数を以下に置き換える:

変更前:
```javascript
function closeModal3d() {
  document.getElementById('modal-3d').classList.remove('open');
  if (modalAnimId) { cancelAnimationFrame(modalAnimId); modalAnimId = null; }
  if (modalRenderer) { modalRenderer.dispose(); modalRenderer = null; }
  modalControls = null;
}
```

変更後:
```javascript
function closeModal3d() {
  document.getElementById('modal-3d').classList.remove('open');
  if (modalAnimId) { cancelAnimationFrame(modalAnimId); modalAnimId = null; }
  if (modalRenderer) { modalRenderer.dispose(); modalRenderer = null; }
  modalControls = null;
  modalInteractionBlock = true;
  setTimeout(() => { modalInteractionBlock = false; }, 350);
}
```

目的: モーダル閉鎖直後にブラウザが合成する tap-through click をブロックするため350msの猶予を設ける。

- [ ] **Step 3: buildCard 内のカードクリックハンドラにガードを追加**

`buildCard` 関数内の以下の行を修正:

変更前:
```javascript
slot.querySelector(".card-inner").addEventListener("click", () => {
  if (didDrag || didTouchDrag || touchHandled) return;
```

変更後:
```javascript
slot.querySelector(".card-inner").addEventListener("click", () => {
  if (modalInteractionBlock || document.getElementById('modal-3d').classList.contains('open')) return;
  if (didDrag || didTouchDrag || touchHandled) return;
```

- [ ] **Step 4: ghostSlot クリックハンドラにガードを追加**

`init` 関数内の以下の行を修正:

変更前:
```javascript
ghostSlot.querySelector(".card-inner").addEventListener("click", () => {
  if (didDrag || touchHandled || !revealDone) return;
```

変更後:
```javascript
ghostSlot.querySelector(".card-inner").addEventListener("click", () => {
  if (modalInteractionBlock || document.getElementById('modal-3d').classList.contains('open')) return;
  if (didDrag || touchHandled || !revealDone) return;
```

- [ ] **Step 5: carousel touchend ハンドラにガードを追加**

`carousel.addEventListener("touchend", ...)` の先頭にガードを追加:

変更前:
```javascript
carousel.addEventListener("touchend", e => {
  const endX = e.changedTouches[0].clientX;
  const dt = Date.now() - ttime;
```

変更後:
```javascript
carousel.addEventListener("touchend", e => {
  if (modalInteractionBlock || document.getElementById('modal-3d').classList.contains('open')) return;
  const endX = e.changedTouches[0].clientX;
  const dt = Date.now() - ttime;
```

- [ ] **Step 6: 動作確認**

1. 「3D で見る」タップ → 3Dモーダルが開く
2. 3Dキャンバス上でドラッグ → 3Dモデルが回転し、カードは動かない
3. モーダル外（背景）タップ → モーダルが閉じ、カードは動かない（350ms以内）
4. モーダル閉鎖後、普通にカードタップ → フリップ動作が正常に動く

- [ ] **Step 7: コミット**

```
git add sky_collection_card_plan_b.html
git commit -m "fix(plan-b): block card interactions while 3D modal is open"
```
