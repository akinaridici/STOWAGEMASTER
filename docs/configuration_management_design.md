# Centralized Configuration Management System Design

## Current State Analysis

### Scattered Configuration Locations
1. **StorageManager**: Default settings in `get_default_settings()` method
2. **OptimizationSettingsDialog**: UI-specific settings handling
3. **MainWindow**: Hard-coded values (0.65, 0.05, etc.)
4. **JSON File**: `storage/optimization_settings.json` with mixed settings
5. **Individual Classes**: Magic numbers throughout optimizer classes

### Issues with Current Approach
1. **No Single Source of Truth**: Settings scattered across multiple files
2. **Hard-coded Values**: Many magic numbers not configurable
3. **No Validation**: Limited validation of configuration values
4. **No Environment Support**: Same settings for development and production
5. **No Type Safety**: Dictionary-based settings with no type checking

## Proposed Architecture

### 1. Configuration Schema

```python
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union
from enum import Enum
import json
from pathlib import Path

class Environment(Enum):
    """Application environment types"""
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"

@dataclass
class GeneticAlgorithmConfig:
    """Configuration for genetic algorithm optimizer"""
    population_size: int = 500
    max_generations: int = 2000
    crossover_rate: float = 0.90
    mutation_rate: float = 0.11
    tournament_size: int = 3
    use_elitism: bool = True
    elitism_count: int = 5
    symmetry_penalty_coef: float = 3000.0
    trim_penalty_coef: float = 1500.0
    operational_penalty_coef: float = 100.0
    receiver_tolerance: float = 0.03
    convergence_threshold: float = 0.0001
    convergence_generations: int = 60

@dataclass
class AdvancedOptimizerConfig:
    """Configuration for advanced multi-phase optimizer"""
    min_utilization: float = 0.65
    drag_drop_warning_threshold: float = 0.70
    
    # FAZ tolerances
    faz1_single_tank_tolerance: float = 0.05
    faz2_two_tank_tolerance: float = 0.05
    faz2_asymmetric_tolerance_factor: float = 0.2
    faz3_three_tank_tolerance: float = 0.04
    faz4_four_tank_tolerance: float = 0.04
    faz5_five_tank_tolerance: float = 0.04
    faz6_six_tank_tolerance: float = 0.05
    
    # Score weights
    score_weights: Dict[str, float] = field(default_factory=lambda: {
        "single_fit": 0.40,
        "symmetry": 0.25,
        "bow_stern": 0.15,
        "best_fit": 0.20
    })
    
    # Waste/utilization weights
    waste_utilization_weights: Dict[str, float] = field(default_factory=lambda: {
        "waste": 0.7,
        "utilization": 0.3
    })
    
    # Other parameters
    exact_fit_threshold: float = 0.01
    bow_stern_violation_threshold: int = 3
    symmetric_pair_min_threshold: float = 0.65
    mandatory_retry_increment: float = 0.01
    mandatory_max_relaxation: float = 0.35

@dataclass
class UIConfig:
    """Configuration for UI behavior"""
    auto_save_interval: int = 300  # seconds
    show_tooltips: bool = True
    animate_transitions: bool = True
    default_window_width: int = 1400
    default_window_height: int = 800
    remember_window_state: bool = True
    theme: str = "auto"  # auto, light, dark

@dataclass
class ValidationConfig:
    """Configuration for input validation"""
    min_tank_utilization: float = 0.65
    max_cargo_quantity: float = 1000000.0
    min_density: float = 0.01
    max_density: float = 10.0
    tank_name_max_length: int = 50
    cargo_type_max_length: int = 100

@dataclass
class AppConfig:
    """Main application configuration"""
    # Environment
    environment: Environment = Environment.DEVELOPMENT
    debug_mode: bool = False
    log_level: str = "INFO"
    
    # Paths
    data_directory: Optional[Path] = None
    backup_directory: Optional[Path] = None
    log_directory: Optional[Path] = None
    
    # Component configurations
    genetic_algorithm: GeneticAlgorithmConfig = field(default_factory=GeneticAlgorithmConfig)
    advanced_optimizer: AdvancedOptimizerConfig = field(default_factory=AdvancedOptimizerConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    validation: ValidationConfig = field(default_factory=ValidationConfig)
    
    # Runtime settings
    last_profile_id: Optional[str] = None
    recent_plans: List[str] = field(default_factory=list)
    optimization_algorithm: str = "genetic"  # Default algorithm
```

### 2. Configuration Manager

```python
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Type, TypeVar, Union
from dataclasses import asdict, is_dataclass

T = TypeVar('T')

class ConfigurationManager:
    """Centralized configuration management system"""
    
    def __init__(self, config_file: Optional[Path] = None):
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
        """Load configuration from file"""
        if self._config is None:
            self._config = self._load_from_file()
        return self._config
    
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
            return self._dict_to_config(data)
        
        except Exception as e:
            # Log error and return default
            print(f"Error loading config: {e}")
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
        """Save configuration to file"""
        try:
            # Ensure directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert to dictionary
            config_dict = asdict(config)
            
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
            print(f"Error saving config: {e}")
            return False
    
    def get_config_value(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value by dot-separated path"""
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
        """Set configuration value by dot-separated path"""
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
        """Add configuration change watcher"""
        self._watchers.append(callback)
    
    def remove_watcher(self, callback: Callable[[AppConfig], None]) -> None:
        """Remove configuration change watcher"""
        if callback in self._watchers:
            self._watchers.remove(callback)
    
    def _notify_watchers(self, config: AppConfig) -> None:
        """Notify all watchers of configuration change"""
        for watcher in self._watchers:
            try:
                watcher(config)
            except Exception as e:
                print(f"Error in config watcher: {e}")
```

### 3. Configuration Validation

```python
from typing import List, Tuple
from dataclasses import fields

class ConfigValidator:
    """Validates configuration values"""
    
    @staticmethod
    def validate_config(config: AppConfig) -> List[str]:
        """Validate entire configuration and return list of errors"""
        errors = []
        
        # Validate genetic algorithm config
        errors.extend(ConfigValidator._validate_genetic_config(config.genetic_algorithm))
        
        # Validate advanced optimizer config
        errors.extend(ConfigValidator._validate_advanced_config(config.advanced_optimizer))
        
        # Validate UI config
        errors.extend(ConfigValidator._validate_ui_config(config.ui))
        
        # Validate validation config (meta!)
        errors.extend(ConfigValidator._validate_validation_config(config.validation))
        
        return errors
    
    @staticmethod
    def _validate_genetic_config(config: GeneticAlgorithmConfig) -> List[str]:
        """Validate genetic algorithm configuration"""
        errors = []
        
        if config.population_size < 10 or config.population_size > 10000:
            errors.append("Genetic algorithm population size must be between 10 and 10000")
        
        if config.max_generations < 50 or config.max_generations > 10000:
            errors.append("Genetic algorithm max generations must be between 50 and 10000")
        
        if not 0.0 <= config.crossover_rate <= 1.0:
            errors.append("Genetic algorithm crossover rate must be between 0.0 and 1.0")
        
        if not 0.0 <= config.mutation_rate <= 1.0:
            errors.append("Genetic algorithm mutation rate must be between 0.0 and 1.0")
        
        if config.tournament_size < 2 or config.tournament_size > 20:
            errors.append("Genetic algorithm tournament size must be between 2 and 20")
        
        if config.elitism_count < 1 or config.elitism_count > 100:
            errors.append("Genetic algorithm elitism count must be between 1 and 100")
        
        return errors
    
    @staticmethod
    def _validate_advanced_config(config: AdvancedOptimizerConfig) -> List[str]:
        """Validate advanced optimizer configuration"""
        errors = []
        
        if not 0.1 <= config.min_utilization <= 1.0:
            errors.append("Minimum utilization must be between 0.1 and 1.0")
        
        if not 0.1 <= config.drag_drop_warning_threshold <= 1.0:
            errors.append("Drag drop warning threshold must be between 0.1 and 1.0")
        
        # Validate FAZ tolerances
        faz_tolerances = [
            (config.faz1_single_tank_tolerance, "FAZ1"),
            (config.faz2_two_tank_tolerance, "FAZ2"),
            (config.faz3_three_tank_tolerance, "FAZ3"),
            (config.faz4_four_tank_tolerance, "FAZ4"),
            (config.faz5_five_tank_tolerance, "FAZ5"),
            (config.faz6_six_tank_tolerance, "FAZ6")
        ]
        
        for tolerance, name in faz_tolerances:
            if not 0.01 <= tolerance <= 0.5:
                errors.append(f"{name} tolerance must be between 0.01 and 0.5")
        
        return errors
    
    @staticmethod
    def _validate_ui_config(config: UIConfig) -> List[str]:
        """Validate UI configuration"""
        errors = []
        
        if config.auto_save_interval < 60 or config.auto_save_interval > 3600:
            errors.append("Auto save interval must be between 60 and 3600 seconds")
        
        if config.default_window_width < 800 or config.default_window_width > 2560:
            errors.append("Default window width must be between 800 and 2560")
        
        if config.default_window_height < 600 or config.default_window_height > 1440:
            errors.append("Default window height must be between 600 and 1440")
        
        if config.theme not in ["auto", "light", "dark"]:
            errors.append("Theme must be one of: auto, light, dark")
        
        return errors
    
    @staticmethod
    def _validate_validation_config(config: ValidationConfig) -> List[str]:
        """Validate validation configuration"""
        errors = []
        
        if not 0.1 <= config.min_tank_utilization <= 1.0:
            errors.append("Minimum tank utilization must be between 0.1 and 1.0")
        
        if config.max_cargo_quantity <= 0:
            errors.append("Maximum cargo quantity must be positive")
        
        if not 0.01 <= config.min_density <= config.max_density:
            errors.append("Density range is invalid (min must be <= max)")
        
        return errors
```

### 4. Environment-Specific Configuration

```python
class EnvironmentConfigLoader:
    """Loads configuration based on environment"""
    
    @staticmethod
    def get_environment() -> Environment:
        """Detect current environment"""
        # Check environment variable
        env = os.getenv('STOWAGE_ENV', '').lower()
        
        if env == 'production':
            return Environment.PRODUCTION
        elif env == 'testing':
            return Environment.TESTING
        else:
            return Environment.DEVELOPMENT
    
    @staticmethod
    def get_config_for_environment() -> AppConfig:
        """Get configuration for current environment"""
        environment = EnvironmentConfigLoader.get_environment()
        
        # Start with base configuration
        config = AppConfig()
        config.environment = environment
        
        # Environment-specific overrides
        if environment == Environment.PRODUCTION:
            config.debug_mode = False
            config.log_level = "WARNING"
            config.ui.show_tooltips = False  # Reduce overhead in production
        elif environment == Environment.TESTING:
            config.debug_mode = True
            config.log_level = "DEBUG"
            config.genetic_algorithm.population_size = 100  # Smaller for faster tests
            config.genetic_algorithm.max_generations = 100
        else:  # DEVELOPMENT
            config.debug_mode = True
            config.log_level = "DEBUG"
            config.ui.animate_transitions = True
        
        return config
```

### 5. Migration Strategy

```python
class ConfigMigration:
    """Handles migration from old configuration format to new format"""
    
    def __init__(self, config_manager: ConfigurationManager):
        self.config_manager = config_manager
    
    def migrate_from_old_format(self) -> bool:
        """Migrate from existing scattered configuration"""
        try:
            # Load old optimization settings
            old_settings_path = self.config_manager.config_file.parent / "optimization_settings.json"
            
            if old_settings_path.exists():
                with open(old_settings_path, 'r') as f:
                    old_data = json.load(f)
                
                # Create new config from old data
                new_config = self._convert_old_to_new_config(old_data)
                
                # Validate new config
                errors = ConfigValidator.validate_config(new_config)
                if errors:
                    print(f"Migration validation errors: {errors}")
                    # Fix common issues automatically
                    new_config = self._auto_fix_migration_issues(new_config, errors)
                
                # Save new config
                if self.config_manager.save_config(new_config):
                    # Backup old file
                    backup_path = old_settings_path.with_suffix('.json.backup')
                    old_settings_path.rename(backup_path)
                    return True
            
            return False
        
        except Exception as e:
            print(f"Migration error: {e}")
            return False
    
    def _convert_old_to_new_config(self, old_data: Dict[str, Any]) -> AppConfig:
        """Convert old format to new AppConfig"""
        # Extract genetic algorithm settings
        ga_config = GeneticAlgorithmConfig(
            population_size=old_data.get('ga_population_size', 500),
            max_generations=old_data.get('ga_max_generations', 2000),
            crossover_rate=old_data.get('ga_crossover_rate', 0.90),
            mutation_rate=old_data.get('ga_mutation_rate', 0.11),
            tournament_size=old_data.get('ga_tournament_size', 3),
            use_elitism=old_data.get('ga_use_elitism', True),
            elitism_count=old_data.get('ga_elitism_count', 5),
            symmetry_penalty_coef=old_data.get('ga_symmetry_penalty_coef', 3000.0),
            trim_penalty_coef=old_data.get('ga_trim_penalty_coef', 1500.0),
            operational_penalty_coef=old_data.get('ga_operational_penalty_coef', 100.0),
            receiver_tolerance=old_data.get('ga_receiver_tolerance', 0.03),
            convergence_threshold=old_data.get('ga_convergence_threshold', 0.0001),
            convergence_generations=old_data.get('ga_convergence_generations', 60)
        )
        
        # Extract advanced optimizer settings
        advanced_config = AdvancedOptimizerConfig(
            min_utilization=old_data.get('min_utilization', 0.65),
            drag_drop_warning_threshold=old_data.get('drag_drop_warning_threshold', 0.70),
            score_weights=old_data.get('score_weights', {}),
            waste_utilization_weights=old_data.get('waste_utilization_weights', {}),
            exact_fit_threshold=old_data.get('exact_fit_threshold', 0.01),
            bow_stern_violation_threshold=old_data.get('bow_stern_violation_threshold', 3),
            symmetric_pair_min_threshold=old_data.get('symmetric_pair_min_threshold', 0.65),
            faz1_single_tank_tolerance=old_data.get('faz1_single_tank_tolerance', 0.05),
            faz2_two_tank_tolerance=old_data.get('faz2_two_tank_tolerance', 0.05),
            faz2_asymmetric_tolerance_factor=old_data.get('faz2_asymmetric_tolerance_factor', 0.2),
            faz3_three_tank_tolerance=old_data.get('faz3_three_tank_tolerance', 0.04),
            faz4_four_tank_tolerance=old_data.get('faz4_four_tank_tolerance', 0.04),
            faz5_five_tank_tolerance=old_data.get('faz5_five_tank_tolerance', 0.04),
            mandatory_retry_increment=old_data.get('mandatory_retry_increment', 0.01),
            mandatory_max_relaxation=old_data.get('mandatory_max_relaxation', 0.35)
        )
        
        # Create full config
        return AppConfig(
            environment=EnvironmentConfigLoader.get_environment(),
            genetic_algorithm=ga_config,
            advanced_optimizer=advanced_config,
            last_profile_id=old_data.get('last_profile_id'),
            recent_plans=old_data.get('recent_plans', []),
            optimization_algorithm=old_data.get('optimization_algorithm', 'genetic')
        )
    
    def _auto_fix_migration_issues(self, config: AppConfig, errors: List[str]) -> AppConfig:
        """Automatically fix common migration issues"""
        # Fix out-of-range values
        if config.genetic_algorithm.population_size > 5000:
            config.genetic_algorithm.population_size = 500
        
        if config.genetic_algorithm.max_generations > 5000:
            config.genetic_algorithm.max_generations = 2000
        
        # Fix invalid weights
        if config.advanced_optimizer.score_weights:
            total_weight = sum(config.advanced_optimizer.score_weights.values())
            if abs(total_weight - 1.0) > 0.01:
                # Normalize weights to sum to 1.0
                weights = config.advanced_optimizer.score_weights
                config.advanced_optimizer.score_weights = {
                    k: v / total_weight for k, v in weights.items()
                }
        
        return config
```

## Integration Points

### 1. MainWindow Integration

```python
# In ui/main_window.py

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Initialize configuration manager
        self.config_manager = ConfigurationManager()
        self.config = self.config_manager.load_config()
        
        # Watch for configuration changes
        self.config_manager.add_watcher(self.on_config_changed)
        
        # Initialize with config values
        self.optimization_settings = self._get_optimization_settings_from_config()
        
        # ... rest of initialization ...
    
    def _get_optimization_settings_from_config(self) -> Dict[str, Any]:
        """Extract optimization settings from centralized config"""
        ga_config = self.config.genetic_algorithm
        advanced_config = self.config.advanced_optimizer
        
        # Create settings dict in format expected by existing code
        settings = {
            'optimization_algorithm': self.config.optimization_algorithm,
            'min_utilization': advanced_config.min_utilization,
            'drag_drop_warning_threshold': advanced_config.drag_drop_warning_threshold,
            'ga_population_size': ga_config.population_size,
            'ga_max_generations': ga_config.max_generations,
            'ga_crossover_rate': ga_config.crossover_rate,
            'ga_mutation_rate': ga_config.mutation_rate,
            'ga_tournament_size': ga_config.tournament_size,
            'ga_use_elitism': ga_config.use_elitism,
            'ga_elitism_count': ga_config.elitism_count,
            'ga_symmetry_penalty_coef': ga_config.symmetry_penalty_coef,
            'ga_trim_penalty_coef': ga_config.trim_penalty_coef,
            'ga_operational_penalty_coef': ga_config.operational_penalty_coef,
            'ga_receiver_tolerance': ga_config.receiver_tolerance,
            'ga_convergence_threshold': ga_config.convergence_threshold,
            'ga_convergence_generations': ga_config.convergence_generations,
            # ... other settings
        }
        
        return settings
    
    def on_config_changed(self, new_config: AppConfig):
        """Handle configuration changes"""
        self.config = new_config
        self.optimization_settings = self._get_optimization_settings_from_config()
        
        # Update UI elements that depend on config
        self._update_ui_from_config()
    
    def open_optimization_settings(self):
        """Modified to use centralized config"""
        from ui.optimization_settings_dialog import OptimizationSettingsDialog
        
        dialog = OptimizationSettingsDialog(self, self.optimization_settings)
        if dialog.exec():
            # Get new settings
            new_settings = dialog.get_settings()
            
            # Update centralized config
            self._update_config_from_dialog_settings(new_settings)
            
            # Save configuration
            self.config_manager.save_config(self.config)
    
    def _update_config_from_dialog_settings(self, dialog_settings: Dict[str, Any]):
        """Update centralized config from dialog settings"""
        # Update genetic algorithm config
        ga_config = self.config.genetic_algorithm
        ga_config.population_size = dialog_settings.get('ga_population_size', ga_config.population_size)
        ga_config.max_generations = dialog_settings.get('ga_max_generations', ga_config.max_generations)
        # ... update other GA settings
        
        # Update advanced optimizer config
        advanced_config = self.config.advanced_optimizer
        advanced_config.min_utilization = dialog_settings.get('min_utilization', advanced_config.min_utilization)
        # ... update other advanced settings
        
        # Update algorithm selection
        self.config.optimization_algorithm = dialog_settings.get('optimization_algorithm', self.config.optimization_algorithm)
```

### 2. StorageManager Integration

```python
# In storage/storage_manager.py

class StorageManager:
    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir) if base_dir else get_base_dir()
        
        # Initialize configuration manager
        self.config_manager = ConfigurationManager()
        self.config = self.config_manager.load_config()
    
    def get_default_settings(self) -> Dict:
        """Get default settings from centralized config"""
        # Convert from AppConfig to old format for backward compatibility
        return {
            'optimization_algorithm': self.config.optimization_algorithm,
            'min_utilization': self.config.advanced_optimizer.min_utilization,
            'drag_drop_warning_threshold': self.config.advanced_optimizer.drag_drop_warning_threshold,
            'ga_population_size': self.config.genetic_algorithm.population_size,
            # ... convert all settings to old format
        }
    
    def save_optimization_settings(self, settings: Dict) -> bool:
        """Save optimization settings to centralized config"""
        # Update config from dialog settings
        self._update_config_from_dict(settings)
        return self.config_manager.save_config(self.config)
    
    def _update_config_from_dict(self, settings: Dict):
        """Update config from dictionary format"""
        # Update genetic algorithm settings
        if 'ga_population_size' in settings:
            self.config.genetic_algorithm.population_size = settings['ga_population_size']
        # ... update other settings
        
        # Update advanced optimizer settings
        if 'min_utilization' in settings:
            self.config.advanced_optimizer.min_utilization = settings['min_utilization']
        # ... update other settings
```

## Implementation Benefits

1. **Single Source of Truth**: All configuration in one place
2. **Type Safety**: Dataclasses with proper type annotations
3. **Validation**: Comprehensive validation of all configuration values
4. **Environment Support**: Different configs for development/production
5. **Migration**: Automatic migration from old format
6. **Extensibility**: Easy to add new configuration options
7. **Runtime Updates**: Configuration changes applied immediately

## Migration Strategy

1. Create new configuration infrastructure
2. Implement migration from existing JSON format
3. Update components to use ConfigurationManager
4. Maintain backward compatibility during transition
5. Add comprehensive validation
6. Test all configuration scenarios

## Testing Considerations

1. Test configuration loading/saving in all environments
2. Test validation with invalid values
3. Test migration from old format
4. Test configuration change notifications
5. Test default value handling