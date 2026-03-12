from __future__ import annotations

import time
import random
import numpy as np
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton,
                               QTextEdit, QHBoxLayout, QComboBox, QProgressBar,
                               QGroupBox, QRadioButton, QFrame, QTabWidget)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QTextCursor, QTextCharFormat
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# Sample text for navigation tasks
SAMPLE_TEXT = """Line 1: This is the first line of text for navigation experiments.
Line 2: You will navigate within this text using keyboard or mouse.
Line 3: Each task will require you to move to a specific position.
Line 4: The experiment measures which method is more efficient.
Line 5: You might need to select specific words or navigate to a location.
Line 6: Different navigation patterns will be analyzed.
Line 7: Short-range movements might favor keyboard shortcuts.
Line 8: While long-range jumps might be faster with a mouse.
Line 9: The experiment will track your timing and accuracy.
Line 10: Results will show efficiency differences between input methods."""

# Navigation task types
TASKS = [
    {"instruction": "Move cursor to the beginning of Line 3", "target_line": 2, "target_pos": 0},
    {"instruction": "Move cursor to the end of Line 8", "target_line": 7, "target_pos": -1},
    {"instruction": "Select the third word on Line 5", "target_line": 4, "target_word": 2, "select": True},
    {"instruction": "Move cursor to the beginning of the document", "target_line": 0, "target_pos": 0},
    {"instruction": "Move cursor to the end of the document", "target_line": -1, "target_pos": -1},
    {"instruction": "Select 'navigation patterns' on Line 6", "target_line": 5, "target_text": "navigation patterns",
     "select": True},
]


class NavigationExperiment(QWidget):
    """
    Screen to conduct the Keyboard vs. Mouse Text Navigation Efficiency experiment.
    """

    def __init__(self, main_window: object) -> None:
        super().__init__()
        self.main_window = main_window
        self.stats_screen = None

        # Experiment data
        self.current_mode = None  # "keyboard" or "mouse"
        self.current_task_index = 0
        self.current_task = None
        self.upcoming_task = None
        self.start_time = 0
        self.task_results = {
            "keyboard": [],
            "mouse": []
        }
        self.all_lines = SAMPLE_TEXT.split('\n')
        self.task_completed = False
        self.success_timer = QTimer(self)
        self.success_timer.setSingleShot(True)
        self.success_timer.timeout.connect(self.process_completed_task)

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout()

        # Instructions
        self.instructions_label = QLabel(
            "This experiment compares keyboard and mouse efficiency for text navigation tasks.\n"
            "You'll perform the same tasks twice: once using only keyboard, once using only mouse."
        )
        self.instructions_label.setAlignment(Qt.AlignCenter)
        self.instructions_label.setWordWrap(True)
        layout.addWidget(self.instructions_label)

        # Initialize the upcoming task display
        if len(TASKS) > 0:
            self.upcoming_task = TASKS[0]  # Set the first task as upcoming

        # Current/upcoming task frame
        self.task_frame = QFrame()
        self.task_frame.setObjectName("TaskFrame")
        self.task_frame.setStyleSheet(
            "QFrame#TaskFrame { background-color: #2d3a4b; border-radius: 8px; padding: 8px; }")
        task_layout = QVBoxLayout(self.task_frame)

        # Task header
        self.task_header = QLabel("UPCOMING TASK:")
        self.task_header.setStyleSheet("font-weight: bold; color: #7fd1b9; font-size: 16px;")
        self.task_header.setAlignment(Qt.AlignCenter)
        task_layout.addWidget(self.task_header)

        # Task description
        self.task_label = QLabel("Not started")
        self.task_label.setStyleSheet("font-weight: bold; color: #f3f3f3; font-size: 18px;")
        self.task_label.setAlignment(Qt.AlignCenter)
        self.task_label.setWordWrap(True)
        task_layout.addWidget(self.task_label)

        # Task status
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-weight: bold; color: #7fd1b9;")
        task_layout.addWidget(self.status_label)

        layout.addWidget(self.task_frame)

        # Input method selection
        self.input_group = QGroupBox("Input Method")
        input_layout = QHBoxLayout()

        self.keyboard_radio = QRadioButton("Keyboard Only")
        self.keyboard_radio.setChecked(True)
        self.mouse_radio = QRadioButton("Mouse Only")

        input_layout.addWidget(self.keyboard_radio)
        input_layout.addWidget(self.mouse_radio)
        self.input_group.setLayout(input_layout)
        layout.addWidget(self.input_group)

        # Text area
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(SAMPLE_TEXT)
        self.text_edit.setReadOnly(False)
        self.text_edit.textChanged.connect(self.on_text_changed)
        self.text_edit.cursorPositionChanged.connect(self.on_cursor_changed)
        self.text_edit.setEnabled(False)
        # Set the dark blue background color and white text
        self.text_edit.setStyleSheet("background-color: #2c3e50; color: white; border-radius: 4px; padding: 8px;")
        layout.addWidget(self.text_edit)

        # Progress indicator
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, len(TASKS) * 2)  # Both keyboard and mouse tasks
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Results graphs (hidden until experiment completes)
        self.results_graph = QWidget()
        self.results_graph.setVisible(False)
        results_graph_layout = QVBoxLayout(self.results_graph)

        # Add plots to compare keyboard vs mouse performance
        self.canvas = FigureCanvas(Figure(figsize=(8, 6)))
        self.canvas.figure.set_facecolor('#2d3a4b')
        results_graph_layout.addWidget(self.canvas)

        # Set dark background for plots
        self.axes = self.canvas.figure.subplots(2, 1)
        for ax in self.axes:
            ax.set_facecolor("#1a1a1a")
            ax.tick_params(colors="#f3f3f3")
            ax.xaxis.label.set_color("#f3f3f3")
            ax.yaxis.label.set_color("#f3f3f3")
            ax.title.set_color("#f3f3f3")
            ax.spines['bottom'].set_color('#f3f3f3')
            ax.spines['top'].set_color('#f3f3f3')
            ax.spines['left'].set_color('#f3f3f3')
            ax.spines['right'].set_color('#f3f3f3')

        layout.addWidget(self.results_graph)

        # Button layout
        button_layout = QHBoxLayout()

        # Start/Stop button
        self.start_button = QPushButton("Start Task")
        self.start_button.clicked.connect(self.start_task)
        button_layout.addWidget(self.start_button)

        # Manual override button (hidden by default)
        self.manual_complete_button = QPushButton("Manual Complete")
        self.manual_complete_button.clicked.connect(self.manual_complete_task)
        self.manual_complete_button.setVisible(False)  # Hidden by default
        button_layout.addWidget(self.manual_complete_button)

        # Back button
        back_button = QPushButton("Back to Keystroke Menu")
        back_button.clicked.connect(self.return_to_menu)
        button_layout.addWidget(back_button)

        layout.addLayout(button_layout)

        # Results section with tabs for text and graphs
        self.results_tab = QTabWidget()
        self.results_tab.setVisible(False)  # Hide until experiment is complete

        # Text results tab (hidden)
        self.results_label = QLabel("")
        self.results_label.setWordWrap(True)
        self.results_label.setVisible(False)  # Hide text results completely

        layout.addWidget(self.results_tab)

        self.setLayout(layout)

        # Initialize the preview of the first task
        self.prepare_task_display()

        # Highlight target after a slight delay to ensure text editor is ready
        QTimer.singleShot(100, self.highlight_target_goal)

    def prepare_task_display(self) -> None:
        """
        Display the upcoming task and highlight its target.
        """
        if not self.upcoming_task:
            return

        # Update task display
        self.task_header.setText("UPCOMING TASK:")
        self.task_header.setStyleSheet("font-weight: bold; color: #7fd1b9; font-size: 16px;")

        input_method = "keyboard" if self.keyboard_radio.isChecked() else "mouse"
        self.task_label.setText(f"{self.upcoming_task['instruction']} using {input_method} only")
        self.status_label.setText("Review the task, then click 'Start Task' when ready")

        # Highlight the target
        self.highlight_target_goal()

    def return_to_menu(self) -> None:
        """Return to keystroke menu after confirming if experiment is active"""
        if self.current_task is not None:
            # Stop the experiment before returning
            self.stop_experiment()

        # Return to keystroke menu
        self.main_window.switch_screen(4)  # Keystroke menu is at index 4

    def set_stats_screen(self, stats_screen: object) -> None:
        """
        Set the stats screen to display results after the experiment.

        Args:
            stats_screen: The screen instance to display the statistics.
        """
        self.stats_screen = stats_screen

    def start_task(self) -> None:
        """
        Start a new navigation task.
        """
        # Determine input mode
        self.current_mode = "keyboard" if self.keyboard_radio.isChecked() else "mouse"

        # Reset text and focus
        self.text_edit.setPlainText(SAMPLE_TEXT)
        self.text_edit.setEnabled(True)
        self.text_edit.setFocus()

        # Reset task completion flag
        self.task_completed = False

        # Set active task from upcoming task
        if self.upcoming_task:
            self.current_task = self.upcoming_task
        else:
            # First task case
            self.current_task = TASKS[self.current_task_index]

        # Update task display
        self.task_header.setText("ACTIVE TASK:")
        self.task_header.setStyleSheet("font-weight: bold; color: #e74c3c; font-size: 16px;")
        self.task_label.setText(f"{self.current_task['instruction']} using {self.current_mode} only")
        self.status_label.setText("Task in progress... completion will be detected automatically")

        # Remove highlights before starting
        self.clear_highlights()

        # Start timing
        self.start_time = time.time()

        # Update UI
        self.start_button.setText("Stop Experiment")
        self.start_button.clicked.disconnect()
        self.start_button.clicked.connect(self.stop_experiment)
        self.keyboard_radio.setEnabled(False)
        self.mouse_radio.setEnabled(False)

        # Show hint based on input mode
        if self.current_mode == "keyboard":
            self.instructions_label.setText(
                "KEYBOARD MODE: Use only keyboard shortcuts (arrow keys, Home/End, Ctrl+arrows, etc.)\n"
                "Task completion will be detected automatically when you reach the target position."
            )
        else:
            self.instructions_label.setText(
                "MOUSE MODE: Use only your mouse (click, drag, scroll) for navigation.\n"
                "Task completion will be detected automatically when you reach the target position."
            )

    def stop_experiment(self) -> None:
        """
        Stop the current experiment early.
        """
        self.reset_ui()
        self.instructions_label.setText("Experiment stopped. You can start again when ready.")
        self.task_header.setText("UPCOMING TASK:")
        self.task_header.setStyleSheet("font-weight: bold; color: #7fd1b9; font-size: 16px;")

        # Make sure upcoming task is still displayed
        if self.upcoming_task:
            input_method = "keyboard" if self.keyboard_radio.isChecked() else "mouse"
            self.task_label.setText(f"{self.upcoming_task['instruction']} using {input_method} only")
        else:
            self.task_label.setText("Not started")

        self.status_label.setText("")
        self.success_timer.stop()
        self.current_task = None

    def reset_ui(self) -> None:
        """
        Reset UI controls to initial state.
        """
        self.text_edit.setEnabled(False)
        self.keyboard_radio.setEnabled(True)
        self.mouse_radio.setEnabled(True)
        self.start_button.setText("Start Task")
        self.start_button.clicked.disconnect()
        self.start_button.clicked.connect(self.start_task)
        self.start_button.setEnabled(True)
        self.manual_complete_button.setVisible(False)

        # Highlight the upcoming task target if available
        if self.upcoming_task:
            self.highlight_target_goal()

    def mark_task_completed(self) -> None:
        """
        Mark the current task as completed and provide visual feedback.
        """
        if self.task_completed:
            return  # Prevent multiple completions

        self.task_completed = True

        # Provide visual feedback
        self.status_label.setText("✓ Task completed successfully!")
        self.status_label.setStyleSheet("font-weight: bold; color: #2ecc71; font-size: 16px;")

        # Disable text edit during transition
        self.text_edit.setEnabled(False)

        # Start a timer to move to the next task after a short delay
        self.success_timer.start(1000)  # 1 second delay

    def process_completed_task(self) -> None:
        """
        Process a completed task after the success feedback has been shown.
        """
        # Calculate time taken
        end_time = time.time()
        time_taken = end_time - self.start_time

        # Record results
        self.task_results[self.current_mode].append({
            "task_index": self.current_task_index,
            "task_description": self.current_task["instruction"],
            "time_taken": time_taken,
            "successful": True
        })

        # Update progress
        completed_tasks = len(self.task_results["keyboard"]) + len(self.task_results["mouse"])
        self.progress_bar.setValue(completed_tasks)

        # Reset status label styling
        self.status_label.setStyleSheet("font-weight: bold; color: #7fd1b9;")

        # Determine next steps
        if self.current_mode == "keyboard" and not any(
                result["task_index"] == self.current_task_index for result in self.task_results["mouse"]):
            # Switch to mouse for the same task
            self.mouse_radio.setChecked(True)
            self.keyboard_radio.setChecked(False)
            self.instructions_label.setText("Now try the same task using the mouse only.")
            self.status_label.setText("Ready for mouse task")
            self.upcoming_task = self.current_task  # Same task but with mouse
        else:
            # Move to next task
            self.current_task_index += 1

            # Reset radio buttons for next task
            self.keyboard_radio.setEnabled(True)
            self.mouse_radio.setEnabled(True)
            self.keyboard_radio.setChecked(True)

            # Check if all tasks are completed
            if self.current_task_index >= len(TASKS):
                self.end_experiment()
                return

            # Set up next task as upcoming
            self.upcoming_task = TASKS[self.current_task_index]
            self.status_label.setText("Ready for next task")

        # Reset UI for next task and show upcoming task
        self.reset_ui()

        # Update task display for upcoming task
        self.prepare_task_display()

    def manual_complete_task(self) -> None:
        """
        Manual override to complete a task if automatic detection is failing.
        """
        if not self.task_completed and self.current_task:
            self.mark_task_completed()

    def verify_task_completion(self) -> bool:
        """
        Verify if the current task was completed successfully.

        Returns:
            bool: True if task completed correctly, False otherwise
        """
        # Get current cursor
        cursor = self.text_edit.textCursor()

        # Check task type
        task = self.current_task

        if "select" in task and task["select"]:
            # Selection task
            if not cursor.hasSelection():
                return False

            selected_text = cursor.selectedText()

            if "target_text" in task:
                # Check specific text selection
                return selected_text == task["target_text"]
            elif "target_word" in task:
                # Check word selection at target line
                line_text = self.all_lines[task["target_line"]]
                words = line_text.split()
                if task["target_word"] < len(words):
                    return selected_text == words[task["target_word"]]
                return False
        else:
            # Cursor position task
            position = cursor.position()

            if task["target_line"] == -1:
                # End of document
                return position == len(self.text_edit.toPlainText())
            elif task["target_pos"] == -1:
                # End of line
                line_text = self.all_lines[task["target_line"]]
                # Calculate position at end of specified line
                lines_before = self.all_lines[:task["target_line"]]
                expected_pos = sum(len(line) + 1 for line in lines_before) + len(line_text)
                return position == expected_pos
            elif task["target_pos"] == 0:
                # Beginning of line or document
                if task["target_line"] == 0:
                    # Beginning of document
                    return position == 0
                else:
                    # Beginning of specified line
                    lines_before = self.all_lines[:task["target_line"]]
                    expected_pos = sum(len(line) + 1 for line in lines_before)
                    return position == expected_pos

        # Default fallback
        return False

    def on_text_changed(self) -> None:
        """
        Handle text changes in the text editor.
        """
        # For this experiment, we should prevent text modifications
        # We're only interested in navigation, not editing
        if self.text_edit.toPlainText() != SAMPLE_TEXT:
            self.text_edit.setPlainText(SAMPLE_TEXT)

            # Restore cursor position
            cursor = self.text_edit.textCursor()
            self.text_edit.setTextCursor(cursor)

    def on_cursor_changed(self) -> None:
        """
        Automatically detect task completion when cursor position changes.
        """
        # Only check if experiment is active and task not already completed
        if self.current_task and self.text_edit.isEnabled() and not self.task_completed:
            if self.verify_task_completion():
                # Mark task as completed
                self.mark_task_completed()

            # Show manual override button after 10 seconds if task not completed
            if time.time() - self.start_time > 10 and not self.task_completed:
                self.manual_complete_button.setVisible(True)

    def highlight_target_goal(self) -> None:
        """
        Highlight the target position or selection in the text editor to show users where to navigate.
        Uses a light highlight color that's visible but doesn't interfere with the task.
        """
        if not self.upcoming_task or not self.text_edit.isVisible():
            return

        # Create a document copy to work with
        doc = self.text_edit.document()
        cursor = QTextCursor(doc)

        # Calculate the target position based on task type
        task = self.upcoming_task

        try:
            # Reset any existing formats
            reset_cursor = QTextCursor(doc)
            reset_cursor.select(QTextCursor.Document)
            reset_format = QTextCharFormat()
            reset_format.setBackground(QColor("transparent"))
            reset_cursor.mergeCharFormat(reset_format)

            # Format for target highlighting - light blue color
            highlight_format = QTextCharFormat()
            highlight_format.setBackground(QColor(173, 216, 230, 80))  # Light blue with alpha

            if "select" in task and task["select"]:
                # Selection task
                if "target_text" in task:
                    # Find and highlight specific text
                    text_to_find = task["target_text"]
                    doc_text = doc.toPlainText()

                    # Find all occurrences of target text
                    start_pos = 0
                    while True:
                        start_pos = doc_text.find(text_to_find, start_pos)
                        if start_pos == -1:
                            break

                        # Check if this is in the correct line
                        if "target_line" in task:
                            # Calculate line number at this position
                            line_cursor = QTextCursor(doc)
                            line_cursor.setPosition(start_pos)
                            line_number = line_cursor.blockNumber()

                            if line_number == task["target_line"]:
                                # This is the correct occurrence
                                cursor.setPosition(start_pos)
                                cursor.setPosition(start_pos + len(text_to_find), QTextCursor.KeepAnchor)
                                cursor.mergeCharFormat(highlight_format)
                                break
                        else:
                            # No line specified, highlight all occurrences
                            cursor.setPosition(start_pos)
                            cursor.setPosition(start_pos + len(text_to_find), QTextCursor.KeepAnchor)
                            cursor.mergeCharFormat(highlight_format)

                        start_pos += len(text_to_find)

                elif "target_word" in task and "target_line" in task:
                    # Highlight specific word in a line
                    line_number = task["target_line"]
                    word_index = task["target_word"]

                    # Move to the beginning of the specified line
                    cursor.movePosition(QTextCursor.Start)
                    cursor.movePosition(QTextCursor.NextBlock, QTextCursor.MoveAnchor, line_number)

                    # Get line text
                    line_cursor = QTextCursor(cursor)
                    line_cursor.select(QTextCursor.LineUnderCursor)
                    line_text = line_cursor.selectedText()

                    # Split into words and find the target word
                    words = line_text.split()
                    if word_index < len(words):
                        target_word = words[word_index]

                        # Find position of this word within the line
                        word_pos = 0
                        for i in range(word_index):
                            word_pos = line_text.find(words[i], word_pos) + len(words[i])

                        word_pos = line_text.find(target_word, word_pos)
                        if word_pos != -1:
                            # Move cursor to beginning of line plus word offset
                            cursor.movePosition(QTextCursor.StartOfLine)
                            cursor.movePosition(QTextCursor.Right, QTextCursor.MoveAnchor, word_pos)
                            cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, len(target_word))
                            cursor.mergeCharFormat(highlight_format)
            else:
                # Cursor position task
                if task["target_line"] == -1:
                    # End of document
                    cursor.movePosition(QTextCursor.End)
                    cursor.movePosition(QTextCursor.Left, QTextCursor.KeepAnchor, 1)
                    cursor.mergeCharFormat(highlight_format)

                elif task["target_pos"] == -1:
                    # End of specified line
                    cursor.movePosition(QTextCursor.Start)
                    cursor.movePosition(QTextCursor.NextBlock, QTextCursor.MoveAnchor, task["target_line"])
                    cursor.movePosition(QTextCursor.EndOfLine)
                    cursor.movePosition(QTextCursor.Left, QTextCursor.KeepAnchor, 1)
                    cursor.mergeCharFormat(highlight_format)

                elif task["target_pos"] == 0:
                    # Beginning of line or document
                    if task["target_line"] == 0:
                        # Beginning of document
                        cursor.movePosition(QTextCursor.Start)
                        cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, 1)
                        cursor.mergeCharFormat(highlight_format)
                    else:
                        # Beginning of specified line
                        cursor.movePosition(QTextCursor.Start)
                        cursor.movePosition(QTextCursor.NextBlock, QTextCursor.MoveAnchor, task["target_line"])
                        cursor.movePosition(QTextCursor.StartOfLine)
                        cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, 1)
                        cursor.mergeCharFormat(highlight_format)
        except Exception as e:
            # If any error occurs during highlighting, just skip it - not critical
            pass

        self.text_edit.setDocument(doc)

    def clear_highlights(self) -> None:
        """
        Clear any existing highlights from the text editor.
        """
        doc = self.text_edit.document()
        cursor = QTextCursor(doc)
        cursor.select(QTextCursor.Document)

        format = QTextCharFormat()
        format.setBackground(QColor("transparent"))

        cursor.mergeCharFormat(format)
        self.text_edit.setDocument(doc)

    def end_experiment(self) -> None:
        """
        End the experiment and display results.
        """
        self.start_button.setEnabled(True)
        self.start_button.setText("Restart Experiment")
        self.start_button.clicked.disconnect()
        self.start_button.clicked.connect(self.restart_experiment)

        # Hide unnecessary UI elements to make more room for graphs
        self.text_edit.setVisible(False)
        self.task_frame.setVisible(False)  # Hide task display
        self.input_group.setVisible(False)  # Hide input method selection

        # Show results graph
        self.results_graph.setVisible(True)

        # Calculate average times
        keyboard_times = [result["time_taken"] for result in self.task_results["keyboard"] if result["successful"]]
        mouse_times = [result["time_taken"] for result in self.task_results["mouse"] if result["successful"]]

        avg_keyboard = sum(keyboard_times) / len(keyboard_times) if keyboard_times else 0
        avg_mouse = sum(mouse_times) / len(mouse_times) if mouse_times else 0

        # Count successful tasks
        keyboard_success = sum(1 for result in self.task_results["keyboard"] if result["successful"])
        mouse_success = sum(1 for result in self.task_results["mouse"] if result["successful"])

        # Generate results text (saved but not displayed)
        results_text = (
            f"EXPERIMENT RESULTS:\n\n"
            f"Keyboard Navigation:\n"
            f"- Average time: {avg_keyboard:.2f} seconds\n"
            f"- Successful tasks: {keyboard_success}/{len(TASKS)}\n\n"
            f"Mouse Navigation:\n"
            f"- Average time: {avg_mouse:.2f} seconds\n"
            f"- Successful tasks: {mouse_success}/{len(TASKS)}\n\n"
        )

        # Add task-specific results
        results_text += "Task Comparisons:\n"
        task_comparisons = []
        for i in range(len(TASKS)):
            kb_result = next((r for r in self.task_results["keyboard"] if r["task_index"] == i), None)
            mouse_result = next((r for r in self.task_results["mouse"] if r["task_index"] == i), None)

            if kb_result and mouse_result and kb_result["successful"] and mouse_result["successful"]:
                faster = "Keyboard" if kb_result["time_taken"] < mouse_result["time_taken"] else "Mouse"
                diff = abs(kb_result["time_taken"] - mouse_result["time_taken"])
                results_text += f"Task {i + 1}: {faster} faster by {diff:.2f}s\n"
                task_comparisons.append({
                    "task_index": i,
                    "task_name": f"Task {i + 1}",
                    "task_description": TASKS[i]["instruction"],
                    "keyboard_time": kb_result["time_taken"],
                    "mouse_time": mouse_result["time_taken"],
                    "faster": faster,
                    "diff": diff
                })

        # Store results text but don't display
        self.results_label.setText(results_text)

        # Update instructions
        self.instructions_label.setText(
            "Navigation experiment complete! See performance graphs below. Click 'Restart Experiment' to run again.")

        # Generate and display graphs
        self.generate_performance_graphs(task_comparisons)

    def generate_performance_graphs(self, task_comparisons: list) -> None:
        """
        Generate performance comparison graphs between keyboard and mouse navigation.

        Args:
            task_comparisons: List of dictionaries containing comparison data for each task
        """
        if not task_comparisons:
            return

        # Clear existing plots
        for ax in self.axes:
            ax.clear()

        # Extract data for plotting
        task_names = [comp["task_name"] for comp in task_comparisons]
        task_descriptions = [comp["task_description"] for comp in task_comparisons]
        keyboard_times = [comp["keyboard_time"] for comp in task_comparisons]
        mouse_times = [comp["mouse_time"] for comp in task_comparisons]

        # Set x positions for bars
        x = np.arange(len(task_names))
        width = 0.35

        # Plot 1: Bar chart comparing completion times
        bar1 = self.axes[0].bar(x - width / 2, keyboard_times, width, label='Keyboard', color='#3498db')
        bar2 = self.axes[0].bar(x + width / 2, mouse_times, width, label='Mouse', color='#e74c3c')

        # Add labels and title
        self.axes[0].set_title('Task Completion Time Comparison', fontsize=14)
        self.axes[0].set_ylabel('Time (seconds)', fontsize=12)
        self.axes[0].set_xticks(x)
        self.axes[0].set_xticklabels(task_names, fontsize=10)
        self.axes[0].legend(fontsize=12)

        # Add value labels on top of bars
        for bars in [bar1, bar2]:
            for bar in bars:
                height = bar.get_height()
                self.axes[0].annotate(f'{height:.2f}s',
                                      xy=(bar.get_x() + bar.get_width() / 2, height),
                                      xytext=(0, 3),  # 3 points vertical offset
                                      textcoords="offset points",
                                      ha='center', va='bottom',
                                      color='white', fontsize=9)

        # Plot 2: Efficiency ratio (Keyboard time / Mouse time)
        # Values below 1 mean keyboard is faster, above 1 mean mouse is faster
        efficiency_ratios = [k / m if m > 0 else 0 for k, m in zip(keyboard_times, mouse_times)]

        # Create colors based on which is faster
        colors = ['#3498db' if ratio < 1 else '#e74c3c' for ratio in efficiency_ratios]

        bars = self.axes[1].bar(x, efficiency_ratios, width, color=colors)
        self.axes[1].axhline(y=1.0, color='#f3f3f3', linestyle='--', alpha=0.7)

        # Add labels and title
        self.axes[1].set_title('Navigation Efficiency Ratio (Keyboard/Mouse)', fontsize=14)
        self.axes[1].set_ylabel('Ratio', fontsize=12)
        self.axes[1].set_xticks(x)
        self.axes[1].set_xticklabels(task_names, fontsize=10)

        # Add horizontal reference line at y=1 (equal efficiency)
        self.axes[1].text(len(task_names) - 1, 1.05, 'Equal Efficiency',
                          color='#f3f3f3', ha='right', va='bottom', fontsize=10)

        # Add annotations for which method is better
        for i, ratio in enumerate(efficiency_ratios):
            if ratio < 0.9:  # Keyboard significantly faster
                label = f"{ratio:.2f}x\nKeyboard faster"
            elif ratio > 1.1:  # Mouse significantly faster
                label = f"{ratio:.2f}x\nMouse faster"
            else:  # Similar performance
                label = f"{ratio:.2f}x\nSimilar"

            self.axes[1].annotate(label,
                                  xy=(x[i], ratio),
                                  xytext=(0, 5 if ratio < 1 else -25),
                                  textcoords="offset points",
                                  ha='center', va='bottom' if ratio < 1 else 'top',
                                  color='white', fontsize=9)

        # Adjust layout and display
        self.canvas.figure.tight_layout()
        self.canvas.draw()

    def restart_experiment(self) -> None:
        """
        Restart the experiment from the beginning.
        """
        # Reset all experiment data
        self.current_task_index = 0
        self.current_task = None
        self.upcoming_task = TASKS[0] if TASKS else None
        self.task_results = {
            "keyboard": [],
            "mouse": []
        }
        self.progress_bar.setValue(0)

        # State resets
        self.task_completed = False
        self.current_mode = None
        self.success_timer.stop()  # Ensure timer is stopped

        # Clear any text highlights
        self.clear_highlights()

        # Reset text content to original
        self.text_edit.setPlainText(SAMPLE_TEXT)

        # Ensure keyboard is selected by default
        self.keyboard_radio.setChecked(True)
        self.mouse_radio.setChecked(False)

        # Reset UI
        self.reset_ui()
        self.results_label.setText("")

        # Hide results graph and show experiment UI elements
        self.results_graph.setVisible(False)
        self.text_edit.setVisible(True)
        self.task_frame.setVisible(True)
        self.input_group.setVisible(True)

        # Show preparation for first task
        self.prepare_task_display()

        self.instructions_label.setText(
            "Experiment restarted! Review the first task, then click 'Start Task' when ready."
        )