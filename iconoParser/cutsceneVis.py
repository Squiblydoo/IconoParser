#!/usr/bin/env python3
"""
Cutscene Visualizer for Iconoclasts
Shows cutscene events on a 2D canvas with sprite placeholders.

Layer / Section reference:
  [0]  Marker    - Frame count markers, always [1,0]
  [1]  Time      - Tick at which this event fires
  [2]  Duration  - Tween length (0 = instant); non-zero on 'pos' commands
  [3]  ?3        - Always 0, unknown
  [4]  ?4        - Always 0, unknown
  [5]  Command   - Action type (edit_robin, edit_demo, pos, play_track,
                   sound, make_text, create_effect, edit_effect, message,
                   edit_scroll, toggle_scroll, lock, unlock, skip, noskip,
                   zero, end, hash, ...)
  [6]  Target ID - Object: '0'=Robin, '1'/'2'/'3'...=NPC index;
                   'scroll','robin','demo' for pos;
                   'HUD','Text','placements' for effects/text
  [7]  Param 1   - Animation string for edits; startX for pos scroll/robin;
                   demo index for pos demo
  [8]  Param 2   - startY for pos scroll/robin; startX for pos demo
  [9]  Param 3   - endX for pos scroll/robin; startY for pos demo;
                   text ID for make_text; effect properties for create_effect
  [10] Param 4   - endY for pos scroll/robin; endX for pos demo
  [11] Param 5   - endY for pos demo; rarely used otherwise
  [12-14]        - Unused in all examined files

pos command format:
  pos [scroll|robin]: [7]=startX [8]=startY [9]=endX [10]=endY
  pos demo:           [7]=demo_idx [8]=startX [9]=startY [10]=endX [11]=endY

Animation string key prefixes:
  #  - Immediate / force (e.g. #X,896 = teleport to X 896)
  !  - Transition (e.g. !Animation,Walk = begin Walk animation)
  (none) - Destination / set state (X = move toward; Animation = set state)
"""

import os
import re
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

sys.path.insert(0, '.')
import cutsceneParse

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
VIEW_W = 1280       # game viewport width in world units
VIEW_H = 720        # game viewport height in world units
CANVAS_W = 900      # display canvas width
CANVAS_H = 504      # display canvas height

SPRITE_W = 26
SPRITE_H = 52

SECTION_LABELS = [
    '(marker)', 'Time', 'Duration', '?3', '?4',
    'Command', 'Target ID', 'Param 1 (Anim/StartX)',
    'Param 2 (StartY)', 'Param 3 (EndX/TextID/FX)',
    'Param 4 (EndY)', 'Param 5', 'Param 6', 'Param 7', 'Param 8',
]

# NPC colors by demo index
DEMO_COLORS = ['#ff8844', '#44ff88', '#ff44aa', '#ffff44', '#aa44ff',
               '#ff4444', '#44aaff', '#aaffaa']

# Commands that place/move entities
ENTITY_CMDS = {'edit_robin', 'edit_robin2', 'edit_demo', 'pos'}

# Commands colored in frame list
CMD_COLORS = {
    'edit_robin':     '#6699ff',
    'edit_robin2':    '#6699ff',
    'edit_demo':      '#ffaa55',
    'pos':            '#55ffaa',
    'play_track':     '#ffdd88',
    'sound':          '#ffdd88',
    'make_text':      '#ff88cc',
    'message':        '#ff88cc',
    'create_effect':  '#bbbbff',
    'edit_effect':    '#bbbbff',
    'edit_scroll':    '#99ddff',
    'toggle_scroll':  '#99ddff',
    'lock':           '#888899',
    'unlock':         '#888899',
    'skip':           '#888899',
    'noskip':         '#888899',
    'zero':           '#888899',
    'end':            '#ff5555',
    'hash':           '#cc9966',
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _decode(data):
    """Decode bytes to str, stripping null terminators."""
    if isinstance(data, bytes):
        try:
            return data.decode('utf-8').rstrip('\x00')
        except Exception:
            return data.hex()
    return str(data) if data is not None else ''


def _clean(s):
    """Strip padding carriage-return / null bytes used as filler."""
    return s.strip('\r\n\x00 ')


def _safe_int(val, default=None):
    if val is None:
        return default
    try:
        return int(float(str(val).strip()))
    except Exception:
        return default


def _strip_dialog_tags(text):
    """Remove {tag} formatting codes from dia text; replace {new} with newline."""
    text = re.sub(r'\{new\}', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'\{[^}]*\}', '', text)
    return text.strip()


def _parse_kv(s):
    """Parse comma-separated key,value animation parameter string.

    Handles three prefix styles:
      '#Key,val'  -> stored as '#Key': val  (immediate/force)
      '!Key,val'  -> stored as '!Key': val  (transition)
      'Key,val'   -> stored as 'Key': val   (destination/set)

    Returns dict.
    """
    d = {}
    parts = [p.strip() for p in s.split(',')]
    it = iter(parts)
    for part in it:
        if not part:
            continue
        if part.startswith('#') or part.startswith('!'):
            key = part  # keep full prefix as part of key
            val = next(it, None)
            d[key] = val
        else:
            key = part
            val = next(it, None)
            if val is not None:
                d[key] = val
            else:
                d[key] = True
    return d


# ---------------------------------------------------------------------------
# Sprite State
# ---------------------------------------------------------------------------
class SpriteState:
    __slots__ = ('key', 'x', 'y', 'anim', 'direction',
                 'dest_x', 'dest_y', '_color', 'index')

    def __init__(self, key, index=0):
        self.key = key
        self.x = None   # world X (None = offscreen / not yet placed)
        self.y = None   # world Y (None = on ground)
        self.anim = 'Default'
        self.direction = 1   # 1 = right, -1 = left
        self.dest_x = None   # destination for current tween (for arrow)
        self.dest_y = None
        self.index = index

    @property
    def color(self):
        if self.key == 'robin':
            return '#4488ff'
        return DEMO_COLORS[self.index % len(DEMO_COLORS)]

    @property
    def label(self):
        if self.key == 'robin':
            return 'Robin'
        if self.key.startswith('demo_'):
            return f'NPC #{self.key[5:]}'
        return self.key


# ---------------------------------------------------------------------------
# Main Visualizer
# ---------------------------------------------------------------------------
class CutsceneVisualizer:

    def __init__(self):
        self.root = tk.Tk()
        self.root.title('Iconoclasts Cutscene Visualizer')
        self.root.configure(bg='#1a1a2e')
        self.root.minsize(1000, 640)

        self.frames = []
        self.current_frame = 0
        self.scroll_x = 0
        self.sprites = {}  # key -> SpriteState
        self._demo_counter = 0  # assign colors in order of first appearance
        self.dia_rows = []       # flat list from diaParser; empty if not loaded
        self.active_dialog = {}  # sprite_key -> (speaker_name, text)

        self._build_ui()
        self._draw_empty()

        # Keyboard navigation
        self.root.bind('<Left>', lambda _: self.prev_frame())
        self.root.bind('<Right>', lambda _: self.next_frame())
        self.root.bind('<Home>', lambda _: self.go_first())
        self.root.bind('<End>', lambda _: self.go_last())

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self):
        menu = tk.Menu(self.root, bg='#16213e', fg='white',
                       activebackground='#0f3460', activeforeground='white')
        self.root.config(menu=menu)
        fm = tk.Menu(menu, tearoff=0, bg='#16213e', fg='white',
                     activebackground='#0f3460', activeforeground='white')
        menu.add_cascade(label='File', menu=fm)
        fm.add_command(label='Open Cutscene File...', command=self.open_file)
        fm.add_command(label='Load Dialog File (dia)...', command=self.load_dia_manual)
        fm.add_separator()
        fm.add_command(label='Exit', command=self.root.quit)

        top = tk.Frame(self.root, bg='#1a1a2e')
        top.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        # --- Canvas pane ---
        canvas_wrap = tk.LabelFrame(top, text='Scene View',
                                    bg='#16213e', fg='#aaaacc',
                                    font=('Helvetica', 9, 'bold'))
        canvas_wrap.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(canvas_wrap, width=CANVAS_W, height=CANVAS_H,
                                bg='#0d1117', highlightthickness=1,
                                highlightbackground='#334455')
        self.canvas.pack(padx=4, pady=4)

        self.cam_label = tk.Label(canvas_wrap,
                                  text='Camera: scroll_x=0  world 0–1280',
                                  bg='#16213e', fg='#8899aa',
                                  font=('Courier', 8))
        self.cam_label.pack(anchor='w', padx=4)

        # --- Right panel ---
        right = tk.Frame(top, bg='#1a1a2e', width=310)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=(6, 0))
        right.pack_propagate(False)

        # Frame list
        fl_frame = tk.LabelFrame(right, text='Frames',
                                 bg='#16213e', fg='#aaaacc',
                                 font=('Helvetica', 9, 'bold'))
        fl_frame.pack(fill=tk.BOTH, expand=True)

        fl_sb = tk.Scrollbar(fl_frame)
        fl_sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.frame_list = tk.Listbox(
            fl_frame, width=36,
            bg='#0d1117', fg='#ccccdd',
            selectbackground='#0f3460', selectforeground='white',
            font=('Courier', 8), yscrollcommand=fl_sb.set,
            activestyle='none',
        )
        self.frame_list.pack(fill=tk.BOTH, expand=True)
        fl_sb.config(command=self.frame_list.yview)
        self.frame_list.bind('<<ListboxSelect>>', self._on_list_select)

        # Frame detail panel
        det_frame = tk.LabelFrame(right, text='Frame Details',
                                  bg='#16213e', fg='#aaaacc',
                                  font=('Helvetica', 9, 'bold'))
        det_frame.pack(fill=tk.BOTH, expand=True, pady=(4, 0))

        det_sb = tk.Scrollbar(det_frame)
        det_sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.detail_text = tk.Text(
            det_frame, width=34,
            bg='#0d1117', fg='#ccccdd',
            font=('Courier', 8), wrap=tk.WORD,
            state=tk.DISABLED,
            yscrollcommand=det_sb.set,
        )
        self.detail_text.pack(fill=tk.BOTH, expand=True)
        det_sb.config(command=self.detail_text.yview)

        # --- Navigation bar ---
        nav = tk.Frame(self.root, bg='#16213e', pady=4)
        nav.pack(fill=tk.X, padx=6, pady=(0, 4))

        btn = dict(bg='#0f3460', fg='white',
                   activebackground='#4488ff', activeforeground='white',
                   relief=tk.FLAT, padx=7, pady=3, font=('Helvetica', 9))

        tk.Button(nav, text='|<<', command=self.go_first, **btn).pack(side=tk.LEFT, padx=2)
        tk.Button(nav, text='< Prev', command=self.prev_frame, **btn).pack(side=tk.LEFT, padx=2)

        self.frame_label = tk.Label(nav, text='—', bg='#16213e', fg='#aaaacc',
                                    font=('Courier', 9), width=18)
        self.frame_label.pack(side=tk.LEFT, padx=6)

        tk.Button(nav, text='Next >', command=self.next_frame, **btn).pack(side=tk.LEFT, padx=2)
        tk.Button(nav, text='>>|', command=self.go_last, **btn).pack(side=tk.LEFT, padx=2)

        tk.Label(nav, text='  Jump:', bg='#16213e', fg='#aaaacc',
                 font=('Courier', 9)).pack(side=tk.LEFT)
        self.jump_entry = tk.Entry(nav, width=5, bg='#0d1117', fg='white',
                                   insertbackground='white', font=('Courier', 9))
        self.jump_entry.pack(side=tk.LEFT, padx=2)
        tk.Button(nav, text='Go', command=self._jump_frame, **btn).pack(side=tk.LEFT, padx=2)

    # ------------------------------------------------------------------
    # File loading
    # ------------------------------------------------------------------
    def open_file(self):
        path = filedialog.askopenfilename(title='Open Cutscene File')
        if path:
            self.load_file(path)

    def load_file(self, path):
        try:
            frames_data, _ = cutsceneParse.guiParse(path)
            self.frames = frames_data
            self.current_frame = 0
            self._demo_counter = 0
            # Auto-load 'dia' from the same directory as the cutscene file
            dia_path = os.path.join(os.path.dirname(os.path.abspath(path)), 'dia')
            if os.path.isfile(dia_path):
                self._load_dia(dia_path)
            self._build_frame_list()
            self.render_frame(0)
            fname = os.path.basename(path)
            self.root.title(f'Cutscene Visualizer — {fname}')
        except Exception as exc:
            messagebox.showerror('Load Error', str(exc))

    def load_dia_manual(self):
        path = filedialog.askopenfilename(title='Load Dialog File (dia)')
        if path:
            self._load_dia(path)
            if self.frames:
                self.render_frame(self.current_frame)

    def _load_dia(self, path):
        try:
            import iconoParser.diaParser as diaParser
            self.dia_rows = diaParser.parse(path)
        except Exception as exc:
            messagebox.showwarning('Dialog Load', f'Could not load dia file:\n{exc}')
            self.dia_rows = []

    def _get_dialog(self, text_id):
        """Given a make_text ID, return (speaker_name, demo_index, plain_text).
        text_id is the dialog group number (as shown in IconoParserGUI).
        Each group occupies 3 consecutive flat rows: type0=speaker, type1=text, type2=whotalk.
        Flat index = (text_id - 1) * 3."""
        if not self.dia_rows or text_id is None:
            return None, None, None
        base = (text_id - 1) * 3
        if base < 0 or base + 2 >= len(self.dia_rows):
            return None, None, None
        name = self.dia_rows[base][2].strip()       # type 0: speaker name
        dialog = _strip_dialog_tags(self.dia_rows[base + 1][2])  # type 1: text
        whotalk_str = self.dia_rows[base + 2][2]    # type 2: whotalk\N...
        demo_idx = None
        m = re.match(r'whotalk\\(\d+)', whotalk_str)
        if m:
            demo_idx = int(m.group(1))
        return name, demo_idx, dialog

    # ------------------------------------------------------------------
    # Section accessors
    # ------------------------------------------------------------------
    def _get(self, frame, idx):
        """Return decoded section value, stripped of padding."""
        if idx >= len(frame):
            return ''
        item = frame[idx]
        if len(item) >= 4:
            return _clean(_decode(item[3]))
        if len(item) >= 2:
            v = item[1]
            return _clean(str(v)) if v not in ('', None) else ''
        return ''

    # ------------------------------------------------------------------
    # Frame list
    # ------------------------------------------------------------------
    def _build_frame_list(self):
        self.frame_list.delete(0, tk.END)
        for i, frame in enumerate(self.frames):
            cmd = self._get(frame, 5)
            tid = self._get(frame, 6)
            t = self._get(frame, 1)
            label = f'{i:3d}  t={t:<6s}  {cmd}'
            if tid:
                label += f'[{tid}]'
            self.frame_list.insert(tk.END, label)
            color = CMD_COLORS.get(cmd, '#ccccdd')
            self.frame_list.itemconfig(i, fg=color)

    # ------------------------------------------------------------------
    # State accumulation
    # ------------------------------------------------------------------
    def _reset_state(self):
        self.scroll_x = 0
        self.sprites = {}
        self._demo_counter = 0
        self.active_dialog = {}  # sprite_key -> (speaker_name, text)

    def _get_or_make_sprite(self, key):
        if key not in self.sprites:
            if key.startswith('demo_'):
                idx = self._demo_counter
                self._demo_counter += 1
            else:
                idx = 0
            self.sprites[key] = SpriteState(key, index=idx)
        return self.sprites[key]

    def _accumulate(self, up_to):
        """Reset and replay frames 0..up_to to build scene state.
        For all frames before the current one, finalize any tween so sprites
        appear at their destination. Only the current frame shows the
        start→dest arrow."""
        self._reset_state()
        for fi in range(up_to + 1):
            self._apply_frame(self.frames[fi])
            if fi < up_to:
                # Snap sprite tweens to their destinations so earlier frames
                # don't leave sprites stranded at their start positions.
                # The camera is NOT finalized here — a camera tween often
                # overlaps the next sprite command (e.g. both fire around
                # the same tick), so keeping scroll_x at the tween startX
                # gives a more accurate picture of the scene at that moment.
                for s in self.sprites.values():
                    if s.dest_x is not None:
                        s.x = s.dest_x
                        s.dest_x = None
                    if s.dest_y is not None:
                        s.y = s.dest_y
                        s.dest_y = None

    def _apply_frame(self, frame):
        cmd = self._get(frame, 5)
        tid = self._get(frame, 6)
        p7 = self._get(frame, 7)
        p8 = self._get(frame, 8)
        p9 = self._get(frame, 9)
        p10 = self._get(frame, 10)
        p11 = self._get(frame, 11)

        if cmd in ('edit_robin', 'edit_robin2'):
            s = self._get_or_make_sprite('robin')
            s.dest_x = None
            s.dest_y = None
            self._apply_anim_str(s, p7)

        elif cmd == 'edit_demo':
            key = f'demo_{tid}' if tid else 'demo_?'
            s = self._get_or_make_sprite(key)
            s.dest_x = None
            s.dest_y = None
            self._apply_anim_str(s, p7)

        elif cmd == 'pos':
            target = tid.lower()
            # Check if [7] is a demo NPC index (small integer)
            # Format: pos demo -> [7]=index, [8]=startX, [9]=startY, [10]=endX, [11]=endY
            # Format: pos scroll/robin -> [7]=startX, [8]=startY, [9]=endX, [10]=endY
            p7_int = _safe_int(p7)
            is_demo_pos = (target == 'demo' and p7_int is not None and 1 <= p7_int <= 20)

            if is_demo_pos:
                key = f'demo_{p7}'
                s = self._get_or_make_sprite(key)
                sx = _safe_int(p8)
                sy = _safe_int(p9)
                ex = _safe_int(p10)
                ey = _safe_int(p11)
                if sx is not None:
                    s.x = sx
                if sy is not None and sy != 0:
                    s.y = sy
                s.dest_x = ex
                s.dest_y = ey if ey else None
            elif 'robin' in target:
                s = self._get_or_make_sprite('robin')
                sx = _safe_int(p7)
                sy = _safe_int(p8)
                ex = _safe_int(p9)
                ey = _safe_int(p10)
                if sx is not None:
                    s.x = sx
                if sy is not None and sy != 0:
                    s.y = sy
                s.dest_x = ex
                s.dest_y = ey if ey else None
            elif 'scroll' in target:
                sx = _safe_int(p7)
                ex = _safe_int(p9)
                if sx is not None:
                    self.scroll_x = sx
                self._scroll_dest = ex

        elif cmd == 'make_text':
            text_id = _safe_int(self._get(frame, 9))
            speaker_name, demo_idx, dialog = self._get_dialog(text_id)
            if dialog:
                # Map speaker to sprite key: use demo_idx if available,
                # else fall back to speaker name matching Robin.
                if demo_idx is not None:
                    key = f'demo_{demo_idx}'
                elif speaker_name and 'robin' in speaker_name.lower():
                    key = 'robin'
                else:
                    key = f'_text_{text_id}'
                self.active_dialog[key] = (speaker_name, dialog)

        elif cmd == 'end':
            self.active_dialog = {}

        elif cmd == 'edit_scroll':
            if p7:
                kv = _parse_kv(p7)
                for k in ('#X', '#ForceX', '#GoX', 'X'):
                    if k in kv:
                        v = _safe_int(kv[k])
                        if v is not None:
                            self.scroll_x = v
                            break

    def _apply_anim_str(self, s, anim_str):
        """Apply a key=value animation string to a SpriteState."""
        if not anim_str:
            return
        kv = _parse_kv(anim_str)

        # Immediate/force position (#X, #Y)
        x_imm = _safe_int(kv.get('#X'))
        y_imm = _safe_int(kv.get('#Y'))
        if x_imm is not None:
            s.x = x_imm
        if y_imm is not None and y_imm != 0:
            s.y = y_imm

        # Destination position (X, Y without #) – treat as current pos
        # on first encounter or use as target
        x_dest = _safe_int(kv.get('X'))
        y_dest = _safe_int(kv.get('Y'))
        if x_dest is not None and s.x is None:
            s.x = x_dest
        if y_dest is not None and s.y is None and y_dest != 0:
            s.y = y_dest

        # MoveX means "end X after movement"
        mx = _safe_int(kv.get('#MoveX'))
        if mx is not None:
            s.dest_x = mx

        # Animation state
        anim = kv.get('!Animation') or kv.get('Animation')
        if anim:
            s.anim = anim

        # Direction
        d = _safe_int(kv.get('#Direction'))
        if d is not None:
            s.direction = d

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------
    def render_frame(self, fi):
        self.current_frame = fi
        total = len(self.frames)
        self.frame_label.config(text=f'Frame {fi + 1} / {total}')
        self._accumulate(fi)

        self.canvas.delete('all')
        self._draw_scene(fi)
        self._update_details(fi)

        self.frame_list.selection_clear(0, tk.END)
        self.frame_list.selection_set(fi)
        self.frame_list.see(fi)

        cam_end = self.scroll_x + VIEW_W
        self.cam_label.config(
            text=f'Camera: x={self.scroll_x}–{cam_end}  (viewport shown as blue box)'
        )

    def _compute_fit(self):
        """Return (ox, oy, scale) world-to-canvas transform that fits all
        placed sprites and the camera viewport into the canvas."""
        xs = [self.scroll_x, self.scroll_x + VIEW_W]
        ys = [0, int(VIEW_H * 0.9)]
        for s in self.sprites.values():
            if s.x is not None:
                xs.append(s.x)
            if s.dest_x is not None:
                xs.append(s.dest_x)
            if s.y is not None:
                ys.append(s.y)
        pad_x, pad_y = 200, 80
        min_x = min(xs) - pad_x
        max_x = max(xs) + pad_x
        min_y = max(0, min(ys) - pad_y)
        max_y = max(ys) + pad_y
        scale = min(CANVAS_W / max(max_x - min_x, 1),
                    CANVAS_H / max(max_y - min_y, 1))
        return min_x, min_y, scale

    def _draw_scene(self, fi):
        ox, oy, scale = self._compute_fit()

        def ws(wx, wy):
            return int((wx - ox) * scale), int((wy - oy) * scale)

        ground_world = int(VIEW_H * 0.85)
        _, ground_cy = ws(0, ground_world)
        ground_cy = max(20, min(ground_cy, CANVAS_H - 10))

        # Sky / ground fill
        self.canvas.create_rectangle(0, 0, CANVAS_W, ground_cy,
                                     fill='#0d1b2a', outline='')
        self.canvas.create_rectangle(0, ground_cy, CANVAS_W, CANVAS_H,
                                     fill='#142214', outline='')
        self.canvas.create_line(0, ground_cy, CANVAS_W, ground_cy,
                                fill='#2a4a2a', width=2)

        # World X grid every 320 units
        for wx in range(0, 9000, 320):
            gx, _ = ws(wx, 0)
            if -5 <= gx <= CANVAS_W + 5:
                self.canvas.create_line(gx, 0, gx, ground_cy,
                                        fill='#1a2a3a', dash=(3, 6))
                self.canvas.create_text(gx + 2, 4, text=str(wx),
                                        fill='#334455', font=('Courier', 7),
                                        anchor='nw')

        # Camera viewport as a shaded + outlined rectangle
        cam_x0, _ = ws(self.scroll_x, 0)
        cam_x1, _ = ws(self.scroll_x + VIEW_W, 0)
        self.canvas.create_rectangle(cam_x0, 2, cam_x1, CANVAS_H - 2,
                                     fill='#111b2e', outline='#4466aa',
                                     width=1, dash=(6, 3))
        self.canvas.create_text((cam_x0 + cam_x1) // 2, 10,
                                text=f'camera  x={self.scroll_x}',
                                fill='#4466aa', font=('Courier', 7))

        # Scaled sprite dimensions
        sp_w = max(8, int(SPRITE_W * scale))
        sp_h = max(14, int(SPRITE_H * scale))

        # Sprites: Robin first, then NPCs in key order
        ordered = []
        if 'robin' in self.sprites:
            ordered.append(self.sprites['robin'])
        for k, s in sorted(self.sprites.items()):
            if k != 'robin':
                ordered.append(s)

        for s in ordered:
            if s.x is None:
                continue

            wy_feet = s.y if s.y is not None else ground_world
            sx, sy_bot = ws(s.x, wy_feet)
            sy_top = sy_bot - sp_h
            x0 = sx - sp_w // 2
            x1 = sx + sp_w // 2
            head_r = max(4, sp_w // 2)

            self.canvas.create_oval(x0 + 2, sy_bot - 3, x1 + 2, sy_bot + 4,
                                    fill='#000000', outline='')
            self.canvas.create_rectangle(x0, sy_top, x1, sy_bot,
                                         fill=s.color, outline='white', width=1)
            self.canvas.create_oval(sx - head_r, sy_top - head_r * 2,
                                    sx + head_r, sy_top,
                                    fill=s.color, outline='white', width=1)

            mid_y = sy_top + sp_h // 2
            arr = max(5, int(8 * scale))
            if s.direction >= 0:
                pts = [x1, mid_y - 3, x1 + arr, mid_y, x1, mid_y + 3]
            else:
                pts = [x0, mid_y - 3, x0 - arr, mid_y, x0, mid_y + 3]
            self.canvas.create_polygon(*pts, fill='white', outline='')

            self.canvas.create_text(sx, sy_top - head_r * 2 - 2, text=s.label,
                                    fill='white', font=('Courier', 7, 'bold'),
                                    anchor='s')
            anim_display = s.anim[:16] if s.anim else ''
            self.canvas.create_text(sx, sy_bot + 3, text=anim_display,
                                    fill=s.color, font=('Courier', 7), anchor='n')

            if s.dest_x is not None:
                dwy = s.dest_y if s.dest_y else wy_feet
                dx, _ = ws(s.dest_x, dwy)
                self.canvas.create_line(sx, mid_y, dx, mid_y,
                                        fill='#ffff44', width=1,
                                        dash=(5, 3), arrow=tk.LAST)
                self.canvas.create_text(dx, mid_y - 10, text=str(s.dest_x),
                                        fill='#ffff44', font=('Courier', 7))

        # Scroll destination arrow
        scroll_dest = getattr(self, '_scroll_dest', None)
        if scroll_dest is not None:
            sd_x1, _ = ws(scroll_dest + VIEW_W, 0)
            self.canvas.create_line(cam_x1, 12, sd_x1, 12,
                                    fill='#99ddff', width=1,
                                    dash=(4, 3), arrow=tk.LAST)
            self.canvas.create_text(sd_x1 + 2, 12, text=f'cam→{scroll_dest}',
                                    fill='#99ddff', font=('Courier', 7), anchor='w')

        # Speech bubbles for active dialog
        sp_h_bub = max(14, int(SPRITE_H * scale))
        head_r_bub = max(4, max(8, int(SPRITE_W * scale)) // 2)
        for sprite_key, (speaker_name, dialog_text) in self.active_dialog.items():
            # Find the sprite to anchor the bubble above, or float it
            sprite = self.sprites.get(sprite_key)
            if sprite and sprite.x is not None:
                wy_feet = sprite.y if sprite.y is not None else ground_world
                bx, by_feet = ws(sprite.x, wy_feet)
                by = by_feet - sp_h_bub - head_r_bub * 2 - 8  # above the head
            else:
                # No sprite placed yet — stack floated bubbles at top-center
                bx = CANVAS_W // 2
                by = 30 + list(self.active_dialog.keys()).index(sprite_key) * 60

            lines = dialog_text.splitlines()
            max_line = max((len(l) for l in lines), default=1)
            pad = 6
            char_w, char_h = 6, 11
            bw = max_line * char_w + pad * 2
            bh = len(lines) * char_h + pad * 2
            bx0 = bx - bw // 2
            bx1 = bx + bw // 2
            by0 = by - bh
            by1 = by

            # Bubble background + border
            bubble_color = self.sprites[sprite_key].color if sprite_key in self.sprites else '#ffffff'
            self.canvas.create_rectangle(bx0, by0, bx1, by1,
                                         fill='#1a1a2e', outline=bubble_color, width=1)
            # Tail pointing down toward the sprite
            if sprite and sprite.x is not None:
                self.canvas.create_polygon(
                    bx - 4, by1, bx, by1 + 6, bx + 4, by1,
                    fill='#1a1a2e', outline=bubble_color
                )

            # Speaker name (small, colored)
            if speaker_name:
                self.canvas.create_text(bx0 + pad, by0 + 2,
                                        text=speaker_name,
                                        fill=bubble_color,
                                        font=('Courier', 7, 'bold'),
                                        anchor='nw')
                text_top = by0 + char_h + 2
            else:
                text_top = by0 + pad

            self.canvas.create_text(bx0 + pad, text_top,
                                    text=dialog_text,
                                    fill='white',
                                    font=('Courier', 8),
                                    anchor='nw')

        # Current command overlay (bottom-left)
        frame = self.frames[fi]
        cmd = self._get(frame, 5)
        tid = self._get(frame, 6)
        t = self._get(frame, 1)
        overlay = f't={t}  {cmd}'
        if tid:
            overlay += f'[{tid}]'
        self.canvas.create_text(6, CANVAS_H - 4, text=overlay,
                                anchor='sw', fill='#aaaacc',
                                font=('Courier', 9))

    # ------------------------------------------------------------------
    # Detail panel
    # ------------------------------------------------------------------
    def _update_details(self, fi):
        frame = self.frames[fi]
        t = self.detail_text
        t.config(state=tk.NORMAL)
        t.delete('1.0', tk.END)

        t.insert(tk.END, f'Frame {fi}  (time={self._get(frame, 1)})\n')
        t.insert(tk.END, '─' * 28 + '\n')

        for i in range(len(frame)):
            val = self._get(frame, i)
            if not val:
                continue
            lbl = SECTION_LABELS[i] if i < len(SECTION_LABELS) else f'Param {i}'
            t.insert(tk.END, f'[{i}] {lbl}:\n  {val}\n')

        # Scene state summary
        t.insert(tk.END, '\n' + '─' * 28 + '\n')
        t.insert(tk.END, 'Scene state after this frame:\n')
        for s in ([self.sprites['robin']] if 'robin' in self.sprites else []):
            xv = str(s.x) if s.x is not None else '?'
            yv = str(s.y) if s.y is not None else 'gnd'
            dv = '→' if s.direction >= 0 else '←'
            t.insert(tk.END, f'  Robin: ({xv},{yv}) {dv} [{s.anim}]\n')
        demo_keys = sorted(k for k in self.sprites if k.startswith('demo_'))
        for k in demo_keys:
            s = self.sprites[k]
            xv = str(s.x) if s.x is not None else '?'
            yv = str(s.y) if s.y is not None else 'gnd'
            dv = '→' if s.direction >= 0 else '←'
            t.insert(tk.END, f'  {s.label}: ({xv},{yv}) {dv} [{s.anim}]\n')
        t.insert(tk.END, f'  scroll_x: {self.scroll_x}\n')

        t.config(state=tk.DISABLED)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------
    def _on_list_select(self, _event):
        sel = self.frame_list.curselection()
        if sel:
            self.render_frame(sel[0])

    def _jump_frame(self):
        try:
            n = int(self.jump_entry.get()) - 1
            if 0 <= n < len(self.frames):
                self.render_frame(n)
        except Exception:
            pass

    def go_first(self):
        if self.frames:
            self.render_frame(0)

    def prev_frame(self):
        if self.current_frame > 0:
            self.render_frame(self.current_frame - 1)

    def next_frame(self):
        if self.current_frame < len(self.frames) - 1:
            self.render_frame(self.current_frame + 1)

    def go_last(self):
        if self.frames:
            self.render_frame(len(self.frames) - 1)

    def _draw_empty(self):
        self.canvas.create_text(
            CANVAS_W // 2, CANVAS_H // 2,
            text='Open a cutscene file to begin\n(File > Open  or  pass path as argument)',
            fill='#445566', font=('Helvetica', 13), justify=tk.CENTER,
        )

    def run(self):
        self.root.mainloop()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    vis = CutsceneVisualizer()
    if len(sys.argv) > 1:
        vis.load_file(sys.argv[1])
    vis.run()


if __name__ == '__main__':
    main()
