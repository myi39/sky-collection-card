"""表画像を表示用に縮小する。
元画像は images/card_front/raw/ に退避し、800px幅の軽量版を元の場所に書き出す。
冪等（再実行しても raw/ の元画像から作り直すだけ）。
"""
import glob
import os
import shutil
from PIL import Image

SRC_DIR = "images/card_front"
RAW_DIR = os.path.join(SRC_DIR, "raw")
TARGET_W = 480
QUALITY = 82

os.makedirs(RAW_DIR, exist_ok=True)

files = sorted(glob.glob(os.path.join(SRC_DIR, "*.jpg")))
count = 0
total_raw = 0
total_out = 0
sample_dim = None

for f in files:
    name = os.path.basename(f)
    raw_path = os.path.join(RAW_DIR, name)
    # 元画像を raw/ へ退避（初回のみ。2回目以降は raw/ を正とする）
    if not os.path.exists(raw_path):
        shutil.move(f, raw_path)

    im = Image.open(raw_path).convert("RGB")
    w, h = im.size
    if w > TARGET_W:
        new_h = round(h * TARGET_W / w)
        im = im.resize((TARGET_W, new_h), Image.LANCZOS)

    out_path = os.path.join(SRC_DIR, name)
    im.save(out_path, "JPEG", quality=QUALITY, optimize=True, progressive=True)

    count += 1
    total_raw += os.path.getsize(raw_path)
    total_out += os.path.getsize(out_path)
    if sample_dim is None:
        sample_dim = im.size

print(f"processed={count}")
print(f"raw_total_MB={total_raw/1024/1024:.1f}")
print(f"out_total_MB={total_out/1024/1024:.1f}")
print(f"sample_out_dim={sample_dim}")
