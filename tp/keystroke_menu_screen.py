from __future__ import annotations
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QSizePolicy
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon


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

        label = QLabel(" Choisir une expérience Keystroke")
        label.setObjectName("TitleLabel")
        label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(label)

        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(24)
        btn_layout.setAlignment(Qt.AlignCenter)

        # Button: K operator experiment
        btn_k = QPushButton(" Expérience K — Temps de frappe clavier")
        btn_k.setIcon(QIcon("icons/keyboard_white.svg"))
        btn_k.setIconSize(QSize(32, 32))
        btn_k.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        btn_k.setToolTip("Mesure empirique du temps moyen pour appuyer sur une touche (opérateur K)")
        btn_k.clicked.connect(lambda: self.main_window.switch_screen(7))
        btn_layout.addWidget(btn_k)

        # Button: H operator experiment
        btn_h = QPushButton("  Expérience 1 H — Changement main clavier → souris")
        btn_h.setIcon(QIcon("icons/keyboard_white.svg"))
        btn_h.setIconSize(QSize(32, 32))
        btn_h.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        btn_h.setToolTip("Mesure empirique du temps de transfert main clavier vers souris (opérateur H)")
        btn_h.clicked.connect(lambda: self.main_window.switch_screen(8))
        btn_layout.addWidget(btn_h)

        # Button: H2 operator experiment
        btn_h2 = QPushButton("  Expérience 2 H — Changement main clavier → souris")
        btn_h2.setIcon(QIcon("icons/keyboard_white.svg"))
        btn_h2.setIconSize(QSize(32, 32))
        btn_h2.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        btn_h2.setToolTip("Mesure empirique du temps de transfert main clavier vers souris (opérateur H)")
        btn_h2.clicked.connect(lambda: self.main_window.switch_screen(9))
        btn_layout.addWidget(btn_h2)

        # Button for Cognitive Load Impact experiment
        # btn_cognitive = QPushButton("  Cognitive Load Impact on Typing Performance")
        # btn_cognitive.setIcon(QIcon("icons/keyboard_white.svg"))
        # btn_cognitive.setIconSize(QSize(32, 32))
        # btn_cognitive.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        # btn_cognitive.clicked.connect(lambda: self.main_window.switch_screen(5))  # Cognitive load experiment is at index 5
        # btn_layout.addWidget(btn_cognitive)

        # Button for Keyboard vs. Mouse Navigation experiment
        # btn_navigation = QPushButton("  Keyboard vs. Mouse Text Navigation Efficiency")
        # btn_navigation.setIcon(QIcon("icons/keyboard_white.svg"))
        # btn_navigation.setIconSize(QSize(32, 32))
        # btn_navigation.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        # btn_navigation.clicked.connect(lambda: self.main_window.switch_screen(6))  # Navigation experiment is at index 6
        # btn_layout.addWidget(btn_navigation)

        # Back button
        back_btn = QPushButton(" ← Menu Principal")
        back_btn.clicked.connect(lambda: self.main_window.switch_screen(0))
        back_btn.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        
        main_layout.addLayout(btn_layout)
        main_layout.addWidget(back_btn, alignment=Qt.AlignCenter)
        self.setLayout(main_layout)
