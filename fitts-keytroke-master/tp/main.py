import sys
import platform
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PySide6.QtGui import QAction
from constants import Settings, t
from menu_screen import MenuScreen
from fitts_experiment_screen import FittsExperimentScreen
from stats_screen import StatsScreen
from settings_screen import SettingsScreen
from keystroke_menu_screen import KeystrokeMenuScreen
from cognitive_load_experiment import CognitiveLoadExperiment
from navigation_experiment import NavigationExperiment


class MainWindow(QMainWindow):
    """
    Main application window that manages different screens using a QStackedWidget.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(t("app_title"))
        self.resize(1280, 800)
        self.setMinimumSize(1100, 700)

        self.stack = QStackedWidget(self)
        self.setCentralWidget(self.stack)

        # Initialize screens
        self.menu_screen = MenuScreen(self)
        self.fitts_screen = FittsExperimentScreen(self)
        self.stats_screen = StatsScreen(self)
        self.settings_screen = SettingsScreen(self)
        self.keystroke_menu_screen = KeystrokeMenuScreen(self)
        self.cognitive_load_screen = CognitiveLoadExperiment(self)
        self.navigation_screen = NavigationExperiment(self)

        # Add screens to the stack
        self.stack.addWidget(self.menu_screen)  # index 0
        self.stack.addWidget(self.fitts_screen)  # index 1
        self.stack.addWidget(self.stats_screen)  # index 2
        self.stack.addWidget(self.settings_screen)  # index 3
        self.stack.addWidget(self.keystroke_menu_screen)  # index 4
        self.stack.addWidget(self.cognitive_load_screen)  # index 5
        self.stack.addWidget(self.navigation_screen)  # index 6

        # Provide the stats screen reference to the Fitts screen
        self.fitts_screen.set_stats_screen(self.stats_screen)
        
        # Provide the stats screen reference to the keystroke experiment screens
        self.cognitive_load_screen.set_stats_screen(self.stats_screen)
        self.navigation_screen.set_stats_screen(self.stats_screen)

        # Setup menu bar
        self.setup_menu()
        self.apply_theme()
        self.refresh_ui()

    def setup_menu(self) -> None:
        """
        Setup the application menu bar based on the operating system.
        """
        # Create menu bar - macOS uses native menu bar outside the window
        if platform.system() == "Darwin":  # macOS
            self.menuBar().setNativeMenuBar(True)
        else:
            self.menuBar().setNativeMenuBar(False)

        self.file_menu = self.menuBar().addMenu("")

        # Add actions to file menu
        self.exit_action = QAction("", self)
        self.exit_action.triggered.connect(self.close)
        self.file_menu.addAction(self.exit_action)

        # Navigation menu
        self.nav_menu = self.menuBar().addMenu("")

        self.home_action = QAction("", self)
        self.home_action.triggered.connect(lambda: self.switch_screen(0))
        self.nav_menu.addAction(self.home_action)
        
        self.keystroke_menu_action = QAction("", self)
        self.keystroke_menu_action.triggered.connect(lambda: self.switch_screen(4))
        self.nav_menu.addAction(self.keystroke_menu_action)

        self.settings_action = QAction("", self)
        self.settings_action.triggered.connect(lambda: self.switch_screen(3))
        self.nav_menu.addAction(self.settings_action)

    def apply_theme(self) -> None:
        dark = Settings.theme == "dark"
        if dark:
            bg = "#1a1a1a"
            text = "#f3f3f3"
            panel = "#232a34"
            hover = "#2d3a4b"
            accent = "#7fd1b9"
            target_area = "#fefefe"
        else:
            bg = "#f7f9fb"
            text = "#1c2530"
            panel = "#e4e9ef"
            hover = "#d9e3ef"
            accent = "#2f7f6f"
            target_area = "#ffffff"

        style = f"""
QWidget {{
    background: {bg};
    color: {text};
    font-family: 'Arial', 'Helvetica Neue', 'Liberation Sans', sans-serif;
    font-size: 15px;
}}
QLabel#TitleLabel {{
    font-size: 28px;
    font-weight: bold;
    margin-bottom: 18px;
}}
QLabel#HelpText {{
    font-size: 15px;
    color: {accent};
    padding: 8px;
}}
QPushButton {{
    background: {panel};
    color: {text};
    border: none;
    border-radius: 16px;
    padding: 18px 14px;
    font-size: 18px;
    font-weight: 600;
    margin: 8px;
}}
QPushButton:hover {{
    background: {hover};
    color: {accent};
}}
QPushButton#SmallNavButton {{
    font-size: 13px;
    padding: 6px 10px;
    max-width: 100px;
    min-width: 72px;
    border-radius: 10px;
}}
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
    background: {panel};
    color: {text};
    border-radius: 10px;
    border: 1px solid {accent};
    padding: 6px 10px;
}}
#StatsFields QLabel {{
    color: {accent};
    font-weight: 600;
}}
QWidget#ExperimentArea {{
    background-color: {target_area};
    border: 1px solid {accent};
    border-radius: 12px;
}}
QLabel#CountdownOverlay {{
    background: transparent;
    color: {accent};
    font-size: 90px;
    font-weight: 800;
}}
"""
        self.window().setStyleSheet(style)
        self.setWindowTitle(t("app_title"))
        self.refresh_ui()

    def refresh_ui(self) -> None:
        self.setWindowTitle(t("app_title"))
        if hasattr(self, "file_menu"):
            self.file_menu.setTitle(t("file_menu"))
            self.nav_menu.setTitle(t("navigation_menu"))
            self.exit_action.setText(t("exit"))
            self.home_action.setText(t("main_menu"))
            self.keystroke_menu_action.setText(t("keystroke_experiments"))
            self.settings_action.setText(t("settings"))
        for screen in [
            self.menu_screen,
            self.fitts_screen,
            self.stats_screen,
            self.settings_screen,
            self.keystroke_menu_screen,
            self.cognitive_load_screen,
            self.navigation_screen,
        ]:
            if hasattr(screen, "refresh_ui"):
                screen.refresh_ui()

    def switch_screen(self, index: int) -> None:
        """
        Switch the visible screen.

        Args:
            index (int): The index of the screen in the QStackedWidget.
        """
        self.stack.setCurrentIndex(index)
        current = self.stack.currentWidget()
        if hasattr(current, "refresh_ui"):
            current.refresh_ui()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())