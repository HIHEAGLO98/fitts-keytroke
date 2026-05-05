from __future__ import annotations
import time
import random
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton,
                               QTextEdit, QHBoxLayout, QProgressBar, QApplication,
                               QMessageBox)
from PySide6.QtCore import Qt, QTimer, Signal, QObject
from PySide6.QtGui import QKeyEvent, QTextCharFormat, QColor, QFont, QTextCursor
from constants import t

# Short, simple text for typing test
SAMPLE_TEXT = """The quick brown fox jumps over the lazy dog. 
This sentence contains all letters of the alphabet. 
Reading improves vocabulary and critical thinking.
Good typists maintain steady rhythm and accuracy."""


class BeepSignals(QObject):
    """Signal class for beep events"""
    beep_played = Signal()


class CognitiveLoadExperiment(QWidget):
    """
    Screen to conduct the Cognitive Load Impact on Typing Performance experiment.
    """

    def __init__(self, main_window: object) -> None:
        super().__init__()
        self.main_window = main_window
        self.stats_screen = None
        self.beep_signals = BeepSignals()

        # Experiment data
        self.experiment_active = False
        self.experiment_paused = False
        self.current_phase = "none"  # none, baseline, break, dual_task, complete
        self.phase_start_time = 0
        self.break_start_time = 0
        self.break_duration = 5  # 5 seconds break between phases
        self.key_presses = []
        self.beep_times = []
        self.beep_response_times = []
        self.beep_timer_remaining = 0  # Track remaining time when paused
        self.target_text = SAMPLE_TEXT
        self.current_text = ""  # Store current text for error calculation
        self.min_beeps = 3  # Minimum number of beeps in dual task phase
        self.beep_response_window = 2.0  # Time window in seconds to respond to a beep

        # Timers
        self.beep_timer = QTimer()
        self.beep_timer.timeout.connect(self.play_beep)

        self.break_timer = QTimer()
        self.break_timer.timeout.connect(self.update_break_countdown)
        self.break_timer.setInterval(1000)  # Update every second

        # Results
        self.baseline_results = {
            "wpm": 0,
            "error_rate": 0,
            "keystroke_times": []
        }
        self.dual_task_results = {
            "wpm": 0,
            "error_rate": 0,
            "keystroke_times": [],
            "beep_response_times": []
        }

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout()

        # Instructions
        self.instructions_label = QLabel(
            "This experiment measures typing performance under cognitive load.\n"
            "You'll type the same text twice: once at your normal pace, and once while "
            "responding to beeps by pressing the Enter key."
        )
        self.instructions_label.setAlignment(Qt.AlignCenter)
        self.instructions_label.setWordWrap(True)
        layout.addWidget(self.instructions_label)

        # Phase indicator
        self.phase_label = QLabel("Ready to start")
        self.phase_label.setAlignment(Qt.AlignCenter)
        self.phase_label.setStyleSheet("font-weight: bold; color: #0066cc;")
        layout.addWidget(self.phase_label)

        # Sample text display
        self.sample_text_label = QLabel(SAMPLE_TEXT)
        self.sample_text_label.setWordWrap(True)
        self.sample_text_label.setFrameStyle(1)
        self.sample_text_label.setStyleSheet(
            "background-color: #2c3e50; color: white; padding: 10px; border-radius: 4px;")
        layout.addWidget(self.sample_text_label)

        # Text input area
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Type the text shown above here...")
        self.text_input.setEnabled(False)
        self.text_input.textChanged.connect(self.on_text_changed)
        self.text_input.keyPressEvent = self.custom_key_press_event
        # Set text color to white for better visibility on dark background
        self.text_input.setStyleSheet("background-color: #2c3e50; color: white; border-radius: 4px; padding: 8px;")
        layout.addWidget(self.text_input)

        # Progress indicator
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Button layout
        button_layout = QHBoxLayout()

        # Start/Pause button
        self.start_button = QPushButton("Start Experiment")
        self.start_button.clicked.connect(self.toggle_experiment)
        button_layout.addWidget(self.start_button)

        # Reset button (hidden initially)
        self.reset_button = QPushButton("Reset Experiment")
        self.reset_button.clicked.connect(self.reset_experiment)
        self.reset_button.setVisible(False)
        button_layout.addWidget(self.reset_button)

        # Back button
        self.back_button = QPushButton("Back to Keystroke Menu")
        self.back_button.setObjectName("SmallNavButton")
        self.back_button.clicked.connect(self.return_to_menu)
        button_layout.addWidget(self.back_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)
        self.refresh_ui()

    def refresh_ui(self) -> None:
        self.back_button.setText(t("back_keystroke_menu"))

    def return_to_menu(self) -> None:
        """Return to keystroke menu after confirming if experiment is active"""
        if self.experiment_active and not self.experiment_paused:
            reply = QMessageBox.question(self, 'Confirm Exit',
                                         'Experiment is still running. Are you sure you want to exit?',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return
            self.toggle_experiment()  # Pause the experiment

        # Return to keystroke menu
        self.main_window.switch_screen(4)

    def set_stats_screen(self, stats_screen: object) -> None:
        """
        Set the stats screen to display results after the experiment.

        Args:
            stats_screen: The screen instance to display the statistics.
        """
        self.stats_screen = stats_screen

    def toggle_experiment(self) -> None:
        """Toggle between start/pause/resume experiment"""
        if not self.experiment_active:
            self.start_experiment()
        elif self.experiment_paused:
            self.resume_experiment()
        else:
            self.pause_experiment()

    def start_experiment(self) -> None:
        """Initialize experiment data and start with baseline phase"""
        self.experiment_active = True
        self.experiment_paused = False
        self.current_phase = "baseline"
        self.phase_start_time = time.time()

        # Reset data
        self.key_presses = []
        self.beep_times = []
        self.beep_response_times = []
        self.current_text = ""
        self.text_input.clear()
        self.text_input.setEnabled(True)
        self.text_input.setFocus()
        self.progress_bar.setValue(0)

        # Update UI
        self.start_button.setText("Pause Experiment")
        self.reset_button.setVisible(True)
        self.phase_label.setText("Phase: Baseline - Type text at your normal pace")
        self.instructions_label.setText("Type the text above as accurately as possible.")

    def pause_experiment(self) -> None:
        """Pause the current experiment"""
        self.experiment_paused = True
        self.start_button.setText("Resume Experiment")

        # Disable text input during pause
        self.text_input.setEnabled(False)

        # Pause beep timer if in dual-task phase
        if self.current_phase == "dual_task":
            if self.beep_timer.isActive():
                self.beep_timer_remaining = self.beep_timer.remainingTime()
                self.beep_timer.stop()

        # Pause break timer if in break phase
        if self.current_phase == "break":
            self.break_timer.stop()

    def resume_experiment(self) -> None:
        """Resume the paused experiment"""
        self.experiment_paused = False
        self.start_button.setText("Pause Experiment")

        # Re-enable text input
        self.text_input.setEnabled(True)
        self.text_input.setFocus()

        # Resume beep timer if in dual-task phase
        if self.current_phase == "dual_task":
            if self.beep_timer_remaining > 0:
                self.beep_timer.start(self.beep_timer_remaining)
                self.beep_timer_remaining = 0
            else:
                self.schedule_next_beep()

        # Resume break timer if in break phase
        if self.current_phase == "break":
            self.break_timer.start()

    def start_break(self) -> None:
        """Start the break between phases"""
        # Confirm with user before proceeding
        reply = QMessageBox.information(self, "Phase Complete",
                                        "Baseline phase completed! Take a short break before starting the dual-task phase.",
                                        QMessageBox.Ok)

        self.current_phase = "break"
        self.break_start_time = time.time()
        self.text_input.clear()
        self.text_input.setEnabled(False)
        self.progress_bar.setValue(0)

        # Update UI
        self.phase_label.setText(f"Break: {self.break_duration} seconds remaining")
        self.instructions_label.setText("Take a short break. The dual-task phase will begin soon.\n"
                                        "In the next phase, you'll type the same text while responding to beeps by pressing Enter.")

        # Start break timer
        self.break_timer.start()

    def update_break_countdown(self) -> None:
        """Update the break countdown timer"""
        elapsed = time.time() - self.break_start_time
        remaining = max(0, self.break_duration - elapsed)

        if remaining <= 0:
            # Break is over, start dual-task phase
            self.break_timer.stop()
            self.start_dual_task_phase()
        else:
            # Update countdown
            self.phase_label.setText(f"Break: {int(remaining)} seconds remaining")

    def start_dual_task_phase(self) -> None:
        """Start the dual-task phase of the experiment"""
        # Confirm with user before proceeding
        reply = QMessageBox.information(self, "Dual-Task Phase",
                                        "The dual-task phase will now begin. Type the text while responding to beeps by pressing Enter.",
                                        QMessageBox.Ok)

        self.current_phase = "dual_task"
        self.phase_start_time = time.time()

        # Reset data for this phase
        self.key_presses = []
        self.beep_times = []
        self.beep_response_times = []
        self.current_text = ""
        self.text_input.clear()
        self.text_input.setEnabled(True)
        self.text_input.setFocus()
        self.progress_bar.setValue(0)

        # Update UI
        self.phase_label.setText("Phase: Dual-Task - Type text while responding to beeps")
        self.instructions_label.setText(
            "Type the text above as accurately as possible.\n"
            "Press the ENTER key when you hear a beep."
        )

        # Start beep timer
        self.schedule_next_beep()

    def custom_key_press_event(self, event: QKeyEvent) -> None:
        """
        Custom key press event handler to track typing metrics and handle beep responses.
        """
        # Record timestamp for keystroke analysis
        timestamp = time.time()
        key = event.text()
        key_code = event.key()

        # Check if Enter key was pressed for beep response
        if key_code == Qt.Key_Return or key_code == Qt.Key_Enter:
            if self.current_phase == "dual_task":
                # Process as beep response, and check if it was actually used for a beep
                beep_handled = self.process_beep_response(timestamp)
                if beep_handled:
                    return  # Skip default handling only if we actually responded to a beep

        # Record key press with timestamp (excluding Enter for beep responses when they actually respond to a beep)
        self.key_presses.append({
            "key": key,
            "timestamp": timestamp,
            "is_backspace": key_code == Qt.Key_Backspace
        })

        # Pass the event to the default handler for normal typing
        QTextEdit.keyPressEvent(self.text_input, event)

        # Update progress and check for errors
        self.check_for_errors()
        self.update_progress()

    def process_beep_response(self, timestamp: float) -> bool:
        """
        Process a beep response from the user

        Args:
            timestamp: The timestamp when the key was pressed

        Returns:
            bool: True if a beep was successfully handled, False otherwise
        """
        # Check if there was a recent beep that hasn't been responded to
        most_recent_beep = None
        most_recent_time = 0

        for beep_time in self.beep_times:
            # Check if this beep has already been responded to
            if beep_time not in [b["beep_time"] for b in self.beep_response_times]:
                # Check if the response is within the valid window (e.g., 2 seconds)
                response_time = timestamp - beep_time
                if response_time <= self.beep_response_window and beep_time > most_recent_time:
                    most_recent_beep = beep_time
                    most_recent_time = beep_time

        if most_recent_beep:
            response_time = timestamp - most_recent_beep
            self.beep_response_times.append({
                "beep_time": most_recent_beep,
                "response_time": response_time
            })

            # Provide visual feedback
            self.instructions_label.setText(
                f"Beep response recorded! ({response_time * 1000:.0f}ms)\n"
                "Continue typing and watch for more beeps."
            )
            return True  # Beep was handled
        else:
            # No valid beep was found - allow normal Enter key behavior
            return False  # No beep was handled

    def check_for_errors(self) -> None:
        """Check for typing errors and highlight them line by line"""
        current_text = self.text_input.toPlainText()
        self.current_text = current_text  # Store for error calculation

        if not current_text:  # Skip if text is empty
            return

        # Create a cursor to manipulate formatting
        cursor = self.text_input.textCursor()

        # Save current position
        current_position = self.text_input.textCursor().position()

        # Reset all formatting to default white text
        format_cursor = QTextCursor(self.text_input.document())
        format_cursor.select(QTextCursor.Document)
        char_format = QTextCharFormat()
        char_format.setForeground(QColor("white"))  # Set default text color to white
        format_cursor.mergeCharFormat(char_format)

        # Split both texts into lines
        current_lines = current_text.splitlines()
        target_lines = self.target_text.splitlines()

        # Print for debugging
        # print(f"Current: {current_lines}")
        # print(f"Target: {target_lines}")

        # Process each line that exists in the user's input
        doc = self.text_input.document()
        position_in_doc = 0

        for line_idx, current_line in enumerate(current_lines):
            # Get corresponding target line if it exists
            target_line = target_lines[line_idx] if line_idx < len(target_lines) else ""

            # Compare characters in this line
            for char_idx, (typed_char, target_char) in enumerate(zip(current_line, target_line)):
                if typed_char != target_char:
                    # Calculate position in the document for this character
                    error_pos = position_in_doc + char_idx

                    # Highlight the error
                    error_cursor = QTextCursor(doc)
                    error_cursor.setPosition(error_pos)
                    error_cursor.setPosition(error_pos + 1, QTextCursor.KeepAnchor)
                    error_format = QTextCharFormat()
                    error_format.setForeground(QColor("red"))
                    error_format.setUnderlineStyle(QTextCharFormat.WaveUnderline)
                    error_cursor.mergeCharFormat(error_format)

            # Mark any excess characters in this line as errors
            if len(current_line) > len(target_line):
                for i in range(len(target_line), len(current_line)):
                    error_pos = position_in_doc + i

                    error_cursor = QTextCursor(doc)
                    error_cursor.setPosition(error_pos)
                    error_cursor.setPosition(error_pos + 1, QTextCursor.KeepAnchor)
                    error_format = QTextCharFormat()
                    error_format.setForeground(QColor("red"))
                    error_format.setUnderlineStyle(QTextCharFormat.WaveUnderline)
                    error_cursor.mergeCharFormat(error_format)

            # Update position for next line (add line length + 1 for the newline character)
            position_in_doc += len(current_line) + 1

            # When we reach the end of the buffer, break out
            if position_in_doc >= len(current_text):
                break

        # Restore cursor position
        cursor.setPosition(current_position)
        self.text_input.setTextCursor(cursor)

    def text_to_plain_string(self, text: str) -> str:
        """
        Convert text to a plain string with all whitespace normalized for comparison.
        Removes all line breaks and normalizes spaces.

        Args:
            text: The text to convert

        Returns:
            str: Text with all line breaks removed and whitespace normalized
        """
        # First replace all types of line breaks with a space
        normalized = text.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ')

        # Then normalize multiple spaces to a single space
        while '  ' in normalized:
            normalized = normalized.replace('  ', ' ')

        return normalized

    def on_text_changed(self) -> None:
        """
        Handle text changes in the input field and check for completion.
        """
        current_text = self.text_input.toPlainText()
        self.current_text = current_text  # Store for error calculation

        # Limit text length to prevent performance issues with very long input
        if len(current_text) > len(self.target_text) * 1.5:
            # Trim excess text
            self.text_input.setPlainText(current_text[:int(len(self.target_text) * 1.5)])
            cursor = self.text_input.textCursor()
            cursor.setPosition(int(len(self.target_text) * 1.5))
            self.text_input.setTextCursor(cursor)

            # Warn user about limit
            self.instructions_label.setText(
                "Text length limited. Focus on typing the sample text accurately."
            )
            QApplication.beep()  # Provide audible feedback

        # Update progress
        self.update_progress()

        # Check if typing task is complete based on a more robust method
        if self.is_typing_complete(current_text):
            self.complete_current_phase()

    def is_typing_complete(self, current_text: str) -> bool:
        """
        Determine if the typing task is complete using a line-by-line comparison.

        Args:
            current_text: The text currently in the input field

        Returns:
            bool: True if the typing task is considered complete, False otherwise
        """
        # First check: must have a reasonable amount of text
        if len(current_text) < len(self.target_text) * 0.8:
            return False

        # Compare the last line for completion
        current_lines = current_text.splitlines()
        target_lines = self.target_text.splitlines()

        # Must have at least one line
        if not current_lines:
            return False

        # Check if we reached the last line of the target text
        if len(current_lines) < len(target_lines):
            return False

        # Get the last line of both texts
        last_current_line = current_lines[-1]
        last_target_line = target_lines[-1]

        # Check if the last line is at least 80% complete
        min_length = 0.8 * len(last_target_line)
        if len(last_current_line) < min_length:
            return False

        # Check the similarity of the last lines
        matching_chars = sum(1 for a, b in zip(last_current_line, last_target_line) if a == b)
        last_line_similarity = matching_chars / len(last_target_line) if len(last_target_line) > 0 else 0

        # Consider complete if last line is at least 80% similar and has sufficient length
        return last_line_similarity >= 0.8

    def update_progress(self) -> None:
        """
        Update the progress bar based on text completion.
        """
        current_text = self.text_input.toPlainText()
        progress = min(100, int((len(current_text) / len(self.target_text)) * 100))
        self.progress_bar.setValue(progress)

    def play_beep(self) -> None:
        """
        Play a beep sound and record the time.
        """
        # Use the system beep function
        QApplication.beep()

        beep_time = time.time()
        self.beep_times.append(beep_time)
        self.beep_signals.beep_played.emit()

        # Schedule next beep
        self.schedule_next_beep()

    def schedule_next_beep(self) -> None:
        """
        Schedule the next random beep.
        """
        # Only schedule if experiment is active and not paused
        if self.experiment_active and not self.experiment_paused and self.current_phase == "dual_task":
            # Random interval between 4-8 seconds
            interval = random.randint(4000, 8000)
            self.beep_timer.start(interval)
            self.beep_timer_remaining = interval

    def complete_current_phase(self) -> None:
        """
        Complete the current phase and proceed to the next phase or end experiment.
        """
        end_time = time.time()
        phase_duration = end_time - self.phase_start_time

        # Stop timers
        self.beep_timer.stop()

        # Calculate results
        results = self.calculate_results(phase_duration)

        # Store results based on current phase
        if self.current_phase == "baseline":
            self.baseline_results = results

            # Move to break between phases
            self.start_break()

        elif self.current_phase == "dual_task":
            self.dual_task_results = results

            # Check if we have enough beep responses
            if len(self.beep_response_times) < self.min_beeps:
                # Not enough beeps, show warning and continue
                reply = QMessageBox.warning(self, "Insufficient Beep Responses",
                                            f"You only responded to {len(self.beep_response_times)} beeps. "
                                            f"At least {self.min_beeps} responses are recommended for valid results.\n\n"
                                            "Would you like to continue and see the results anyway?",
                                            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

                if reply == QMessageBox.No:
                    # Restart dual task phase
                    self.start_dual_task_phase()
                    return

            # Extract response times
            self.dual_task_results["beep_response_times"] = [r["response_time"] for r in self.beep_response_times]

            # End experiment
            self.end_experiment()

    def calculate_results(self, duration: float) -> dict:
        """
        Calculate performance metrics from the experiment.

        Args:
            duration: Duration of the phase in seconds

        Returns:
            dict: Dictionary with WPM, error rate, and keystroke timing data.
        """
        duration_minutes = duration / 60.0

        # Calculate error rate using line-by-line comparison
        current_lines = self.current_text.splitlines()
        target_lines = self.target_text.splitlines()

        total_chars = 0
        error_count = 0

        # Process each line
        for line_idx, current_line in enumerate(current_lines):
            # Get corresponding target line if it exists
            target_line = target_lines[line_idx] if line_idx < len(target_lines) else ""

            # Compare characters in this line
            for char_idx, (typed_char, target_char) in enumerate(zip(current_line, target_line)):
                total_chars += 1
                if typed_char != target_char:
                    error_count += 1

            # Count extra or missing characters
            total_chars += abs(len(current_line) - len(target_line))
            error_count += abs(len(current_line) - len(target_line))

        # Add error count for any missing lines
        if len(target_lines) > len(current_lines):
            for i in range(len(current_lines), len(target_lines)):
                line_len = len(target_lines[i])
                total_chars += line_len
                error_count += line_len

        error_rate = error_count / total_chars if total_chars > 0 else 0

        # Calculate WPM (Words Per Minute) based on actual typed text
        char_count = len(self.current_text)
        word_count = char_count / 5.0  # Standard definition: 5 characters = 1 word
        wpm = word_count / duration_minutes if duration_minutes > 0 else 0

        # Calculate keystroke timing metrics with improved handling of backspaces
        keystroke_times = []
        prev_time = None
        skip_next = False

        for i, kp in enumerate(self.key_presses):
            if skip_next:
                skip_next = False
                continue

            if kp["is_backspace"]:
                # Skip the next timing calculation as backspace disrupts normal flow
                skip_next = True
            else:
                if prev_time is not None:
                    # Only include reasonable timings (e.g., under 2 seconds)
                    interval = kp["timestamp"] - prev_time
                    if interval < 2.0:  # Reasonable typing interval
                        keystroke_times.append(interval)
                prev_time = kp["timestamp"]

        return {
            "wpm": wpm,
            "error_rate": error_rate,
            "keystroke_times": keystroke_times
        }

    def end_experiment(self) -> None:
        """
        End the experiment and display final results.
        """
        self.current_phase = "complete"
        self.experiment_active = False
        self.text_input.setEnabled(False)

        # Update UI
        self.start_button.setText("Start New Experiment")
        self.phase_label.setText("Experiment Complete")

        # Display results
        self.display_final_results()

    def display_final_results(self) -> None:
        """
        Display the final results comparing baseline and dual-task performance.
        """
        baseline_wpm = self.baseline_results["wpm"]
        dual_task_wpm = self.dual_task_results["wpm"]
        wpm_change = ((dual_task_wpm - baseline_wpm) / baseline_wpm) * 100 if baseline_wpm > 0 else 0

        baseline_error = self.baseline_results["error_rate"]
        dual_task_error = self.dual_task_results["error_rate"]
        error_change = ((dual_task_error - baseline_error) / baseline_error) * 100 if baseline_error > 0 else 0

        # Calculate average and median response times
        response_times = self.dual_task_results["beep_response_times"]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0

        # Calculate median (middle value)
        median_response_time = 0
        if response_times:
            sorted_times = sorted(response_times)
            mid = len(sorted_times) // 2
            if len(sorted_times) % 2 == 0:
                median_response_time = (sorted_times[mid - 1] + sorted_times[mid]) / 2
            else:
                median_response_time = sorted_times[mid]

        # Calculate average keystroke interval for both phases
        baseline_intervals = self.baseline_results["keystroke_times"]
        dual_task_intervals = self.dual_task_results["keystroke_times"]

        avg_baseline_interval = sum(baseline_intervals) / len(baseline_intervals) if baseline_intervals else 0
        avg_dual_task_interval = sum(dual_task_intervals) / len(dual_task_intervals) if dual_task_intervals else 0
        interval_change = ((
                                       avg_dual_task_interval - avg_baseline_interval) / avg_baseline_interval) * 100 if avg_baseline_interval > 0 else 0

        results_text = (
            f"EXPERIMENT RESULTS:\n\n"
            f"Baseline WPM: {baseline_wpm:.1f}\n"
            f"Dual-Task WPM: {dual_task_wpm:.1f}\n"
            f"WPM Change: {wpm_change:.1f}% {'slower' if wpm_change < 0 else 'faster'}\n\n"
            f"Baseline Error Rate: {baseline_error * 100:.1f}%\n"
            f"Dual-Task Error Rate: {dual_task_error * 100:.1f}%\n"
            f"Error Rate Change: {error_change:.1f}% {'worse' if error_change > 0 else 'better'}\n\n"
            f"Average Keystroke Interval (Baseline): {avg_baseline_interval * 1000:.0f}ms\n"
            f"Average Keystroke Interval (Dual-Task): {avg_dual_task_interval * 1000:.0f}ms\n"
            f"Interval Change: {interval_change:.1f}% {'slower' if interval_change > 0 else 'faster'}\n\n"
            f"Average Beep Response Time: {avg_response_time * 1000:.0f}ms\n"
            f"Median Beep Response Time: {median_response_time * 1000:.0f}ms\n"
            f"Number of Beeps: {len(self.beep_times)}\n"
            f"Number of Responses: {len(self.dual_task_results['beep_response_times'])}\n"
        )

        self.instructions_label.setText(results_text)

        # Show reset button
        self.reset_button.setVisible(True)
        self.start_button.setVisible(False)

    def reset_experiment(self) -> None:
        """Reset the experiment to initial state"""
        # Reset all data
        self.experiment_active = False
        self.experiment_paused = False
        self.current_phase = "none"
        self.key_presses = []
        self.beep_times = []
        self.beep_response_times = []
        self.current_text = ""

        # Reset results
        self.baseline_results = {
            "wpm": 0,
            "error_rate": 0,
            "keystroke_times": []
        }
        self.dual_task_results = {
            "wpm": 0,
            "error_rate": 0,
            "keystroke_times": [],
            "beep_response_times": []
        }

        # Reset UI
        self.text_input.clear()
        self.text_input.setEnabled(False)
        self.progress_bar.setValue(0)
        self.phase_label.setText("Ready to start")
        self.instructions_label.setText(
            "This experiment measures typing performance under cognitive load.\n"
            "You'll type the same text twice: once at your normal pace, and once while "
            "responding to beeps by pressing the Enter key."
        )

        # Reset buttons
        self.start_button.setText("Start Experiment")
        self.start_button.setVisible(True)
        self.reset_button.setVisible(False)