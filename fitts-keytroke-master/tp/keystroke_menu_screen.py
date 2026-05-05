from __future__ import annotations
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QSizePolicy
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from constants import t


class KeystrokeMenuScreen(QWidget):
    """
    Menu screen that allows the user to choose between keystroke experiments.
    """

    def __init__(self, main_window: object) -> None:
        super().__init__()
        self.main_window = main_window
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignCenter)

        self.label = QLabel()
        self.label.setObjectName("TitleLabel")
        self.label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.label)

        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(24)
        btn_layout.setAlignment(Qt.AlignCenter)

        # Button for Cognitive Load Impact experiment
        self.btn_cognitive = QPushButton()
        self.btn_cognitive.setIcon(QIcon("icons/keyboard_white.svg"))
        self.btn_cognitive.setIconSize(QSize(32, 32))
        self.btn_cognitive.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.btn_cognitive.clicked.connect(lambda: self.main_window.switch_screen(5))  # Cognitive load experiment is at index 5
        btn_layout.addWidget(self.btn_cognitive)

        # Button for Keyboard vs. Mouse Navigation experiment
        self.btn_navigation = QPushButton()
        self.btn_navigation.setIcon(QIcon("icons/keyboard_white.svg"))
        self.btn_navigation.setIconSize(QSize(32, 32))
        self.btn_navigation.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.btn_navigation.clicked.connect(lambda: self.main_window.switch_screen(6))  # Navigation experiment is at index 6
        btn_layout.addWidget(self.btn_navigation)

        # Back button
        self.back_btn = QPushButton()
        self.back_btn.setObjectName("SmallNavButton")
        self.back_btn.clicked.connect(lambda: self.main_window.switch_screen(0))
        self.back_btn.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        
        main_layout.addLayout(btn_layout)
        main_layout.addWidget(self.back_btn, alignment=Qt.AlignCenter)
        self.setLayout(main_layout)
        self.refresh_ui()

    def refresh_ui(self) -> None:
        self.label.setText(t("keystroke_menu_title"))
        self.btn_cognitive.setText(f"  {t('cognitive_load_btn')}")
        self.btn_navigation.setText(f"  {t('navigation_btn')}")
        self.back_btn.setText(t("back_menu"))
