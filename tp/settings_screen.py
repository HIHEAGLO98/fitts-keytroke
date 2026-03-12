from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSpinBox, QDoubleSpinBox, QPushButton, QGroupBox
)
from PySide6.QtCore import Qt
from constants import Settings, NUM_TARGETS, TARGET_MIN_SIZE, TARGET_MAX_SIZE, DEFAULT_A, DEFAULT_B


class SettingsScreen(QWidget):
    """
    Screen to configure application settings.
    """

    def __init__(self, main_window: object) -> None:
        super().__init__()
        self.main_window = main_window
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)

        # Title
        title = QLabel("Experiment Settings")
        title.setObjectName("TitleLabel")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Target count settings
        target_group = QGroupBox("Target Count")
        target_layout = QHBoxLayout()
        target_layout.addWidget(QLabel("Number of Targets:"))
        self.target_count = QSpinBox()
        self.target_count.setRange(1, 50)
        self.target_count.setValue(Settings.num_targets)
        target_layout.addWidget(self.target_count)
        target_group.setLayout(target_layout)
        layout.addWidget(target_group)

        # Target size settings
        size_group = QGroupBox("Target Size Range")
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Min:"))
        self.min_size = QSpinBox()
        self.min_size.setRange(5, 100)
        self.min_size.setValue(Settings.target_min_size)
        size_layout.addWidget(self.min_size)

        size_layout.addWidget(QLabel("Max:"))
        self.max_size = QSpinBox()
        self.max_size.setRange(10, 200)
        self.max_size.setValue(Settings.target_max_size)
        size_layout.addWidget(self.max_size)
        size_group.setLayout(size_layout)
        layout.addWidget(size_group)

        # Fitts' law coefficients
        coef_group = QGroupBox("Fitts' Law Coefficients")
        coef_layout = QHBoxLayout()
        coef_layout.addWidget(QLabel("a ="))
        self.coef_a = QDoubleSpinBox()
        self.coef_a.setRange(0.0, 2.0)
        self.coef_a.setSingleStep(0.05)
        self.coef_a.setDecimals(2)
        self.coef_a.setValue(Settings.a_coefficient)
        coef_layout.addWidget(self.coef_a)
        coef_layout.addWidget(QLabel("b ="))
        self.coef_b = QDoubleSpinBox()
        self.coef_b.setRange(0.0, 2.0)
        self.coef_b.setSingleStep(0.05)
        self.coef_b.setDecimals(2)
        self.coef_b.setValue(Settings.b_coefficient)
        coef_layout.addWidget(self.coef_b)
        coef_group.setLayout(coef_layout)
        layout.addWidget(coef_group)

        # Apply coefficients immediately to affect graph in real-time
        apply_coef_btn = QPushButton("Apply Coefficients")
        apply_coef_btn.clicked.connect(self.apply_coefficients)
        layout.addWidget(apply_coef_btn)

        # Buttons
        button_layout = QHBoxLayout()

        save_btn = QPushButton("Save All Settings")
        save_btn.setMinimumHeight(40)
        save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(save_btn)

        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self.reset_defaults)
        button_layout.addWidget(reset_btn)

        back_btn = QPushButton("Back to Menu")
        back_btn.clicked.connect(lambda: self.main_window.switch_screen(0))
        button_layout.addWidget(back_btn)

        layout.addLayout(button_layout)

        # Add some spacing
        layout.addStretch()

        self.setLayout(layout)

    def apply_coefficients(self) -> None:
        """
        Apply just the coefficient changes without saving other settings.
        This allows the coefficients to affect the graph in real-time.
        """
        Settings.a_coefficient = self.coef_a.value()
        Settings.b_coefficient = self.coef_b.value()

        # If stats screen has data, update it with the new coefficients
        if hasattr(self.main_window, 'stats_screen') and self.main_window.stats_screen.data:
            # Recalculate expected times with new coefficients
            for data_point in self.main_window.stats_screen.data:
                d = data_point['D']
                w = data_point['W']
                difficulty = data_point['difficulty']
                data_point['expected_time'] = Settings.a_coefficient + Settings.b_coefficient * difficulty

            # Update the plot
            self.main_window.stats_screen.set_data(self.main_window.stats_screen.data,
                                                   self.main_window.stats_screen.is_final_view)

    def save_settings(self) -> None:
        """
        Save the current settings.
        """
        # Validate min size is less than max size
        if self.min_size.value() >= self.max_size.value():
            self.max_size.setValue(self.min_size.value() + 1)

        Settings.num_targets = self.target_count.value()
        Settings.target_min_size = self.min_size.value()
        Settings.target_max_size = self.max_size.value()
        Settings.a_coefficient = self.coef_a.value()
        Settings.b_coefficient = self.coef_b.value()

        # Return to menu
        self.main_window.switch_screen(0)

    def reset_defaults(self) -> None:
        """
        Reset all settings to default values.
        """
        self.target_count.setValue(NUM_TARGETS)
        self.min_size.setValue(TARGET_MIN_SIZE)
        self.max_size.setValue(TARGET_MAX_SIZE)
        self.coef_a.setValue(DEFAULT_A)
        self.coef_b.setValue(DEFAULT_B)

        # Also update the Settings class
        Settings.reset_to_defaults()

        # Apply changes to any existing data
        self.apply_coefficients()