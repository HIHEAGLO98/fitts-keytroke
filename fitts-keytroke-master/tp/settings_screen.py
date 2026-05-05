from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSpinBox, QDoubleSpinBox, QPushButton, QGroupBox, QComboBox
)
from PySide6.QtCore import Qt
from constants import Settings, NUM_TARGETS, TARGET_MIN_SIZE, TARGET_MAX_SIZE, DEFAULT_A, DEFAULT_B, t


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
        self.title = QLabel("Experiment Settings")
        self.title.setObjectName("TitleLabel")
        self.title.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title)

        # Target count settings
        self.target_group = QGroupBox("Target Count")
        target_layout = QHBoxLayout()
        self.target_count_label = QLabel("Number of Targets:")
        target_layout.addWidget(self.target_count_label)
        self.target_count = QSpinBox()
        self.target_count.setRange(1, 50)
        self.target_count.setValue(Settings.num_targets)
        target_layout.addWidget(self.target_count)
        self.target_group.setLayout(target_layout)
        layout.addWidget(self.target_group)

        # Target size settings
        self.size_group = QGroupBox("Target Size Range")
        size_layout = QHBoxLayout()
        self.min_label = QLabel("Min:")
        size_layout.addWidget(self.min_label)
        self.min_size = QSpinBox()
        self.min_size.setRange(5, 100)
        self.min_size.setValue(Settings.target_min_size)
        size_layout.addWidget(self.min_size)

        self.max_label = QLabel("Max:")
        size_layout.addWidget(self.max_label)
        self.max_size = QSpinBox()
        self.max_size.setRange(10, 200)
        self.max_size.setValue(Settings.target_max_size)
        size_layout.addWidget(self.max_size)
        self.size_group.setLayout(size_layout)
        layout.addWidget(self.size_group)

        # Fitts' law coefficients
        self.coef_group = QGroupBox("Fitts' Law Coefficients")
        coef_layout = QHBoxLayout()
        self.coef_a_label = QLabel("a =")
        coef_layout.addWidget(self.coef_a_label)
        self.coef_a = QDoubleSpinBox()
        self.coef_a.setRange(0.0, 2.0)
        self.coef_a.setSingleStep(0.05)
        self.coef_a.setDecimals(2)
        self.coef_a.setValue(Settings.a_coefficient)
        coef_layout.addWidget(self.coef_a)
        self.coef_b_label = QLabel("b =")
        coef_layout.addWidget(self.coef_b_label)
        self.coef_b = QDoubleSpinBox()
        self.coef_b.setRange(0.0, 2.0)
        self.coef_b.setSingleStep(0.05)
        self.coef_b.setDecimals(2)
        self.coef_b.setValue(Settings.b_coefficient)
        coef_layout.addWidget(self.coef_b)
        self.coef_group.setLayout(coef_layout)
        layout.addWidget(self.coef_group)

        # Theme + language
        self.appearance_group = QGroupBox("Appearance")
        appearance_layout = QHBoxLayout()
        self.theme_label = QLabel()
        appearance_layout.addWidget(self.theme_label)
        self.theme_selector = QComboBox()
        self.theme_selector.addItems(["dark", "light"])
        self.theme_selector.setCurrentText(Settings.theme)
        appearance_layout.addWidget(self.theme_selector)

        self.language_label = QLabel()
        appearance_layout.addWidget(self.language_label)
        self.language_selector = QComboBox()
        self.language_selector.addItems(["fr", "en"])
        self.language_selector.setCurrentText(Settings.language)
        appearance_layout.addWidget(self.language_selector)
        self.appearance_group.setLayout(appearance_layout)
        layout.addWidget(self.appearance_group)

        # Apply coefficients immediately to affect graph in real-time
        self.apply_coef_btn = QPushButton("Apply Coefficients")
        self.apply_coef_btn.clicked.connect(self.apply_coefficients)
        layout.addWidget(self.apply_coef_btn)

        # Buttons
        button_layout = QHBoxLayout()

        self.save_btn = QPushButton("Save All Settings")
        self.save_btn.setMinimumHeight(40)
        self.save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(self.save_btn)

        self.reset_btn = QPushButton("Reset to Defaults")
        self.reset_btn.clicked.connect(self.reset_defaults)
        button_layout.addWidget(self.reset_btn)

        self.back_btn = QPushButton("Back to Menu")
        self.back_btn.setObjectName("SmallNavButton")
        self.back_btn.clicked.connect(lambda: self.main_window.switch_screen(0))
        button_layout.addWidget(self.back_btn)

        layout.addLayout(button_layout)

        # Add some spacing
        layout.addStretch()

        self.setLayout(layout)
        self.refresh_ui()

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
        Settings.theme = self.theme_selector.currentText()
        Settings.language = self.language_selector.currentText()
        self.main_window.apply_theme()
        for screen in [
            self.main_window.menu_screen,
            self.main_window.fitts_screen,
            self.main_window.stats_screen,
            self.main_window.settings_screen,
            self.main_window.keystroke_menu_screen,
            self.main_window.cognitive_load_screen,
            self.main_window.navigation_screen,
        ]:
            if hasattr(screen, "refresh_ui"):
                screen.refresh_ui()

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
        self.theme_selector.setCurrentText("dark")
        self.language_selector.setCurrentText("fr")

        # Also update the Settings class
        Settings.reset_to_defaults()

        # Apply changes to any existing data
        self.apply_coefficients()
        self.main_window.apply_theme()
        self.refresh_ui()

    def refresh_ui(self) -> None:
        self.title.setText(t("settings_title"))
        self.target_group.setTitle(t("target_count"))
        self.target_count_label.setText(t("number_of_targets"))
        self.size_group.setTitle(t("target_size_range"))
        self.min_label.setText(t("min"))
        self.max_label.setText(t("max"))
        self.coef_group.setTitle(t("fitts_coefficients"))
        self.appearance_group.setTitle(t("appearance"))
        self.theme_label.setText(f"{t('theme')}:")
        self.language_label.setText(f"{t('language')}:")
        self.apply_coef_btn.setText(t("apply_coefficients"))
        self.save_btn.setText(t("save_all_settings"))
        self.reset_btn.setText(t("reset_defaults"))
        self.back_btn.setText(t("back_menu"))