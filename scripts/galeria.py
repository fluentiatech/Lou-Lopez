"""Build the gallery: python scripts/galeria.py

Reads the photos listed below from design/fotos-galeria/, writes a thumbnail and a large
version of each to img/galeria/, and rewrites the tiles and lightboxes in index.html
between the "galeria:inicio" and "galeria:fin" comments. To change the gallery, edit
PHOTOS and run it again.

Needs: pip install pillow
"""
import io
import os
import re

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "design", "fotos-galeria")
OUT = os.path.join(ROOT, "img", "galeria")

TEAMS = {"jairis": "Hozono Global Jairis", "uconn": "UConn", "fairfield": "Fairfield"}

# source file, team, caption, credit, tile ("", "big" or "tall"), focus (CSS object-position), alt text
PHOTOS = [
    ("jairis-renovacion-2026-gigantes.jpg", "jairis", "Hozono Global Jairis", "Gigantes del Basket", "big", "60% 40%",
     "Lou López smiling on court in the black Hozono Global Jairis kit"),
    ("jairis-copa-2025-IMG_7088.jpg", "jairis", "Copa de la Reina final · 2025", "Campo Atrás", "tall", "50% 45%",
     "Lou López, number 19, seen from behind as she goes up with the ball among defenders in the Copa de la Reina final"),
    ("jairis-copa-2025-gigantes.jpg", "jairis", "Copa de la Reina champions · 2025", "Gigantes del Basket", "", "50% 60%",
     "The Hozono Global Jairis squad lifting the 2025 Copa de la Reina trophy on court under falling confetti"),
    ("jairis-copa-2025-IMG_6933.jpg", "jairis", "Copa de la Reina final · 2025", "Campo Atrás", "tall", "60% 42%",
     "Lou López dribbling up the floor next to a teammate in the Copa de la Reina final"),
    ("jairis-entrevista-2025-gigantes.jpg", "jairis", "Hozono Global Jairis", "Gigantes del Basket", "", "50% 35%",
     "Lou López laughing during a warm-up with Hozono Global Jairis"),
    ("jairis-feb-2024-b.jpg", "jairis", "Liga Femenina Endesa · 2024", "FEB", "", "75% 40%",
     "Lou López looking across the court during a home game in Alcantarilla"),
    ("jairis-copa-2025-IMG_6687.jpg", "jairis", "Copa de la Reina final · 2025", "Campo Atrás", "", "35% 50%",
     "Lou López, number 19, watching a team-mate's shot from the wing in the Copa de la Reina final"),
    ("uconn-accion.jpg", "uconn", "UConn · 2022–23", "UConn Athletics", "big", "45% 50%",
     "Lou López driving to the basket for UConn against Duke"),
    ("uconn-vs-marquette.jpg", "uconn", "UConn · 2022–23", "UConn Athletics", "tall", "45% 40%",
     "Lou López protecting the ball from a Marquette defender"),
    ("uconn-villanova.jpg", "uconn", "UConn · 2022–23", "UConn Athletics", "", "50% 45%",
     "Lou López, number 11, with her arms out wide at Villanova"),
    ("uconn-con-griffin.jpg", "uconn", "UConn · 2022–23", "UConn Athletics", "", "72% 40%",
     "Lou López slapping hands with a UConn teammate"),
    ("uconn-con-juhasz.jpg", "uconn", "UConn · 2022–23", "UConn Athletics", "", "58% 40%",
     "Lou López talking with two UConn teammates during a game"),
    ("fairfield-2022-01-10.jpg", "fairfield", "Fairfield · 2021–22", "Fairfield Athletics", "big", "52% 50%",
     "Lou López shooting over a defender for Fairfield at Indiana"),
    ("fairfield-2022-03-19.jpg", "fairfield", "NCAA Tournament · 2022", "Fairfield Athletics", "", "50% 45%",
     "Lou López going up for a shot against Texas in the NCAA Tournament"),
    ("fairfield-mejor-jugadora-2022.jpg", "fairfield", "Fairfield · 2021–22", "Fairfield Athletics", "", "48% 40%",
     "Lou López celebrating on court with her fists clenched"),
    ("fairfield-2022-03-07.jpg", "fairfield", "Fairfield · 2021–22", "Fairfield Athletics", "", "55% 45%",
     "Lou López finishing a layup for Fairfield"),
    ("fairfield-2022-02-26.jpg", "fairfield", "Fairfield · 2021–22", "Fairfield Athletics", "", "45% 40%",
     "Lou López rising for a jump shot for Fairfield"),
    ("fairfield-2022-02-12.jpg", "fairfield", "Fairfield · 2021–22", "Fairfield Athletics", "", "62% 45%",
     "Lou López driving past a Siena defender"),
    ("fairfield-2021-12-18.jpg", "fairfield", "Fairfield · 2021–22", "Fairfield Athletics", "", "50% 40%",
     "Lou López shooting a jumper for Fairfield"),
    ("fairfield-2021-03-12.jpg", "fairfield", "Fairfield · 2020–21", "Fairfield Athletics", "", "35% 45%",
     "Lou López dribbling against a Marist defender"),
]

ARROW = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M2 12h20M15 5l7 7-7 7" /></svg>'
CLOSE = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M4 4l16 16M20 4 4 20" /></svg>'


def save(im, path, width):
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    im.save(path, "WEBP", quality=82, method=6)
    return im.size


os.makedirs(OUT, exist_ok=True)
tiles, boxes = [], []
n = len(PHOTOS)
for i, (src, team, caption, credit, kind, focus, alt) in enumerate(PHOTOS, 1):
    im = Image.open(os.path.join(SRC, src)).convert("RGB")
    portrait = im.height > im.width
    tw, th = save(im, os.path.join(OUT, f"{i:02d}-t.webp"), 1280 if kind == "big" else (700 if portrait else 900))
    lw, lh = save(im, os.path.join(OUT, f"{i:02d}.webp"), 1280 if portrait else 1920)
    cls = "tile" + (f" tile--{kind}" if kind else "")
    lead = "" if caption.startswith(TEAMS[team]) else f"<strong>{TEAMS[team]}</strong>"  # no "UConn UConn"
    prev_id, next_id = f"foto-{(i - 2) % n + 1:02d}", f"foto-{i % n + 1:02d}"
    tiles.append(f"""            <a class="{cls} reveal" id="t-{i:02d}" href="#foto-{i:02d}" data-team="{team}">
              <img src="img/galeria/{i:02d}-t.webp" alt="{alt}" width="{tw}" height="{th}" loading="lazy" style="object-position: {focus}" />
              <span class="tile__label">{caption}</span>
            </a>
""")
    # Closing goes back to the tile of the photo being shown, so the page ends up where the visitor is looking.
    boxes.append(f"""        <div class="lightbox" id="foto-{i:02d}" role="dialog" aria-label="Photo {i} of {n}">
          <figure>
            <img src="img/galeria/{i:02d}.webp" alt="{alt}" width="{lw}" height="{lh}" loading="lazy" />
            <figcaption>{lead}{caption} <span>Photo: {credit}</span></figcaption>
          </figure>
          <a class="lightbox__nav lightbox__nav--prev" href="#{prev_id}" aria-label="Previous photo">{ARROW}</a>
          <a class="lightbox__nav lightbox__nav--next" href="#{next_id}" aria-label="Next photo">{ARROW}</a>
          <a class="lightbox__close" href="#t-{i:02d}" aria-label="Close">{CLOSE}</a>
        </div>
""")

block = ("<!-- galeria:inicio (generated by scripts/galeria.py) -->\n"
         '          <div class="gallery__grid">\n' + "".join(tiles) + "          </div>\n"
         "        </div>\n\n" + "".join(boxes) +
         "        <!-- galeria:fin -->")

p = os.path.join(ROOT, "index.html")
html = io.open(p, encoding="utf-8").read()
new, count = re.subn(r"<!-- galeria:inicio.*?<!-- galeria:fin -->", lambda m: block, html, flags=re.S)
assert count == 1, "gallery markers not found in index.html"
io.open(p, "w", encoding="utf-8", newline="\n").write(new)
size = sum(os.path.getsize(os.path.join(OUT, f)) for f in os.listdir(OUT)) // 1024
print(f"{n} photos, {size} KB in img/galeria/")
