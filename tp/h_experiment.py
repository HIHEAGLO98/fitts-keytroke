from __future__ import annotations
import time
import random
import math
import statistics
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar, QGroupBox, QSizePolicy,
    QFrame
)
from PySide6.QtCore import Qt, QTimer, QRect, QPoint
from PySide6.QtGui import QFont, QMouseEvent, QPainter, QColor, QPen, QBrush

from constants import Settings

# Experiment configuration
NUM_TRIALS: int = 15          # Number of click trials
TARGET_W: int = 120           # Target button width  (px) – intentionally large
TARGET_H: int = 60            # Target button height (px) – intentionally large


class ClickTarget(QFrame):
    """
    A large clickable target drawn on a canvas.
    Reports click coordinates and time via a callback.
    """

    def __init__(self, parent: QWidget, on_click_cb) -> None:
        super().__init__(parent)
        self.on_click_cb = on_click_cb
        self.active = False          # True when the signal has fired
        self._target_rect = QRect()  # Where the target circle is drawn
        self.setMinimumHeight(260)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_active(self, pos: QPoint) -> None:
        """Show the target at *pos* (centre) and accept clicks."""
        hw, hh = TARGET_W // 2, TARGET_H // 2
        self._target_rect = QRect(pos.x() - hw, pos.y() - hh, TARGET_W, TARGET_H)
        self.active = True
        self.update()

    def set_inactive(self) -> None:
        self.active = False
        self._target_rect = QRect()
        self.update()

    # Painting

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if self.active and not self._target_rect.isNull():
            # Glowing green target ellipse
            painter.setPen(QPen(QColor("#2ecc71"), 3))
            painter.setBrush(QBrush(QColor(46, 204, 113, 80)))
            painter.drawEllipse(self._target_rect)
            # Cross-hair at centre
            cx = self._target_rect.center().x()
            cy = self._target_rect.center().y()
            painter.setPen(QPen(QColor("#2ecc71"), 2))
            painter.drawLine(cx - 16, cy, cx + 16, cy)
            painter.drawLine(cx, cy - 16, cx, cy + 16)
        else:
            # Idle hint
            painter.setPen(QColor("#555555"))
            painter.setFont(QFont("Arial", 12))
            painter.drawText(self.rect(), Qt.AlignCenter,
                             "La cible apparaîtra ici\naprès votre signal.")

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self.active and self._target_rect.contains(event.pos()):
            click_time = time.perf_counter()
            # Compute distance from click to target centre
            cx = self._target_rect.center().x()
            cy = self._target_rect.center().y()
            dist = math.hypot(event.pos().x() - cx, event.pos().y() - cy)
            self.on_click_cb(click_time, hit=True, dist=dist)
            self.set_inactive()
        elif self.active:
            # Miss – visual flash
            self.on_click_cb(None, hit=False, dist=0)


# Main experiment widget

class HExperiment(QWidget):
    """
    Experiment screen to empirically estimate the H (hand-movement) operator.

    Protocol
    --------
    1. User places both hands on the keyboard and presses SPACE.
    2. After a random delay, a large green target appears on the canvas.
    3. User moves hand to mouse and clicks the target as quickly as possible.
    4. Δt = t_click − t_signal is recorded.
    5. We subtract the estimated Fitts pointing time T_p = a + b·log2(D/W + 1)
       (using the current Settings coefficients and the measured click distance D).
    6. After NUM_TRIALS, we compute mean, std-dev and display H_empirique.
    """

    def __init__(self, main_window: object) -> None:
        super().__init__()
        self.main_window = main_window

        # State
        self.trials_done: int = 0
        self.raw_deltas: list[float] = []      # Δt in ms (total = H + T_fitts)
        self.fitts_times: list[float] = []     # Estimated T_fitts for each trial (ms)
        self.signal_time: float = 0.0
        self.waiting_for_space: bool = False
        self.waiting_for_click: bool = False

        self._delay_timer = QTimer(self)
        self._delay_timer.setSingleShot(True)
        self._delay_timer.timeout.connect(self._show_target)

        self._init_ui()

    # UI

    def _init_ui(self) -> None:
        root = QVBoxLayout()
        root.setSpacing(16)
        root.setContentsMargins(32, 24, 32, 24)

        # Title
        title = QLabel("Expérience H — Changement main clavier → souris")
        title.setObjectName("TitleLabel")
        title.setAlignment(Qt.AlignCenter)
        root.addWidget(title)

        # Instructions
        self.instructions_label = QLabel(
            "Cliquez sur <b>Démarrer</b> pour commencer.<br>"
            "À chaque essai : posez les deux mains sur le clavier, puis appuyez "
            "sur <b>Espace</b>.<br>"
            "Dès qu'une cible verte apparaît, saisissez la souris et cliquez "
            "dessus <b>aussi vite que possible</b>."
        )
        self.instructions_label.setWordWrap(True)
        self.instructions_label.setAlignment(Qt.AlignCenter)
        root.addWidget(self.instructions_label)

        # Status banner
        self.status_label = QLabel("—")
        self.status_label.setAlignment(Qt.AlignCenter)
        status_font = QFont()
        status_font.setPointSize(16)
        status_font.setBold(True)
        self.status_label.setFont(status_font)
        self.status_label.setStyleSheet("color: #f39c12;")
        root.addWidget(self.status_label)

        # Click canvas
        self.canvas = ClickTarget(self, self._on_click)
        self.canvas.setStyleSheet(
            "background-color: #1e2733; border: 1.5px solid #444; border-radius: 12px;"
        )
        root.addWidget(self.canvas, stretch=1)

        # Progress
        prog_layout = QHBoxLayout()
        self.progress_label = QLabel(f"Essai : 0 / {NUM_TRIALS}")
        prog_layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, NUM_TRIALS)
        self.progress_bar.setValue(0)
        self.progress_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        prog_layout.addWidget(self.progress_bar)
        root.addLayout(prog_layout)

        # Results box
        self.results_box = QGroupBox("Résultats")
        res_layout = QVBoxLayout()
        self.results_label = QLabel("")
        self.results_label.setWordWrap(True)
        self.results_label.setAlignment(Qt.AlignCenter)
        res_layout.addWidget(self.results_label)
        self.results_box.setLayout(res_layout)
        self.results_box.setVisible(False)
        root.addWidget(self.results_box)

        # Buttons
        btn_layout = QHBoxLayout()

        self.start_btn = QPushButton("▶ Démarrer")
        self.start_btn.clicked.connect(self._start_experiment)
        btn_layout.addWidget(self.start_btn)

        self.apply_btn = QPushButton("✔ Appliquer H aux paramètres")
        self.apply_btn.setVisible(False)
        self.apply_btn.clicked.connect(self._apply_h_to_settings)
        btn_layout.addWidget(self.apply_btn)

        self.reset_btn = QPushButton("↺ Recommencer")
        self.reset_btn.setVisible(False)
        self.reset_btn.clicked.connect(self._reset)
        btn_layout.addWidget(self.reset_btn)

        back_btn = QPushButton("← Menu Keystroke")
        back_btn.clicked.connect(lambda: self.main_window.switch_screen(4))
        btn_layout.addWidget(back_btn)

        root.addLayout(btn_layout)
        self.setLayout(root)

    # Experiment flow

    def _start_experiment(self) -> None:
        self.trials_done = 0
        self.raw_deltas = []
        self.fitts_times = []

        self.start_btn.setVisible(False)
        self.apply_btn.setVisible(False)
        self.reset_btn.setVisible(False)
        self.results_box.setVisible(False)
        self.progress_bar.setValue(0)
        self.progress_label.setText(f"Essai : 0 / {NUM_TRIALS}")

        self._ask_for_space()

    def _ask_for_space(self) -> None:
        """Invite l'utilisateur à poser les mains sur le clavier et appuyer Espace."""
        remaining = NUM_TRIALS - self.trials_done
        self.status_label.setText(
            f"Posez les deux mains sur le clavier puis appuyez sur  ESPACE  "
            f"({remaining} essai{'s' if remaining > 1 else ''} restant{'s' if remaining > 1 else ''})"
        )
        self.status_label.setStyleSheet("color: #f39c12;")
        self.canvas.set_inactive()
        self.waiting_for_space = True
        self.waiting_for_click = False
        self.setFocus()

    def keyPressEvent(self, event) -> None:
        if self.waiting_for_space and event.key() == Qt.Key_Space:
            self.waiting_for_space = False
            self.status_label.setText("Prêt…")
            self.status_label.setStyleSheet("color: #aaaaaa;")
            # Random delay 400–900 ms before target appears
            delay_ms = random.randint(400, 900)
            self._delay_timer.start(delay_ms)
        else:
            super().keyPressEvent(event)

    def _show_target(self) -> None:
        """Affiche la cible à une position aléatoire dans le canvas."""
        # Pick a random centre inside the canvas (with margin)
        margin = max(TARGET_W, TARGET_H)
        w = max(self.canvas.width() - margin, margin + 1)
        h = max(self.canvas.height() - margin, margin + 1)
        cx = random.randint(margin // 2, w)
        cy = random.randint(margin // 2, h)

        self.status_label.setText("🖱  CLIQUEZ !")
        self.status_label.setStyleSheet("color: #2ecc71; font-size: 20px;")
        self.signal_time = time.perf_counter()
        self.canvas.set_active(QPoint(cx, cy))
        self.waiting_for_click = True

    def _on_click(self, click_time: float | None, hit: bool, dist: float) -> None:
        """Callback appelé par ClickTarget lors d'un clic."""
        if not self.waiting_for_click:
            return
        self.waiting_for_click = False

        if not hit:
            # Miss : on redemande sans compter l'essai
            self.status_label.setText("✗ Cible manquée — réessayez !")
            self.status_label.setStyleSheet("color: #e74c3c;")
            QTimer.singleShot(800, self._ask_for_space)
            return

        delta_ms = (click_time - self.signal_time) * 1000.0

        # Estimate Fitts pointing time for this trial
        # T_p = a + b * log2(D / W + 1)   (D = distance to centre, W = target width)
        # We use Settings.a_coefficient (in seconds) converted to ms
        a_ms = Settings.a_coefficient * 1000.0
        b_ms = Settings.b_coefficient * 1000.0
        t_fitts_ms = a_ms + b_ms * math.log2(max(dist, 1) / TARGET_W + 1)

        self.raw_deltas.append(delta_ms)
        self.fitts_times.append(t_fitts_ms)
        self.trials_done += 1

        self.progress_bar.setValue(self.trials_done)
        self.progress_label.setText(f"Essai : {self.trials_done} / {NUM_TRIALS}")
        self.status_label.setText(f"✓  Δt = {delta_ms:.0f} ms")
        self.status_label.setStyleSheet("color: #2ecc71;")

        if self.trials_done >= NUM_TRIALS:
            QTimer.singleShot(600, self._finish_experiment)
        else:
            QTimer.singleShot(600, self._ask_for_space)

    # Results

    def _finish_experiment(self) -> None:
        self.canvas.set_inactive()
        self.waiting_for_space = False
        self.waiting_for_click = False

        mean_raw = statistics.mean(self.raw_deltas)
        std_raw = statistics.stdev(self.raw_deltas) if len(self.raw_deltas) > 1 else 0.0
        mean_fitts = statistics.mean(self.fitts_times)
        h_empirique = max(0.0, mean_raw - mean_fitts)

        self._computed_h_ms = h_empirique

        lines = [
            f"<b>Nombre d'essais :</b> {NUM_TRIALS}",
            f"<b>Δt moyen brut (H + T_pointage) :</b> {mean_raw:.1f} ms",
            f"<b>Écart-type brut :</b> {std_raw:.1f} ms",
            f"<b>T_pointage Fitts moyen soustrait :</b> {mean_fitts:.1f} ms",
            "",
            f"<b>➜ H empirique :</b> {h_empirique:.1f} ms",
            f"<b>Valeur GOMS de référence :</b> ~400 ms",
        ]
        self.results_label.setText("<br>".join(lines))
        self.results_box.setVisible(True)

        self.status_label.setText("Expérience terminée ✔")
        self.status_label.setStyleSheet("color: #2ecc71;")
        self.instructions_label.setText(
            "Vous pouvez appliquer la valeur H mesurée aux paramètres de l'application, ou recommencer."
        )
        self.apply_btn.setVisible(True)
        self.reset_btn.setVisible(True)

    def _apply_h_to_settings(self) -> None:
        if hasattr(self, "_computed_h_ms"):
            Settings.H = self._computed_h_ms
            self.apply_btn.setText(f"✔  H = {self._computed_h_ms:.0f} ms appliqué")
            self.apply_btn.setEnabled(False)

    def _reset(self) -> None:
        self._delay_timer.stop()
        self.waiting_for_space = False
        self.waiting_for_click = False
        self.trials_done = 0
        self.raw_deltas = []
        self.fitts_times = []

        self.canvas.set_inactive()
        self.progress_bar.setValue(0)
        self.progress_label.setText(f"Essai : 0 / {NUM_TRIALS}")
        self.status_label.setText("—")
        self.status_label.setStyleSheet("color: #f39c12;")
        self.results_box.setVisible(False)
        self.apply_btn.setVisible(False)
        self.apply_btn.setEnabled(True)
        self.apply_btn.setText("✔ Appliquer H aux paramètres")
        self.reset_btn.setVisible(False)
        self.start_btn.setVisible(True)
        self.instructions_label.setText(
            "Cliquez sur <b>Démarrer</b> pour commencer.<br>"
            "À chaque essai : posez les deux mains sur le clavier, puis appuyez "
            "sur <b>Espace</b>.<br>"
            "Dès qu'une cible verte apparaît, saisissez la souris et cliquez "
            "dessus <b>aussi vite que possible</b>."
        )