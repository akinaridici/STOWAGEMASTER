"""Progress reporting interface for long-running operations"""

from abc import ABC, abstractmethod
from typing import Optional, Callable
from enum import Enum


class ProgressStage(Enum):
    """Enumeration of optimization stages"""
    INITIALIZING = "Initializing"
    INITIALIZING_POPULATION = "Initializing population"
    RUNNING_OPTIMIZATION = "Running optimization"
    PLACING_MANDATORY = "Placing mandatory cargo"
    FINALIZING_RESULTS = "Finalizing results"
    POST_PROCESSING = "Post processing"
    VALIDATING = "Validating data"
    MANDATORY_PLACEMENT = "Placing mandatory cargo"
    PHASE_1 = "Single tank fitting"
    PHASE_2 = "Two tank fitting"
    PHASE_3 = "Three tank fitting"
    PHASE_4 = "Four tank fitting"
    PHASE_5 = "Five tank fitting"
    PHASE_6 = "Six tank fitting"
    PHASE_7 = "Multi-tank fitting"
    FINALIZING = "Finalizing plan"
    SCORING = "Scoring solutions"


class ProgressReporter(ABC):
    """Abstract interface for progress reporting"""
    
    @abstractmethod
    def report_progress(self, 
                      current_stage: ProgressStage,
                      stage_progress: float,  # 0.0 to 1.0
                      overall_progress: float,  # 0.0 to 1.0
                      message: str = "") -> None:
        """Report progress update
        
        Args:
            current_stage: Current optimization phase
            stage_progress: Progress within current phase (0.0-1.0)
            overall_progress: Overall progress (0.0-1.0)
            message: Optional detailed message
        """
        pass
    
    @abstractmethod
    def report_subtask(self, task_name: str, progress: float) -> None:
        """Report progress for a subtask
        
        Args:
            task_name: Name of the subtask
            progress: Progress of subtask (0.0-1.0)
        """
        pass
    
    @abstractmethod
    def is_cancelled(self) -> bool:
        """Check if operation was cancelled
        
        Returns:
            True if operation was cancelled
        """
        pass
    
    @abstractmethod
    def set_cancellation_callback(self, callback: Callable[[], None]) -> None:
        """Set callback to be called when cancellation is requested
        
        Args:
            callback: Function to call for cancellation
        """
        pass