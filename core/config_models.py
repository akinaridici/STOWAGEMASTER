"""Configuration data models with type safety and validation"""

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
    
    def validate(self) -> List[str]:
        """Validate genetic algorithm configuration
        
        Returns:
            List of validation error messages
        """
        errors = []
        
        if self.population_size < 10 or self.population_size > 10000:
            errors.append("Genetic algorithm population size must be between 10 and 10000")
        
        if self.max_generations < 50 or self.max_generations > 10000:
            errors.append("Genetic algorithm max generations must be between 50 and 10000")
        
        if not 0.0 <= self.crossover_rate <= 1.0:
            errors.append("Genetic algorithm crossover rate must be between 0.0 and 1.0")
        
        if not 0.0 <= self.mutation_rate <= 1.0:
            errors.append("Genetic algorithm mutation rate must be between 0.0 and 1.0")
        
        if self.tournament_size < 2 or self.tournament_size > 20:
            errors.append("Genetic algorithm tournament size must be between 2 and 20")
        
        if self.elitism_count < 1 or self.elitism_count > 100:
            errors.append("Genetic algorithm elitism count must be between 1 and 100")
        
        return errors


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
    
    def validate(self) -> List[str]:
        """Validate advanced optimizer configuration
        
        Returns:
            List of validation error messages
        """
        errors = []
        
        if not 0.1 <= self.min_utilization <= 1.0:
            errors.append("Minimum utilization must be between 0.1 and 1.0")
        
        if not 0.1 <= self.drag_drop_warning_threshold <= 1.0:
            errors.append("Drag drop warning threshold must be between 0.1 and 1.0")
        
        # Validate FAZ tolerances
        faz_tolerances = [
            (self.faz1_single_tank_tolerance, "FAZ1"),
            (self.faz2_two_tank_tolerance, "FAZ2"),
            (self.faz3_three_tank_tolerance, "FAZ3"),
            (self.faz4_four_tank_tolerance, "FAZ4"),
            (self.faz5_five_tank_tolerance, "FAZ5"),
            (self.faz6_six_tank_tolerance, "FAZ6")
        ]
        
        for tolerance, name in faz_tolerances:
            if not 0.01 <= tolerance <= 0.5:
                errors.append(f"{name} tolerance must be between 0.01 and 0.5")
        
        # Validate score weights sum to 1.0
        total_weight = sum(self.score_weights.values())
        if abs(total_weight - 1.0) > 0.01:
            errors.append("Score weights must sum to 1.0")
        
        return errors


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
    
    def validate(self) -> List[str]:
        """Validate UI configuration
        
        Returns:
            List of validation error messages
        """
        errors = []
        
        if self.auto_save_interval < 60 or self.auto_save_interval > 3600:
            errors.append("Auto save interval must be between 60 and 3600 seconds")
        
        if self.default_window_width < 800 or self.default_window_width > 2560:
            errors.append("Default window width must be between 800 and 2560")
        
        if self.default_window_height < 600 or self.default_window_height > 1440:
            errors.append("Default window height must be between 600 and 1440")
        
        if self.theme not in ["auto", "light", "dark"]:
            errors.append("Theme must be one of: auto, light, dark")
        
        return errors


@dataclass
class ValidationConfig:
    """Configuration for input validation"""
    min_tank_utilization: float = 0.65
    max_cargo_quantity: float = 1000000.0
    min_density: float = 0.01
    max_density: float = 10.0
    tank_name_max_length: int = 50
    cargo_type_max_length: int = 100
    
    def validate(self) -> List[str]:
        """Validate validation configuration
        
        Returns:
            List of validation error messages
        """
        errors = []
        
        if not 0.1 <= self.min_tank_utilization <= 1.0:
            errors.append("Minimum tank utilization must be between 0.1 and 1.0")
        
        if self.max_cargo_quantity <= 0:
            errors.append("Maximum cargo quantity must be positive")
        
        if not 0.01 <= self.min_density <= self.max_density:
            errors.append("Density range is invalid (min must be <= max)")
        
        if self.tank_name_max_length < 1 or self.tank_name_max_length > 100:
            errors.append("Tank name max length must be between 1 and 100")
        
        if self.cargo_type_max_length < 1 or self.cargo_type_max_length > 200:
            errors.append("Cargo type max length must be between 1 and 200")
        
        return errors


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
    
    def validate(self) -> List[str]:
        """Validate entire application configuration
        
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Validate component configurations
        errors.extend(self.genetic_algorithm.validate())
        errors.extend(self.advanced_optimizer.validate())
        errors.extend(self.ui.validate())
        errors.extend(self.validation.validate())
        
        # Validate runtime settings
        if self.optimization_algorithm not in ["genetic", "advanced"]:
            errors.append("Optimization algorithm must be 'genetic' or 'advanced'")
        
        return errors
    
    def to_dict(self) -> Dict:
        """Convert configuration to dictionary for JSON serialization
        
        Returns:
            Dictionary representation of configuration
        """
        return {
            'environment': self.environment.value,
            'debug_mode': self.debug_mode,
            'log_level': self.log_level,
            'data_directory': str(self.data_directory) if self.data_directory else None,
            'backup_directory': str(self.backup_directory) if self.backup_directory else None,
            'log_directory': str(self.log_directory) if self.log_directory else None,
            'genetic_algorithm': {
                'population_size': self.genetic_algorithm.population_size,
                'max_generations': self.genetic_algorithm.max_generations,
                'crossover_rate': self.genetic_algorithm.crossover_rate,
                'mutation_rate': self.genetic_algorithm.mutation_rate,
                'tournament_size': self.genetic_algorithm.tournament_size,
                'use_elitism': self.genetic_algorithm.use_elitism,
                'elitism_count': self.genetic_algorithm.elitism_count,
                'symmetry_penalty_coef': self.genetic_algorithm.symmetry_penalty_coef,
                'trim_penalty_coef': self.genetic_algorithm.trim_penalty_coef,
                'operational_penalty_coef': self.genetic_algorithm.operational_penalty_coef,
                'receiver_tolerance': self.genetic_algorithm.receiver_tolerance,
                'convergence_threshold': self.genetic_algorithm.convergence_threshold,
                'convergence_generations': self.genetic_algorithm.convergence_generations
            },
            'advanced_optimizer': {
                'min_utilization': self.advanced_optimizer.min_utilization,
                'drag_drop_warning_threshold': self.advanced_optimizer.drag_drop_warning_threshold,
                'score_weights': self.advanced_optimizer.score_weights,
                'waste_utilization_weights': self.advanced_optimizer.waste_utilization_weights,
                'exact_fit_threshold': self.advanced_optimizer.exact_fit_threshold,
                'bow_stern_violation_threshold': self.advanced_optimizer.bow_stern_violation_threshold,
                'symmetric_pair_min_threshold': self.advanced_optimizer.symmetric_pair_min_threshold,
                'faz1_single_tank_tolerance': self.advanced_optimizer.faz1_single_tank_tolerance,
                'faz2_two_tank_tolerance': self.advanced_optimizer.faz2_two_tank_tolerance,
                'faz2_asymmetric_tolerance_factor': self.advanced_optimizer.faz2_asymmetric_tolerance_factor,
                'faz3_three_tank_tolerance': self.advanced_optimizer.faz3_three_tank_tolerance,
                'faz4_four_tank_tolerance': self.advanced_optimizer.faz4_four_tank_tolerance,
                'faz5_five_tank_tolerance': self.advanced_optimizer.faz5_five_tank_tolerance,
                'faz6_six_tank_tolerance': self.advanced_optimizer.faz6_six_tank_tolerance,
                'mandatory_retry_increment': self.advanced_optimizer.mandatory_retry_increment,
                'mandatory_max_relaxation': self.advanced_optimizer.mandatory_max_relaxation
            },
            'ui': {
                'auto_save_interval': self.ui.auto_save_interval,
                'show_tooltips': self.ui.show_tooltips,
                'animate_transitions': self.ui.animate_transitions,
                'default_window_width': self.ui.default_window_width,
                'default_window_height': self.ui.default_window_height,
                'remember_window_state': self.ui.remember_window_state,
                'theme': self.ui.theme
            },
            'validation': {
                'min_tank_utilization': self.validation.min_tank_utilization,
                'max_cargo_quantity': self.validation.max_cargo_quantity,
                'min_density': self.validation.min_density,
                'max_density': self.validation.max_density,
                'tank_name_max_length': self.validation.tank_name_max_length,
                'cargo_type_max_length': self.validation.cargo_type_max_length
            },
            'last_profile_id': self.last_profile_id,
            'recent_plans': self.recent_plans,
            'optimization_algorithm': self.optimization_algorithm
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AppConfig':
        """Create AppConfig from dictionary
        
        Args:
            data: Dictionary representation of configuration
            
        Returns:
            AppConfig instance
        """
        # Extract genetic algorithm config
        ga_data = data.get('genetic_algorithm', {})
        genetic_algorithm = GeneticAlgorithmConfig(
            population_size=ga_data.get('population_size', 500),
            max_generations=ga_data.get('max_generations', 2000),
            crossover_rate=ga_data.get('crossover_rate', 0.90),
            mutation_rate=ga_data.get('mutation_rate', 0.11),
            tournament_size=ga_data.get('tournament_size', 3),
            use_elitism=ga_data.get('use_elitism', True),
            elitism_count=ga_data.get('elitism_count', 5),
            symmetry_penalty_coef=ga_data.get('symmetry_penalty_coef', 3000.0),
            trim_penalty_coef=ga_data.get('trim_penalty_coef', 1500.0),
            operational_penalty_coef=ga_data.get('operational_penalty_coef', 100.0),
            receiver_tolerance=ga_data.get('receiver_tolerance', 0.03),
            convergence_threshold=ga_data.get('convergence_threshold', 0.0001),
            convergence_generations=ga_data.get('convergence_generations', 60)
        )
        
        # Extract advanced optimizer config
        advanced_data = data.get('advanced_optimizer', {})
        advanced_optimizer = AdvancedOptimizerConfig(
            min_utilization=advanced_data.get('min_utilization', 0.65),
            drag_drop_warning_threshold=advanced_data.get('drag_drop_warning_threshold', 0.70),
            score_weights=advanced_data.get('score_weights', {}),
            waste_utilization_weights=advanced_data.get('waste_utilization_weights', {}),
            exact_fit_threshold=advanced_data.get('exact_fit_threshold', 0.01),
            bow_stern_violation_threshold=advanced_data.get('bow_stern_violation_threshold', 3),
            symmetric_pair_min_threshold=advanced_data.get('symmetric_pair_min_threshold', 0.65),
            faz1_single_tank_tolerance=advanced_data.get('faz1_single_tank_tolerance', 0.05),
            faz2_two_tank_tolerance=advanced_data.get('faz2_two_tank_tolerance', 0.05),
            faz2_asymmetric_tolerance_factor=advanced_data.get('faz2_asymmetric_tolerance_factor', 0.2),
            faz3_three_tank_tolerance=advanced_data.get('faz3_three_tank_tolerance', 0.04),
            faz4_four_tank_tolerance=advanced_data.get('faz4_four_tank_tolerance', 0.04),
            faz5_five_tank_tolerance=advanced_data.get('faz5_five_tank_tolerance', 0.04),
            faz6_six_tank_tolerance=advanced_data.get('faz6_six_tank_tolerance', 0.05),
            mandatory_retry_increment=advanced_data.get('mandatory_retry_increment', 0.01),
            mandatory_max_relaxation=advanced_data.get('mandatory_max_relaxation', 0.35)
        )
        
        # Extract UI config
        ui_data = data.get('ui', {})
        ui = UIConfig(
            auto_save_interval=ui_data.get('auto_save_interval', 300),
            show_tooltips=ui_data.get('show_tooltips', True),
            animate_transitions=ui_data.get('animate_transitions', True),
            default_window_width=ui_data.get('default_window_width', 1400),
            default_window_height=ui_data.get('default_window_height', 800),
            remember_window_state=ui_data.get('remember_window_state', True),
            theme=ui_data.get('theme', 'auto')
        )
        
        # Extract validation config
        validation_data = data.get('validation', {})
        validation = ValidationConfig(
            min_tank_utilization=validation_data.get('min_tank_utilization', 0.65),
            max_cargo_quantity=validation_data.get('max_cargo_quantity', 1000000.0),
            min_density=validation_data.get('min_density', 0.01),
            max_density=validation_data.get('max_density', 10.0),
            tank_name_max_length=validation_data.get('tank_name_max_length', 50),
            cargo_type_max_length=validation_data.get('cargo_type_max_length', 100)
        )
        
        # Extract environment
        env_str = data.get('environment', 'development')
        environment = Environment(env_str) if env_str in [e.value for e in Environment] else Environment.DEVELOPMENT
        
        return cls(
            environment=environment,
            debug_mode=data.get('debug_mode', False),
            log_level=data.get('log_level', 'INFO'),
            data_directory=Path(data.get('data_directory')) if data.get('data_directory') else None,
            backup_directory=Path(data.get('backup_directory')) if data.get('backup_directory') else None,
            log_directory=Path(data.get('log_directory')) if data.get('log_directory') else None,
            genetic_algorithm=genetic_algorithm,
            advanced_optimizer=advanced_optimizer,
            ui=ui,
            validation=validation,
            last_profile_id=data.get('last_profile_id'),
            recent_plans=data.get('recent_plans', []),
            optimization_algorithm=data.get('optimization_algorithm', 'genetic')
        )