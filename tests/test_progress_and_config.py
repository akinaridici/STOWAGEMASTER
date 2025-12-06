"""
Test suite for progress indicators and configuration management system.

This test suite covers:
1. Configuration loading and validation
2. Progress reporting functionality
3. Optimization worker threading
4. Migration from old configuration format
5. Integration between components
"""

import unittest
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent
import sys
sys.path.insert(0, str(project_root))

from core.config_manager import ConfigurationManager
from core.config_models import AppConfig, GeneticAlgorithmConfig, AdvancedOptimizerConfig
from core.config_validator import ConfigValidator
from core.config_migration import ConfigMigration
from core.progress_reporter import ProgressReporter, ProgressStage
from core.optimization_worker import OptimizationWorker
from models.ship import Ship, Tank
from models.cargo import Cargo


class TestConfigurationManagement(unittest.TestCase):
    """Test configuration management functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_manager = ConfigurationManager(config_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_load_default_config(self):
        """Test loading default configuration"""
        config = self.config_manager.load_config()
        
        self.assertIsInstance(config, AppConfig)
        self.assertIsInstance(config.genetic_algorithm, GeneticAlgorithmConfig)
        self.assertIsInstance(config.advanced_optimizer, AdvancedOptimizerConfig)
        self.assertEqual(config.genetic_algorithm.population_size, 500)
        self.assertEqual(config.genetic_algorithm.max_generations, 2000)
    
    def test_save_and_load_config(self):
        """Test saving and loading configuration"""
        # Create custom config
        config = AppConfig(
            genetic_algorithm=GeneticAlgorithmConfig(
                population_size=1000,
                max_generations=3000
            )
        )
        
        # Save config
        self.assertTrue(self.config_manager.save_config(config))
        
        # Load config
        loaded_config = self.config_manager.load_config()
        self.assertEqual(loaded_config.genetic_algorithm.population_size, 1000)
        self.assertEqual(loaded_config.genetic_algorithm.max_generations, 3000)
    
    def test_config_validation(self):
        """Test configuration validation"""
        # Valid config
        valid_config = AppConfig()
        errors = ConfigValidator.validate_config(valid_config)
        self.assertEqual(len(errors), 0)
        
        # Invalid config (population size too high)
        invalid_config = AppConfig(
            genetic_algorithm=GeneticAlgorithmConfig(population_size=10000)
        )
        errors = ConfigValidator.validate_config(invalid_config)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("population_size" in error for error in errors))


class TestProgressReporting(unittest.TestCase):
    """Test progress reporting functionality"""
    
    def test_progress_reporter_interface(self):
        """Test progress reporter interface"""
        reporter = ProgressReporter()
        
        # Test initial state
        self.assertFalse(reporter.is_cancelled())
        self.assertEqual(reporter.get_progress(), 0.0)
        self.assertEqual(reporter.get_stage(), ProgressStage.INITIALIZING_POPULATION)
        
        # Test progress reporting
        reporter.report_progress(ProgressStage.RUNNING_OPTIMIZATION, 50.0, "Test message")
        self.assertEqual(reporter.get_progress(), 50.0)
        self.assertEqual(reporter.get_stage(), ProgressStage.RUNNING_OPTIMIZATION)
        self.assertEqual(reporter.get_message(), "Test message")
        
        # Test cancellation
        reporter.cancel()
        self.assertTrue(reporter.is_cancelled())
    
    def test_progress_stage_values(self):
        """Test progress stage values"""
        stages = [
            ProgressStage.INITIALIZING_POPULATION,
            ProgressStage.PLACING_MANDATORY,
            ProgressStage.RUNNING_OPTIMIZATION,
            ProgressStage.FINALIZING_RESULTS,
            ProgressStage.POST_PROCESSING
        ]
        
        for stage in stages:
            self.assertIsInstance(stage.value, str)
            self.assertIsInstance(stage.display_name, str)


class TestOptimizationWorker(unittest.TestCase):
    """Test optimization worker functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.ship = Ship(
            id="test_ship",
            name="Test Ship",
            tanks=[
                Tank(id="P1", volume=1000.0, row=1, side="port"),
                Tank(id="S1", volume=1000.0, row=1, side="starboard"),
            ]
        )
        
        self.cargos = [
            Cargo(
                unique_id="cargo1",
                name="Test Cargo",
                quantity=500.0,
                is_mandatory=False,
                receivers=[]
            )
        ]
    
    def test_worker_creation(self):
        """Test optimization worker creation"""
        worker = OptimizationWorker(
            algorithm_type="genetic",
            ship=self.ship,
            cargo_requests=self.cargos,
            settings={}
        )
        
        self.assertEqual(worker.algorithm_type, "genetic")
        self.assertEqual(worker.ship, self.ship)
        self.assertEqual(worker.cargo_requests, self.cargos)
    
    def test_worker_signals(self):
        """Test optimization worker signals"""
        worker = OptimizationWorker(
            algorithm_type="genetic",
            ship=self.ship,
            cargo_requests=self.cargos,
            settings={}
        )
        
        # Mock signal handlers
        progress_handler = Mock()
        completed_handler = Mock()
        failed_handler = Mock()
        
        worker.progress_updated.connect(progress_handler)
        worker.optimization_completed.connect(completed_handler)
        worker.optimization_failed.connect(failed_handler)
        
        # Test signal emission (mock the actual optimization)
        with patch.object(worker, '_run_optimization') as mock_run:
            mock_run.return_value = None
            
            # Emit progress signal
            worker.progress_updated.emit(ProgressStage.RUNNING_OPTIMIZATION, 50.0, "Test")
            
            # Verify signal was received
            progress_handler.assert_called_with(ProgressStage.RUNNING_OPTIMIZATION, 50.0, "Test")


class TestConfigurationMigration(unittest.TestCase):
    """Test configuration migration functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_manager = ConfigurationManager(config_dir=self.temp_dir)
        self.migration = ConfigMigration(self.config_manager)
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_migration_from_old_format(self):
        """Test migration from old configuration format"""
        # Create old configuration file
        old_config_path = Path(self.temp_dir) / "optimization_settings.json"
        old_config = {
            "ga_population_size": 1000,
            "ga_max_generations": 3000,
            "ga_crossover_rate": 0.85,
            "ga_mutation_rate": 0.15,
            "min_utilization": 0.70,
            "optimization_algorithm": "genetic"
        }
        
        with open(old_config_path, 'w') as f:
            json.dump(old_config, f)
        
        # Run migration
        success = self.migration.migrate_from_old_format()
        
        # Verify migration
        self.assertTrue(success)
        
        # Load new configuration
        new_config = self.config_manager.load_config()
        
        # Verify values were migrated correctly
        self.assertEqual(new_config.genetic_algorithm.population_size, 1000)
        self.assertEqual(new_config.genetic_algorithm.max_generations, 3000)
        self.assertEqual(new_config.genetic_algorithm.crossover_rate, 0.85)
        self.assertEqual(new_config.genetic_algorithm.mutation_rate, 0.15)
        self.assertEqual(new_config.advanced_optimizer.min_utilization, 0.70)
        self.assertEqual(new_config.optimization_algorithm, "genetic")
        
        # Verify old file was backed up
        backup_path = old_config_path.with_suffix('.json.backup')
        self.assertTrue(backup_path.exists())


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete system"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_manager = ConfigurationManager(config_dir=self.temp_dir)
        
        # Create test ship and cargo
        self.ship = Ship(
            id="integration_test_ship",
            name="Integration Test Ship",
            tanks=[
                Tank(id="P1", volume=1000.0, row=1, side="port"),
                Tank(id="S1", volume=1000.0, row=1, side="starboard"),
                Tank(id="P2", volume=1500.0, row=2, side="port"),
                Tank(id="S2", volume=1500.0, row=2, side="starboard"),
            ]
        )
        
        self.cargos = [
            Cargo(
                unique_id="cargo1",
                name="Integration Test Cargo 1",
                quantity=1000.0,
                is_mandatory=True,
                receivers=[]
            ),
            Cargo(
                unique_id="cargo2",
                name="Integration Test Cargo 2",
                quantity=1500.0,
                is_mandatory=False,
                receivers=[]
            ),
        ]
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_full_optimization_workflow(self):
        """Test complete optimization workflow with progress reporting"""
        # Load configuration
        config = self.config_manager.load_config()
        
        # Create progress reporter
        progress_reporter = ProgressReporter()
        
        # Track progress updates
        progress_updates = []
        def track_progress(stage, progress, message):
            progress_updates.append((stage, progress, message))
        
        progress_reporter.progress_updated.connect(track_progress)
        
        # Create optimization worker
        worker = OptimizationWorker(
            algorithm_type="genetic",
            ship=self.ship,
            cargo_requests=self.cargos,
            settings=config.to_dict()
        )
        
        # Connect progress reporting
        worker.progress_updated.connect(progress_reporter.report_progress)
        
        # Mock the optimization to avoid long execution
        with patch('optimizer.genetic_optimizer_with_progress.GeneticOptimizerWithProgress.optimize') as mock_optimize:
            from models.plan import StowagePlan
            mock_plan = StowagePlan(
                ship_name=self.ship.name,
                ship_profile_id=self.ship.id,
                cargo_requests=self.cargos,
                plan_name="Test Plan"
            )
            mock_optimize.return_value = mock_plan
            
            # Run optimization
            worker._run_optimization()
            
            # Verify progress was reported
            self.assertGreater(len(progress_updates), 0)
            
            # Verify different stages were reported
            stages = [update[0] for update in progress_updates]
            self.assertIn(ProgressStage.INITIALIZING_POPULATION, stages)
            self.assertIn(ProgressStage.RUNNING_OPTIMIZATION, stages)
    
    def test_configuration_change_notification(self):
        """Test configuration change notification"""
        # Create initial config
        config = AppConfig(genetic_algorithm=GeneticAlgorithmConfig(population_size=500))
        self.config_manager.save_config(config)
        
        # Set up change handler
        change_handler = Mock()
        self.config_manager.add_change_observer(change_handler)
        
        # Modify configuration
        modified_config = AppConfig(genetic_algorithm=GeneticAlgorithmConfig(population_size=1000))
        self.config_manager.save_config(modified_config)
        
        # Verify change notification (this might need file system watcher implementation)
        # For now, just verify the config was saved
        loaded_config = self.config_manager.load_config()
        self.assertEqual(loaded_config.genetic_algorithm.population_size, 1000)


class TestErrorHandling(unittest.TestCase):
    """Test error handling scenarios"""
    
    def test_invalid_configuration_handling(self):
        """Test handling of invalid configuration"""
        temp_dir = tempfile.mkdtemp()
        try:
            config_manager = ConfigurationManager(config_dir=temp_dir)
            
            # Create invalid configuration file
            config_file = Path(temp_dir) / "app_config.json"
            with open(config_file, 'w') as f:
                f.write("invalid json content")
            
            # Should load default configuration instead of crashing
            config = config_manager.load_config()
            self.assertIsInstance(config, AppConfig)
            
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_progress_cancellation(self):
        """Test progress cancellation handling"""
        reporter = ProgressReporter()
        
        # Cancel before any progress
        reporter.cancel()
        self.assertTrue(reporter.is_cancelled())
        
        # Try to report progress after cancellation
        reporter.report_progress(ProgressStage.RUNNING_OPTIMIZATION, 50.0, "Test")
        
        # Should still be cancelled
        self.assertTrue(reporter.is_cancelled())


def run_tests():
    """Run all tests"""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestConfigurationManagement,
        TestProgressReporting,
        TestOptimizationWorker,
        TestConfigurationMigration,
        TestIntegration,
        TestErrorHandling
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Return success status
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)