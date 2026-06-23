# Special Card Reveal — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** カルーセル最後のカード（07）の右に金色パルスのヒント（`and... ▶`）を置き、右スワイプで到達すると `image999.jpg` が上からゆっくり回転落下して着地・カルーセルに加わる演出を実装する。

**Architecture:** 単一 HTML ファイル内の純 JS。`players.length` 番目にゴーストスロットを追加し、慣性スワイプで到達した瞬間に `triggerReveal()` を起動。オーバーレイ div で落下アニメーションを行い、完了後にゴーストスロットの card-inner を表示してカルーセルに合流させる。

**Tech Stack:** Vanilla HTML / CSS / JS、ビルドなし。

---

## ファイルマップ

| ファイル | 変更内容 |
|---------|----------|
| `sky_collection_card.html` | CSS・HTML・JS すべて。3タスクに分けて変更 |

---

### Task 1: ゴーストスロット — HTML・CSS・ナビゲーション拡張

**Files:**
- Modify: `sky_collection_card.html`

- [ ] **Step 0: グローバル変数・定数を追加** — `let current = 3;` の直後（`const flipped = ...` の前）に挿入

```js
const SPECIAL_IDX = players.length; // = 7  ゴーストスロットのインデックス
let revealing  = false;             // reveal アニメーション実行中フラグ
let revealDone = false;             // reveal 完了フラグ
```

> ⚠️ `init()` の外・グローバルスコープに置くこと。`render()` / `buildDots()` / `triggerReveal()` すべてから参照する。

- [ ] **Step 1: CSS を追加** — `</style>` の直前に以下を挿入

```css
.carousel-wrap { position: relative; } /* overlay の位置基準に */

.ghost-slot {
  flex: 0 0 auto;
  width: var(--card-w);
  height: var(--card-h);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.5s cubic-bezier(0.25,0.1,0.25,1), opacity 0.5s;
  perspective: 900px;
  cursor: pointer;
}

.ghost-hint {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
  opacity: 0;
  transition: opacity 0.4s;
  pointer-events: none;
}
.ghost-hint.visible { opacity: 1; }

.hint-label {
  font-size: 9px;
  letter-spacing: 0.14em;
  color: rgba(255, 228, 100, 0.55);
  font-family: serif;
  font-style: italic;
}

.hint-arrow {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 1px solid rgba(255, 215, 80, 0.22);
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255, 222, 90, 0.58);
  font-size: 11px;
  animation: hint-pulse 2.8s ease-in-out infinite;
}

@keyframes hint-pulse {
  0%, 100% { box-shadow: 0 0 5px rgba(255, 200, 60, 0.10); }
  50%       { box-shadow: 0 0 13px rgba(255, 200, 60, 0.24); }
}
```

- [ ] **Step 2: ゴーストスロット HTML を `init()` に追加** — `carousel.style.cssText = ...` の直後に以下を挿入

```js
const ghostSlot = document.createElement("div");
ghostSlot.className = "ghost-slot";
ghostSlot.id = "ghost-slot";
ghostSlot.innerHTML = `
  <div class="ghost-hint" id="ghost-hint">
    <span class="hint-label">and...</span>
    <div class="hint-arrow">▶</div>
  </div>
  <div class="card-inner" id="ci-${SPECIAL_IDX}"
       style="display:none;width:var(--card-w);height:var(--card-h);
              position:relative;transform-style:preserve-3d;border-radius:11px;cursor:pointer">
    <div class="card-face">
      <img src="images/image999.jpg" class="card-front-img" alt="&You" draggable="false">
    </div>
    <div class="card-face card-back"
         style="background:linear-gradient(160deg,#141e38 0%,#0a1020 100%);transform:rotateY(180deg);
                display:flex;flex-direction:column;align-items:center;justify-content:center;
                padding:16px 12px;gap:6px">
      <div class="back-emoji">✦</div>
      <div class="back-name">&amp;You</div>
      <div class="back-stat">サンプルテキスト</div>
    </div>
  </div>`;
carousel.appendChild(ghostSlot);
```

- [ ] **Step 3: ゴーストスロットのクリック・タッチハンドラを追加** — Step 2 の直後に挿入

```js
// ゴーストスロット — クリック（PC）
ghostSlot.querySelector(".card-inner").addEventListener("click", () => {
  if (didDrag || !revealDone) return;
  if (current === SPECIAL_IDX) doFlip(SPECIAL_IDX);
});
```

タッチは Task 3 で既存 touchend ハンドラを拡張する。

- [ ] **Step 4: `nearestCard()` の上限を拡張** — `players.length - 1` を `players.length` に変更

```js
function nearestCard(offset) {
  const W = carousel.parentElement.offsetWidth;
  const cardEl = carousel.querySelector(".card-inner");
  const cardW = cardEl ? cardEl.offsetWidth : 240;
  const cw = cardW + 16;
  return Math.max(0, Math.min(players.length, Math.round((W / 2 - cardW / 2 - offset) / cw)));
}
```

- [ ] **Step 5: `startInertia()` の `minOff` を拡張** — `players.length - 1` を `players.length` に変更

```js
const minOff = getBaseOffset(players.length);
```

- [ ] **Step 6: `render()` にゴーストスロットの表示制御を追加** — `render()` 関数内の `adjustTranslate();` の直後に挿入

```js
// ゴーストスロットのスケール/透明度
const gs = document.getElementById("ghost-slot");
if (gs) {
  const d = Math.abs(SPECIAL_IDX - current);
  const scl = d === 0 ? 1.0 : d === 1 ? 0.88 : d === 2 ? 0.75 : 0.60;
  const opc = d === 0 ? 1   : d === 1 ? 0.7  : d === 2 ? 0.3  : 0.08;
  gs.style.transform = `scale(${scl})`;
  gs.style.opacity   = String(opc);
}

// ゴーストヒント — 最後のカードまたはゴーストスロット上で表示
const hint = document.getElementById("ghost-hint");
if (hint && !revealDone) {
  if (current >= players.length - 1) hint.classList.add("visible");
  else hint.classList.remove("visible");
}
```

- [ ] **Step 7: `render()` の info-panel / buildDots を修正** — 既存の `const p = players[current]; infoName...` ブロックを以下に置き換え

```js
if (current < players.length) {
  const p = players[current];
  infoName.textContent = p.name;
  infoDesc.textContent = p.desc;
} else if (revealDone) {
  infoName.textContent = "&You";
  infoDesc.textContent = "サンプルテキスト";
} else {
  infoName.textContent = "";
  infoDesc.textContent = "";
}
```

- [ ] **Step 8: `buildDots()` を修正** — 既存の `buildDots()` 全体を置き換え

```js
function buildDots() {
  navDots.innerHTML = "";
  if (current === SPECIAL_IDX && !revealDone) return; // reveal前はゴーストスロット時にdots非表示
  const count = revealDone ? players.length + 1 : players.length;
  for (let i = 0; i < count; i++) {
    const d = document.createElement("div");
    d.className = "dot" + (i === current ? " active" : "");
    d.addEventListener("click", () => navigateTo(i));
    navDots.appendChild(d);
  }
}
```

- [ ] **Step 9: ブラウザで動作確認**
  - `sky_collection_card.html` を開く
  - カード07まで右スワイプ → さらに右にスワイプ
  - ゴーストスロットが07の右に現れ、`and... ▶` が薄く光ること
  - カード07で `and...` ヒントが見え始めること
  - ゴーストスロットでナビゲーション情報が消え、dotsが消えること
  - 左スワイプでカード07に戻れること

- [ ] **Step 10: コミット**

```
git add sky_collection_card.html
git commit -m "feat: add ghost slot with and... hint and extended navigation bounds"
```

---

### Task 2: 特殊カードオーバーレイ — HTML・CSS

**Files:**
- Modify: `sky_collection_card.html`

- [ ] **Step 1: オーバーレイ HTML を追加** — `<div class="carousel-wrap">` の直後（`<div class="carousel-track" ...>` の前）に挿入

```html
<div id="special-card-overlay"
     style="display:none; position:absolute; top:0; left:0; right:0; bottom:0;
            z-index:20; pointer-events:none; perspective:900px;
            align-items:center; justify-content:center;">
  <div id="special-card-drop"
       style="width:var(--card-w); height:var(--card-h); border-radius:11px;
              overflow:hidden; border:0.5px solid rgba(255,255,255,0.12);
              transform:translateY(-120vh) rotateY(0deg);">
    <img src="images/image999.jpg"
         style="width:100%;height:100%;object-fit:cover;display:block;"
         draggable="false">
  </div>
</div>
```

- [ ] **Step 2: ブラウザで確認** — オーバーレイが画面上に見えないことを確認（`display:none` なので通常時は不可視）

- [ ] **Step 3: コミット**

```
git add sky_collection_card.html
git commit -m "feat: add special-card-overlay element for reveal animation"
```

---

### Task 3: `triggerReveal()` — 全フェーズ実装・post-reveal 統合

**Files:**
- Modify: `sky_collection_card.html`

- [ ] **Step 1: Task 1 Step 0 で定数・フラグを追加済みであることを確認**（`SPECIAL_IDX`・`revealing`・`revealDone` がスクリプト上部にあること）

- [ ] **Step 2: `triggerReveal()` 関数を追加** — `function init()` の直前に挿入

```js
function triggerReveal() {
  if (revealing || revealDone) return;
  revealing = true;
  cancelInertia();

  const infoPanelEl  = document.querySelector(".info-panel");
  const flipHintEl   = document.querySelector(".flip-hint");
  const overlay      = document.getElementById("special-card-overlay");
  const drop         = document.getElementById("special-card-drop");

  // ─── Phase 1: コンテンツをフェードアウト（1.0s） ───
  [carousel, infoPanelEl, navDots, flipHintEl].forEach(el => {
    if (!el) return;
    el.style.transition = "opacity 1.0s ease";
    el.style.opacity    = "0";
  });

  setTimeout(() => {
    carousel.style.visibility = "hidden";

    // ─── Phase 2: 落下 + 回転アニメーション（2.8s） ───
    overlay.style.display = "flex";
    drop.style.transition = "none";
    drop.style.transform  = "translateY(-120vh) rotateY(0deg)";
    drop.getBoundingClientRect(); // reflow

    drop.style.transition = "transform 2.8s cubic-bezier(0.12, 0.8, 0.3, 1)";
    drop.style.transform  = "translateY(0px) rotateY(1080deg)";

    setTimeout(() => {
      // ─── Phase 3: 静止（1.2s） ───

      setTimeout(() => {
        // ─── Phase 4: カルーセル復帰（0.8s） ───
        revealDone = true;

        // ゴーストスロットを特殊カードに切り替え
        document.getElementById("ghost-hint").style.display   = "none";
        document.getElementById(`ci-${SPECIAL_IDX}`).style.display = "block";

        // オーバーレイをフェードアウト
        overlay.style.transition = "opacity 0.6s ease";
        overlay.style.opacity    = "0";

        // カルーセルをぼんやり復帰
        carousel.style.visibility = "visible";
        [carousel, infoPanelEl, navDots, flipHintEl].forEach(el => {
          if (!el) return;
          el.style.transition = "opacity 0.8s ease";
          el.style.opacity    = "1";
        });

        render(); // 8つ目のdot・info-panel を更新

        setTimeout(() => {
          overlay.style.display  = "none";
          overlay.style.opacity  = "1"; // 次回用にリセット
          drop.style.transition  = "none";
          drop.style.transform   = "translateY(-120vh) rotateY(0deg)";
          revealing = false;
        }, 800);

      }, 1200); // Phase 3
    }, 2800);   // Phase 2
  }, 1000);     // Phase 1
}
```

- [ ] **Step 3: `updateHighlight()` から `triggerReveal()` を呼ぶ** — 既存の `updateHighlight()` 内の `if (nearest !== current) {` ブロックの末尾（`}`の直前）に追加

```js
if (current === SPECIAL_IDX && !revealDone) triggerReveal();
```

最終的な `updateHighlight()` は以下になる：

```js
function updateHighlight(offset) {
  const nearest = nearestCard(offset);
  if (nearest !== current) {
    current = nearest;
    carousel.querySelectorAll(".card-slot").forEach((s, i) => {
      s.className = "card-slot " + getClass(i);
    });
    if (current === SPECIAL_IDX && !revealDone) triggerReveal();
  }
}
```

- [ ] **Step 4: `touchend` ハンドラを拡張** — 既存の `touchend` ハンドラ内、`startInertia(...)` の直前に追加（ghost slot タップでフリップできるように）

`if (cardSlot) { ... }` ブロックの直後に挿入：

```js
} else if (!didTouchDrag && dt < 250) {
  const ghostEl = e.target.closest(".ghost-slot");
  if (ghostEl && revealDone && current === SPECIAL_IDX) {
    touchHandled = true;
    setTimeout(() => { touchHandled = false; }, 400);
    carousel.style.transition = "";
    doFlip(SPECIAL_IDX);
    return;
  }
}
```

既存の `startInertia(...)` 呼び出しはそのまま残す。

- [ ] **Step 5: ブラウザで全フロー確認**
  1. カード07まで右スワイプ → さらに右にスワイプ
  2. `and... ▶` が見えること
  3. ゴーストスロットに到達 → 画面コンテンツがフェードアウトすること
  4. `image999.jpg` が上からゆっくり回転しながら落下すること（約2.8s）
  5. 着地後1.2s静止 → カルーセルがぼんやり戻ってくること
  6. 特殊カードが index 7 のカードとしてカルーセルに収まっていること
  7. navdots が8点になっていること
  8. 特殊カードをタップ → フリップすること（PC: クリック、スマホ: タップ）
  9. 左スワイプで07に戻れること

- [ ] **Step 6: コミット**

```
git add sky_collection_card.html
git commit -m "feat: implement triggerReveal with fall animation and post-reveal carousel integration"
```
