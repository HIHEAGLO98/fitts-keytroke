from __future__ import annotations
import numpy as np
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QFrame, QSizePolicy
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from constants import Settings, t


class StatsScreen(QWidget):
    """
    Screen to display the results and perform regression analysis on the Fitts experiment data.
    """

    def __init__(self, main_window: object) -> None:
        super().__init__()
        self.main_window = main_window
        self.data: list[dict[str, float]] = []
        self.is_final_view: bool = False
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout()

        self.status_label = QLabel()
        self.status_label.setObjectName("TitleLabel")
        layout.addWidget(self.status_label)

        # Coefficients at the top
        inputs_frame = QFrame()
        inputs_frame.setObjectName("StatsFields")
        inputs_layout = QHBoxLayout()
        inputs_layout.setContentsMargins(0, 0, 0, 0)
        self.label_a = QLabel()
        inputs_layout.addWidget(self.label_a)
        self.input_a = QLineEdit(str(Settings.a_coefficient))
        self.input_a.textChanged.connect(self.coefficient_changed)
        inputs_layout.addWidget(self.input_a)

        self.label_b = QLabel()
        inputs_layout.addWidget(self.label_b)
        self.input_b = QLineEdit(str(Settings.b_coefficient))
        self.input_b.textChanged.connect(self.coefficient_changed)
        inputs_layout.addWidget(self.input_b)
        inputs_frame.setLayout(inputs_layout)
        layout.addWidget(inputs_frame)

        # Add graph
        self.canvas = FigureCanvas(Figure(figsize=(8, 5)))
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.original_xlim = None
        self.original_ylim = None
        layout.addWidget(self.canvas, stretch=2)
        self.ax = self.canvas.figure.subplots()
        self.apply_chart_theme()

        # X-axis selector
        x_axis_frame = QFrame()
        x_axis_frame.setObjectName("StatsFields")
        x_axis_layout = QHBoxLayout()
        x_axis_layout.setContentsMargins(0, 0, 0, 0)
        x_axis_layout.setSpacing(8)
        self.x_axis_label = QLabel()
        x_axis_layout.addWidget(self.x_axis_label)
        self.x_axis_selector = QComboBox()
        self.x_axis_selector.addItems(["Target Number", "Time", "Index of Difficulty"])
        self.x_axis_selector.currentTextChanged.connect(self.update_plot)
        x_axis_layout.addWidget(self.x_axis_selector)
        x_axis_frame.setLayout(x_axis_layout)
        layout.addWidget(x_axis_frame)

        # Navigation buttons
        nav_layout = QHBoxLayout()
        self.back_btn = QPushButton()
        self.back_btn.setObjectName("SmallNavButton")
        self.back_btn.clicked.connect(lambda: self.main_window.switch_screen(0))
        nav_layout.addWidget(self.back_btn)

        self.restart_btn = QPushButton()
        self.restart_btn.setObjectName("SmallNavButton")
        self.restart_btn.clicked.connect(self.restart_experiment)
        nav_layout.addWidget(self.restart_btn)

        self.zoom_reset_btn = QPushButton()
        self.zoom_reset_btn.setObjectName("SmallNavButton")
        self.zoom_reset_btn.clicked.connect(self.reset_zoom)
        nav_layout.addWidget(self.zoom_reset_btn)

        layout.addLayout(nav_layout)

        self.setLayout(layout)
        self.refresh_ui()

    def coefficient_changed(self) -> None:
        """
        Handle coefficient input changes: switch to difficulty view and update plot
        """
        # Update settings with current values
        try:
            a = float(self.input_a.text())
            b = float(self.input_b.text())
            Settings.a_coefficient = a
            Settings.b_coefficient = b
        except ValueError:
            pass
        # Set x-axis to Index of Difficulty when coefficients change
        self.x_axis_selector.setCurrentText("Index of Difficulty")
        self.update_plot()

    def set_data(self, data: list[dict[str, float]], is_final: bool = True) -> None:
        """
        Set the experimental data and plot the statistics.

        Args:
            data (list[dict[str, float]]): List of trial data dictionaries.
            is_final (bool): Whether this is the final view after completing all targets.
        """
        self.data = data
        self.is_final_view = is_final
        # Calculate optimal coefficients from actual times
        self.calculate_optimal_coefficients()
        self.refresh_ui()

    def calculate_optimal_coefficients(self) -> None:
        """Calculate optimal coefficients a and b from actual time data using linear regression."""
        if not self.data or len(self.data) < 2:
            return
        
        try:
            # Sort by difficulty for regression
            sorted_data = sorted(self.data, key=lambda d: d['difficulty'])
            x_data = np.array([d['difficulty'] for d in sorted_data])
            y_actual = np.array([d['actual_time'] for d in sorted_data])
            
            # Check if we have enough variation in x data
            if len(x_data) > 1 and np.std(x_data) > 0:
                # Linear regression: y = a + b*x where x = log2(1 + D/W), y = actual_time
                coeffs = np.polyfit(x_data, y_actual, 1)
                b_optimal = coeffs[0]  # slope
                a_optimal = coeffs[1]  # intercept
                
                # Update input fields and settings
                self.input_a.blockSignals(True)
                self.input_b.blockSignals(True)
                self.input_a.setText(f"{a_optimal:.4f}")
                self.input_b.setText(f"{b_optimal:.4f}")
                self.input_a.blockSignals(False)
                self.input_b.blockSignals(False)
                
                Settings.a_coefficient = a_optimal
                Settings.b_coefficient = b_optimal
        except (ValueError, np.linalg.LinAlgError):
            # If calculation fails, keep default values
            pass

    def update_plot(self, *_):
        """
        Update the plot based on the current x-axis selection.
        Only shows regression line for Index of Difficulty view.
        """
        self.ax.clear()
        self.apply_chart_theme()
        if not self.data:
            self.canvas.draw()
            return

        x_axis_choice = self.x_axis_selector.currentText()

        if x_axis_choice == t("target_number"):
            x_data = [d['target_index'] for d in self.data]
            x_label = t("target_number")
            # Connected points for time series views
            self.ax.plot(x_data, [d['actual_time'] for d in self.data], 'o-', label=t("actual_time"))
            self.ax.plot(x_data, [d['expected_time'] for d in self.data], 's--', label=t("expected_time"))

        elif x_axis_choice == t("time"):
            # For time, use cumulative time
            cumulative_time = 0
            x_data = []
            for d in self.data:
                cumulative_time += d['actual_time']
                x_data.append(cumulative_time)
            x_label = "Cumulative Time (s)"
            # Connected points for time series views
            self.ax.plot(x_data, [d['actual_time'] for d in self.data], 'o-', label=t("actual_time"))
            self.ax.plot(x_data, [d['expected_time'] for d in self.data], 's--', label=t("expected_time"))

        else:  # Index of Difficulty
            # For difficulty view, sort by difficulty for better regression visualization
            sorted_data = sorted(self.data, key=lambda d: d['difficulty'])
            x_data = [d['difficulty'] for d in sorted_data]
            x_label = "Index of Difficulty (log2(D/W+1))"

            # Scatter plot (unconnected) for actual times in difficulty view
            self.ax.plot(x_data, [d['actual_time'] for d in sorted_data], 'o', label=t("actual_time"))
            self.ax.plot(x_data, [d['expected_time'] for d in sorted_data], 's--', label=t("expected_time"))

            # Calculate regression line based on actual times
            if len(x_data) > 1:
                try:
                    a = float(self.input_a.text())
                    b = float(self.input_b.text())
                    
                    # Generate more points for a smoother regression line
                    min_difficulty = min(x_data)
                    max_difficulty = max(x_data)
                    regression_x = [min_difficulty + (max_difficulty - min_difficulty) * i / 100 for i in range(101)]
                    regression_y = [a + b * x for x in regression_x]
                    
                    # Plot the regression line (Fitts' law based on actual times)
                    self.ax.plot(regression_x, regression_y, 'r-', linewidth=2.5, label=f"{t('fitts_law')} (a={a:.4f}, b={b:.4f})")
                except ValueError:
                    # Skip regression if invalid coefficients
                    pass

        self.ax.set_xlabel(x_label)
        self.ax.set_ylabel("Time (s)")
        self.ax.legend()
        # Store original limits for zoom reset
        self.original_xlim = self.ax.get_xlim()
        self.original_ylim = self.ax.get_ylim()
        self.canvas.draw()
        # Enable interactive zoom via scroll wheel
        self.canvas.mpl_connect('scroll_event', self._on_scroll_zoom)

    def apply_chart_theme(self) -> None:
        is_dark = Settings.theme == "dark"
        if is_dark:
            bg = "#1a1a1a"
            fg = "#f3f3f3"
        else:
            bg = "#ffffff"
            fg = "#1c2530"
        self.ax.set_facecolor(bg)
        self.canvas.figure.patch.set_facecolor(bg)
        self.ax.tick_params(colors=fg)
        self.ax.xaxis.label.set_color(fg)
        self.ax.yaxis.label.set_color(fg)
        self.ax.title.set_color(fg)
        for side in ["bottom", "top", "left", "right"]:
            self.ax.spines[side].set_color(fg)

    def reset_zoom(self) -> None:
        """Reset the plot zoom to show all data."""
        if self.original_xlim and self.original_ylim:
            self.ax.set_xlim(self.original_xlim)
            self.ax.set_ylim(self.original_ylim)
            self.canvas.draw()
        else:
            self.ax.autoscale()
            self.canvas.draw()

    def refresh_ui(self) -> None:
        self.status_label.setText(t("final_results") if self.is_final_view else t("live_results"))
        self.label_a.setText(t("coef_a"))
        self.label_b.setText(t("coef_b"))
        self.x_axis_label.setText(t("x_axis"))
        current = self.x_axis_selector.currentText()
        self.x_axis_selector.blockSignals(True)
        self.x_axis_selector.clear()
        self.x_axis_selector.addItems([t("target_number"), t("time"), t("difficulty_index")])
        self.x_axis_selector.setCurrentText(current if current in [t("target_number"), t("time"), t("difficulty_index")] else t("target_number"))
        self.x_axis_selector.blockSignals(False)
        self.back_btn.setText(t("back_menu"))
        self.restart_btn.setText(t("restart"))
        self.zoom_reset_btn.setText(t("zoom_reset"))
        self.update_plot()

    def restart_experiment(self) -> None:
        """
        Navigate back to the Fitts experiment screen and trigger a restart.
        """
        self.main_window.switch_screen(1)
        # Reset the experiment to be ready for a new start
        self.main_window.fitts_screen.start_button.setEnabled(True)
    
    def _on_scroll_zoom(self, event) -> None:
        """Handle mouse scroll zoom on the plot."""
        if event.inaxes != self.ax:
            return
        
        cur_xlim = self.ax.get_xlim()
        cur_ylim = self.ax.get_ylim()
        
        xdata = event.xdata
        ydata = event.ydata
        
        if event.button == 'up':
            scale_factor = 0.8  # Zoom in
        elif event.button == 'down':
            scale_factor = 1.2  # Zoom out
        else:
            return
        
        new_width = (cur_xlim[1] - cur_xlim[0]) * scale_factor
        new_height = (cur_ylim[1] - cur_ylim[0]) * scale_factor
        
        relx = (cur_xlim[1] - xdata) / (cur_xlim[1] - cur_xlim[0])
        rely = (cur_ylim[1] - ydata) / (cur_ylim[1] - cur_ylim[0])
        
        self.ax.set_xlim([xdata - new_width * (1 - relx), xdata + new_width * relx])
        self.ax.set_ylim([ydata - new_height * (1 - rely), ydata + new_height * rely])
        self.canvas.draw()