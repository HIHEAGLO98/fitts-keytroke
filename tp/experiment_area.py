from __future__ import annotations
import random
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QBrush, QColor
from PySide6.QtCore import QRect, QPoint
from constants import Settings


class ExperimentArea(QWidget):
    """
    Widget that displays the target and handles mouse events during the experiment.
    """

    def __init__(self, experiment_screen: object) -> None:
        super().__init__()
        self.experiment_screen = experiment_screen
        self.target_rect: QRect | None = None
        self.setMinimumHeight(400)
        self.setObjectName("ExperimentArea")

    def new_target(self, last_click_pos: QPoint | None) -> None:
        """
        Generate a new target with random size and position within the widget.

        Args:
            last_click_pos (QPoint | None): The position of the last click (unused here).
        """
        area = self.rect()
        # Use settings for target size
        size = random.randint(Settings.target_min_size, Settings.target_max_size)
        max_x = area.width() - size
        max_y = area.height() - size
        x = random.randint(0, max_x) if max_x > 0 else 0
        y = random.randint(0, max_y) if max_y > 0 else 0
        self.target_rect = QRect(x, y, size, size)
        self.experiment_screen.current_target = self.target_rect
        self.update()

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        if self.target_rect:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setBrush(QBrush(QColor(255, 0, 0)))
            painter.setPen(QColor(170, 0, 0))
            painter.drawEllipse(self.target_rect)

    def mousePressEvent(self, event) -> None:
        if self.target_rect and self.target_rect.contains(event.pos()):
            self.experiment_screen.target_clicked(event.pos(), self.target_rect)

    def clear_target(self) -> None:
        """
        Clear the current target display.
        """
        self.target_rect = None
        self.update()