# Progress Indicator Architecture Design

## Current State Analysis

### Existing Progress Indicators
The application currently has minimal progress indication:
- Basic cursor changes to wait cursor (`QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)`)
- No progress bars or status updates during long operations
- UI freezes during optimization runs (blocking main thread)

### Operations Requiring Progress Indicators
1. **Genetic Algorithm Optimization** - Can take 30+ seconds with default settings
2. **Advanced Multi-phase Optimization** - Complex operations with multiple phases
3. **Plan Loading/Saving** - Large plans may take noticeable time
4. **Plan Comparison** - Multiple solutions being evaluated

## Proposed Architecture

### 1. Progress Reporting Interface

```python
from abc import ABC, abstractmethod
from typing import Optional, Callable
from enum import Enum

class ProgressStage(Enum):
    """Enumeration of optimization stages"""
    INITIALIZING = "Initializing"
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
        """Report progress update"""
        pass
    
    @abstractmethod
    def report_subtask(self, task_name: str, progress: float) -> None:
        """Report progress for a subtask"""
        pass
    
    @abstractmethod
    def is_cancelled(self) -> bool:
        """Check if operation was cancelled"""
        pass
```

### 2. Progress Dialog Implementation

```python
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                           QProgressBar, QPushButton, QTextEdit)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

class OptimizationProgressDialog(QDialog):
    """Dialog showing optimization progress with cancellation support"""
    
    # Signal emitted when user cancels
    cancelled = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Optimizasyon İlerlemesi")
        self.setFixedSize(500, 300)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Yükleme Planı Oluşturuluyor...")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Stage label
        self.stage_label = QLabel("Hazırlanıyor...")
        layout.addWidget(self.stage_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)
        
        # Details text (scrollable)
        self.details_text = QTextEdit()
        self.details_text.setMaximumHeight(100)
        self.details_text.setReadOnly(True)
        layout.addWidget(self.details_text)
        
        # Cancel button
        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.cancel)
        layout.addWidget(cancel_btn)
    
    def update_progress(self, stage: ProgressStage, 
                     stage_progress: float, 
                     overall_progress: float, 
                     message: str = ""):
        """Update progress display"""
        self.stage_label.setText(f"Aşama: {stage.value}")
        self.progress_bar.setValue(int(overall_progress * 100))
        
        if message:
            self.details_text.append(message)
    
    def cancel(self):
        """Handle cancellation"""
        self.cancelled.emit()
        self.reject()
```

### 3. Threaded Optimization Wrapper

```python
from PyQt6.QtCore import QThread, pyqtSignal
from typing import Optional, Callable

class OptimizationWorker(QThread):
    """Worker thread for optimization operations"""
    
    # Signals
    progress = pyqtSignal(ProgressStage, float, float, str)
    completed = pyqtSignal(object)  # StowagePlan
    error = pyqtSignal(str)
    
    def __init__(self, optimizer_func: Callable, *args, **kwargs):
        super().__init__()
        self.optimizer_func = optimizer_func
        self.args = args
        self.kwargs = kwargs
        self._cancelled = False
    
    def run(self):
        """Execute optimization in background thread"""
        try:
            # Create progress reporter
            reporter = ThreadProgressReporter(self.progress, self.is_cancelled)
            
            # Call optimizer with progress reporter
            result = self.optimizer_func(reporter, *self.args, **self.kwargs)
            
            if not self._cancelled:
                self.completed.emit(result)
        except Exception as e:
            self.error.emit(str(e))
    
    def cancel(self):
        """Cancel the optimization"""
        self._cancelled = True

class ThreadProgressReporter:
    """Progress reporter implementation for threaded operations"""
    
    def __init__(self, progress_signal: pyqtSignal, 
                 cancelled_check: Callable[[], bool]):
        self.progress_signal = progress_signal
        self.cancelled_check = cancelled_check
    
    def report_progress(self, stage: ProgressStage, 
                      stage_progress: float,
                      overall_progress: float,
                      message: str = ""):
        if not self.cancelled_check():
            self.progress_signal.emit(stage, stage_progress, overall_progress, message)
    
    def report_subtask(self, task_name: str, progress: float):
        if not self.cancelled_check():
            message = f"{task_name}: {int(progress * 100)}%"
            self.progress_signal.emit(ProgressStage.INITIALIZING, progress, progress, message)
    
    def is_cancelled(self) -> bool:
        return self.cancelled_check()
```

### 4. Integration Points

#### MainWindow Integration
```python
# In ui/main_window.py

def create_optimized_plan(self):
    """Modified to use progress dialog"""
    if not self.current_ship or not self.current_cargo_requests:
        # Existing validation...
        return
    
    # Create progress dialog
    progress_dialog = OptimizationProgressDialog(self)
    
    # Create worker thread
    if self.optimization_settings.get('optimization_algorithm', 'genetic') == 'genetic':
        worker = OptimizationWorker(
            self._run_genetic_with_progress,
            self.current_ship,
            self.current_cargo_requests,
            self.excluded_tanks,
            self.optimization_settings
        )
    else:
        worker = OptimizationWorker(
            self._run_advanced_with_progress,
            self.current_ship,
            self.current_cargo_requests,
            self.excluded_tanks,
            self.optimization_settings
        )
    
    # Connect signals
    worker.progress.connect(progress_dialog.update_progress)
    worker.completed.connect(self.on_optimization_completed)
    worker.error.connect(self.on_optimization_error)
    progress_dialog.cancelled.connect(worker.cancel)
    
    # Show dialog and start worker
    progress_dialog.show()
    worker.start()
    
    # Wait for completion
    def on_completion():
        progress_dialog.accept()
        worker.deleteLater()
    
    worker.finished.connect(on_completion)
```

#### Genetic Algorithm Integration
```python
# In optimizer/genetic_optimizer.py

def optimize_with_progress(self, reporter: ProgressReporter) -> StowagePlan:
    """Modified optimize method with progress reporting"""
    
    # Phase 1: Initialization
    reporter.report_progress(ProgressStage.INITIALIZING, 0.0, 0.0, 
                         "Genetik algoritma başlatılıyor...")
    
    # Place mandatory cargos
    if self.mandatory_cargos:
        reporter.report_progress(ProgressStage.MANDATORY_PLACEMENT, 0.0, 0.1,
                             "Zorunlu yükler yerleştiriliyor...")
        # ... existing mandatory cargo logic ...
        reporter.report_progress(ProgressStage.MANDATORY_PLACEMENT, 1.0, 0.2,
                             "Zorunlu yükler yerleştirildi")
    
    # Initialize population
    reporter.report_progress(ProgressStage.INITIALIZING, 0.0, 0.3,
                         "Başlangıç popülasyonu oluşturuluyor...")
    population = self.create_initial_population()
    
    # GA main loop with progress
    total_generations = self.max_generations
    for generation in range(total_generations):
        if reporter.is_cancelled():
            return None  # Cancelled
        
        # Report progress every 10 generations
        if generation % 10 == 0:
            gen_progress = (generation + 1) / total_generations
            overall_progress = 0.3 + (0.5 * gen_progress)  # 30% init + 50% GA
            best_fitness = max(self.best_fitness_history) if self.best_fitness_history else 0
            reporter.report_progress(ProgressStage.INITIALIZING, gen_progress, overall_progress,
                                 f"Nesil {generation+1}/{total_generations} - En iyi uygunluk: {best_fitness:.2f}")
        
        # ... existing GA logic for this generation ...
        
        # Check convergence
        if len(self.best_fitness_history) >= self.convergence_generations:
            # ... existing convergence check ...
            if recent_improvement < self.convergence_threshold:
                reporter.report_progress(ProgressStage.INITIALIZING, 1.0, 0.8,
                                     "Yakınsama sağlandı - Sonuçlar işleniyor...")
                break
    
    # Final phase
    reporter.report_progress(ProgressStage.FINALIZING, 0.0, 0.9,
                         "En iyi çözüm seçiliyor ve uygulanıyor...")
    
    # Convert chromosome to plan
    plan = self._chromosome_to_plan(best_chromosome)
    
    # Post-processing
    reporter.report_progress(ProgressStage.SCORING, 0.0, 0.95,
                         "Son optimizasyon ve puanlama...")
    plan = self._fill_empty_tanks_with_remaining_cargo(plan, self.settings)
    
    reporter.report_progress(ProgressStage.SCORING, 1.0, 1.0,
                         "Yükleme planı tamamlandı")
    
    return plan
```

#### Advanced Optimizer Integration
```python
# In optimizer/advanced_optimizer.py

def optimize_advanced_with_progress(ship: Ship, cargo_requests: List[Cargo],
                               excluded_tanks: Optional[set[str]] = None,
                               fixed_assignments: Optional[Dict[str, TankAssignment]] = None,
                               settings: Optional[Dict] = None,
                               reporter: ProgressReporter = None) -> StowagePlan:
    """Modified advanced optimizer with progress reporting"""
    
    # Calculate overall progress weight for each phase
    phase_weights = {
        ProgressStage.MANDATORY_PLACEMENT: 0.1,
        ProgressStage.PHASE_1: 0.1,
        ProgressStage.PHASE_2: 0.1,
        ProgressStage.PHASE_3: 0.1,
        ProgressStage.PHASE_4: 0.15,  # More complex
        ProgressStage.PHASE_5: 0.15,  # More complex
        ProgressStage.PHASE_6: 0.1,
        ProgressStage.PHASE_7: 0.1,
        ProgressStage.FINALIZING: 0.05,
        ProgressStage.SCORING: 0.05
    }
    
    current_progress = 0.0
    
    def report_phase_start(stage: ProgressStage, message: str):
        nonlocal current_progress
        reporter.report_progress(stage, 0.0, current_progress, message)
    
    def report_phase_end(stage: ProgressStage, message: str):
        nonlocal current_progress
        current_progress += phase_weights.get(stage, 0.1)
        reporter.report_progress(stage, 1.0, current_progress, message)
    
    # Phase 0: Mandatory
    if mandatory_cargos:
        report_phase_start(ProgressStage.MANDATORY_PLACEMENT, "Zorunlu yükler işleniyor...")
        # ... existing FAZ 0 logic ...
        report_phase_end(ProgressStage.MANDATORY_PLACEMENT, "Zorunlu yükler yerleştirildi")
    
    # Phase 1: Single tank
    report_phase_start(ProgressStage.PHASE_1, "Tek tanklı yükler aranıyor...")
    # ... existing FAZ 1 logic with subtask reporting ...
    report_phase_end(ProgressStage.PHASE_1, "Tek tanklı yükler tamamlandı")
    
    # Continue for all phases...
    # Each phase reports start, progress for subtasks, and completion
    
    return plan
```

## Implementation Benefits

1. **Non-blocking UI**: Long operations run in background threads
2. **Detailed Feedback**: Users see which phase is active and overall progress
3. **Cancellation Support**: Users can cancel long-running operations
4. **Scalable**: Easy to add new operations with progress reporting
5. **Consistent**: Unified progress reporting across all optimization methods

## Migration Strategy

1. Create new progress infrastructure files
2. Modify optimization algorithms to accept optional ProgressReporter
3. Update MainWindow to use threaded optimization with progress dialog
4. Maintain backward compatibility (operations work without progress reporter)
5. Add unit tests for progress reporting

## Testing Considerations

1. Test cancellation at different phases
2. Test with very small and very large cargo sets
3. Test error handling in threaded environment
4. Test UI responsiveness during optimization
5. Test progress accuracy (overall progress should reach 100%)