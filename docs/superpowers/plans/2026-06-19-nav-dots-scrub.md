# 目次ドットのスクラブ ＋ plan_b 整理 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** plan_b を正式なメイン（`sky_collection_card.html`）に整理し、目次ドット（`.nav-dots`）を iPhone ホーム画面風になぞって移動できるようにする。

**Architecture:** 単一HTMLファイル（バニラJS＋Three.js）。ファイル整理→死にコード掃除→スクラブ実装の3フェーズ。各フェーズ末でユーザー確認後にコミット。自動テスト基盤は無いため、検証はブラウザでの手動確認（`serve` スキルでローカル配信、またはファイルを直接開く）。

**Tech Stack:** HTML / バニラJS / Pointer Events API / CSS keyframes / Three.js（既存）

## Global Constraints

- 対象ファイルは `sky_collection_card_plan_b.html`（フェーズ1で `sky_collection_card.html` にリネーム後はそちら）。
- `index.html`（プレースホルダー）と `3d_test.html`（テスト用）は触らない。
- 退避は削除ではなく `archive/` への移動。履歴保持のため `git mv` を使う。
- 依頼範囲外の UI レイアウト・文言・コード構造の変更はしない。
- ブランチ: `feat/nav-dots-scrub`（作成済み）。
- 行番号は編集で前後するため、本計画では「アンカー（特定の文字列）」で位置を示す。各編集前にその文字列を検索して現在地を確認すること。
- 弾みの強さ（scale 1.6 / 120ms）と振動量（10ms）は調整可能な値として実装。

---

## Phase 1 — ファイル整理 ＋ セレクタ除去

### Task 1: ファイルをアーカイブ移動・リネームし、セレクタUI／遷移リンクを除去

**Files:**
- Move: `sky_collection_card.html` → `archive/sky_collection_card_image.html`
- Move: `sky_collection_card_plan_a.html` → `archive/sky_collection_card_plan_a.html`
- Rename: `sky_collection_card_plan_b.html` → `sky_collection_card.html`
- Modify: `sky_collection_card.html`（リネーム後 = 旧 plan_b）

**Interfaces:**
- Produces: メインファイル `sky_collection_card.html`（旧 plan_b）。以降のタスクはすべてこのファイルを編集対象とする。

- [ ] **Step 1: アーカイブ先フォルダを用意し、画像版を退避**

名前衝突を避けるため、先に既存の `sky_collection_card.html` を退避する。

```bash
mkdir -p archive
git mv sky_collection_card.html archive/sky_collection_card_image.html
```

- [ ] **Step 2: 案Aを退避**

```bash
git mv sky_collection_card_plan_a.html archive/sky_collection_card_plan_a.html
```

- [ ] **Step 3: plan_b をメイン名にリネーム**

```bash
git mv sky_collection_card_plan_b.html sky_collection_card.html
```

- [ ] **Step 4: セレクタ UI（HTML）を削除**

`sky_collection_card.html` 内の以下のブロック（アンカー `<select id="viewModeSel">`）を丸ごと削除する。

削除する内容:
```html
<select id="viewModeSel">
  <option value="image">現在（画像）</option>
  <option value="plan-a">案A（3Dに置換）</option>
  <option value="plan-b" selected>案B（ボタンで3D）</option>
</select>
```

- [ ] **Step 5: 遷移リンク（JS）を削除**

アンカー `// View mode selector — navigate to corresponding HTML file` から始まる以下のブロックを削除する。

削除する内容:
```js
// View mode selector — navigate to corresponding HTML file
const MODE_FILES = {
  'image':  'sky_collection_card.html',
  'plan-a': 'sky_collection_card_plan_a.html',
  'plan-b': 'sky_collection_card_plan_b.html',
};
document.getElementById('viewModeSel').addEventListener('change', e => {
  const target = MODE_FILES[e.target.value];
  if (target) window.location.href = target;
});
```

- [ ] **Step 6: setViewMode 内のセレクタ参照を削除**

`setViewMode` 関数内の以下の1行（アンカー `document.getElementById('viewModeSel').value = mode;`）を削除する。これを残すと削除した select を参照して実行時エラーになる。

削除する行:
```js
  document.getElementById('viewModeSel').value = mode;
```

- [ ] **Step 7: CSS のセレクタ用スタイルを削除**

アンカー `#viewModeSel {` で始まる CSS ルールブロックを丸ごと削除する（`}` まで）。

- [ ] **Step 8: ブラウザで手動検証**

`serve` スキルでローカル配信し、スマホ／PCで `sky_collection_card.html` を開く。確認項目:
- カルーセルが表示され、左右スワイプでカードが移動する
- 「3Dで見る」ボタンで3Dモーダルが開く
- 右下のモード切替セレクタが**消えている**
- ブラウザのコンソールにエラーが出ていない（特に `viewModeSel` 関連の null 参照エラーが無い）

> このフェーズでは内部の plan-a / 画像描画コードはまだ残す。エラーが出ないことだけ確認する。

- [ ] **Step 9: ユーザー確認を待つ**

問題が無いことをユーザーに確認してもらってから次へ。

- [ ] **Step 10: コミット**

```bash
git add -A
git commit -m "refactor: make plan_b the main file and archive other variants

- archive image/plan-a variants under archive/
- rename plan_b -> sky_collection_card.html
- remove view-mode selector UI and navigation links

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Phase 2 — 死にコードの掃除

### Task 2: plan-a / 画像モード用の死にコードを除去

**Files:**
- Modify: `sky_collection_card.html`

**Interfaces:**
- Consumes: Task 1 の成果（メインファイル、セレクタ除去済み）。
- Produces: plan-b（カルーセル＋「3Dで見る」→モーダル3D）専用に縮約されたファイル。`setViewMode` は廃止され、起動時に `.btn-3d` を表示する初期化のみが残る。

- [ ] **Step 1: resetBtn / planA-reset 系が plan-b でも使われるか検証**

除去判断の前に、`.planA-reset-show` / `@keyframes planAResetAppear` / `resetBtn` を全文検索し、plan-b の動作（カルーセル・3Dモーダル）で使われているか確認する。

Run: 対象ファイルを `resetBtn` / `planA-reset` / `planAResetAppear` で検索
判断:
- plan-a 専用（モード切替や planA_* からのみ参照）なら除去対象に含める。
- plan-b でも使う（3Dモーダルのリセットボタン等）なら**残す**。
この検証結果を Step 6 の除去範囲に反映する。

- [ ] **Step 2: render() 内の plan-a フックを削除**

アンカー `if (typeof planA_onCardChange === 'function') planA_onCardChange();` の行を削除する。

- [ ] **Step 3: 案A 3D描画一式を削除**

アンカー `let planARenderer = null` から `function planA_onCardChange()` の定義終わり（`{ /* all cards always rendered */ }`）までの一連の関数・変数を削除する。対象:
- `planARenderer` / `planAAnimId` / `planAScenes` / `planACameras` / `planAModels` の宣言
- `planA_animate()` 関数全体
- `planA_init()` 関数全体（`async function planA_init()`）
- `planA_onCardChange()` 関数全体
- これらに付随する resize リスナー等、`planARenderer` を参照する箇所

削除後、ファイル内に `planA` を含む識別子が残っていないことを検索で確認する（resetBtn の判断は Step 1 に従う）。

- [ ] **Step 4: setViewMode を plan-b 固定の初期化に置き換え**

アンカー `function setViewMode(mode) {` から関数末尾までを削除し、代わりに「`.btn-3d` を表示する」だけの初期化に置き換える。

置き換え後:
```js
// ─── Init (plan-b only) ───────────────────────────────────
function showCardButtons() {
  document.querySelectorAll('.btn-3d').forEach(btn => {
    btn.style.display = 'block';
  });
}
```

- [ ] **Step 5: 末尾の setViewMode 呼び出しを置き換え**

アンカー `setViewMode('plan-b');` を以下に置き換える。

```js
showCardButtons();
```

- [ ] **Step 6: 残りの plan-a / image 専用要素を削除**

以下を削除する（Step 1 の判断を反映）:
- JS: `let viewMode = 'image';` の宣言、および `viewMode` を参照する分岐（例: `viewMode !== 'plan-a'` 等）。`viewMode` 参照が無くなるよう全て解消する。
- HTML: `<canvas id="canvas-plan-a"></canvas>`（アンカー `id="canvas-plan-a"`）
- CSS: `#canvas-plan-a` ルール、`body.viewmode-plan-a ...` ルール
- （Step 1 で plan-a 専用と判断した場合のみ）`@keyframes planAResetAppear` / `.planA-reset-show` と、`resetBtn` 関連コード

削除後、ファイル内を `viewMode` / `plan-a` / `planA` / `canvas-plan-a` / `viewmode-plan` で検索し、意図せぬ残骸が無いことを確認する。

- [ ] **Step 7: ブラウザで手動検証**

`serve` で配信し `sky_collection_card.html` を開く。確認項目:
- カルーセル左右スワイプ、ドットのタップ移動が従来通り
- 「3Dで見る」ボタン → 3Dモーダルが開く・閉じる
- BGM ボタン、リビール演出（特殊カード）など既存機能に影響なし
- コンソールにエラー・未定義参照が無い

- [ ] **Step 8: ユーザー確認を待つ**

ユーザーが確認し問題なければ次へ。

- [ ] **Step 9: コミット**

```bash
git add -A
git commit -m "refactor: remove dead plan-a/image rendering code

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Phase 3 — 目次ドットのスクラブ実装

### Task 3: `.nav-dots` をスクラブ対応にする

**Files:**
- Modify: `sky_collection_card.html`

**Interfaces:**
- Consumes: 既存の `navDots`（コンテナ要素）, `current`（現在のインデックス）, `players`（配列）, `revealDone` / `SPECIAL_IDX`（リビール状態）, `navigateTo(idx)`, `buildDots()`, `render()`, `isUIElement(el)`。
- Produces: スクラブ可能なドット列。タップ／なぞりの両方で `navigateTo` 経由でカード移動し、切替時に視覚 pop ＋（Android のみ）振動。

- [ ] **Step 1: カルーセルドラッグとの衝突を防ぐ（isUIElement に .nav-dots を追加）**

アンカー `function isUIElement(el) {` の return を以下に変更する。これで `.nav-dots` 上の pointerdown/touchstart がカルーセルの document レベルドラッグを起動しなくなる。

変更前:
```js
function isUIElement(el) {
  return !!el.closest('nav, .footer-line, button, select, a');
}
```
変更後:
```js
function isUIElement(el) {
  return !!el.closest('nav, .footer-line, button, select, a, .nav-dots');
}
```

- [ ] **Step 2: CSS に pop アニメーションと touch-action を追加**

アンカー `.dot { width: 5px;` の行（ドットのCSS定義群）の直後に以下を追加する。`.nav-dots` の `touch-action: none` は縦スクロールによる横なぞりの妨害を防ぐ。

```css
  .nav-dots { touch-action: none; }
  @keyframes dot-pop {
    0%   { transform: scale(1); }
    45%  { transform: scale(1.6); }  /* 弾みの強さ（調整可） */
    100% { transform: scale(1); }
  }
  .dot.pop { animation: dot-pop 120ms ease-out; }  /* 弾みの速さ（調整可） */
```

> 注: `.nav-dots` には既存ルールがある。重複定義を避けたい場合は既存の `.nav-dots {` ブロック内に `touch-action: none;` を1行追加してもよい。

- [ ] **Step 3: pendingPop フラグを宣言**

アンカー `const navDots = document.getElementById("navDots");` の直後に以下を追加する。

```js
let pendingPop = false; // 次の buildDots で active ドットを弾ませる
```

- [ ] **Step 4: navigateTo に変化検出・pop・振動を追加**

アンカー `function navigateTo(idx) { current = idx; render(); }` を以下に置き換える。

```js
function navigateTo(idx) {
  if (idx === current) return;       // 同じカードなら何もしない
  pendingPop = true;                 // buildDots で弾ませる
  if (navigator.vibrate) navigator.vibrate(10); // Android のみ反応・iOS は無視
  current = idx;
  render();
}
```

- [ ] **Step 5: buildDots を改修（click 廃止・pop 付与）**

アンカー `function buildDots() {` の関数全体を以下に置き換える。各ドットの個別 `click` リスナーを廃止し（スクラブの統一ハンドラに移行）、`pendingPop` が立っていれば新 active ドットに `pop` クラスを付ける。

```js
function buildDots() {
  navDots.innerHTML = "";
  if (current === SPECIAL_IDX && !revealDone) return; // reveal前はdots非表示
  const count = revealDone ? players.length + 1 : players.length;
  for (let i = 0; i < count; i++) {
    const d = document.createElement("div");
    d.className = "dot" + (i === current ? " active" : "");
    if (i === current && pendingPop) d.classList.add("pop");
    navDots.appendChild(d);
  }
  pendingPop = false;
}
```

- [ ] **Step 6: スクラブ用ポインタハンドラを追加**

アンカー `function navigateTo(idx)` の置換後ブロックの直後に、以下を追加する。`.nav-dots` コンテナにハンドラを一度だけ付与する（ドットは render ごとに作り直されるが、コンテナは永続するため capture が外れない）。位置判定は、active ドットの幅変化で中心がずれるのを避けるため、**pointerdown 時に端点（先頭/末尾ドット中心）を一度だけキャッシュして線形マッピング**する。

```js
// ─── Nav-dots スクラブ（iPhone ホーム画面風） ───────────────
let scrubbing = false;
let scrubFirstC = 0, scrubLastC = 0, scrubCount = 0;

function cacheScrubGeometry() {
  const dots = navDots.querySelectorAll('.dot');
  scrubCount = dots.length;
  if (scrubCount === 0) return;
  const firstR = dots[0].getBoundingClientRect();
  const lastR  = dots[scrubCount - 1].getBoundingClientRect();
  scrubFirstC = firstR.left + firstR.width / 2;
  scrubLastC  = lastR.left + lastR.width / 2;
}

function scrubIndexFromX(clientX) {
  if (scrubCount <= 1) return 0;
  const span = scrubLastC - scrubFirstC;
  const ratio = span === 0 ? 0 : (clientX - scrubFirstC) / span;
  const idx = Math.round(ratio * (scrubCount - 1));
  return Math.max(0, Math.min(scrubCount - 1, idx));
}

navDots.addEventListener('pointerdown', e => {
  if (current === SPECIAL_IDX && !revealDone) return; // reveal前はドット無し
  if (!navDots.querySelector('.dot')) return;
  e.preventDefault();
  e.stopPropagation();
  scrubbing = true;
  navDots.setPointerCapture(e.pointerId);
  cacheScrubGeometry();
  navigateTo(scrubIndexFromX(e.clientX));
});

navDots.addEventListener('pointermove', e => {
  if (!scrubbing) return;
  e.preventDefault();
  navigateTo(scrubIndexFromX(e.clientX));
});

function endScrub(e) {
  if (!scrubbing) return;
  scrubbing = false;
  try { navDots.releasePointerCapture(e.pointerId); } catch (_) {}
}
navDots.addEventListener('pointerup', endScrub);
navDots.addEventListener('pointercancel', endScrub);
```

- [ ] **Step 7: ブラウザで手動検証（PC）**

`serve` で配信し PC で開く。マウスで:
- ドット列を押した瞬間、その位置のカードへ移動する（タップ＝ジャンプ）
- 押したまま左右にドラッグすると、カードが指（カーソル）に追従して次々移動する
- 切り替わるたびに active ドットがピクッと弾む
- カルーセル本体のドラッグと干渉しない（ドット操作中にカルーセルが別挙動しない）
- コンソールエラーなし

- [ ] **Step 8: ブラウザで手動検証（スマホ実機）**

`serve` スキルで Tailscale 経由配信し、iPhone と（可能なら）Android で開く。確認:
- 指でドット列をなぞるとカードが追従移動する
- 縦スクロールに邪魔されず横なぞりできる
- タップでのジャンプも効く
- Android では切替時に軽く振動する（iPhone は振動しないが動作は同じ＝想定通り）
- pop アニメーションが見える

- [ ] **Step 9: コミット**

```bash
git add -A
git commit -m "feat(nav-dots): add iPhone-style scrub to navigate cards

- drag along the dot strip to scrub through cards (pointer events)
- tap still jumps to a card
- visual pop on change + vibrate(10) on Android
- guard against carousel drag conflict via isUIElement

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Self-Review（計画作成者による確認）

**Spec coverage:**
- フェーズ1（ファイル整理＋セレクタ除去）→ Task 1 ✓
- フェーズ2（死にコード掃除、resetBtn 依存検証含む）→ Task 2 ✓
- フェーズ3（スクラブ＋pop＋Android振動、最近傍/端点キャッシュ、カルーセル干渉対策、リビール整合）→ Task 3 ✓
- 非対象（iOSハプティクス・効果音・plan-a維持）→ 実装しない方針で各タスクに反映 ✓

**Placeholder scan:** 各コード変更ステップに実コードを記載。プレースホルダー無し。Step 1（Task2）の検証結果に応じた分岐は、判断基準を明記済み。

**Type consistency:** `navigateTo(idx)` / `buildDots()` / `pendingPop` / `scrubbing` / `cacheScrubGeometry()` / `scrubIndexFromX()` / `endScrub()` / `showCardButtons()` の名称は全タスクで一貫。
