# 中央カードだけ高画質 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** カルーセルで「今見ている中央のカード1枚だけ」を高画質(800px)で表示し、それ以外は従来どおり軽量版(480px)のまま。粗い版は即表示されているので、止まった一瞬あとに中央だけスッとくっきりになる。

**Architecture:** 単一HTMLファイル（バニラJS＋Three.js）。表画像は全カードを480pxで常駐デコード（`loadAllFronts`）・描画は中央±2のみ（`applyCardVisibility`）という既存構成は維持。そこに「**高画質で描くのは常に中央1枚だけ**」を追加する。`applyCenterHiRes()` が、停止時(=非モーション時)に中央の表imgだけ `src` を高画質版へ差し替え、中央から外れたカードは480pxへ戻す。これにより高画質テクスチャはGPU上に常に1枚だけ＝メモリ/GPUは安全。

**Tech Stack:** HTML / バニラJS / CSS / Pillow（画像生成, 既存 `_optimize_front.py`）

## Global Constraints

- 対象ファイル: `sky_collection_card.html`、`_optimize_front.py`。
- 元画像は `images/card_front/raw/`（gitignore済み・ローカル）。表示用480pxは `images/card_front/`（コミット済み）。高画質版は新規 `images/card_front_hi/`。
- **raw は gitignore のため、生成物（card_front_hi）はコミットして配布する**（クローン先で再生成できないため）。
- 高画質の読み込みは**停止時(`motionActive===false`)のみ**。スクラブ/フリック中は絶対に高画質を読み込まない（重い画像のデコード殺到＝クラッシュ再発を防ぐ）。
- 高画質で同時に持つのは**常に中央1枚だけ**。中央を外れたカードは480pxへ戻す。
- 行番号は編集でずれるため、位置は「アンカー（特定の文字列）」で示す。各編集前に検索して現在地を確認すること。
- 既存の挙動（即表示・無クラッシュ・リビール・フリップ・3D）を壊さない。
- 検証は `serve` スキルでのブラウザ手動確認（自動テスト基盤は無い）。

---

## Phase 1 — 高画質アセットの生成

### Task 1: `images/card_front_hi/` に 800px 版を生成

**Files:**
- Modify: `_optimize_front.py`
- Modify: `.gitignore`（card_front_hi はコミットするので追記不要だが、raw 除外は維持の確認のみ）
- Produce: `images/card_front_hi/*.jpg`（31枚, 横800px）

**Interfaces:**
- Consumes: `images/card_front/raw/`（元画像 1226×1750）
- Produces: 中央表示用の高画質JPEG群。ファイル名は raw と同一（NFD形のまま）。

- [ ] **Step 1: `_optimize_front.py` に高画質出力を追加**

アンカー `TARGET_W = 480` の付近（定数定義部）に高画質サイズと出力先を追加し、生成ループで raw から **480px(表示用) と 800px(高画質) の両方**を書き出すようにする。raw を正として再生成するため冪等。

定数追加（イメージ）:
```python
HI_W = 800
HI_DIR = "images/card_front_hi"
```
生成ループ内（480px を保存している箇所のアンカー `im.save(out_path, "JPEG"` の直後）に、同じ raw 画像から 800px 版も保存する処理を追加する:
```python
import os
os.makedirs(HI_DIR, exist_ok=True)
# raw からもう一度開いて 800px 版を生成（480版を再縮小しないこと）
hi = Image.open(raw_path).convert("RGB")
if hi.size[0] > HI_W:
    hi = hi.resize((HI_W, round(hi.size[1] * HI_W / hi.size[0])), Image.LANCZOS)
hi.save(os.path.join(HI_DIR, name), "JPEG", quality=QUALITY, optimize=True, progressive=True)
```

> 注意: 800px版は必ず **raw から** 作る（480px版を拡大/再縮小しない）。劣化の累積を防ぐ。

- [ ] **Step 2: スクリプトを実行して生成**

```bash
python _optimize_front.py
```
確認: `images/card_front_hi/` に31枚生成され、合計が数MB程度（800px なので1枚200〜400KB目安）であること。

- [ ] **Step 3: 配信確認（NFD/特殊カード）**

`serve` で配信し、NFDパス・特殊カード(`%26`)の高画質が 200 で返るか curl で確認:
```bash
# 例: 01_モブ表.jpg (NFD) と 00_&you表.jpg
curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:8000/images/card_front_hi/01_%E3%83%A2%E3%83%95%E3%82%99%E8%A1%A8.jpg"
curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:8000/images/card_front_hi/00_%26you%E8%A1%A8.jpg"
```

---

## Phase 2 — 中央カードの高画質差し替え

### Task 2: `applyCenterHiRes()` を実装し停止時に中央だけ高画質化

**Files:**
- Modify: `sky_collection_card.html`

**Interfaces:**
- Consumes: `carousel`, `current`, `motionActive`, 各カードの表img（`.card-face` 内の `img[data-src]`）, `players[].frontImg`(NFD済), `render()`, `endScrub()`。
- Produces: 中央1枚だけ高画質、それ以外は480pxという表示。高画質読み込みは停止時のみ。

- [ ] **Step 1: 表imgに高画質パス `data-hi-src` を付与（通常カード）**

アンカー `<img data-src="${p.frontImg}" class="card-front-img"`（buildCard 内）の img に `data-hi-src` を追加する。高画質パスは表示用パスのフォルダ名を差し替えて導出（NFDはfrontImgが正規化済みなので継承）。

変更後:
```html
<img data-src="${p.frontImg}" data-hi-src="${p.frontImg.replace('card_front/','card_front_hi/')}" class="card-front-img" alt="${p.name}" draggable="false" decoding="async">
```

- [ ] **Step 2: 表imgに `data-hi-src` を付与（特殊カード=ゴースト）**

アンカー `<img data-src="images/card_front/00_%26you表.jpg"` の img にも同様に追加する。

変更後:
```html
<img data-src="images/card_front/00_%26you表.jpg" data-hi-src="images/card_front_hi/00_%26you表.jpg" class="card-front-img" alt="&You" draggable="false" decoding="async">
```

- [ ] **Step 3: `applyCenterHiRes()` を追加**

アンカー `function applyCardVisibility() {` のブロックの直後に以下を追加する。各スロットの**表img**（`img[data-src]`＝裏は `data-back-src` なので対象外）について、中央なら高画質、それ以外は480pxへ戻す。**モーション中は何もしない**。

```js
// 高画質で描くのは常に中央1枚だけ。停止時のみ中央を高画質へ、他は480pxへ戻す。
// （スクラブ/フリック中は重い高画質を読み込まない＝クラッシュ防止）
function applyCenterHiRes() {
  if (motionActive) return;
  const slots = carousel.children;
  for (let i = 0; i < slots.length; i++) {
    const img = slots[i].querySelector('img[data-src]'); // 表imgのみ
    if (!img) continue;
    if (i === current && img.dataset.hiSrc) {
      if (img.getAttribute('src') !== img.dataset.hiSrc) img.src = img.dataset.hiSrc;
    } else {
      if (img.getAttribute('src') !== img.dataset.src) img.src = img.dataset.src;
    }
  }
}
```

- [ ] **Step 4: `render()` から呼ぶ**

アンカー `applyCardVisibility();`（render 内）の直後に `applyCenterHiRes();` を追加する。render はタップ移動・慣性停止時に呼ばれ、その時 `motionActive===false` なので中央が高画質化される（スクラブ中の render は `motionActive===true` で早期 return）。

```js
  applyCardVisibility();
  applyCenterHiRes();
```

- [ ] **Step 5: スクラブ終了時にも呼ぶ**

アンカー `motionActive = false;             // 停止：ウィンドウ内の画像をまとめて読み込む`（endScrub 内）に続く `loadNearImages();` の直後に `applyCenterHiRes();` を追加する。スクラブ終了は最終 navigateTo→render が motionActive=true のまま走るため、停止確定後に明示的に呼ぶ。

```js
  loadNearImages();
  applyCenterHiRes();
```

- [ ] **Step 6: ブラウザで手動検証（PC）**

`serve` で配信し PC で開く。確認:
- 止まると中央カードが一瞬おいてくっきり（高画質）になる
- 左右に1枚移動すると、新しい中央が高画質・前の中央は粗い版に戻る
- **同時に高画質なのは常に1枚だけ**（DevTools の Network/Memory で確認できればなお良い）
- コンソールエラーなし

- [ ] **Step 7: ブラウザで手動検証（スマホ実機・最重要）**

`serve` で Tailscale 配信し iPhone で開く。確認:
- **目次の高速スクラブでクラッシュしない**（高画質はスクラブ中に読み込まれないこと）
- 止めると中央だけシャープになる
- フリップ（裏面）・3D・リビールが従来通り

- [ ] **Step 8: ユーザー確認を待つ**

問題なければ次へ。

- [ ] **Step 9: コミット**

```bash
git add -A
git commit -m "feat: 中央カードだけ高画質(800px)で表示

- 停止時に中央の表画像だけ高画質へ差し替え、外れたら480pxへ戻す
- 高画質はモーション中は読み込まない（クラッシュ防止）/ 常に1枚だけ
- card_front_hi/ を _optimize_front.py で raw から生成

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Phase 3 —（任意）先読みで即シャープ化

### Task 3: 中央付近の高画質を idle 中に先読み

> Phase 2 だけでも機能する。「止めてからくっきりになるまでの一瞬の間」を消したい場合のみ実施。

**Files:**
- Modify: `sky_collection_card.html`

- [ ] **Step 1: 停止時に中央±1の高画質を低優先で先読み**

`applyCenterHiRes()` の後、`fetch(hiUrl, { cache:'force-cache', priority:'low' })` で中央±1の高画質**ファイルだけダウンロード**（デコードしない＝メモリ増やさない）。次に隣へ動いた時の高画質化が即時になる。

- [ ] **Step 2: 検証・コミット**

スマホで「移動→ほぼ即くっきり」を確認。クラッシュしないこと（fetch はデコードしないので安全）を確認してコミット。

---

## Self-Review（計画作成者による確認）

**Spec coverage:**
- 高画質アセット生成（raw→800px, card_front_hi）→ Task 1 ✓
- 中央だけ高画質・他は480px・停止時のみ・常に1枚 → Task 2 ✓
- 即シャープ化（任意の先読み）→ Task 3 ✓

**安全性の要点:**
- 高画質読み込みは `motionActive` ガードで停止時のみ → スクラブ中のデコード殺到なし ✓
- 高画質は中央1枚だけ（他は480pxへ戻す）→ GPU/メモリは+1枚分のみ ✓
- raw は gitignore のため生成物 card_front_hi はコミットして配布 ✓

**Placeholder scan:** 各ステップに実コード/実コマンドを記載。`data-hi-src` 導出はフォルダ名差し替えで一貫。

**Type consistency:** `applyCenterHiRes()` / `data-hi-src`(=dataset.hiSrc) / `motionActive` / 表imgセレクタ `img[data-src]` の扱いは全タスクで一貫。
