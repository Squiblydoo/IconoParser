## UI Libraries
from tkinter import *
from tkinter import ttk
import tkinter.scrolledtext as st
from tkinterdnd2 import DND_FILES, TkinterDnD
from tkinter import filedialog, simpledialog, messagebox
import struct
import binascii


class main_window(TkinterDnD.Tk):
    """Scaffold Level Editor GUI.

    This window loads a level file and will parse it according to a
    pattern you provide. Right now parsing is a placeholder; when
    you provide the pattern I will implement the parsing logic.
    """

    def __init__(self):
        TkinterDnD.Tk.__init__(self)
        self.geometry("700x600")
        self.title("IconoParser - Level Editor")

        # Storage for parsed level data (list of lists / frames)
        self.level_data = []
        self.current_index = 0

        # Menu
        menu = Menu(self)
        self.config(menu=menu)
        file_menu = Menu(menu, tearoff=0)
        menu.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Level File", command=self.openFile)
        file_menu.add_command(label="Close File", command=self.closeFile)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)

        # Tree to show parsed hierarchical entries
        treeFrame = Frame(self)
        treeFrame.pack(pady=10, fill=BOTH, expand=True)

        # Notebook to show each parsed part as its own page
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(pady=8, fill=BOTH, expand=True)

        self.table = ttk.Treeview(treeFrame, columns=("name", "info", "value"), show='tree headings', height=20)
        self.table.heading('#0', text='')
        self.table.heading('name', text='Name')
        self.table.heading('info', text='Info')
        self.table.heading('value', text='Value')
        self.table.column('name', width=220)
        self.table.column('info', width=220)
        self.table.column('value', width=220)
        self.table.pack(fill=BOTH, expand=True)
        self.table.bind('<Double-1>', self.on_tree_double_click)

        # remove older per-layer table; notebook tabs will host per-part tables

        # mapping node id -> path in parsed dict
        self.node_map = {}
        self.parsed = None

        # Controls
        ctl_frame = Frame(self)
        ctl_frame.pack(pady=6)
        self.prev_btn = Button(ctl_frame, text="Previous", command=self.previous_item)
        self.prev_btn.grid(row=0, column=0, padx=4)
        self.next_btn = Button(ctl_frame, text="Next", command=self.next_item)
        self.next_btn.grid(row=0, column=1, padx=4)

        # Placeholder export / parse buttons
        # Reparse uses the embedded pattern (no user-provided pattern required)
        self.request_pattern_btn = Button(ctl_frame, text="Parse (use built-in pattern)", command=self.parse_with_pattern)
        self.request_pattern_btn.grid(row=0, column=2, padx=8)
        self.export_btn = Button(ctl_frame, text="Export Binary", command=self.export_binary)
        self.export_btn.grid(row=0, column=3, padx=8)

    def openFile(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.processFileUpload(file_path)

    def closeFile(self):
        self.level_data = []
        self.current_index = 0
        self.table.delete(*self.table.get_children())

    def processFileUpload(self, event):
        # Accept either an event or a file path string
        try:
            file_path = event.data
        except Exception:
            file_path = event

        if file_path and file_path[0] == '{' and file_path[-1] == '}':
            file_path = file_path[1:-1]

        # Placeholder read: store raw lines until we have a pattern
        try:
            with open(file_path, 'rb') as f:
                raw = f.read()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file: {e}")
            return

        # For now keep the raw bytes as a single item in level_data and auto-parse
        self.level_data = [[raw]]
        self.current_index = 0
        # parse using the built-in pattern and populate UI tabs
        self.parse_with_pattern()

    def request_pattern(self):
        """Trigger parsing using the embedded parse pattern (no user input required)."""
        self.parse_with_pattern()

    def parse_with_pattern(self):
        """Parse the loaded level file according to the pattern you supplied.

        The parsing implemented here follows the structure you provided:
        arr_hdr_t { magic:u64, version_minor:u16, level[5], unknown[1], level2[2], unknown2[1], level3[1], hr_s[1], sm[2] }

        Notes:
        - Assumes little-endian encoding for integers (common for game files).
        - If your files are big-endian, change the `endian` variable to '>' below.
        - This function parses into Python dicts/lists and replaces self.level_data
          with a summary list usable by the UI.
        """
        if not self.level_data or not self.level_data[0]:
            messagebox.showwarning("No data", "No file loaded to parse.")
            return

        raw = self.level_data[0][0]
        endian = '<'  # change to '>' for big-endian
        off = 0

        def read(fmt):
            nonlocal off
            size = struct.calcsize(fmt)
            val = struct.unpack_from(endian + fmt, raw, off)
            off += size
            return val if len(val) > 1 else val[0]

        def read_u8():
            return read('B')

        def read_u16():
            return read('H')

        def read_u32():
            return read('I')

        def read_u64():
            return read('Q')

        def read_bytes(n):
            nonlocal off
            b = raw[off:off + n]
            off += n
            return b

        def parse_level_contents():
            # struct level_contents { u32 size; data level[size]; }
            start = off
            size = read_u32()
            items = []
            for _ in range(size):
                d1 = read_u64()
                d2 = read_u64()
                items.append({'data1': d1, 'data2': d2})
            # preserve original raw bytes for this block so we can do bit-for-bit export if unchanged
            raw_slice = raw[start:off]
            return {'size': size, 'level': items, '_orig_bytes': raw_slice}

        def parse_chunk_default():
            # chunk: u32 head; u32 type; u32 section_size; then conditional
            start = off
            head = read_u32()
            typ = read_u32()
            section_size = read_u32()
            extra = None
            if typ == 0:
                extra = {'dunno': read_u32()}
            elif typ == 2:
                extra = {'section': read_bytes(section_size)}
            raw_slice = raw[start:off]
            return {'head': head, 'type': typ, 'section_size': section_size, 'extra': extra, '_orig_bytes': raw_slice}

        def parse_chunk_new_unknown():
            # same layout as default chunks in this pattern
            return parse_chunk_default()

        def parse_chunk_sm():
            start = off
            head = read_u32()
            typ = read_u32()
            extra = None
            if typ == 0:
                section_size = read_u32()
                dunno = read_u32()
                extra = {'section_size': section_size, 'dunno': dunno}
            elif typ == 2:
                section_size = read_u32()
                section = read_bytes(section_size)
                # If section_size > 1 this appears to be textual in many files; keep both
                # the raw bytes and a decoded text form for UI convenience.
                section_text = None
                if section_size > 0 and section:
                    try:
                        # decode up to the first NUL for readability
                        section_text = section.split(b'\x00', 1)[0].decode('utf-8', errors='replace')
                    except Exception:
                        section_text = None
                extra = {'section_size': section_size, 'section': section, 'section_text': section_text}
            raw_slice = raw[start:off]
            return {'head': head, 'type': typ, 'extra': extra, '_orig_bytes': raw_slice}

        parsed = {}
        try:
            parsed['magic_number'] = read_u64()
            parsed['version_minor'] = read_u16()

            # parse level[5]
            parsed['level'] = [parse_level_contents() for _ in range(5)]

            # unknown::data (array of 1)
            # struct data { u32 size; unk_chunk chunks[2]; unk_data data[size - 2]; }
            def parse_unknown_data():
                start = off
                size = read_u32()
                chunks = [parse_chunk_default() for _ in range(2)]
                data_entries = []
                for _ in range(max(0, size - 2)):
                    d1 = read_u64()
                    d2 = read_u64()
                    data_entries.append({'data1': d1, 'data2': d2})
                raw_slice = raw[start:off]
                return {'size': size, 'chunks': chunks, 'data': data_entries, '_orig_bytes': raw_slice}

            parsed['unknown'] = [parse_unknown_data() for _ in range(1)]

            # level2[2]
            parsed['level2'] = [parse_level_contents() for _ in range(2)]

            # new_unknown::unk_data { u32 size; chunks dunno[2]; chunks unk[size - 2]; }
            def parse_new_unknown():
                start = off
                size = read_u32()
                dunno = [parse_chunk_new_unknown() for _ in range(2)]
                unk = [parse_chunk_new_unknown() for _ in range(max(0, size - 2))]
                raw_slice = raw[start:off]
                return {'size': size, 'dunno': dunno, 'unk': unk, '_orig_bytes': raw_slice}

            parsed['unknown2'] = [parse_new_unknown() for _ in range(1)]

            # level3[1]
            parsed['level3'] = [parse_level_contents() for _ in range(1)]

            # hr::unk_data (same chunk layout as new_unknown)
            def parse_hr():
                start = off
                size = read_u32()
                dunno = [parse_chunk_default() for _ in range(2)]
                unk = [parse_chunk_default() for _ in range(max(0, size - 2))]
                raw_slice = raw[start:off]
                return {'size': size, 'dunno': dunno, 'unk': unk, '_orig_bytes': raw_slice}

            parsed['hr_s'] = [parse_hr() for _ in range(1)]

            # sm::unk_data with sm-specific chunks
            def parse_sm():
                start = off
                size = read_u32()
                dunno = [parse_chunk_sm() for _ in range(2)]
                unk = [parse_chunk_sm() for _ in range(max(0, size - 2))]
                raw_slice = raw[start:off]
                return {'size': size, 'dunno': dunno, 'unk': unk, '_orig_bytes': raw_slice}

            parsed['sm'] = [parse_sm() for _ in range(2)]

        except struct.error as e:
            messagebox.showerror("Parse error", f"Failed to parse file: {e}\nOffset: {off}")
            return

        # Convert parsed data into UI-friendly list: show section summaries
        ui_list = []
        ui_list.append(("hdr", f"magic=0x{parsed['magic_number']:016x}", f"version={parsed['version_minor']}"))
        for i, lvl in enumerate(parsed['level']):
            ui_list.append((f"level[{i}]", f"count={lvl['size']}", f"first={lvl['level'][0] if lvl['level'] else ''}"))
        ui_list.append(("unknown", f"size={parsed['unknown'][0]['size']}", "chunks/entries"))
        for i, lvl in enumerate(parsed['level2']):
            ui_list.append((f"level2[{i}]", f"count={lvl['size']}", ""))
        ui_list.append(("unknown2", f"size={parsed['unknown2'][0]['size']}", "chunks"))
        ui_list.append(("level3", f"count={parsed['level3'][0]['size']}", ""))
        ui_list.append(("hr_s", f"size={parsed['hr_s'][0]['size']}", ""))
        for i, s in enumerate(parsed['sm']):
            ui_list.append((f"sm[{i}]", f"size={s['size']}", ""))
        # Store the full parsed object for editing/export and populate tree
        # Add friendly aliases for UI clarity (keep originals for compatibility)
        parsed['render_group'] = parsed.get('hr_s')
        parsed['spatial_meta'] = parsed.get('sm')
        parsed['objects'] = parsed.get('level')
        parsed['objects2'] = parsed.get('level2')
        parsed['objects3'] = parsed.get('level3')
        parsed['unknown_data'] = parsed.get('unknown')
        parsed['unknown2_data'] = parsed.get('unknown2')

        self.parsed = parsed
        # also keep a simple UI list for backward compatibility in navigation
        self.level_data = [[(a, b, c) for (a, b, c) in ui_list]]
        self.current_index = 0
        self.populate_tree_from_parsed()
        # build notebook tabs now that we have parsed data
        self.build_tabs()

    def load_current(self):
        # For compatibility: show the simple summary if parsed is not present
        if not self.parsed:
            self.table.delete(*self.table.get_children())
            if not self.level_data:
                return
            current = self.level_data[self.current_index]
            for entry in current:
                if isinstance(entry, bytes):
                    a = entry.hex()[:64]
                    b = ""
                    c = ""
                elif isinstance(entry, (list, tuple)):
                    a = str(entry[0]) if len(entry) > 0 else ""
                    b = str(entry[1]) if len(entry) > 1 else ""
                    c = str(entry[2]) if len(entry) > 2 else ""
                else:
                    a = str(entry)
                    b = ""
                    c = ""
                self.table.insert('', 'end', values=(a, b, c))
        else:
            # If we have a parsed structure, repopulate the hierarchical tree
            self.populate_tree_from_parsed()

    def populate_tree_from_parsed(self):
        """Populate the Treeview with the hierarchical parsed data.

        Uses self.parsed and creates nodes mapping back to the parsed structure
        via self.node_map where values are tuples representing the path within
        the parsed dict/list (e.g. ('level', 0, 'level', 1, 'data1')).
        """
        self.table.delete(*self.table.get_children())
        self.node_map.clear()

        def add_node(parent, name, obj, path):
            # display string for object
            if isinstance(obj, dict):
                display = ''
            elif isinstance(obj, list):
                display = f'len={len(obj)}'
            elif isinstance(obj, bytes):
                display = obj.hex()[:64]
            else:
                display = str(obj)

            node_id = self.table.insert(parent, 'end', text='', values=(name, display, display))
            self.node_map[node_id] = path
            # recurse
            if isinstance(obj, dict):
                for k, v in obj.items():
                    add_node(node_id, str(k), v, path + (k,))
            elif isinstance(obj, list):
                for idx, v in enumerate(obj):
                    add_node(node_id, f'[{idx}]', v, path + (idx,))

        # start from top-level parsed dict
        if not isinstance(self.parsed, dict):
            return
        root_id = self.table.insert('', 'end', text='', values=('root', '', ''))
        self.node_map[root_id] = ()
        for k, v in self.parsed.items():
            add_node(root_id, str(k), v, (k,))
        # expand top level
        self.table.item(root_id, open=True)

    def build_tabs(self):
        """Create notebook tabs for each top-level part of the parsed structure."""
        # clear existing tabs
        for tab in self.notebook.tabs():
            self.notebook.forget(tab)

        if not self.parsed:
            return
        # Header tab
        hdr_frame = Frame(self.notebook)
        hdr_tree = ttk.Treeview(hdr_frame, columns=('field', 'value'), show='headings')
        hdr_tree.heading('field', text='Field')
        hdr_tree.heading('value', text='Value')
        hdr_tree.pack(fill=BOTH, expand=True)
        hdr_tree.insert('', 'end', values=('magic_number', f'0x{self.parsed.get("magic_number",0):016x}'))
        hdr_tree.insert('', 'end', values=('version_minor', str(self.parsed.get('version_minor', 0))))
        self.notebook.add(hdr_frame, text='Header')

        # Entity Inspector tab: lets the user pick an index and see all per-layer values
        try:
            total = self.parsed.get('level', [])[0]['size']
        except Exception:
            total = 0
        insp_frame = Frame(self.notebook)
        ctl = Frame(insp_frame)
        ctl.pack(fill=X, pady=4)
        Label(ctl, text='Index:').pack(side=LEFT, padx=(6,4))
        self.inspector_spin = Spinbox(ctl, from_=0, to=max(0, total-1), width=8)
        self.inspector_spin.pack(side=LEFT)
        def _prev():
            try:
                v = int(self.inspector_spin.get())
            except Exception:
                v = 0
            v = max(0, v-1)
            self.inspector_spin.delete(0, 'end')
            self.inspector_spin.insert(0, str(v))
            populate(int(v))
        def _next():
            try:
                v = int(self.inspector_spin.get())
            except Exception:
                v = 0
            v = min(max(0, total-1), v+1)
            self.inspector_spin.delete(0, 'end')
            self.inspector_spin.insert(0, str(v))
            populate(int(v))
        Button(ctl, text='Prev', command=_prev).pack(side=LEFT, padx=4)
        Button(ctl, text='Next', command=_next).pack(side=LEFT)

        self.inspector_tree = ttk.Treeview(insp_frame, columns=('layer', 'value'), show='headings')
        self.inspector_tree.heading('layer', text='Layer')
        self.inspector_tree.heading('value', text='Value')
        self.inspector_tree.column('layer', width=240)
        self.inspector_tree.column('value', width=420)
        self.inspector_tree.pack(fill=BOTH, expand=True)

        def populate(idx:int):
            # show values for index idx across layers
            self.inspector_tree.delete(*self.inspector_tree.get_children())
            if not self.parsed:
                return
            # header
            self.inspector_tree.insert('', 'end', values=('magic_number', f'0x{self.parsed.get("magic_number",0):016x}'))
            self.inspector_tree.insert('', 'end', values=('version_minor', str(self.parsed.get('version_minor',0))))
            # levels
            for j, lvl in enumerate(self.parsed.get('level', [])):
                if idx < len(lvl.get('level', [])):
                    d1, d2 = lvl['level'][idx]['data1'], lvl['level'][idx]['data2']
                    self.inspector_tree.insert('', 'end', values=(f'level[{j}].data1', f'0x{d1:016x}'))
                    self.inspector_tree.insert('', 'end', values=(f'level[{j}].data2', str(d2)))
                else:
                    self.inspector_tree.insert('', 'end', values=(f'level[{j}]', '<out-of-range>'))
            # level2
            for j, lvl in enumerate(self.parsed.get('level2', [])):
                if idx < len(lvl.get('level', [])):
                    d1, d2 = lvl['level'][idx]['data1'], lvl['level'][idx]['data2']
                    self.inspector_tree.insert('', 'end', values=(f'level2[{j}].data1', f'0x{d1:016x}'))
                    self.inspector_tree.insert('', 'end', values=(f'level2[{j}].data2', str(d2)))
            # level3
            for j, lvl in enumerate(self.parsed.get('level3', [])):
                if idx < len(lvl.get('level', [])):
                    d1, d2 = lvl['level'][idx]['data1'], lvl['level'][idx]['data2']
                    self.inspector_tree.insert('', 'end', values=(f'level3[{j}].data1', f'0x{d1:016x}'))
                    self.inspector_tree.insert('', 'end', values=(f'level3[{j}].data2', str(d2)))

            # hr render_group: try to map hr unk entries (size-2) to index
            hr_tab = self.parsed.get('hr_s', [])
            if hr_tab:
                hr_unk = hr_tab[0].get('unk', [])
                if idx < len(hr_unk):
                    c = hr_unk[idx]
                    if isinstance(c, dict) and c.get('type') == 2 and c.get('extra') and 'section' in c['extra']:
                        rawsec = c['extra']['section']
                        tag = rawsec.split(b'\x00',1)[0].decode('utf-8',errors='replace')
                        self.inspector_tree.insert('', 'end', values=('render_group', tag))
                    else:
                        self.inspector_tree.insert('', 'end', values=('render_group', str(c)))
                else:
                    self.inspector_tree.insert('', 'end', values=('render_group', '<out-of-range>'))

            # unknown/unknown2/sm: try to show per-index small entries where available
            unk = self.parsed.get('unknown', [None])[0]
            if unk:
                data = unk.get('data', [])
                if idx < len(data):
                    d1, d2 = data[idx]['data1'], data[idx]['data2']
                    self.inspector_tree.insert('', 'end', values=('unknown.data', f'{d1},{d2}'))
            unk2 = self.parsed.get('unknown2', [None])[0]
            if unk2:
                # unknown2.unk likely corresponds to size-2 entries
                data = unk2.get('unk', [])
                if idx < len(data):
                    self.inspector_tree.insert('', 'end', values=('unknown2.unk', str(data[idx].get('extra'))))
            sms = self.parsed.get('sm', [])
            for si, s in enumerate(sms):
                u = s.get('unk', [])
                if idx < len(u):
                    c = u[idx]
                    extra = c.get('extra') or {}
                    if isinstance(extra, dict) and extra.get('section_text'):
                        val = extra.get('section_text')
                    elif isinstance(extra, dict) and isinstance(extra.get('section'), (bytes, bytearray)):
                        # show a printable prefix of the raw bytes
                        val = extra.get('section').split(b'\x00', 1)[0].decode('utf-8', errors='replace')
                    else:
                        val = str(extra)
                    self.inspector_tree.insert('', 'end', values=(f'sm[{si}]', val))

        # populate initial
        populate(0)
        self.notebook.add(insp_frame, text='Entity Inspector')

        # level[5]
        for i, lvl in enumerate(self.parsed.get('level', [])):
            self.add_level_tab(f'level[{i}]', lvl.get('level', []))

        # unknown
        if self.parsed.get('unknown'):
            unk = self.parsed['unknown'][0]
            f = Frame(self.notebook)
            t = ttk.Treeview(f, columns=('name', 'value'), show='headings')
            t.heading('name', text='Name')
            t.heading('value', text='Value')
            t.pack(fill=BOTH, expand=True)
            t.insert('', 'end', values=('size', str(unk.get('size'))))
            t.insert('', 'end', values=('chunks', str(len(unk.get('chunks', [])))))
            t.insert('', 'end', values=('data_entries', str(len(unk.get('data', [])))))
            self.notebook.add(f, text='unknown')

        # level2[2]
        for i, lvl in enumerate(self.parsed.get('level2', [])):
            self.add_level_tab(f'level2[{i}]', lvl.get('level', []))

        # unknown2
        if self.parsed.get('unknown2'):
            unk2 = self.parsed['unknown2'][0]
            f = Frame(self.notebook)
            t = ttk.Treeview(f, columns=('name', 'value'), show='headings')
            t.heading('name', text='Name')
            t.heading('value', text='Value')
            t.pack(fill=BOTH, expand=True)
            t.insert('', 'end', values=('size', str(unk2.get('size'))))
            t.insert('', 'end', values=('dunno_chunks', str(len(unk2.get('dunno', [])))))
            t.insert('', 'end', values=('unk_chunks', str(len(unk2.get('unk', [])))))
            self.notebook.add(f, text='unknown2')

        # level3[1]
        for i, lvl in enumerate(self.parsed.get('level3', [])):
            self.add_level_tab(f'level3[{i}]', lvl.get('level', []))

        # hr_s
        if self.parsed.get('hr_s'):
            hr = self.parsed['hr_s'][0]
            f = Frame(self.notebook)
            t = ttk.Treeview(f, columns=('name', 'value'), show='headings')
            t.heading('name', text='Name')
            t.heading('value', text='Value')
            t.pack(fill=BOTH, expand=True)
            t.insert('', 'end', values=('size', str(hr.get('size'))))
            t.insert('', 'end', values=('dunno_chunks', str(len(hr.get('dunno', [])))))
            t.insert('', 'end', values=('unk_chunks', str(len(hr.get('unk', [])))))
            self.notebook.add(f, text='render_group')

        # sm[2]
        for i, s in enumerate(self.parsed.get('sm', [])):
            f = Frame(self.notebook)
            t = ttk.Treeview(f, columns=('name', 'value'), show='headings')
            t.heading('name', text='Name')
            t.heading('value', text='Value')
            t.pack(fill=BOTH, expand=True)
            t.insert('', 'end', values=('size', str(s.get('size'))))
            t.insert('', 'end', values=('dunno_chunks', str(len(s.get('dunno', [])))))
            t.insert('', 'end', values=('unk_chunks', str(len(s.get('unk', [])))))
            self.notebook.add(f, text=f'sm[{i}]')

    def add_level_tab(self, title, entries):
        """Add a notebook tab for a level array (entries is list of dicts)."""
        f = Frame(self.notebook)
        t = ttk.Treeview(f, columns=('index', 'data1', 'data2'), show='headings')
        t.heading('index', text='#')
        t.heading('data1', text='data1 (hex)')
        t.heading('data2', text='data2 (hex)')
        t.column('index', width=40)
        t.column('data1', width=260)
        t.column('data2', width=260)
        t.pack(fill=BOTH, expand=True)

        for i, e in enumerate(entries):
            d1 = e.get('data1', 0)
            d2 = e.get('data2', 0)
            t.insert('', 'end', values=(str(i), f'0x{d1:016x}', f'0x{d2:016x}'))

        def _on_double(ev):
            item = t.focus()
            if not item:
                return
            vals = t.item(item, 'values')
            if not vals:
                return
            idx = int(vals[0])
            if idx < 0 or idx >= len(entries):
                return
            ent = entries[idx]
            cur1 = f'0x{ent.get("data1",0):016x}'
            cur2 = f'0x{ent.get("data2",0):016x}'
            new1 = simpledialog.askstring('Edit entry', f'Entry #{idx} data1 (hex):', initialvalue=cur1)
            if new1 is None:
                return
            new2 = simpledialog.askstring('Edit entry', f'Entry #{idx} data2 (hex):', initialvalue=cur2)
            if new2 is None:
                return
            try:
                v1 = int(new1, 0)
                v2 = int(new2, 0)
            except Exception:
                messagebox.showerror('Invalid', 'Please enter valid integers (decimal or 0xhex).')
                return
            ent['data1'] = v1
            ent['data2'] = v2
            # mark this entry as modified so exports won't blindly reuse original bytes
            ent['_modified'] = True
            t.item(item, values=(str(idx), f'0x{v1:016x}', f'0x{v2:016x}'))

        t.bind('<Double-1>', _on_double)
        self.notebook.add(f, text=title)

    def on_tree_double_click(self, event):
        item = self.table.focus()
        if not item or item not in self.node_map:
            return
        path = self.node_map[item]
        # retrieve value
        target = self.parsed
        for p in path[:-1]:
            target = target[p]
        key = path[-1] if path else None
        if key is None:
            return
        old = target[key]
        # allow editing for ints and bytes and strings
        if isinstance(old, int):
            new_s = simpledialog.askstring('Edit integer', f'Current value: {old}\nEnter new integer:')
            if new_s is None:
                return
            try:
                new_v = int(new_s, 0)
            except Exception:
                messagebox.showerror('Invalid', 'Please enter a valid integer (decimal or 0xhex).')
                return
            target[key] = new_v
        elif isinstance(old, bytes):
            new_s = simpledialog.askstring('Edit bytes (hex)', f'Current hex (truncated): {old.hex()[:80]}\nEnter new hex:')
            if new_s is None:
                return
            try:
                new_v = bytes.fromhex(new_s)
            except Exception:
                messagebox.showerror('Invalid', 'Please enter a valid hex string (no 0x).')
                return
            target[key] = new_v
        elif isinstance(old, str):
            new_s = simpledialog.askstring('Edit text', f'Current value: {old}\nEnter new text:')
            if new_s is None:
                return
            target[key] = new_s
        # mark parent container as modified so exports will rebuild this block
        if isinstance(target, dict):
            target['_modified'] = True
        else:
            # not editable
            messagebox.showinfo('Info', 'Editing of this node type is not supported yet.')
            return

        # refresh the tree display for this node
        # update value column
        val_display = target[key].hex()[:64] if isinstance(target[key], bytes) else str(target[key])
        self.table.item(item, values=(self.table.item(item, 'values')[0], val_display, val_display))

    def export_binary(self):
        if not self.parsed:
            messagebox.showwarning('No data', 'No parsed data to export.')
            return
        path = filedialog.asksaveasfilename(defaultextension='.lvl')
        if not path:
            return

        # build bytes from parsed
        try:
            data = self.build_bytes_from_parsed(self.parsed)
        except Exception as e:
            messagebox.showerror('Export failed', f'Failed to serialize data: {e}')
            return

        try:
            with open(path, 'wb') as f:
                f.write(data)
        except Exception as e:
            messagebox.showerror('Write failed', f'Failed to write file: {e}')
            return

        messagebox.showinfo('Export', f'Wrote {len(data)} bytes to {path}')

    def build_bytes_from_parsed(self, parsed):
        """Serialize the parsed structure back into bytes using the same layout.

        Note: recomputes sizes (e.g., level sizes) from list lengths.
        """
        endian = '<'
        parts = []

        def p_u8(v):
            parts.append(struct.pack(endian + 'B', v))

        def p_u16(v):
            parts.append(struct.pack(endian + 'H', v))

        def p_u32(v):
            parts.append(struct.pack(endian + 'I', v))

        def p_u64(v):
            parts.append(struct.pack(endian + 'Q', v))

        def p_bytes(b):
            parts.append(b)

        # header
        p_u64(parsed.get('magic_number', 0))
        p_u16(parsed.get('version_minor', 0))

        def write_level_contents(lvl):
            # If we have the original raw slice and none of the contained entries were modified,
            # prefer writing the original bytes for bit-for-bit fidelity.
            arr = lvl.get('level', [])
            if lvl.get('_orig_bytes') and not any(e.get('_modified') for e in arr):
                p_bytes(lvl.get('_orig_bytes'))
                return
            p_u32(len(arr))
            for entry in arr:
                p_u64(entry.get('data1', 0))
                p_u64(entry.get('data2', 0))

        # level[5]
        for lvl in parsed.get('level', [])[:5]:
            write_level_contents(lvl)

        # unknown::data (1)
        def write_unknown_data(unk):
            # If original bytes present and not modified, reuse
            if unk.get('_orig_bytes') and not unk.get('_modified'):
                p_bytes(unk.get('_orig_bytes'))
                return
            # size is 2 + len(data)
            data_entries = unk.get('data', [])
            size = 2 + len(data_entries)
            p_u32(size)
            # chunks (2)
            for c in unk.get('chunks', [])[:2]:
                if c.get('_orig_bytes') and not c.get('_modified'):
                    p_bytes(c.get('_orig_bytes'))
                    continue
                p_u32(c.get('head', 0))
                p_u32(c.get('type', 0))
                p_u32(c.get('section_size', 0))
                extra = c.get('extra')
                if extra:
                    if c.get('type') == 0 and 'dunno' in extra:
                        p_u32(extra['dunno'])
                    elif c.get('type') == 2 and 'section' in extra:
                        p_bytes(extra['section'])
            # data entries
            for d in data_entries:
                p_u64(d.get('data1', 0))
                p_u64(d.get('data2', 0))

        for unk in parsed.get('unknown', [])[:1]:
            write_unknown_data(unk)

        # level2[2]
        for lvl in parsed.get('level2', [])[:2]:
            write_level_contents(lvl)

        # unknown2 (new_unknown) [1]
        def write_new_unknown(unk):
            # reuse original block if possible
            if unk.get('_orig_bytes') and not unk.get('_modified'):
                p_bytes(unk.get('_orig_bytes'))
                return
            data_list = unk.get('unk', [])
            dunno = unk.get('dunno', [])
            size = 2 + len(data_list)
            p_u32(size)
            for c in dunno[:2]:
                if c.get('_orig_bytes') and not c.get('_modified'):
                    p_bytes(c.get('_orig_bytes'))
                    continue
                p_u32(c.get('head', 0))
                p_u32(c.get('type', 0))
                p_u32(c.get('section_size', 0))
                extra = c.get('extra')
                if extra:
                    if c.get('type') == 0 and 'dunno' in extra:
                        p_u32(extra['dunno'])
                    elif c.get('type') == 2 and 'section' in extra:
                        p_bytes(extra['section'])
            for c in data_list:
                if c.get('_orig_bytes') and not c.get('_modified'):
                    p_bytes(c.get('_orig_bytes'))
                    continue
                p_u32(c.get('head', 0))
                p_u32(c.get('type', 0))
                p_u32(c.get('section_size', 0))
                extra = c.get('extra')
                if extra:
                    if c.get('type') == 0 and 'dunno' in extra:
                        p_u32(extra['dunno'])
                    elif c.get('type') == 2 and 'section' in extra:
                        p_bytes(extra['section'])

        for unk in parsed.get('unknown2', [])[:1]:
            write_new_unknown(unk)

        # level3[1]
        for lvl in parsed.get('level3', [])[:1]:
            write_level_contents(lvl)

        # hr_s[1]
        for hr in parsed.get('hr_s', [])[:1]:
            if hr.get('_orig_bytes') and not hr.get('_modified'):
                p_bytes(hr.get('_orig_bytes'))
                continue
            # similar to default chunk layout
            size = hr.get('size', 0)
            p_u32(size)
            for c in hr.get('dunno', [])[:2]:
                if c.get('_orig_bytes') and not c.get('_modified'):
                    p_bytes(c.get('_orig_bytes'))
                    continue
                p_u32(c.get('head', 0))
                p_u32(c.get('type', 0))
                p_u32(c.get('section_size', 0))
                extra = c.get('extra')
                if extra:
                    if c.get('type') == 0 and 'dunno' in extra:
                        p_u32(extra['dunno'])
                    elif c.get('type') == 2 and 'section' in extra:
                        p_bytes(extra['section'])
            for c in hr.get('unk', []):
                if c.get('_orig_bytes') and not c.get('_modified'):
                    p_bytes(c.get('_orig_bytes'))
                    continue
                p_u32(c.get('head', 0))
                p_u32(c.get('type', 0))
                p_u32(c.get('section_size', 0))
                extra = c.get('extra')
                if extra:
                    if c.get('type') == 0 and 'dunno' in extra:
                        p_u32(extra['dunno'])
                    elif c.get('type') == 2 and 'section' in extra:
                        p_bytes(extra['section'])

        # sm[2]
        for sm in parsed.get('sm', [])[:2]:
            if sm.get('_orig_bytes') and not sm.get('_modified'):
                p_bytes(sm.get('_orig_bytes'))
                continue
            size = sm.get('size', 0)
            p_u32(size)
            for c in sm.get('dunno', [])[:2]:
                if c.get('_orig_bytes') and not c.get('_modified'):
                    p_bytes(c.get('_orig_bytes'))
                    continue
                p_u32(c.get('head', 0))
                p_u32(c.get('type', 0))
                # sm chunk has different conditional layout
                extra = c.get('extra')
                if c.get('type') == 0 and extra:
                    p_u32(extra.get('section_size', 0))
                    p_u32(extra.get('dunno', 0))
                elif c.get('type') == 2 and extra:
                    # accept either raw bytes (extra['section']) or decoded text (extra['section_text'])
                    bs = b''
                    if isinstance(extra.get('section'), (bytes, bytearray)):
                        bs = bytes(extra.get('section'))
                    elif isinstance(extra.get('section_text'), str):
                        bs = extra.get('section_text').encode('utf-8')
                    p_u32(len(bs))
                    p_bytes(bs)
            for c in sm.get('unk', []):
                if c.get('_orig_bytes') and not c.get('_modified'):
                    p_bytes(c.get('_orig_bytes'))
                    continue
                p_u32(c.get('head', 0))
                p_u32(c.get('type', 0))
                extra = c.get('extra')
                if c.get('type') == 0 and extra:
                    p_u32(extra.get('section_size', 0))
                    p_u32(extra.get('dunno', 0))
                elif c.get('type') == 2 and extra:
                    bs = b''
                    if isinstance(extra.get('section'), (bytes, bytearray)):
                        bs = bytes(extra.get('section'))
                    elif isinstance(extra.get('section_text'), str):
                        bs = extra.get('section_text').encode('utf-8')
                    p_u32(len(bs))
                    p_bytes(bs)

        return b''.join(parts)

    def previous_item(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.load_current()

    def next_item(self):
        if self.current_index < len(self.level_data) - 1:
            self.current_index += 1
            self.load_current()


def main():
    root = main_window()
    root.mainloop()


if __name__ == '__main__':
    main()
