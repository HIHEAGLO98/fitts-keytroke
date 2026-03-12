from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QFrame, QSizePolicy
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from constants import Settings


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

        # Add graph
        self.canvas = FigureCanvas(Figure(figsize=(8, 5)))
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.canvas, stretch=2)
        self.ax = self.canvas.figure.subplots()
        # Set dark background for the graph and axes
        self.ax.set_facecolor("#1a1a1a")
        self.canvas.figure.patch.set_facecolor("#1a1a1a")
        self.ax.tick_params(colors="#f3f3f3")
        self.ax.xaxis.label.set_color("#f3f3f3")
        self.ax.yaxis.label.set_color("#f3f3f3")
        self.ax.title.set_color("#f3f3f3")
        self.ax.spines['bottom'].set_color('#f3f3f3')
        self.ax.spines['top'].set_color('#f3f3f3')
        self.ax.spines['left'].set_color('#f3f3f3')
        self.ax.spines['right'].set_color('#f3f3f3')

        # X-axis selector
        x_axis_frame = QFrame()
        x_axis_frame.setObjectName("StatsFields")
        x_axis_layout = QHBoxLayout()
        x_axis_layout.setContentsMargins(0, 0, 0, 0)
        x_axis_layout.setSpacing(8)
        x_axis_label = QLabel("X-Axis:")
        x_axis_layout.addWidget(x_axis_label)
        self.x_axis_selector = QComboBox()
        self.x_axis_selector.addItems(["Target Number", "Time", "Index of Difficulty"])
        self.x_axis_selector.currentTextChanged.connect(self.update_plot)
        x_axis_layout.addWidget(self.x_axis_selector)
        x_axis_frame.setLayout(x_axis_layout)
        layout.addWidget(x_axis_frame)

        # User inputs for regression with immediate update
        inputs_frame = QFrame()
        inputs_frame.setObjectName("StatsFields")
        inputs_layout = QHBoxLayout()
        inputs_layout.setContentsMargins(0, 0, 0, 0)
        inputs_layout.addWidget(QLabel("Coefficient a:"))
        self.input_a = QLineEdit(str(Settings.a_coefficient))
        self.input_a.textChanged.connect(self.coefficient_changed)
        inputs_layout.addWidget(self.input_a)

        inputs_layout.addWidget(QLabel("Coefficient b:"))
        self.input_b = QLineEdit(str(Settings.b_coefficient))
        self.input_b.textChanged.connect(self.coefficient_changed)
        inputs_layout.addWidget(self.input_b)
        inputs_frame.setLayout(inputs_layout)
        layout.addWidget(inputs_frame)

        # Navigation buttons
        nav_layout = QHBoxLayout()
        back_btn = QPushButton("Back to Menu")
        back_btn.clicked.connect(lambda: self.main_window.switch_screen(0))
        nav_layout.addWidget(back_btn)

        restart_btn = QPushButton("Restart Experiment")
        restart_btn.clicked.connect(self.restart_experiment)
        nav_layout.addWidget(restart_btn)

        layout.addLayout(nav_layout)

        self.setLayout(layout)

    def coefficient_changed(self) -> None:
        """
        Handle coefficient input changes: switch to difficulty view and update plot
        """
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
        self.update_plot()

    def update_plot(self, *_):
        """
        Update the plot based on the current x-axis selection.
        Only shows regression line for Index of Difficulty view.
        """
        self.ax.clear()
        if not self.data:
            return

        x_axis_choice = self.x_axis_selector.currentText()

        if x_axis_choice == "Target Number":
            x_data = [d['target_index'] for d in self.data]
            x_label = "Target Number"
            # Connected points for time series views
            self.ax.plot(x_data, [d['actual_time'] for d in self.data], 'o-', label="Actual Times")
            self.ax.plot(x_data, [d['expected_time'] for d in self.data], 's--', label="Expected Times")

        elif x_axis_choice == "Time":
            # For time, use cumulative time
            cumulative_time = 0
            x_data = []
            for d in self.data:
                cumulative_time += d['actual_time']
                x_data.append(cumulative_time)
            x_label = "Cumulative Time (s)"
            # Connected points for time series views
            self.ax.plot(x_data, [d['actual_time'] for d in self.data], 'o-', label="Actual Times")
            self.ax.plot(x_data, [d['expected_time'] for d in self.data], 's--', label="Expected Times")

        else:  # Index of Difficulty
            # For difficulty view, sort by difficulty for better regression visualization
            sorted_data = sorted(self.data, key=lambda d: d['difficulty'])
            x_data = [d['difficulty'] for d in sorted_data]
            x_label = "Index of Difficulty (log2(D/W+1))"

            # Scatter plot (unconnected) for actual times in difficulty view
            self.ax.plot(x_data, [d['actual_time'] for d in sorted_data], 'o', label="Actual Times")
            self.ax.plot(x_data, [d['expected_time'] for d in sorted_data], 's--', label="Expected Times")

            # Only add regression line in difficulty view
            try:
                a = float(self.input_a.text())
                b = float(self.input_b.text())

                # Update settings
                Settings.a_coefficient = a
                Settings.b_coefficient = b

                # Generate more points for a smoother regression line
                min_difficulty = min(x_data)
                max_difficulty = max(x_data)
                regression_x = [min_difficulty + (max_difficulty - min_difficulty) * i / 100 for i in range(101)]
                regression_y = [a + b * x for x in regression_x]

                # Plot the regression line
                self.ax.plot(regression_x, regression_y, 'r-', label=f"Regression (a={a:.2f}, b={b:.2f})")
            except ValueError:
                # Skip regression if invalid coefficients
                pass

        self.ax.set_xlabel(x_label)
        self.ax.set_ylabel("Time (s)")
        self.ax.legend()
        self.ax.xaxis.label.set_color("#f3f3f3")
        self.ax.yaxis.label.set_color("#f3f3f3")
        self.ax.tick_params(colors="#f3f3f3")
        self.ax.title.set_color("#f3f3f3")
        self.canvas.draw()

    def restart_experiment(self) -> None:
        """
        Navigate back to the Fitts experiment screen and trigger a restart.
        """
        self.main_window.switch_screen(1)
        # Reset the experiment to be ready for a new start
        self.main_window.fitts_screen.start_button.setEnabled(True)