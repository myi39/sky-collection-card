# 音の扉（入口ポップアップ） Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 訪問時に「音が流れます」の扉を1枚置き、そのOKタップを唯一のユーザー操作として音の自動再生ロックを解く。あわせて心音とBGMの受け渡しを作り直す。

**Architecture:** 既存のローディングオーバーレイ（z-index 500）の上に、テキストのみの全画面レイヤ `#sound-gate`（z-index 700）を重ねる。扉の裏では心音動画が従来通り無音・不可視で自動再生され、その滞在時間がバッファリングに充てられる。OKのクリックハンドラの中で同期的に「心音の頭出し＋アンミュート＋play()」と「BGMの解錠（play直後にpause）」を行い、その後ローディングの本処理を開始する。入場時は心音を落としきってから蒼穹を曲の頭から鳴らす。

**Tech Stack:** 素のHTML/CSS/JS（フレームワークなし、ビルドなし）。アイコンは Lucide のSVGをインラインで埋め込む（CDN不使用）。

**Spec:** `docs/superpowers/specs/2026-08-14-sound-gate-design.md`

## Global Constraints

- 対象ファイルは `sky_collection_card.html` の1枚のみ。ビルド工程もパッケージマネージャも無い
- **このリポジトリに自動テスト基盤は無い**（`package.json` なし）。各タスクの検証はブラウザのDevToolsコンソールと目視で行う。検証手順は「実行するコマンド／操作」と「期待される出力」を必ず具体値で書くこと
- **JSの本体は572〜1742行の単一 `<script>` ブロック**（`type="module"` ではない）。関数宣言はブロック全体に巻き上がるため、579行付近で定義した関数を1518行付近から呼べる。`const` / `let` は巻き上がらないので、参照する側は必ず定義より後に置くこと。Task 1 がこの手前に1行だけの `<script>` を1つ増やすが、別ブロックなので本体の巻き上げには影響しない
- **z-index の割り当て:** `.bgm-btn` = 200 / `#modal-3d` = 300 / `#loading-overlay` = 500 / `.bgm-btn.over-loading` = 600 / **`#sound-gate` = 700**。既存の値は変更しない
- **音の解錠に関わる処理は、必ずOKの `click` ハンドラの中で同期的に実行すること。** `await` や `setTimeout` を挟んだ後に `play()` を呼ぶと、iOSでユーザー操作の文脈が切れて解錠に失敗する
- **`HEART_VOL` は 1.0（最大）。心音は必ず 0 から 800ms のフェードで入れること。** いきなり最大音量で鳴らさない
- **Papyrus は日本語グリフを持たない。** 扉のテキストに `font-family: Papyrus` を指定しないこと。システムUIフォントを明示指定する
- **`.bgm-btn` の位置（`bottom: 18px` / `left: 18px`）・色（`rgba(255,255,255,0.28)`、hover `0.55`）・背景・枠線は変更しない。** タップ領域の拡大も今回は行わない（2026-08-14 に見送りを決定）
- 既存の `#loading-still` / `.playing` による静止画フォールバック機構、`loadAllFronts()` / `prefetchBacks()` / `updateCenterBack()` / `applyCardVisibility()`、`LOADING_MIN_MS`（3000）/ `BEAT_PERIOD`（3.5）/ `BEAT_PEAK_OFFSET`（1.5）は変更しない
- **各タスクは意図的に未完成な中間状態を残す。** Task 1 で扉を出した後、Task 2 が入るまでOKを押しても何も起きないのは計画通りの正しい状態。Task 3 の完了時点で入場しても蒼穹が鳴らないのも計画通り（Task 4 で解消する）。各タスクはそのタスクの範囲に対してのみ評価する
- コミットメッセージは日本語。末尾に以下2行を付ける:
  ```
  Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
  Claude-Session: https://claude.ai/code/session_01Rq9Emv9qVLQBG21EoLfEoR
  ```

---

## File Structure

| ファイル | 役割 | 変更 |
|---|---|---|
| `sky_collection_card.html` | 全実装。CSS・HTML・JSすべて同ファイル内 | 変更 |

`sky_collection_card.html` 内の変更箇所（行番号は着手時点のもの。前のタスクの挿入で下にずれる）:

| 箇所 | 内容 | タスク |
|---|---|---|
| `.bgm-btn` のCSS（213〜229行） | テキスト用の指定をアイコン用に差し替え | 5 |
| z-index台帳のコメント（449〜450行） | `#sound-gate = 700` を追記 | 1 |
| `<style>` 末尾（505行 `</style>` の直前） | 扉のCSS | 1 |
| `#loading-overlay` の閉じタグ直後（567行と569行の間） | 扉のHTML＋スクロール抑止 | 1 |
| `<button class="bgm-btn">`（570行） | テキストをインラインSVG 2枚に置き換え | 5 |
| 最終フェイルセーフ（579〜583行） | 関数化し、起動をOK後に移す | 2 |
| 音コントローラ（1376〜1447行） | `primeBgm` / `handoffToBgm` / `setSound` の作り替え | 3, 4 |
| ローディング制御（1449〜1531行） | 扉のコントローラを追加し、本処理をOK後に移す | 2, 3 |

**JSの最終的な並び順**（前方参照が起きないようにするため、この順を守ること）:

```
armLoadingFailsafe() の定義（579行付近・function 宣言なので位置は自由）
  ↓
音コントローラ … loadingVideo / soundOn / primeBgm / startBgm /
                 handoffToBgm / setSound / updateSoundBtn / enterFromGate を定義
  ↓
ローディング制御 … 上を参照する。扉のコントローラもここに置く
```

---

## Task 1: 扉の静止表示

扉を出すところまで。**OKを押しても何も起きず、ローディングへ進めなくなるのは計画通りの正しい状態。**

**Files:**
- Modify: `sky_collection_card.html:449-450`（z-index台帳のコメント）
- Modify: `sky_collection_card.html` — `</style>`（505行）の直前
- Modify: `sky_collection_card.html` — `#loading-overlay` の閉じ `</div>`（567行）と `<audio id="bgm">`（569行）の間

**Interfaces:**
- Produces: DOM要素 `#sound-gate` / `#sound-gate-ok`、CSSクラス `#sound-gate.done`（Task 2 が付与）、`html.gate-open`（Task 2 が除去）

- [ ] **Step 1: z-index台帳のコメントを更新する**

449〜450行の

```css
/* z-index: .bgm-btn=200 / #modal-3d=300 なので、オーバーレイは 500、
   ローディング中だけ前面に出すボタンは 600 を使う。 */
```

を以下に置き換える。

```css
/* z-index: .bgm-btn=200 / #modal-3d=300 なので、オーバーレイは 500、
   ローディング中だけ前面に出すボタンは 600 を使う。
   入口の扉 #sound-gate は、そのすべての上に出すため 700。 */
```

- [ ] **Step 2: 扉のCSSを追加する**

`</style>`（505行）の直前に挿入する。

```css
/* ─── 音の扉（入口）───────────────────────────────────── */
/* ローディング(500)・ローディング中のボタン(600)より上の 700。
   背景色は #loading-overlay と同一にして、OK後の暗転に継ぎ目を作らない。 */
#sound-gate {
  position: fixed;
  inset: 0;
  z-index: 700;
  background: #080810;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 0 24px;
  text-align: center;
  opacity: 1;
  transition: opacity 0.4s ease;
  /* Papyrus は日本語グリフを持たないため扉には使えない。
     指定しないとフォールバック任せになるので、システムUIを明示する。 */
  font-family: -apple-system, BlinkMacSystemFont, "Hiragino Sans",
               "Noto Sans JP", "Yu Gothic", sans-serif;
}
#sound-gate.done { opacity: 0; pointer-events: none; }

/* 主文で事実を伝え、操作の説明は一回り小さく淡く下に置く。 */
#sound-gate-title {
  font-size: 15px;
  color: rgba(255,255,255,0.75);
  letter-spacing: 0.08em;
  line-height: 1.8;
}
#sound-gate-note {
  margin-top: 14px;
  font-size: 11px;
  color: rgba(255,255,255,0.32);
  letter-spacing: 0.08em;
  line-height: 1.8;
}

/* .bgm-btn と同じ質感を一回り大きくしたもの。 */
#sound-gate-ok {
  margin-top: 32px;
  background: rgba(255,255,255,0.05);
  border: 0.5px solid rgba(255,255,255,0.12);
  border-radius: 20px;
  padding: 10px 40px;
  color: rgba(255,255,255,0.6);
  font-family: inherit;
  font-size: 13px;
  letter-spacing: 0.16em;
  cursor: pointer;
  transition: background 0.3s, color 0.3s;
}
#sound-gate-ok:hover { background: rgba(255,255,255,0.1); color: rgba(255,255,255,0.85); }
#sound-gate-ok:focus-visible { outline: 1px solid rgba(255,255,255,0.5); outline-offset: 3px; }

/* 扉の表示中は背後をスクロールさせない（Task 2 の OK で除去する）。 */
html.gate-open, html.gate-open body { overflow: hidden; }
```

- [ ] **Step 3: 扉のHTMLを追加する**

`#loading-overlay` の閉じ `</div>`（567行）と `<audio id="bgm">`（569行）の間に挿入する。

`type="button"` は必須（`<form>` の外なので実害は無いが、既定の submit 挙動に依存しないことを明示する）。

```html
<div id="sound-gate">
  <p id="sound-gate-title">このサイトでは音が流れます</p>
  <p id="sound-gate-note">音のオン／オフは左下でいつでも</p>
  <button id="sound-gate-ok" type="button">OK</button>
</div>
<script>document.documentElement.classList.add('gate-open');</script>
```

- [ ] **Step 4: 表示を確認する**

`sky_collection_card.html` をブラウザで開く。

期待:
- **ページを開いた瞬間に**、黒背景の中央に「このサイトでは音が流れます」が表示される（心音の映像は見えない）
- その下に一回り小さく淡い「音のオン／オフは左下でいつでも」がある
- さらに下に「OK」ボタンがある
- 左下の `♪ OFF` ボタンは**見えない**（扉の下に隠れている）
- ページがスクロールしない
- OKを押しても何も起きない（Task 2 で実装するため。これで正しい）

- [ ] **Step 5: コンソールで前提を確認する**

DevToolsのコンソールで実行:

```js
const g = document.getElementById('sound-gate');
console.log('gate z-index:', getComputedStyle(g).zIndex);
console.log('gate bg:', getComputedStyle(g).backgroundColor);
console.log('font-family:', getComputedStyle(g).fontFamily.slice(0, 20));
console.log('html overflow:', getComputedStyle(document.documentElement).overflow);
console.log('video paused:', document.getElementById('loading-video').paused);
```

期待:
```
gate z-index: 700
gate bg: rgb(8, 8, 16)
font-family: -apple-system, Blink   ← Papyrus が含まれていないこと
html overflow: hidden
video paused: false                 ← 扉の裏で心音動画が回り、先読みが進んでいる
```

**`video paused: true` の場合は自動再生が止まっている。** 低電力モードやブラウザ設定を確認すること（扉の裏の先読みが効かなくなるだけで、Task 3 の実装後は正常に動く）。

- [ ] **Step 6: コミット**

```bash
git add sky_collection_card.html
git commit -m "feat: 入口の扉（音のお知らせ）を静止表示で追加

ローディングの上に z-index 700 の全画面レイヤを重ねる。
背景色は #loading-overlay と同一にして OK 後の暗転に継ぎ目を作らない。
Papyrus は日本語グリフを持たないため、扉にはシステムUIフォントを明示指定。

OK の処理はまだ未実装のため、この時点では先へ進めない。

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01Rq9Emv9qVLQBG21EoLfEoR"
```

---

## Task 2: OKでローディングを開始する

扉を閉じ、ローディングの本処理をOK後に移す。タイムアウトの起点も移す。**音の処理はまだ入れない**（Task 3）。この時点では従来通り初期OFFで、心音は無音のまま流れる。

**Files:**
- Modify: `sky_collection_card.html:579-583`（最終フェイルセーフ）
- Modify: `sky_collection_card.html` — ローディング制御の末尾（`loadingScreenReady().then(...)` のブロック）

**Interfaces:**
- Consumes: `#sound-gate` / `#sound-gate-ok` / `html.gate-open`（Task 1）、`loadingScreenReady()` / `revealSite()` / `msToNextBeatPeak()` / `LOADING_MIN_MS` / `LOADING_MAX_MS`（既存）
- Produces:
  - `armLoadingFailsafe(): void` — 呼ぶと `LOADING_FAILSAFE_MS` 後に本編を強制表示するタイマーを起動する
  - 定数 `LOADING_FAILSAFE_MS = 70000`
  - `soundGate` / `soundGateOk` — DOM参照
  - `gateOpened: Promise<void>` — OKがクリックされたら解決する
  - `window.__gateOpenedAt` — 検証用のタイムスタンプ

- [ ] **Step 1: 最終フェイルセーフを関数化する**

579〜583行の

```js
setTimeout(() => {
  document.querySelector('.site-frame')?.classList.add('revealed');
  document.querySelector('.carousel-wrap')?.classList.add('revealed');
  document.getElementById('loading-overlay')?.remove();
}, 70000);
```

を以下に置き換える。ページ読込の時点では起動せず、扉のOK後に呼ばれるのを待つ。

```js
// 通常経路の最悪ケース = LOADING_ASSET_WAIT_MS(2000) + LOADING_MAX_MS(60000)
// + 拍のピーク待ち(最大 BEAT_PERIOD=3500) = 65500ms。
// これより後に発火しないとフェイルセーフが正常経路を追い越してしまうため 70000。
//
// 起動は扉の OK 後（armLoadingFailsafe の呼び出し）。ページ読込から数えると、
// 扉を開いたまま放置した人の裏で本編が現れ、扉を閉じたら既に一覧、という壊れ方をする。
const LOADING_FAILSAFE_MS = 70000;
function armLoadingFailsafe() {
  setTimeout(() => {
    document.querySelector('.site-frame')?.classList.add('revealed');
    document.querySelector('.carousel-wrap')?.classList.add('revealed');
    document.getElementById('loading-overlay')?.remove();
  }, LOADING_FAILSAFE_MS);
}
```

- [ ] **Step 2: 扉のコントローラを追加し、本処理をOK後に移す**

ローディング制御の末尾にある以下のブロック（`loadingScreenReady()` 関数の定義の直後、1515〜1531行付近）

```js
// ネットワークが停滞して画像リクエストが成功も失敗もしないまま止まると、
// loadAllFronts の完了が永久に来ない。スキップ手段を持たない設計なので、
// 全体に上限を掛けておかないとギャラリーへ到達する手段が完全に失われる。
loadingScreenReady().then(() => {
  init();
  showCardButtons(); // カード生成後でないと .btn-3d が存在しない（元は末尾で呼ばれていた）
  Promise.race([
    Promise.all([
      new Promise(r => setTimeout(r, LOADING_MIN_MS)),
      new Promise(r => loadAllFronts(r)), // 表画像を全カード分、軽量解像度で読み込む（完了まで待つ）
      prefetchBacks(),
    ]),
    new Promise(r => setTimeout(r, LOADING_MAX_MS)),
  ]).catch(() => {}).then(() => {
    setTimeout(revealSite, msToNextBeatPeak());
  });
});
```

を、以下で丸ごと置き換える。

```js
// ─── 扉（入口）─────────────────────────────────────────
// OK のタップが、このサイトで唯一の「音の解錠」ジェスチャーになる。
// 扉を出している間も心音動画の先読み（loadingScreenReady）は走らせておく。
// 滞在時間がそのままバッファリングに使われ、OK 後の待ちが短くなる。
const soundGate   = document.getElementById('sound-gate');
const soundGateOk = document.getElementById('sound-gate-ok');

const gateOpened = new Promise(resolve => {
  soundGateOk.addEventListener('click', () => {
    // 【重要】音の解錠処理は Task 3 でこの位置に入る。
    // await や setTimeout を挟んだ後に play() を呼ぶと、iOS でユーザー操作の
    // 文脈が切れて解錠に失敗する。必ずこのハンドラ内で同期的に実行すること。

    window.__gateOpenedAt = performance.now(); // 検証用
    document.documentElement.classList.remove('gate-open');
    soundGate.classList.add('done');
    setTimeout(() => soundGate.remove(), 450); // CSS の 0.4s より少し長く
    armLoadingFailsafe();
    resolve();
  }, { once: true });
});
soundGateOk.focus();

// 心音動画の先読みはページ読込時から走らせる。扉の滞在で先に終わっていれば、
// OK 直後にローディングの本処理へ入れる。
const loadingAssetsReady = loadingScreenReady();

// ネットワークが停滞して画像リクエストが成功も失敗もしないまま止まると、
// loadAllFronts の完了が永久に来ない。スキップ手段を持たない設計なので、
// 全体に上限を掛けておかないとギャラリーへ到達する手段が完全に失われる。
// LOADING_MAX_MS の計測も、この Promise.all が解けた後＝OK 以降に始まる。
Promise.all([gateOpened, loadingAssetsReady]).then(() => {
  window.__loadingStartedAt = performance.now();
  init();
  showCardButtons(); // カード生成後でないと .btn-3d が存在しない（元は末尾で呼ばれていた）
  Promise.race([
    Promise.all([
      new Promise(r => setTimeout(r, LOADING_MIN_MS)),
      new Promise(r => loadAllFronts(r)), // 表画像を全カード分、軽量解像度で読み込む（完了まで待つ）
      prefetchBacks(),
    ]),
    new Promise(r => setTimeout(r, LOADING_MAX_MS)),
  ]).catch(() => {}).then(() => {
    setTimeout(revealSite, msToNextBeatPeak());
  });
});
```

- [ ] **Step 3: 既存の `__loadingStartedAt` の代入を削除する**

1474行付近にある以下の行を**削除する**。Step 2 で `Promise.all` の中に移したため、二重に代入すると `revealSite()` のログが「扉に滞在した時間」を含んでしまい、実効の待ち時間が読めなくなる。

```js
window.__loadingStartedAt = performance.now(); // 検証用
```

削除後、`window.__loadingStartedAt` への代入がファイル内で**1箇所だけ**であることを確認する。

```bash
grep -n "__loadingStartedAt" sky_collection_card.html
```

期待: 代入1件（`Promise.all` の中）と参照1件（`revealSite()` 内の `console.log`）の**計2件のみ**。

- [ ] **Step 4: OKで扉を抜けられることを確認する**

ページを再読み込みし、OKを押す。

期待:
- 扉が 0.4秒でフェードアウトし、心音のロゴが現れる
- 心音の映像が明滅する（音は鳴らない。Task 3 で実装するため、これで正しい）
- 左下に `♪ OFF` ボタンが現れる
- ページのスクロールが復活する
- 数秒後に自動で本編（カルーセル）へ遷移する
- コンソールに `[loading] revealed at <数値> ms` が1回だけ出力される

- [ ] **Step 5: ローディングの計測がOK起点になっていることを確認する**

再読み込みし、**OKを押さずに10秒待ってから**OKを押す。

期待:
- `[loading] revealed at <数値> ms` の数値が **10000 を大きく下回る**（キャッシュが効いていれば 4500〜5500 程度）。10000を超えていたら起点の移設ができていない
- 扉に滞在した10秒の間、本編が裏で現れていない（OKを押した直後にカルーセルが見えていない）

コンソールで確認:

```js
console.log('gate → loading start:', Math.round(window.__loadingStartedAt - window.__gateOpenedAt), 'ms');
```

期待: 扉に10秒滞在した後なら **0〜100 程度**（動画の先読みが扉の滞在中に完了しているため、OK直後にローディングが始まる）。

- [ ] **Step 6: フェイルセーフがOK後に起動することを確認する**

再読み込みし、OKを押さずにコンソールで実行:

```js
console.log('site-frame revealed:', document.querySelector('.site-frame').classList.contains('revealed'));
```

期待: `false`。この状態で放置してもフェイルセーフは動かない（`armLoadingFailsafe()` が未呼び出しのため）。

- [ ] **Step 7: コミット**

```bash
git add sky_collection_card.html
git commit -m "feat: 扉のOKでローディングを開始するようにした

ローディングの本処理を Promise.all([gateOpened, loadingAssetsReady]) の後へ移し、
LOADING_MAX_MS と最終フェイルセーフの起点を OK 後に移した。
起点がページ読込のままだと、扉を放置した人の裏で本編が現れ、
扉を閉じたら既に一覧という壊れ方をする。

心音動画の先読み（loadingScreenReady）だけはページ読込時から走らせ、
扉の滞在時間をバッファリングに充てる。

音の処理はまだ入れていない（次のタスク）。

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01Rq9Emv9qVLQBG21EoLfEoR"
```

---

## Task 3: OKで音を解錠し、心音を立ち上げる

OKのジェスチャーの中で、心音を先頭から音付きで鳴らし直し、BGMは解錠だけして止める。

**この時点では、入場しても蒼穹が鳴らない。これは計画通りの正しい状態。** 旧 `handoffToBgm()` は `primeBgm()` に再生を任せる作りだったが、Task 1 の変更で `primeBgm()` は解錠後すぐ `pause()` するようになるため、誰も `play()` を呼ばなくなる。Task 4 で `startBgm()` を入れて解消する。**このタスクでは入場後の音を検証しない。**

**Files:**
- Modify: `sky_collection_card.html:1406-1411`（`primeBgm()`）
- Modify: `sky_collection_card.html:1420-1447`（`setSound()` と初期化）
- Modify: `sky_collection_card.html` — 扉のコントローラ（Task 2）のクリックハンドラ内

**Interfaces:**
- Consumes: `loadingVideo` / `soundBtn` / `bgm` / `soundOn` / `loadingDone` / `fadeAudio()` / `HEART_VOL` / `BGM_VOL`（既存）
- Produces:
  - `bgmPrimePromise: Promise|null` — 解錠処理の完了を表す（`bgmPrimed` フラグを置き換える）
  - `primeBgm(): Promise` — 解錠のみ。鳴らさない
  - `updateSoundBtn(): void` — `soundOn` の現在値をボタンに反映する（Task 5 でアイコン版に差し替える）
  - `enterFromGate(): void` — 扉のOKハンドラから同期的に呼ぶ

- [ ] **Step 1: `primeBgm()` を「解錠のみ」に変える**

1385行の

```js
let bgmPrimed = false;
```

を以下に置き換える。

```js
let bgmPrimePromise = null; // 解錠処理。二重に走らせない
let bgmStarted = false;     // 一度でも聞こえる形で鳴らしたか（Task 4 の頭出し判定で使う）
```

続いて 1404〜1411行の

```js
// ユーザー操作の中で一度 play() しておくと autoplay ロックが解ける。
// preload="none" でも play() で読み込みが始まる。
function primeBgm() {
  if (bgmPrimed) return;
  bgmPrimed = true;
  bgm.volume = 0;
  bgm.play().catch(() => { bgmPrimed = false; });
}
```

を以下に置き換える。

```js
// ユーザー操作の中で一度 play() しておくと autoplay ロックが解ける。
// preload="none" でも play() で読み込みが始まる。
//
// 【変更点】以前は再生しっぱなしにしていたため、本編に着く頃には蒼穹が
// 数秒〜数十秒進んでいた。ここでは解錠だけして即 pause() し、
// 実際に鳴らすのは startBgm()（Task 4）に任せる。
// play() 直後の pause() は AbortError を投げる環境があるので握り潰す。
function primeBgm() {
  if (bgmPrimePromise) return bgmPrimePromise;
  bgm.volume = 0;
  bgmPrimePromise = bgm.play().then(() => bgm.pause()).catch(() => {});
  return bgmPrimePromise;
}
```

- [ ] **Step 2: `setSound()` からラベル書き換えを切り出す**

1420〜1422行の

```js
function setSound(on) {
  soundOn = on;
  soundBtn.textContent = on ? '♪ ON' : '♪ OFF';
```

を以下に置き換える。

```js
// ボタンには「現在の状態」を出す（押した後どうなるか、ではない）。
// aria-label だけは動作を書く。Task 5 でアイコン版に差し替える。
function updateSoundBtn() {
  soundBtn.textContent = soundOn ? '♪ ON' : '♪ OFF';
  soundBtn.setAttribute('aria-label', soundOn ? '音を消す' : '音を出す');
}

function setSound(on) {
  soundOn = on;
  updateSoundBtn();
```

- [ ] **Step 3: `setSound()` から `primeBgm()` の呼び出しを外す**

`setSound()` の中の以下の行（1425行付近）を**削除する**。解錠は扉のOKで必ず済んでいるため不要になった。残しておくと、`primeBgm()` の `pause()` が `startBgm()` の `play()` と競合する余地が生まれる。

```js
    primeBgm(); // このクリックのうちに解錠しておく
```

削除後の `if (on) {` ブロックの先頭は `if (loadingDone) {` になる。

- [ ] **Step 4: 初期化を差し替える**

1442行の

```js
soundBtn.textContent = '♪ OFF';
```

を以下に置き換える。

```js
updateSoundBtn(); // 初期は OFF。扉の OK（enterFromGate）で ON になる
```

- [ ] **Step 5: `enterFromGate()` を追加する**

音コントローラの末尾、`soundBtn.addEventListener('click', ...)` のブロック（1444〜1447行）の**直後**に挿入する。

```js
// ─── 扉の OK から呼ばれる。すべてユーザー操作の文脈の中で同期的に実行する ───
// ここに await や setTimeout を挟むと、iOS で解錠に失敗する。
function enterFromGate() {
  soundOn = true;
  updateSoundBtn();

  // 蒼穹は「解錠だけ」して止めておく。鳴らすのは本編に着いてから。
  primeBgm();

  // 心音を先頭の拍から鳴らし直す。currentTime=0 により、最初のピークが
  // 1.5秒後に来ることが保証される（msToNextBeatPeak の前提と一致する）。
  try { loadingVideo.currentTime = 0; } catch (e) {}
  loadingVideo.muted = false;
  loadingVideo.volume = 0;
  // 低電力モード等で autoplay が失敗していても、ユーザー操作起点のここで通る。
  // iOS が自動再生を拒否したときに描く再生ボタン（WebKit Bug 219889）も、
  // この経路なら現れない。
  loadingVideo.play().catch(() => {});
  fadeAudio(loadingVideo, 0, HEART_VOL, 800); // いきなり最大音量にしない
}
```

- [ ] **Step 6: 扉のOKハンドラから呼ぶ**

Task 2 で入れたクリックハンドラの先頭にあるコメント

```js
    // 【重要】音の解錠処理は Task 3 でこの位置に入る。
    // await や setTimeout を挟んだ後に play() を呼ぶと、iOS でユーザー操作の
    // 文脈が切れて解錠に失敗する。必ずこのハンドラ内で同期的に実行すること。
```

を以下に置き換える。

```js
    // 【重要】必ずハンドラの先頭で、同期的に呼ぶこと。
    // await や setTimeout を挟んだ後に play() を呼ぶと、
    // iOS でユーザー操作の文脈が切れて解錠に失敗する。
    enterFromGate();
```

- [ ] **Step 7: OK直後に心音が鳴ることを確認する**

ページを再読み込みし、OKを押す。

期待:
- 心音が**フェードインで**鳴り始める（いきなり最大音量にならない）
- 明滅と鼓動の音が同期している
- 左下のボタンが `♪ ON` になっている
- **音楽（蒼穹）はまだ鳴らない**

コンソールで実行:

```js
console.log('soundOn:', soundOn);
console.log('video muted:', loadingVideo.muted, '/ volume:', loadingVideo.volume.toFixed(2));
console.log('bgm paused:', bgm.paused, '/ currentTime:', bgm.currentTime.toFixed(2));
console.log('btn label:', soundBtn.textContent, '/ aria:', soundBtn.getAttribute('aria-label'));
```

期待（OKの1〜2秒後に実行）:
```
soundOn: true
video muted: false / volume: 1.00
bgm paused: true / currentTime: 0.00      ← 解錠のみ。進んでいないこと
btn label: ♪ ON / aria: 音を消す
```

**`bgm paused: false` の場合は解錠が「鳴らしっぱなし」になっている。** `primeBgm()` の `pause()` が効いていないので Step 1 を見直すこと。

- [ ] **Step 8: 心音が先頭から始まっていることを確認する**

再読み込みし、OKを押した**直後**にコンソールで実行:

```js
console.log('video currentTime right after OK:', loadingVideo.currentTime.toFixed(2));
```

期待: **1.0 未満**。扉に長く滞在した後でも 0 付近から始まること。1.0 を大きく超える場合は `currentTime = 0` が効いていない。

- [ ] **Step 9: 左下ボタンで切り替えられることを確認する**

OK後、心音が鳴っている状態で左下の `♪ ON` をタップする。

期待:
- 心音がフェードアウトして止まり、ラベルが `♪ OFF` になる
- もう一度タップすると心音が戻り、`♪ ON` になる

- [ ] **Step 10: コミット**

```bash
git add sky_collection_card.html
git commit -m "feat: 扉のOKで音を解錠し、心音を先頭から鳴らすようにした

OK のクリックハンドラ内で同期的に enterFromGate() を呼ぶ。
心音は currentTime=0 で頭出しして muted を外し、0 から 800ms でフェードイン。
play() をユーザー操作起点で呼ぶ形になったため、iOS 低電力モードで
自動再生が拒否されて再生ボタンが描かれる問題を構造的に回避できる。

primeBgm() は再生しっぱなしをやめ、解錠後すぐ pause() するように変更。
以前は音ONの瞬間から蒼穹が音量0で流れ続け、本編に着く頃には
曲が数秒〜数十秒進んでいた。

この時点では入場しても蒼穹が鳴らない（誰も play() を呼ばなくなるため）。
次のタスクで startBgm() を入れて解消する。

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01Rq9Emv9qVLQBG21EoLfEoR"
```

---

## Task 4: 心音 → 静けさ → 蒼穹

クロスフェードを廃止し、心音が完全に終わってから蒼穹を曲の頭から始める。

```
拍のピークで revealSite() が呼ばれる
  0ms     心音 1.0 ──フェード600ms──▶ 0
  600ms   心音が無音に達する
  700ms   loadingVideo.pause() / オーバーレイ除去（既存の挙動を維持）
          ───── 完全な静けさ 400ms ─────
 1000ms   bgm.currentTime = 0 → play() ──フェード1200ms──▶ 0.28
```

**Files:**
- Modify: `sky_collection_card.html` — 音コントローラ内の `handoffToBgm()` と `setSound()`

**Interfaces:**
- Consumes: `bgmPrimePromise` / `bgmStarted` / `primeBgm()`（Task 3）、`fadeAudio()` / `BGM_VOL` / `loadingDone`（既存）
- Produces:
  - 定数 `HEART_FADE_OUT_MS = 600`、`BGM_START_DELAY_MS = 1000`
  - `startBgm(fadeMs: number): void` — 蒼穹を鳴らし始める。初回だけ曲の頭に巻き戻す

- [ ] **Step 1: 定数を追加する**

1383行の

```js
const BGM_VOL   = 0.28;
```

の直後に以下を追加する。

```js
const HEART_FADE_OUT_MS  = 600;  // 入場時に心音を落としきるまで
const BGM_START_DELAY_MS = 1000; // revealSite() 起点。心音600ms + 完全な静けさ400ms
```

- [ ] **Step 2: `startBgm()` を追加し、`handoffToBgm()` を置き換える**

1413〜1418行の

```js
// 入場時に心音から BGM へ渡す。Task 6 の revealSite() から呼ばれる。
function handoffToBgm() {
  fadeAudio(loadingVideo, loadingVideo.volume, 0, 600);
  primeBgm();
  fadeAudio(bgm, 0, BGM_VOL, 1200);
}
```

を以下で置き換える。

```js
// 蒼穹を鳴らし始める。初めて聞こえる形で鳴らすときだけ曲の頭に巻き戻す。
// 2回目以降のオン／オフは止まった位置から再開する（途中で消してまた点けたときに
// 頭へ戻るのは不自然なため）。
// 解錠(primeBgm)の pause() と play() が競合しないよう、解錠の完了を待ってから鳴らす。
function startBgm(fadeMs) {
  Promise.resolve(primeBgm()).then(() => {
    if (!bgmStarted) {
      bgmStarted = true;
      try { bgm.currentTime = 0; } catch (e) {}
      bgm.volume = 0;
    }
    bgm.play().catch(() => {});
    fadeAudio(bgm, bgm.volume, BGM_VOL, fadeMs);
  });
}

// 入場時。心音を完全に落としきり、静けさを挟んでから蒼穹を始める。
// 以前は両者を同時に走らせるクロスフェードで、約600ms 重なっていた。
function handoffToBgm() {
  fadeAudio(loadingVideo, loadingVideo.volume, 0, HEART_FADE_OUT_MS);
  setTimeout(() => startBgm(1200), BGM_START_DELAY_MS);
}
```

- [ ] **Step 3: `setSound()` の入場後の再開を `startBgm()` に通す**

`setSound()` の中の以下の行（Task 3 適用後、1425行付近）

```js
    if (loadingDone) {
      fadeAudio(bgm, bgm.volume, BGM_VOL, 800);
    } else {
```

を以下に置き換える。扉で音を消していた人が一覧でONにしたときも、蒼穹が頭から鳴るようにする。

```js
    if (loadingDone) {
      startBgm(800); // 初回なら頭出しされる（bgmStarted の判定は startBgm 内）
    } else {
```

- [ ] **Step 4: 被らずに受け渡されることを確認する**

ページを再読み込みし、OKを押して、そのまま本編へ遷移するまで待つ。

期待（耳で確認する）:
- 一覧が現れると同時に心音が引いていく
- **心音が完全に消えた後、一拍の静けさがあってから**蒼穹が入る
- 心音と蒼穹が重なって聞こえる瞬間が無い
- **蒼穹が曲の頭から始まる**（イントロが聞こえる）

コンソールで数値を確認する。再読み込みしてOKを押し、遷移の**直後**に実行:

```js
console.log('bgm currentTime:', bgm.currentTime.toFixed(2), '/ volume:', bgm.volume.toFixed(2));
console.log('video paused:', loadingVideo.paused, '/ volume:', loadingVideo.volume.toFixed(2));
```

期待（遷移から1〜2秒後）:
```
bgm currentTime: 0.xx 〜 1.xx    ← 曲の頭から。10 を超えていたら頭出しが効いていない
bgm volume: 0.0x 〜 0.28         ← フェードイン中
video paused: true / volume: 0.00
```

- [ ] **Step 5: タイミングを計測で確認する**

再読み込みし、OKを押した直後にコンソールで実行してから、遷移まで待つ。

```js
let t0 = null;
const iv = setInterval(() => {
  if (loadingDone && t0 === null) t0 = performance.now();
  if (t0 !== null && !bgm.paused && bgm.volume > 0) {
    console.log('bgm started at +', Math.round(performance.now() - t0), 'ms after reveal');
    clearInterval(iv);
  }
}, 20);
```

期待: `bgm started at + <数値> ms after reveal` の数値が **950〜1150** の範囲。600以下なら `BGM_START_DELAY_MS` が効いていない。

- [ ] **Step 6: 2回目以降は頭に戻らないことを確認する**

遷移後、蒼穹が鳴っている状態で左下ボタンをタップしてOFFにし、10秒待ってからもう一度タップしてONにする。

期待:
- OFFで蒼穹がフェードアウトする
- ONで蒼穹が戻るが、**曲の頭には戻らず続きから鳴る**

コンソールで確認:

```js
console.log('bgm currentTime after resume:', bgm.currentTime.toFixed(1));
```

期待: **10 より大きい値**。0 付近なら `bgmStarted` の判定が効いておらず、毎回頭出ししてしまっている。

- [ ] **Step 7: 扉で音を消した人の経路を確認する**

再読み込みし、OKを押した**直後**に左下ボタンをタップしてOFFにする。そのまま本編へ遷移するまで待つ。

期待:
- ローディング中、心音が鳴らない
- 遷移時に蒼穹も鳴らない（無音のまま一覧が出る）
- 一覧で左下ボタンをタップしてONにすると、**蒼穹が曲の頭から**鳴り始める

コンソールで確認（ONにした直後）:

```js
console.log('bgm currentTime:', bgm.currentTime.toFixed(2), '/ paused:', bgm.paused);
```

期待: `bgm currentTime: 0.xx / paused: false`。解錠が維持されていれば鳴る。**鳴らない場合は `play() → pause()` で解錠が失われている**ので、設計書 §5-2 のフォールバック（音量0で流し続け、到達時に巻き戻す）へ切り替えて報告すること。

- [ ] **Step 8: コミット**

```bash
git add sky_collection_card.html
git commit -m "fix: 心音と蒼穹の被りをなくし、蒼穹を曲の頭から鳴らす

入場時のクロスフェード（心音アウト600ms と 蒼穹イン1200ms の同時実行）を廃止。
心音を落としきり、400ms の静けさを挟んでから蒼穹を始める。

startBgm() を追加し、初めて聞こえる形で鳴らすときだけ currentTime=0 で
頭出しする。2回目以降のオン／オフは止まった位置から再開する。
扉で音を消していた人が一覧で ON にしたときも頭から鳴る。

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01Rq9Emv9qVLQBG21EoLfEoR"
```

---

## Task 5: 左下ボタンをLucideアイコンにする

`♪ ON` / `♪ OFF` のテキストを、Lucide の `volume-2` / `volume-off` のインラインSVGに置き換える。

**Files:**
- Modify: `sky_collection_card.html:213-229`（`.bgm-btn` のCSS）
- Modify: `sky_collection_card.html:570`（`<button class="bgm-btn">`）
- Modify: `sky_collection_card.html` — `updateSoundBtn()`（Task 3 で追加した関数）

**Interfaces:**
- Consumes: `soundBtn` / `soundOn`（既存）
- Produces: CSSクラス `.bgm-btn.is-muted`、`.bgm-btn .icon-sound-on` / `.icon-sound-off`

- [ ] **Step 1: `.bgm-btn` のCSSをアイコン用に差し替える**

213〜229行を以下で置き換える。位置・色・背景・枠線・角丸・hover は変更しない。テキスト用の `font-size` / `letter-spacing` を落とし、`padding` を左右非対称からアイコン用の均等な `7px` に変える（16pxのアイコンと合わせて30px角になり、`border-radius: 16px` で円形に収まる）。

```css
  .bgm-btn {
    position: fixed;
    bottom: 18px;
    left: 18px;
    z-index: 200;
    background: rgba(255,255,255,0.05);
    border: 0.5px solid rgba(255,255,255,0.12);
    border-radius: 16px;
    padding: 7px;
    color: rgba(255,255,255,0.28);
    display: grid;
    place-items: center;
    cursor: pointer;
    transition: background 0.3s, color 0.3s, opacity 0.3s;
    user-select: none;
  }
  .bgm-btn:hover { background: rgba(255,255,255,0.1); color: rgba(255,255,255,0.55); }

  /* Lucide の volume-2（音あり）/ volume-off（音なし）。
     stroke="currentColor" なので .bgm-btn の color がそのまま効く。
     表示するのは「現在の状態」で、押した後どうなるかではない。 */
  .bgm-btn svg { display: block; width: 16px; height: 16px; }
  .bgm-btn .icon-sound-off { display: none; }
  .bgm-btn.is-muted .icon-sound-on { display: none; }
  .bgm-btn.is-muted .icon-sound-off { display: block; }
```

- [ ] **Step 2: ボタンの中身をSVGに置き換える**

570行の

```html
<button class="bgm-btn" id="bgmBtn">♪ OFF</button>
```

を以下で置き換える。パスは `lucide-icons/lucide` の `icons/volume-2.svg` / `icons/volume-off.svg` そのまま。CDNを使わないのは、追加リクエストを増やさないためと、読み込み前に一瞬アイコンが消えるのを避けるため。

```html
<button class="bgm-btn" id="bgmBtn" type="button" aria-label="音を出す">
  <svg class="icon-sound-on" xmlns="http://www.w3.org/2000/svg" width="16" height="16"
       viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
       stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
    <path d="M11 4.702a.705.705 0 0 0-1.203-.498L6.413 7.587A1.4 1.4 0 0 1 5.416 8H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.416a1.4 1.4 0 0 1 .997.413l3.383 3.384A.705.705 0 0 0 11 19.298z"/>
    <path d="M16 9a5 5 0 0 1 0 6"/>
    <path d="M19.364 18.364a9 9 0 0 0 0-12.728"/>
  </svg>
  <svg class="icon-sound-off" xmlns="http://www.w3.org/2000/svg" width="16" height="16"
       viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
       stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
    <path d="M16 9a5 5 0 0 1 .95 2.293"/>
    <path d="M19.364 5.636a9 9 0 0 1 1.889 9.96"/>
    <path d="m2 2 20 20"/>
    <path d="m7 7-.587.587A1.4 1.4 0 0 1 5.416 8H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.416a1.4 1.4 0 0 1 .997.413l3.383 3.384A.705.705 0 0 0 11 19.298V11"/>
    <path d="M9.828 4.172A.686.686 0 0 1 11 4.657v.686"/>
  </svg>
</button>
```

- [ ] **Step 3: `updateSoundBtn()` をアイコン切り替えに変える**

Task 3 で追加した

```js
function updateSoundBtn() {
  soundBtn.textContent = soundOn ? '♪ ON' : '♪ OFF';
  soundBtn.setAttribute('aria-label', soundOn ? '音を消す' : '音を出す');
}
```

を以下に置き換える。`textContent` を書くとSVGが消し飛ぶので、必ずクラスの付け外しにすること。

```js
function updateSoundBtn() {
  soundBtn.classList.toggle('is-muted', !soundOn); // 表示するのは現在の状態
  soundBtn.setAttribute('aria-label', soundOn ? '音を消す' : '音を出す');
}
```

- [ ] **Step 4: アイコンの切り替えを確認する**

ページを再読み込みする。

期待:
- 扉が出ている間、左下のボタンは見えない
- OKを押すと、左下に**波紋が出ているスピーカー**（`volume-2`）が現れる
- タップすると**斜線の入ったスピーカー**（`volume-off`）に変わり、心音が止まる
- もう一度タップすると波紋に戻り、心音が鳴る
- アイコンの色が周囲と同じ淡い白で、hover すると明るくなる
- スピーカー本体の位置と大きさが、切り替えても**動かない**

コンソールで確認:

```js
console.log('aria:', soundBtn.getAttribute('aria-label'), '/ is-muted:', soundBtn.classList.contains('is-muted'));
console.log('svg count:', soundBtn.querySelectorAll('svg').length);
const r = soundBtn.getBoundingClientRect();
console.log('btn size:', Math.round(r.width), 'x', Math.round(r.height));
```

期待（音ONの状態）:
```
aria: 音を消す / is-muted: false
svg count: 2          ← 1 になっていたら textContent でSVGを消している
btn size: 31 x 31     ← 30〜32 程度
```

- [ ] **Step 5: 3Dモーダルとの重なりが変わっていないことを確認する**

一覧でカードの「3D で見る ›」を押す。

期待: 3Dモーダル（z-index 300）が開いたとき、左下のアイコンが**モーダルの背後に隠れる**。`.bgm-btn` の平常時 z-index 200 を変えていないので、既存の挙動と同じであること。

- [ ] **Step 6: コミット**

```bash
git add sky_collection_card.html
git commit -m "feat: 左下の音ボタンを Lucide アイコンにした

♪ ON / ♪ OFF のテキストを volume-2 / volume-off のインラインSVGに置き換え。
CDN は使わず埋め込む（追加リクエストなし・読み込み前の欠けなし）。
stroke=currentColor により既存の色と hover がそのまま効く。

表示するのは現在の状態（volume-2 = 鳴っている）。aria-label のみ動作を書く。
位置・色・背景・枠線・角丸・平常時の z-index は変更なし。
タップ領域の拡大は今回のスコープ外。

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01Rq9Emv9qVLQBG21EoLfEoR"
```

---

## Task 6: 実機確認

PCブラウザだけでは検証できない項目が集中している。とくに **iOS低電力モードでの再生ボタン**は、直近2コミット（`09d6ab4` / `3c2d152`）で対処していた問題であり、本設計で構造的に解消するはずの本命。

**Files:** 変更なし（問題が見つかった場合を除く）

- [ ] **Step 1: ローカルサーバを起動する**

`serve` スキルを使い、Tailscale経由でスマートフォンからアクセスできる状態にする。`file://` では `fetch()` がCORSで失敗するため、必ずHTTPで配信すること。

- [ ] **Step 2: iOS 低電力モードで再生ボタンが出ないことを確認する（本命）**

iPhoneで「設定 → バッテリー → 低電力モード」をONにしてから、Safariでキャッシュを消した状態で開く。

期待:
- 扉が出る
- OKを押すと心音の映像が出て、**再生ボタン（▶の丸いオーバーレイ）が一瞬たりとも見えない**
- 心音が音付きで鳴る

**再生ボタンが見えた場合は報告すること。** `enterFromGate()` の `loadingVideo.play()` がユーザー操作の文脈の中で呼べていない可能性がある（ハンドラ内に `await` や `setTimeout` が紛れ込んでいないか確認する）。

低電力モードをOFFに戻して、同じ確認をもう一度行う。

- [ ] **Step 3: OK直後の心音を確認する**

iOSのサイレントスイッチをOFFにして（ONだと仕様上 `<video>` の音声が鳴らない）、再読み込みしてOKを押す。

期待:
- 心音が**フェードインで**鳴り始める（いきなり最大音量にならない）
- 心音が**曲の頭の拍から**始まる
- 映像の明滅と鼓動の音が同期している

- [ ] **Step 4: 心音から蒼穹への受け渡しを確認する**

そのまま本編へ遷移するまで待つ。

期待:
- 一覧が現れると心音が引いていく
- **心音が完全に消えた後、一拍の静けさがあってから**蒼穹が入る
- 重なって聞こえる瞬間が無い
- **蒼穹が曲の頭から始まる**（イントロが聞こえる）

- [ ] **Step 5: 解錠が維持されていることを確認する**

再読み込みし、OKを押した直後に左下アイコンをタップして音を消す。そのまま本編へ遷移するまで待ち、一覧で左下アイコンをタップして音を出す。

期待: **蒼穹が曲の頭から鳴り始める。**

**鳴らない場合**は `play() → pause()` の解錠が iOS で維持されていないということなので、設計書 §5-2 のフォールバックへ切り替える。`primeBgm()` の `.then(() => bgm.pause())` を外して音量0のまま流し続け、`startBgm()` の `currentTime = 0` で頭出しする形にする。切り替えた場合はその旨を報告に含めること。

- [ ] **Step 6: 扉の見え方と操作性を確認する**

期待:
- 縦画面で文字が中央に収まり、端で折り返して読みにくくなっていない
- 主文と説明の大きさ・明るさの差がついている
- OKボタンが親指の届く位置にあり、押しやすい大きさである
- 扉の表示中にページが縦にスクロールしない（ラバーバンドしない）
- OKを押したときの暗転に、白い明滅や継ぎ目が無い

- [ ] **Step 7: 低速回線を模擬して確認する**

PCブラウザで、DevToolsのNetworkスロットリングを `Slow 4G` にして再読み込みする。

期待:
- 扉が**即座に**出る（テキストだけなので待ちが無い）
- OK後、心音のループを回り続けて待つ（途中で止まったり暗転したりしない）
- 最終的に遷移し、蒼穹が頭から鳴る

- [ ] **Step 8: 既存機能が壊れていないことを確認する**

遷移後、カルーセルを端から端まで数往復スクラブし、複数のカードをフリップし、3Dビューを開閉する。

期待:
- ブラウザがクラッシュしない
- めくった裏面が黒いまま止まらない
- 3Dモーダルが画面全体に開き、左下アイコンがその背後に隠れる
- スクラブが引っかからない

- [ ] **Step 9: 結果を報告する**

問題が見つかった場合は、修正して該当タスクの検証をやり直す。問題が無ければ変更なしで次へ進む。

Step 2（低電力モードの再生ボタン）と Step 5（解錠の維持）の結果は、成否にかかわらず必ず報告に含めること。

---

## 完了後

- `feat/loading-screen` を `main` へマージする
- `main` を `origin` へ push する
