from __future__ import annotations
import time
import random
import statistics
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar, QGroupBox, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QKeyEvent, QFont
from constants import Settings


NUM_TRIALS: int = 20          # Total number of key-press trials
COGNITIVE_OFFSET_MS: float = Settings.M   # Estimated cognitive reaction time (ms) to subtract
# Letters chosen to be on the home row or adjacent – easy to locate without hunting
LETTER_POOL: list[str] = list("FJDKSLAEIRUMVHZPQBWXGTO")


class KExperiment(QWidget):
    """
    Experiment screen to empirically estimate the K (keystroke) operator time.

    Protocol
    --------
    1. A random letter is displayed in large font at the centre of the screen.
    2. The participant presses the matching key as quickly as possible.
    3. We record Δt = t_keypress − t_display for each trial.
    4. After NUM_TRIALS, we compute mean and std-dev, subtract COGNITIVE_OFFSET_MS
       to isolate the pure motor component, and optionally update Settings.K.
    """

    def __init__(self, main_window: object) -> None:
        super().__init__()
        self.main_window = main_window

        # State
        self.trials_done: int = 0
        self.reaction_times: list[float] = []   # raw t in ms for each trial
        self.current_letter: str = ""
        self.display_time: float = 0.0          # time.time() when letter appeared
        self.waiting_for_keypress: bool = False
        self.experiment_started: bool = False

        # Small delay timer between trials (avoids anticipation)
        self._inter_trial_timer = QTimer(self)
        self._inter_trial_timer.setSingleShot(True)
        self._inter_trial_timer.timeout.connect(self._show_next_letter)

        self._init_ui()

    # UI construction

    def _init_ui(self) -> None:
        root = QVBoxLayout()
        root.setSpacing(16)
        root.setContentsMargins(32, 24, 32, 24)

        # Title
        title = QLabel("Expérience K — Temps de frappe clavier")
        title.setObjectName("TitleLabel")
        title.setAlignment(Qt.AlignCenter)
        root.addWidget(title)

        # Instructions
        self.instructions_label = QLabel(
            "Appuyez sur <b>Démarrer</b> pour lancer l'expérience.<br>"
            "À chaque essai, une lettre apparaîtra en grand au centre.<br>"
            "Appuyez <b>aussi vite que possible</b> sur cette touche."
        )
        self.instructions_label.setWordWrap(True)
        self.instructions_label.setAlignment(Qt.AlignCenter)
        root.addWidget(self.instructions_label)

        # Central stimulus
        stimulus_box = QGroupBox()
        stimulus_layout = QVBoxLayout()
        stimulus_layout.setAlignment(Qt.AlignCenter)

        # Countdown label – prominent, shown above the letter
        self.countdown_label = QLabel("")
        self.countdown_label.setAlignment(Qt.AlignCenter)
        countdown_font = QFont()
        countdown_font.setPointSize(22)
        countdown_font.setBold(True)
        self.countdown_label.setFont(countdown_font)
        self.countdown_label.setStyleSheet("color: #f39c12;")
        self.countdown_label.setMinimumHeight(36)
        stimulus_layout.addWidget(self.countdown_label)

        self.stimulus_label = QLabel("—")
        self.stimulus_label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(120)
        font.setBold(True)
        self.stimulus_label.setFont(font)
        self.stimulus_label.setMinimumHeight(200)
        stimulus_layout.addWidget(self.stimulus_label)

        self.feedback_label = QLabel("")
        self.feedback_label.setAlignment(Qt.AlignCenter)
        self.feedback_label.setStyleSheet("font-size: 16px; color: #aaaaaa;")
        stimulus_layout.addWidget(self.feedback_label)

        stimulus_box.setLayout(stimulus_layout)
        root.addWidget(stimulus_box, stretch=1)

        #  Progress
        progress_layout = QHBoxLayout()
        self.progress_label = QLabel(f"Essai : 0 / {NUM_TRIALS}")
        progress_layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, NUM_TRIALS)
        self.progress_bar.setValue(0)
        self.progress_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        progress_layout.addWidget(self.progress_bar)
        root.addLayout(progress_layout)

        #  Results box (hidden until experiment ends)
        self.results_box = QGroupBox("Résultats")
        results_layout = QVBoxLayout()
        self.results_label = QLabel("")
        self.results_label.setWordWrap(True)
        self.results_label.setAlignment(Qt.AlignCenter)
        results_layout.addWidget(self.results_label)
        self.results_box.setLayout(results_layout)
        self.results_box.setVisible(False)
        root.addWidget(self.results_box)

        # Buttons
        btn_layout = QHBoxLayout()

        self.start_btn = QPushButton("▶ Démarrer")
        #self.start_btn.setMinimumHeight(40)
        self.start_btn.clicked.connect(self._start_experiment)
        btn_layout.addWidget(self.start_btn)


        self.apply_btn = QPushButton("✔ Appliquer K aux paramètres")
        #self.apply_btn.setMinimumHeight(40)
        self.apply_btn.setVisible(False)
        self.apply_btn.clicked.connect(self._apply_k_to_settings)
        btn_layout.addWidget(self.apply_btn)

        self.reset_btn = QPushButton("↺ Recommencer")
        #self.reset_btn.setMinimumHeight(40)
        self.reset_btn.setVisible(False)
        self.reset_btn.clicked.connect(self._reset)
        btn_layout.addWidget(self.reset_btn)

        back_btn = QPushButton("← Menu Keystroke")
        #back_btn.setMinimumHeight(40)
        back_btn.clicked.connect(lambda: self.main_window.switch_screen(4))
        btn_layout.addWidget(back_btn)

        root.addLayout(btn_layout)
        self.setLayout(root)

    #  Experiment flow

    def _start_experiment(self) -> None:
        """Initialise l'état et lance le premier essai."""
        self.trials_done = 0
        self.reaction_times = []
        self.experiment_started = True

        self.start_btn.setVisible(False)
        self.apply_btn.setVisible(False)
        self.reset_btn.setVisible(False)
        self.results_box.setVisible(False)
        self.progress_bar.setValue(0)
        self.progress_label.setText(f"Essai : 0 / {NUM_TRIALS}")
        self.instructions_label.setText(
            "Regardez la lettre et appuyez dessus immédiatement."
        )

        # Small random delay before first letter (300–800 ms) to avoid anticipation
        delay_ms = random.randint(300, 800)
        self.stimulus_label.setText("…")
        self.feedback_label.setText("")
        self._inter_trial_timer.start(delay_ms)

    def _show_next_letter(self) -> None:
        """Affiche la prochaine lettre et démarre le chronomètre."""
        if self.trials_done >= NUM_TRIALS:
            self._finish_experiment()
            return

        remaining = NUM_TRIALS - (self.trials_done + 1)
        self.countdown_label.setText(f"{remaining} lettre{'s' if remaining > 1 else ''} restante{'s' if remaining > 1 else ''}")
        self.current_letter = random.choice(LETTER_POOL)
        self.stimulus_label.setText(self.current_letter)
        self.feedback_label.setText("")
        self.display_time = time.perf_counter()
        self.waiting_for_keypress = True
        self.setFocus()

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        """Capture la touche pressée et mesure le Δt."""
        if not self.waiting_for_keypress:
            super().keyPressEvent(event)
            return

        press_time = time.perf_counter()
        pressed_text = event.text().upper()

        if pressed_text == self.current_letter:
            # Correct key
            delta_ms = (press_time - self.display_time) * 1000.0
            self.reaction_times.append(delta_ms)
            self.trials_done += 1
            self.waiting_for_keypress = False

            self.progress_bar.setValue(self.trials_done)
            self.progress_label.setText(f"Essai : {self.trials_done} / {NUM_TRIALS}")
            self.feedback_label.setText(f"✓  {delta_ms:.0f} ms")
            self.stimulus_label.setText("✓")

            # Inter-trial pause (variable to prevent anticipation)
            delay_ms = random.randint(400, 900)
            self._inter_trial_timer.start(delay_ms)
        else:
            # Wrong key – visual warning, do NOT record this trial
            self.feedback_label.setText("✗  Mauvaise touche !")
            self.stimulus_label.setStyleSheet("color: #e74c3c;")
            QTimer.singleShot(600, self._clear_error_style)

    def _clear_error_style(self) -> None:
        self.stimulus_label.setStyleSheet("")

    # Results

    def _finish_experiment(self) -> None:
        """Calcule les statistiques et affiche les résultats."""
        self.waiting_for_keypress = False
        self.stimulus_label.setText("✔")
        self.feedback_label.setText("")

        mean_raw = statistics.mean(self.reaction_times)
        std_raw = statistics.stdev(self.reaction_times) if len(self.reaction_times) > 1 else 0.0
        k_motor = max(0.0, mean_raw - COGNITIVE_OFFSET_MS)

        # Store computed K on the instance for later use
        self._computed_k_ms = k_motor
        self._mean_raw_ms = mean_raw

        lines = [
            f"<b>Nombre d'essais :</b> {NUM_TRIALS}",
            f"<b>Temps moyen brut (Δt) :</b> {mean_raw:.1f} ms",
            f"<b>Écart-type :</b> {std_raw:.1f} ms",
            f"<b>Offset cognitif soustrait :</b> {COGNITIVE_OFFSET_MS:.0f} ms",
            "",
            f"<b>➜ K empirique (moteur) :</b> {k_motor:.1f} ms",
            f"<b>Valeur GOMS de référence :</b> ~{Settings.K} ms",
        ]
        self.results_label.setText("<br>".join(lines))
        self.results_box.setVisible(True)

        self.instructions_label.setText(
            "Expérience terminée ! Vous pouvez appliquer la valeur K mesurée\n"
            "aux paramètres de l'application, ou recommencer."
        )
        self.apply_btn.setVisible(True)
        self.reset_btn.setVisible(True)

    def _apply_k_to_settings(self) -> None:
        """Met à jour Settings.K avec la valeur mesurée."""
        if hasattr(self, "_computed_k_ms"):
            Settings.K = self._computed_k_ms
            self.apply_btn.setText(f"✔  K = {self._computed_k_ms:.0f} ms appliqué")
            self.apply_btn.setEnabled(False)

    def _reset(self) -> None:
        """Remet l'écran à l'état initial."""
        self.waiting_for_keypress = False
        self._inter_trial_timer.stop()
        self.trials_done = 0
        self.reaction_times = []
        self.experiment_started = False

        self.stimulus_label.setText("—")
        self.stimulus_label.setStyleSheet("")
        self.countdown_label.setText("")
        self.feedback_label.setText("")
        self.progress_bar.setValue(0)
        self.progress_label.setText(f"Essai : 0 / {NUM_TRIALS}")
        self.results_box.setVisible(False)
        self.apply_btn.setVisible(False)
        self.apply_btn.setEnabled(True)
        self.apply_btn.setText("✔  Appliquer K aux paramètres")
        self.reset_btn.setVisible(False)
        self.start_btn.setVisible(True)
        self.instructions_label.setText(
            "Appuyez sur <b>Démarrer</b> pour lancer l'expérience.<br>"
            "À chaque essai, une lettre apparaîtra en grand au centre.<br>"
            "Appuyez <b>aussi vite que possible</b> sur cette touche."
        )