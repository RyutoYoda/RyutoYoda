#!/usr/bin/env python3
"""
Contribution Tree — 3D isometric block renderer.
Tree size scales with total GitHub contributions.
Irregular branches and fuzzy leaf clusters for a realistic look.
"""
import argparse
import random
from PIL import Image, ImageDraw

# --- Isometric projection constants ---
TW = 48
TH = 24
SH = 26

PALETTE = {
    'leaf':  [(106, 185,  54), ( 72, 130,  36), ( 88, 158,  44)],
    'leafD': [( 82, 150,  40), ( 54,  98,  24), ( 68, 120,  30)],
    'wood':  [(162, 130,  73), ( 98,  74,  40), (128,  98,  54)],
    'grass': [(106, 185,  54), (108,  78,  42), (130,  96,  54)],
    'dirt':  [(130,  96,  54), (108,  78,  42), (118,  86,  46)],
}


def iso(x, y, z, ox=0, oy=0):
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
        draw.polygon(pts, fill=rgb + (255,))
        dark = tuple(max(0, c - 55) for c in rgb) + (230,)
        draw.polygon(pts, outline=dark)

    face([v[1,0,0], v[1,1,0], v[1,1,1], v[1,0,1]], right_rgb)
    face([v[0,0,1], v[0,1,1], v[1,1,1], v[1,0,1]], left_rgb)
    face([v[0,1,0], v[1,1,0], v[1,1,1], v[0,1,1]], top_rgb)


def build_tree(commits):
    rng = random.Random(commits % 9973)

    if   commits <  200: trunk_h, n_br = 7, 5
    elif commits <  500: trunk_h, n_br = 8, 6
    elif commits < 1500: trunk_h, n_br = 9, 7
    else:                trunk_h, n_br = 10, 8

    blk = {}  # (x,y,z) -> block_type

    def put(x, y, z, t, force=False):
        if force or (x, y, z) not in blk:
            blk[(x, y, z)] = t

    # Ground
    for dx in range(-7, 8):
        for dz in range(-7, 8):
            put(dx, -1, dz, 'grass')
            put(dx, -2, dz, 'dirt')

    # Thick trunk: 2×2 base tapering to 1×1 near top
    thick_up_to = trunk_h - 3  # lower portion is 2×2
    for y in range(trunk_h):
        put(0, y, 0, 'wood', force=True)
        if y < thick_up_to:
            put(1, y, 0, 'wood', force=True)
            put(0, y, 1, 'wood', force=True)
            put(1, y, 1, 'wood', force=True)

    # 8 possible branch directions (cardinal + diagonal)
    all_dirs = [(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1)]
    rng.shuffle(all_dirs)
    branch_dirs = all_dirs[:n_br]

    tips = []
    for bdx, bdz in branch_dirs:
        # Branch starts at a random height in the upper trunk
        y0 = trunk_h - 3 + rng.randint(0, 3)
        length = 3 + rng.randint(0, 2)  # longer branches for better visibility
        # Branch origin shifts from trunk center based on direction
        ox = 1 if bdx > 0 else 0
        oz = 1 if bdz > 0 else 0
        x, y, z = ox, y0, oz
        for _ in range(length):
            x += bdx
            z += bdz
            y += 1
            put(x, y, z, 'wood', force=True)
        tips.append((x, y, z))

    # Fuzzy spherical leaf cluster at each branch tip
    def add_cluster(cx, cy, cz, r=2):
        for dx in range(-r, r + 1):
            for dy in range(-1, r + 2):
                for dz in range(-r, r + 1):
                    # Slightly elliptical: flatter vertically
                    d2 = dx*dx + (dy - 1)*(dy - 1) * 0.75 + dz*dz
                    if d2 > r*r + 0.5:
                        continue
                    # Fuzzy outer shell: ~45% of edge blocks omitted
                    if d2 > r*r - 0.5 and rng.random() < 0.45:
                        continue
                    lx, ly, lz = cx + dx, cy + dy, cz + dz
                    if blk.get((lx, ly, lz)) != 'wood':
                        t = 'leafD' if rng.random() < 0.30 else 'leaf'
                        put(lx, ly, lz, t)

    for tx, ty, tz in tips:
        add_cluster(tx, ty, tz, r=2)

    # Small cap cluster at the very top of the trunk
    add_cluster(0, trunk_h, 0, r=1)

    return [(x, y, z, t) for (x, y, z), t in blk.items()]


def generate(commits, out='minecraft_tree.png'):
    blocks = build_tree(commits)

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

    pad = 28
    w = max_x - min_x + pad * 2
    h = max_y - min_y + pad * 2
    ox = ox0 - min_x + pad
    oy = oy0 - min_y + pad

    img = Image.new('RGBA', (int(w), int(h)), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

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
