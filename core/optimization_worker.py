"""Threaded optimization worker with progress reporting"""

from PyQt6.QtCore import QThread, pyqtSignal
from typing import Optional, Callable, Any

from .progress_reporter import ProgressReporter


class OptimizationWorker(QThread):
    """Worker thread for optimization operations with progress reporting"""
    
    # Signals
    progress = pyqtSignal(object, float, float, str)  # ProgressStage, stage_progress, overall_progress, message
    completed = pyqtSignal(object)  # StowagePlan or other result
    error = pyqtSignal(str)  # Error message
    
    def __init__(self, optimizer_func: Callable, *args, **kwargs):
        """Initialize optimization worker
        
        Args:
            optimizer_func: Function to execute in background thread
            *args: Positional arguments for optimizer function
            **kwargs: Keyword arguments for optimizer function
        """
        super().__init__()
        self.optimizer_func = optimizer_func
        self.args = args
        self.kwargs = kwargs
        self._cancelled = False
        self._progress_reporter: Optional[ProgressReporter] = None
    
    def set_progress_reporter(self, reporter: ProgressReporter) -> None:
        """Set progress reporter for this worker
        
        Args:
            reporter: Progress reporter implementation
        """
        self._progress_reporter = reporter
    
    def run(self):
        """Execute optimization in background thread"""
        try:
            # Create progress reporter wrapper if not provided
            if self._progress_reporter is None:
                self._progress_reporter = ThreadProgressReporter(self.progress, self.is_cancelled)
            
            # Call optimizer with progress reporter
            result = self.optimizer_func(self._progress_reporter, *self.args, **self.kwargs)
            
            if not self._cancelled:
                self.completed.emit(result)
        except Exception as e:
            if not self._cancelled:
                self.error.emit(str(e))
    
    def cancel(self):
        """Cancel the optimization operation"""
        self._cancelled = True


class ThreadProgressReporter:
    """Progress reporter implementation for threaded operations"""
    
    def __init__(self, progress_signal: pyqtSignal, 
                 cancelled_check: Callable[[], bool]):
        """Initialize thread progress reporter
        
        Args:
            progress_signal: Signal to emit progress updates
            cancelled_check: Function to check if operation was cancelled
        """
        self.progress_signal = progress_signal
        self.cancelled_check = cancelled_check
    
    def report_progress(self, stage, stage_progress: float, 
                      overall_progress: float, message: str = "") -> None:
        """Report progress update
        
        Args:
            stage: Current optimization stage
            stage_progress: Progress within current phase (0.0-1.0)
            overall_progress: Overall progress (0.0-1.0)
            message: Optional detailed message
        """
        if not self.cancelled_check():
            self.progress_signal.emit(stage, stage_progress, overall_progress, message)
    
    def report_subtask(self, task_name: str, progress: float) -> None:
        """Report progress for a subtask
        
        Args:
            task_name: Name of the subtask
            progress: Progress of subtask (0.0-1.0)
        """
        if not self.cancelled_check():
            message = f"{task_name}: {int(progress * 100)}%"
            self.progress_signal.emit(None, progress, 0.0, message)
    
    def is_cancelled(self) -> bool:
        """Check if operation was cancelled
        
        Returns:
            True if operation was cancelled
        """
        return self.cancelled_check()