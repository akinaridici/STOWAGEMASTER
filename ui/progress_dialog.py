"""Dialog showing optimization progress with cancellation support"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                           QProgressBar, QPushButton, QTextEdit,
                           QDialogButtonBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QTextCursor
from typing import Optional, Callable

from core.progress_reporter import ProgressStage


class OptimizationProgressDialog(QDialog):
    """Dialog showing optimization progress with cancellation support"""
    
    def __init__(self, parent=None):
        """Initialize progress dialog
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self._cancelled = False
        self._cancellation_callback: Optional[Callable[[], None]] = None
        self.setWindowTitle("Optimizasyon İlerlemesi")
        self.setFixedSize(600, 400)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint)
        
        # Prevent closing with ESC key during critical operations
        self._escape_key_disabled = False
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Title
        title = QLabel("Yükleme Planı Oluşturuluyor...")
        title_font = QFont("Arial", 12, QFont.Weight.Bold)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Current stage label
        self.stage_label = QLabel("Hazırlanıyor...")
        stage_font = QFont("Arial", 10)
        self.stage_label.setFont(stage_font)
        self.stage_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.stage_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        layout.addWidget(self.progress_bar)
        
        # Details text
        self.details_text = QTextEdit()
        self.details_text.setMaximumHeight(120)
        self.details_text.setReadOnly(True)
        self.details_text.setFont(QFont("Consolas", 9))
        
        # Set dark/light theme based on system palette
        self._apply_theme()
        
        layout.addWidget(self.details_text)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.cancel_btn = QPushButton("İptal")
        self.cancel_btn.setMinimumHeight(30)
        self.cancel_btn.clicked.connect(self.cancel)
        button_layout.addWidget(self.cancel_btn)
        
        button_layout.addStretch()
        
        # Minimize button (optional)
        self.minimize_btn = QPushButton("Küçült")
        self.minimize_btn.setMinimumHeight(30)
        self.minimize_btn.clicked.connect(self.showMinimized)
        button_layout.addWidget(self.minimize_btn)
        
        layout.addLayout(button_layout)
        
        # Status label
        self.status_label = QLabel("")
        status_font = QFont("Arial", 9)
        self.status_label.setFont(status_font)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Set layout
        self.setLayout(layout)
    
    def _apply_theme(self):
        """Apply theme based on system palette"""
        from PyQt6.QtWidgets import QApplication
        
        palette = QApplication.palette()
        is_dark = palette.color(palette.ColorRole.Window).lightness() < 128
        
        if is_dark:
            # Dark theme
            self.setStyleSheet("""
                QDialog {
                    background-color: #2b2b2b;
                    color: #ffffff;
                    border: 1px solid #444444;
                    border-radius: 6px;
                }
                QLabel {
                    color: #ffffff;
                    background-color: transparent;
                }
                QProgressBar {
                    border: 1px solid #555555;
                    border-radius: 3px;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #4CAF50;
                    border-radius: 2px;
                }
                QTextEdit {
                    background-color: #1e1e1e;
                    color: #e0e0e0;
                    border: 1px solid #444444;
                    border-radius: 4px;
                    padding: 5px;
                }
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 5px 15px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
                QPushButton:pressed {
                    background-color: #3d8b40;
                }
            """)
        else:
            # Light theme
            self.setStyleSheet("""
                QDialog {
                    background-color: #ffffff;
                    color: #333333;
                    border: 1px solid #cccccc;
                    border-radius: 6px;
                }
                QLabel {
                    color: #333333;
                    background-color: transparent;
                }
                QProgressBar {
                    border: 1px solid #cccccc;
                    border-radius: 3px;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #4CAF50;
                    border-radius: 2px;
                }
                QTextEdit {
                    background-color: #f8f9fa;
                    color: #333333;
                    border: 1px solid #dddddd;
                    border-radius: 4px;
                    padding: 5px;
                }
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 5px 15px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
                QPushButton:pressed {
                    background-color: #3d8b40;
                }
            """)
    
    def report_progress(self,
                        stage: ProgressStage,
                        stage_progress: float,
                        overall_progress: Optional[float] = None,
                        message: str = "") -> None:
        """Adapt progress updates from optimizers to the dialog UI."""
        # Optimizers pass (stage, progress, message); normalize both call styles.
        if isinstance(overall_progress, str) and not message:
            message = overall_progress
            overall_progress = stage_progress
        overall = overall_progress if overall_progress is not None else stage_progress
        # Accept either 0-1 or 0-100 inputs.
        normalized_overall = overall / 100 if overall > 1 else overall
        self.update_progress(stage, normalized_overall, message)

    def report_subtask(self, task_name: str, progress: float) -> None:
        """Show subtask progress in the details area."""
        pct = progress * 100 if progress <= 1 else progress
        self.details_text.append(f"{task_name}: {pct:.1f}%")
        cursor = self.details_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.details_text.setTextCursor(cursor)

    def is_cancelled(self) -> bool:
        return self._cancelled

    def set_cancellation_callback(self, callback: Callable[[], None]) -> None:
        self._cancellation_callback = callback

    def was_cancelled(self) -> bool:
        """Compatibility helper used by callers after optimization."""
        return self._cancelled

    def update_progress(self, stage: ProgressStage,
                        overall_progress: float,
                        message: str = ""):
        """Update progress display."""
        # Update stage label
        self.stage_label.setText(f"Aşama: {stage.value}")
        
        # Update progress bar
        self.progress_bar.setValue(int(overall_progress * 100))
        
        # Update details if message provided
        if message:
            self.details_text.append(message)
            # Auto-scroll to bottom
            cursor = self.details_text.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.details_text.setTextCursor(cursor)
        
        # Update status
        if overall_progress < 1.0:
            remaining_time = "Tahmini süre: hesaplanıyor..."
        else:
            remaining_time = "İşlem tamamlandı"
        self.status_label.setText(remaining_time)
    
    def set_cancellable(self, cancellable: bool) -> None:
        """Set whether operation can be cancelled
        
        Args:
            cancellable: True if operation can be cancelled
        """
        self.cancel_btn.setEnabled(cancellable)
        if cancellable:
            self.cancel_btn.setText("İptal")
        else:
            self.cancel_btn.setText("İptal Edilmez")
            self.cancel_btn.setStyleSheet("""
                QPushButton {
                    background-color: #cccccc;
                    color: #666666;
                }
            """)
    
    def set_escape_key_disabled(self, disabled: bool) -> None:
        """Disable or enable ESC key to close dialog
        
        Args:
            disabled: True to prevent ESC key closing
        """
        self._escape_key_disabled = disabled
    
    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.key() == Qt.Key.Key_Escape and not self._escape_key_disabled:
            self.cancel()
        else:
            super().keyPressEvent(event)
    
    def cancel(self):
        """Handle cancellation"""
        self._cancelled = True
        self.status_label.setText("İptal ediliyor...")
        self.cancel_btn.setEnabled(False)
        self.set_escape_key_disabled(True)
        if self._cancellation_callback:
            self._cancellation_callback()
        
        # Emit cancelled signal
        self.reject()

    def reject(self):
        """Ensure cancellation flag is set when dialog is rejected."""
        self._cancelled = True
        super().reject()
    
    def closeEvent(self, event):
        """Handle close event"""
        # Re-enable ESC key when dialog is closed
        self.set_escape_key_disabled(False)
        super().closeEvent(event)
    
    def showMinimized(self):
        """Show dialog minimized"""
        self.setWindowState(Qt.WindowState.WindowMinimized)
        