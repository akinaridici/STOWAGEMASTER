"""
Example usage of progress indicators and configuration management
for tanker stowage optimization.

This example demonstrates:
1. Using the new configuration management system
2. Running optimization with progress reporting
3. Handling cancellation and errors
4. Migrating from old configuration format
"""

import sys
import os
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel, QDialog
from PyQt6.QtCore import QTimer

from core.config_manager import ConfigurationManager
from core.config_migration import ConfigMigration
from core.optimization_worker import OptimizationWorker
from core.progress_reporter import ProgressStage
from ui.progress_dialog import OptimizationProgressDialog
from models.ship import Ship, Tank
from models.cargo import Cargo
from optimizer.genetic_optimizer_with_progress import GeneticOptimizerWithProgress
from optimizer.advanced_optimizer_with_progress import AdvancedStowageOptimizerWithProgress


class OptimizationExampleWindow(QMainWindow):
    """Example window demonstrating optimization with progress indicators"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tanker Stowage Optimization Example")
        self.setGeometry(100, 100, 400, 300)
        
        # Initialize configuration manager
        self.config_manager = ConfigurationManager()
        
        # Try to migrate from old configuration
        self._migrate_configuration()
        
        # Load current configuration
        self.config = self.config_manager.get_config()
        
        # Setup UI
        self._setup_ui()
    
    def _migrate_configuration(self):
        """Migrate from old configuration format if needed"""
        try:
            migration = ConfigMigration(self.config_manager)
            success = migration.migrate_from_old_format()
            if success:
                print("Configuration migrated successfully from old format")
            else:
                print("No old configuration found or migration failed")
        except Exception as e:
            print(f"Migration error: {e}")
    
    def _setup_ui(self):
        """Setup the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        
        # Status label
        self.status_label = QLabel("Ready to optimize")
        layout.addWidget(self.status_label)
        
        # Configuration info
        config_info = f"Algorithm: {self.config.optimization_algorithm}\n"
        config_info += f"Population Size: {self.config.genetic_algorithm.population_size}\n"
        config_info += f"Max Generations: {self.config.genetic_algorithm.max_generations}"
        
        self.config_label = QLabel(config_info)
        layout.addWidget(self.config_label)
        
        # Optimization buttons
        self.genetic_btn = QPushButton("Run Genetic Algorithm")
        self.genetic_btn.clicked.connect(self._run_genetic_optimization)
        layout.addWidget(self.genetic_btn)
        
        self.advanced_btn = QPushButton("Run Advanced Optimizer")
        self.advanced_btn.clicked.connect(self._run_advanced_optimization)
        layout.addWidget(self.advanced_btn)
        
        self.threaded_btn = QPushButton("Run Threaded Optimization")
        self.threaded_btn.clicked.connect(self._run_threaded_optimization)
        layout.addWidget(self.threaded_btn)
        
        central_widget.setLayout(layout)
    
    def _create_sample_data(self):
        """Create sample ship and cargo data for demonstration"""
        # Create a simple ship with 6 tanks (3 rows, port/starboard)
        ship = Ship(
            id="example_ship",
            name="Example Tanker",
            tanks=[
                # Row 1 (bow)
                Tank(id="P1", name="Port 1", volume=1000.0),
                Tank(id="S1", name="Starboard 1", volume=1000.0),
                # Row 2 (mid)
                Tank(id="P2", name="Port 2", volume=1500.0),
                Tank(id="S2", name="Starboard 2", volume=1500.0),
                # Row 3 (stern)
                Tank(id="P3", name="Port 3", volume=1200.0),
                Tank(id="S3", name="Starboard 3", volume=1200.0),
            ]
        )
        
        # Create sample cargo requests
        cargos = [
            Cargo(
                unique_id="cargo1",
                cargo_type="Crude Oil A",
                quantity=2000.0,
                is_mandatory=True,
                receivers=[]
            ),
            Cargo(
                unique_id="cargo2",
                cargo_type="Crude Oil B",
                quantity=1500.0,
                is_mandatory=False,
                receivers=[]
            ),
            Cargo(
                unique_id="cargo3",
                cargo_type="Crude Oil C",
                quantity=1800.0,
                is_mandatory=False,
                receivers=[]
            ),
        ]
        
        return ship, cargos
    
    def _run_genetic_optimization(self):
        """Run genetic algorithm with progress dialog"""
        ship, cargos = self._create_sample_data()
        
        # Create progress dialog
        progress_dialog = OptimizationProgressDialog(self)
        progress_dialog.setWindowTitle("Genetic Algorithm Optimization")
        
        # Create optimizer with progress reporter
        optimizer = GeneticOptimizerWithProgress(
            ship=ship,
            cargo_requests=cargos,
            settings=self.config.genetic_algorithm.__dict__,
            progress_reporter=progress_dialog
        )
        
        # Connect dialog signals
        progress_dialog.rejected.connect(lambda: self._on_optimization_cancelled("Genetic Algorithm"))
        
        # Show dialog and run optimization
        progress_dialog.show()
        
        try:
            # Run optimization (this will update progress dialog)
            plan = optimizer.optimize()
            
            if progress_dialog.result() == QDialog.DialogCode.Rejected:
                self.status_label.setText("Genetic Algorithm cancelled")
            else:
                self.status_label.setText(f"Genetic Algorithm completed. Loaded: {plan.get_total_loaded():.1f}")
                
        except Exception as e:
            self.status_label.setText(f"Genetic Algorithm error: {e}")
        finally:
            progress_dialog.close()
    
    def _run_advanced_optimization(self):
        """Run advanced optimizer with progress dialog"""
        ship, cargos = self._create_sample_data()
        
        # Create progress dialog
        progress_dialog = OptimizationProgressDialog(self)
        progress_dialog.setWindowTitle("Advanced Optimizer")
        
        # Create optimizer with progress reporter
        optimizer = AdvancedStowageOptimizerWithProgress(progress_reporter=progress_dialog)
        
        # Connect dialog signals
        progress_dialog.rejected.connect(lambda: self._on_optimization_cancelled("Advanced Optimizer"))
        
        # Show dialog and run optimization
        progress_dialog.show()
        
        try:
            # Run optimization (this will update progress dialog)
            plan = optimizer.optimize_advanced(
                ship=ship,
                cargo_requests=cargos,
                settings=self.config.advanced_optimizer.__dict__
            )
            
            if progress_dialog.result() == QDialog.DialogCode.Rejected:
                self.status_label.setText("Advanced Optimizer cancelled")
            else:
                self.status_label.setText(f"Advanced Optimizer completed. Loaded: {plan.get_total_loaded():.1f}")
                
        except Exception as e:
            self.status_label.setText(f"Advanced Optimizer error: {e}")
        finally:
            progress_dialog.close()
    
    def _run_threaded_optimization(self):
        """Run optimization in background thread"""
        ship, cargos = self._create_sample_data()
        
        # Create progress dialog
        progress_dialog = OptimizationProgressDialog(self)
        progress_dialog.setWindowTitle("Threaded Optimization")
        
        # Create optimization worker with appropriate optimizer function
        if self.config.optimization_algorithm == 'genetic':
            from optimizer.genetic_optimizer_with_progress import GeneticOptimizerWithProgress
            optimizer_func = GeneticOptimizerWithProgress.optimize
            worker_args = (ship, cargos)
            worker_kwargs = {
                'settings': self.config.genetic_algorithm.__dict__,
                'excluded_tanks': None,
                'fixed_assignments': None
            }
        else:
            from optimizer.advanced_optimizer_with_progress import AdvancedStowageOptimizerWithProgress
            optimizer_func = AdvancedStowageOptimizerWithProgress.optimize_advanced
            worker_args = (ship, cargos)
            worker_kwargs = {
                'settings': self.config.advanced_optimizer.__dict__,
                'excluded_tanks': None,
                'fixed_assignments': None
            }
        
        worker = OptimizationWorker(optimizer_func, *worker_args, **worker_kwargs)
        
        # Connect worker signals
        worker.progress_updated.connect(progress_dialog.update_progress)
        worker.optimization_completed.connect(self._on_optimization_completed)
        worker.optimization_failed.connect(self._on_optimization_failed)
        worker.optimization_cancelled.connect(lambda: self._on_optimization_cancelled("Threaded Optimization"))
        
        # Connect dialog signals
        progress_dialog.rejected.connect(worker.cancel_optimization)
        
        # Show dialog and start worker
        progress_dialog.show()
        worker.start()
    
    def _on_optimization_completed(self, plan):
        """Handle optimization completion"""
        self.status_label.setText(f"Threaded optimization completed. Loaded: {plan.get_total_loaded():.1f}")
    
    def _on_optimization_failed(self, error_message):
        """Handle optimization failure"""
        self.status_label.setText(f"Threaded optimization failed: {error_message}")
    
    def _on_optimization_cancelled(self, algorithm_name):
        """Handle optimization cancellation"""
        self.status_label.setText(f"{algorithm_name} cancelled by user")


def main():
    """Main function to run the example"""
    app = QApplication(sys.argv)
    
    # Create and show the example window
    window = OptimizationExampleWindow()
    window.show()
    
    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()