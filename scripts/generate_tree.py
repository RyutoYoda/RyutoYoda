#!/usr/bin/env python3
"""
3D Isometric Minecraft-style tree generator.
Tree size scales with total GitHub contributions.
"""
import argparse
from PIL import Image, ImageDraw

# --- Isometric projection constants ---
TW = 48   # top-face diamond width (px)
TH = 24   # top-face diamond height (px)
SH = 26   # side-face height (px)

# Block palettes: [top_face_rgb, right_face_rgb (x+1 side), left_face_rgb (z+1 side)]
PALETTE = {
    'leaf':  [(106, 185,  54), ( 72, 130,  36), ( 88, 158,  44)],
    'leafD': [( 88, 158,  44), ( 58, 105,  28), ( 72, 128,  34)],
    'wood':  [(162, 130,  73), ( 98,  74,  40), (128,  98,  54)],
    'grass': [(106, 185,  54), (108,  78,  42), (130,  96,  54)],
    'dirt':  [(130,  96,  54), (108,  78,  42), (118,  86,  46)],
}


def iso(x, y, z, ox=0, oy=0):
    """3D block coords → 2D screen coords."""
    sx = ox + (x - z) * (TW // 2)
    sy = oy + (x + z) * (TH // 2) - y * SH
    return int(sx), int(sy)


def block_corners(bx, by, bz, ox, oy):
    return {
        (dx, dy, dz): iso(bx+dx, by+dy, bz+dz, ox, oy)
        for dx in (0, 1) for dy in (0, 1) for dz in (0, 1)
    }


def draw_block(draw, bx, by, bz, btype, ox, oy):
    v = block_corners(bx, by, bz, ox, oy)
    top_rgb, right_rgb, left_rgb = PALETTE[btype]

    def face(pts, rgb):
        rgba = rgb + (255,)
        draw.polygon(pts, fill=rgba)
        dark = tuple(max(0, c - 55) for c in rgb) + (230,)
        draw.polygon(pts, outline=dark)

    # Draw order: right → left → top (top always visible)
    face([v[1,0,0], v[1,1,0], v[1,1,1], v[1,0,1]], right_rgb)
    face([v[0,0,1], v[0,1,1], v[1,1,1], v[1,0,1]], left_rgb)
    face([v[0,1,0], v[1,1,0], v[1,1,1], v[0,1,1]], top_rgb)


def build_tree(commits):
    """Return list of (bx, by, bz, block_type) for the tree."""
    if   commits <    50: trunk_h, cr = 3, 2
    elif commits <   200: trunk_h, cr = 4, 2
    elif commits <   500: trunk_h, cr = 5, 3
    elif commits <  1500: trunk_h, cr = 6, 3
    elif commits <  3000: trunk_h, cr = 7, 4
    else:                 trunk_h, cr = 8, 4

    blocks = []

    # Ground platform (grass + dirt)
    for dx in range(-cr - 1, cr + 2):
        for dz in range(-cr - 1, cr + 2):
            blocks.append((dx, -1, dz, 'grass'))
            blocks.append((dx, -2, dz, 'dirt'))

    # Trunk
    for y in range(trunk_h):
        blocks.append((0, y, 0, 'wood'))

    # Canopy (4 layers starting 1 below trunk top)
    y_base = trunk_h - 1
    for layer in range(4):
        y = y_base + layer
        if layer == 0:   r = max(1, cr - 1)
        elif layer <= 2: r = cr
        else:            r = max(1, cr - 1)

        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                if abs(dx) == r and abs(dz) == r:  # round corners
                    continue
                if dx == 0 and dz == 0 and y < trunk_h:  # don't overwrite trunk
                    continue
                btype = 'leafD' if (abs(dx) + abs(dz)) % 3 == 0 else 'leaf'
                blocks.append((dx, y, dz, btype))

    return blocks


def generate(commits, out='minecraft_tree.png'):
    blocks = build_tree(commits)

    # Compute bounding box with a temporary origin
    ox0, oy0 = 1000, 1000
    all_pts = [
        iso(bx+dx, by+dy, bz+dz, ox0, oy0)
        for bx, by, bz, _ in blocks
        for dx in (0, 1) for dy in (0, 1) for dz in (0, 1)
    ]
    min_x = min(p[0] for p in all_pts)
    min_y = min(p[1] for p in all_pts)
    max_x = max(p[0] for p in all_pts)
    max_y = max(p[1] for p in all_pts)

    pad = 24
    w = max_x - min_x + pad * 2
    h = max_y - min_y + pad * 2
    ox = ox0 - min_x + pad
    oy = oy0 - min_y + pad

    img = Image.new('RGBA', (int(w), int(h)), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Painter's algorithm: back-to-front (x+z ascending), bottom-to-top (y ascending)
    sorted_blocks = sorted(blocks, key=lambda b: (b[0] + b[2], b[1]))
    for bx, by, bz, btype in sorted_blocks:
        draw_block(draw, bx, by, bz, btype, ox, oy)

    img.save(out)
    print(f"Saved {out}  ({int(w)}×{int(h)}px, {len(blocks)} blocks, commits={commits})")


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--commits', type=int, default=100)
    ap.add_argument('--output', default='minecraft_tree.png')
    args = ap.parse_args()
    generate(args.commits, args.output)
