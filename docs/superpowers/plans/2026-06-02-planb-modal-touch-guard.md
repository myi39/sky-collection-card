# Plan B モーダル表示中カルーセル誤操作防止

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 3Dモーダルが開いている間、背後のカルーセルがタッチ/マウス操作で動かないようにする。

**Architecture:** `sky_collection_card_plan_b.html` の `touchstart` / `mousedown` ハンドラにモーダル開閉チェックを追加する。既存の `touchend` ハンドラにはすでにガードがあるが、`touchstart` にガードがないため `touchmove` でカルーセルの `transform` が書き換わってしまう。

**Tech Stack:** Vanilla JS、HTML ファイル直書き

---

## 根本原因の詳細

`sky_collection_card_plan_b.html` の touch イベントフロー（問題発生時）：

```
touchstart (document) ← モーダルチェックなし → carouselDragPending = true, tbaseOff を記録
touchmove  (document) ← モーダルチェックなし → liveOffset 更新, carousel.style.transform 書き換え
touchend   (document) ← ✅ モーダルチェックあり → startInertia をスキップ
```

結果：`touchend` がスキップしても、`touchmove` でカルーセルの CSS transform がすでに変わっているため、モーダルを閉じると位置がずれる。

---

### Task 1: touchstart にモーダルガードを追加

**Files:**
- Modify: `sky_collection_card_plan_b.html:897-906`（touchstart ハンドラ）

現在のコード（line 897-906）:
```js
document.addEventListener("touchstart", e => {
    if (isUIElement(e.target)) return;
    carouselDragPending = true;
    carouselDragActive = false;
    cancelInertia();
    tx = e.touches[0].clientX; ty = e.touches[0].clientY; ttime = Date.now();
    tbaseOff = liveOffset = getBaseOffset(current);
    didTouchDrag = false;
    carousel.style.transition = "none";
}, { passive: true });
```

- [ ] **Step 1: touchstart ハンドラにモーダルガードを追加する**

`isUIElement` チェックの直後に以下を追加：

```js
document.addEventListener("touchstart", e => {
    if (isUIElement(e.target)) return;
    if (document.getElementById('modal-3d').classList.contains('open')) return;
    carouselDragPending = true;
    carouselDragActive = false;
    cancelInertia();
    tx = e.touches[0].clientX; ty = e.touches[0].clientY; ttime = Date.now();
    tbaseOff = liveOffset = getBaseOffset(current);
    didTouchDrag = false;
    carousel.style.transition = "none";
}, { passive: true });
```

- [ ] **Step 2: mousedown ハンドラにも同様のガードを追加する（整合性）**

現在のコード（line 875-882）:
```js
document.addEventListener("mousedown", e => {
    if (isUIElement(e.target)) return;
    cancelInertia();
    drag = true; didDrag = false;
    sx = e.clientX; stime = Date.now();
    baseOff = liveOffset = getBaseOffset(current);
    carousel.style.transition = "none";
});
```

`isUIElement` チェックの直後に追加：

```js
document.addEventListener("mousedown", e => {
    if (isUIElement(e.target)) return;
    if (document.getElementById('modal-3d').classList.contains('open')) return;
    cancelInertia();
    drag = true; didDrag = false;
    sx = e.clientX; stime = Date.now();
    baseOff = liveOffset = getBaseOffset(current);
    carousel.style.transition = "none";
});
```

- [ ] **Step 3: 動作確認**

1. ブラウザで `sky_collection_card_plan_b.html` を開く
2. 「案B（ボタンで3D）」が選択されていることを確認
3. 「3D で見る ›」ボタンをクリックしてモーダルを開く
4. モーダル内の3Dキャンバス外を横にスワイプする
5. モーダルを閉じる（✕ボタンまたは背景タップ）
6. カードの位置がスワイプ前と変わっていないことを確認

- [ ] **Step 4: コミット**

```bash
git add sky_collection_card_plan_b.html
git commit -m "fix(plan-b): block carousel touch/mouse drag while 3D modal is open"
```
