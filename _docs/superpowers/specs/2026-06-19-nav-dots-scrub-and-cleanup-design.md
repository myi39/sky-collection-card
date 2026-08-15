# 目次ドットのスクラブ機能 ＋ plan_b メイン化・整理

日付: 2026-06-19
対象ファイル: `sky_collection_card_plan_b.html`（作業後 `sky_collection_card.html` にリネーム）

## 背景・目的

カルーセル（カード一覧）の下にある小さなドット列（`.nav-dots`）は、現在クリックで該当カードへジャンプするだけ。これを **iPhone のホーム画面下部のページドットのように、指で押したまま左右になぞって（スクラブして）カードを高速に切り替えられる** ようにする。

あわせて、案B（plan_b）を正式採用したため、ファイル構成を plan_b 中心に整理する。

## スコープ全体像

3つのフェーズに分け、各フェーズの区切りでコミット（フェーズ1・2はユーザー確認後にコミット）。

- **フェーズ1**: ファイル整理（アーカイブ＋リネーム）＋ モード切替セレクタUI・遷移リンクの除去
- **フェーズ2**: 内部の死にコード（画像版・案Aの描画ロジック）の掃除
- **フェーズ3**: 目次ドットのスクラブ機能の実装

ブランチ: `feat/nav-dots-scrub`

---

## フェーズ1: ファイル整理 ＋ セレクタ除去

### ファイル移動（`git mv` で履歴保持）

1. `sky_collection_card.html`（画像版）→ `archive/sky_collection_card_image.html`
2. `sky_collection_card_plan_a.html` → `archive/sky_collection_card_plan_a.html`
3. `sky_collection_card_plan_b.html` → `sky_collection_card.html`（メイン）

> 名前衝突を避けるため、必ず「画像版を退避 → plan_b をリネーム」の順で行う。

触らないファイル: `index.html`（プレースホルダー）、`3d_test.html`（テスト用）。

### セレクタUI・遷移リンクの除去（リネーム後の `sky_collection_card.html` 内）

- HTML: `<select id="viewModeSel">`（旧 511–515 行）を削除
- JS: `MODE_FILES` と `viewModeSel` の `change` リスナー（旧 1222–1231 行）を削除
- CSS: `#viewModeSel`（旧 313 行付近）を削除
- `setViewMode` 内の `document.getElementById('viewModeSel').value = mode;`（旧 1197 行）を削除し、セレクタ参照で落ちないようにする

> このフェーズでは内部の plan-a / 画像描画コードはまだ残す（セレクタ除去だけで挙動が壊れないことを優先）。

### 完了条件

- リネーム後の `sky_collection_card.html` をブラウザで開き、案B（カルーセル＋「3Dで見る」ボタン）が従来通り動く
- コンソールエラーが出ない（特にセレクタ削除に伴う参照エラーがない）
- ユーザー確認 → コミット

---

## フェーズ2: 死にコードの掃除

plan-b（カルーセル＋「3Dで見る」ボタン→モーダル3D）以外のモード用コードを除去する。

### 除去対象（相互依存があるため慎重に）

- **JS**
  - `viewMode` グローバル変数（旧 543 行）と、それを参照する分岐（`viewMode !== 'plan-a'` など）
  - 案A 3D描画一式: `planARenderer` / `planAAnimId` / `planAScenes` / `planACameras` / `planAModels`、`planA_animate` / `planA_init` / `planA_onCardChange`（旧 1015–1088 行）
  - `render()` 内の `planA_onCardChange()` フック呼び出し（旧 752 行）
  - `setViewMode` 全体（旧 1194–1220 行）→ plan-b 固定の初期化に置き換え（`.btn-3d` を表示する処理のみ残す）
  - 末尾の `setViewMode('plan-b')` 呼び出し（旧 1239 行）の置き換え
- **HTML**
  - `<canvas id="canvas-plan-a">`（旧 457 行）
- **CSS**
  - `#canvas-plan-a`（旧 331 行付近）
  - `body.viewmode-plan-a ...`（旧 339 行付近）

### 要確認の依存（実装時に検証）

- `resetBtn` / `.planA-reset-show` / `@keyframes planAResetAppear`（旧 439–444, 1143–1155, 1186 行）が **plan-a 専用か、plan-b でも使うか** を確認してから除去判断する。plan-b でも使うなら残す。

### 完了条件

- 案B が従来通り動く（カルーセル、3Dモーダル、BGM、リビールなど既存機能に影響なし）
- コンソールエラーなし、未定義参照なし
- ユーザー確認 → コミット

---

## フェーズ3: 目次ドットのスクラブ機能

### 挙動

- `.nav-dots` 上で **押した瞬間**、指の位置に最も近いドットのカードへ移動（タップ＝従来通り効く）
- 押したまま **左右になぞる** と、指の位置に最も近いドットのカードへリアルタイムで次々移動
- 指を離すと終了。なぞり中はページの縦スクロールを抑止（`touch-action` / `preventDefault`）

### 位置判定

- active ドットだけ幅が広く（5px → 15px pill）間隔が不均一なため、単純な座標割り算ではなく **各ドットの中心X座標との最近傍** で対象インデックスを決める
- スクラブ開始時に各ドットの中心X座標をキャッシュし、`pointermove` ごとに最近傍を求める

### フィードバック（案2: 視覚pop ＋ Android振動）

- **視覚pop**: カードが切り替わった瞬間、新 active ドットが一瞬ピクッと弾む（CSSキーフレーム、scale 約1.6倍・約120ms の控えめな弾み。強さは調整可能なパラメータにする）
- **追従**: active ドット（pill）が指の位置へ滑らかに移動（既存 transition を活かしつつ、なぞり中は応答性のため必要なら短縮）
- **Android振動**: 切り替わるたび `navigator.vibrate(10)`（iOS Safari は Vibration API 非対応のため無視されるだけ。害なし）

### 既存コードとの統合

- 既存の各ドットの `click` リスナー（`buildDots` 内、旧 607 行）を廃止し、`.nav-dots` コンテナ側の統一ポインタハンドラ（down/move/up）に置き換え。タップもなぞりも1経路で処理
- スクラブのイベントは `stopPropagation` し、カルーセル本体のスワイプ／ドラッグ処理（`carouselDrag*`, `isUIElement`）と衝突させない
- リビール前にドットが非表示・本数が変化する既存仕様（`buildDots` の早期 return、`revealDone` による本数変化）と整合させる

### 完了条件

- スマホ実機（できれば iPhone と Android 両方）で、なぞってカードが追従移動する
- タップでのジャンプも従来通り効く
- カルーセルのスワイプと干渉しない
- 視覚 pop が出る／Android では振動する

---

## 非対象（YAGNI）

- iPhone でのハプティクス（Apple が Web の Vibration API を塞いでいるため不可能）
- 効果音によるフィードバック（iOS の制約・人前での気まずさで体験が不安定なため見送り）
- plan-a / 画像版の機能維持（archive/ に退避し、必要時に参照）
