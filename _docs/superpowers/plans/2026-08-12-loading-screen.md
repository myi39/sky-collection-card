# ローディング画面（心音） Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 全カードの表・裏画像を先に取得しきってから本編を見せる。その待ち時間を、心音のロゴ明滅動画によるローディング演出で埋める。

**Architecture:** 全画面オーバーレイに `mix-blend-mode: screen` で動画を合成し、裏で表画像の常駐デコード（既存 `loadAllFronts()`）と裏画像のHTTPキャッシュ充填（新規 `prefetchBacks()`）を並行させる。両方の完了と最低表示時間を満たした後、心音の拍の頂点に合わせて自動遷移する。入場のタップは無く、タップは左下の既存ボタンによる音のON/OFFのみ。

**Tech Stack:** 素のHTML/CSS/JS（フレームワークなし、ビルドなし）。動画生成に ffmpeg。

設計書: `docs/superpowers/specs/2026-08-12-loading-screen-design.md`

## Global Constraints

- 対象ファイルは `sky_collection_card.html` の1枚のみ。ビルド工程もパッケージマネージャも無い
- **このリポジトリに自動テスト基盤は無い**（`package.json` なし、`3d_test.html` は手動確認用ページ）。各タスクの検証はブラウザのDevToolsコンソールと目視で行う。検証手順は「実行するコマンド／操作」と「期待される出力」を必ず具体値で書くこと
- **`display: none` を本編の隠蔽に使わないこと。** `adjustTranslate()` が `carousel.parentElement.offsetWidth` を参照しており、非表示だと 0 になりカルーセルの中央位置が壊れる（`d0e8934` で修正した中央ズレの再発になる）。隠蔽は `opacity: 0` で行う
- **`.site-frame` に `transform` / `filter` を付けないこと。** 内側の `#modal-3d` が `position: fixed` であり、`transform` が付くと位置基準が `.site-frame` に変わって3Dモーダルが壊れる。スケールのアニメーションは `.carousel-wrap` に掛ける
- **z-index の既存割り当て:** `.bgm-btn` = 200、`#modal-3d` = 300。ローディングオーバーレイは **500**、ローディング中の `.bgm-btn` は **600** を使う。`.bgm-btn` の平常時 200 は変更しない（3Dモーダルの背後に隠れる既存挙動を保つため）
- 画像パスは `players[]` から導出する。`players[]` は読み込み時に `normalize('NFD')` 済みのため、正規化を自動的に引き継げる
- 実参照のカードは **37枚**（`players` 36件 + 特殊カード `00_&You1`）。各ディレクトリには39ファイルあるが `00_&I表` と `00_&You2` は未参照の残存アセットであり、先読み対象に含めない
- 既存の `updateCenterBack()` の裏画像メモリ管理と `applyCardVisibility()` の可視性制御は変更しない
- **各タスクは意図的に未完成な中間状態を残す。** Task 2 でオーバーレイを出した後、Task 6 の遷移が入るまでローディングから先へ進めないのは計画通りの正しい状態であり、欠陥ではない。各タスクはそのタスクのブリーフが定義する範囲に対してのみ評価する
- コミットメッセージは日本語。末尾に以下2行を付ける:
  ```
  Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
  Claude-Session: https://claude.ai/code/session_01FXbvaRJkBbQ3AutrSRLMst
  ```

---

## File Structure

| ファイル | 役割 | 変更 |
|---|---|---|
| `movies/heartbeat_loop.mp4` | ローディング用のループ動画（生成物） | 新規 |
| `movies/心音.mp4` | 原本。参照されなくなるが保持する | 変更なし |
| `sky_collection_card.html` | 全実装。CSS・HTML・JSすべて同ファイル内 | 変更 |

`sky_collection_card.html` 内の変更箇所:

| 箇所 | 内容 | タスク |
|---|---|---|
| `<style>` 末尾（447行 `</style>` の直前） | オーバーレイと遷移のCSS | 2 |
| `.site-frame` の閉じタグ直後（501行と503行の間） | オーバーレイのHTML | 2 |
| `<audio id="bgm">`（503行） | `preload="auto"` → `"none"` | 5 |
| `loadAllFronts()`（800〜815行） | 完了コールバック引数の追加 | 3 |
| `loadAllFronts()` の直後 | 裏画像の先読み関数 | 4 |
| BGM制御ブロック（1235〜1271行） | 音コントローラへ全面置き換え | 5 |
| `init(); loadAllFronts();`（1232〜1233行） | `init();` のみに変更 | 6 |
| 音コントローラの直後 | ローディング制御 | 6 |

**JSの最終的な並び順**（前方参照が起きないようにするため、この順を守ること）:

```
init();
  ↓
音コントローラ（Task 5）        … loadingDone / soundBtn / soundOn / handoffToBgm を定義
  ↓
ローディング制御（Task 6）      … 上を参照し、revealSite() で loadingDone を true にする
```

---

## Task 1: ループ動画の生成

**Files:**
- Create: `movies/heartbeat_loop.mp4`

**Interfaces:**
- Consumes: `movies/心音.mp4`（32.2秒 / 1200×674 / h264+AAC / 3.76MB）
- Produces: `movies/heartbeat_loop.mp4` — 17.5秒 / 800×450 / 約268KB。先頭と末尾の輝度が一致しシームレスにループする。拍のピークは先頭から `1.5 + 3.5k` 秒

- [ ] **Step 1: 元動画の存在と諸元を確認する**

```powershell
ffprobe -v error -show_entries format=duration,size -show_entries stream=codec_name,width,height -of default=noprint_wrappers=1 "movies/心音.mp4"
```

期待される出力（この値でなければ以降の切り出し秒数が合わないので中止して報告すること）:
```
codec_name=aac
codec_name=h264
width=1200
height=674
duration=32.200000
size=3946480
```

- [ ] **Step 2: ループ区間を切り出す**

10.5秒から17.5秒間＝心音ちょうど5拍分。この区間は輝度・音声とも完全に周期的であることを計測済み。

```powershell
ffmpeg -ss 10.5 -t 17.5 -i "movies/心音.mp4" -vf scale=800:-2 -c:v libx264 -crf 30 -preset slow -profile:v main -pix_fmt yuv420p -movflags +faststart -c:a aac -b:a 96k -ac 1 -y "movies/heartbeat_loop.mp4"
```

- [ ] **Step 3: 生成物の尺とサイズを検証する**

```powershell
ffprobe -v error -show_entries format=duration,size -of default=noprint_wrappers=1 "movies/heartbeat_loop.mp4"
```

期待: `duration` が 17.5 前後、`size` が 250000〜300000（約268KB）の範囲。500KBを超えていたら `-crf` を上げて作り直すこと。

- [ ] **Step 4: ループの継ぎ目を検証する**

先頭と末尾の平均輝度が一致していればシームレスにループする。

```powershell
$log = ffmpeg -v error -i "movies/heartbeat_loop.mp4" -vf "fps=2,signalstats,metadata=print:file=-" -f null NUL; $ys=@(); foreach ($line in ($log -split "`n")) { if ($line -match 'YAVG=([0-9.]+)') { $ys += [math]::Round([double]$matches[1],1) } }; "head: $($ys[0..3] -join ', ')"; "tail: $($ys[-4..-1] -join ', ')"
```

期待: `head: 19.2, 19.2, 21.1, 25.7` / `tail: 25, 22.8, 20.7, 19.4` に近い値。**先頭の1つ目（約19.2）と末尾の最後（約19.4）の差が 1.0 以内**であること。差が大きい場合は切り出し位置がずれているので Step 2 の `-ss` を見直す。

`head` の4つ目が 25.7 付近まで上がることも確認する。これは先頭から1.5秒地点が拍のピークであることを意味し、遷移タイミングの計算（Task 6）の前提になる。

- [ ] **Step 5: コミット**

```bash
git add movies/heartbeat_loop.mp4
git commit -m "feat: ローディング用の心音ループ動画を追加

心音.mp4 の 10.5-28.0 秒（心音5拍分）を切り出し、800px / 音声96k mono へ圧縮。
3.76MB → 268KB。先頭と末尾の輝度が一致するためシームレスにループする。
元の 心音.mp4 は原本として保持。

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01FXbvaRJkBbQ3AutrSRLMst"
```

---

## Task 2: オーバーレイの静止表示

本編を隠し、動画をループ再生するところまで。先読みも遷移もまだ実装しない。**この時点でローディング画面から先へ進めなくなるのは計画通りの正しい状態。**

**Files:**
- Modify: `sky_collection_card.html` — `<style>` 末尾（447行 `</style>` の直前）、`.site-frame` の閉じタグ直後（501行と503行の間）

**Interfaces:**
- Consumes: `movies/heartbeat_loop.mp4`（Task 1）
- Produces: DOM要素 `#loading-overlay` / `#loading-video`、CSSクラス `.bgm-btn.over-loading`（Task 5 が付与）/ `.site-frame.revealed` / `.carousel-wrap.revealed`（Task 6 が付与）

- [ ] **Step 1: CSSを追加する**

`</style>`（447行）の直前に挿入。

```css
/* ─── ローディング画面 ─────────────────────────────────── */
/* z-index: .bgm-btn=200 / #modal-3d=300 なので、オーバーレイは 500、
   ローディング中だけ前面に出すボタンは 600 を使う。 */
#loading-overlay {
  position: fixed;
  inset: 0;
  z-index: 500;
  background: #080810;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 1;
  transition: opacity 0.6s ease;
}
#loading-overlay.done { opacity: 0; pointer-events: none; }

/* 動画は純黒背景にグレーのロゴ。screen 合成で黒が透過するため、
   横長動画を縦画面に置いてもレターボックスが出ない。 */
#loading-video {
  width: 100%;
  max-width: 700px;
  height: auto;
  mix-blend-mode: screen;
  pointer-events: none;
}

/* ローディング中だけ音ボタンをオーバーレイより前面へ（Task 5 で付与）。
   平常時の 200 は変えない（3Dモーダル 300 の背後に隠れる既存挙動を保つため）。 */
.bgm-btn.over-loading { z-index: 600; }

/* 本編の隠蔽は opacity で行う。display:none にすると
   adjustTranslate() が参照する offsetWidth が 0 になり中央位置が壊れる。
   .site-frame に transform を付けないこと（内側の #modal-3d が position:fixed のため）。 */
.site-frame {
  opacity: 0;
  transition: opacity 0.6s ease;
}
.site-frame.revealed { opacity: 1; }

.carousel-wrap {
  transform: scale(1.04);
  transition: transform 0.6s cubic-bezier(0.16, 1, 0.3, 1);
}
.carousel-wrap.revealed { transform: scale(1); }
```

- [ ] **Step 2: HTMLを追加する**

`.site-frame` の閉じ `</div>`（501行）と `<audio id="bgm">`（503行）の間に挿入。

`muted` と `playsinline` は必須。これが無いとモバイルで自動再生されない（`playsinline` が無いとiOSで全画面再生に化ける）。

```html
<div id="loading-overlay">
  <video id="loading-video" src="movies/heartbeat_loop.mp4"
         muted playsinline autoplay loop preload="auto"></video>
</div>
```

- [ ] **Step 3: ブラウザで表示を確認する**

`sky_collection_card.html` をブラウザで開く。

期待:
- 黒背景の中央に「SKY AIRRACE / #skyairraceCC」のロゴが表示され、**約3.5秒周期で明滅を繰り返す**
- ロゴの周囲に動画の矩形の境界（黒い長方形の縁）が**見えない**。見える場合は `mix-blend-mode: screen` が効いていない
- カルーセルは見えない
- ループの折り返しで明滅が飛んだり暗転したりしない

- [ ] **Step 4: コンソールで前提を確認する**

DevToolsのコンソールで実行:

```js
const v = document.getElementById('loading-video');
console.log('paused:', v.paused, 'muted:', v.muted, 'duration:', v.duration.toFixed(2));
console.log('siteFrame opacity:', getComputedStyle(document.querySelector('.site-frame')).opacity);
console.log('carouselWrap offsetWidth:', document.querySelector('.carousel-wrap').offsetWidth);
```

期待:
```
paused: false muted: true duration: 17.50
siteFrame opacity: 0
carouselWrap offsetWidth: <0 より大きい数値>
```

**`offsetWidth` が 0 の場合は隠蔽方法が間違っている。** `display:none` を使っていないか確認すること。

- [ ] **Step 5: コミット**

```bash
git add sky_collection_card.html
git commit -m "feat: ローディングオーバーレイの静止表示を追加

心音ループ動画を全画面オーバーレイに mix-blend-mode:screen で合成。
本編は opacity:0 で隠す（display:none にすると offsetWidth が 0 になり
adjustTranslate() のカルーセル中央位置が壊れるため）。
遷移はまだ未実装のため、この時点では本編へ進めない。

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01FXbvaRJkBbQ3AutrSRLMst"
```

---

## Task 3: 表画像の完了通知

既存の `loadAllFronts()` は `img.src` を割り当てるだけで、実際の読み込み完了を待っていない。ローディングの完了判定に使うため、デコード完了まで待つコールバックを追加する。

**Files:**
- Modify: `sky_collection_card.html:800-815`（`loadAllFronts()`）

**Interfaces:**
- Produces: `loadAllFronts(onComplete)` — `onComplete` は省略可。全表画像のデコードが完了（または失敗）した時点で引数なしで1回だけ呼ばれる

- [ ] **Step 1: `loadAllFronts()` を差し替える**

800〜815行を以下で置き換える。progressive な読み込み方式（1フレーム6msの間引き、480px解像度）は変更しない。

```js
// 表画像は全カードを軽量解像度(480px)で常駐デコードする（仮想化なし）。
// → スクラブ中のデコードが起きず、どこでも即表示になる。
// 裏画像は重い(769px)ため、フリップ時のみ読み込む（doFlip 参照）。
// onComplete: 全枚数のデコードが済んだ時点で1回だけ呼ばれる（ローディングの完了判定用）。
function loadAllFronts(onComplete) {
  const imgs = carousel.querySelectorAll('img[data-src]'); // 表画像のみ
  let i = 0;
  const pending = []; // src 割り当てだけでは読み終わっていないので、完了を待つ Promise を貯める
  function step() {
    const t0 = performance.now();
    while (i < imgs.length && performance.now() - t0 < 6) { // 1フレーム最大6msだけ読む
      const img = imgs[i++];
      if (img.getAttribute('src') !== img.dataset.src) {
        img.src = img.dataset.src;
        if (img.decode) {
          pending.push(img.decode().catch(() => {})); // 失敗も完了扱いにする
        } else {
          pending.push(new Promise(r => { img.onload = img.onerror = r; }));
        }
      }
    }
    if (i < imgs.length) requestAnimationFrame(step);
    else if (onComplete) Promise.all(pending).then(() => onComplete());
  }
  requestAnimationFrame(step);
}
```

- [ ] **Step 2: 既存の呼び出しが壊れていないことを確認する**

1233行の `loadAllFronts();` は引数なしのまま。`onComplete` が `undefined` でも動くこと。

ブラウザで開き、コンソールにエラーが出ていないことを確認する。この時点ではまだローディングから抜けられないので、以下をコンソールで実行して本編を強制表示させ、カード画像が表示されることを見る。

```js
document.getElementById('loading-overlay').style.display = 'none';
document.querySelector('.site-frame').classList.add('revealed');
document.querySelector('.carousel-wrap').classList.add('revealed');
```

期待: カルーセルのカード画像が表示される。コンソールにエラーが無い。

- [ ] **Step 3: コールバックが呼ばれることを確認する**

ページを再読み込みし、コンソールで実行:

```js
const t0 = performance.now();
loadAllFronts(() => console.log('fronts done in', Math.round(performance.now() - t0), 'ms'));
```

期待: 数百ms〜数秒で `fronts done in <数値> ms` が**1回だけ**出力される。出力されない場合は `Promise.all` に到達していない。

- [ ] **Step 4: コミット**

```bash
git add sky_collection_card.html
git commit -m "feat: loadAllFronts に完了コールバックを追加

src 割り当てだけでは読み終わっていないため、img.decode() の Promise を集めて
全枚数のデコード完了を待てるようにした。ローディングの完了判定に使う。
progressive な読み込み方式（1フレーム6ms間引き・480px）は変更なし。

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01FXbvaRJkBbQ3AutrSRLMst"
```

---

## Task 4: 裏画像の先読み

**Files:**
- Modify: `sky_collection_card.html` — `loadAllFronts()` の直後（Task 3 適用後の815行付近）に追加

**Interfaces:**
- Consumes: `players[]`（`backImg` は `normalize('NFD')` 済み）
- Produces:
  - `backImagePaths(): string[]` — 先読み対象の裏画像パス配列。74件を返す
  - `prefetchBacks(): Promise<number>` — 全件の取得が終わるかタイムアウトで解決。解決値は完了した件数
  - 定数 `PREFETCH_CONCURRENCY = 6`、`PREFETCH_TIMEOUT_MS = 60000`

- [ ] **Step 1: 先読み関数を追加する**

`loadAllFronts()` の直後に挿入する。

```js
// ─── 裏画像の先読み（HTTPキャッシュに入れるだけ）───────────────
// img.src には載せない。載せるとデコード済みビットマップが常駐し、
// 裏フル(769px)37枚だけで 769*1077*4*37 ≒ 122MB になってモバイルが落ちる。
// ここで潰すのはネットワーク待ちだけ。デコードは従来どおりフリップ時に行い、
// アニメ(850ms)の間に間に合う。メモリ管理は updateCenterBack() のまま変更しない。
const PREFETCH_CONCURRENCY = 6;     // 一斉に投げるとブラウザの同時接続上限で表画像まで遅延する
const PREFETCH_TIMEOUT_MS  = 60000; // 極端に遅い回線で永久に明けないのを防ぐ

function backImagePaths() {
  const paths = [];
  const add = full => {
    paths.push(full);
    paths.push(full.replace('card_back/', 'card_back_lo/'));
  };
  players.forEach(p => add(p.backImg)); // 読み込み時に NFD 正規化済み
  add('images/card_back/00_%26You1_back.png'.normalize('NFD')); // 特殊カード（players に無い）
  return paths;
}

function prefetchBacks() {
  const queue = backImagePaths();
  const total = queue.length;
  let done = 0;

  return new Promise(resolve => {
    let settled = false;
    const finish = () => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      resolve(done);
    };
    const timer = setTimeout(finish, PREFETCH_TIMEOUT_MS);
    if (total === 0) { finish(); return; }

    function pump() {
      const url = queue.shift();
      if (url === undefined) return;
      fetch(url, { cache: 'force-cache' })
        // 本文を読み切る。読み手がいないとブラウザが転送を打ち切り、
        // キャッシュに入り切らないことがある（＝先読みが無意味になる）。
        // arrayBuffer は圧縮されたままの生バイト(約69KB)で、画像のデコードは起きない。
        .then(r => r.arrayBuffer())
        .catch(() => {}) // 個別の失敗は無視。その1枚だけ従来どおりフリップ時に取得されるだけ
        .then(() => {
          if (++done >= total) finish();
          else pump();
        });
    }
    for (let i = 0; i < PREFETCH_CONCURRENCY; i++) pump();
  });
}
```

- [ ] **Step 2: 対象件数を確認する**

ブラウザで開き、コンソールで実行:

```js
const p = backImagePaths();
console.log('count:', p.length);
console.log('lo included:', p.filter(x => x.includes('card_back_lo/')).length);
console.log('unused excluded:', p.filter(x => x.includes('00_&I') || x.includes('00_&You2')).length);
console.log(p[0], '|', p[1], '|', p[p.length - 1]);
```

期待:
```
count: 74
lo included: 37
unused excluded: 0
images/card_back/01_Mob_back.png | images/card_back_lo/01_Mob_back.png | images/card_back_lo/00_%26You1_back.png
```

`count` が 74 でなければ `players` の件数か特殊カードの追加が間違っている。

- [ ] **Step 3: 実際に取得できることを確認する**

DevToolsのNetworkタブを開いた状態で、コンソールで実行:

```js
const t0 = performance.now();
prefetchBacks().then(n => console.log('prefetched', n, 'of 74 in', Math.round(performance.now() - t0), 'ms'));
```

期待:
- `prefetched 74 of 74 in <数値> ms` が出力される
- Networkタブに `card_back/` と `card_back_lo/` へのリクエストが並ぶ。**ステータスが 404 のものが無いこと**
- Networkタブで同時に飛んでいるリクエストが概ね6本以下に収まっている

- [ ] **Step 4: メモリに載っていないことを確認する**

先読みしただけでは `img.src` に入らないことを確認する。

```js
const backs = document.querySelectorAll('.card-back img[data-back-src]');
const withSrc = [...backs].filter(i => i.hasAttribute('src')).length;
console.log('back imgs total:', backs.length, '/ with src:', withSrc);
```

期待: `with src` が **0 か 1**（中央カードのみ `updateCenterBack()` がフルを保持するため）。2以上なら先読みが `img.src` に載せてしまっている。

- [ ] **Step 5: 失敗が握りつぶされることを確認する**

存在しないパスを混ぜても解決することを確認する。

```js
const orig = backImagePaths;
backImagePaths = () => [...orig().slice(0, 3), 'images/card_back/__missing__.png'];
prefetchBacks().then(n => console.log('resolved with', n, '(expected 4)'));
backImagePaths = orig;
```

期待: 404 がコンソールに出るが、`resolved with 4 (expected 4)` が出力され、Promise が解決する。ハングしないこと。

- [ ] **Step 6: コミット**

```bash
git add sky_collection_card.html
git commit -m "feat: 裏画像の先読み（HTTPキャッシュ充填）を追加

裏画像74件(4.35MB)を fetch でキャッシュに入れ、フリップ時のネットワーク待ちを消す。
img.src には載せない — 載せるとデコード済みビットマップが122MB常駐して
モバイルが落ちるため。メモリ管理は updateCenterBack() のまま変更なし。

並列度6に制限（同時接続上限で表画像の読み込みを遅らせないため）、
個別の失敗は無視して続行、全体60秒でタイムアウト。

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01FXbvaRJkBbQ3AutrSRLMst"
```

---

## Task 5: 音の統合

左下の既存ボタン1個で、ローディング中は心音、入場後はBGMを制御する。状態を引き継ぐのではなく、最初から最後まで同じDOM要素を使う。

遷移（Task 6）はまだ無いため、このタスクの完了時点では `loadingDone` は永久に `false` のまま。**入場後のBGMの動作は Task 6 で検証する。** ここでは心音側と、BGMが勝手に鳴らないことを検証する。

**Files:**
- Modify: `sky_collection_card.html:503`（`<audio id="bgm">` の `preload`）
- Modify: `sky_collection_card.html` — BGM制御ブロック（`// BGM` で始まる IIFE 全体）を音コントローラへ置き換え

**Interfaces:**
- Consumes: `#loading-video`（Task 2）、`.bgm-btn.over-loading`（Task 2）
- Produces:
  - `loadingVideo` — `#loading-video` の参照
  - `soundBtn` — `#bgmBtn` の参照
  - `bgm` — `#bgm` の参照
  - `let soundOn = false` — 音のON/OFF状態
  - `let loadingDone = false` — Task 6 の `revealSite()` が `true` にする
  - `fadeAudio(el, from, to, ms): void`
  - `primeBgm(): void`
  - `handoffToBgm(): void` — Task 6 の `revealSite()` が呼ぶ
  - `setSound(on: boolean): void`
  - 定数 `HEART_VOL = 1.0`、`BGM_VOL = 0.28`

- [ ] **Step 1: `preload` を変更する**

503行を以下に変更する。BGMの3.97MBがページを開いた瞬間から画像の先読みと帯域を奪い合うのを止める。

```html
<audio id="bgm" src="bgm/蒼穹.mp3" loop preload="none"></audio>
```

- [ ] **Step 2: 旧BGMブロックを音コントローラへ置き換える**

`// BGM` で始まる IIFE 全体（`(function() { ... })();`、1235〜1271行付近）を丸ごと削除し、同じ位置に以下を挿入する。削除対象は以下の内容を含むブロック:

```js
// BGM
(function() {
  const bgm = document.getElementById("bgm");
  const btn = document.getElementById("bgmBtn");
  bgm.volume = 0.28;
  ...
  document.addEventListener("touchstart", onFirstInteraction, { passive: true });
  document.addEventListener("mousedown", onFirstInteraction);
  ...
})();
```

挿入する内容:

```js
// ─── 音（ローディング中は心音、入場後は BGM。左下の同じボタンで操作する）───
// 初期は OFF。autoplay 制限により、無音でなければ自動再生できないため。
// 反応するのはこのボタン1箇所だけ。画面のどこを触っても音は鳴らない。
const loadingVideo = document.getElementById('loading-video');
const soundBtn = document.getElementById('bgmBtn');
const bgm = document.getElementById('bgm');
const HEART_VOL = 1.0;
const BGM_VOL   = 0.28;
let soundOn = false;
let bgmPrimed = false;
let loadingDone = false; // Task 6 の revealSite() が true にする

// 同じ要素に対して新しいフェードが始まったら、古いフェードは次のフレームで降りる。
// これが無いと、ボタン連打で複数のループが同時に el.volume を書き合い、
// 音量がばたついたり、OFF にしたのに下がりきらないまま一瞬鳴ったりする。
function fadeAudio(el, from, to, ms) {
  const gen = el._fadeGen = (el._fadeGen || 0) + 1;
  const t0 = performance.now();
  el.volume = from;
  function tick(ts) {
    if (el._fadeGen !== gen) return; // 自分より新しいフェードが始まっている
    const k = Math.min(1, (ts - t0) / ms);
    el.volume = from + (to - from) * k;
    if (k < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

// ユーザー操作の中で一度 play() しておくと autoplay ロックが解ける。
// preload="none" でも play() で読み込みが始まる。
function primeBgm() {
  if (bgmPrimed) return;
  bgmPrimed = true;
  bgm.volume = 0;
  bgm.play().catch(() => { bgmPrimed = false; });
}

// 入場時に心音から BGM へ渡す。Task 6 の revealSite() から呼ばれる。
function handoffToBgm() {
  fadeAudio(loadingVideo, loadingVideo.volume, 0, 600);
  primeBgm();
  fadeAudio(bgm, 0, BGM_VOL, 1200);
}

function setSound(on) {
  soundOn = on;
  soundBtn.textContent = on ? '♪ ON' : '♪ OFF';

  if (on) {
    primeBgm(); // このクリックのうちに解錠しておく
    if (loadingDone) {
      fadeAudio(bgm, bgm.volume, BGM_VOL, 800);
    } else {
      loadingVideo.muted = false;
      fadeAudio(loadingVideo, 0, HEART_VOL, 800); // いきなり最大音量にしない
    }
  } else {
    if (loadingDone) {
      fadeAudio(bgm, bgm.volume, 0, 300);
    } else {
      fadeAudio(loadingVideo, loadingVideo.volume, 0, 300);
      setTimeout(() => { if (!soundOn) loadingVideo.muted = true; }, 320);
    }
  }
}

soundBtn.textContent = '♪ OFF';
soundBtn.classList.add('over-loading'); // ローディング中はオーバーレイより前面
soundBtn.addEventListener('click', e => {
  e.stopPropagation();
  setSound(!soundOn);
});
```

- [ ] **Step 3: 初期状態がOFFで、勝手に鳴らないことを確認する**

ページを再読み込みし、**何も触らずに**待つ。

期待:
- 左下に `♪ OFF` と表示され、オーバーレイの上に見えている（`over-loading` の z-index 600 が効いている）
- 心音の映像は明滅するが**音は鳴らない**
- 画面中央や上下をタップしても音は鳴らない
- DevToolsのNetworkタブに `蒼穹.mp3` のリクエストが**無い**（`preload="none"` が効いている）

- [ ] **Step 4: 誤タップで鳴らないことを確認する**

再読み込みし、コンソールで実行:

```js
document.body.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
document.body.dispatchEvent(new MouseEvent('click', { bubbles: true }));
setTimeout(() => console.log('bgm paused:', bgm.paused, '/ video muted:', loadingVideo.muted), 1500);
```

期待: `bgm paused: true / video muted: true`。旧ロジックが残っていると `bgm paused: false` になる。

- [ ] **Step 5: ボタンで心音が鳴ることを確認する**

再読み込みし、左下の `♪ OFF` をタップする。

期待:
- ラベルが `♪ ON` に変わる
- 心音が**フェードインで**鳴り始める（いきなり最大音量にならない）
- 明滅と鼓動の音が同期している
- Networkタブに `蒼穹.mp3` のリクエストが現れる（`primeBgm()` が解錠している）
- もう一度タップすると心音がフェードアウトし、ラベルが `♪ OFF` に戻る

コンソールで状態を確認:

```js
console.log('soundOn:', soundOn, '/ video muted:', loadingVideo.muted, '/ bgm volume:', bgm.volume);
```

`♪ ON` の状態での期待: `soundOn: true / video muted: false / bgm volume: 0`（BGMは解錠のみで無音待機）

- [ ] **Step 6: コミット**

```bash
git add sky_collection_card.html
git commit -m "feat: 音を左下ボタン1つに統合し、BGMの無条件自動再生を撤去

ローディング中は心音、入場後は BGM を同じボタンで操作する。
状態を引き継ぐのではなく、最初から最後まで同じ DOM 要素を使う。

- 初期は OFF（autoplay 制限により無音でしか自動再生できないため）
- 反応するのはボタン1箇所のみ。画面のどこを触っても鳴らない
- 0.8秒のフェードインで、いきなり最大音量にならないようにした
- 画面のどこを触っても1秒後に鳴る旧ロジックを削除
- preload=auto → none。音を鳴らさない人は 3.97MB を読まずに済み、
  画像の先読みと帯域を奪い合わなくなる

入場後の BGM 動作は遷移の実装後に検証する。

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01FXbvaRJkBbQ3AutrSRLMst"
```

---

## Task 6: 遷移

**Files:**
- Modify: `sky_collection_card.html:1232-1233`（`init(); loadAllFronts();`）
- Modify: `sky_collection_card.html` — 音コントローラ（Task 5）の直後にローディング制御を追加

**Interfaces:**
- Consumes: `loadAllFronts(onComplete)`（Task 3）、`prefetchBacks()`（Task 4）、`loadingVideo` / `soundBtn` / `soundOn` / `loadingDone` / `handoffToBgm()`（Task 5）、`#loading-overlay` / `.site-frame` / `.carousel-wrap`（Task 2）
- Produces:
  - 定数 `LOADING_MIN_MS = 3000`、`LOADING_MAX_MS = 60000`、`BEAT_PERIOD = 3.5`、`BEAT_PEAK_OFFSET = 1.5`
  - `msToNextBeatPeak(): number` — 次の拍のピークまでのミリ秒
  - `revealSite(): void` — オーバーレイを閉じて本編を出す
  - `window.__loadingStartedAt` — 検証用のタイムスタンプ

- [ ] **Step 1: `loadAllFronts()` の即時呼び出しを外す**

1232〜1233行の

```js
init();
loadAllFronts(); // 表画像を全カード分、軽量解像度で常駐読み込み（progressive）
```

を以下に変更する。`loadAllFronts()` はローディング制御の中から呼ぶため、ここでは呼ばない。

```js
init();
```

- [ ] **Step 2: ローディング制御を追加する**

音コントローラ（Task 5）の最後、`soundBtn.addEventListener('click', ...)` の直後に挿入する。**音コントローラより前に置かないこと** — `soundBtn` / `soundOn` / `handoffToBgm` を参照するため。

```js
// ─── ローディング制御 ───────────────────────────────────
// 最低表示時間・表画像のデコード・裏画像の先読み がすべて済んだ後、
// 次に来る心音の拍の頂点で本編へ移る。入場のタップは無い。
const LOADING_MIN_MS   = 3000;  // 最低表示時間（目安。実効の最短は次のピークまで待つため約5.0秒）
const LOADING_MAX_MS   = 60000; // 上限。どれか1つでも固まったら諦めて本編へ進む
const BEAT_PERIOD      = 3.5;   // 心音の周期(秒)
const BEAT_PEAK_OFFSET = 1.5;   // ループ先頭から最初のピークまで(秒)

const loadingOverlay = document.getElementById('loading-overlay');
const siteFrame      = document.querySelector('.site-frame');
const carouselWrap   = document.querySelector('.carousel-wrap');

window.__loadingStartedAt = performance.now(); // 検証用

// 拍のピークは currentTime が 1.5 + 3.5k 秒の地点。次のピークまでの ms を返す。
function msToNextBeatPeak() {
  const t = loadingVideo.currentTime || 0;
  const phase = (((t - BEAT_PEAK_OFFSET) % BEAT_PERIOD) + BEAT_PERIOD) % BEAT_PERIOD;
  return (phase === 0 ? 0 : BEAT_PERIOD - phase) * 1000;
}

function revealSite() {
  if (loadingDone) return;
  loadingDone = true;

  siteFrame.classList.add('revealed');
  carouselWrap.classList.add('revealed');
  loadingOverlay.classList.add('done');
  soundBtn.classList.remove('over-loading');
  if (soundOn) handoffToBgm();

  setTimeout(() => {
    loadingVideo.pause();
    loadingOverlay.remove();
    carouselWrap.style.transform = 'none'; // 以降 getBoundingClientRect に影響させない
    console.log('[loading] revealed at', Math.round(performance.now() - window.__loadingStartedAt), 'ms');
  }, 700); // CSS の 0.6s トランジションより少し長く
}

// ネットワークが停滞して画像リクエストが成功も失敗もしないまま止まると、
// loadAllFronts の完了が永久に来ない。スキップ手段を持たない設計なので、
// 全体に上限を掛けておかないとギャラリーへ到達する手段が完全に失われる。
Promise.race([
  Promise.all([
    new Promise(r => setTimeout(r, LOADING_MIN_MS)),
    new Promise(r => loadAllFronts(r)), // 表画像を全カード分、軽量解像度で常駐読み込み（progressive）
    prefetchBacks(),
  ]),
  new Promise(r => setTimeout(r, LOADING_MAX_MS)),
]).then(() => {
  setTimeout(revealSite, msToNextBeatPeak());
});
```

- [ ] **Step 3: 遷移が起きることを確認する**

ページを再読み込みする。

期待:
- 心音が数拍ぶん明滅した後、**ロゴが消えると同時にカルーセルがわずかに縮みながらフェードイン**する
- コンソールに `[loading] revealed at <数値> ms` が1回だけ出力される
- キャッシュが効いた状態（2回目以降の読み込み）で、その数値が **4500〜5500 の範囲**に入る。これが設計上の最短5.0秒にあたる
- 遷移後、カルーセルを左右にスワイプでき、カードが中央に正しく収まる

- [ ] **Step 4: 拍の頂点で遷移していることを確認する**

遷移の瞬間にロゴが最も明るい状態であることを目視する。判定しづらい場合は、再読み込み直後にコンソールで次を実行し、拍の位相を直接確認する。

```js
const v = document.getElementById('loading-video');
setInterval(() => {
  const phase = (((v.currentTime - 1.5) % 3.5) + 3.5) % 3.5;
  if (phase < 0.1) console.log('peak at currentTime', v.currentTime.toFixed(2));
}, 50);
```

期待: `peak at currentTime 1.5x / 5.0x / 8.5x / 12.0x / 15.5x` のように 3.5秒間隔で出力される。遷移はこのいずれかの直後に起きる。

- [ ] **Step 5: 音の受け渡しを確認する**

再読み込みし、ローディング中に左下ボタンをタップして `♪ ON` にしてから、遷移するまで待つ。

期待:
- 遷移の際、心音がフェードアウトしながら**BGMがフェードインする**
- 遷移後に `♪ ON` をタップすると BGM がフェードアウトし、ラベルが `♪ OFF` になる
- もう一度タップすると BGM が戻る
- 音を OFF のまま遷移した場合、遷移後も無音のままで、カードを触っても鳴らない

- [ ] **Step 6: 3Dモーダルが壊れていないことを確認する**

`.carousel-wrap` の transform が3Dビューに影響していないことを確認する。

遷移後、カードの「3D で見る ›」ボタンを押す。

期待: 3Dモーダルが**画面全体**に開く。`.carousel-wrap` の内側にめり込んだり、位置がずれたりしないこと。閉じた後もカルーセルが正常に動くこと。

- [ ] **Step 7: コミット**

```bash
git add sky_collection_card.html
git commit -m "feat: ローディングから本編への自動遷移を追加

最低表示時間・表画像のデコード・裏画像の先読みが揃った後、
次の心音の拍の頂点で本編へ移る。入場のタップは無し。
実効の最短表示は約5.0秒（3秒経過後、最初に来るピークが5.0秒地点のため）。

遷移後に .carousel-wrap の transform を除去し、
スクラブのドット判定（getBoundingClientRect）に影響させない。
音が ON の場合は心音から BGM へフェードで渡す。

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01FXbvaRJkBbQ3AutrSRLMst"
```

---

## Task 7: 実機確認

PCブラウザだけでは検証できない項目が集中している。過去に29枚のカルーセルでモバイルChromeがクラッシュした経緯があるため、実機確認を必須とする。

**Files:** 変更なし（問題が見つかった場合を除く）

- [ ] **Step 1: ローカルサーバを起動する**

`serve` スキルを使い、Tailscale経由でスマートフォンからアクセスできる状態にする。`file://` では `fetch()` がCORSで失敗するため、必ずHTTPで配信すること。

- [ ] **Step 2: スマートフォンで初回読み込みを確認する**

**キャッシュを消した状態**で `sky_collection_card.html` を開く。

期待:
- ロゴが縦画面の中央に出て、**動画の矩形の縁が見えない**（`mix-blend-mode: screen` が効いている）
- 動画が自動再生される（`muted` + `playsinline` が効いている。全画面再生に化けないこと）
- 明滅が滑らかで、カクつきやループの飛びが無い
- 数秒〜十数秒後に自動で本編へ遷移する

- [ ] **Step 3: メモリとクラッシュを確認する**

遷移後、カルーセルを端から端まで数往復スクラブし、複数のカードをフリップする。

期待:
- ブラウザがクラッシュしない
- カードをめくった瞬間に**裏面が黒いまま止まらない**（先読みが効いていれば即座に絵が出る）
- スクラブが引っかからない

- [ ] **Step 4: 音を確認する**

再読み込みし、ローディング中に左下ボタンをタップする。

期待:
- 心音が鳴る（iOSの場合はサイレントスイッチをOFFにして確認する。ONだと仕様上鳴らない）
- 入場時に心音からBGMへ渡る
- ボタン以外をタップしても音が鳴らない

- [ ] **Step 5: 低速回線を模擬して確認する**

DevToolsのNetworkスロットリングを `Slow 4G` にして再読み込みする（PCブラウザで可）。

期待:
- ローディングが**心音のループを回り続けて待つ**（途中で止まったり暗転したりしない）
- 最終的に遷移する
- 遷移後、どのカードへ移動しても表画像が既に表示されている

- [ ] **Step 6: 音ボタンの視認性を判断する**

設計書の「未確定事項」として残していた項目。実機で見て、ローディング中に左下ボタンが音の切り替え手段として気づける明るさかを判断する。

現状は `color: rgba(255,255,255,0.28)` / `font-size: 10px` とかなり控えめ。気づけないと判断した場合のみ、ローディング中だけ以下を適用する。

```css
.bgm-btn.over-loading { z-index: 600; color: rgba(255,255,255,0.5); }
```

判断結果（変更したか、しなかったか）を報告に含めること。

- [ ] **Step 7: 結果を報告する**

問題が見つかった場合は、修正して該当タスクの検証をやり直す。問題が無ければ変更なしで次へ進む。

---

## 完了後

- `feat/loading-screen` を `main` へマージする
- `main` を `origin` へ push する
