from __future__ import annotations
import time
import math

from PySide6.QtGui import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QMainWindow, QHBoxLayout,
    QMessageBox, QStackedLayout, QGraphicsOpacityEffect, QSpinBox, QFrame
)
from PySide6.QtCore import QPoint, QTimer, QPropertyAnimation
from constants import Settings, t


class FittsExperimentScreen(QWidget):
    """
    Screen to conduct the Fitts experiment where users click on sequential targets.
    """

    def __init__(self, main_window: QMainWindow) -> None:
        super().__init__(main_window)
        self.main_window = main_window
        self.stats_screen: object = None
        self.targets_data: list[dict[str, float]] = []
        self.current_target = None
        self.target_index: int = 0
        self.last_click_time: float = 0.0
        self.countdown_value = 0
        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self._on_countdown_tick)
        self.countdown_fade = None
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout()
        self.instructions = QLabel()
        self.instructions.setAlignment(Qt.AlignCenter)
        self.instructions.setObjectName("TitleLabel")
        layout.addWidget(self.instructions)

        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setObjectName("HelpText")
        layout.addWidget(self.status_label)

        # Add remaining targets display
        self.remaining_targets_label = QLabel()
        self.remaining_targets_label.setAlignment(Qt.AlignCenter)
        self.remaining_targets_label.setObjectName("HelpText")
        layout.addWidget(self.remaining_targets_label)

        # Add target count selector
        targets_frame = QFrame()
        targets_frame.setObjectName("StatsFields")
        targets_layout = QHBoxLayout()
        targets_layout.setContentsMargins(0, 0, 0, 0)
        self.targets_label = QLabel()
        targets_layout.addWidget(self.targets_label)
        self.targets_spinbox = QSpinBox()
        self.targets_spinbox.setMinimum(3)
        self.targets_spinbox.setMaximum(50)
        self.targets_spinbox.setValue(Settings.num_targets)
        self.targets_spinbox.setEnabled(True)
        def on_targets_changed(value):
            Settings.num_targets = value
        self.targets_spinbox.valueChanged.connect(on_targets_changed)
        targets_layout.addWidget(self.targets_spinbox)
        targets_layout.addStretch()
        targets_frame.setLayout(targets_layout)
        layout.addWidget(targets_frame)

        from experiment_area import ExperimentArea
        self.area_container = QWidget()
        area_stack = QStackedLayout(self.area_container)
        area_stack.setStackingMode(QStackedLayout.StackAll)
        self.area = ExperimentArea(self)
        area_stack.addWidget(self.area)

        self.countdown_overlay = QLabel("")
        self.countdown_overlay.setAlignment(Qt.AlignCenter)
        self.countdown_overlay.setObjectName("CountdownOverlay")
        self.countdown_overlay.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.countdown_overlay.hide()
        self.countdown_opacity = QGraphicsOpacityEffect(self.countdown_overlay)
        self.countdown_overlay.setGraphicsEffect(self.countdown_opacity)
        area_stack.addWidget(self.countdown_overlay)

        layout.addWidget(self.area_container, stretch=1)

        # Move buttons to the bottom
        button_layout = QHBoxLayout()
        self.start_button = QPushButton()
        self.start_button.clicked.connect(self.start_experiment)
        button_layout.addWidget(self.start_button)

        self.explain_button = QPushButton()
        self.explain_button.clicked.connect(self.show_fitts_explanation)
        button_layout.addWidget(self.explain_button)

        self.menu_button = QPushButton()
        self.menu_button.setObjectName("SmallNavButton")
        self.menu_button.clicked.connect(lambda: self.main_window.switch_screen(0))
        button_layout.addWidget(self.menu_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)
        self.refresh_ui()

    def set_stats_screen(self, stats_screen: object) -> None:
        """
        Set the stats screen to display results after the experiment.

        Args:
            stats_screen: The screen instance to display the statistics.
        """
        self.stats_screen = stats_screen

    def start_experiment(self) -> None:
        """
        Initialize experiment data and start the Fitts test.
        """
        self.targets_data = []
        self.target_index = 0
        self.last_click_time = None
        self.current_target = None
        self.start_button.setEnabled(False)
        self.targets_spinbox.setEnabled(False)
        self.countdown_value = 3
        self.status_label.setText(t("countdown_label").format(seconds=self.countdown_value))
        self._show_countdown_overlay(str(self.countdown_value))
        self.area.clear_target()
        self.countdown_timer.start(1000)

    def _on_countdown_tick(self) -> None:
        self.countdown_value -= 1
        if self.countdown_value > 0:
            self.status_label.setText(t("countdown_label").format(seconds=self.countdown_value))
            self._show_countdown_overlay(str(self.countdown_value))
            return
        self.countdown_timer.stop()
        self._show_countdown_overlay("GO", hide_after_ms=520)
        self.status_label.setText(f"{t('running_label')} {t('target_hint')}")
        self.area.new_target(None)

    def _show_countdown_overlay(self, text: str, hide_after_ms: int = 700) -> None:
        self.countdown_overlay.setText(text)
        self.countdown_overlay.show()
        self.countdown_opacity.setOpacity(1.0)
        self.countdown_fade = QPropertyAnimation(self.countdown_opacity, b"opacity", self)
        self.countdown_fade.setDuration(hide_after_ms)
        self.countdown_fade.setStartValue(1.0)
        self.countdown_fade.setEndValue(0.0)
        self.countdown_fade.finished.connect(self.countdown_overlay.hide)
        self.countdown_fade.start()

    def target_clicked(self, pos: QPoint, target_rect: object) -> None:
        """
        Handle a target click: compute the actual and expected times and record the trial data.

        Args:
            pos (QPoint): The click position.
            target_rect: The QRect of the target.
        """
        current_time = time.time()

        # Handle the first click differently
        if self.last_click_time is None:
            self.last_click_time = current_time
            self.update_remaining_targets()
            self.area.new_target(pos)
            return  # Skip recording data for the first target

        actual_time = current_time - self.last_click_time

        # Determine the center of the previous target or the area center if first target
        if self.current_target:
            prev_center = self.current_target.center()
        else:
            prev_center = self.area.rect().center()

        D = ((pos.x() - prev_center.x()) ** 2 + (pos.y() - prev_center.y()) ** 2) ** 0.5
        W = target_rect.width()

        # Always use current settings for the expected time calculation
        expected_time = Settings.a_coefficient + Settings.b_coefficient * math.log2(D / W + 1) if W > 0 else 0.0
        difficulty = math.log2(D / W + 1) if W > 0 else 0.0

        self.targets_data.append({
            'D': D,
            'W': W,
            'actual_time': actual_time,
            'expected_time': expected_time,
            'difficulty': difficulty,
            'target_index': self.target_index  # Add target index for x-axis plotting
        })
        self.last_click_time = current_time
        self.target_index += 1

        # Update stats screen with current data for live updates
        self.stats_screen.set_data(self.targets_data, is_final=False)
        self.update_remaining_targets()

        if self.target_index < Settings.num_targets - 1:  # Have exactly num_targets total targets
            self.area.new_target(pos)
        else:
            self.end_experiment()

    def end_experiment(self) -> None:
        """
        End the experiment, enable the start button, and display the statistics.
        """
        self.start_button.setEnabled(True)
        self.targets_spinbox.setEnabled(True)
        self.countdown_overlay.hide()
        self.stats_screen.set_data(self.targets_data, is_final=True)
        # Assuming parent is the MainWindow, which has the switch_screen method
        self.main_window.switch_screen(2)

    def show_fitts_explanation(self) -> None:
        message = (
            f"{t('fitts_law_title')}\n\n"
            "T = a + b * log2(D/W + 1)\n\n"
            f"{t('fitts_law_short')}"
        )
        QMessageBox.information(self, t("fitts_law_title"), message)

    def update_remaining_targets(self) -> None:
        """Update the display of remaining targets."""
        self.remaining_targets_label.setText(f"Cible {self.target_index + 1} / {Settings.num_targets}")

    def refresh_ui(self) -> None:
        self.instructions.setText(t("fitts_intro"))
        self.targets_label.setText(t("target_count"))
        self.start_button.setText(t("start"))
        self.explain_button.setText(t("show_fitts_law"))
        self.menu_button.setText(t("back_menu"))
        if not self.countdown_timer.isActive():
            self.status_label.setText(t("target_hint"))
            self.remaining_targets_label.setText("")

    def showEvent(self, event) -> None:
        """
        Called when the widget is shown. Clear any previous targets.
        """
        super().showEvent(event)
        # Clear any targets left from previous experiment runs
        if hasattr(self, 'area') and self.area:
            self.area.clear_target()
        # Reset current_target reference in this class as well
        self.current_target = None
        self.refresh_ui()