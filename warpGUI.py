#!/usr/bin/env python3
"""
warpGUI.py — GUI level warp and flag editor for Iconoclasts.

Usage:
    python3 warpGUI.py
"""

import os, platform, shutil, struct, sys
import tkinter as tk
from tkinter import ttk, messagebox

if platform.system() == 'Windows':
    SAVE_ROOT = os.path.expandvars(r'%PROGRAMFILES(X86)%\Steam\steamapps\common\Iconoclasts\data')
else:
    SAVE_ROOT = os.path.expanduser('~/.local/share/Steam/steamapps/common/Iconoclasts/data')
LVL_ROOT  = os.path.join(SAVE_ROOT, 'lvl')

AREA_CENTER = {
    'house':    (57, 36), 'strait':   (60, 30), 'isi':      (46, 24),
    'blocky':   (59, 36), 'city':     (53, 26), 'concern':  (57, 50),
    'concernb': (51, 52), 'descent':  (40, 53), 'desert':   (52, 49),
    'midway':   (45, 50), 'mountain': (47, 46), 'tower':    (51, 48),
    'wood':     (36, 50),
}

KNOWN_EXACT = {
    ('house',  '1+'): (57, 36), ('isi',    '4+'): (43, 21),
    ('isi',   '22+'): (50, 27), ('strait', '2+'): (59, 30),
}

# Frame IDs written to 'areacheck' and the last field of 'status'.
# These are Clickteam Fusion internal frame numbers; they determine the
# region name shown on the load screen (e.g. 3536 → "GLASS STRAIT").
AREA_FRAME = {
    'blocky':   3525,  # BLOCKROCK
    'house':    3527,  # ROBIN'S HOUSE
    'city':     3542,  # CITY ONE
    'concern':  3539,  # ONE CONCERN WEST
    'concernb': 3543,  # BASTION
    'descent':  3546,  # INTO THE EARTH
    'desert':   3529,  # DESERT
    'isi':      3530,  # ISILUGAR
    'midway':   3545,  # MIDWAY
    'mountain': 3538,  # MOUNTAIN
    'strait':   3536,  # GLASS STRAIT
    'tower':    3535,  # THE TOWER
    'wood':     3534,  # SHOCKWOOD
}

FLAGS = [
    ('relaxed',             1, 'Relaxed Mode',         'No damage taken'),
    ('difficulty',          1, 'Hard Mode',            '0 = normal, 1 = hard'),
    ('forcenight',          1, 'Force Night',          'Force night-time visuals'),
    ('consistentchallenge', 1, 'Consistent Challenge', 'Challenge modifier on'),
]

BG_APP   = '#1a1a24'
BG_TOOL  = '#252535'
BG_PANEL = '#1e1e2e'
FG_TEXT  = '#d0d0e0'
FG_DIM   = '#7070a0'
FG_EDIT  = '#ffffff'
ACC_BLUE = '#4488cc'
ACC_GRN  = '#44cc88'
ACC_RED  = '#cc4444'
ACC_YLW  = '#ccaa22'
ROW_ODD  = '#1a1a2e'
ROW_EVEN = '#1e1e38'
ROW_SEL  = '#2a3a5a'


# ── MAP1.0 I/O ────────────────────────────────────────────────────────────────

def parse_map10(data: bytes):
    if data[:6] != b'MAP1.0':
        raise ValueError(f'Not a MAP1.0 file')
    pos = 6
    count = struct.unpack_from('<I', data, pos)[0]; pos += 4
    entries = []
    for _ in range(count):
        klen = struct.unpack_from('<I', data, pos)[0]; pos += 4
        key  = data[pos:pos+klen].rstrip(b'\x00').decode('latin-1'); pos += klen
        vtype = struct.unpack_from('<I', data, pos)[0]; pos += 4
        if vtype == 1:
            val = struct.unpack_from('<d', data, pos)[0]; pos += 8
        elif vtype == 2:
            slen = struct.unpack_from('<I', data, pos)[0]; pos += 4
            val  = data[pos:pos+slen].rstrip(b'\x00').decode('latin-1'); pos += slen
        else:
            raise ValueError(f'Unknown vtype {vtype}')
        entries.append([key, vtype, val])
    return entries


def serialise_map10(entries) -> bytes:
    out = bytearray(b'MAP1.0')
    out += struct.pack('<I', len(entries))
    for key, vtype, val in entries:
        key_b = (key + '\x00').encode('latin-1')
        out += struct.pack('<I', len(key_b))
        out += key_b
        out += struct.pack('<I', vtype)
        if vtype == 1:
            out += struct.pack('<d', float(val))
        elif vtype == 2:
            val_b = (str(val) + '\x00').encode('latin-1')
            out += struct.pack('<I', len(val_b))
            out += val_b
    return bytes(out)


def get_entry(entries, key):
    for e in entries:
        if e[0] == key:
            return e
    return None


def set_entry(entries, key, vtype, val):
    for e in entries:
        if e[0] == key:
            e[1] = vtype; e[2] = val; return
    entries.append([key, vtype, val])


def save_path(slot: int) -> str:
    return os.path.join(SAVE_ROOT, 'point' if slot == 0 else f'save{slot}')


def active_slot() -> int:
    try:
        with open(save_path(0), 'rb') as f:
            entries = parse_map10(f.read())
        e = get_entry(entries, 'lastsaveslot')
        if e:
            return max(1, min(3, int(float(e[2]))))
    except Exception:
        pass
    return 1


def load_slot(slot: int):
    with open(save_path(slot), 'rb') as f:
        return parse_map10(f.read())


def write_slot(slot: int, entries):
    path = save_path(slot)
    bak  = path + '.warp.bak'
    if not os.path.exists(bak):
        shutil.copy2(path, bak)
    with open(path, 'wb') as f:
        f.write(serialise_map10(entries))


def list_rooms(area: str):
    d = os.path.join(LVL_ROOT, area)
    if not os.path.isdir(d):
        return []
    rooms = [f.replace('.lvl', '') for f in os.listdir(d) if f.endswith('.lvl')]
    rooms.sort(key=lambda x: (len(x), x))
    return rooms


def all_areas():
    if not os.path.isdir(LVL_ROOT):
        return []
    return sorted(d for d in os.listdir(LVL_ROOT) if os.path.isdir(os.path.join(LVL_ROOT, d)))


# ── GUI ───────────────────────────────────────────────────────────────────────

class WarpGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Iconoclasts — Warp')
        self.geometry('780x540')
        self.minsize(640, 420)
        self.configure(bg=BG_APP)

        self._slot    = tk.IntVar(value=active_slot())
        self._entries = []   # current save entries

        self._build_ui()
        self._load_current_slot()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Toolbar ───────────────────────────────────────────────────────────
        bar = tk.Frame(self, bg=BG_TOOL, pady=6)
        bar.pack(side='top', fill='x')

        tk.Label(bar, text='Save slot:', bg=BG_TOOL, fg=FG_DIM).pack(side='left', padx=(10, 4))
        for n in (1, 2, 3):
            tk.Radiobutton(
                bar, text=f'Save {n}', variable=self._slot, value=n,
                bg=BG_TOOL, fg=FG_TEXT, selectcolor=BG_APP,
                activebackground=BG_TOOL, activeforeground=FG_TEXT,
                command=self._load_current_slot,
            ).pack(side='left', padx=4)

        self._loc_lbl = tk.Label(bar, text='', bg=BG_TOOL, fg=ACC_BLUE,
                                  font=('TkFixedFont', 9))
        self._loc_lbl.pack(side='right', padx=10)

        # ── Three columns ─────────────────────────────────────────────────────
        body = tk.Frame(self, bg=BG_APP)
        body.pack(fill='both', expand=True, padx=6, pady=4)
        body.columnconfigure(0, weight=1, minsize=140)
        body.columnconfigure(1, weight=2, minsize=200)
        body.columnconfigure(2, weight=0, minsize=220)
        body.rowconfigure(0, weight=1)

        # ── Area list (left) ──────────────────────────────────────────────────
        left = tk.Frame(body, bg=BG_APP)
        left.grid(row=0, column=0, sticky='nsew', padx=(0, 4))
        left.rowconfigure(1, weight=1)
        left.columnconfigure(0, weight=1)

        tk.Label(left, text='Area', bg=BG_APP, fg=FG_DIM,
                 font=('TkDefaultFont', 9)).grid(row=0, column=0, sticky='w', pady=(0, 2))

        self._area_lb = tk.Listbox(
            left, bg=ROW_ODD, fg=FG_TEXT, selectbackground=ROW_SEL,
            selectforeground=FG_EDIT, relief='flat', activestyle='none',
            font=('TkFixedFont', 10), exportselection=False,
        )
        self._area_lb.grid(row=1, column=0, sticky='nsew')
        vsb_a = ttk.Scrollbar(left, orient='vertical', command=self._area_lb.yview)
        vsb_a.grid(row=1, column=1, sticky='ns')
        self._area_lb.configure(yscrollcommand=vsb_a.set)
        self._area_lb.bind('<<ListboxSelect>>', self._on_area_select)

        areas = all_areas()
        for i, a in enumerate(areas):
            self._area_lb.insert('end', f'  {a}')
            self._area_lb.itemconfig(i, bg=ROW_ODD if i % 2 == 0 else ROW_EVEN)

        # ── Room list (middle) ────────────────────────────────────────────────
        mid = tk.Frame(body, bg=BG_APP)
        mid.grid(row=0, column=1, sticky='nsew', padx=4)
        mid.rowconfigure(1, weight=1)
        mid.columnconfigure(0, weight=1)

        tk.Label(mid, text='Room', bg=BG_APP, fg=FG_DIM,
                 font=('TkDefaultFont', 9)).grid(row=0, column=0, sticky='w', pady=(0, 2))

        self._room_lb = tk.Listbox(
            mid, bg=ROW_ODD, fg=FG_TEXT, selectbackground=ROW_SEL,
            selectforeground=FG_EDIT, relief='flat', activestyle='none',
            font=('TkFixedFont', 10), exportselection=False,
        )
        self._room_lb.grid(row=1, column=0, sticky='nsew')
        vsb_r = ttk.Scrollbar(mid, orient='vertical', command=self._room_lb.yview)
        vsb_r.grid(row=1, column=1, sticky='ns')
        self._room_lb.configure(yscrollcommand=vsb_r.set)
        self._room_lb.bind('<<ListboxSelect>>', self._on_room_select)
        self._room_lb.bind('<Double-1>', lambda _e: self._do_warp())

        # ── Right panel ───────────────────────────────────────────────────────
        right = tk.Frame(body, bg=BG_PANEL, padx=12, pady=10)
        right.grid(row=0, column=2, sticky='nsew')

        # Current location readout
        tk.Label(right, text='Current location', bg=BG_PANEL, fg=FG_DIM,
                 font=('TkDefaultFont', 8)).pack(anchor='w')
        self._cur_area_lbl = tk.Label(right, text='—', bg=BG_PANEL, fg=FG_TEXT,
                                       font=('TkFixedFont', 11, 'bold'))
        self._cur_area_lbl.pack(anchor='w')
        self._cur_room_lbl = tk.Label(right, text='', bg=BG_PANEL, fg=FG_DIM,
                                       font=('TkFixedFont', 10))
        self._cur_room_lbl.pack(anchor='w', pady=(0, 8))

        # Target readout
        tk.Label(right, text='Warp target', bg=BG_PANEL, fg=FG_DIM,
                 font=('TkDefaultFont', 8)).pack(anchor='w')
        self._tgt_lbl = tk.Label(right, text='Select area + room →', bg=BG_PANEL,
                                  fg=ACC_BLUE, font=('TkFixedFont', 10),
                                  wraplength=190, justify='left')
        self._tgt_lbl.pack(anchor='w', pady=(0, 10))

        self._warp_btn = tk.Button(
            right, text='Warp  ↵', bg=BG_TOOL, fg=ACC_GRN,
            relief='flat', activebackground=ACC_GRN, activeforeground=BG_APP,
            font=('TkDefaultFont', 11, 'bold'), padx=10, pady=6,
            state='disabled', command=self._do_warp,
        )
        self._warp_btn.pack(anchor='w', fill='x', pady=(0, 12))

        ttk.Separator(right, orient='horizontal').pack(fill='x', pady=6)

        # Flags
        tk.Label(right, text='Flags', bg=BG_PANEL, fg=FG_DIM,
                 font=('TkDefaultFont', 8)).pack(anchor='w', pady=(0, 4))

        self._flag_vars = {}
        for key, vtype, label, tip in FLAGS:
            row = tk.Frame(right, bg=BG_PANEL)
            row.pack(fill='x', pady=1)
            var = tk.BooleanVar()
            self._flag_vars[key] = (var, vtype)
            cb = tk.Checkbutton(
                row, text=label, variable=var,
                bg=BG_PANEL, fg=FG_TEXT, selectcolor=BG_APP,
                activebackground=BG_PANEL, activeforeground=FG_TEXT,
                font=('TkDefaultFont', 10),
                command=lambda k=key: self._on_flag_toggle(k),
            )
            cb.pack(side='left')
            tk.Label(row, text=tip, bg=BG_PANEL, fg=FG_DIM,
                     font=('TkDefaultFont', 7)).pack(side='left', padx=4)

        # ── Status bar ────────────────────────────────────────────────────────
        self._status = tk.Label(self, text='Ready', bg=BG_TOOL, fg=FG_DIM,
                                 anchor='w', padx=8, font=('TkDefaultFont', 9))
        self._status.pack(side='bottom', fill='x')

        # Selection state
        self._selected_area = None
        self._selected_room = None

    # ── Data loading ──────────────────────────────────────────────────────────

    def _load_current_slot(self):
        slot = self._slot.get()
        path = save_path(slot)
        try:
            self._entries = load_slot(slot)
        except Exception as e:
            self._entries = []
            self._set_status(f'Could not load save{slot}: {e}')
            return

        e_folder = get_entry(self._entries, 'folder')
        e_file   = get_entry(self._entries, 'file')
        cur_area = e_folder[2] if e_folder else '?'
        cur_room = e_file[2]   if e_file   else '?'

        self._cur_area_lbl.config(text=cur_area)
        self._cur_room_lbl.config(text=cur_room)
        self._loc_lbl.config(text=f'save{slot}: {cur_area} / {cur_room}')

        # Highlight current area in list
        areas = all_areas()
        if cur_area in areas:
            idx = areas.index(cur_area)
            self._area_lb.selection_clear(0, 'end')
            self._area_lb.selection_set(idx)
            self._area_lb.see(idx)
            self._populate_rooms(cur_area)

            # Highlight current room
            rooms = list_rooms(cur_area)
            if cur_room in rooms:
                ridx = rooms.index(cur_room)
                self._room_lb.selection_clear(0, 'end')
                self._room_lb.selection_set(ridx)
                self._room_lb.see(ridx)
                self._selected_area = cur_area
                self._selected_room = cur_room
                self._update_target_label()

        # Update flag checkboxes
        for key, (var, vtype) in self._flag_vars.items():
            e = get_entry(self._entries, key)
            if e and e[1] == 1:
                var.set(float(e[2]) != 0.0)
            else:
                var.set(False)

        self._set_status(f'Loaded save{slot}  ({cur_area}/{cur_room})')

    def _populate_rooms(self, area: str):
        self._room_lb.delete(0, 'end')
        for i, room in enumerate(list_rooms(area)):
            self._room_lb.insert('end', f'  {room}')
            self._room_lb.itemconfig(i, bg=ROW_ODD if i % 2 == 0 else ROW_EVEN)

    # ── Event handlers ────────────────────────────────────────────────────────

    def _on_area_select(self, _event=None):
        sel = self._area_lb.curselection()
        if not sel:
            return
        area = all_areas()[sel[0]]
        self._selected_area = area
        self._selected_room = None
        self._populate_rooms(area)
        self._update_target_label()
        self._warp_btn.config(state='disabled')

    def _on_room_select(self, _event=None):
        sel = self._room_lb.curselection()
        if not sel or self._selected_area is None:
            return
        room = list_rooms(self._selected_area)[sel[0]]
        self._selected_room = room
        self._update_target_label()
        self._warp_btn.config(state='normal')

    def _update_target_label(self):
        area = self._selected_area or '—'
        room = self._selected_room or '(pick a room)'
        self._tgt_lbl.config(text=f'{area} / {room}')

    def _on_flag_toggle(self, key: str):
        if not self._entries:
            return
        var, vtype = self._flag_vars[key]
        val = 1.0 if var.get() else 0.0
        set_entry(self._entries, key, vtype, val)
        slot = self._slot.get()
        try:
            write_slot(slot, self._entries)
            self._set_status(f'Saved: {key} = {int(val)}  (save{slot})')
        except Exception as e:
            self._set_status(f'Error saving flag: {e}')

    def _do_warp(self):
        area = self._selected_area
        room = self._selected_room
        if not area or not room:
            return

        slot = self._slot.get()
        if not self._entries:
            self._set_status('No save loaded.')
            return

        exact = KNOWN_EXACT.get((area, room))
        if exact:
            mx, my = exact
        else:
            mx, my = AREA_CENTER.get(area, (50, 30))

        mapload = f'./data\\lvl\\{area}\\map.file'

        set_entry(self._entries, 'folder',   2, area)
        set_entry(self._entries, 'file',     2, room)
        set_entry(self._entries, 'mapload',  2, mapload)
        set_entry(self._entries, 'position', 2, '512,512')
        set_entry(self._entries, 'mapx',     1, float(mx))
        set_entry(self._entries, 'mapy',     1, float(my))
        set_entry(self._entries, 'facing',   1, 1.0)

        frame_id = AREA_FRAME.get(area)
        if frame_id is not None:
            set_entry(self._entries, 'areacheck', 2, str(frame_id))
            # Update the last comma-separated field of 'status' to match.
            e_status = get_entry(self._entries, 'status')
            if e_status:
                parts = e_status[2].split(',')
                parts[-1] = str(frame_id)
                e_status[2] = ','.join(parts)

        try:
            write_slot(slot, self._entries)
        except Exception as e:
            messagebox.showerror('Warp failed', str(e))
            return

        self._cur_area_lbl.config(text=area)
        self._cur_room_lbl.config(text=room)
        self._loc_lbl.config(text=f'save{slot}: {area} / {room}')
        self._set_status(f'Warped save{slot} → {area}/{room}  ·  load that save in-game')

    def _set_status(self, msg: str):
        self._status.config(text=msg)


if __name__ == '__main__':
    app = WarpGUI()
    app.mainloop()
