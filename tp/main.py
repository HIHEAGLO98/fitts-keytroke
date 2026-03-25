import sys
import platform
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PySide6.QtGui import QAction
from menu_screen import MenuScreen
from fitts_experiment_screen import FittsExperimentScreen
from stats_screen import StatsScreen
from settings_screen import SettingsScreen
from keystroke_menu_screen import KeystrokeMenuScreen
from cognitive_load_experiment import CognitiveLoadExperiment
from navigation_experiment import NavigationExperiment
from k_experiment import KExperiment
from h_experiment import HExperiment
from h_2_experiment import H2Experiment


class MainWindow(QMainWindow):
    """
    Main application window that manages different screens using a QStackedWidget.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Fitts & Keystroke Experiments")
        self.resize(800, 600)

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
        self.k_experiment_screen = KExperiment(self)
        self.h_experiment_screen = HExperiment(self)
        self.h_2_experiment_screen = H2Experiment(self)

        # Add screens to the stack
        self.stack.addWidget(self.menu_screen)  # index 0
        self.stack.addWidget(self.fitts_screen)  # index 1
        self.stack.addWidget(self.stats_screen)  # index 2
        self.stack.addWidget(self.settings_screen)  # index 3
        self.stack.addWidget(self.keystroke_menu_screen)  # index 4
        self.stack.addWidget(self.cognitive_load_screen)  # index 5
        self.stack.addWidget(self.navigation_screen)  # index 6
        self.stack.addWidget(self.k_experiment_screen)  # index 7
        self.stack.addWidget(self.h_experiment_screen)  # index 8
        self.stack.addWidget(self.h_2_experiment_screen)  # index 9

        # Provide the stats screen reference to the Fitts screen
        self.fitts_screen.set_stats_screen(self.stats_screen)
        
        # Provide the stats screen reference to the keystroke experiment screens
        self.cognitive_load_screen.set_stats_screen(self.stats_screen)
        self.navigation_screen.set_stats_screen(self.stats_screen)

        # Setup menu bar
        self.setup_menu()

    def setup_menu(self) -> None:
        """
        Setup the application menu bar based on the operating system.
        """
        # Create menu bar - macOS uses native menu bar outside the window
        if platform.system() == "Darwin":  # macOS
            self.menuBar().setNativeMenuBar(True)
        else:
            self.menuBar().setNativeMenuBar(False)

        # File menu
        file_menu = self.menuBar().addMenu("File")

        # Add actions to file menu
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Navigation menu
        nav_menu = self.menuBar().addMenu("Navigation")

        home_action = QAction("Main Menu", self)
        home_action.triggered.connect(lambda: self.switch_screen(0))
        nav_menu.addAction(home_action)
        
        keystroke_menu_action = QAction("Keystroke Experiments", self)
        keystroke_menu_action.triggered.connect(lambda: self.switch_screen(4))
        nav_menu.addAction(keystroke_menu_action)

        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(lambda: self.switch_screen(3))
        nav_menu.addAction(settings_action)

    def switch_screen(self, index: int) -> None:
        """
        Switch the visible screen.

        Args:
            index (int): The index of the screen in the QStackedWidget.
        """
        self.stack.setCurrentIndex(index)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Apply modern stylesheet
    with open("style.qss", "r") as f:
        app.setStyleSheet(f.read())
    window = MainWindow()
    window.show()
    sys.exit(app.exec())