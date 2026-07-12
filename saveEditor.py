#!/usr/bin/env python3
"""
saveEditor.py — Interactive GUI editor for Iconoclasts MAP1.0 save files.

Usage:
    python3 saveEditor.py [save_file]
    python3 saveEditor.py ~/.local/share/Steam/steamapps/common/Iconoclasts/data/point
    python3 saveEditor.py ~/.local/share/Steam/steamapps/common/Iconoclasts/data/save1

Controls:
    Click row           — select entry
    Double-click row    — edit value inline
    Toggle button       — flip 0.0 ↔ 1.0 for numeric flags
    Search box          — filter by key name
    Save button         — write changes back to file (makes .bak backup first)
    Ctrl+S              — save
    Ctrl+O              — open file
"""

import argparse
import os
import shutil
import struct
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog


import platform
if platform.system() == 'Windows':
    SAVE_ROOT = os.path.expandvars(r'%PROGRAMFILES(X86)%\Steam\steamapps\common\Iconoclasts\data')
else:
    SAVE_ROOT = os.path.expanduser('~/.local/share/Steam/steamapps/common/Iconoclasts/data')

# ── Colour scheme (matches lvlInspector palette) ──────────────────────────────
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
ROW_MOD  = '#3a2a1a'


# ── MAP1.0 parser / serialiser ────────────────────────────────────────────────

def parse_map10(data: bytes):
    """Parse MAP1.0 binary into ordered list of (key, vtype, value) tuples."""
    if data[:6] != b'MAP1.0':
        raise ValueError(f'Not a MAP1.0 file (magic={data[:6]!r})')
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
            raise ValueError(f'Unknown value type {vtype} for key {key!r}')
        entries.append([key, vtype, val])
    return entries


def serialise_map10(entries) -> bytes:
    """Serialise entry list back to MAP1.0 binary."""
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


# ── Helper: classify entries for colour-coding ────────────────────────────────

def entry_category(key: str):
    if key.startswith('-'):        return 'event'
    if key.startswith('tweak_'):   return 'tweak'
    if key.startswith('boulders+') or key.startswith('chest+') \
            or key.startswith('lock+') or key.startswith('key+') \
            or key.startswith('boxkey+') or key.endswith('+roadblock') \
            or key.startswith('keymaster+') or key.startswith('chestunlock+'):
        return 'world_obj'
    if key.endswith('_map') or key.endswith('_loot'): return 'map'
    if key in ('folder', 'file', 'position', 'mapload', 'mapx', 'mapy',
               'facing', 'status', 'areacheck', 'time', 'lastsaveslot'):
        return 'location'
    if key.startswith('bgm_') or key == 'newsong' or key == 'last_song' \
            or key == 'bgm_lock' or key == 'bgm_freq' or key == 'bgm_channel':
        return 'audio'
    if key in ('wrenchplus', 'gotawrench', 'ability1', 'ability2', 'ability3',
               'warps', 'collection', 'collectsize', 'quads', 'all_loot',
               'all_schematics', 'bullets', 'stackslot1', 'stackslot2',
               'stackslot3', 'stackslots', 'stackcharge', 'stackactive',
               'tools', 'powerups', 'gun_used', 'gunpower', 'defense',
               'cooldown', 'keys', 'party', 'party_check', 'contrastock1'):
        return 'player'
    if key.startswith('stack') or key.startswith('ability') \
            or key.startswith('damage'): return 'player'
    return 'misc'

CAT_COLORS = {
    'event':    '#cc9944',   # amber
    'tweak':    '#44aacc',   # sky blue
    'world_obj':'#9966cc',   # purple
    'map':      '#44bb88',   # teal
    'location': '#cc4488',   # pink
    'audio':    '#8888cc',   # lavender
    'player':   '#88cc44',   # lime
    'misc':     '#7070a0',   # dim
}


# ── Main application ──────────────────────────────────────────────────────────

class SaveEditor(tk.Tk):
    def __init__(self, initial_path=None):
        super().__init__()
        self.title('SaveEditor — Iconoclasts save file editor')
        self.geometry('1100x720')
        self.minsize(700, 400)
        self.configure(bg=BG_APP)

        self._filepath  = None
        self._entries   = []      # list of [key, vtype, value]  (mutable)
        self._modified  = set()   # indices of modified entries
        self._filter    = tk.StringVar()
        self._filter.trace_add('write', self._on_filter_change)
        self._shown_indices = []  # entry indices currently visible in tree

        self._build_ui()
        self.bind('<Control-o>', lambda e: self._open_file())
        self.bind('<Control-s>', lambda e: self._save_file())

        if initial_path:
            self._load(initial_path)
        else:
            self._prompt_open()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Toolbar ───────────────────────────────────────────────────────────
        bar = tk.Frame(self, bg=BG_TOOL, pady=4)
        bar.pack(side='top', fill='x')

        tk.Button(bar, text='Open', bg=BG_TOOL, fg=FG_TEXT, relief='flat',
                  activebackground=ACC_BLUE, command=self._open_file,
                  padx=10).pack(side='left', padx=4)
        tk.Button(bar, text='Save', bg=BG_TOOL, fg=ACC_GRN, relief='flat',
                  activebackground=ACC_GRN, command=self._save_file,
                  padx=10).pack(side='left', padx=4)

        tk.Label(bar, text='Filter:', bg=BG_TOOL, fg=FG_DIM).pack(side='left', padx=(12,2))
        self._filter_entry = tk.Entry(bar, textvariable=self._filter,
                                      bg=BG_PANEL, fg=FG_TEXT, insertbackground=FG_TEXT,
                                      relief='flat', width=30)
        self._filter_entry.pack(side='left', padx=2)
        tk.Button(bar, text='✕', bg=BG_TOOL, fg=FG_DIM, relief='flat',
                  command=lambda: self._filter.set(''),
                  padx=4).pack(side='left')

        # Category legend
        for cat, col in [('event', CAT_COLORS['event']),
                         ('tweak', CAT_COLORS['tweak']),
                         ('player', CAT_COLORS['player']),
                         ('location', CAT_COLORS['location']),
                         ('world', CAT_COLORS['world_obj']),
                         ('map', CAT_COLORS['map']),
                         ('audio', CAT_COLORS['audio'])]:
            tk.Label(bar, text=f'● {cat}', bg=BG_TOOL, fg=col,
                     font=('TkDefaultFont', 8)).pack(side='right', padx=4)

        self._title_lbl = tk.Label(bar, text='No file loaded',
                                   bg=BG_TOOL, fg=FG_DIM)
        self._title_lbl.pack(side='left', padx=16)

        # ── Main split: tree + detail panel ──────────────────────────────────
        paned = tk.PanedWindow(self, orient='horizontal', bg=BG_APP,
                               sashwidth=4, sashrelief='flat')
        paned.pack(fill='both', expand=True, padx=4, pady=4)

        # Left: treeview
        left = tk.Frame(paned, bg=BG_APP)
        paned.add(left, minsize=500)

        cols = ('key', 'type', 'value')
        style = ttk.Style()
        style.theme_use('default')
        style.configure('Save.Treeview',
                        background=ROW_ODD, foreground=FG_TEXT,
                        fieldbackground=ROW_ODD, rowheight=22,
                        font=('TkFixedFont', 10))
        style.configure('Save.Treeview.Heading',
                        background=BG_TOOL, foreground=FG_DIM, relief='flat')
        style.map('Save.Treeview',
                  background=[('selected', ROW_SEL)],
                  foreground=[('selected', FG_EDIT)])

        self._tree = ttk.Treeview(left, columns=cols, show='headings',
                                  style='Save.Treeview', selectmode='browse')
        self._tree.heading('key',   text='Key',   anchor='w')
        self._tree.heading('type',  text='T',     anchor='center')
        self._tree.heading('value', text='Value', anchor='w')
        self._tree.column('key',   width=260, stretch=False)
        self._tree.column('type',  width=30,  stretch=False, anchor='center')
        self._tree.column('value', width=340)

        vsb = ttk.Scrollbar(left, orient='vertical',   command=self._tree.yview)
        hsb = ttk.Scrollbar(left, orient='horizontal', command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self._tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        left.grid_rowconfigure(0, weight=1)
        left.grid_columnconfigure(0, weight=1)

        self._tree.bind('<<TreeviewSelect>>', self._on_select)
        self._tree.bind('<Double-1>',         self._on_double_click)
        self._tree.bind('<Return>',           self._on_double_click)

        # (Moved to after self._val_entry is created)

        # Tag colours for categories
        for cat, col in CAT_COLORS.items():
            self._tree.tag_configure(cat, foreground=col)
        self._tree.tag_configure('modified', background=ROW_MOD)
        self._tree.tag_configure('even_row', background=ROW_EVEN)

        # Right: detail / edit panel
        right = tk.Frame(paned, bg=BG_PANEL, padx=12, pady=10)
        paned.add(right, minsize=220)

        tk.Label(right, text='Selected entry', bg=BG_PANEL, fg=FG_DIM,
                 font=('TkDefaultFont', 9)).pack(anchor='w')

        self._detail_key = tk.Label(right, text='', bg=BG_PANEL, fg=FG_TEXT,
                                    font=('TkFixedFont', 11, 'bold'),
                                    wraplength=200, justify='left')
        self._detail_key.pack(anchor='w', pady=(2,8))

        tk.Label(right, text='Value', bg=BG_PANEL, fg=FG_DIM,
                 font=('TkDefaultFont', 9)).pack(anchor='w')
        self._val_var = tk.StringVar()
        self._val_entry = tk.Entry(right, textvariable=self._val_var,
                       bg=BG_APP, fg=FG_EDIT, insertbackground=FG_EDIT,
                       relief='flat', font=('TkFixedFont', 11),
                       width=24)
        self._val_entry.pack(anchor='w', fill='x', pady=2)
        self._val_entry.bind('<Return>', self._commit_edit)
        # Ensure value entry is always enabled and editable (now safe)
        self._val_entry.config(state='normal')

        self._type_lbl = tk.Label(right, text='', bg=BG_PANEL, fg=FG_DIM,
                                  font=('TkDefaultFont', 9))
        self._type_lbl.pack(anchor='w', pady=(0,8))

        self._toggle_btn = tk.Button(right, text='Toggle  0 ↔ 1',
                                     bg=BG_TOOL, fg=ACC_YLW, relief='flat',
                                     activebackground=ACC_YLW, padx=8,
                                     command=self._toggle_value)
        self._toggle_btn.pack(anchor='w', pady=2)

        self._commit_btn = tk.Button(right, text='Apply  ↵',
                                     bg=BG_TOOL, fg=ACC_GRN, relief='flat',
                                     activebackground=ACC_GRN, padx=8,
                                     command=self._commit_edit)
        self._commit_btn.pack(anchor='w', pady=2)

        ttk.Separator(right, orient='horizontal').pack(fill='x', pady=10)

        self._status_lbl = tk.Label(right, text='', bg=BG_PANEL, fg=FG_DIM,
                                    wraplength=200, justify='left',
                                    font=('TkDefaultFont', 8))
        self._status_lbl.pack(anchor='w')

        # Bottom status bar
        self._statusbar = tk.Label(self, text='', bg=BG_TOOL, fg=FG_DIM,
                                   anchor='w', padx=8)
        self._statusbar.pack(side='bottom', fill='x')

    # ── File I/O ──────────────────────────────────────────────────────────────

    def _prompt_open(self):
        saves = ['point', 'save1', 'save2', 'save3']
        paths = [os.path.join(SAVE_ROOT, s) for s in saves]
        existing = [p for p in paths if os.path.exists(p)]
        if existing:
            self._load(existing[0])
        else:
            self._open_file()

    def _open_file(self):
        path = filedialog.askopenfilename(
            title='Open save file',
            initialdir=SAVE_ROOT if os.path.isdir(SAVE_ROOT) else os.path.expanduser('~'),
            filetypes=[('Iconoclasts save files', 'point save1 save2 save3'),
                       ('All files', '*')],
        )
        if path:
            self._load(path)

    def _load(self, path):
        try:
            with open(path, 'rb') as f:
                data = f.read()
            self._entries = parse_map10(data)
            self._modified.clear()
            self._filepath = path
            name = os.path.basename(path)
            self._title_lbl.config(text=name)
            self.title(f'SaveEditor — {name}')
            self._rebuild_tree()
            n = len(self._entries)
            self._set_status(f'Loaded {n} entries from {name}')
        except Exception as e:
            messagebox.showerror('Load error', str(e))

    def _save_file(self):
        if not self._filepath:
            return
        if not self._modified:
            self._set_status('No changes to save.')
            return
        # Backup
        bak = self._filepath + '.bak'
        try:
            shutil.copy2(self._filepath, bak)
        except Exception as e:
            if not messagebox.askyesno('Backup failed',
                                       f'Could not write backup:\n{e}\n\nSave anyway?'):
                return
        try:
            data = serialise_map10(self._entries)
            with open(self._filepath, 'wb') as f:
                f.write(data)
            n = len(self._modified)
            self._modified.clear()
            self._rebuild_tree()
            self._set_status(f'Saved {n} change(s). Backup: {os.path.basename(bak)}')
        except Exception as e:
            messagebox.showerror('Save error', str(e))

    # ── Tree management ───────────────────────────────────────────────────────

    def _rebuild_tree(self):
        self._tree.delete(*self._tree.get_children())
        self._shown_indices = []
        filt = self._filter.get().lower()
        row = 0
        for i, (key, vtype, val) in enumerate(self._entries):
            if filt and filt not in key.lower():
                continue
            tags = [entry_category(key)]
            if i in self._modified:
                tags.append('modified')
            elif row % 2 == 0:
                tags.append('even_row')
            type_str = 'f' if vtype == 1 else 's'
            disp_val = _fmt_val(val, vtype)
            self._tree.insert('', 'end', iid=str(i),
                               values=(key, type_str, disp_val),
                               tags=tuple(tags))
            self._shown_indices.append(i)
            row += 1
        self._set_status(f'Showing {len(self._shown_indices)} / {len(self._entries)} entries'
                         + (f'  (filter: {filt!r})' if filt else ''))

    def _on_filter_change(self, *_):
        self._rebuild_tree()

    # ── Selection / editing ───────────────────────────────────────────────────

    def _on_select(self, _event=None):
        sel = self._tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        key, vtype, val = self._entries[idx]
        self._detail_key.config(text=key)
        self._val_var.set(str(val))
        tname = 'double (f64)' if vtype == 1 else 'string'
        self._type_lbl.config(text=f'Type: {tname}  [{entry_category(key)}]')
        self._toggle_btn.config(state='normal' if vtype == 1 else 'disabled')
        # Always enable and focus the value entry on selection
        self._val_entry.config(state='normal')
        self._val_entry.focus_set()
        self._val_entry.select_range(0, 'end')

    def _on_double_click(self, _event=None):
        sel = self._tree.selection()
        if not sel:
            return
        self._val_entry.config(state='normal')
        self._val_entry.focus_set()
        self._val_entry.select_range(0, 'end')

    def _commit_edit(self, _event=None):
        sel = self._tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        key, vtype, _ = self._entries[idx]
        new_str = self._val_var.get()
        try:
            if vtype == 1:
                new_val = float(new_str)
            else:
                new_val = new_str
        except ValueError:
            messagebox.showerror('Invalid value',
                                 f'Cannot convert {new_str!r} to float for key {key!r}')
            return
        self._entries[idx][2] = new_val
        self._modified.add(idx)
        self._refresh_row(idx)
        self._set_status(f'Modified: {key!r}  →  {new_val!r}  (unsaved)')

    def _toggle_value(self):
        sel = self._tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        key, vtype, val = self._entries[idx]
        if vtype != 1:
            return
        new_val = 0.0 if float(val) != 0.0 else 1.0
        self._entries[idx][2] = new_val
        self._modified.add(idx)
        self._val_var.set(str(new_val))
        self._refresh_row(idx)
        self._set_status(f'Toggled: {key!r}  →  {new_val}  (unsaved)')

    def _refresh_row(self, idx):
        key, vtype, val = self._entries[idx]
        tags = [entry_category(key), 'modified']
        disp = _fmt_val(val, vtype)
        self._tree.item(str(idx), values=(key, 'f' if vtype == 1 else 's', disp),
                        tags=tuple(tags))

    # ── Status bar ────────────────────────────────────────────────────────────

    def _set_status(self, msg):
        self._statusbar.config(text=msg)
        self._status_lbl.config(text=msg)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fmt_val(val, vtype):
    """Format a value for display in the tree."""
    if vtype == 1:
        f = float(val)
        # Show as integer if it's a whole number
        if f == int(f) and abs(f) < 1e12:
            return str(int(f))
        return f'{f:.6g}'
    s = str(val)
    # Truncate very long strings (map tile lists etc.)
    if len(s) > 80:
        return s[:77] + '…'
    return s


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description='Iconoclasts save file editor')
    ap.add_argument('path', nargs='?', help='Save file to open (point/save1/save2/save3)')
    args = ap.parse_args()

    path = None
    if args.path:
        # Accept bare names like "save1" as well as full paths
        if not os.path.isabs(args.path) and not os.path.exists(args.path):
            candidate = os.path.join(SAVE_ROOT, args.path)
            if os.path.exists(candidate):
                path = candidate
            else:
                path = args.path
        else:
            path = args.path

    app = SaveEditor(initial_path=path)
    app.mainloop()


if __name__ == '__main__':
    main()
