import sys
import os
import platform
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PySide6.QtGui import QAction, QIcon
from menu_screen import MenuScreen
from fitts_experiment_screen import FittsExperimentScreen
from stats_screen import StatsScreen
from settings_screen import SettingsScreen
from keystroke_menu_screen import KeystrokeMenuScreen
from cognitive_load_experiment import CognitiveLoadExperiment
from navigation_experiment import NavigationExperiment
from k_experiment import KExperiment
from h_2_experiment import H2Experiment
from tp.c_experiment import CExperiment
from tp.settings.keystroke_settings_screen import KeystrokeSettingsScreen, load_goms_settings
from tp.settings.help import HelpDialog


class MainWindow(QMainWindow):
    """
    Main application window that manages different screens using a QStackedWidget.
    """

    def __init__(self) -> None:
        super().__init__()
        self._action_dark = None
        self._action_light = None
        self.setWindowTitle("Loi de Fitts & Keystroke - HM40")
        self.resize(800, 600)

        # Application icon
        import os as _os
        _icon_dir = _os.path.dirname(_os.path.abspath(__file__))
        for _icon_name in ("icons/app_icon.png", "icons/app_icon.ico"):
            _icon_path = _os.path.join(_icon_dir, _icon_name)
            if _os.path.exists(_icon_path):
                self.setWindowIcon(QIcon(_icon_path))
                break

        self._current_theme = "dark"  # "dark" | "light"

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
        self.h_2_experiment_screen = H2Experiment(self)
        self.c_experiment_screen = CExperiment(self)
        self.keystroke_settings_screen = KeystrokeSettingsScreen(self)

        # Add screens to the stack
        self.stack.addWidget(self.menu_screen)  # index 0
        self.stack.addWidget(self.fitts_screen)  # index 1
        self.stack.addWidget(self.stats_screen)  # index 2
        self.stack.addWidget(self.settings_screen)  # index 3
        self.stack.addWidget(self.keystroke_menu_screen)  # index 4
        self.stack.addWidget(self.cognitive_load_screen)  # index 5
        self.stack.addWidget(self.navigation_screen)  # index 6
        self.stack.addWidget(self.k_experiment_screen)  # index 7
        self.stack.addWidget(self.h_2_experiment_screen)  # index 8
        self.stack.addWidget(self.c_experiment_screen)  # index 9
        self.stack.addWidget(self.keystroke_settings_screen)  # index 10

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
        if platform.system() == "Darwin":
            self.menuBar().setNativeMenuBar(True)
        else:
            self.menuBar().setNativeMenuBar(False)

        # Fichier
        file_menu = self.menuBar().addMenu("Fichier")
        exit_action = QAction("Quitter", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Navigation
        nav_menu = self.menuBar().addMenu("Navigation")

        home_action = QAction("Menu principal", self)
        home_action.triggered.connect(lambda: self.switch_screen(0))
        nav_menu.addAction(home_action)

        keystroke_menu_action = QAction("Expériences Keystroke", self)
        keystroke_menu_action.triggered.connect(lambda: self.switch_screen(4))
        nav_menu.addAction(keystroke_menu_action)

        settings_action = QAction("Paramètres Fitts", self)
        settings_action.triggered.connect(lambda: self.switch_screen(3))
        nav_menu.addAction(settings_action)

        keystroke_setting = QAction("Paramètres Keystroke", self)
        keystroke_setting.triggered.connect(lambda: self.switch_screen(10))
        nav_menu.addAction(keystroke_setting)

        # Affichage
        display_menu = self.menuBar().addMenu("Affichage")

        theme_menu = display_menu.addMenu("Thème de l'interface")

        self._action_dark = QAction("Thème sombre", self)
        self._action_dark.setCheckable(True)
        self._action_dark.setChecked(True)
        self._action_dark.triggered.connect(lambda: self._apply_theme("dark"))
        theme_menu.addAction(self._action_dark)

        self._action_light = QAction("Thème clair", self)
        self._action_light.setCheckable(True)
        self._action_light.setChecked(False)
        self._action_light.triggered.connect(lambda: self._apply_theme("light"))
        theme_menu.addAction(self._action_light)

        # ? Aide
        help_menu = self.menuBar().addMenu("?")
        help_action = QAction("Aide", self)
        help_action.setShortcut("F1")
        help_action.triggered.connect(self._show_help)
        help_menu.addAction(help_action)

    def _show_help(self) -> None:
        """Open the help dialog (beep + modal display)."""
        HelpDialog(self).show_with_beep()

    def switch_screen(self, index: int) -> None:
        """
        Switch the visible screen.

        Args:
            index (int): The index of the screen in the QStackedWidget.
        """
        self.stack.setCurrentIndex(index)

    def _apply_theme(self, theme: str) -> None:
        """Switch between dark and light QSS themes."""
        if theme == self._current_theme:
            return
        self._current_theme = theme
        base_dir = os.path.dirname(os.path.abspath(__file__))
        qss_file = "style.qss" if theme == "dark" else "style_light.qss"
        qss_path = os.path.join(base_dir, qss_file)
        try:
            with open(qss_path, "r", encoding="utf-8") as f:
                QApplication.instance().setStyleSheet(f.read())
        except FileNotFoundError:
            pass
        # Update checkmarks
        self._action_dark.setChecked(theme == "dark")
        self._action_light.setChecked(theme == "light")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Apply modern stylesheet
    with open("style.qss", "r") as f:
        app.setStyleSheet(f.read())

    # Load persisted GOMS empirical values before building the UI
    load_goms_settings()
    window = MainWindow()
    window.show()
    sys.exit(app.exec())