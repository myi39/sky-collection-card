"""表画像を表示用に最適化する。
元画像は images/card_front/raw/ に退避し、raw から2種類を書き出す:
  - 表示用 480px  → images/card_front/      （全カード常駐用の軽量版）
  - 高画質 800px  → images/card_front_hi/   （中央カードだけ表示する高画質版）
冪等（再実行しても raw/ の元画像から作り直すだけ。劣化は累積しない）。
"""
import glob
import os
import shutil
from PIL import Image

SRC_DIR = "images/card_front"
RAW_DIR = os.path.join(SRC_DIR, "raw")
TARGET_W = 480
HI_W = 800
HI_DIR = "images/card_front_hi"
QUALITY = 82

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(HI_DIR, exist_ok=True)

files = sorted(glob.glob(os.path.join(SRC_DIR, "*.jpg")))
count = 0
total_raw = 0
total_out = 0
total_hi = 0
sample_dim = None
sample_hi_dim = None

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

    # 高画質版（中央カード用）も raw から生成（480版を拡大しない）
    hi = Image.open(raw_path).convert("RGB")
    if hi.size[0] > HI_W:
        hi = hi.resize((HI_W, round(hi.size[1] * HI_W / hi.size[0])), Image.LANCZOS)
    hi.save(os.path.join(HI_DIR, name), "JPEG", quality=QUALITY, optimize=True, progressive=True)

    count += 1
    total_raw += os.path.getsize(raw_path)
    total_out += os.path.getsize(out_path)
    total_hi += os.path.getsize(os.path.join(HI_DIR, name))
    if sample_dim is None:
        sample_dim = im.size
        sample_hi_dim = hi.size

print(f"processed={count}")
print(f"raw_total_MB={total_raw/1024/1024:.1f}")
print(f"out_total_MB(480)={total_out/1024/1024:.1f}")
print(f"hi_total_MB(800)={total_hi/1024/1024:.1f}")
print(f"sample_out_dim={sample_dim} sample_hi_dim={sample_hi_dim}")
