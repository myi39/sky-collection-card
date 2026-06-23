"""裏画像の透明余白をトリミングする。
元画像は images/card_back/raw/ に退避し、不透明領域(alpha bbox)で切り抜いて
元の場所(images/card_back/)に書き出す。冪等（再実行しても raw/ から作り直すだけ）。

裏画像は四辺に約36pxの透明余白があり、これがカードの縁との「隙間」の原因。
切り抜くことでデザイン(黒地＋白枠)が端まで来る。表示は object-fit:cover のため、
切り抜き後の比率(約1.456)とカード枠(1.4274)の差で上下が約1%だけ見切れる（白枠は無傷）。
"""
import glob
import os
import shutil
from PIL import Image

SRC_DIR = "images/card_back"
RAW_DIR = os.path.join(SRC_DIR, "raw")

os.makedirs(RAW_DIR, exist_ok=True)

files = sorted(glob.glob(os.path.join(SRC_DIR, "*.png")))
count = 0
sample = None

for f in files:
    name = os.path.basename(f)
    raw_path = os.path.join(RAW_DIR, name)
    # 元画像を raw/ へ退避（初回のみ。2回目以降は raw/ を正とする）
    if not os.path.exists(raw_path):
        shutil.move(f, raw_path)

    im = Image.open(raw_path)
    bbox = im.getbbox()  # 不透明（非ゼロ）領域の範囲
    out = im.crop(bbox) if bbox else im
    out.save(os.path.join(SRC_DIR, name))

    count += 1
    if sample is None:
        sample = (im.size, out.size, bbox)

print(f"processed={count}")
print(f"sample before={sample[0]} after={sample[1]} bbox={sample[2]}")
