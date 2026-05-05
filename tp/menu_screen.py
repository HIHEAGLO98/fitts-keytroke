from __future__ import annotations
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox, QHBoxLayout, QSizePolicy
from PySide6.QtCore import Qt, QSize, QEvent, QVariantAnimation
from PySide6.QtGui import QIcon
from constants import t


class MenuScreen(QWidget):
    """
    Menu screen that allows the user to choose between experiments.
    """

    def __init__(self, main_window: object) -> None:
        super().__init__()
        self.main_window = main_window
        self.title_animation: QVariantAnimation | None = None
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignCenter)

        self.label = QLabel()
        self.label.setObjectName("TitleLabel")
        self.label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.label)

        self.help_label = QLabel()
        self.help_label.setObjectName("HelpText")
        self.help_label.setAlignment(Qt.AlignCenter)
        self.help_label.setWordWrap(True)
        main_layout.addWidget(self.help_label)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(24)
        btn_layout.setAlignment(Qt.AlignCenter)

        self.btn_fitts = QPushButton()
        # Use a custom SVG icon with white color for contrast
        self.btn_fitts.setIcon(QIcon("icons/play_white.svg"))
        self.btn_fitts.setIconSize(QSize(48, 48))
        self.btn_fitts.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.btn_fitts.setMinimumHeight(220)
        self.btn_fitts.clicked.connect(lambda: self.main_window.switch_screen(1))
        self.btn_fitts.installEventFilter(self)
        btn_layout.addWidget(self.btn_fitts)

        self.btn_keystroke = QPushButton()
        self.btn_keystroke.setIcon(QIcon("icons/keyboard_white.svg"))
        self.btn_keystroke.setIconSize(QSize(48, 48))
        self.btn_keystroke.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.btn_keystroke.setMinimumHeight(220)
        self.btn_keystroke.clicked.connect(lambda: self.main_window.switch_screen(4))
        self.btn_keystroke.installEventFilter(self)
        btn_layout.addWidget(self.btn_keystroke)

        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)
        self.refresh_ui()

    def refresh_ui(self) -> None:
        self.label.setText(t("choose_experiment"))
        self.help_label.setText(t("default_menu_help"))
        self.btn_fitts.setText(f"  {t('fitts_experiment')}")
        self.btn_keystroke.setText(f"  {t('keystroke_experiment')}")

    def _animate_title(self, hovered: bool) -> None:
        start = 28 if not hovered else 32
        end = 32 if hovered else 28
        self.title_animation = QVariantAnimation(self)
        self.title_animation.setDuration(160)
        self.title_animation.setStartValue(start)
        self.title_animation.setEndValue(end)
        self.title_animation.valueChanged.connect(self._set_title_size)
        self.title_animation.start()

    def _set_title_size(self, size: int) -> None:
        self.label.setStyleSheet(f"font-size: {int(size)}px; font-weight: bold;")

    def eventFilter(self, watched: object, event: QEvent) -> bool:
        if event.type() == QEvent.Enter:
            self._animate_title(True)
            if watched == self.btn_fitts:
                self.help_label.setText(t("hover_fitts_desc"))
            elif watched == self.btn_keystroke:
                self.help_label.setText(t("hover_keys_desc"))
        elif event.type() == QEvent.Leave:
            self._animate_title(False)
            self.help_label.setText(t("default_menu_help"))
        return super().eventFilter(watched, event)

    def not_implemented(self) -> None:
        """
        Display an information dialog for the unimplemented experiment.
        """
        msg = QMessageBox(self)
        msg.setWindowTitle("Info")
        msg.setText("Keystroke Experiment not implemented yet.")
        msg.exec()
