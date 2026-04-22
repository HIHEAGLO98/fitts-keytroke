from __future__ import annotations
import time
import random
import statistics
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar, QGroupBox, QLineEdit,
    QSizePolicy, QFrame
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QKeyEvent, QMouseEvent

from constants import Settings

# Experiment configuration
NUM_ROUNDS: int = 3
NUM_FIELDS: int = 4
MIN_CHARS: int = 4
H_MIN_MS: float = 80.0
H_MAX_MS: float = 3000.0
COGNITIVE_OFFSET_MS: int = 150  # Estimated cognitive reaction time (ms) to subtract


FIELD_WORDS = [
    ["Marie",   "Lucas",  "Paris",    "marie@utbm.fr"],
    ["Sophie",  "Dupont", "Lyon",     "sophie@utbm.fr"],
    ["Paul",    "Martin", "Nice",     "paul@utbm.fr"],
    ["Claire",  "Petit",  "Bordeaux", "claire@utbm.fr"],
    ["Antoine", "Simon",  "Rennes",   "antoine@utbm.fr"],
    ["Julie",   "Morin",  "Nantes",   "julie@utbm.fr"],
]
FIELD_LABELS = ["Prénom", "Nom", "Ville", "Email"]


class TrackedLineEdit(QLineEdit):
    def __init__(self, field_index: int, experiment, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.field_index = field_index
        self.experiment = experiment
        self.last_keypress_time: float = 0.0

    def keyPressEvent(self, event: QKeyEvent) -> None:
        self.last_keypress_time = time.perf_counter()
        super().keyPressEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        click_time = time.perf_counter()
        self.experiment._on_field_clicked(self.field_index, click_time)
        super().mousePressEvent(event)


class H2Experiment(QWidget):
    def __init__(self, main_window: object) -> None:
        super().__init__()
        self.main_window = main_window
        self.current_round: int = 0
        self.current_field: int = 0
        self.h_measures: list[float] = []
        self.rejected: int = 0
        self.active: bool = False
        self._init_ui()

    def _init_ui(self) -> None:
        root = QVBoxLayout()
        root.setSpacing(14)
        root.setContentsMargins(40, 24, 40, 24)

        title = QLabel("Expérience H - Temps de transfert clavier → souris")
        title.setObjectName("TitleLabel")
        title.setAlignment(Qt.AlignCenter)
        root.addWidget(title)

        self.instructions_label = QLabel(
            "Remplissez le formulaire ci-dessous.<br>"
            "Tapez le mot suggéré dans chaque champ, puis <b>cliquez à la souris</b> "
            "sur le champ suivant pour passer au suivant.<br>"
            "<b>N'utilisez pas Tab</b> - le clic souris est obligatoire."
        )
        self.instructions_label.setWordWrap(True)
        self.instructions_label.setAlignment(Qt.AlignCenter)
        root.addWidget(self.instructions_label)

        self.status_label = QLabel("—")
        self.status_label.setAlignment(Qt.AlignCenter)
        f = QFont()
        f.setPointSize(13)
        f.setBold(True)
        self.status_label.setFont(f)
        self.status_label.setStyleSheet("color: #f39c12;")
        root.addWidget(self.status_label)

        # Form frame
        form_frame = QFrame()
        form_frame.setStyleSheet(
            "QFrame { background: #1e2733; border: 1.5px solid #444; border-radius: 14px; }"
        )
        form_layout = QVBoxLayout(form_frame)
        form_layout.setSpacing(18)
        form_layout.setContentsMargins(30, 24, 30, 24)

        self.field_rows: list[dict] = []

        for i, lbl_text in enumerate(FIELD_LABELS):
            row_layout = QHBoxLayout()

            lbl = QLabel(f"{lbl_text} :")
            lbl.setFixedWidth(80)
            lbl.setStyleSheet("color: #7fd1b9; font-weight: 600; font-size: 14px; background: transparent; border: none;")
            row_layout.addWidget(lbl)

            hint = QLabel("")
            hint.setFixedWidth(150)
            hint.setStyleSheet("color: #aaaaaa; font-style: italic; font-size: 13px; background: transparent; border: none;")
            row_layout.addWidget(hint)

            edit = TrackedLineEdit(i, self)
            edit.setReadOnly(True)
            edit.setPlaceholderText("…")
            edit.setMinimumHeight(38)
            row_layout.addWidget(edit, stretch=1)

            indicator = QLabel("●")
            indicator.setFixedWidth(28)
            indicator.setAlignment(Qt.AlignCenter)
            indicator.setStyleSheet("color: #444444; font-size: 18px; background: transparent; border: none;")
            row_layout.addWidget(indicator)

            form_layout.addLayout(row_layout)
            self.field_rows.append({"label": lbl, "hint": hint, "edit": edit, "indicator": indicator})

        root.addWidget(form_frame)

        self.next_form_btn = QPushButton("Formulaire suivant ➔")
        self.next_form_btn.setMinimumHeight(42)
        self.next_form_btn.setCursor(Qt.PointingHandCursor)
        self.next_form_btn.setStyleSheet(
            "QPushButton { background-color: #27ae60; color: white; border-radius: 8px; font-weight: bold; font-size: 15px; padding: 0 20px; }"
            "QPushButton:hover { background-color: #2ecc71; }"
        )
        self.next_form_btn.setVisible(False)  # Masqué par défaut
        self.next_form_btn.clicked.connect(self._on_next_form_clicked)

        # Conteneur pour centrer le bouton
        btn_container = QHBoxLayout()
        btn_container.addStretch()
        btn_container.addWidget(self.next_form_btn)
        btn_container.addStretch()
        root.addLayout(btn_container)

        self.log_label = QLabel("")
        self.log_label.setAlignment(Qt.AlignCenter)
        self.log_label.setStyleSheet("color: #888888; font-size: 13px;")
        root.addWidget(self.log_label)

        prog_layout = QHBoxLayout()
        total = NUM_ROUNDS * NUM_FIELDS
        self.progress_label = QLabel(f"Mesures : 0 / {total}")
        prog_layout.addWidget(self.progress_label)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(0)
        self.progress_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        prog_layout.addWidget(self.progress_bar)
        root.addLayout(prog_layout)

        self.results_box = QGroupBox("Résultats")
        res_layout = QVBoxLayout()
        self.results_label = QLabel("")
        self.results_label.setWordWrap(True)
        self.results_label.setAlignment(Qt.AlignCenter)
        res_layout.addWidget(self.results_label)
        self.results_box.setLayout(res_layout)
        self.results_box.setVisible(False)
        root.addWidget(self.results_box)

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
        self.current_round = 0
        self.current_field = 0
        self.h_measures = []
        self.rejected = 0
        self.active = True
        self.start_btn.setVisible(False)
        self.apply_btn.setVisible(False)
        self.reset_btn.setVisible(False)
        self.results_box.setVisible(False)
        self.progress_bar.setValue(0)
        self.log_label.setText("")
        self._load_round()
        self.next_form_btn.setVisible(False)

    def _load_round(self) -> None:
        words = FIELD_WORDS[self.current_round % len(FIELD_WORDS)]
        for i, row in enumerate(self.field_rows):
            row["hint"].setText(f"→ {words[i]}")
            row["edit"].clear()
            row["edit"].setReadOnly(True)
            #row["edit"].setStyleSheet("")
            row["edit"].setStyleSheet(
                "QLineEdit { border: 1px solid #444; border-radius: 10px; "
                "background: #1e2733; color: #666666; padding: 4px 8px; }"
            )
            row["indicator"].setText("●")
            row["indicator"].setStyleSheet("color: #444444; font-size: 18px; background: transparent; border: none;")
        self._activate_field(0)
        self.status_label.setText(
            f"Formulaire {self.current_round + 1} / {NUM_ROUNDS}  —  "
            "tapez le mot, puis cliquez sur le champ suivant"
        )
        self.status_label.setStyleSheet("color: #f39c12;")

    def _activate_field(self, index: int) -> None:
        self.current_field = index
        row = self.field_rows[index]
        row["edit"].setReadOnly(False)
        row["edit"].setStyleSheet(
            "QLineEdit { border: 2px solid #7fd1b9; border-radius: 10px; "
            "background: #1e2d3d; color: #f3f3f3; padding: 4px 8px; }"
        )
        row["indicator"].setText("▶")
        row["indicator"].setStyleSheet("color: #f39c12; font-size: 18px; background: transparent; border: none;")
        row["edit"].setFocus()

        # Afficher le bouton uniquement sur le dernier champ
        if index == NUM_FIELDS - 1:
            self.next_form_btn.setVisible(True)
        else:
            self.next_form_btn.setVisible(False)

    def _mark_field_done(self, index: int) -> None:
        row = self.field_rows[index]
        row["edit"].setReadOnly(True)
        row["edit"].setStyleSheet(
            "QLineEdit { border: 1.5px solid #2ecc71; border-radius: 10px; "
            "background: #1a2a1a; color: #aaaaaa; padding: 4px 8px; }"
        )
        row["indicator"].setText("✓")
        row["indicator"].setStyleSheet("color: #2ecc71; font-size: 16px; background: transparent; border: none;")

    # Core measurement

    def _on_field_clicked(self, clicked_index: int, click_time: float) -> None:
        if not self.active:
            return
        source_index = self.current_field
        # Only accept click on the immediately next field
        if clicked_index != source_index + 1:
            return

        expected_word = FIELD_WORDS[self.current_round % len(FIELD_WORDS)][source_index]
        source_edit = self.field_rows[source_index]["edit"]
        if source_edit.text() != expected_word:
            self._flash_status(
                f"✗ Saisie incorrecte. Veuillez taper exactement « {expected_word} »",
                "#e74c3c"
            )
            return
        # if len(source_edit.text()) < MIN_CHARS:
        #     self._flash_status(
        #         f"✗ Tapez au moins {MIN_CHARS} caractères dans "
        #         f"« {FIELD_LABELS[source_index]} » avant de cliquer",
        #         "#e74c3c"
        #     )
        #     return
        last_kp = source_edit.last_keypress_time
        if last_kp <= 0:
            return
        h_ms = (click_time - last_kp) * 1000.0
        if h_ms < H_MIN_MS or h_ms > H_MAX_MS:
            self.rejected += 1
            self._flash_status(f"⚠ Transition hors plage ({h_ms:.0f} ms) — ignorée", "#e67e22")
            self._advance_to_field(clicked_index)
            return
        # Valid measure
        self.h_measures.append(h_ms)
        self._update_progress()
        self._flash_status(f"✓  H = {h_ms:.0f} ms enregistré", "#2ecc71")
        self._update_log()
        self._advance_to_field(clicked_index)

    def _on_next_form_clicked(self) -> None:
        if not self.active:
            return

        click_time = time.perf_counter()
        source_index = NUM_FIELDS - 1
        source_edit = self.field_rows[source_index]["edit"]
        expected_word = FIELD_WORDS[self.current_round % len(FIELD_WORDS)][source_index]

        # Vérification de la saisie
        if source_edit.text() != expected_word:
            self._flash_status(
                f"✗ Saisie incorrecte. Veuillez taper exactement « {expected_word} »",
                "#e74c3c"
            )
            return
        # if len(source_edit.text()) < MIN_CHARS:
        #     self._flash_status(
        #         f"✗ Tapez au moins {MIN_CHARS} caractères dans "
        #         f"« {FIELD_LABELS[source_index]} » avant de cliquer",
        #         "#e74c3c"
        #     )
        #     return

        last_kp = source_edit.last_keypress_time
        if last_kp <= 0:
            return

        # Calcul du temps H
        h_ms = (click_time - last_kp) * 1000.0

        if h_ms < H_MIN_MS or h_ms > H_MAX_MS:
            self.rejected += 1
            self._flash_status(f"⚠ Transition hors plage ({h_ms:.0f} ms) - ignorée", "#e67e22")
        else:
            # Mesure valide
            self.h_measures.append(h_ms)
            self._update_progress()
            self._flash_status(f"✓  H = {h_ms:.0f} ms enregistré", "#2ecc71")
            self._update_log()

        # Masquer le bouton et passer à la suite
        self.next_form_btn.setVisible(False)
        self._complete_round()

    def _advance_to_field(self, new_index: int) -> None:
        self._mark_field_done(new_index - 1)
        if new_index < NUM_FIELDS:
            self._activate_field(new_index)
        else:
            self._complete_round()

    def _complete_round(self) -> None:
        self._mark_field_done(NUM_FIELDS - 1)
        self.current_round += 1
        if self.current_round >= NUM_ROUNDS:
            QTimer.singleShot(400, self._finish_experiment)
        else:
            QTimer.singleShot(600, self._load_round)

    def _update_progress(self) -> None:
        total = NUM_ROUNDS * NUM_FIELDS
        n = len(self.h_measures)
        self.progress_bar.setValue(min(n, total))
        self.progress_label.setText(f"Mesures : {n} / {total}")

    def _update_log(self) -> None:
        recent = self.h_measures[-5:]
        parts = [f"{v:.0f} ms" for v in recent]
        self.log_label.setText("Dernières mesures : " + "  |  ".join(parts))

    def _flash_status(self, text: str, color: str) -> None:
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"color: {color};")

    # Results

    def _finish_experiment(self) -> None:
        self.active = False
        if len(self.h_measures) < 3:
            self.status_label.setText("Pas assez de mesures valides - recommencez.")
            self.status_label.setStyleSheet("color: #e74c3c;")
            self.reset_btn.setVisible(True)
            return
        mean_h = statistics.mean(self.h_measures)
        std_h = statistics.stdev(self.h_measures) if len(self.h_measures) > 1 else 0.0
        median_h = statistics.median(self.h_measures)
        mean_total = max(0.0, mean_h - COGNITIVE_OFFSET_MS)
        self._computed_h_ms = mean_h
        lines = [
            f"<b>Mesures valides :</b> {len(self.h_measures)}"
            f"  <span style='color:#888'>(rejetées : {self.rejected})</span>",
            f"<b>H moyen :</b> {mean_h:.1f} ms",
            f"<b>H médian :</b> {median_h:.1f} ms",
            f"<b>Écart-type :</b> {std_h:.1f} ms",
            f"<b>Offset cognitif soustrait :</b> {COGNITIVE_OFFSET_MS:.0f} ms",
            "",
            f"<b>➜ H empirique retenu :</b> {mean_total:.1f} ms",
            f"<b>Valeur GOMS de référence :</b> ~400 ms",
        ]
        self.results_label.setText("<br>".join(lines))
        self.results_box.setVisible(True)
        self.status_label.setText("Expérience terminée ✔")
        self.status_label.setStyleSheet("color: #2ecc71;")
        self.instructions_label.setText(
            "Vous pouvez appliquer la valeur H mesurée aux paramètres, ou recommencer."
        )
        self.apply_btn.setVisible(True)
        self.reset_btn.setVisible(True)

    def _apply_h_to_settings(self) -> None:
        if hasattr(self, "_computed_h_ms"):
            Settings.H = self._computed_h_ms
            self.apply_btn.setText(f"✔  H = {self._computed_h_ms:.0f} ms appliqué")
            self.apply_btn.setEnabled(False)

    def _reset(self) -> None:
        self.active = False
        self.current_round = 0
        self.current_field = 0
        self.h_measures = []
        self.rejected = 0
        for row in self.field_rows:
            row["hint"].setText("")
            row["edit"].clear()
            row["edit"].setReadOnly(True)
            row["edit"].setStyleSheet("")
            row["indicator"].setText("●")
            row["edit"].setStyleSheet(
                "QLineEdit { border: 1px solid #444; border-radius: 10px; "
                "background: #1e2733; color: #666666; padding: 4px 8px; }"
            )
        total = NUM_ROUNDS * NUM_FIELDS
        self.progress_bar.setValue(0)
        self.progress_label.setText(f"Mesures : 0 / {total}")
        self.log_label.setText("")
        self.status_label.setText("—")
        self.status_label.setStyleSheet("color: #f39c12;")
        self.results_box.setVisible(False)
        self.apply_btn.setVisible(False)
        self.apply_btn.setEnabled(True)
        self.apply_btn.setText("✔ Appliquer H aux paramètres")
        self.reset_btn.setVisible(False)
        self.start_btn.setVisible(True)
        self.instructions_label.setText(
            "Remplissez le formulaire ci-dessous.<br>"
            "Tapez le mot suggéré dans chaque champ, puis <b>cliquez à la souris</b> "
            "sur le champ suivant pour passer au suivant.<br>"
            "<b>N'utilisez pas Tab</b> - le clic souris est obligatoire."
        )
        self.next_form_btn.setVisible(False)