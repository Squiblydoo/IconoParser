from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QTextEdit, QPushButton, QLabel,
    QLineEdit, QGroupBox, QComboBox, QFileDialog,
    QAbstractItemView, QHeaderView, QSplitter, QDialog,
    QStyledItemDelegate, QStyle,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRectF, QItemSelection, QItemSelectionModel
from PyQt6.QtGui import (
    QColor, QBrush, QFont, QFontMetrics,
    QAction, QPainter, QPainterPath, QPen, QFontDatabase,
)
import math
import random
import re
import os
import sys
import fileParse
import iconoParser.helperDictionaries as helperDict

BASE_PACE_MS = 30
WAVE_AMP   = 3    # pixels of vertical displacement
WAVE_WIDTH = 100   # pixels per full wave cycle
WAVE_SPEED = 0.2 # radians per 75 ms tick (~4 s per full cycle)

def _default_game_dia_path():
    base = ('steamapps', 'common', 'Iconoclasts', 'data', 'dia')
    if sys.platform == 'win32':
        return os.path.join('C:\\', 'Program Files (x86)', 'Steam', *base)
    elif sys.platform == 'darwin':
        return os.path.join(
            os.path.expanduser('~'), 'Library', 'Application Support', 'Steam', *base
        )
    else:  # Linux
        return os.path.join(
            os.path.expanduser('~'), '.local', 'share', 'Steam', *base
        )

GAME_DIA_PATH = _default_game_dia_path()

BUB_STYLES = {
    'bub04': {'bg': '#1a3a8f', 'border_color': '#1a3a8f', 'border_width': 0, 'show_speaker': False},
    'bub05': {'bg': '#222222', 'border_color': '#ffffff',  'border_width': 2, 'show_speaker': True},
    'bub06': {'bg': '#222222', 'border_color': '#ffffff',  'border_width': 2, 'show_speaker': False},
    'bub07': {'bg': '#5a2510', 'border_color': '#5a2510', 'border_width': 0, 'show_speaker': False},
}
_DEFAULT_BUB_STYLE = {'bg': '#222222', 'border_color': '#222222', 'border_width': 0, 'show_speaker': True}

DYE_COLORS = {
    'dye00': '#ffffff', 'dye01': '#FF4444', 'dye02': '#FFFF99',
    'dye03': '#ffffff', 'dye04': '#FFFF00', 'dye05': '#44CC44',
    'dye06': '#87CEEB', 'dye07': '#888888', 'dye08': '#ffffff',
    'dye09': '#00FFFF', 'dye10': '#CC44CC',
}

PIXEL_FONT_CANDIDATES = ['Press Start 2P', 'VT323', 'Pixel Operator', 'PixelOperator']

DARK_THEME = """
QMainWindow, QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
}
QMenuBar {
    background-color: #181825;
    color: #cdd6f4;
    border-bottom: 1px solid #313244;
    padding: 2px;
}
QMenuBar::item { padding: 4px 10px; border-radius: 4px; }
QMenuBar::item:selected { background-color: #313244; }
QMenu {
    background-color: #181825;
    color: #cdd6f4;
    border: 1px solid #313244;
    padding: 4px;
}
QMenu::item { padding: 5px 22px; border-radius: 4px; }
QMenu::item:selected { background-color: #45475a; }
QMenu::separator { height: 1px; background: #313244; margin: 4px 0; }
QPushButton {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 5px 14px;
    min-height: 24px;
}
QPushButton:hover { background-color: #45475a; border-color: #89b4fa; }
QPushButton:pressed { background-color: #585b70; }
QPushButton#playButton {
    background-color: #1e3a5f;
    border-color: #89b4fa;
    color: #89b4fa;
    font-weight: bold;
}
QPushButton#playButton:hover { background-color: #2a4a7a; }
QPushButton#exportButton {
    background-color: #1e3a1e;
    border-color: #a6e3a1;
    color: #a6e3a1;
    font-weight: bold;
    padding: 6px 22px;
}
QPushButton#exportButton:hover { background-color: #2a4a2a; }
QLineEdit {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 4px 8px;
    selection-background-color: #89b4fa;
    selection-color: #1e1e2e;
}
QLineEdit:focus { border-color: #89b4fa; }
QTextEdit {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    selection-background-color: #89b4fa;
    selection-color: #1e1e2e;
}
QTextEdit:focus { border-color: #89b4fa; }
QTableWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    gridline-color: #313244;
    border: 1px solid #313244;
    border-radius: 6px;
    alternate-background-color: #252535;
    selection-background-color: #45475a;
    selection-color: #cdd6f4;
    outline: none;
}
QTableWidget::item { padding: 3px 6px; border: none; }
QTableWidget::item:selected { background-color: #45475a; }
QHeaderView { background-color: #181825; }
QHeaderView::section {
    background-color: #181825;
    color: #89b4fa;
    border: none;
    border-right: 1px solid #313244;
    border-bottom: 1px solid #313244;
    padding: 5px 8px;
    font-weight: bold;
}
QHeaderView::section:hover { background-color: #313244; }
QGroupBox {
    border: 1px solid #45475a;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 6px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 6px;
    color: #89b4fa;
    font-weight: bold;
}
QComboBox {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 4px 8px;
}
QComboBox:hover { border-color: #89b4fa; }
QComboBox::drop-down { border: none; width: 20px; }
QComboBox QAbstractItemView {
    background-color: #313244;
    color: #cdd6f4;
    selection-background-color: #45475a;
    border: 1px solid #45475a;
}
QScrollBar:vertical {
    background: #181825;
    width: 10px;
    border-radius: 5px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #45475a;
    border-radius: 5px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover { background: #585b70; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal {
    background: #181825;
    height: 10px;
    border-radius: 5px;
    margin: 0;
}
QScrollBar::handle:horizontal {
    background: #45475a;
    border-radius: 5px;
    min-width: 20px;
}
QScrollBar::handle:horizontal:hover { background: #585b70; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QLabel { color: #cdd6f4; }
QSplitter::handle { background: #313244; }
QSplitter::handle:vertical { height: 2px; }
"""


def get_key(val):
    for key, value in helperDict.DIALOG_FUNCTION.items():
        if val == value:
            return key


class _RowColorDelegate(QStyledItemDelegate):
    """Full paint override so row background colors work despite QSS being active.

    QStyleSheetStyle reads background from CSS and ignores BackgroundRole entirely,
    so initStyleOption tricks don't work.  We draw background + text ourselves.
    """
    _SEL_BG   = QColor('#45475a')
    _FG       = QColor('#cdd6f4')
    _HPAD     = 6   # horizontal text padding

    def paint(self, painter, option, index):
        painter.save()
        is_selected = bool(option.state & QStyle.StateFlag.State_Selected)

        # Background
        if is_selected:
            painter.fillRect(option.rect, self._SEL_BG)
        else:
            bg = index.data(Qt.ItemDataRole.BackgroundRole)
            painter.fillRect(option.rect, bg if isinstance(bg, QBrush) else QBrush(QColor('#1e1e2e')))

        # Text
        text = index.data(Qt.ItemDataRole.DisplayRole)
        if text is not None:
            raw_align = index.data(Qt.ItemDataRole.TextAlignmentRole)
            align = int(raw_align) if raw_align is not None else int(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            )
            painter.setPen(self._FG)
            painter.drawText(
                option.rect.adjusted(self._HPAD, 0, -self._HPAD, 0),
                align, str(text)
            )
        painter.restore()


class DialogTable(QTableWidget):
    fileDropped = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DropOnly)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            path = event.mimeData().urls()[0].toLocalFile()
            self.fileDropped.emit(path)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)


class _TextCanvas(QWidget):
    """Renders styled characters with optional shutter (jitter) or wave animation."""
    _ANIM_INTERVAL_MS = 50  # ~20 fps
    _SHUTTER_AMP = 1        # pixels of random vertical offset for shutter

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self._chars = []
        self._laid_out = False
        self._wave_phase = 0.0
        self._animTimer = QTimer(self)
        self._animTimer.setInterval(self._ANIM_INTERVAL_MS)
        self._animTimer.timeout.connect(self._tick)

    def _tick(self):
        self._wave_phase += WAVE_SPEED
        self.update()

    def clear(self):
        self._chars = []
        self._laid_out = False
        self._wave_phase = 0.0
        self._animTimer.stop()
        self.update()

    def appendChar(self, char, color, font, shutter=False, wave=False):
        self._chars.append({
            'char': char,
            'color': QColor(color) if isinstance(color, str) else QColor(color),
            'font': QFont(font),
            'shutter': shutter,
            'wave': wave,
            'x': 0, 'y': 0,
        })
        self._laid_out = False
        if (shutter or wave) and not self._animTimer.isActive():
            self._animTimer.start()
        self.update()

    def appendRun(self, text, color, font, shutter=False, wave=False):
        for ch in text:
            self.appendChar(ch, color, font, shutter, wave)

    def resizeEvent(self, event):
        self._laid_out = False
        super().resizeEvent(event)

    def _layout(self):
        x = 0
        y = 0
        line_h = 0
        w = self.width()
        for rec in self._chars:
            fm = QFontMetrics(rec['font'])
            if rec['char'] == '\n':
                x = 0
                y += line_h if line_h else fm.height()
                line_h = 0
                rec['x'] = 0
                rec['y'] = -1  # sentinel — skip in paintEvent
                continue
            cw = fm.horizontalAdvance(rec['char'])
            ch = fm.height()
            if x > 0 and x + cw > w:
                x = 0
                y += line_h
                line_h = 0
            rec['x'] = x
            rec['y'] = y + fm.ascent()
            x += cw
            line_h = max(line_h, ch)
        self._laid_out = True

    def paintEvent(self, event):
        if not self._chars:
            return
        if not self._laid_out:
            self._layout()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        for rec in self._chars:
            if rec['y'] < 0:  # newline sentinel
                continue
            if rec['shutter']:
                dy = random.randint(-self._SHUTTER_AMP, self._SHUTTER_AMP)
            elif rec['wave']:
                dy = int(WAVE_AMP * math.sin(
                    2 * math.pi * rec['x'] / WAVE_WIDTH + self._wave_phase
                ))
            else:
                dy = 0
            p.setFont(rec['font'])
            p.setPen(rec['color'])
            p.drawText(rec['x'], rec['y'] + dy, rec['char'])


class BubblePreview(QWidget):
    """Game-style rounded dialog bubble with markup-aware text rendering."""

    def __init__(self, pixel_font, speaker_font, parent=None):
        super().__init__(parent)
        self.setAutoFillBackground(False)
        self.setMinimumHeight(100)
        self._bg = _DEFAULT_BUB_STYLE['bg']
        self._border_color = QColor(_DEFAULT_BUB_STYLE['border_color'])
        self._border_width = _DEFAULT_BUB_STYLE['border_width']
        self._pixel_font = pixel_font
        self._speaker_font = speaker_font

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(0)

        self.canvas = _TextCanvas()
        layout.addWidget(self.canvas)

    def applyBubStyle(self, bub_tag):
        style = BUB_STYLES.get(bub_tag, _DEFAULT_BUB_STYLE)
        self._bg = style['bg']
        self._border_color = QColor(style['border_color'])
        self._border_width = style['border_width']
        self.update()
        return style['show_speaker']

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        bw = self._border_width
        rect = QRectF(self.rect())
        if bw > 0:
            painter.setPen(QPen(self._border_color, bw))
            rect = rect.adjusted(bw / 2, bw / 2, -bw / 2, -bw / 2)
        else:
            painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(self._bg)))
        path = QPainterPath()
        path.addRoundedRect(rect, 12, 12)
        painter.drawPath(path)

    def clear(self):
        self.canvas.clear()

    def _make_font(self, size_mult=1.0, underline=False):
        font = QFont(self._pixel_font)
        if size_mult != 1.0:
            font.setPointSizeF(self._pixel_font.pointSizeF() * size_mult)
        if underline:
            font.setUnderline(True)
        return font

    def renderText(self, text, speaker='', bub_tag=None):
        show_speaker = self.applyBubStyle(bub_tag)
        self.canvas.clear()

        if speaker and show_speaker:
            self.canvas.appendRun(speaker + '\n', QColor('#FFFF00'), self._speaker_font)

        parts = re.split(r'(\{[^}]+\})', text)
        cur_color = QColor('#ffffff')
        cur_shutter = False
        cur_wave = False
        cur_size = 1.0
        underline = False
        for part in parts:
            if part.startswith('{') and part.endswith('}'):
                tag = part[1:-1]
                if tag == 'new':
                    self.canvas.appendChar('\n', cur_color, self._make_font(cur_size, underline))
                elif tag in DYE_COLORS:
                    cur_color = QColor(DYE_COLORS[tag])
                elif tag == 'type00':
                    cur_shutter = False
                    cur_wave = False
                    underline = False
                elif tag == 'type01':
                    cur_shutter = True
                elif tag == 'type02':
                    cur_wave = True
                elif tag.startswith('size'):
                    try:
                        cur_size = float(tag[4:]) if tag[4:] else 1.0
                    except ValueError:
                        pass
            elif part:
                self.canvas.appendRun(part, cur_color, self._make_font(cur_size, underline), cur_shutter, cur_wave)


class main_window(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("IconoParser")
        self.resize(1050, 780)
        self.setMinimumSize(800, 600)

        self.dialogIndexMap = {}
        self.dialogRowsMap = {}
        self.totalDialogs = 0
        self._selectingGroup = False
        self.searchResults = []
        self.searchResultIndex = -1
        self.animating = False
        self._animTimer = QTimer(self)
        self._animTimer.setSingleShot(True)
        self._animTimer.timeout.connect(self._scheduleNextChar)
        self._killTimer = QTimer(self)
        self._killTimer.setSingleShot(True)
        self._killTimer.timeout.connect(self._chainToNextDialog)
        self._currentText = ''
        self._currentSpeaker = ''
        self._currentBub = None
        self._renderSequence = []
        self._renderIndex = 0
        self._chainNextIdx = None
        self._chainKillMs = None

        families = set(QFontDatabase.families())
        font_name = next((f for f in PIXEL_FONT_CANDIDATES if f in families), 'Courier')
        self._pixelFont = QFont(font_name, 10)
        self._speakerFont = QFont(font_name, 10)
        self._speakerFont.setBold(True)

        self._buildMenuBar()
        self._buildUI()

        if os.path.isfile(GAME_DIA_PATH):
            self.processFileLoad(GAME_DIA_PATH)

    def _buildMenuBar(self):
        mb = self.menuBar()

        file_menu = mb.addMenu("File")
        for label, shortcut, slot in [
            ("Open File",   "Ctrl+O", self.openFile),
            ("Export",      "Ctrl+S", self.dataExport),
            ("Close File",  "",       self.closeFile),
        ]:
            act = QAction(label, self)
            if shortcut:
                act.setShortcut(shortcut)
            act.triggered.connect(slot)
            file_menu.addAction(act)
        file_menu.addSeparator()
        exit_act = QAction("Exit", self)
        exit_act.setShortcut("Ctrl+Q")
        exit_act.triggered.connect(self.close)
        file_menu.addAction(exit_act)

        help_menu = mb.addMenu("Help")
        for label, slot in [
            ("Getting Started",   self.starting_advice),
            ("I broke something!", self.broken_help),
            ("About",             self.about),
        ]:
            act = QAction(label, self)
            act.triggered.connect(slot)
            help_menu.addAction(act)

    def _buildUI(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(8, 4, 8, 8)
        root.setSpacing(6)

        instr = QLabel("Open a file via File > Open File, or drag a 'dia' file onto the table.")
        instr.setStyleSheet("color: #a6adc8; font-size: 11px;")
        root.addWidget(instr)

        # Navigation bar
        nav = QHBoxLayout()
        nav.setSpacing(6)
        self.prevBtn = QPushButton("◄ Prev")
        self.prevBtn.clicked.connect(self.prevDialog)
        nav.addWidget(self.prevBtn)
        nav.addWidget(QLabel("Go to index:"))
        self.indexEntry = QLineEdit()
        self.indexEntry.setFixedWidth(70)
        self.indexEntry.returnPressed.connect(self.goToIndex)
        nav.addWidget(self.indexEntry)
        go_btn = QPushButton("Go")
        go_btn.setFixedWidth(50)
        go_btn.clicked.connect(self.goToIndex)
        nav.addWidget(go_btn)
        self.nextBtn = QPushButton("Next ►")
        self.nextBtn.clicked.connect(self.nextDialog)
        nav.addWidget(self.nextBtn)
        self.navStatusLabel = QLabel("No file loaded")
        self.navStatusLabel.setStyleSheet("color: #a6adc8; font-size: 11px;")
        nav.addWidget(self.navStatusLabel)
        nav.addStretch()
        root.addLayout(nav)

        # Search bar
        search = QHBoxLayout()
        search.setSpacing(6)
        search.addWidget(QLabel("Search:"))
        self.searchEntry = QLineEdit()
        self.searchEntry.setFixedWidth(250)
        self.searchEntry.setPlaceholderText("Search dialog text…")
        self.searchEntry.returnPressed.connect(self.searchDialog)
        search.addWidget(self.searchEntry)
        find_btn = QPushButton("Find")
        find_btn.setFixedWidth(60)
        find_btn.clicked.connect(self.searchDialog)
        search.addWidget(find_btn)
        prev_m = QPushButton("◄")
        prev_m.setFixedWidth(36)
        prev_m.clicked.connect(self.prevMatch)
        search.addWidget(prev_m)
        next_m = QPushButton("►")
        next_m.setFixedWidth(36)
        next_m.clicked.connect(self.nextMatch)
        search.addWidget(next_m)
        self.searchStatusLabel = QLabel("")
        self.searchStatusLabel.setStyleSheet("color: #a6adc8; font-size: 11px;")
        search.addWidget(self.searchStatusLabel)
        search.addStretch()
        root.addLayout(search)

        # Vertical splitter: table on top, panels on bottom
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setChildrenCollapsible(False)
        root.addWidget(splitter, stretch=1)

        # Dialog table
        self.tableWidget = DialogTable()
        self.tableWidget.setColumnCount(3)
        self.tableWidget.setHorizontalHeaderLabels(["Index", "Dialog Part", "Text"])
        h = self.tableWidget.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.tableWidget.verticalHeader().setVisible(False)
        self.tableWidget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tableWidget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.tableWidget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tableWidget.setAlternatingRowColors(False)
        self.tableWidget.setShowGrid(False)
        self.tableWidget.setItemDelegate(_RowColorDelegate(self.tableWidget))
        self.tableWidget.currentCellChanged.connect(
            lambda cur_row, cur_col, prev_row, prev_col: self.onSelectionChange(cur_row)
        )
        self.tableWidget.fileDropped.connect(self.processFileLoad)
        splitter.addWidget(self.tableWidget)

        # Bottom panels
        bottom = QWidget()
        bottom_layout = QVBoxLayout(bottom)
        bottom_layout.setContentsMargins(0, 4, 0, 0)
        bottom_layout.setSpacing(8)
        splitter.addWidget(bottom)
        splitter.setSizes([320, 420])

        # Middle row: Modify Lines + Options Key
        mid = QHBoxLayout()
        mid.setSpacing(8)

        modify_group = QGroupBox("Modify Lines")
        ml = QVBoxLayout(modify_group)
        ml.setSpacing(4)
        ml.addWidget(QLabel("Speaker"))
        self.speakerEdit = QLineEdit()
        ml.addWidget(self.speakerEdit)
        ml.addWidget(QLabel("Dialog"))
        self.dialogEdit = QTextEdit()
        self.dialogEdit.setFixedHeight(70)
        ml.addWidget(self.dialogEdit)
        ml.addWidget(QLabel("Animation"))
        self.animEdit = QLineEdit()
        ml.addWidget(self.animEdit)
        save_btn = QPushButton("Save Changes")
        save_btn.clicked.connect(self.saveUpdatedRecord)
        ml.addWidget(save_btn)
        mid.addWidget(modify_group, stretch=1)

        key_group = QGroupBox("Dialog Options Key — Reference Only")
        kl = QVBoxLayout(key_group)
        kl.addWidget(QLabel("Dialog Bubble Style"))
        bub_cb = QComboBox()
        bub_cb.addItems([
            "{bub01}",
            "{bub03} = transparent (menus/UI)",
            "{bub04} = tutorials (no speaker)",
            "{bub05} = normal dialog (with speaker)",
            "{bub06} = normal dialog (no speaker)",
            "{bub07} = signage (no speaker)",
        ])
        kl.addWidget(bub_cb)
        color_font_row = QHBoxLayout()
        color_font_row.setSpacing(6)

        color_col = QVBoxLayout()
        color_col.setSpacing(2)
        color_col.addWidget(QLabel("Color Options"))
        color_cb = QComboBox()
        color_cb.addItems([
            "{dye00} = normal",          "{dye01} = red",
            "{dye02} = light yellow",    "{dye03} = unused",
            "{dye04} = yellow (names)",  "{dye05} = green",
            "{dye06} = light blue",      "{dye07} = grey",
            "{dye08} = unused text",     "{dye09} = cyan",
            "{dye10} = purple",
        ])
        color_col.addWidget(color_cb)
        color_font_row.addLayout(color_col)

        font_col = QVBoxLayout()
        font_col.setSpacing(2)
        font_col.addWidget(QLabel("Font"))
        font_cb = QComboBox()
        font_cb.addItems([
            "{font00} = default",
            "{font01} = small / dense",
            "{font02} = same as default",
            "{font04} = special symbols / icons",
            "{font06} = title screen / UI headers",
        ])
        font_col.addWidget(font_cb)
        color_font_row.addLayout(font_col)

        kl.addLayout(color_font_row)
        kl.addWidget(QLabel("Text Animations"))
        anim_cb = QComboBox()
        anim_cb.addItems(["{type00} = default", "{type01} = shutter (jitter)", "{type02} = wave (undulate)"])
        kl.addWidget(anim_cb)
        kl.addWidget(QLabel("Text Size"))
        size_cb = QComboBox()
        size_cb.addItems(["{size} = default size", "{size2.00} = double size"])
        kl.addWidget(size_cb)
        kl.addStretch()
        mid.addWidget(key_group, stretch=1)
        bottom_layout.addLayout(mid)

        # Preview — play button sits to the left of the bubble
        preview_group = QGroupBox("Rendered Preview")
        pl = QHBoxLayout(preview_group)
        pl.setSpacing(8)
        self.playButton = QPushButton("▶ Play")
        self.playButton.setObjectName("playButton")
        self.playButton.setFixedWidth(90)
        self.playButton.clicked.connect(self.playAnimation)
        pl.addWidget(self.playButton, alignment=Qt.AlignmentFlag.AlignTop)
        self.bubblePreview = BubblePreview(self._pixelFont, self._speakerFont)
        pl.addWidget(self.bubblePreview, stretch=1)
        bottom_layout.addWidget(preview_group)

        # Export button
        export_row = QHBoxLayout()
        export_row.addStretch()
        self.exportStatusLabel = QLabel("")
        self.exportStatusLabel.setStyleSheet("font-size: 11px;")
        export_row.addWidget(self.exportStatusLabel)
        export_btn = QPushButton("Export Changes")
        export_btn.setObjectName("exportButton")
        export_btn.clicked.connect(self.dataExport)
        export_row.addWidget(export_btn)
        root.addLayout(export_row)

    # ── File operations ──────────────────────────────────────────────────────

    def openFile(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Dialog File", "", "All Files (*)")
        if path:
            self.processFileLoad(path)

    def processFileLoad(self, path):
        if path.startswith('{') and path.endswith('}'):
            path = path[1:-1]

        data = fileParse.guiParse(path)
        self.tableWidget.setRowCount(0)
        self.dialogIndexMap = {}
        dialog_count = 0

        self.tableWidget.setUpdatesEnabled(False)
        for i, record in enumerate(data):
            if i == 0:
                continue  # skip header row from guiParse
            dialog_part = helperDict.DIALOG_FUNCTION[record[0]]
            text = record[2]

            if record[0] == 0:  # Speaker row — starts a new dialog group
                dialog_count += 1
                self.dialogIndexMap[dialog_count] = self.tableWidget.rowCount()

            row = self.tableWidget.rowCount()
            self.tableWidget.insertRow(row)

            idx_item = QTableWidgetItem(str(dialog_count))
            idx_item.setData(Qt.ItemDataRole.UserRole, dialog_count)
            idx_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            part_item = QTableWidgetItem(dialog_part)
            text_item = QTableWidgetItem(text)

            # Alternate whole groups (every 3 rows) with clearly distinct colors;
            # speaker row is slightly brighter within each group.
            if dialog_count % 2 == 1:
                row_bg = QColor('#263550') if record[0] == 0 else QColor('#1c2840')
            else:
                row_bg = QColor('#302840') if record[0] == 0 else QColor('#26202e')
            bg = QBrush(row_bg)
            for item in (idx_item, part_item, text_item):
                item.setBackground(bg)
                item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)

            self.tableWidget.setItem(row, 0, idx_item)
            self.tableWidget.setItem(row, 1, part_item)
            self.tableWidget.setItem(row, 2, text_item)

        self.tableWidget.setUpdatesEnabled(True)
        self.totalDialogs = dialog_count
        self._buildDialogRowsMap()
        self.navStatusLabel.setText(f"Dialogs: {self.totalDialogs}")
        self.searchResults = []
        self.searchResultIndex = -1
        self.searchStatusLabel.setText("")

    def _buildDialogRowsMap(self):
        self.dialogRowsMap = {}
        current_idx = None
        for row in range(self.tableWidget.rowCount()):
            item = self.tableWidget.item(row, 0)
            if not item:
                continue
            idx = item.data(Qt.ItemDataRole.UserRole)
            if idx != current_idx:
                current_idx = idx
                self.dialogRowsMap[current_idx] = []
            self.dialogRowsMap[current_idx].append(row)

    def closeFile(self):
        self.tableWidget.setRowCount(0)
        self.dialogIndexMap = {}
        self.dialogRowsMap = {}
        self.totalDialogs = 0
        self.navStatusLabel.setText("No file loaded")
        self.searchResults = []
        self.searchResultIndex = -1
        self.searchStatusLabel.setText("")
        self._stopAnimation()
        self.speakerEdit.clear()
        self.dialogEdit.clear()
        self.animEdit.clear()
        self.bubblePreview.clear()

    def dataExport(self):
        dataObject = []
        for row in range(self.tableWidget.rowCount()):
            part_item = self.tableWidget.item(row, 1)
            text_item = self.tableWidget.item(row, 2)
            if part_item and text_item:
                dataObject.append((
                    get_key(part_item.text()),
                    len(text_item.text()),
                    text_item.text(),
                ))
        self.exportStatusLabel.setStyleSheet("color: #a6adc8; font-size: 11px;")
        self.exportStatusLabel.setText("Saving…")
        QApplication.processEvents()
        try:
            fileParse.guiExport(dataObject, GAME_DIA_PATH)
            self.exportStatusLabel.setStyleSheet("color: #a6e3a1; font-size: 11px;")
            self.exportStatusLabel.setText("Saved successfully")
        except Exception as e:
            self.exportStatusLabel.setStyleSheet("color: #f38ba8; font-size: 11px;")
            self.exportStatusLabel.setText(f"Export failed: {e}")
        QTimer.singleShot(4000, lambda: self.exportStatusLabel.setText(""))

    # ── Navigation ───────────────────────────────────────────────────────────

    def getCurrentDialogIndex(self):
        row = self.tableWidget.currentRow()
        if row < 0:
            return None
        item = self.tableWidget.item(row, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def prevDialog(self):
        cur = self.getCurrentDialogIndex()
        if cur is not None and cur - 1 >= 1:
            self._navigateToDialogIndex(cur - 1)

    def nextDialog(self):
        cur = self.getCurrentDialogIndex()
        if cur is None:
            if self.totalDialogs > 0:
                self._navigateToDialogIndex(1)
        elif cur + 1 <= self.totalDialogs:
            self._navigateToDialogIndex(cur + 1)

    def goToIndex(self):
        try:
            self._navigateToDialogIndex(int(self.indexEntry.text()))
        except ValueError:
            pass

    def _navigateToDialogIndex(self, index):
        if index not in self.dialogIndexMap:
            return
        row = self.dialogIndexMap[index]
        self.tableWidget.selectRow(row)
        self.tableWidget.scrollToItem(self.tableWidget.item(row, 0))
        self.indexEntry.setText(str(index))

    # ── Search ───────────────────────────────────────────────────────────────

    def searchDialog(self):
        query = self.searchEntry.text().strip().lower()
        if not query:
            self.searchResults = []
            self.searchResultIndex = -1
            self.searchStatusLabel.setText("")
            return
        self.searchResults = [
            row for row in range(self.tableWidget.rowCount())
            if self.tableWidget.item(row, 2) and
               query in self.tableWidget.item(row, 2).text().lower()
        ]
        if self.searchResults:
            self.searchResultIndex = 0
            self._jumpToSearchResult()
        else:
            self.searchResultIndex = -1
            self.searchStatusLabel.setText("No results")

    def nextMatch(self):
        if not self.searchResults:
            return
        self.searchResultIndex = (self.searchResultIndex + 1) % len(self.searchResults)
        self._jumpToSearchResult()

    def prevMatch(self):
        if not self.searchResults:
            return
        self.searchResultIndex = (self.searchResultIndex - 1) % len(self.searchResults)
        self._jumpToSearchResult()

    def _jumpToSearchResult(self):
        row = self.searchResults[self.searchResultIndex]
        self.tableWidget.selectRow(row)
        self.tableWidget.scrollToItem(self.tableWidget.item(row, 0))
        self.searchStatusLabel.setText(
            f"{self.searchResultIndex + 1} of {len(self.searchResults)}"
        )

    # ── Editing ──────────────────────────────────────────────────────────────

    def _selectGroupRows(self, dialog_index):
        if dialog_index not in self.dialogRowsMap:
            return
        rows = self.dialogRowsMap[dialog_index]
        model = self.tableWidget.model()
        col_last = self.tableWidget.columnCount() - 1
        selection = QItemSelection()
        for r in rows:
            selection.select(model.index(r, 0), model.index(r, col_last))
        self.tableWidget.selectionModel().select(
            selection, QItemSelectionModel.SelectionFlag.ClearAndSelect
        )

    def onSelectionChange(self, row):
        if self._selectingGroup or row < 0:
            return
        dialog_index = self.getCurrentDialogIndex()
        if dialog_index is None:
            return

        self._selectingGroup = True
        try:
            self._selectGroupRows(dialog_index)
        finally:
            self._selectingGroup = False

        self._stopAnimation()

        speaker_text = dialog_text = anim_text = ''
        for r in self.dialogRowsMap.get(dialog_index, []):
            part = self.tableWidget.item(r, 1).text()
            text = self.tableWidget.item(r, 2).text()
            if part == 'Speaker':
                speaker_text = text
            elif part == 'Dialog':
                dialog_text = text
            elif part == 'Animation':
                anim_text = text

        self.speakerEdit.setText(speaker_text)
        self.dialogEdit.setPlainText(dialog_text)
        self.animEdit.setText(anim_text)

        self._currentText = dialog_text
        self._currentSpeaker = speaker_text
        self._currentBub = self._parseBubTag(dialog_text)
        self.bubblePreview.renderText(dialog_text, speaker_text, self._currentBub)

    def saveUpdatedRecord(self):
        dialog_index = self.getCurrentDialogIndex()
        if dialog_index is None or dialog_index not in self.dialogRowsMap:
            return
        for r in self.dialogRowsMap[dialog_index]:
            part = self.tableWidget.item(r, 1).text()
            text_item = self.tableWidget.item(r, 2)
            if not text_item:
                continue
            if part == 'Speaker':
                text_item.setText(self.speakerEdit.text())
            elif part == 'Dialog':
                text_item.setText(self.dialogEdit.toPlainText())
            elif part == 'Animation':
                text_item.setText(self.animEdit.text())
        self.onSelectionChange(self.tableWidget.currentRow())

    # ── Preview & animation ──────────────────────────────────────────────────

    def _parseBubTag(self, text):
        m = re.search(r'\{(bub\d+)\}', text)
        return m.group(1) if m else None

    def _parseNextKillTags(self, text):
        """Returns (next_dialog_index, kill_ms) parsed from {next} and {kill} tags."""
        next_idx = None
        kill_ms = None
        m = re.search(r'\{next\\(\d+)\\[^}]*\}', text)
        if m:
            next_idx = int(m.group(1))
        m = re.search(r'\{kill(\d+)\}', text)
        if m:
            kill_ms = int(m.group(1)) / 60 * 1000
        return next_idx, kill_ms

    def _buildRenderSequence(self, text):
        sequence = []
        parts = re.split(r'(\{[^}]+\})', text)
        current_color = '#ffffff'
        underline = False
        current_pace = 1.0
        current_size = 1.0
        current_shutter = False
        current_wave = False
        for part in parts:
            if part.startswith('{') and part.endswith('}'):
                tag = part[1:-1]
                if tag == 'new':
                    sequence.append({'char': '\n', 'color': current_color, 'underline': underline, 'pace': current_pace, 'size': current_size, 'shutter': current_shutter, 'wave': current_wave})
                elif tag in DYE_COLORS:
                    current_color = DYE_COLORS[tag]
                elif tag == 'type00':
                    current_shutter = False
                    current_wave = False
                    underline = False
                elif tag == 'type01':
                    current_shutter = True
                elif tag == 'type02':
                    current_wave = True
                elif tag.startswith('pace'):
                    try:
                        current_pace = float(tag[4:])
                    except ValueError:
                        pass
                elif tag.startswith('size'):
                    try:
                        current_size = float(tag[4:]) if tag[4:] else 1.0
                    except ValueError:
                        pass
            elif part:
                for ch in part:
                    sequence.append({'char': ch, 'color': current_color, 'underline': underline, 'pace': current_pace, 'size': current_size, 'shutter': current_shutter, 'wave': current_wave})
        return sequence

    def playAnimation(self):
        if self.animating:
            self._stopAnimation()
            self.bubblePreview.renderText(self._currentText, self._currentSpeaker, self._currentBub)
            return
        self._chainNextIdx, self._chainKillMs = self._parseNextKillTags(self._currentText)
        self._renderSequence = self._buildRenderSequence(self._currentText)
        self._renderIndex = 0
        self.animating = True
        self.playButton.setText("■ Stop")

        show_speaker = self.bubblePreview.applyBubStyle(self._currentBub)
        self.bubblePreview.canvas.clear()
        if self._currentSpeaker and show_speaker:
            self.bubblePreview.canvas.appendRun(
                self._currentSpeaker + '\n', QColor('#FFFF00'), self._speakerFont
            )

        self._animTimer.start(1)

    def _scheduleNextChar(self):
        if not self.animating or self._renderIndex >= len(self._renderSequence):
            if self._chainNextIdx is not None:
                delay = max(1, int(self._chainKillMs)) if self._chainKillMs else 1500
                self._killTimer.start(delay)
            else:
                self._stopAnimation()
            return
        item = self._renderSequence[self._renderIndex]
        self._renderIndex += 1
        font = QFont(self._pixelFont)
        if item['size'] != 1.0:
            font.setPointSizeF(self._pixelFont.pointSizeF() * item['size'])
        if item['underline']:
            font.setUnderline(True)
        self.bubblePreview.canvas.appendChar(
            item['char'], QColor(item['color']), font, item['shutter'], item['wave']
        )
        self._animTimer.start(max(1, int(item['pace'] * BASE_PACE_MS)))

    def _chainToNextDialog(self):
        next_idx = self._chainNextIdx
        self._chainNextIdx = None
        self._chainKillMs = None

        if next_idx is None or next_idx not in self.dialogIndexMap:
            self._stopAnimation()
            return

        self._selectingGroup = True
        try:
            self._navigateToDialogIndex(next_idx)
            self._selectGroupRows(next_idx)
        finally:
            self._selectingGroup = False

        speaker_text = dialog_text = anim_text = ''
        for r in self.dialogRowsMap.get(next_idx, []):
            part = self.tableWidget.item(r, 1).text()
            text = self.tableWidget.item(r, 2).text()
            if part == 'Speaker':
                speaker_text = text
            elif part == 'Dialog':
                dialog_text = text
            elif part == 'Animation':
                anim_text = text

        self.speakerEdit.setText(speaker_text)
        self.dialogEdit.setPlainText(dialog_text)
        self.animEdit.setText(anim_text)

        self._currentText = dialog_text
        self._currentSpeaker = speaker_text
        self._currentBub = self._parseBubTag(dialog_text)
        self._chainNextIdx, self._chainKillMs = self._parseNextKillTags(dialog_text)

        self._renderSequence = self._buildRenderSequence(dialog_text)
        self._renderIndex = 0

        show_speaker = self.bubblePreview.applyBubStyle(self._currentBub)
        self.bubblePreview.canvas.clear()
        if speaker_text and show_speaker:
            self.bubblePreview.canvas.appendRun(
                speaker_text + '\n', QColor('#FFFF00'), self._speakerFont
            )

        self._animTimer.start(1)

    def _stopAnimation(self):
        self._animTimer.stop()
        self._killTimer.stop()
        self._chainNextIdx = None
        self._chainKillMs = None
        self.animating = False
        if hasattr(self, 'playButton'):
            self.playButton.setText("▶ Play")

    # ── Help dialogs ─────────────────────────────────────────────────────────

    def about(self):
        self._help_dialog("About", (
            "IconoParser\n\n"
            "A tool for editing dialog files in Iconoclasts.\n"
            "Created by Squiblydoo.\n"
            "Robin art is by Sho Sakazaki, used with permission."
        ))

    def broken_help(self):
        self._help_dialog("I broke something!", (
            "If you want to revert changes, there are two options.\n\n"
            "1) A backup copy is created with '_backup' in the same directory as "
            "the file you edited. Replace the current file with it.\n\n"
            "2) Use 'Verify Game Files' in Steam to restore all original files."
        ))

    def starting_advice(self):
        self._help_dialog("Getting Started", (
            "Open a 'dia' file via File > Open File, or drag it onto the table.\n\n"
            "Edit text in the Modify Lines box and press Save Changes.\n"
            "When done, click Export Changes or use File > Export.\n\n"
            "Game files are at:\n"
            "Windows:  C:/…/Steam/steamapps/common/Iconoclasts/data/\n"
            "Mac:      ~/Library/…/Steam/steamapps/common/Iconoclasts/data/\n"
            "Linux:    ~/.local/share/Steam/steamapps/common/Iconoclasts/data/"
        ))

    def _help_dialog(self, title, text):
        dlg = QDialog(self)
        dlg.setWindowTitle(title)
        dlg.resize(460, 240)
        layout = QVBoxLayout(dlg)
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(lbl)
        ok = QPushButton("OK")
        ok.clicked.connect(dlg.accept)
        layout.addWidget(ok, alignment=Qt.AlignmentFlag.AlignCenter)
        dlg.exec()


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_THEME)
    window = main_window()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
