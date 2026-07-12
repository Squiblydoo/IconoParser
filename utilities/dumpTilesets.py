#!/usr/bin/env python3
"""
dumpTilesets.py — Pre-scan Assets.dat and save all wide images to disk.

Usage:
    python3 dumpTilesets.py [--min-width 256] [--out-dir ~/.cache/iconoparser/tilesets]
    python3 dumpTilesets.py --regen-thumbs    # re-generate thumbnails from existing dump

Creates one PPM + one thumbnail PPM per wide image, plus an index.json.
Run once; then open tilesetBrowser.py to browse results quickly.
"""

import sys
import os
import json
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iconoParser.assetParser import AssetsParser

THUMB_H = 120   # thumbnail height in pixels (must match tilesetBrowser.py)


def save_ppm(path, w, h, rgba):
    """Save RGBA pixel data as a P6 PPM file."""
    header = f'P6\n{w} {h}\n255\n'.encode()
    rgb = bytearray(w * h * 3)
    for i in range(w * h):
        rgb[i * 3]     = rgba[i * 4]       # R
        rgb[i * 3 + 1] = rgba[i * 4 + 1]   # G
        rgb[i * 3 + 2] = rgba[i * 4 + 2]   # B
    with open(path, 'wb') as f:
        f.write(header)
        f.write(rgb)


def make_thumb_rgba(rgba, w, h):
    """Nearest-neighbour scale RGBA data down to THUMB_H tall, return PPM bytes."""
    factor = max(1, -(-h // THUMB_H))   # ceiling division
    dw = max(1, w // factor)
    dh = max(1, h // factor)
    sx_f = w / dw
    sy_f = h / dh
    header = f'P6\n{dw} {dh}\n255\n'.encode()
    rgb = bytearray(dw * dh * 3)
    for dy in range(dh):
        sy = int(dy * sy_f)
        for dx in range(dw):
            sx = int(dx * sx_f)
            i_src = (sy * w + sx) * 4
            i_dst = (dy * dw + dx) * 3
            rgb[i_dst]     = rgba[i_src]       # R
            rgb[i_dst + 1] = rgba[i_src + 1]   # G
            rgb[i_dst + 2] = rgba[i_src + 2]   # B
    return header + bytes(rgb)


def make_thumb_ppm(ppm_path, w, h):
    """Read an existing full PPM and return thumbnail PPM bytes."""
    with open(ppm_path, 'rb') as f:
        raw = f.read()
    # skip 3-line header: "P6\n", "W H\n", "255\n"
    pos = raw.index(b'\n') + 1          # after magic
    pos = raw.index(b'\n', pos) + 1     # after dimensions
    pos = raw.index(b'\n', pos) + 1     # after maxval
    rgb_src = raw[pos:]

    factor = max(1, -(-h // THUMB_H))
    dw = max(1, w // factor)
    dh = max(1, h // factor)
    sx_f = w / dw
    sy_f = h / dh
    header = f'P6\n{dw} {dh}\n255\n'.encode()
    rgb = bytearray(dw * dh * 3)
    for dy in range(dh):
        sy = int(dy * sy_f)
        for dx in range(dw):
            sx = int(dx * sx_f)
            i_src = (sy * w + sx) * 3
            i_dst = (dy * dw + dx) * 3
            rgb[i_dst:i_dst + 3] = rgb_src[i_src:i_src + 3]
    return header + bytes(rgb)


def swap_rb_ppm(path):
    """Read a P6 PPM, swap R and B channels in every pixel, write back."""
    with open(path, 'rb') as f:
        raw = f.read()
    # Parse 3-line P6 header
    p = raw.index(b'\n') + 1
    dim_end = raw.index(b'\n', p) + 1
    dim_str = raw[p:dim_end - 1].split()
    pw_px, ph_px = int(dim_str[0]), int(dim_str[1])
    maxval_end = raw.index(b'\n', dim_end) + 1
    header = raw[:maxval_end]
    pixels = bytearray(raw[maxval_end:])
    for i in range(0, pw_px * ph_px * 3, 3):
        pixels[i], pixels[i + 2] = pixels[i + 2], pixels[i]   # swap R↔B
    with open(path, 'wb') as f:
        f.write(header)
        f.write(pixels)


def main():
    ap = argparse.ArgumentParser(
        description='Dump all wide images from Assets.dat to disk as PPMs')
    ap.add_argument('--min-width', type=int, default=1,
                    help='Minimum image width to include (default: 1 = all images)')
    ap.add_argument('--out-dir',
                    default=os.path.expanduser(
                        '~/.cache/iconoparser/tilesets'),
                    help='Output directory (default: ~/.cache/iconoparser/tilesets)')
    ap.add_argument('--regen-thumbs', action='store_true',
                    help='Regenerate thumbnail PPMs from existing full PPMs '
                         '(reads index.json, does not re-scan Assets.dat)')
    ap.add_argument('--fix-colors', action='store_true',
                    help='Swap R↔B channels in all existing PPMs (converts '
                         'between BGRA and RGBA interpretation). '
                         'Run this if images look colour-inverted (blue=red etc). '
                         'Safe to run twice — it reverts itself.')
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    # ── fix-colors mode: swap R↔B in every PPM (full + thumb) ──
    if args.fix_colors:
        idx_path = os.path.join(args.out_dir, 'index.json')
        if not os.path.exists(idx_path):
            print(f'ERROR: no index.json in {args.out_dir}')
            sys.exit(1)
        with open(idx_path) as f:
            index = json.load(f)
        print(f'Swapping R↔B channels in {len(index)} images + thumbs…')
        for aid_s, meta in index.items():
            for key in ('file', 'thumb'):
                fname = meta.get(key)
                if not fname:
                    continue
                fpath = os.path.join(args.out_dir, fname)
                if os.path.exists(fpath):
                    try:
                        swap_rb_ppm(fpath)
                        print(f'  #{aid_s:6} {key}')
                    except Exception as exc:
                        print(f'  #{aid_s} {key}: ERROR — {exc}')
        print('\nDone. Run python3 tilesetBrowser.py to view corrected images.')
        return

    # ── regen-thumbs mode: just rebuild thumbnails from existing full PPMs ──
    if args.regen_thumbs:
        idx_path = os.path.join(args.out_dir, 'index.json')
        if not os.path.exists(idx_path):
            print(f'ERROR: no index.json found in {args.out_dir}')
            print('Run without --regen-thumbs first to do the initial dump.')
            sys.exit(1)
        with open(idx_path) as f:
            index = json.load(f)
        print(f'Regenerating thumbnails for {len(index)} images…')
        for aid_s, meta in index.items():
            fpath = os.path.join(args.out_dir, meta['file'])
            th_fname = f'{aid_s}_thumb.ppm'
            th_path = os.path.join(args.out_dir, th_fname)
            try:
                ppm_data = make_thumb_ppm(fpath, meta['width'], meta['height'])
                with open(th_path, 'wb') as f:
                    f.write(ppm_data)
                meta['thumb'] = th_fname
                print(f'  #{aid_s:6}  {meta["width"]}×{meta["height"]}')
            except Exception as exc:
                print(f'  #{aid_s}: error — {exc}')
        with open(idx_path, 'w') as f:
            json.dump(index, f, indent=2)
        print(f'\nDone. Index updated: {idx_path}')
        return

    # ── full dump mode ──
    print(f'Output dir : {args.out_dir}')
    print(f'Min width  : {args.min_width}')
    print()

    parser = AssetsParser()
    all_ids = parser.asset_ids()
    print(f'Total assets in archive: {len(all_ids)}')

    index = {}
    saved = 0
    errors = 0

    for i, aid in enumerate(all_ids):
        if i % 1000 == 0:
            print(f'  [{i:5d}/{len(all_ids)}] scanning…', flush=True)
        try:
            info = parser.get_asset(aid)
            if not info or info['type'] != 'image':
                continue
            w  = info['width']
            h  = info['height']
            if w < args.min_width:
                continue

            fname = f'{aid}_{w}x{h}.ppm'
            fpath = os.path.join(args.out_dir, fname)
            save_ppm(fpath, w, h, info['pixels'])

            # generate thumbnail
            th_fname = f'{aid}_thumb.ppm'
            th_path = os.path.join(args.out_dir, th_fname)
            ppm_data = make_thumb_rgba(info['pixels'], w, h)
            with open(th_path, 'wb') as f:
                f.write(ppm_data)

            index[str(aid)] = {
                'width':        w,
                'height':       h,
                'frame_width':  info['frame_width'],
                'frame_height': info['frame_height'],
                'frame_count':  info['frame_count'],
                'file':         fname,
                'thumb':        th_fname,
            }
            print(f'  #{aid:6d}  {w}×{h}  →  {fname}')
            saved += 1

        except Exception as exc:
            print(f'  #{aid}: error — {exc}')
            errors += 1

    idx_path = os.path.join(args.out_dir, 'index.json')
    with open(idx_path, 'w') as f:
        json.dump(index, f, indent=2)

    print()
    print(f'Done: {saved} images saved, {errors} errors')
    print(f'Index written to: {idx_path}')
    print()
    print('Now run:  python3 tilesetBrowser.py')


if __name__ == '__main__':
    main()
