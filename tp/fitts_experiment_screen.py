from __future__ import annotations
import time
import math

from PySide6.QtGui import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QMainWindow, QHBoxLayout
from PySide6.QtCore import QPoint
from constants import Settings


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
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout()
        instructions = QLabel("Click Start to begin the Fitts experiment")
        instructions.setAlignment(Qt.AlignCenter)
        layout.addWidget(instructions)

        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_experiment)
        button_layout.addWidget(self.start_button)

        layout.addLayout(button_layout)

        from experiment_area import ExperimentArea
        self.area = ExperimentArea(self)
        layout.addWidget(self.area, stretch=1)

        self.setLayout(layout)

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
        self.area.new_target(None)

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

        if self.target_index < Settings.num_targets:  # Use value from settings
            self.area.new_target(pos)
        else:
            self.end_experiment()

    def end_experiment(self) -> None:
        """
        End the experiment, enable the start button, and display the statistics.
        """
        self.start_button.setEnabled(True)
        self.stats_screen.set_data(self.targets_data, is_final=True)
        # Assuming parent is the MainWindow, which has the switch_screen method
        self.main_window.switch_screen(2)

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