"""Gera as versoes web das imagens 360 a partir da pasta 360/ (originais).

Uso:  python tools/build_panos.py
Saida: panos/<id>_4k.jpg (celular/VR), panos/<id>_8k.jpg (desktop), panos/<id>_thumb.jpg
"""
import re
import sys
from pathlib import Path
from PIL import Image

Image.MAX_IMAGE_PIXELS = None
ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "360"
OUT = ROOT / "panos"
OUT.mkdir(exist_ok=True)

SIZES = {"8k": (8192, 4096, 80), "4k": (4096, 2048, 84)}


def scene_id(name: str) -> str:
    m = re.match(r"WEEMO_360_(\d+)_(.+?)(_P\d+)?$", Path(name).stem)
    if not m:
        return Path(name).stem.lower()
    return f"{m.group(1)}-{m.group(2).lower().replace('_', '-')}"


for src in sorted(SRC.glob("*.jpg")):
    sid = scene_id(src.name)
    with Image.open(src) as im:
        im = im.convert("RGB")
        for tag, (w, h, q) in SIZES.items():
            dst = OUT / f"{sid}_{tag}.jpg"
            im.resize((w, h), Image.LANCZOS).save(dst, "JPEG", quality=q, progressive=True, optimize=True)
        # miniatura: faixa central 16:9 do equador
        W, H = im.size
        cw, ch = W // 4, int(W // 4 * 9 / 16)
        box = (W // 2 - cw // 2, H // 2 - ch // 2, W // 2 + cw // 2, H // 2 + ch // 2)
        im.crop(box).resize((480, 270), Image.LANCZOS).save(OUT / f"{sid}_thumb.jpg", "JPEG", quality=80, progressive=True)
    print(sid, flush=True)
