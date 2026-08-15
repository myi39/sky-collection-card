# 3D ビューア統合 — デザインドキュメント

Date: 2026-05-09

## 概要

`sky_collection_card.html` に Three.js を使った3Dビューア機能を追加する。
右下の「View Mode」セレクターで3つの表示モードを切り替えられるようにする。

---

## View Mode セレクター（右下）

画面右下に固定配置。既存の BGM ボタン（左下）とは反対側。

**3つの選択肢（ラジオボタン方式）：**

| 選択肢 | 内容 |
|--------|------|
| 現在（画像） | 現行のデザイン（変更なし） |
| 案A（3Dに置換） | カード表面の画像を Three.js キャンバスに置換 |
| 案B（ボタンで3D） | カード上にボタン → モーダルで3D表示 |

初期状態は「現在（画像）」。

---

## 案A — カード表面を3Dに置換

**動作：**
- 中央カードの表面（`.card-face` 前面）に Three.js キャンバスを描画
- カード切り替え時に3Dシーンも切り替わる（同じ GLTFモデル、将来は個別対応）
- キャンバス上でドラッグ → 回転、ピンチ/ホイール → ズーム（OrbitControls）
- サイドカードは通常の画像表示のまま

**実装方針：**
- Three.js レンダラーは1つのみ（複数 WebGL コンテキスト問題を回避）
- 中央カードの `.card-face` に重なる `<canvas>` を絶対配置
- `current` が変わるたびにキャンバスの位置を更新

---

## 案B — ボタン → モーダル3D表示

**ボタン配置：**
- カード枠の**上**（カルーセルの `padding: 30px 0` の上余白内）に配置
- `card-slot` に `position: relative` を追加し、ボタンを `position: absolute; top: ~6px; right: 0` で浮かせる（カード上端より上、カルーセルの 30px 上余白内に収まる）
- 画像サイズ・位置に一切影響しない

**モーダル動作：**
- 「3D ▶」クリック → 全画面オーバーレイモーダルが開く
- モーダル内に Three.js キャンバス（ドラッグ回転、ズーム対応）
- カード名を表示
- 右上の ✕ ボタンまたはオーバーレイ背景クリックで閉じる
- モーダル開閉時に Three.js レンダラーを初期化 / 破棄

---

## データ構造

各カードに `modelSrc` フィールドを追加。将来の個別ファイル対応に備える。

```js
const players = [
  { num:"01", name:"Sample 01", desc:"...", emoji:"🌊",
    frontImg:"images/image1.jpg",
    modelSrc:"3d/3d_sample_hal.gltf" },  // 今は全カード共通
  ...
];
```

---

## Three.js 読み込み

CDN から importmap 経由で読み込む（ビルドツール不要）。

```html
<script type="importmap">
{
  "imports": {
    "three": "https://cdn.jsdelivr.net/npm/three@0.165.0/build/three.module.js",
    "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.165.0/examples/jsm/"
  }
}
</script>
```

使用モジュール: `GLTFLoader`, `OrbitControls`

---

## スコープ外

- BGM、カルーセルドラッグ、フリップアニメーション、特殊カード reveal は変更しない
- モバイル向けの追加最適化は今回含まない
- カードのフリップ（表→裏）と3Dの組み合わせは今回含まない
