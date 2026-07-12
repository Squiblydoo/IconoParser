"""
iconoParser/assetParser.py — Iconoclasts Assets.dat parser

Reverse-engineered format (Assets.dat, ~100 MB):

  Index table (bytes 0..FIRST_ASSET_OFFSET-1):
    - FIRST_ASSET_OFFSET / 4 = 20237 entries, each a u32 file-byte-offset
    - index[asset_id] == 0  →  asset absent
    - index[asset_id] != 0  →  byte offset of asset record in this file

  Asset record (image):
    u16  total_width
    u16  total_height
    u16  frame_width        (0 if no animation frames)
    u16  frame_height       (0 if no animation frames)
    u8   frame_count        (N)
    u32  frame_data[N]      (per-frame timing or offset data, N × 4 bytes)
    u32  compressed_size    (bytes of zlib payload that follows)
    u8   zlib_data[compressed_size]
         → decompresses to total_width × total_height × 4 bytes
           in BGRA channel order (Blue, Green, Red, Alpha)

  Asset record (audio):
    Raw RIFF/WAVE data starting with "RIFF" magic.
    The 16 bytes preceding the "RIFF" bytes appear to be a record
    header with (asset_id u32, ??? u32, 1 u32, data_size u32).

  Valid asset IDs: 6645..20234  (IDs 0..6644 unused in examined copy)
  Total non-zero entries: 13,589

Usage:
    from iconoParser.assetParser import AssetsParser

    parser = AssetsParser()                    # uses default Steam install path
    parser = AssetsParser('/path/to/Assets.dat')

    ids  = parser.asset_ids()                  # sorted list of present IDs
    info = parser.get_asset(12328)             # dict with image metadata + pixels
    w, h, bgra = parser.get_image(12328)       # (width, height, bytes_bgra)
    parser.save_png(12328, 'tile.png')         # needs Pillow
    tk_img = parser.to_tk_photo(12328, root)   # tkinter PhotoImage, no Pillow needed
"""

import os
import struct
import zlib

# Default path for the Steam installation on Linux
_DEFAULT_PATH = os.path.join(
    os.path.expanduser('~'),
    '.local', 'share', 'Steam', 'steamapps', 'common',
    'Iconoclasts', 'Assets.dat',
)

# The index table occupies bytes 0..(FIRST_ASSET_OFFSET-1).
# index_entry_count = FIRST_ASSET_OFFSET // 4 = 20237.
# This was determined empirically: data at offset 80948 is the first valid
# asset record; 80948 / 4 = 20237 index slots.
FIRST_ASSET_OFFSET = 80948
INDEX_COUNT = FIRST_ASSET_OFFSET // 4  # 20237


class AssetsParser:
    """
    Lazy-loading parser for Iconoclasts Assets.dat.

    The file is memory-mapped on first access; the full index is built
    once and cached.  Call :meth:`close` (or use as a context manager)
    when done to release the file handle.
    """

    def __init__(self, path: str = None):
        self.path = path or _DEFAULT_PATH
        self._data: bytes = None   # raw file bytes (loaded on demand)
        self._index: dict = None   # asset_id -> byte_offset

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def close(self):
        """Release the in-memory file data."""
        self._data = None
        self._index = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load(self):
        if self._data is None:
            with open(self.path, 'rb') as fh:
                self._data = fh.read()

    def _build_index(self):
        """Parse the flat u32 index table and cache it."""
        if self._index is not None:
            return
        self._load()
        data = self._data
        index = {}
        for i in range(INDEX_COUNT):
            off = struct.unpack_from('<I', data, i * 4)[0]
            if off != 0:
                index[i] = off
        self._index = index

    @staticmethod
    def _u8(data, pos):
        return data[pos]

    @staticmethod
    def _u16(data, pos):
        return struct.unpack_from('<H', data, pos)[0]

    @staticmethod
    def _u32(data, pos):
        return struct.unpack_from('<I', data, pos)[0]

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def asset_ids(self) -> list:
        """Return a sorted list of all present asset IDs."""
        self._build_index()
        return sorted(self._index)

    def has_asset(self, asset_id: int) -> bool:
        """Return True if asset_id is present in the archive."""
        self._build_index()
        return asset_id in self._index

    def get_asset(self, asset_id: int) -> dict | None:
        """
        Parse and return the asset record for *asset_id*.

        Returns ``None`` if the ID is absent.

        For **image** assets the returned dict contains::

            {
              'id':           int,
              'type':         'image',
              'width':        int,          # total sprite-sheet width
              'height':       int,          # total sprite-sheet height
              'frame_width':  int,          # single-frame width (0 = no frames)
              'frame_height': int,          # single-frame height
              'frame_count':  int,          # number of animation frames
              'frame_data':   list[int],    # per-frame timing/offset values
              'pixels':       bytes,        # BGRA, length = width*height*4
            }

        For **audio** assets::

            {
              'id':   int,
              'type': 'audio',
              'data': bytes,    # raw RIFF/WAVE bytes
            }
        """
        self._build_index()
        if asset_id not in self._index:
            return None

        data = self._data
        pos = self._index[asset_id]

        w  = self._u16(data, pos);     pos += 2
        h  = self._u16(data, pos);     pos += 2
        fw = self._u16(data, pos);     pos += 2
        fh = self._u16(data, pos);     pos += 2
        fc = self._u8(data, pos);      pos += 1

        frame_data = []
        for _ in range(fc):
            frame_data.append(self._u32(data, pos))
            pos += 4

        comp_size = self._u32(data, pos);  pos += 4
        payload = data[pos: pos + comp_size]

        # Distinguish zlib-compressed images from raw RIFF audio
        is_zlib = (len(payload) >= 2
                   and payload[0] == 0x78
                   and payload[1] in (0x01, 0x5E, 0x9C, 0xDA))

        if payload[:4] == b'RIFF':
            return {
                'id':   asset_id,
                'type': 'audio',
                'data': payload,
            }

        if is_zlib:
            pixels = zlib.decompress(payload)
        else:
            # Unknown / uncompressed; return raw bytes
            pixels = payload

        return {
            'id':           asset_id,
            'type':         'image',
            'width':        w,
            'height':       h,
            'frame_width':  fw,
            'frame_height': fh,
            'frame_count':  fc,
            'frame_data':   frame_data,
            'pixels':       pixels,   # BGRA
        }

    def get_image(self, asset_id: int):
        """
        Convenience method.  Returns ``(width, height, bgra_bytes)``
        for image assets, or ``None`` for absent/non-image assets.
        """
        asset = self.get_asset(asset_id)
        if asset and asset['type'] == 'image':
            return asset['width'], asset['height'], asset['pixels']
        return None

    def save_png(self, asset_id: int, output_path: str) -> bool:
        """
        Save an image asset as a PNG file.

        Requires Pillow (``pip install Pillow``).
        Returns True on success, False if asset absent or not an image.
        """
        from PIL import Image  # noqa: PLC0415

        result = self.get_image(asset_id)
        if result is None:
            return False

        w, h, bgra = result
        # Sanity-check: decompressed data must be exactly w*h*4 bytes
        if len(bgra) != w * h * 4:
            return False
        # Reorder BGRA → RGBA in-place via slice reassignment
        rgba = bytearray(len(bgra))
        for i in range(0, len(bgra), 4):
            rgba[i]     = bgra[i + 2]  # R  ← src B+2
            rgba[i + 1] = bgra[i + 1]  # G
            rgba[i + 2] = bgra[i]      # B  ← src R+0
            rgba[i + 3] = bgra[i + 3]  # A
        img = Image.frombytes('RGBA', (w, h), bytes(rgba))
        img.save(output_path)
        return True

    def to_tk_photo(self, asset_id: int, root=None):
        """
        Return a ``tkinter.PhotoImage`` for an image asset.

        Does **not** require Pillow — uses PPM encoding instead.
        Alpha channel is discarded (tkinter's PhotoImage has no alpha).
        *root* is an optional Tk root widget (needed if no Tk window
        exists yet).

        Returns None if the asset is absent or not an image.
        """
        import tkinter as tk  # noqa: PLC0415

        result = self.get_image(asset_id)
        if result is None:
            return None

        w, h, bgra = result
        # Build a raw PPM (P6) image: RGB, 1 byte per channel
        ppm_header = f'P6\n{w} {h}\n255\n'.encode()
        rgb = bytearray(w * h * 3)
        for i in range(w * h):
            b = bgra[i * 4]
            g = bgra[i * 4 + 1]
            r = bgra[i * 4 + 2]
            rgb[i * 3]     = r
            rgb[i * 3 + 1] = g
            rgb[i * 3 + 2] = b

        if root is not None:
            return tk.PhotoImage(master=root, data=ppm_header + bytes(rgb))
        return tk.PhotoImage(data=ppm_header + bytes(rgb))

    def to_tk_photo_scaled(self, asset_id: int, scale: float = 1.0, root=None):
        """
        Like :meth:`to_tk_photo` but applies nearest-neighbour scaling.
        Useful for rendering small tiles at a larger size in the visualizer.
        """
        import tkinter as tk  # noqa: PLC0415

        result = self.get_image(asset_id)
        if result is None:
            return None

        w, h, bgra = result
        nw = max(1, int(w * scale))
        nh = max(1, int(h * scale))

        ppm_header = f'P6\n{nw} {nh}\n255\n'.encode()
        rgb = bytearray(nw * nh * 3)
        for dy in range(nh):
            sy = int(dy / scale)
            for dx in range(nw):
                sx = int(dx / scale)
                i_src = (sy * w + sx) * 4
                i_dst = (dy * nw + dx) * 3
                rgb[i_dst]     = bgra[i_src + 2]  # R
                rgb[i_dst + 1] = bgra[i_src + 1]  # G
                rgb[i_dst + 2] = bgra[i_src]      # B

        if root is not None:
            return tk.PhotoImage(master=root, data=ppm_header + bytes(rgb))
        return tk.PhotoImage(data=ppm_header + bytes(rgb))

    def iter_assets(self, asset_type: str = None):
        """
        Yield all asset dicts.  Pass ``asset_type='image'`` or
        ``asset_type='audio'`` to filter by type.
        """
        for aid in self.asset_ids():
            asset = self.get_asset(aid)
            if asset and (asset_type is None or asset['type'] == asset_type):
                yield asset

    def find_tilesheet_candidates(self, min_width: int = 256) -> list:
        """
        Return a list of asset IDs that look like tile-sheet images:
        large, square-ish images whose dimensions are multiples of common
        tile sizes (8, 16, 32).

        These are candidates for level tile graphics.  The actual mapping
        from .lvl tileset IDs to asset IDs is not yet reverse-engineered.
        """
        self._build_index()
        results = []
        data = self._data
        file_size = len(data)
        for aid, offset in self._index.items():
            w  = self._u16(data, offset)
            h  = self._u16(data, offset + 2)
            fc = self._u8(data, offset + 8)
            # Skip implausibly large or empty dimensions
            if w < min_width or h == 0 or w > 4096 or h > 4096:
                continue
            # Quick sanity-check: header + comp_size field must be in-file
            hdr_len = 9 + fc * 4 + 4
            if offset + hdr_len > file_size:
                continue
            comp_size = self._u32(data, offset + 9 + fc * 4)
            if comp_size == 0 or offset + hdr_len + comp_size > file_size:
                continue
            # Expect pixel data = w*h*4 bytes when decompressed
            expected_pixels = w * h * 4
            if expected_pixels > 64 * 1024 * 1024:  # skip >64 MB decompressed
                continue
            is_tile_multiple = (
                (w % 16 == 0 or w % 8 == 0) and
                (h % 16 == 0 or h % 8 == 0)
            )
            if is_tile_multiple:
                results.append((w * h, aid, w, h))
        results.sort(reverse=True)
        return [(aid, w, h) for _, aid, w, h in results]
