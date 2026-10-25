#!/usr/bin/env python3
"""Genera todas las texturas del addon Berrocal.

Uso:
    python3 tools/generate_textures.py

Requiere Pillow:  pip install pillow

El script es determinista (usa semillas fijas), así que volver a ejecutarlo
produce exactamente los mismos PNG. Las texturas generadas se guardan en
Berrocal_RP/textures/ y los iconos de pack en cada pack.
"""

from __future__ import annotations

import os
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
RP = ROOT / "Berrocal_RP"
BP = ROOT / "Berrocal_BP"
BLOCK_DIR = RP / "textures" / "blocks"
ITEM_DIR = RP / "textures" / "items"
DOCS = ROOT / "docs"

T = (0, 0, 0, 0)  # transparente


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def canvas(size: int = 16) -> Image.Image:
    return Image.new("RGBA", (size, size), T)


def shade(color, factor: float):
    """Aclara (factor > 1) u oscurece (factor < 1) un color RGBA."""
    r, g, b, a = color
    return (
        max(0, min(255, int(r * factor))),
        max(0, min(255, int(g * factor))),
        max(0, min(255, int(b * factor))),
        a,
    )


def mix(c1, c2, t: float):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(4))


# ---------------------------------------------------------------------------
# Paletas (piedra de granito / berilo)
# ---------------------------------------------------------------------------

GRANITE_BASE = [(150, 104, 86, 255), (145, 99, 82, 255), (156, 110, 91, 255)]
GRANITE_DARK = [(112, 74, 60, 255), (100, 66, 54, 255), (122, 82, 66, 255)]
GRANITE_MID = [(134, 90, 74, 255), (140, 95, 79, 255)]
GRANITE_LIGHT = [(177, 132, 113, 255), (186, 142, 121, 255)]
GRANITE_PALE = [(208, 178, 164, 255), (216, 188, 174, 255)]
GRANITE_WHITE = [(234, 219, 209, 255)]

GEM_DARK = (22, 92, 58, 255)
GEM_MID = (38, 141, 88, 255)
GEM = (54, 178, 111, 255)
GEM_LIGHT = (110, 230, 158, 255)
GEM_PALE = (186, 255, 214, 255)

MOSS_DARK = (68, 94, 44, 255)
MOSS = (92, 126, 58, 255)
MOSS_LIGHT = (124, 158, 78, 255)
MOSS_PALE = (150, 184, 100, 255)

WOOD_DARK = (74, 48, 28, 255)
WOOD = (110, 74, 42, 255)
WOOD_LIGHT = (146, 102, 58, 255)


# ---------------------------------------------------------------------------
# Bloques
# ---------------------------------------------------------------------------

def granite_field(seed: int, size: int = 16) -> Image.Image:
    """Textura de granito rugoso, con motas tipo piedra natural."""
    rnd = random.Random(seed)
    img = canvas(size)
    px = img.load()
    for y in range(size):
        for x in range(size):
            n = rnd.random()
            if n < 0.44:
                color = rnd.choice(GRANITE_BASE)
            elif n < 0.66:
                color = rnd.choice(GRANITE_MID)
            elif n < 0.84:
                color = rnd.choice(GRANITE_DARK)
            elif n < 0.93:
                color = rnd.choice(GRANITE_LIGHT)
            elif n < 0.98:
                color = rnd.choice(GRANITE_PALE)
            else:
                color = rnd.choice(GRANITE_WHITE)
            px[x, y] = color

    # Pequeños grumos de 2-3 píxeles para que no se vea "ruido plano".
    for _ in range(9):
        x = rnd.randrange(size)
        y = rnd.randrange(size)
        color = rnd.choice(GRANITE_DARK + GRANITE_LIGHT + GRANITE_PALE)
        px[x, y] = color
        if rnd.random() < 0.6:
            px[(x + 1) % size, y] = shade(color, 0.94)
    return img


def tex_berrocal_block() -> Image.Image:
    return granite_field(seed=1261)


def tex_mossy_berrocal() -> Image.Image:
    rnd = random.Random(77)
    img = granite_field(seed=4102)
    px = img.load()
    size = img.width

    # Manchas de musgo irregular.
    for _ in range(7):
        cx = rnd.uniform(0, size)
        cy = rnd.uniform(0, size)
        radius = rnd.uniform(1.2, 3.0)
        for y in range(size):
            for x in range(size):
                dx = min(abs(x - cx), size - abs(x - cx))
                dy = min(abs(y - cy), size - abs(y - cy))
                dist = (dx * dx + dy * dy) ** 0.5
                if dist <= radius:
                    if dist > radius - 0.9:
                        px[x, y] = rnd.choice([MOSS_DARK, MOSS])
                    else:
                        px[x, y] = rnd.choice([MOSS, MOSS_LIGHT, MOSS_LIGHT, MOSS_PALE])
    # Motas verdes sueltas.
    for _ in range(22):
        px[rnd.randrange(size), rnd.randrange(size)] = rnd.choice([MOSS, MOSS_LIGHT, MOSS_DARK])
    return img


def tex_polished_berrocal() -> Image.Image:
    """Berrocal pulido: superficie lisa, clara y con junta marcada."""
    rnd = random.Random(915)
    size = 16
    img = canvas(size)
    px = img.load()
    smooth = [
        (196, 156, 136, 255),
        (190, 150, 130, 255),
        (202, 162, 141, 255),
        (186, 145, 126, 255),
    ]
    for y in range(size):
        for x in range(size):
            px[x, y] = rnd.choice(smooth)

    # Vetas suaves (líneas casi horizontales) típicas de la piedra pulida.
    for _ in range(3):
        y = rnd.randrange(2, size - 2)
        for x in range(2, size - 2):
            if rnd.random() < 0.7:
                px[x, y] = shade(px[x, y], 0.93)
    # Motas finas.
    for _ in range(16):
        x, y = rnd.randrange(2, size - 2), rnd.randrange(2, size - 2)
        px[x, y] = rnd.choice([GRANITE_PALE[0], GRANITE_LIGHT[0], shade(px[x, y], 0.9)])

    # Junta perimetral oscura.
    joint = (156, 114, 96, 255)
    joint_dark = (134, 96, 80, 255)
    for i in range(size):
        px[i, 0] = joint_dark
        px[0, i] = joint_dark
        px[i, size - 1] = joint
        px[size - 1, i] = joint
    # Bisel: filo claro arriba/izquierda, sombra abajo/derecha.
    for i in range(1, size - 1):
        px[i, 1] = shade(px[i, 1], 1.07)
        px[1, i] = shade(px[1, i], 1.04)
        px[i, size - 2] = shade(px[i, size - 2], 0.92)
        px[size - 2, i] = shade(px[size - 2, i], 0.92)
    return img


def tex_berrocal_bricks() -> Image.Image:
    rnd = random.Random(2024)
    size = 16
    img = canvas(size)
    px = img.load()
    mortar = (138, 96, 78, 255)
    brick_colors = [(160, 115, 96, 255), (170, 124, 104, 255), (152, 108, 90, 255)]

    for y in range(size):
        for x in range(size):
            row = y // 4
            offset = 0 if row % 2 == 0 else 4
            is_mortar_h = (y % 4 == 3)
            is_mortar_v = ((x + offset) % 8 == 7)
            if is_mortar_h or is_mortar_v:
                px[x, y] = mortar
            else:
                px[x, y] = rnd.choice(brick_colors)

    # Textura moteada dentro de cada ladrillo.
    for _ in range(60):
        x = rnd.randrange(size)
        y = rnd.randrange(size)
        if px[x, y] != mortar:
            px[x, y] = rnd.choice(
                [shade(px[x, y], 0.9), shade(px[x, y], 1.1), GRANITE_WHITE[0], rnd.choice(GRANITE_DARK)]
            )
    # Luz superior de cada ladrillo.
    for y in range(size):
        if y % 4 == 0:
            for x in range(size):
                if px[x, y] != mortar:
                    px[x, y] = shade(px[x, y], 1.08)
    return img


def tex_berrocal_ore() -> Image.Image:
    rnd = random.Random(555)
    img = granite_field(seed=3311)
    px = img.load()
    size = img.width

    def crystal(cx: int, cy: int) -> None:
        shape = [(0, 0), (1, 0), (0, 1), (1, 1)]
        if rnd.random() < 0.5:
            shape = [(0, 0), (1, 0), (2, 0), (1, 1)]
        for i, (dx, dy) in enumerate(shape):
            x, y = (cx + dx) % size, (cy + dy) % size
            if i == 0:
                px[x, y] = GEM_LIGHT
            elif i == len(shape) - 1:
                px[x, y] = GEM_DARK
            else:
                px[x, y] = GEM
        # Chispa brillante.
        px[(cx + 1) % size, (cy + 1) % size] = GEM_PALE

    for _ in range(5):
        crystal(rnd.randrange(size), rnd.randrange(size))
    # Cristales de un solo píxel.
    for _ in range(14):
        px[rnd.randrange(size), rnd.randrange(size)] = rnd.choice([GEM, GEM_LIGHT, GEM_DARK])
    return img


def tex_berilo_block() -> Image.Image:
    """Bloque de gemas: 4 gemas grandes talladas con ranuras oscuras."""
    img = canvas(16)
    px = img.load()
    grout = (16, 70, 44, 255)
    for y in range(16):
        for x in range(16):
            px[x, y] = grout

    cells = [(1, 1), (9, 1), (1, 9), (9, 9)]
    for idx, (ox, oy) in enumerate(cells):
        # Gema de 6x6 dentro de una celda de 6x6 + borde.
        for y in range(6):
            for x in range(6):
                # Octógono: se recortan las esquinas.
                if (x in (0, 5)) and (y in (0, 5)):
                    continue
                gx, gy = ox + x, oy + y
                if x + y <= 2 or (5 - x) + y <= 2 or x + (5 - y) <= 2 or (5 - x) + (5 - y) <= 2:
                    px[gx, gy] = GEM_DARK
                elif (x + y) % 5 == 0:
                    px[gx, gy] = GEM_LIGHT
                else:
                    px[gx, gy] = GEM if (x + y + idx) % 3 else GEM_MID
        # Faceta superior de la gema.
        px[ox + 2, oy + 1] = GEM_LIGHT
        px[ox + 3, oy + 1] = GEM_PALE
        px[ox + 1, oy + 2] = GEM_LIGHT
        px[ox + 4, oy + 4] = GEM_DARK
    return img


def tex_berrocal_lamp() -> Image.Image:
    """Lámpara: marco de berrocal pulido con núcleo de berilo luminoso."""
    img = canvas(16)
    px = img.load()
    frame_light = (176, 132, 113, 255)
    frame = (150, 108, 92, 255)
    frame_dark = (118, 82, 68, 255)

    for y in range(16):
        for x in range(16):
            px[x, y] = frame if (x in (0, 15) or y in (0, 15)) else frame_light
    for i in range(1, 15):
        px[i, 1] = frame_light
        px[i, 14] = frame_dark
        px[1, i] = frame_light
        px[14, i] = frame_dark
    for corner in ((1, 1), (14, 1), (1, 14), (14, 14)):
        px[corner] = frame

    # Núcleo luminoso 10x10.
    for y in range(3, 13):
        for x in range(3, 13):
            dist = max(abs(x - 7.5), abs(y - 7.5))
            if dist > 4.0:
                px[x, y] = GEM_DARK
            elif dist > 3.0:
                px[x, y] = GEM
            elif dist > 2.0:
                px[x, y] = GEM_LIGHT
            else:
                px[x, y] = GEM_PALE
    # Gema central + destellos.
    for dx, dy in ((0, 0), (1, 0), (0, 1), (-1, 0), (0, -1), (1, 1)):
        px[7 + dx, 7 + dy] = GEM_LIGHT if (dx + dy) % 2 else GEM_PALE
    px[7, 7] = (255, 255, 240, 255)
    for x, y in ((4, 4), (11, 4), (4, 11), (11, 11)):
        px[x, y] = (255, 255, 255, 255)
    return img


# ---------------------------------------------------------------------------
# Objetos
# ---------------------------------------------------------------------------

def tex_berilo() -> Image.Image:
    """Gema de berilo tallada en facetas."""
    img = canvas(16)
    d = ImageDraw.Draw(img)
    # Contorno.
    outline = [
        (7, 1), (9, 1), (13, 5), (13, 8), (9, 14), (7, 14), (3, 8), (3, 5),
    ]
    d.polygon(outline, fill=GEM_DARK)
    body = [
        (8, 2), (9, 2), (12, 5), (12, 8), (8, 13), (7, 13), (4, 8), (4, 5),
    ]
    d.polygon(body, fill=GEM)
    # Faceta superior clara.
    d.polygon([(8, 2), (9, 2), (12, 5), (6, 5), (4, 5)], fill=GEM_LIGHT)
    # Faceta inferior/derecha.
    d.polygon([(12, 5), (12, 8), (8, 13), (8, 9)], fill=GEM_MID)
    # Brillo.
    d.point([(6, 6), (7, 6), (6, 7), (5, 7)], fill=GEM_PALE)
    px = img.load()
    px[9, 3] = GEM_PALE
    px[8, 4] = (240, 255, 246, 255)
    px[7, 10] = GEM_DARK
    px[6, 11] = GEM_DARK
    return img


def tex_berilo_pickaxe() -> Image.Image:
    img = canvas(16)
    d = ImageDraw.Draw(img)

    # Mango de madera en diagonal (de abajo-izquierda hacia arriba-derecha).
    d.line([(2, 14), (11, 5)], fill=WOOD_DARK, width=3)
    d.line([(2, 13), (10, 5)], fill=WOOD, width=2)
    d.line([(2, 13), (9, 6)], fill=WOOD_LIGHT, width=1)

    # Cabeza de berilo en forma de arco.
    head = [(3, 7), (4, 4), (7, 2), (10, 2), (13, 4), (14, 7)]
    d.line(head, fill=GEM_DARK, width=4, joint="curve")
    d.line(head, fill=GEM_MID, width=2, joint="curve")
    d.line([(4, 5), (7, 3), (10, 3), (12, 4)], fill=GEM, width=2, joint="curve")
    d.line([(5, 4), (7, 3), (9, 3)], fill=GEM_LIGHT, width=1, joint="curve")

    # Puntas hacia abajo de la cabeza.
    d.line([(3, 7), (3, 9)], fill=GEM_DARK, width=2)
    d.line([(14, 7), (14, 9)], fill=GEM_DARK, width=2)

    # Destellos.
    px = img.load()
    px[6, 3] = GEM_PALE
    px[10, 3] = GEM_LIGHT
    px[13, 5] = GEM_LIGHT
    px[3, 4] = GEM
    return img


def tex_berilo_sword() -> Image.Image:
    img = canvas(16)
    d = ImageDraw.Draw(img)

    # Hoja diagonal con filo claro.
    d.line([(5, 10), (13, 2)], fill=GEM_DARK, width=4)
    d.line([(5, 10), (12, 3)], fill=GEM_MID, width=2)
    d.line([(5, 9), (11, 3)], fill=GEM, width=1)
    d.line([(4, 9), (10, 3)], fill=GEM_LIGHT, width=1)
    d.point([(13, 2)], fill=GEM_PALE)

    # Guarda (cruceta).
    d.line([(2, 9), (6, 13)], fill=GEM_DARK, width=2)
    d.line([(3, 9), (6, 12)], fill=GEM_MID, width=1)

    # Mango.
    d.line([(3, 12), (1, 14)], fill=WOOD_DARK, width=2)
    d.line([(2, 12), (1, 13)], fill=WOOD, width=1)

    px = img.load()
    px[9, 4] = GEM_PALE
    px[7, 6] = GEM_PALE
    px[11, 4] = GEM_LIGHT
    return img


# ---------------------------------------------------------------------------
# Iconos de pack
# ---------------------------------------------------------------------------

def load_font(size: int):
    for name in ("DejaVuSans-Bold.ttf", "DejaVuSans.ttf", "Arial Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # Pillow < 10
        return ImageFont.load_default()


def _iso_cube(texture: Image.Image, edge: int = 76) -> Image.Image:
    """Dibuja un cubo isométrico 2:1 con la textura dada en sus 3 caras."""
    tex = texture.convert("RGBA")
    ts = tex.width
    px = tex.load()

    w = edge
    h = edge / 2.0
    cx, cy = edge * 1.0, edge * 0.5      # centro de la cara superior

    Lx, Ly = cx - w, cy                  # vértice izquierdo
    Rx, Ry = cx + w, cy                  # vértice derecho
    Tx, Ty = cx, cy - h                  # vértice superior
    Bx, By = cx, cy + h                  # vértice inferior (del rombo superior)
    H = float(edge)

    width = int(2 * w) + 2
    height = int(2 * h + H) + 2
    out = Image.new("RGBA", (width, height), T)
    opx = out.load()
    off_x, off_y = 1, 1

    for y in range(height):
        for x in range(width):
            dx = x - off_x
            dy = y - off_y
            color = None

            # Cara superior (rombo).
            if abs(dx - cx) / w + abs(dy - cy) / h <= 1.0:
                u = (dx - cx) / w
                v = (dy - cy) / h
                uu = (u + v) / 2.0 + 0.5
                vv = (v - u) / 2.0 + 0.5
                color = px[min(ts - 1, max(0, int(uu * ts))), min(ts - 1, max(0, int(vv * ts)))]
                color = shade(color, 1.12)
            else:
                # Cara izquierda.
                if Lx <= dx <= Bx and By <= dy <= By + H:
                    uu = (dx - Lx) / w
                    vv = (dy - Ly - uu * h) / H
                    if 0 <= uu <= 1 and 0 <= vv <= 1:
                        color = shade(px[min(ts - 1, int(uu * ts)), min(ts - 1, int(vv * ts))], 0.62)
                # Cara derecha.
                if color is None and Bx <= dx <= Rx and By <= dy <= By + H:
                    uu = (dx - Bx) / w
                    vv = (dy - By) / H
                    if 0 <= uu <= 1 and 0 <= vv <= 1:
                        uu2 = 1.0 - vv * 0  # mantiene el mapeo simple
                        color = shade(px[min(ts - 1, int(uu * ts)), min(ts - 1, int(vv * ts))], 0.82)

            if color is not None:
                opx[x, y] = color
    return out


def make_pack_icon(badge: str) -> Image.Image:
    size = 256
    img = Image.new("RGBA", (size, size), (24, 30, 28, 255))
    d = ImageDraw.Draw(img)

    for y in range(size):
        t = y / (size - 1)
        d.line(
            [(0, y), (size, y)],
            fill=(int(30 + 26 * t), int(43 + 34 * t), int(39 + 28 * t), 255),
        )
    # Halo detrás del cubo.
    glow = Image.new("RGBA", (size, size), T)
    gd = ImageDraw.Draw(glow)
    gd.ellipse([(38, 46), (218, 190)], fill=(90, 210, 150, 60))
    glow = glow.filter(ImageFilter.GaussianBlur(18))
    img.alpha_composite(glow)

    cube = _iso_cube(tex_berrocal_block(), 74)
    img.alpha_composite(cube, (126 - cube.width // 2, 24))

    # Gema flotante.
    gem = tex_berilo().resize((72, 72), Image.NEAREST)
    img.alpha_composite(gem, (156, 30))

    # Placa de título.
    d.rounded_rectangle([(16, 196), (240, 240)], 10, fill=(14, 20, 17, 210))
    font = load_font(26)
    text = "BERROCAL"
    bbox = d.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    d.text(((size - tw) / 2, 203), text, font=font, fill=(226, 255, 238, 255))

    if badge:
        bfont = load_font(18)
        bb = d.textbbox((0, 0), badge, font=bfont)
        bw = bb[2] - bb[0] + 12
        d.rounded_rectangle([(size - bw - 12, 12), (size - 12, 40)], 8, fill=(48, 160, 108, 235))
        d.text((size - bw - 6, 17), badge, font=bfont, fill=(240, 255, 246, 255))
    return img


# ---------------------------------------------------------------------------
# Hoja de previsualización para el README
# ---------------------------------------------------------------------------

def make_preview(blocks: dict[str, Image.Image], items: dict[str, Image.Image]) -> Image.Image:
    width, height = 1080, 630
    img = Image.new("RGBA", (width, height), (22, 27, 25, 255))
    d = ImageDraw.Draw(img)
    for y in range(height):
        t = y / (height - 1)
        d.line([(0, y), (width, y)], fill=(int(24 + 14 * t), int(31 + 20 * t), int(28 + 18 * t), 255))

    title_font = load_font(46)
    sub_font = load_font(21)
    label_font = load_font(17)

    def centered(text: str, font, y: int, fill) -> None:
        bb = d.textbbox((0, 0), text, font=font)
        d.text(((width - (bb[2] - bb[0])) / 2, y), text, font=font, fill=fill)

    centered("BERROCAL", title_font, 26, (190, 255, 216, 255))
    centered(
        "Addon para Minecraft Bedrock · bloques, mena de berilo, gemas y herramientas",
        sub_font,
        86,
        (212, 222, 217, 255),
    )

    zoom = 5
    cell = 16 * zoom
    gap = 30
    padding = 10

    def row(title_text: str, entries: dict[str, Image.Image], top: int) -> int:
        d.text((54, top), title_text, font=sub_font, fill=(150, 240, 190, 255))
        total = len(entries) * cell + (len(entries) - 1) * gap
        x = (width - total) / 2
        y = top + 34
        for name, tex in entries.items():
            frame = Image.new("RGBA", (cell + padding * 2, cell + padding * 2), (42, 50, 46, 255))
            frame.alpha_composite(
                tex.convert("RGBA").resize((cell, cell), Image.NEAREST), (padding, padding)
            )
            img.alpha_composite(frame, (int(x), y))
            d.rectangle(
                [(x, y), (x + cell + padding * 2, y + cell + padding * 2)],
                outline=(78, 92, 85, 255),
            )
            label = name.replace("_", " ").title()
            bb = d.textbbox((0, 0), label, font=label_font)
            lw = bb[2] - bb[0]
            if lw <= cell + padding * 2:
                d.text((x + (cell + padding * 2 - lw) / 2, y + cell + padding * 2 + 9),
                       label, font=label_font, fill=(206, 216, 211, 255))
            else:
                words = label.split(" ")
                line1, line2 = " ".join(words[:-1]), words[-1]
                for i, part in enumerate((line1, line2)):
                    bb = d.textbbox((0, 0), part, font=label_font)
                    pw = bb[2] - bb[0]
                    d.text((x + (cell + padding * 2 - pw) / 2,
                            y + cell + padding * 2 + 6 + i * 19),
                           part, font=label_font, fill=(206, 216, 211, 255))
            x += cell + gap + padding * 2
        return y + cell + padding * 2 + 84

    next_top = row("BLOQUES", blocks, 130)
    row("OBJETOS", items, next_top)

    centered(
        "Texturas generadas con: python3 tools/generate_textures.py",
        label_font,
        height - 44,
        (140, 152, 146, 255),
    )
    return img


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    for directory in (BLOCK_DIR, ITEM_DIR, DOCS, BP, RP):
        directory.mkdir(parents=True, exist_ok=True)

    blocks = {
        "berrocal_block": tex_berrocal_block(),
        "mossy_berrocal": tex_mossy_berrocal(),
        "polished_berrocal": tex_polished_berrocal(),
        "berrocal_bricks": tex_berrocal_bricks(),
        "berrocal_ore": tex_berrocal_ore(),
        "berilo_block": tex_berilo_block(),
        "berrocal_lamp": tex_berrocal_lamp(),
    }
    items = {
        "berilo": tex_berilo(),
        "berilo_pickaxe": tex_berilo_pickaxe(),
        "berilo_sword": tex_berilo_sword(),
    }

    for name, image in blocks.items():
        image.save(BLOCK_DIR / f"{name}.png")
    for name, image in items.items():
        image.save(ITEM_DIR / f"{name}.png")

    make_pack_icon("BP").save(BP / "pack_icon.png")
    make_pack_icon("RP").save(RP / "pack_icon.png")
    make_preview(blocks, items).save(DOCS / "preview.png")

    print(f"Texturas de bloque: {len(blocks)}")
    print(f"Texturas de objeto: {len(items)}")
    print(f"Guardado en {RP.relative_to(ROOT)} y {DOCS.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
