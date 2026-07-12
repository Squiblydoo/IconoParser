import os
import subprocess
import sys

from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)


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
QLabel#title {
    color: #89b4fa;
    font-size: 26px;
    font-weight: 700;
}
QLabel#subtitle {
    color: #bac2de;
    font-size: 13px;
}
QFrame#card {
    background-color: #181825;
    border: 1px solid #313244;
    border-radius: 10px;
}
QPushButton {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 8px;
    padding: 8px 14px;
    min-height: 34px;
    text-align: left;
}
QPushButton:hover { background-color: #45475a; border-color: #89b4fa; }
QPushButton:pressed { background-color: #585b70; }
QPushButton#accent {
    background-color: #1e3a5f;
    border-color: #89b4fa;
    color: #89b4fa;
    font-weight: 600;
}
QStatusBar {
    background-color: #181825;
    color: #9399b2;
    border-top: 1px solid #313244;
}
"""


class main_window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IconoParser Launcher")
        self.resize(860, 560)
        self.setMinimumSize(720, 440)

        if getattr(sys, "frozen", False):
            self._base_dir = os.path.dirname(os.path.abspath(sys.executable))
        else:
            self._base_dir = os.path.dirname(os.path.abspath(__file__))

        self._build_menu()
        self._build_ui()

        status = QStatusBar(self)
        status.showMessage("Ready")
        self.setStatusBar(status)

    def _build_menu(self):
        menu = self.menuBar()
        file_menu = menu.addMenu("File")

        file_menu.addAction("Open Dialog Editor", self.open_text_editor)
        file_menu.addAction("Open Save Editor", self.open_save_editor)
        file_menu.addAction("Open Cut Scene Editor", self.open_cut_scene_editor)
        file_menu.addAction("Open Warp Editor", self.open_warp_editor)
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.close)

        help_menu = menu.addMenu("Help")
        help_menu.addAction("About", self._about)

    def _build_ui(self):
        root = QWidget(self)
        self.setCentralWidget(root)

        outer = QVBoxLayout(root)
        outer.setContentsMargins(28, 26, 28, 24)
        outer.setSpacing(16)

        title = QLabel("IconoParser Toolkit")
        title.setObjectName("title")
        subtitle = QLabel(
            "Launch editors for dialogue, saves, cutscenes, and warps."
        )
        subtitle.setObjectName("subtitle")
        subtitle.setWordWrap(True)

        outer.addWidget(title)
        outer.addWidget(subtitle)

        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 18, 18, 18)
        card_layout.setSpacing(10)

        launch_grid = QGridLayout()
        launch_grid.setHorizontalSpacing(10)
        launch_grid.setVerticalSpacing(10)

        self._dialog_btn = QPushButton("Dialog Editor  -  Edit dia text files")
        self._dialog_btn.setObjectName("accent")
        self._dialog_btn.clicked.connect(self.open_text_editor)
        launch_grid.addWidget(self._dialog_btn, 0, 0)

        self._save_btn = QPushButton("Save Editor  -  Edit MAP1.0 save files")
        self._save_btn.clicked.connect(self.open_save_editor)
        launch_grid.addWidget(self._save_btn, 0, 1)

        self._scene_btn = QPushButton("Cut Scene Visualizer  -  View scene timeline")
        self._scene_btn.clicked.connect(self.open_cut_scene_editor)
        launch_grid.addWidget(self._scene_btn, 1, 0)

        self._warp_btn = QPushButton("Warp Editor  -  Quick save/warp tools")
        self._warp_btn.clicked.connect(self.open_warp_editor)
        launch_grid.addWidget(self._warp_btn, 1, 1)

        card_layout.addLayout(launch_grid)
        outer.addWidget(card)

        hint = QLabel(
            "Each editor is launched in a separate process so Tk and PyQt tools can "
            "run side-by-side without event-loop conflicts."
        )
        hint.setStyleSheet("color: #9399b2;")
        hint.setWordWrap(True)
        outer.addWidget(hint)

        outer.addStretch(1)

    def _launch_script(self, script_name, label):
        try:
            if getattr(sys, "frozen", False):
                base = self._base_dir
                stem = os.path.splitext(script_name)[0]
                candidates = [
                    os.path.join(base, stem),
                    os.path.join(base, stem + ".exe"),
                ]
                for candidate in candidates:
                    if os.path.isfile(candidate):
                        subprocess.Popen([candidate], cwd=base)
                        self.statusBar().showMessage(f"Launched {label}", 4000)
                        return

                QMessageBox.critical(
                    self,
                    "File missing",
                    f"Could not find a bundled executable for {label}.\n"
                    f"Expected one of:\n- {candidates[0]}\n- {candidates[1]}",
                )
                return

            script_path = os.path.join(self._base_dir, script_name)
            if not os.path.isfile(script_path):
                QMessageBox.critical(
                    self,
                    "File missing",
                    f"Could not find {script_name} in:\n{self._base_dir}",
                )
                return

            subprocess.Popen([sys.executable, script_path], cwd=self._base_dir)
            self.statusBar().showMessage(f"Launched {label}", 4000)
        except Exception as exc:
            QMessageBox.critical(self, "Launch failed", f"{label} failed to launch:\n{exc}")

    def open_text_editor(self):
        self._launch_script("IconoParserGUI.py", "Dialog Editor")

    def open_save_editor(self):
        self._launch_script("saveEditor.py", "Save Editor")

    def open_cut_scene_editor(self):
        self._launch_script("cutsceneVis.py", "Cut Scene Visualizer")

    def open_warp_editor(self):
        self._launch_script("warpGUI.py", "Warp Editor")

    def _about(self):
        QMessageBox.information(
            self,
            "About",
            "IconoParser Launcher\n\n"
            "Unified launcher for Iconoclasts editing tools with a modern UI "
            "and process-safe editor startup.",
        )


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_THEME)
    window = main_window()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()