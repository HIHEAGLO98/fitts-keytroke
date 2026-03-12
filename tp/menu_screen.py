from __future__ import annotations
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox, QHBoxLayout, QSizePolicy
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon


class MenuScreen(QWidget):
    """
    Menu screen that allows the user to choose between experiments.
    """

    def __init__(self, main_window: object) -> None:
        super().__init__()
        self.main_window = main_window
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignCenter)

        label = QLabel("Choose an Experiment")
        label.setObjectName("TitleLabel")
        label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(label)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(24)
        btn_layout.setAlignment(Qt.AlignCenter)

        btn_fitts = QPushButton("  Fitts Experiment")
        # Use a custom SVG icon with white color for contrast
        btn_fitts.setIcon(QIcon("icons/play_white.svg"))
        btn_fitts.setIconSize(QSize(48, 48))
        btn_fitts.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        btn_fitts.clicked.connect(lambda: self.main_window.switch_screen(1))
        btn_layout.addWidget(btn_fitts)

        btn_keystroke = QPushButton("  Keystroke Experiment")
        btn_keystroke.setIcon(QIcon("icons/keyboard_white.svg"))
        btn_keystroke.setIconSize(QSize(48, 48))
        btn_keystroke.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        btn_keystroke.clicked.connect(lambda: self.main_window.switch_screen(4))
        btn_layout.addWidget(btn_keystroke)

        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)

    def not_implemented(self) -> None:
        """
        Display an information dialog for the unimplemented experiment.
        """
        msg = QMessageBox(self)
        msg.setWindowTitle("Info")
        msg.setText("Keystroke Experiment not implemented yet.")
        msg.exec()
