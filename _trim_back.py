"""裏画像の透明余白をトリミングし、表示用サイズに収める。
元画像は images/card_back/raw/ に退避し、不透明領域(alpha bbox)で切り抜いて
元の場所(images/card_back/)に書き出す。冪等（再実行しても raw/ から作り直すだけ）。

初期の裏画像は四辺に約36pxの透明余白があり、これがカードの縁との「隙間」の原因。
切り抜くことでデザイン(黒地＋白枠)が端まで来る。

注意点2つ:
  - bbox は必ず「アルファチャンネル」から取る。im.getbbox() は RGB 画像だと
    「黒でない領域」を返すため、黒地の裏画像から黒縁を丸ごと削ってしまう。
    アルファが無い画像はトリミング対象外とする。
  - No.30 以降の裏画像は 3276px 幅で入稿されるため、MAX_W まで縮小する。
    表示は最大でも 340csspx x DPR3 ≒ 1020px であり、原寸のまま持つと
    中央カードのデコード時にモバイルでメモリを圧迫する。
"""
import glob
import os
import shutil
from PIL import Image

SRC_DIR = "images/card_back"
RAW_DIR = os.path.join(SRC_DIR, "raw")
MAX_W = 800  # 表示用フル版の上限幅（card_front_hi と揃える）

os.makedirs(RAW_DIR, exist_ok=True)

files = sorted(glob.glob(os.path.join(SRC_DIR, "*.png")))
count = 0
rows = []

for f in files:
    name = os.path.basename(f)
    raw_path = os.path.join(RAW_DIR, name)
    # 元画像を raw/ へ退避（初回のみ。2回目以降は raw/ を正とする）
    if not os.path.exists(raw_path):
        shutil.move(f, raw_path)

    im = Image.open(raw_path)
    before = im.size

    # 透明余白のトリミング（アルファを持つ画像のみ）
    if im.mode in ("RGBA", "LA"):
        bbox = im.getchannel("A").getbbox()
        if bbox:
            im = im.crop(bbox)

    # 表示用サイズへ縮小
    if im.size[0] > MAX_W:
        im = im.resize((MAX_W, round(im.size[1] * MAX_W / im.size[0])), Image.LANCZOS)

    im.save(os.path.join(SRC_DIR, name), optimize=True)

    count += 1
    rows.append((name, before, im.size))

print(f"processed={count}")
for name, before, after in rows:
    if before != after:
        print(f"  {name}: {before[0]}x{before[1]} -> {after[0]}x{after[1]}")
