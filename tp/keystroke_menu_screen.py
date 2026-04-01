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
        btn_k = QPushButton(" Expérience K - Temps de frappe clavier")
        btn_k.setIcon(QIcon("icons/keyboard_white.svg"))
        btn_k.setIconSize(QSize(32, 32))
        btn_k.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        btn_k.setToolTip("Mesure empirique du temps moyen pour appuyer sur une touche (opérateur K)")
        btn_k.clicked.connect(lambda: self.main_window.switch_screen(7))
        btn_layout.addWidget(btn_k)

        # Button: H operator experiment
        btn_h2 = QPushButton("  Expérience  H - Changement main clavier → souris")
        btn_h2.setIcon(QIcon("icons/keyboard_white.svg"))
        btn_h2.setIconSize(QSize(32, 32))
        btn_h2.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        btn_h2.setToolTip("Mesure empirique du temps de changement de dispositif main clavier vers souris (opérateur H)")
        btn_h2.clicked.connect(lambda: self.main_window.switch_screen(8))
        btn_layout.addWidget(btn_h2)

        # Button: C experiment
        btn_c = QPushButton("  Expérience C - Ouverture de fichier Souris vs Clavier")
        btn_c.setIcon(QIcon("icons/play_white.svg"))
        btn_c.setIconSize(QSize(32, 32))
        btn_c.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        btn_c.setToolTip("Comparaison souris vs clavier + validation du modèle GOMS théorique")
        btn_c.clicked.connect(lambda: self.main_window.switch_screen(9))
        btn_layout.addWidget(btn_c)

        main_layout.addLayout(btn_layout)

        main_layout.addLayout(btn_layout)


        # Bottom row : Retour | Paramètres des durées
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(0)

        back_btn = QPushButton("← Retour")
        back_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        back_btn.clicked.connect(lambda: self.main_window.switch_screen(0))
        bottom_row.addWidget(back_btn)

        settings_btn = QPushButton("⚙  Paramètres des durées")
        settings_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        settings_btn.setToolTip("Définir manuellement les valeurs empiriques K, H, P, M")
        settings_btn.clicked.connect(lambda: self.main_window.switch_screen(10))
        bottom_row.addWidget(settings_btn)

        main_layout.addSpacing(2)
        main_layout.addLayout(bottom_row)
        self.setLayout(main_layout)
