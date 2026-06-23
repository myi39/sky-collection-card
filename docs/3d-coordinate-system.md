# 3D データの座標系ガイド

## 基準座標系

このプロジェクトでは **Three.js の座標系を正として話す**。

- X+ = 右
- Y+ = 上
- Z+ = 手前（カメラ方向）

---

## Blender → GLB で Y と Z が入れ替わる問題

Blender は Y+ が奥・Z+ が上。Three.js は Y+ が上・Z+ が手前。  
GLB エクスポーター（Y Up 設定）がこの変換を自動処理するが、**モデルの「正面」がどちらを向くか**はモデルの作り方次第で変わる。

モデルの出力向きはエクスポート設定で変わるため、補正値はモデルに依存する。

- 旧モデル: Three.js で読み込むと向きがズレていたため `rotation.x = Math.PI / 2` で補正していた。
- 現行モデル（2026/06/21 差し替え）: 最初から正面（+Z）を向いて出力されているため**向き補正は不要**（`rotation` は触らない）。

モデルを再エクスポートしたら向きが変わり得るので、`3d_test.html` で正しい角度を目視確認してから本番に反映する。

---

## 問題のある実装パターン（現状）

```javascript
// モデルに補正とユーザー操作が混在している
model.rotation.set(Math.PI / 2 + rot[0], 0, rot[1]);
```

`Math.PI/2` の補正と、ユーザードラッグ由来の `rot[0]`, `rot[1]` が同じ `rotation.set` に混在している。  
これにより操作コードを「補正済みの軸」で書く必要が生じ、直感に反する軸マッピングになる（横ドラッグを Y でなく Z に入れるなど）。

---

## 正しい実装パターン（ピボット分離）

```javascript
// ── ロード時 ──
const pivot = new THREE.Object3D();
scene.add(pivot);

loader.load(src, gltf => {
  gltf.scene.rotation.x = Math.PI / 2; // ← 補正は子（モデル）に固定
  pivot.add(gltf.scene);               // ← 子としてぶら下げる
});

// ── レンダーループ・イベント ──
// 操作は pivot（親）に対して行う → Three.js の自然な座標系で書ける
pivot.rotation.x += dy * sensitivity; // 縦ドラッグ → X 軸チルト（前後傾き）
pivot.rotation.y += dx * sensitivity; // 横ドラッグ → Y 軸スピン（縦軸回転）
```

**ルール：**
- `gltf.scene`（子）: 座標補正のみ。ユーザー操作は与えない。
- `pivot`（親）: ユーザー操作のみ。補正は持たない。
- 操作コードは常に Three.js 標準の軸（横→Y、縦→X）で記述する。

---

## 操作軸のまとめ

| ユーザー操作 | 回転軸 | 意味 |
|---|---|---|
| 横スワイプ | Y 軸 | カードが縦軸で回転（回転ドア） |
| 縦スワイプ | X 軸 | カードが前後に傾く |
| 使わない | Z 軸 | カードが画面内でくるくる回る（不要） |

---

## Plan A / Plan B での注意

- **Plan A / Plan B ともに OrbitControls を使用**。手動ドラッグ回転は実装しない。
- モデルの座標補正（`rotation.x = Math.PI/2`）は pivot の子に固定し、OrbitControls はカメラ操作として独立させる。

---

## このプロジェクトの 3D 実装標準

新しく 3D ビューアを実装するときは以下のパターンに従う。

### インタラクション：OrbitControls を使う

手動でドラッグ回転を実装しない。Three.js の OrbitControls を使う。  
回転・ズーム・パンが最初から入っており、軸ズレの心配もない。

```javascript
const controls = new OrbitControls(camera, domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.06;
controls.enablePan = true;
```

### モデル配置：pivot パターン

座標補正（`rotation.x = Math.PI/2`）をモデル（子）に固定し、親の pivot には何も持たせない。  
OrbitControls はカメラを操作するためモデル側は変更不要。

```javascript
const pivot = new THREE.Object3D();
scene.add(pivot);

loader.load(src, gltf => {
  gltf.scene.rotation.x = Math.PI / 2; // 子に固定
  pivot.add(gltf.scene);
});
```

### 複数モデルを 1 canvas に scissor 描画する場合（Plan A 方式）

複数の OrbitControls を同じ canvas に付与すると競合する。  
代わりに、アクティブなカード上に透明な overlay div を作り、そこに OrbitControls を 1 つ付与する。  
カードが切り替わるたびに `dispose()` して新しいカメラで再生成する。

```javascript
// overlay div をセンターカードの位置に毎フレーム同期
const r = face.getBoundingClientRect();
overlay.style.left = r.left + 'px';
overlay.style.top  = r.top  + 'px';
// カードが変わったら差し替え
controls.dispose();
controls = new OrbitControls(cameras[newCenterIdx], overlay);
```
