from __future__ import annotations
import json
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QSizePolicy, QFrame, QLineEdit
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from tp.constants import Settings, DEFAULT_K_MS, DEFAULT_H_MS, DEFAULT_P_MS, DEFAULT_M_MS

# Persistence
SAVE_FILE = os.path.join(os.path.dirname(__file__), "goms_settings.json")

STEP_MS: float = 100.0     # Increment/decrement step
MIN_MS:  float = 100.0     # Minimum allowed value
MAX_MS:  float = 5000.0   # Maximum allowed value


def load_goms_settings() -> None:
    """Load saved GOMS values from disk into Settings (called at startup)."""
    if not os.path.exists(SAVE_FILE):
        return
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        Settings.K = float(data.get("K", Settings.K))
        Settings.H = float(data.get("H", Settings.H))
        Settings.P = float(data.get("P", Settings.P))
        Settings.M = float(data.get("M", Settings.M))
    except (json.JSONDecodeError, KeyError, ValueError):
        pass   # Corrupted file – keep defaults


def save_goms_settings() -> None:
    """Persist current Settings GOMS values to disk."""
    data = {"K": Settings.K, "H": Settings.H, "P": Settings.P, "M": Settings.M}
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# Reusable ± spinbox row

class SpinRow(QFrame):
    """
    A horizontal row with:
      label  |  [ — ]   value (ms)   [ + ]
    """

    def __init__(self, label_text: str, initial_value: float, parent=None):
        super().__init__(parent)
        self._value: float = initial_value

        self.setStyleSheet("QFrame { background: transparent; border: none; }")

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(20)

        # Label (left)
        lbl = QLabel(label_text)
        lbl.setStyleSheet("color: #f3f3f3; font-size: 16px; background: transparent; border: none;")
        lbl.setFixedWidth(280)
        row.addWidget(lbl)

        # Pill control (— · value · +)
        pill = QFrame()
        pill.setFixedHeight(56)
        pill.setStyleSheet(
            "QFrame { background: #232a34; border-radius: 28px; border: none; }"
        )
        pill_layout = QHBoxLayout(pill)
        pill_layout.setContentsMargins(6, 4, 6, 4)
        pill_layout.setSpacing(0)

        btn_style = (
            "QPushButton { background: transparent; color: #f3f3f3; border: none; "
            "font-size: 26px; font-weight: bold; padding: 2px 20px; margin: 0; border-radius: 0; }"
            "QPushButton:hover { color: #7fd1b9; }"
            "QPushButton:pressed { color: #2ecc71; }"
        )

        self.minus_btn = QPushButton("−")
        self.minus_btn.setStyleSheet(btn_style)
        self.minus_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.minus_btn.clicked.connect(self._decrement)
        pill_layout.addWidget(self.minus_btn)

        self.value_edit = QLineEdit(f"{int(self._value)}")
        self.value_edit.setAlignment(Qt.AlignCenter)
        self.value_edit.setMinimumWidth(120)
        self.value_edit.setStyleSheet(
            "QLineEdit { color: #f3f3f3; font-size: 18px; font-weight: 600; "
            "background: transparent; border: none; border-radius: 0; }"
        )
        self.value_edit.editingFinished.connect(self._on_edit_finished)
        pill_layout.addWidget(self.value_edit, stretch=1)

        self.plus_btn = QPushButton("+")
        self.plus_btn.setStyleSheet(btn_style)
        self.plus_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.plus_btn.clicked.connect(self._increment)
        pill_layout.addWidget(self.plus_btn)

        row.addWidget(pill, stretch=1)

    # Value management

    def _increment(self) -> None:
        self._value = min(self._value + STEP_MS, MAX_MS)
        self._refresh()

    def _decrement(self) -> None:
        self._value = max(self._value - STEP_MS, MIN_MS)
        self._refresh()

    def _refresh(self) -> None:
        self.value_edit.setText(f"{int(self._value)}")

    def _on_edit_finished(self) -> None:
        """Parse manual input, clamp to [MIN_MS, MAX_MS]."""
        try:
            v = float(self.value_edit.text().replace(",", ".").strip())
            self._value = max(MIN_MS, min(MAX_MS, round(v / STEP_MS) * STEP_MS))
        except ValueError:
            pass
        self._refresh()

    @property
    def value(self) -> float:
        return self._value

    @value.setter
    def value(self, v: float) -> None:
        self._value = max(MIN_MS, min(MAX_MS, float(v)))
        self.value_edit.setText(f"{int(self._value)}")


# Main screen

class KeystrokeSettingsScreen(QWidget):
    """
    Screen to view and edit the GOMS/Keystroke empirical operator times
    (K, P, H, M).  Values are persisted to disk so they survive restarts.
    """

    def __init__(self, main_window: object) -> None:
        super().__init__()
        self.main_window = main_window
        self._init_ui()

    def _init_ui(self) -> None:
        root = QVBoxLayout()
        root.setContentsMargins(48, 32, 48, 32)
        root.setSpacing(0)
        self.setLayout(root)

        # Title
        title = QLabel("Paramètres des durées théoriques")
        title.setObjectName("TitleLabel")
        title.setAlignment(Qt.AlignLeft)
        root.addWidget(title)
        root.addSpacing(24)

        # Spin rows
        self.row_K = SpinRow("K : Frappe/clic (en ms) :", Settings.K)
        self.row_P = SpinRow("P : Déplacement de souris (en ms) :", Settings.P)
        self.row_H = SpinRow("H : Changement souris-clavier (en ms) :", Settings.H)
        self.row_M = SpinRow("M : Réflexion mentale (en ms) :", Settings.M)

        for row in (self.row_K, self.row_P, self.row_H, self.row_M):
            root.addWidget(row)
            root.addSpacing(18)

        root.addStretch()

        # Bottom bar
        bottom = QFrame()
        bottom_layout = QHBoxLayout(bottom)
        bottom_layout.setContentsMargins(20, 10, 20, 10)
        bottom_layout.setSpacing(16)

        reset_btn = QPushButton("Réinitialiser")
        reset_btn.setFixedHeight(52)
        reset_btn.setMinimumWidth(200)
        reset_btn.setStyleSheet(
            "QPushButton { background: #2d3a4b; color: #aaaaaa; border: none; "
            "border-radius: 12px; padding: 12px 36px; font-size: 16px; font-weight: 600; margin: 0; }"
            "QPushButton:hover { color: #f3f3f3; background: #3a4a5b; }"
        )
        reset_btn.clicked.connect(self._reset_defaults)
        bottom_layout.addWidget(reset_btn)

        bottom_layout.addStretch()

        # Status label (feedback after save)
        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet("color: #2ecc71; font-size: 15px; background: transparent;")
        bottom_layout.addWidget(self.status_lbl)

        save_btn = QPushButton("💾  Enregistrer les paramètres")
        save_btn.setFixedHeight(52)
        save_btn.setMinimumWidth(300)
        save_btn.setStyleSheet(
            "QPushButton { background: #232a34; color: #f3f3f3; border: none; "
            "border-radius: 12px; padding: 12px 40px; font-size: 16px; "
            "font-weight: 600; margin: 0; }"
            "QPushButton:hover { background: #2d3a4b; color: #7fd1b9; }"
            "QPushButton:pressed { background: #1a2230; }"
        )
        save_btn.clicked.connect(self._save)
        bottom_layout.addWidget(save_btn)

        root.addWidget(bottom)

    # Slots

    def showEvent(self, event) -> None:  # noqa: N802
        """Refresh displayed values each time the screen is shown."""
        super().showEvent(event)
        self.row_K.value = Settings.K
        self.row_P.value = Settings.P
        self.row_H.value = Settings.H
        self.row_M.value = Settings.M
        self.status_lbl.setText("")

    def _save(self) -> None:
        """Apply values to Settings and persist to disk."""
        Settings.K = self.row_K.value
        Settings.P = self.row_P.value
        Settings.H = self.row_H.value
        Settings.M = self.row_M.value
        save_goms_settings()
        self.status_lbl.setText("✔  Enregistré")
        # Clear feedback after 2 s
        from PySide6.QtCore import QTimer
        QTimer.singleShot(2000, lambda: self.status_lbl.setText(""))

    def _reset_defaults(self) -> None:
        """Restore GOMS default values in the UI (does not save yet)."""
        self.row_K.value = DEFAULT_K_MS
        self.row_P.value = DEFAULT_P_MS
        self.row_H.value = DEFAULT_H_MS
        self.row_M.value = DEFAULT_M_MS
        self.status_lbl.setText("")