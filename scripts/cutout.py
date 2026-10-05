"""Cut a studio photo shot on a pure white backdrop out to a transparent WebP.

The hero image is built in two steps:

1. scripts/mejorar_foto_colab.ipynb (Google Colab, GPU): Real-ESRGAN turns
   design/lou-hero-original.jpg into design/lou-hero-x2.png (twice the size, no JPEG artefacts).
2. This script cuts the figure out and writes the three sizes the page uses:

    python scripts/cutout.py design/lou-hero-x2.png img/lou-hero-2608.webp --scale 2         --mix design/lou-hero-original.jpg:0.15 --hair-box 1480,0,2560,960 --crop 800,10,3408,2640         --variants 1956:img/lou-hero-1956.webp,1304:img/lou-hero.webp

Needs: pip install rembg opencv-python numpy pillow

u2net gives the silhouette; the edges are then rebuilt from the photo itself, using the
fact that every edge pixel is a mix of the subject and pure white. That keeps skin, hair
and the navy trim crisp and removes the white fringe a plain mask leaves behind.
"""
import argparse

import cv2
import numpy as np
from PIL import Image
from rembg import new_session, remove


def odd(n):
    return int(round(n)) | 1


def ellipse(n):
    return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (odd(n), odd(n)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--hair-box", help="x0,y0,x1,y1 in source pixels: area where loose dark hair crosses the backdrop")
    ap.add_argument("--scale", type=float, default=1, help="size of src relative to the original photo (2 for the upscaled one)")
    ap.add_argument("--mix", help="path:weight, blend a little of another version (e.g. the untouched original) back in so skin keeps some texture")
    ap.add_argument("--crop", help="x0,y0,x1,y1 in source pixels; default is the figure's bounding box plus --margin")
    ap.add_argument("--variants", help="width:path,... smaller copies to save next to dst")
    ap.add_argument("--margin", type=int, default=6)
    ap.add_argument("--quality", type=int, default=90)
    args = ap.parse_args()
    k = args.scale

    src = Image.open(args.src).convert("RGB")
    if args.mix:
        path, weight = args.mix.rsplit(":", 1)
        src = Image.blend(src, Image.open(path).convert("RGB").resize(src.size, Image.BICUBIC), float(weight))
    rgb = np.asarray(src).astype(np.float32)
    m = np.asarray(remove(src, session=new_session("u2net"), only_mask=True).convert("L")).astype(np.float32) / 255

    core = cv2.erode((m > 0.92).astype(np.uint8), ellipse(7 * k))
    near = cv2.dilate((m > 0.3).astype(np.uint8), ellipse(41 * k))
    band = (near == 1) & (core == 0)

    # Local foreground estimate: colour of the nearest surely-opaque pixel.
    _, labels = cv2.distanceTransformWithLabels(1 - core, cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
    ys, xs = np.nonzero(core)
    lut = np.zeros((labels.max() + 1, 2), np.int32)
    lut[labels[ys, xs]] = np.stack([ys, xs], 1)
    nn = lut[labels]
    fg = cv2.blur(rgb[nn[..., 0], nn[..., 1]], (odd(7 * k), odd(7 * k)))

    # C = a*F + (1-a)*255  ->  least-squares alpha per pixel.
    num = 255.0 - rgb
    den = 255.0 - fg
    den_len = np.sqrt((den * den).sum(-1))
    a_col = np.clip((num * den).sum(-1) / np.maximum(den_len**2, 1e-3), 0, 1)
    conf = np.clip((den_len - 45) / 110, 0, 1)  # 0 where the subject itself is white (kit, socks)
    t = np.clip((m - 0.32) / 0.36, 0, 1)
    a_model = t * t * (3 - 2 * t)
    a = np.where(band, conf * a_col + (1 - conf) * a_model, core.astype(np.float32))

    if args.hair_box:
        # Loose strands: where an edge pixel is a neutral grey rather than a skin tint,
        # treat it as dark hair over white instead of whatever opaque pixel is nearest.
        x0, y0, x1, y1 = map(int, args.hair_box.split(","))
        box = np.zeros(a.shape, bool)
        box[y0:y1, x0:x1] = True
        lum = rgb.mean(-1)
        hair = np.median(rgb[box & (core == 1) & (lum < 80)], axis=0)
        dh = 255.0 - hair
        num_len = np.sqrt((num * num).sum(-1))
        cos_hair = (num * dh).sum(-1) / np.maximum(num_len * np.linalg.norm(dh), 1e-3)
        cos_near = (num * den).sum(-1) / np.maximum(num_len * den_len, 1e-3)
        # conf > 0.5 keeps this away from the edges of the white kit.
        as_hair = box & band & (conf > 0.5) & (num_len > 10) & (cos_hair > cos_near)
        a = np.where(as_hair, np.clip((num * dh).sum(-1) / (dh * dh).sum(), 0, 1), a)
        fg = np.where(as_hair[..., None], hair, fg)

    a[near == 0] = 0
    a = np.clip((a - 0.05) / 0.90, 0, 1)

    # Drop specks that are not attached to the figure.
    _, lab, stats, _ = cv2.connectedComponentsWithStats((a > 0.08).astype(np.uint8), 8)
    a[lab != 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])] = 0

    # Fill holes. White kit next to hair or skin reads as "backdrop" to the colour test,
    # but the backdrop cannot be somewhere it has no way in to: any transparent patch
    # sealed inside the figure, where the silhouette model also sees the subject, is kit.
    solid = cv2.morphologyEx((a >= 0.5).astype(np.uint8), cv2.MORPH_CLOSE, ellipse(3 * k))
    n, lab = cv2.connectedComponents(1 - solid, connectivity=4)
    edge = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    outside = np.isin(lab, edge) & (solid == 0)
    holes = np.zeros(a.shape, np.uint8)
    for i in set(range(1, n)) - set(edge.tolist()):
        if m[lab == i].mean() > 0.5:
            holes[lab == i] = 1
    a[(cv2.dilate(holes, ellipse(9 * k)) == 1) & ~outside] = 1

    # Remove the white the backdrop mixed into the edge pixels.
    a3 = np.clip(a, 1e-3, 1)[..., None]
    out = np.clip((rgb - (1 - a3) * 255.0) / a3, 0, 255)
    out = np.where(a[..., None] < 0.15, fg, out)

    if args.crop:
        crop = tuple(map(int, args.crop.split(",")))
    else:
        ys, xs = np.where(a > 0.03)
        h, w = a.shape
        pad = int(args.margin * k)
        crop = (max(xs.min() - pad, 0), max(ys.min() - pad, 0), min(xs.max() + 1 + pad, w), min(ys.max() + 1 + pad, h))
    img = Image.fromarray(np.dstack([out, a * 255]).astype(np.uint8), "RGBA").crop(crop)
    targets = [(img.width, args.dst)] + [(int(v.split(":")[0]), v.split(":", 1)[1]) for v in (args.variants or "").split(",") if v]
    for width, path in targets:
        im = img if width == img.width else img.resize((width, round(img.height * width / img.width)), Image.LANCZOS)
        im.save(path, "WEBP", quality=args.quality, method=6, alpha_quality=100)
        print(f"{path}: {im.width}x{im.height}")
    print("crop box in source =", crop)


if __name__ == "__main__":
    main()
