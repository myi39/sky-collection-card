# カードの縦横比固定・表/裏の表示調整 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:**
- 表面：**常に画像全体を表示（フルサイズ・切り取りなし）**。ブラウザ差で見え方が変わらないようにする。
- 裏面：表と**同じ大きさの枠**に、**縦（高さ）を基準に中央揃え**で入れ、**横が若干見切れる**形にする。

**調査結果（実測）:**
- 表画像：全31枚 `1226×1750`（縦/横 = **1.4274**）で統一。
- 裏画像：全31枚 `769×1088`（縦/横 = **1.4148**）で統一。表よりわずかに横広。
- 現状の崩れ原因：`--card-h: min(calc(var(--card-w) * 1.406), 56vh)`。高さを **56vh で頭打ち**にしているため、ビューポート高さ（ブラウザのアドレスバー等で変動）次第でカードの**縦横比が変化**。基準 `1.406` は表・裏どちらの比率とも一致しないため、`object-fit: cover` で常に可変的に切り取られていた。

**方針:**
1. カードの縦横比を**表画像の比率(1.4274)に固定**し、画面が低いときは**幅を高さ予算から縮める**ことで比率を一定に保つ（＝ブラウザ差で見え方が変わらない）。
2. 表は `object-fit: contain`（＝全体表示・フルサイズ）。枠の比率が表と一致するので余白なくぴったり収まる。
3. 裏は `object-fit: cover` ＋ `object-position: center`（＝枠を高さで満たし、横がはみ出して中央で見切れる）。

**Tech Stack:** CSS のみ（`sky_collection_card.html`）。JS変更なし。

## Global Constraints

- 対象ファイル: `sky_collection_card.html`。
- JS・カルーセル挙動・画像生成（`_optimize_front.py`）は変更しない。CSSのみ。
- 行番号は編集でずれるため、位置は「アンカー（特定の文字列）」で示す。各編集前に検索して現在地を確認すること。
- 角丸(11px)と裏画像内の白い四角枠の不一致（角が合わない件）は**本計画の対象外**（別途）。本計画は「比率・全体表示・縦合わせ中央・横見切れ・同サイズ」のみ扱う。
- 検証は `serve` スキルでのブラウザ手動確認（PC＋スマホ実機、複数ブラウザ）。

---

## Phase 1 — カードの縦横比を表画像に固定（ブラウザ差の解消）

### Task 1: `:root` のサイズ計算を「アスペクト固定＋高さ予算で幅制限」に変更

**Files:**
- Modify: `sky_collection_card.html`（`:root` の CSS変数）

**Interfaces:**
- Produces: `--card-w` / `--card-h` が常に比率 1.4274 を保つ。`.card-inner` / 各 `.card-face` / reveal オーバーレイはこの変数を参照しているため自動追従。

- [ ] **Step 1: `:root` のカードサイズ定義を差し替え**

アンカー `--card-w: clamp(240px, 78vw, 340px);` を含む `:root` ブロックを以下に置き換える。高さを直接頭打ちにせず、**幅を「幅基準」と「高さ予算÷比率」の小さい方**にすることで、画面が低くても比率が崩れない。

変更前:
```css
  :root {
    --card-w: clamp(240px, 78vw, 340px);
    --card-h: min(calc(var(--card-w) * 1.406), 56vh);
  }
```
変更後:
```css
  :root {
    /* 表画像の比率に固定（1226:1750 → 縦/横 = 1.4274）。
       高さ予算(56vh)は幅側に変換して効かせ、アスペクトを常に一定に保つ。 */
    --card-ar: 1.4274;
    --card-w: min(clamp(240px, 78vw, 340px), calc(56vh / 1.4274));
    --card-h: calc(var(--card-w) * 1.4274);
  }
```

> 注: `56vh` は従来の高さ予算を踏襲（カード以外のUI領域を確保）。見え方を調整したい場合はこの値で全体サイズを上下できる（比率は不変）。

- [ ] **Step 2: 手動検証（比率がブラウザ差で変わらないこと）**

`serve` で配信。PC（ウィンドウ高さを変えてみる）＋スマホ実機で開く。確認:
- 縦長・横長・短い画面のいずれでも、**カードの縦横比が一定**（表画像が常にぴったり収まる）
- カードが画面からはみ出さない（短い画面では小さくなるが比率は保つ）

---

## Phase 2 — 表は全体表示(contain)、裏は縦合わせ中央・横見切れ(cover)

### Task 2: `object-fit` を表=contain / 裏=cover に分離

**Files:**
- Modify: `sky_collection_card.html`（CSS `.card-front-img` と reveal オーバーレイの inline style）

**Interfaces:**
- Consumes: Task 1 で固定された枠比率（=表画像比率）。
- Produces: 表＝全体表示（フルサイズ）、裏＝高さ合わせ中央・横見切れ。

- [ ] **Step 1: `.card-front-img` を contain にし、裏だけ cover で上書き**

アンカー `.card-front-img {` のルールを以下に置き換える（表をフルサイズ表示に）。続けて裏面用の上書きルールを追加する。

変更前:
```css
  .card-front-img {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
```
変更後:
```css
  .card-front-img {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    object-fit: contain;        /* 表：全体表示（フルサイズ・切り取りなし） */
  }
  /* 裏：高さを基準に満たし、横は中央で見切れる（表と同じ枠サイズ） */
  .card-back .card-front-img {
    object-fit: cover;
    object-position: center;
  }
```

> 補足: 枠比率は表画像と一致させたので、表は contain でも余白なくぴったり収まる（rounding 由来の極小余白対策に contain を採用＝決して切れない）。裏は表より横広なので cover で左右がわずかに見切れる＝ご要望どおり。

- [ ] **Step 2: reveal オーバーレイ（特殊カード落下演出）も同様に**

リビール演出の落下カードはインライン style で `object-fit:cover` を持つ。表/裏で挙動を合わせる。

- 表側（アンカー `<img src="images/card_front/00_%26you表.jpg"` を含む div 内の img）の inline style の `object-fit:cover` を **`object-fit:contain`** に変更。
- 裏側（アンカー `<img src="images/card_back/00_%26You裏.png"`）は `object-fit:cover`（中央）で**変更なし**。

> オーバーレイの枠は `var(--card-w)/var(--card-h)` を使うため、Phase 1 の比率固定が自動的に効く。

- [ ] **Step 3: 手動検証（PC＋スマホ）**

`serve` で配信。確認:
- **表**：全カードで画像全体が見える（上下左右が切れていない＝フルサイズ）
- **裏**：表と同じ枠サイズで、**上下はぴったり・左右がわずかに見切れる**・中央揃え
- スクラブ／フリップ／3D／リビールが従来通り
- 複数ブラウザ（Chrome／Safari 等）で見え方が揃っている

- [ ] **Step 4: ユーザー確認を待つ**

問題なければ次へ。

- [ ] **Step 5: コミット**

```bash
git add -A
git commit -m "fix: カード枠を表画像比率に固定し、表=全体表示/裏=縦合わせ中央に

- :root のサイズ計算を高さ予算→幅制限に変え、縦横比を常に一定化
  （ブラウザ高さ差で比率が変わる問題を解消）
- 表は object-fit:contain で全体表示、裏は cover で横を中央見切れに
- reveal オーバーレイの表も contain に統一

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Self-Review（計画作成者による確認）

**Spec coverage:**
- 表＝常にフルサイズ表示 → Phase 1（比率固定）＋ Phase 2 Step 1（contain）✓
- 裏＝縦基準・中央揃え・横見切れ・同サイズ → Phase 2 Step 1（cover/center, 同一枠）✓
- ブラウザ差の解消 → Phase 1（高さ頭打ちを廃し幅制限へ）✓
- reveal 演出の整合 → Phase 2 Step 2 ✓

**調査の裏付け:** 表 1226×1750(1.4274)／裏 769×1088(1.4148) を実測で確認済み。両セットとも比率が完全統一のため、枠比率を表に固定すれば表は無余白・無切れ、裏は左右見切れのみで成立する。

**対象外の明示:** 角丸 vs 裏画像内の四角枠の不一致は本計画では扱わない（別途）。

**Placeholder scan:** 各ステップに実CSS/実コマンドを記載。プレースホルダー無し。

**Type consistency:** 変更は CSS 変数 `--card-w/--card-h/--card-ar` と `.card-front-img` / `.card-back .card-front-img` セレクタのみ。JS は不変。
