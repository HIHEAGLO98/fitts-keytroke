from __future__ import annotations
import time
import random
import statistics
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar, QGroupBox, QSizePolicy,
    QFrame, QListWidget, QListWidgetItem, QAbstractItemView,
    QStackedWidget, QApplication
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QKeyEvent, QColor

from constants import Settings

# Configuration
NUM_TRIALS: int = 5 # Trials per method (mouse / keyboard)

FAKE_FILES = [
    "rapport_annuel_2025.docx",
    "budget_Q3.xlsx",
    "presentation_client.pptx",
    "notes_reunion.txt",
    "photo_vacances.jpg",
    "contrat_fournisseur.pdf",
    "planning_sprint.xlsx",
    "readme.md",
    "facture_0042.pdf",
    "backup_config.zip",
]


# Simulated sub-widgets

class FakeMenuBar(QFrame):
    """
    Simulated menu bar with a single 'Fichier' menu that opens a dropdown.
    """
    def __init__(self, on_open_clicked, parent=None):
        super().__init__(parent)
        self.on_open_clicked = on_open_clicked
        self.setFixedHeight(36)
        self.setStyleSheet(
            "QFrame { background: #2a2a3a; border-bottom: 1px solid #555; }"
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(0)

        self.file_btn = QPushButton("Fichier")
        self.file_btn.setStyleSheet(
            "QPushButton { background: transparent; color: #f3f3f3; "
            "border: none; border-radius: 4px; padding: 4px 12px; font-size: 14px; "
            "font-weight: normal; margin: 0; }"
            "QPushButton:hover { background: #3a3a5a; }"
            "QPushButton:pressed { background: #4a4a6a; }"
        )
        self.file_btn.clicked.connect(self._toggle_dropdown)
        layout.addWidget(self.file_btn)
        layout.addStretch()

        # Dropdown (initially hidden, shown as overlay via parent)
        self._dropdown_visible = False
        self._dropdown = None   # created lazily on first use

    def _build_dropdown(self):
        """Build the dropdown widget parented to the main window."""
        parent = self.window()
        self._dropdown = QFrame(parent)
        self._dropdown.setWindowFlags(Qt.Popup)
        self._dropdown.setStyleSheet(
            "QFrame { background: #2a2a3a; border: 1px solid #666; border-radius: 6px; }"
        )
        dlay = QVBoxLayout(self._dropdown)
        dlay.setContentsMargins(2, 4, 2, 4)
        dlay.setSpacing(0)

        open_btn = QPushButton("  Ouvrir…       Ctrl+O")
        open_btn.setStyleSheet(
            "QPushButton { background: transparent; color: #f3f3f3; "
            "border: none; border-radius: 4px; padding: 6px 16px; "
            "font-size: 13px; font-weight: normal; text-align: left; margin: 0; }"
            "QPushButton:hover { background: #3a6aaa; }"
        )
        open_btn.clicked.connect(self._open_clicked)
        dlay.addWidget(open_btn)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #555;")
        dlay.addWidget(sep)

        for txt in ["Enregistrer", "Fermer", "Quitter"]:
            btn = QPushButton(f"  {txt}")
            btn.setStyleSheet(
                "QPushButton { background: transparent; color: #888; "
                "border: none; border-radius: 4px; padding: 6px 16px; "
                "font-size: 13px; font-weight: normal; text-align: left; margin: 0; }"
            )
            btn.setEnabled(False)
            dlay.addWidget(btn)

        self._dropdown.adjustSize()

    def _toggle_dropdown(self):
        if self._dropdown is None:
            self._build_dropdown()
        # Position below the Fichier button
        pos = self.file_btn.mapToGlobal(self.file_btn.rect().bottomLeft())
        self._dropdown.move(pos)
        self._dropdown.show()
        self._dropdown.raise_()

    def _open_clicked(self):
        if self._dropdown:
            self._dropdown.hide()
        self.on_open_clicked()

    def reset(self):
        if self._dropdown:
            self._dropdown.hide()


class FakeFileDialog(QFrame):
    """
    Simulated file-open dialog.
    Shows a list of files; one is highlighted as 'target'.
    Calls on_confirmed() when the user clicks OK or presses Enter.
    """

    def __init__(self, on_confirmed, parent=None):
        super().__init__(parent)
        self.on_confirmed = on_confirmed
        self._target_index: int = -1  # set during populate()
        self.setStyleSheet(
            "QFrame { background: #23293a; border: 2px solid #666; border-radius: 10px; }"
        )
        self.setFixedSize(420, 320)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(8)

        title_bar = QLabel("📂  Ouvrir un fichier")
        title_bar.setStyleSheet("color: #f3f3f3; font-size: 14px; font-weight: bold; background: transparent; border: none;")
        root.addWidget(title_bar)

        # Warning label shown when wrong file is selected
        self.warn_label = QLabel("⚠  Sélectionnez le fichier ★ en surbrillance !")
        self.warn_label.setStyleSheet(
            "color: #e74c3c; font-size: 12px; font-weight: bold; "
            "background: transparent; border: none;"
        )
        self.warn_label.setAlignment(Qt.AlignCenter)
        self.warn_label.setVisible(False)
        root.addWidget(self.warn_label)

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(
            "QListWidget { background: #1a1f2e; border: 1px solid #444; "
            "border-radius: 6px; color: #f3f3f3; font-size: 13px; }"
            "QListWidget::item:selected { background: #2a5aaa; }"
        )
        self.list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        root.addWidget(self.list_widget, stretch=1)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.ok_btn = QPushButton("OK")
        self.ok_btn.setFixedWidth(80)
        self.ok_btn.setStyleSheet(
            "QPushButton { background: #2a5aaa; color: #fff; border: none; "
            "border-radius: 6px; padding: 6px 0; font-size: 13px; font-weight: 600; margin: 0; }"
            "QPushButton:hover { background: #3a6acc; }"
        )
        self.ok_btn.clicked.connect(self._confirm)
        btn_row.addWidget(self.ok_btn)

        cancel_btn = QPushButton("Annuler")
        cancel_btn.setFixedWidth(80)
        cancel_btn.setStyleSheet(
            "QPushButton { background: #444; color: #aaa; border: none; "
            "border-radius: 6px; padding: 6px 0; font-size: 13px; margin: 0; }"
        )
        cancel_btn.setEnabled(False)
        btn_row.addWidget(cancel_btn)

        root.addLayout(btn_row)

    def populate(self, target_index: int) -> None:
        """Fill with fake files, highlight the target."""
        self._target_index = target_index
        self.warn_label.setVisible(False)
        self.list_widget.clear()
        for i, fname in enumerate(FAKE_FILES):
            item = QListWidgetItem(f"  {fname}")
            if i == target_index:
                item.setBackground(QColor("#1a4a1a"))
                item.setForeground(QColor("#7fd1b9"))
                item.setText(f"  ★  {fname}")
            self.list_widget.addItem(item)
        self.list_widget.setCurrentRow(target_index)

    def _confirm(self):
        selected = self.list_widget.currentRow()
        if selected != self._target_index:
            self.warn_label.setVisible(True)
            # Flash the OK button red briefly
            self.ok_btn.setStyleSheet(
                "QPushButton { background: #c0392b; color: #fff; border: none; "
                "border-radius: 6px; padding: 6px 0; font-size: 13px; font-weight: 600; margin: 0; }"
            )
            QTimer.singleShot(600, self._reset_ok_style)
            return
        self.warn_label.setVisible(False)
        self.hide()
        self.on_confirmed()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self._confirm()
        else:
            super().keyPressEvent(event)

    def _reset_ok_style(self):
        self.ok_btn.setStyleSheet(
            "QPushButton { background: #2a5aaa; color: #fff; border: none; "
            "border-radius: 6px; padding: 6px 0; font-size: 13px; font-weight: 600; margin: 0; }"
            "QPushButton:hover { background: #3a6acc; }"
        )


# Main experiment widget

class CExperiment(QWidget):
    """
    Expérience C — Évaluation de la commande « Ouvrir un fichier ».

    Phase SOURIS : signal → clic Fichier → clic Ouvrir → clic fichier cible → clic OK
    Phase CLAVIER : signal → Ctrl+O → Entrée (fichier pré-sélectionné)

    Δt mesuré = t_confirmation − t_signal dans les deux cas.
    """

    def __init__(self, main_window: object) -> None:
        super().__init__()
        self.main_window = main_window

        # State
        self.phase: str = "idle" # idle | intro | mouse | keyboard | results
        self.trial: int = 0
        self.signal_time: float = 0.0
        self.waiting_signal: bool = False
        self.mouse_times: list[float] = []
        self.keyboard_times: list[float] = []
        self.target_index: int = 0

        self._signal_timer = QTimer(self)
        self._signal_timer.setSingleShot(True)
        self._signal_timer.timeout.connect(self._fire_signal)

        self._init_ui()

    # UI

    def _init_ui(self) -> None:
        root = QVBoxLayout()
        root.setSpacing(10)
        root.setContentsMargins(0, 0, 0, 0)
        self.setLayout(root)

        # Simulated app frame
        app_frame = QFrame()
        #app_frame.setStyleSheet()
        app_layout = QVBoxLayout(app_frame)
        app_layout.setContentsMargins(0, 0, 0, 0)
        app_layout.setSpacing(0)

        # Fake menu bar (mouse method uses this)
        self.menu_bar = FakeMenuBar(on_open_clicked=self._on_menu_open_clicked)
        app_layout.addWidget(self.menu_bar)

        # Main content area (stacked: intro / signal / results)
        self.content_stack = QStackedWidget()
        app_layout.addWidget(self.content_stack, stretch=1)

        root.addWidget(app_frame, stretch=1)

        # Page 0 : Intro / instructions
        intro_page = QWidget()
        intro_layout = QVBoxLayout(intro_page)
        intro_layout.setAlignment(Qt.AlignCenter)
        intro_layout.setSpacing(20)

        title = QLabel("Expérience C - Ouverture de fichier\nSouris vs Clavier")
        title.setObjectName("TitleLabel")
        title.setAlignment(Qt.AlignCenter)
        intro_layout.addWidget(title)

        desc = QLabel(
            "<b>Phase 1 - Souris</b> : quand le signal apparaît, cliquez sur "
            "<i>Fichier → Ouvrir…</i>, puis sur le fichier en surbrillance, "
            "puis sur <b>OK</b>.<br><br>"
            "<b>Phase 2 - Clavier</b> : quand le signal apparaît, appuyez sur "
            "<b>Ctrl+O</b>, puis sur <b>Entrée</b>.<br><br>"
            f"Chaque phase comporte <b>{NUM_TRIALS} essais</b>."
        )
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("font-size: 14px; line-height: 1.6;")
        intro_layout.addWidget(desc)


        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(0)

        back_btn = QPushButton("← Menu Keystroke")
        back_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        back_btn.clicked.connect(lambda: self.main_window.switch_screen(4))
        bottom_row.addWidget(back_btn)

        self.start_btn = QPushButton("▶ Démarrer - Phase Souris")
        self.start_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.start_btn.clicked.connect(self._start_mouse_phase)
        bottom_row.addWidget(self.start_btn)

        intro_layout.addLayout(bottom_row)

        self.content_stack.addWidget(intro_page)   # index 0

        # Page 1 : Signal / trial area
        trial_page = QWidget()
        trial_layout = QVBoxLayout(trial_page)
        trial_layout.setAlignment(Qt.AlignCenter)
        trial_layout.setSpacing(16)

        self.phase_label = QLabel("")
        self.phase_label.setAlignment(Qt.AlignCenter)
        pf = QFont()
        pf.setPointSize(14)
        pf.setBold(True)
        self.phase_label.setFont(pf)
        self.phase_label.setStyleSheet("color: #7fd1b9;")
        trial_layout.addWidget(self.phase_label)

        self.countdown_label = QLabel("")
        self.countdown_label.setAlignment(Qt.AlignCenter)
        cf = QFont()
        cf.setPointSize(20)
        cf.setBold(True)
        self.countdown_label.setFont(cf)
        self.countdown_label.setStyleSheet("color: #f39c12;")
        trial_layout.addWidget(self.countdown_label)

        self.signal_widget = QLabel("")
        self.signal_widget.setAlignment(Qt.AlignCenter)
        sf = QFont()
        sf.setPointSize(42)
        sf.setBold(True)
        self.signal_widget.setFont(sf)
        self.signal_widget.setMinimumHeight(120)
        trial_layout.addWidget(self.signal_widget)

        self.hint_label = QLabel("")
        self.hint_label.setAlignment(Qt.AlignCenter)
        self.hint_label.setWordWrap(True)
        self.hint_label.setStyleSheet("color: #aaaaaa; font-size: 14px;")
        trial_layout.addWidget(self.hint_label)

        # Progress bar
        prog_row = QHBoxLayout()
        self.trial_progress_label = QLabel(f"Essai : 0 / {NUM_TRIALS}")
        prog_row.addWidget(self.trial_progress_label)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, NUM_TRIALS)
        self.progress_bar.setValue(0)
        self.progress_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        prog_row.addWidget(self.progress_bar)
        trial_layout.addLayout(prog_row)

        # Last delta
        self.last_delta_label = QLabel("")
        self.last_delta_label.setAlignment(Qt.AlignCenter)
        self.last_delta_label.setStyleSheet("color: #2ecc71; font-size: 14px;")
        trial_layout.addWidget(self.last_delta_label)

        self.content_stack.addWidget(trial_page)   # index 1

        # Page 2 : Results
        results_page = QWidget()
        results_layout = QVBoxLayout(results_page)
        results_layout.setAlignment(Qt.AlignTop)
        results_layout.setSpacing(14)
        results_layout.setContentsMargins(30, 20, 30, 20)

        res_title = QLabel("Résultats - Souris vs Clavier")
        res_title.setObjectName("TitleLabel")
        res_title.setAlignment(Qt.AlignCenter)
        results_layout.addWidget(res_title)

        self.results_label = QLabel("")
        self.results_label.setWordWrap(True)
        self.results_label.setAlignment(Qt.AlignCenter)
        self.results_label.setStyleSheet("font-size: 14px; line-height: 1.8;")
        results_layout.addWidget(self.results_label)

        self.goms_label = QLabel("")
        self.goms_label.setWordWrap(True)
        self.goms_label.setAlignment(Qt.AlignCenter)
        self.goms_label.setStyleSheet(
            "font-size: 13px; color: #aaaaaa; background: #1e2733; "
            "border: 1px solid #444; border-radius: 8px; padding: 12px;"
        )
        results_layout.addWidget(self.goms_label)

        res_btn_row = QHBoxLayout()

        self.restart_btn = QPushButton("↺ Recommencer")
        self.restart_btn.clicked.connect(self._reset)
        res_btn_row.addWidget(self.restart_btn)

        back_btn2 = QPushButton("← Menu Keystroke")
        back_btn2.clicked.connect(lambda: self.main_window.switch_screen(4))
        res_btn_row.addWidget(back_btn2)

        results_layout.addLayout(res_btn_row)
        self.content_stack.addWidget(results_page)  # index 2

        # Floating fake dialog
        self.file_dialog = FakeFileDialog(
            on_confirmed=self._on_dialog_confirmed,
            parent=self
        )
        self.file_dialog.hide()

    # Positioning the dialog overlay

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._center_dialog()

    def _center_dialog(self) -> None:
        dw, dh = self.file_dialog.width(), self.file_dialog.height()
        x = (self.width() - dw) // 2
        y = (self.height() - dh) // 2
        self.file_dialog.move(x, y)

    # Phase management

    def _start_mouse_phase(self) -> None:
        self.phase = "mouse"
        self.trial = 0
        self.mouse_times = []
        self.menu_bar.setVisible(True)
        self.content_stack.setCurrentIndex(1)
        self.phase_label.setText("Phase 1 / 2 - SOURIS  🖱")
        self._next_trial()

    def _start_keyboard_phase(self) -> None:
        self.phase = "keyboard"
        self.trial = 0
        self.keyboard_times = []
        self.menu_bar.setVisible(False)
        self.content_stack.setCurrentIndex(1)
        self.phase_label.setText("Phase 2 / 2 - CLAVIER  ⌨")
        self._next_trial()

    def _next_trial(self) -> None:
        self.trial += 1
        self.progress_bar.setValue(self.trial - 1)
        self.trial_progress_label.setText(f"Essai : {self.trial - 1} / {NUM_TRIALS}")
        self.last_delta_label.setText("")
        self.file_dialog.hide()
        self.menu_bar.reset()

        # Pick a random target file
        self.target_index = random.randint(0, len(FAKE_FILES) - 1)

        # Show "get ready" state
        self.signal_widget.setText("…")
        self.signal_widget.setStyleSheet("color: #555555;")
        if self.phase == "mouse":
            self.hint_label.setText("Attendez le signal, puis : Fichier → Ouvrir → fichier ★ → OK")
        else:
            self.hint_label.setText("Attendez le signal, puis appuyez : Ctrl + O  →  Entrée")

        # Random delay 600–1200 ms before signal
        delay_ms = random.randint(600, 1200)
        self._signal_timer.start(delay_ms)
        self.waiting_signal = False
        self.setFocus()

    def _fire_signal(self) -> None:
        """Show the GO signal and start timing."""
        QApplication.beep()
        self.signal_time = time.perf_counter()
        self.waiting_signal = True
        self.signal_widget.setText("GO (COMMENCEZ) !")
        self.signal_widget.setStyleSheet("color: #2ecc71;")

        # Update countdown label
        remaining = NUM_TRIALS - self.trial + 1
        self.countdown_label.setText(
            f"{remaining} essai{'s' if remaining > 1 else ''} restant{'s' if remaining > 1 else ''}"
        )

        # For mouse phase: enable menu bar interaction
        if self.phase == "mouse":
            self.hint_label.setText("➜  Fichier  →  Ouvrir…  →  fichier ★  →  OK")

    # Mouse phase interaction

    def _on_menu_open_clicked(self) -> None:
        """Called when user clicks Fichier → Ouvrir… in the fake menu."""
        if self.phase != "mouse" or not self.waiting_signal:
            return
        self.signal_widget.setText("…")
        self.signal_widget.setStyleSheet("color: #aaaaaa;")
        self.hint_label.setText("➜ Cliquez sur le fichier ★ puis sur OK")
        self.file_dialog.populate(self.target_index)
        self._center_dialog()
        self.file_dialog.show()
        self.file_dialog.raise_()
        self.file_dialog.setFocus()

    # Keyboard phase interaction

    def keyPressEvent(self, event: QKeyEvent) -> None:
        # Ctrl+O before signal: warn user and ignore
        if (self.phase == "keyboard"
                and not self.waiting_signal
                and event.modifiers() == Qt.ControlModifier
                and event.key() == Qt.Key_O):
            self.hint_label.setText("⚠  Attendez le signal GO ! avant d'appuyer sur Ctrl+O")
            self.hint_label.setStyleSheet("color: #e74c3c; font-size: 14px;")
            QTimer.singleShot(1200, self._reset_hint_style)
            return
        # Ctrl+O triggers dialog in keyboard phase
        if (self.phase == "keyboard" and self.waiting_signal
                and event.modifiers() == Qt.ControlModifier
                and event.key() == Qt.Key_O):
            self.signal_widget.setText("…")
            self.signal_widget.setStyleSheet("color: #aaaaaa;")
            self.hint_label.setText("➜  Appuyez sur Entrée pour confirmer")
            self.file_dialog.populate(self.target_index)
            self._center_dialog()
            self.file_dialog.show()
            self.file_dialog.raise_()
            self.file_dialog.setFocus()
        else:
            super().keyPressEvent(event)

    def _reset_hint_style(self) -> None:
        """Restore hint label to its default grey style."""
        self.hint_label.setStyleSheet("color: #aaaaaa; font-size: 14px;")
    # Shared confirmation

    def _on_dialog_confirmed(self) -> None:
        """Called when the user clicks OK or presses Enter in the dialog."""
        if not self.waiting_signal:
            return
        self.waiting_signal = False
        delta_ms = (time.perf_counter() - self.signal_time) * 1000.0

        if self.phase == "mouse":
            self.mouse_times.append(delta_ms)
        else:
            self.keyboard_times.append(delta_ms)

        self.progress_bar.setValue(self.trial)
        self.trial_progress_label.setText(f"Essai : {self.trial} / {NUM_TRIALS}")
        self.last_delta_label.setText(f"✓  {delta_ms:.0f} ms")
        self.signal_widget.setText("✓")

        if self.trial >= NUM_TRIALS:
            if self.phase == "mouse":
                QTimer.singleShot(800, self._between_phases)
            else:
                QTimer.singleShot(800, self._show_results)
        else:
            QTimer.singleShot(700, self._next_trial)

    def _between_phases(self) -> None:
        """Show a transition message before the keyboard phase."""
        self.phase_label.setText("Phase 1 terminée ✔ - Phase 2 : CLAVIER")
        self.signal_widget.setText("")
        self.countdown_label.setText("")
        self.hint_label.setText(
            "Bien joué ! La phase Clavier va démarrer.\n"
            "Appuyez sur le bouton ci-dessous quand vous êtes prêt."
        )
        self.progress_bar.setValue(0)
        self.trial_progress_label.setText(f"Essai : 0 / {NUM_TRIALS}")
        self.last_delta_label.setText("")

        ready_btn = QPushButton("▶ Démarrer-Phase Clavier")
        ready_btn.clicked.connect(self._start_keyboard_phase)

        # Insert button temporarily in the trial page layout
        trial_page = self.content_stack.widget(1)
        lay = trial_page.layout()
        lay.addWidget(ready_btn, alignment=Qt.AlignCenter)
        self._ready_btn_ref = ready_btn   # keep ref to remove later

    # Results

    def _show_results(self) -> None:
        self.phase = "results"
        self.menu_bar.setVisible(False)
        self._cleanup_ready_btn()

        # Measured stats
        mean_mouse = statistics.mean(self.mouse_times)
        std_mouse = statistics.stdev(self.mouse_times) if len(self.mouse_times) > 1 else 0.0
        mean_kb = statistics.mean(self.keyboard_times)
        std_kb = statistics.stdev(self.keyboard_times) if len(self.keyboard_times) > 1 else 0.0

        # Theoretical GOMS times
        K = Settings.K
        H = Settings.H
        P = Settings.P
        M = Settings.M

        # Souris : M + H + 4P + 4K
        goms_mouse = M + H + 4 * P + 4 * K
        # Clavier : M + 2K
        goms_kb = M + 2 * K

        ecart_mouse = ((mean_mouse - goms_mouse) / goms_mouse) * 100
        ecart_kb = ((mean_kb - goms_kb) / goms_kb) * 100

        faster = "Clavier" if mean_kb < mean_mouse else "Souris"
        ratio = max(mean_mouse, mean_kb) / min(mean_mouse, mean_kb)

        # Display
        result_lines = [
            "<table width='100%' cellspacing='8'>",
            "<tr><th></th><th style='color:#7fd1b9'>Souris 🖱</th><th style='color:#f39c12'>Clavier ⌨</th></tr>",
            f"<tr><td><b>Temps moyen mesuré</b></td>"
            f"<td align='center'>{mean_mouse:.0f} ms</td>"
            f"<td align='center'>{mean_kb:.0f} ms</td></tr>",
            f"<tr><td><b>Écart-type</b></td>"
            f"<td align='center'>± {std_mouse:.0f} ms</td>"
            f"<td align='center'>± {std_kb:.0f} ms</td></tr>",
            f"<tr><td><b>GOMS théorique</b></td>"
            f"<td align='center'>{goms_mouse:.0f} ms</td>"
            f"<td align='center'>{goms_kb:.0f} ms</td></tr>",
            f"<tr><td><b>Écart théorie/pratique</b></td>"
            f"<td align='center'>{ecart_mouse:+.1f}%</td>"
            f"<td align='center'>{ecart_kb:+.1f}%</td></tr>",
            "</table>",
            "",
            f"<b>➜ {faster} plus rapide</b> (×{ratio:.2f})",
        ]
        self.results_label.setText("<br>".join(result_lines))

        # GOMS formula reminder
        goms_lines = [
            "<b>Formules GOMS utilisées :</b>",
            f"Souris : M + H + 4P + 4K = {M:.0f} + {H:.0f} + 4×{P:.0f} + 4×{K:.0f} = <b>{goms_mouse:.0f} ms</b>",
            f"Clavier : M + 2K = {M:.0f} + 2×{K:.0f} = <b>{goms_kb:.0f} ms</b>",
            "",
            f"<span style='color:#888'>Valeurs : K = {K:.0f} ms  H = {H:.0f} ms  "
            f"P = {P:.0f} ms  M = {M:.0f} ms</span>",
        ]
        self.goms_label.setText("<br>".join(goms_lines))

        self.content_stack.setCurrentIndex(2)

    def _cleanup_ready_btn(self) -> None:
        if hasattr(self, "_ready_btn_ref") and self._ready_btn_ref:
            self._ready_btn_ref.setParent(None)
            self._ready_btn_ref = None

    def _reset(self) -> None:
        self._cleanup_ready_btn()
        self._signal_timer.stop()
        self.phase = "idle"
        self.trial = 0
        self.mouse_times = []
        self.keyboard_times = []
        self.waiting_signal = False
        self.file_dialog.hide()
        self.menu_bar.reset()
        self.menu_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.trial_progress_label.setText(f"Essai : 0 / {NUM_TRIALS}")
        self.countdown_label.setText("")
        self.signal_widget.setText("")
        self.last_delta_label.setText("")
        self.content_stack.setCurrentIndex(0)