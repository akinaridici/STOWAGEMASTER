"""Centralized configuration management system"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Type, TypeVar, Union, Callable, List
from dataclasses import asdict, is_dataclass
from datetime import datetime

from .config_models import (
    AppConfig, GeneticAlgorithmConfig, AdvancedOptimizerConfig, 
    UIConfig, ValidationConfig, Environment
)
from .progress_reporter import ProgressReporter

T = TypeVar('T')


class ConfigurationManager:
    """Centralized configuration management system"""
    
    def __init__(self, config_file: Optional[Path] = None):
        """Initialize configuration manager
        
        Args:
            config_file: Path to configuration file. If None, uses default location
        """
        self.config_file = config_file or self._get_default_config_path()
        self._config: Optional[AppConfig] = None
        self._watchers: List[Callable[[AppConfig], None]] = []
    
    def _get_default_config_path(self) -> Path:
        """Get default configuration file path"""
        # Use same logic as StorageManager.get_base_dir()
        if getattr(sys, 'frozen', False):
            if hasattr(sys, '_MEIPASS'):
                base_path = Path(sys._MEIPASS)
            else:
                base_path = Path(sys.executable).parent
        else:
            base_path = Path.cwd()
        
        return base_path / "config" / "app_config.json"
    
    def load_config(self) -> AppConfig:
        """Load configuration from file
        
        Returns:
            Loaded configuration or default if file doesn't exist
        """
        if self._config is None:
            self._config = self._load_from_file()
        return self._config
    
    def get_config(self) -> AppConfig:
        """Get current configuration (alias for load_config)
        
        Returns:
            Current configuration
        """
        return self.load_config()
    
    def _load_from_file(self) -> AppConfig:
        """Load configuration from JSON file with validation"""
        if not self.config_file.exists():
            # Create default config
            default_config = AppConfig()
            self.save_config(default_config)
            return default_config
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate and convert to AppConfig
            config = self._dict_to_config(data)
            
            # Validate loaded config
            errors = config.validate()
            if errors:
                print(f"Configuration validation errors: {errors}")
                # Log errors but continue with default values for invalid fields
                # This prevents app from failing due to config issues
            
            return config
        
        except Exception as e:
            print(f"Error loading configuration: {e}")
            return AppConfig()
    
    def _dict_to_config(self, data: Dict[str, Any]) -> AppConfig:
        """Convert dictionary to AppConfig with validation"""
        # Extract main config
        main_config = data.get('app', {})
        
        # Convert nested configs
        ga_data = main_config.get('genetic_algorithm', {})
        advanced_data = main_config.get('advanced_optimizer', {})
        ui_data = main_config.get('ui', {})
        validation_data = main_config.get('validation', {})
        
        # Create config objects with validation
        return AppConfig(
            environment=Environment(main_config.get('environment', 'development')),
            debug_mode=main_config.get('debug_mode', False),
            log_level=main_config.get('log_level', 'INFO'),
            data_directory=Path(main_config.get('data_directory')) if main_config.get('data_directory') else None,
            backup_directory=Path(main_config.get('backup_directory')) if main_config.get('backup_directory') else None,
            log_directory=Path(main_config.get('log_directory')) if main_config.get('log_directory') else None,
            genetic_algorithm=self._convert_to_dataclass(GeneticAlgorithmConfig, ga_data),
            advanced_optimizer=self._convert_to_dataclass(AdvancedOptimizerConfig, advanced_data),
            ui=self._convert_to_dataclass(UIConfig, ui_data),
            validation=self._convert_to_dataclass(ValidationConfig, validation_data),
            last_profile_id=main_config.get('last_profile_id'),
            recent_plans=main_config.get('recent_plans', []),
            optimization_algorithm=main_config.get('optimization_algorithm', 'genetic')
        )
    
    def _convert_to_dataclass(self, dataclass_type: Type[T], data: Dict[str, Any]) -> T:
        """Convert dictionary to dataclass with type validation"""
        if not data:
            return dataclass_type()
        
        # Get field information from dataclass
        fields = dataclass_type.__dataclass_fields__
        kwargs = {}
        
        for field in fields:
            field_name = field.name
            field_type = field.type
            
            if field_name in data:
                value = data[field_name]
                
                # Type validation and conversion
                if hasattr(field_type, '__origin__'):  # Generic type like List, Dict
                    # Handle generic types
                    kwargs[field_name] = value
                elif field_type == bool:
                    kwargs[field_name] = bool(value)
                elif field_type == int:
                    kwargs[field_name] = int(value)
                elif field_type == float:
                    kwargs[field_name] = float(value)
                elif field_type == str:
                    kwargs[field_name] = str(value)
                elif hasattr(field_type, '__dataclass_fields__'):  # Nested dataclass
                    kwargs[field_name] = self._convert_to_dataclass(field_type, value)
                else:
                    kwargs[field_name] = value
        
        return dataclass_type(**kwargs)
    
    def save_config(self, config: AppConfig) -> bool:
        """Save configuration to file
        
        Args:
            config: Configuration to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert to dictionary with custom handling for enum
            config_dict = self._config_to_dict(config)
            
            # Structure for JSON
            json_data = {
                'app': config_dict,
                'version': '1.0',
                'timestamp': datetime.now().isoformat()
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            self._config = config
            self._notify_watchers(config)
            return True
        
        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False
    
    def get_config_value(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value by dot-separated path
        
        Args:
            key_path: Dot-separated path to configuration value
            default: Default value if path doesn't exist
            
        Returns:
            Configuration value or default
        """
        config = self.load_config()
        
        # Navigate through nested structure
        keys = key_path.split('.')
        value = config
        
        try:
            for key in keys:
                if hasattr(value, key):
                    value = getattr(value, key)
                else:
                    return default
            return value
        except (AttributeError, KeyError):
            return default
    
    def set_config_value(self, key_path: str, value: Any) -> bool:
        """Set configuration value by dot-separated path
        
        Args:
            key_path: Dot-separated path to configuration value
            value: Value to set
            
        Returns:
            True if successful, False otherwise
        """
        config = self.load_config()
        
        # Navigate through nested structure
        keys = key_path.split('.')
        target = config
        
        # Navigate to parent of target
        for key in keys[:-1]:
            if hasattr(target, key):
                target = getattr(target, key)
            else:
                return False
        
        # Set the value
        setattr(target, keys[-1], value)
        
        return self.save_config(config)
    
    def add_watcher(self, callback: Callable[[AppConfig], None]) -> None:
        """Add configuration change watcher
        
        Args:
            callback: Function to call when configuration changes
        """
        self._watchers.append(callback)
    
    def remove_watcher(self, callback: Callable[[AppConfig], None]) -> None:
        """Remove configuration change watcher
        
        Args:
            callback: Function to remove from watchers
        """
        if callback in self._watchers:
            self._watchers.remove(callback)
    
    def _notify_watchers(self, config: AppConfig) -> None:
        """Notify all watchers of configuration change
        
        Args:
            config: New configuration
        """
        for watcher in self._watchers:
            try:
                watcher(config)
            except Exception as e:
                print(f"Error in configuration watcher: {e}")
    
    def get_optimization_settings_dict(self) -> Dict[str, Any]:
        """Get optimization settings in legacy format for backward compatibility
        
        Returns:
            Dictionary compatible with existing code
        """
        config = self.load_config()
        
        # Convert to legacy format expected by existing code
        return {
            'optimization_algorithm': config.optimization_algorithm,
            'min_utilization': config.advanced_optimizer.min_utilization,
            'drag_drop_warning_threshold': config.advanced_optimizer.drag_drop_warning_threshold,
            'ga_population_size': config.genetic_algorithm.population_size,
            'ga_max_generations': config.genetic_algorithm.max_generations,
            'ga_crossover_rate': config.genetic_algorithm.crossover_rate,
            'ga_mutation_rate': config.genetic_algorithm.mutation_rate,
            'ga_tournament_size': config.genetic_algorithm.tournament_size,
            'ga_use_elitism': config.genetic_algorithm.use_elitism,
            'ga_elitism_count': config.genetic_algorithm.elitism_count,
            'ga_symmetry_penalty_coef': config.genetic_algorithm.symmetry_penalty_coef,
            'ga_trim_penalty_coef': config.genetic_algorithm.trim_penalty_coef,
            'ga_operational_penalty_coef': config.genetic_algorithm.operational_penalty_coef,
            'ga_receiver_tolerance': config.genetic_algorithm.receiver_tolerance,
            'ga_convergence_threshold': config.genetic_algorithm.convergence_threshold,
            'ga_convergence_generations': config.genetic_algorithm.convergence_generations,
            # Advanced optimizer settings
            'score_weights': config.advanced_optimizer.score_weights,
            'waste_utilization_weights': config.advanced_optimizer.waste_utilization_weights,
            'exact_fit_threshold': config.advanced_optimizer.exact_fit_threshold,
            'bow_stern_violation_threshold': config.advanced_optimizer.bow_stern_violation_threshold,
            'symmetric_pair_min_threshold': config.advanced_optimizer.symmetric_pair_min_threshold,
            'faz1_single_tank_tolerance': config.advanced_optimizer.faz1_single_tank_tolerance,
            'faz2_two_tank_tolerance': config.advanced_optimizer.faz2_two_tank_tolerance,
            'faz2_asymmetric_tolerance_factor': config.advanced_optimizer.faz2_asymmetric_tolerance_factor,
            'faz3_three_tank_tolerance': config.advanced_optimizer.faz3_three_tank_tolerance,
            'faz4_four_tank_tolerance': config.advanced_optimizer.faz4_four_tank_tolerance,
            'faz5_five_tank_tolerance': config.advanced_optimizer.faz5_five_tank_tolerance,
            'faz6_six_tank_tolerance': config.advanced_optimizer.faz6_six_tank_tolerance,
            'mandatory_retry_increment': config.advanced_optimizer.mandatory_retry_increment,
            'mandatory_max_relaxation': config.advanced_optimizer.mandatory_max_relaxation
        }
    
    def update_from_legacy_settings(self, legacy_settings: Dict[str, Any]) -> bool:
        """Update configuration from legacy settings format
        
        Args:
            legacy_settings: Settings in old format
            
        Returns:
            True if successful, False otherwise
        """
        config = self.load_config()
        
        # Update genetic algorithm settings
        if 'ga_population_size' in legacy_settings:
            config.genetic_algorithm.population_size = legacy_settings['ga_population_size']
        if 'ga_max_generations' in legacy_settings:
            config.genetic_algorithm.max_generations = legacy_settings['ga_max_generations']
        if 'ga_crossover_rate' in legacy_settings:
            config.genetic_algorithm.crossover_rate = legacy_settings['ga_crossover_rate']
        if 'ga_mutation_rate' in legacy_settings:
            config.genetic_algorithm.mutation_rate = legacy_settings['ga_mutation_rate']
        if 'ga_tournament_size' in legacy_settings:
            config.genetic_algorithm.tournament_size = legacy_settings['ga_tournament_size']
        if 'ga_use_elitism' in legacy_settings:
            config.genetic_algorithm.use_elitism = legacy_settings['ga_use_elitism']
        if 'ga_elitism_count' in legacy_settings:
            config.genetic_algorithm.elitism_count = legacy_settings['ga_elitism_count']
        if 'ga_symmetry_penalty_coef' in legacy_settings:
            config.genetic_algorithm.symmetry_penalty_coef = legacy_settings['ga_symmetry_penalty_coef']
        if 'ga_trim_penalty_coef' in legacy_settings:
            config.genetic_algorithm.trim_penalty_coef = legacy_settings['ga_trim_penalty_coef']
        if 'ga_operational_penalty_coef' in legacy_settings:
            config.genetic_algorithm.operational_penalty_coef = legacy_settings['ga_operational_penalty_coef']
        if 'ga_receiver_tolerance' in legacy_settings:
            config.genetic_algorithm.receiver_tolerance = legacy_settings['ga_receiver_tolerance']
        if 'ga_convergence_threshold' in legacy_settings:
            config.genetic_algorithm.convergence_threshold = legacy_settings['ga_convergence_threshold']
        if 'ga_convergence_generations' in legacy_settings:
            config.genetic_algorithm.convergence_generations = legacy_settings['ga_convergence_generations']
        
        # Update advanced optimizer settings
        if 'min_utilization' in legacy_settings:
            config.advanced_optimizer.min_utilization = legacy_settings['min_utilization']
        if 'drag_drop_warning_threshold' in legacy_settings:
            config.advanced_optimizer.drag_drop_warning_threshold = legacy_settings['drag_drop_warning_threshold']
        if 'score_weights' in legacy_settings:
            config.advanced_optimizer.score_weights = legacy_settings['score_weights']
        if 'waste_utilization_weights' in legacy_settings:
            config.advanced_optimizer.waste_utilization_weights = legacy_settings['waste_utilization_weights']
        if 'exact_fit_threshold' in legacy_settings:
            config.advanced_optimizer.exact_fit_threshold = legacy_settings['exact_fit_threshold']
        if 'bow_stern_violation_threshold' in legacy_settings:
            config.advanced_optimizer.bow_stern_violation_threshold = legacy_settings['bow_stern_violation_threshold']
        if 'symmetric_pair_min_threshold' in legacy_settings:
            config.advanced_optimizer.symmetric_pair_min_threshold = legacy_settings['symmetric_pair_min_threshold']
        if 'faz1_single_tank_tolerance' in legacy_settings:
            config.advanced_optimizer.faz1_single_tank_tolerance = legacy_settings['faz1_single_tank_tolerance']
        if 'faz2_two_tank_tolerance' in legacy_settings:
            config.advanced_optimizer.faz2_two_tank_tolerance = legacy_settings['faz2_two_tank_tolerance']
        if 'faz2_asymmetric_tolerance_factor' in legacy_settings:
            config.advanced_optimizer.faz2_asymmetric_tolerance_factor = legacy_settings['faz2_asymmetric_tolerance_factor']
        if 'faz3_three_tank_tolerance' in legacy_settings:
            config.advanced_optimizer.faz3_three_tank_tolerance = legacy_settings['faz3_three_tank_tolerance']
        if 'faz4_four_tank_tolerance' in legacy_settings:
            config.advanced_optimizer.faz4_four_tank_tolerance = legacy_settings['faz4_four_tank_tolerance']
        if 'faz5_five_tank_tolerance' in legacy_settings:
            config.advanced_optimizer.faz5_five_tank_tolerance = legacy_settings['faz5_five_tank_tolerance']
        if 'faz6_six_tank_tolerance' in legacy_settings:
            config.advanced_optimizer.faz6_six_tank_tolerance = legacy_settings['faz6_six_tank_tolerance']
        if 'mandatory_retry_increment' in legacy_settings:
            config.advanced_optimizer.mandatory_retry_increment = legacy_settings['mandatory_retry_increment']
        if 'mandatory_max_relaxation' in legacy_settings:
            config.advanced_optimizer.mandatory_max_relaxation = legacy_settings['mandatory_max_relaxation']
        
        # Update runtime settings
        if 'last_profile_id' in legacy_settings:
            config.last_profile_id = legacy_settings['last_profile_id']
        if 'recent_plans' in legacy_settings:
            config.recent_plans = legacy_settings['recent_plans']
        if 'optimization_algorithm' in legacy_settings:
            config.optimization_algorithm = legacy_settings['optimization_algorithm']
        
        return self.save_config(config)
    
    def _config_to_dict(self, config) -> Dict[str, Any]:
        """Convert configuration to dictionary with enum handling"""
        from dataclasses import asdict, is_dataclass
        
        def convert_value(value):
            """Recursively convert values to JSON-serializable format"""
            if hasattr(value, 'value'):  # Enum
                return value.value
            elif hasattr(value, '__dict__'):  # Dataclass
                return self._config_to_dict(value)
            elif isinstance(value, dict):
                return {k: convert_value(v) for k, v in value.items()}
            elif isinstance(value, (list, tuple)):
                return [convert_value(item) for item in value]
            elif hasattr(value, '__dataclass_fields__'):  # Dataclass instance
                return self._config_to_dict(value)
            else:
                return value
        
        if is_dataclass(config):
            result = {}
            for field_name, field_def in config.__dataclass_fields__.items():
                value = getattr(config, field_name)
                result[field_name] = convert_value(value)
            return result
        else:
            return convert_value(config)
    
    def update_config(self, settings: Dict[str, Any]) -> bool:
        """Update configuration from dictionary settings
        
        Args:
            settings: Settings dictionary to update
            
        Returns:
            True if successful, False otherwise
        """
        return self.update_from_legacy_settings(settings)