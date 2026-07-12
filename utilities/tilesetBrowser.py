#!/usr/bin/env python3
"""
tilesetBrowser.py — Browse pre-dumped tilesheet images.

Run dumpTilesets.py once first to generate the image cache, then open this.

Usage:
    python3 dumpTilesets.py          # one-time pre-processing
    python3 tilesetBrowser.py        # browse results
"""

import tkinter as tk
from tkinter import ttk, filedialog
import os
import json
import base64
import threading

DEFAULT_DIR = os.path.expanduser('~/.cache/iconoparser/tilesets')
THUMB_H     = 120   # thumbnail height in pixels
THUMB_PAD   = 6


class TilesetBrowser:
    def __init__(self, root, dump_dir=None):
        self.root = root
        self.root.title('Tileset Browser')
        self.root.geometry('1280x720')

        self._dump_dir   = dump_dir or DEFAULT_DIR
        self._index      = {}    # str(aid) -> {width, height, file, …}
        self._thumbs     = []    # PhotoImage refs (must stay alive)
        self._full_img   = None
        self._sel_id     = None

        self._build_ui()
        self._load_index()

    # ── UI ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        top = ttk.Frame(self.root)
        top.pack(fill='x', padx=6, pady=4)

        self._status = tk.StringVar(value='')
        ttk.Label(top, textvariable=self._status).pack(side='left')

        ttk.Button(top, text='Change folder…',
                   command=self._pick_dir).pack(side='right')

        pw = ttk.PanedWindow(self.root, orient='horizontal')
        pw.pack(fill='both', expand=True)

        # ── left: thumbnail canvas ──
        left = ttk.Frame(pw)
        pw.add(left, weight=1)

        self._tcanvas = tk.Canvas(left, bg='#333333',
                                  highlightthickness=0)
        tvsb = ttk.Scrollbar(left, orient='vertical',
                             command=self._tcanvas.yview)
        self._tcanvas.configure(yscrollcommand=tvsb.set)
        tvsb.pack(side='right', fill='y')
        self._tcanvas.pack(fill='both', expand=True)
        self._tcanvas.bind('<Button-4>',
            lambda e: self._tcanvas.yview_scroll(-3, 'units'))
        self._tcanvas.bind('<Button-5>',
            lambda e: self._tcanvas.yview_scroll(3, 'units'))
        self._tcanvas.bind('<Configure>', self._on_tcanvas_resize)

        # ── right: full image ──
        right = ttk.Frame(pw)
        pw.add(right, weight=2)

        self._info = tk.StringVar(value='Click a thumbnail')
        ttk.Label(right, textvariable=self._info,
                  anchor='w').pack(fill='x', padx=4, pady=2)

        sc_row = ttk.Frame(right)
        sc_row.pack(fill='x', padx=4)
        ttk.Label(sc_row, text='Scale: ').pack(side='left')
        self._scale = tk.DoubleVar(value=1.0)
        for s in (0.25, 0.5, 1.0, 2.0):
            ttk.Radiobutton(sc_row, text=f'{s}×', variable=self._scale,
                            value=s, command=self._redisplay).pack(side='left')

        fc = ttk.Frame(right)
        fc.pack(fill='both', expand=True)
        self._fcanvas = tk.Canvas(fc, bg='#222222',
                                  highlightthickness=0)
        fvsb = ttk.Scrollbar(fc, orient='vertical',
                             command=self._fcanvas.yview)
        fhsb = ttk.Scrollbar(fc, orient='horizontal',
                             command=self._fcanvas.xview)
        self._fcanvas.configure(yscrollcommand=fvsb.set,
                                xscrollcommand=fhsb.set)
        fvsb.pack(side='right', fill='y')
        fhsb.pack(side='bottom', fill='x')
        self._fcanvas.pack(fill='both', expand=True)

    # ── index loading ─────────────────────────────────────────────────────

    def _pick_dir(self):
        d = filedialog.askdirectory(initialdir=self._dump_dir)
        if d:
            self._dump_dir = d
            self._load_index()

    def _load_index(self):
        idx_path = os.path.join(self._dump_dir, 'index.json')
        if not os.path.exists(idx_path):
            self._status.set(
                f'No index.json in {self._dump_dir} — '
                f'run:  python3 dumpTilesets.py')
            return

        with open(idx_path) as f:
            self._index = json.load(f)

        self._status.set(
            f'{len(self._index)} images in {self._dump_dir}')
        self._tcanvas.delete('all')
        self._thumbs.clear()
        self._queue = sorted(
            self._index.items(),
            key=lambda kv: int(kv[0]))
        self._cur_x = THUMB_PAD
        self._cur_y = THUMB_PAD
        self._row_h = 0
        self._cw    = 600
        self.root.after(100, self._drain)

    def _on_tcanvas_resize(self, event):
        self._cw = max(event.width, 200)

    # ── thumbnail rendering ───────────────────────────────────────────────

    def _drain(self):
        BATCH = 4
        for _ in range(BATCH):
            if not self._queue:
                total_h = self._cur_y + self._row_h + THUMB_PAD
                self._tcanvas.configure(
                    scrollregion=(0, 0, self._cw, max(total_h, 400)))
                self._status.set(
                    f'{len(self._index)} images — click to view')
                return
            aid_s, meta = self._queue.pop(0)
            self._add_thumb(aid_s, meta)
        self.root.after(10, self._drain)

    def _add_thumb(self, aid_s, meta):
        # Use pre-generated thumbnail if available; fall back to full + subsample
        thumb_key = meta.get('thumb')
        if thumb_key:
            fpath = os.path.join(self._dump_dir, thumb_key)
        else:
            fpath = os.path.join(self._dump_dir, meta['file'])

        if not os.path.exists(fpath):
            return

        w, h = meta['width'], meta['height']
        try:
            img = tk.PhotoImage(file=fpath)
            if not thumb_key:
                # no pre-generated thumb — subsample the full image on the fly
                factor = max(1, -(-h // THUMB_H))
                img = img.subsample(factor, factor)
        except Exception:
            return

        tw = img.width()
        th = img.height()

        # wrap to new row
        if self._cur_x + tw + THUMB_PAD > self._cw and self._cur_x > THUMB_PAD:
            self._cur_y += self._row_h + THUMB_PAD * 2
            self._row_h  = 0
            self._cur_x  = THUMB_PAD

        x, y = self._cur_x, self._cur_y

        self._tcanvas.create_image(x, y, image=img, anchor='nw',
                                   tags=f'i{aid_s}')
        self._tcanvas.create_text(
            x + tw // 2, y + th + 2,
            text=f'#{aid_s}  {w}×{h}',
            fill='#cccccc', font=('Courier', 8), anchor='n',
            tags=f'i{aid_s}')
        box = self._tcanvas.create_rectangle(
            x - 1, y - 1, x + tw + 1, y + th + 14,
            outline='', width=2, tags=f'i{aid_s}')

        self._tcanvas.tag_bind(f'i{aid_s}', '<Button-1>',
                               lambda _e, a=aid_s: self._show(a))
        self._tcanvas.tag_bind(f'i{aid_s}', '<Enter>',
            lambda _e, b=box: self._tcanvas.itemconfig(b, outline='#ffcc00'))
        self._tcanvas.tag_bind(f'i{aid_s}', '<Leave>',
            lambda _e, b=box: self._tcanvas.itemconfig(b, outline=''))

        self._thumbs.append(img)
        self._cur_x += tw + THUMB_PAD
        self._row_h  = max(self._row_h, th + 16)

        total_h = self._cur_y + self._row_h + THUMB_PAD
        self._tcanvas.configure(
            scrollregion=(0, 0, self._cw, max(total_h, 400)))

    # ── full image ────────────────────────────────────────────────────────

    def _show(self, aid_s):
        self._sel_id = aid_s
        self._redisplay()

    def _redisplay(self):
        if self._sel_id is None:
            return
        aid_s = self._sel_id
        meta  = self._index.get(aid_s)
        if not meta:
            return

        fpath = os.path.join(self._dump_dir, meta['file'])
        if not os.path.exists(fpath):
            self._info.set(f'#{aid_s}: full image not on disk — re-run dumpTilesets.py')
            return

        self._info.set(f'Loading #{aid_s}…')
        self._full_img = None
        self._full_ref = None

        def bg_load():
            try:
                with open(fpath, 'rb') as f:
                    raw = f.read()
                b64 = base64.b64encode(raw)
            except Exception as exc:
                self.root.after(0, lambda: self._info.set(f'Error reading file: {exc}'))
                return
            self.root.after(0, lambda: self._show_full_img(aid_s, meta, b64))

        threading.Thread(target=bg_load, daemon=True).start()

    def _show_full_img(self, aid_s, meta, b64):
        # Called on the main thread after bytes are loaded in background
        scale = self._scale.get()
        try:
            full = tk.PhotoImage(data=b64)
            w, h = meta['width'], meta['height']
            if scale < 1.0:
                factor = max(1, round(1.0 / scale))
                img = full.subsample(factor, factor)
            elif scale > 1.0:
                factor = max(1, round(scale))
                img = full.zoom(factor, factor)
            else:
                img = full
        except Exception as exc:
            import traceback; traceback.print_exc()
            self._info.set(f'Error loading #{aid_s}: {exc}')
            return

        self._full_ref = full   # keep the source alive when scale != 1
        self._full_img = img
        self._fcanvas.delete('all')
        self._fcanvas.configure(
            scrollregion=(0, 0, img.width() + 4, img.height() + 4))
        self._fcanvas.create_image(2, 2, image=img, anchor='nw')
        self._info.set(
            f'Asset #{aid_s}  —  {w}×{h} px  '
            f'({meta["frame_count"]} frames, '
            f'frame {meta["frame_width"]}×{meta["frame_height"]})')


if __name__ == '__main__':
    import sys
    dump_dir = sys.argv[1] if len(sys.argv) > 1 else None
    root = tk.Tk()
    TilesetBrowser(root, dump_dir)
    root.mainloop()
