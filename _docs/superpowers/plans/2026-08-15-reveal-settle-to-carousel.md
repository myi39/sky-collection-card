# No.30 リビール演出：着地後にカルーセル定位置へ寄せる Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:**
落下演出のカードが着地したあと、**0.7秒かけて滑らかにカルーセルのカード位置（約68px上）へ移動**してからクロスフェードする。演出明けの「カクッと上にズレる」を解消しつつ、画面いっぱいを使う落下の迫力はそのまま残す。

**方針（対話で決定）:** 選択肢B。「落下は今のまま／静止のあとに定位置へ寄せる」。
選択肢A（着地点そのものを68px上げる）は、演出中は info-panel と nav-dots が非表示のためカードが上寄りに見え、「画面いっぱいを使う演出」という狙いと衝突するため不採用。

---

## 調査結果（実測・コード確認済み）

### 1. ズレの原因：落下カードとカルーセルカードで「中央」の基準が違う

`#special-card-overlay` は `position:absolute; inset:0`（`sky_collection_card.html:586`）で、位置の基準は `.carousel-wrap`。JS が `display:flex`（`:1369`）にするので `align-items:center` が効き、**カードは `.carousel-wrap` の箱の中央に着地**する。

一方 `.carousel-wrap` は `flex-direction:column; justify-content:center`（`:93-96`）で、中身は3つ：

```
.carousel-wrap
├── .carousel-track   ← カルーセルのカードはこの中にいる
├── .info-panel
└── .nav-dots
```

3つを合わせたブロックが縦中央に置かれるため、カルーセルのカード中心は箱の中央より `(info-panel + nav-dots) / 2` だけ**上**にある。

| 要素 | 高さ | 内訳 |
|---|---|---|
| `.info-panel`（`:200-208`） | 94px | `margin-top 14px` + `min-height 80px` |
| `.nav-dots`（`:245-254`） | 43px | `padding 16px` + ドット `5px` + `padding 22px` |
| 合計 | 137px | |

**ズレ = 137 / 2 ≒ 68px**（`max-width:480px` では info-panel の margin が 10px になり約 66px / `:291`）。

### 2. `#ghost-slot` を実測すれば、画面サイズによらず正確な差分が取れる

- `#ghost-slot` は演出中の中央スロットで、演出後に No.30 のカードへ置き換わる（`:1332-1340`）。高さは `var(--card-h)` とカードと同一（`:300-301`）。
- 置き換えは **Phase 4**（`:1393`）なので、Phase 3 の時点では DOM に残っている。
- `render()` が `gs.style.transform = scale(...)` を掛ける（`:1193`）が、`transform-origin` は既定の中心。**中心のY座標はスケールの影響を受けない**ため、`top + height/2` で測れば安全。
- 演出中 `carousel` は `opacity:0` だが、`getBoundingClientRect()` は opacity に影響されない。

→ 68px を直書きせず、毎回実測する。ブレークポイントや将来のレイアウト変更でも再びズレない。

### 3. 座標系：`.carousel-wrap` のスケールは演出時に必ず 1

`.carousel-wrap` は `transform: scale(1.04)` → `.revealed` で `scale(1)`（`:512-516`）。`.revealed` はローディング完了時に付く（`:1717`）。演出は `current === SPECIAL_IDX` になった時＝ユーザーがカルーセル末尾までスワイプした時に発火する（`:1002`）ので、**必ずローディング完了後**。よって画面px＝ローカルpxで、スケール補正は不要。

### 4. 既存タイムライン（`triggerReveal()` / `:1349-1423`）

| 時刻 | 出来事 |
|---|---|
| 0s | Phase 1：カルーセル・info・dots を 1s でフェードアウト |
| 0.1s | Phase 2：オーバーレイ表示、カードを `startY`（箱の上端の真上）へ |
| 1.1s | Phase 2b：落下開始（`transform 6s linear`）＋ `card-spin 8s` 開始 |
| 7.1s | 着地（落下完了） |
| 9.1s | スピン完了 → **Phase 3：静止 1.2s** |
| 10.3s | Phase 4：`revealLockedCards()` ＋ クロスフェード（overlay 0.6s out / carousel 0.8s in） |
| 11.1s | 後片付け（overlay を display:none、`fall` を `startY` へリセット） |

`card-spin` は `rotateY` のみ（`:347-351`）なので縦位置に影響しない。

**この 1.2s の静止を「0.4s 静止 → 0.7s 移動 → 0.1s 間」に分割すれば、Phase 4 以降の時刻は一切変わらない。**

---

**Tech Stack:** `sky_collection_card.html` の JS のみ（`triggerReveal()` 周辺）。CSS・HTML 変更なし。

## Global Constraints

- 対象ファイル: `sky_collection_card.html` のみ。
- **CSS と HTML は変更しない。** レイアウト（`.carousel-wrap` の構造、info-panel/nav-dots の高さ）はそのまま。
- **Phase 4 以降の時刻を変えない。** 追加する「静止＋移動＋間」の合計は既存の 1200ms に収める。
- 68px などの実測値をコードに直書きしない。必ず `#ghost-slot` から算出する。
- 行番号は編集でずれるため、位置はアンカー文字列で示す。各編集前に検索して現在地を確認すること。
- 検証は `serve` スキルでのブラウザ手動確認（PC＋スマホ実機）。

---

## Task 1: ズレ量を実測するヘルパー関数を追加

**Files:**
- Modify: `sky_collection_card.html`（`function triggerReveal() {` の直前）

**Interfaces:**
- Produces: `carouselOffsetY(overlayEl) -> number`
  - 引数 `overlayEl`: `#special-card-overlay` の DOM 要素
  - 戻り値: 落下カードの着地点からカルーセル中央カードの中心までの縦差分（px、上方向が負）。`#ghost-slot` が無い等の想定外時は `0`（＝従来どおり箱の中央に着地）。

- [ ] **Step 1: ヘルパー関数を追加**

アンカー `function triggerReveal() {` を検索し、その**直前**に以下を挿入する。

```js
// Phase 3b でカードを寄せる距離。オーバーレイは .carousel-wrap 全体に敷かれて
// いるのでカードはその中央に着地するが、カルーセルのカードは info-panel と
// nav-dots の分（実測で約68px、480px以下では約66px）だけ上にいる。
// 値を直書きするとブレークポイントや将来のレイアウト変更で再びずれるため、
// 毎回 #ghost-slot を測って差分を取る。
//
// #ghost-slot は演出中の中央スロットで、高さはカードと同一（--card-h）。
// Phase 4 の revealLockedCards() で No.30 に置き換わるので、それより前にしか
// 測れない点に注意。render() が scale() を掛けることがあるが、transform-origin は
// 既定の中心なので「中心のY」はスケールの影響を受けない。
// carousel は opacity:0 だが getBoundingClientRect() は opacity に影響されない。
// .carousel-wrap の scale はローディング完了時に 1 に戻っており（.revealed）、
// 演出はそれより後にしか起きないため、画面px＝translateYのpxとして扱ってよい。
function carouselOffsetY(overlayEl) {
  const ghost = document.getElementById("ghost-slot");
  if (!ghost) return 0;
  const g = ghost.getBoundingClientRect();
  const o = overlayEl.getBoundingClientRect();
  if (!g.height || !o.height) return 0;
  return (g.top + g.height / 2) - (o.top + o.height / 2);
}
```

- [ ] **Step 2: コンソールで戻り値を確認**

`serve` で配信してブラウザで開く。ローディングと音の扉を通過したあと、演出前の状態で DevTools コンソールに以下を貼る。

```js
carouselOffsetY(document.getElementById('special-card-overlay'))
```

期待: **-60 〜 -75 程度の負の数**（PC・広い画面で約 -68）。ウィンドウ幅を 480px 以下に狭めて再実行すると約 -66 になる。

- 正の数、または 0 が返る場合は計算の向きが逆／`#ghost-slot` が取れていない。先に進まず原因を潰すこと。

---

## Task 2: Phase 3 を「静止 → 移動 → 間」に分割

**Files:**
- Modify: `sky_collection_card.html`（`triggerReveal()` 内の Phase 3 ブロック）

**Interfaces:**
- Consumes: Task 1 の `carouselOffsetY(overlayEl)`
- Produces: Phase 4 の開始時刻は従来どおり（Phase 3 開始から 1200ms 後）

- [ ] **Step 1: タイミング定数を追加**

アンカー `function carouselOffsetY(overlayEl) {` を検索し、その**直前**に以下を挿入する。

```js
// Phase 3 の内訳。合計は従来の静止時間 1200ms と同じにしてあり、
// Phase 4（カルーセル復帰）以降の時刻は変わらない。
const SETTLE_HOLD_MS = 400;   // 着地したカードを見せる静止
const SETTLE_MOVE_MS = 700;   // カルーセル定位置へ寄せる時間
const SETTLE_BEAT_MS = 100;   // 到着してからクロスフェード開始までの間
```

- [ ] **Step 2: Phase 3 のブロックを差し替え**

アンカー `// ─── Phase 3: 静止（1.2s） ───` を検索する。

変更前:
```js
      setTimeout(() => {
        // ─── Phase 3: 静止（1.2s） ───

        setTimeout(() => {
          // ─── Phase 4: カルーセル復帰（0.8s） ───
          revealDone = true;
```

変更後:
```js
      setTimeout(() => {
        // ─── Phase 3: 静止（0.4s） ───

        setTimeout(() => {
          // ─── Phase 3b: カルーセルの定位置へ寄せる（0.7s） ───
          // ここで詰めておかないと、Phase 4 のクロスフェードで
          // 約68px ぶんカードが飛んで見える。
          fall.style.transition = `transform ${SETTLE_MOVE_MS}ms cubic-bezier(0.22, 1, 0.36, 1)`;
          fall.style.transform  = `translateY(${carouselOffsetY(overlay)}px)`;

          setTimeout(() => {
            // ─── Phase 4: カルーセル復帰（0.8s） ───
            revealDone = true;
```

続けて、この `setTimeout` の**閉じ側**を合わせる。アンカー `}, 1200); // Phase 3` を検索する。

変更前:
```js
        }, 1200); // Phase 3
      }, 8000);   // Phase 2b
```

変更後:
```js
          }, SETTLE_MOVE_MS + SETTLE_BEAT_MS); // Phase 3b: 移動 → 間
        }, SETTLE_HOLD_MS);                    // Phase 3: 静止
      }, 8000);                                // Phase 2b
```

> 注: Phase 4 のブロック全体が1段深くなる。閉じ括弧の対応がずれやすいので、編集後に Phase 4 内の `}, 800);`（後片付けのタイマー）までインデントと括弧が合っているか目視で確認すること。

- [ ] **Step 3: 後片付けが Phase 3b の transition を残さないことを確認**

アンカー `overlay.style.display  = "none";` を含む後片付けブロック（Phase 4 の 800ms 後）を読む。既に以下があるため**変更不要**。ただし目視で確認すること。

```js
fall.style.transition  = "none";
fall.style.transform   = `translateY(${startY}px)`;
```

`transition = "none"` で Phase 3b の 700ms transition が打ち消され、`startY` へ瞬間復帰する。ここが残っていると次回演出の初期化が 700ms かけて動いてしまう。

- [ ] **Step 4: 構文チェック**

```bash
node --check sky_collection_card.html 2>/dev/null || echo "HTMLなのでnode --checkは不可。ブラウザのコンソールでエラーが出ないことで確認する"
```

`serve` で配信してブラウザで開き、**DevTools コンソールに SyntaxError が出ていないこと**を確認する。括弧の対応を間違えるとページ全体の JS が死に、ローディングから先へ進めなくなるので、この確認は必須。

---

## Task 3: 手動検証

**Files:** なし（検証のみ）

- [ ] **Step 1: 演出を通しで見る**

`serve` で配信。ローディング → 音の扉 → カルーセルを右端までスワイプして「and...」のゴーストスロットを中央に持ってくると演出が始まる。

確認項目:
1. カードが上から落ちてくる範囲は**従来どおり画面いっぱい**（狭くなっていない）
2. 着地後、0.4秒ほど止まってから **すっと約68px 上へ移動**する
3. 移動が終わってからカルーセルがフェードインし、**No.30 のカードが飛ばずにその場に居座る**
4. 演出全体の長さが従来と変わらない（体感 11秒前後）

- [ ] **Step 2: スマホ実機で確認**

`serve` スキルの Tailscale 配信で実機を開き、同じ4点を確認する。特に **480px 以下のブレークポイントでもズレが残らないこと**（`.info-panel` の margin が 14px → 10px に変わる）。

- [ ] **Step 3: 演出を最後まで見ないケースの確認**

演出中に画面を触る／別タブに切り替えて戻る、を試し、カードが変な位置で止まらないこと・カルーセルが正常に復帰することを確認する。

> 補足: 再テストのたびにページを再読み込みする必要がある（`revealDone` はページ読込ごとにリセット）。落下の6秒を待たずに確認したい場合は、コンソールから `triggerReveal()` を直接呼べる。

- [ ] **Step 4: ユーザー確認を待つ**

移動の速さ（`SETTLE_MOVE_MS`）と静止の長さ（`SETTLE_HOLD_MS`）は好みが割れるところなので、実際に見てもらって調整する。合計が 1200ms を超えると Phase 4 以降が後ろにずれる点だけ注意（それ自体は問題ないが、意図した変更かを確認する）。

- [ ] **Step 5: コミット**

```bash
git add sky_collection_card.html docs/superpowers/plans/2026-08-15-reveal-settle-to-carousel.md
git commit -m "feat: リビール演出の着地後にカードをカルーセル定位置へ寄せる

落下カードは .carousel-wrap の中央に着地するが、カルーセルのカードは
info-panel と nav-dots の分だけ上にいるため、演出明けに約68px 飛んでいた。

Phase 3 の静止 1.2s を「静止0.4s → 移動0.7s → 間0.1s」に分割し、
着地後に定位置へ滑らかに寄せてからクロスフェードする。合計時間は
据え置きなので Phase 4 以降のタイミングは変わらない。

ズレ量は #ghost-slot の矩形から毎回算出する。480px ブレークポイントで
info-panel の margin が変わるため、直書きだと再びずれるのを避けた。

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Self-Review（計画作成者による確認）

**Spec coverage:**
- 「落ちてから滑らかに移動してカルーセル表示に戻る」→ Task 2 Step 2（Phase 3b、700ms ease-out）✓
- 「画面いっぱいの落下は残す」→ `startY` と Phase 2b の 6s 落下は無変更 ✓
- 「演出明けのズレをなくす」→ Task 1 の実測ベース算出 ✓

**調査の裏付け:**
- ズレの原因（オーバーレイの基準箱が `.carousel-wrap` 全体）はコードで確認済み（`:586`, `:93-96`, `:608-615`）
- ズレ量 68px は CSS の実値から算出（info-panel 94px + nav-dots 43px の半分）
- `#ghost-slot` が Phase 3 時点で DOM に残ることを確認（置換は Phase 4 の `:1393`）
- scale がかかっても中心Yが不変であることを利用（`transform-origin` 既定）
- `.carousel-wrap` のスケールが演出時に 1 であることを確認（`:1717` の `.revealed` → `:1002` の発火条件）

**リスクと対策:**
- 最大のリスクは Task 2 Step 2 の**括弧の対応ミス**（Phase 4 が1段深くなる）。JS が丸ごと死ぬと画面が真っ黒のままになるため、Step 4 でコンソールエラーの確認を必須にした。
- `carouselOffsetY()` が 0 を返す縮退時は従来と同じ挙動（箱の中央に着地）になるだけで、壊れない設計にした。

**対象外:**
- 着地点そのものを変える案（選択肢A）は不採用。
- `.flip-hint` は CSS（`:242`）と JS（`:1355`）に参照があるが DOM に要素が存在しない。無害なので本計画では触らない。

**Placeholder scan:** 各ステップに実コード・実コマンド・具体的な期待値を記載。プレースホルダー無し。

**Type consistency:** 追加する識別子は `carouselOffsetY()` / `SETTLE_HOLD_MS` / `SETTLE_MOVE_MS` / `SETTLE_BEAT_MS` の4つのみ。既存の `fall` / `overlay` / `startY` は `triggerReveal()` スコープ内の既存変数をそのまま使う。
