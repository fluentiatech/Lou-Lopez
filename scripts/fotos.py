"""Prepare the photos for the About and Career slots from design/fotos-candidatas/
(the wide About photo comes from design/fotos-galeria/).

    python scripts/fotos.py

Each photo is cropped to the shape of its slot (4:5, or 16:9 for the wide one) around the
player and saved to img/ as WebP. The club's studio photo is on a white backdrop, so it is
cut out with scripts/cutout.py and sits on the page's own wall, like the hero.

Needs: pip install pillow (plus what cutout.py needs).
"""
import os
import subprocess
import sys
import tempfile

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "design")
OUT = os.path.join(ROOT, "img")

# output name: (source under design/, crop box in source pixels, output width, keep transparency)
CROPS = {
    "about-jairis.webp": ("fotos-galeria/jairis-copa-2025-IMG_7079.jpg", (0, 100, 1500, 944), 1500, False),
    "career-fairfield.webp": ("fotos-candidatas/fairfield-mejor-jugadora-2022.jpg", (427, 0, 1493, 1333), 800, False),
    "career-uconn.webp": ("fotos-candidatas/uconn-vs-marquette.jpg", (432, 0, 1296, 1080), 800, False),
    "career-dallas.webp": ("fotos-candidatas/dallas-wnba-retrato.png", (216, 0, 824, 760), 608, True),
    "career-jairis.webp": ("fotos-candidatas/jairis-entrevista-2024-gigantes.jpg", (318, 0, 734, 520), 416, False),
}

for name, (src, box, width, alpha) in CROPS.items():
    im = Image.open(os.path.join(SRC, src)).convert("RGBA" if alpha else "RGB").crop(box)
    if im.width != width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    im.save(os.path.join(OUT, name), "WEBP", quality=84, method=6)
    print(f"{name}: {im.width}x{im.height}, {os.path.getsize(os.path.join(OUT, name)) // 1024} KB")

# Studio portrait: shrink (the original is 30 megapixels), cut out, keep the top 4:5.
with tempfile.TemporaryDirectory() as tmp:
    small = os.path.join(tmp, "portrait.png")
    Image.open(os.path.join(SRC, "fotos-candidatas", "jairis-club-oficial.jpg")).convert("RGB").resize((1800, 2700), Image.LANCZOS).save(small)
    subprocess.run(
        [sys.executable, os.path.join(ROOT, "scripts", "cutout.py"), small, os.path.join(tmp, "full.webp"),
         "--crop", "0,0,1800,2250", "--variants", "1280:" + os.path.join(OUT, "about-portrait.webp"), "--quality", "86"],
        check=True,
    )
