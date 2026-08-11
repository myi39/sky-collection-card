"""裏画像の低解像度版を生成する（非中央フリップ時のメモリ節約用フォールバック）。

表示中（トリミング済み）の裏画像 images/card_back/*.png を、そのまま等比縮小して
images/card_back_lo/ に出力する。トリミングはやり直さないため、フル版と完全に同じ
切り抜き・縦横比のまま解像度だけ落ちる（カード枠・object-fit:cover 表示と一致）。
冪等（再実行しても card_back/ から作り直すだけ）。
"""
import glob
import os
from PIL import Image

SRC_DIR = "images/card_back"       # 表示中のトリミング済みフル版（これを正とする）
LO_DIR = "images/card_back_lo"     # 出力：低解像度フォールバック
TARGET_W = 300                     # 非中央表示なら十分な幅

os.makedirs(LO_DIR, exist_ok=True)

# raw/ は元画像退避フォルダなので除外し、card_back 直下の png のみ対象
files = sorted(f for f in glob.glob(os.path.join(SRC_DIR, "*.png")))

count = 0
total_full = 0
total_lo = 0
sample = None

for f in files:
    name = os.path.basename(f)
    im = Image.open(f)
    w, h = im.size
    if w > TARGET_W:
        new_h = round(h * TARGET_W / w)
        lo = im.resize((TARGET_W, new_h), Image.LANCZOS)
    else:
        lo = im
    out_path = os.path.join(LO_DIR, name)
    lo.save(out_path, optimize=True)

    count += 1
    total_full += os.path.getsize(f)
    total_lo += os.path.getsize(out_path)
    if sample is None:
        sample = (im.size, lo.size)

print(f"processed={count}")
print(f"full_total_MB={total_full/1024/1024:.2f}")
print(f"lo_total_MB={total_lo/1024/1024:.2f}")
print(f"sample full={sample[0]} lo={sample[1]}")
