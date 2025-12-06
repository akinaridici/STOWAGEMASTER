"""Configuration validation system"""

from typing import List

from .config_models import (
    AppConfig, GeneticAlgorithmConfig, AdvancedOptimizerConfig, 
    UIConfig, ValidationConfig
)


class ConfigValidator:
    """Validates configuration values"""
    
    @staticmethod
    def validate_config(config: AppConfig) -> List[str]:
        """Validate entire application configuration
        
        Args:
            config: Configuration to validate
            
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Validate component configurations
        errors.extend(ConfigValidator._validate_genetic_config(config.genetic_algorithm))
        errors.extend(ConfigValidator._validate_advanced_config(config.advanced_optimizer))
        errors.extend(ConfigValidator._validate_ui_config(config.ui))
        errors.extend(ConfigValidator._validate_validation_config(config.validation))
        
        # Validate runtime settings
        errors.extend(ConfigValidator._validate_runtime_settings(config))
        
        return errors
    
    @staticmethod
    def _validate_genetic_config(config: GeneticAlgorithmConfig) -> List[str]:
        """Validate genetic algorithm configuration
        
        Args:
            config: Genetic algorithm configuration
            
        Returns:
            List of validation error messages
        """
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
        
        if config.symmetry_penalty_coef < 0 or config.symmetry_penalty_coef > 10000.0:
            errors.append("Genetic algorithm symmetry penalty coefficient must be between 0 and 10000")
        
        if config.trim_penalty_coef < 0 or config.trim_penalty_coef > 10000.0:
            errors.append("Genetic algorithm trim penalty coefficient must be between 0 and 10000")
        
        if config.operational_penalty_coef < 0 or config.operational_penalty_coef > 10000.0:
            errors.append("Genetic algorithm operational penalty coefficient must be between 0 and 10000")
        
        if not 0.001 <= config.receiver_tolerance <= 0.20:
            errors.append("Genetic algorithm receiver tolerance must be between 0.001 and 0.20")
        
        if config.convergence_threshold < 0.00001 or config.convergence_threshold > 0.01:
            errors.append("Genetic algorithm convergence threshold must be between 0.00001 and 0.01")
        
        if config.convergence_generations < 10 or config.convergence_generations > 200:
            errors.append("Genetic algorithm convergence generations must be between 10 and 200")
        
        return errors
    
    @staticmethod
    def _validate_advanced_config(config: AdvancedOptimizerConfig) -> List[str]:
        """Validate advanced optimizer configuration
        
        Args:
            config: Advanced optimizer configuration
            
        Returns:
            List of validation error messages
        """
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
            if not 0.001 <= tolerance <= 0.5:
                errors.append(f"{name} tolerance must be between 0.001 and 0.5")
        
        # Validate score weights sum to 1.0
        total_weight = sum(config.score_weights.values())
        if abs(total_weight - 1.0) > 0.01:
            errors.append("Score weights must sum to 1.0")
        
        # Validate individual score weights
        for weight_name, weight_value in config.score_weights.items():
            if not 0.0 <= weight_value <= 1.0:
                errors.append(f"Score weight '{weight_name}' must be between 0.0 and 1.0")
        
        # Validate waste/utilization weights sum to 1.0
        total_waste_weight = sum(config.waste_utilization_weights.values())
        if abs(total_waste_weight - 1.0) > 0.01:
            errors.append("Waste/utilization weights must sum to 1.0")
        
        # Validate individual waste/utilization weights
        for weight_name, weight_value in config.waste_utilization_weights.items():
            if not 0.0 <= weight_value <= 1.0:
                errors.append(f"Waste/utilization weight '{weight_name}' must be between 0.0 and 1.0")
        
        if not 0.001 <= config.exact_fit_threshold <= 0.1:
            errors.append("Exact fit threshold must be between 0.001 and 0.1")
        
        if config.bow_stern_violation_threshold < 1 or config.bow_stern_violation_threshold > 10:
            errors.append("Bow/stern violation threshold must be between 1 and 10")
        
        if not 0.1 <= config.symmetric_pair_min_threshold <= 1.0:
            errors.append("Symmetric pair minimum threshold must be between 0.1 and 1.0")
        
        if not 0.001 <= config.mandatory_retry_increment <= 0.1:
            errors.append("Mandatory retry increment must be between 0.001 and 0.1")
        
        if not 0.01 <= config.mandatory_max_relaxation <= 1.0:
            errors.append("Mandatory max relaxation must be between 0.01 and 1.0")
        
        return errors
    
    @staticmethod
    def _validate_ui_config(config: UIConfig) -> List[str]:
        """Validate UI configuration
        
        Args:
            config: UI configuration
            
        Returns:
            List of validation error messages
        """
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
        """Validate validation configuration
        
        Args:
            config: Validation configuration
            
        Returns:
            List of validation error messages
        """
        errors = []
        
        if not 0.1 <= config.min_tank_utilization <= 1.0:
            errors.append("Minimum tank utilization must be between 0.1 and 1.0")
        
        if config.max_cargo_quantity <= 0:
            errors.append("Maximum cargo quantity must be positive")
        
        if not 0.001 <= config.min_density <= config.max_density:
            errors.append("Density range is invalid (min must be <= max)")
        
        if config.tank_name_max_length < 1 or config.tank_name_max_length > 100:
            errors.append("Tank name max length must be between 1 and 100")
        
        if config.cargo_type_max_length < 1 or config.cargo_type_max_length > 200:
            errors.append("Cargo type max length must be between 1 and 200")
        
        return errors
    
    @staticmethod
    def _validate_runtime_settings(config: AppConfig) -> List[str]:
        """Validate runtime settings
        
        Args:
            config: Application configuration
            
        Returns:
            List of validation error messages
        """
        errors = []
        
        if config.optimization_algorithm not in ["genetic", "advanced"]:
            errors.append("Optimization algorithm must be 'genetic' or 'advanced'")
        
        return errors
    
    @staticmethod
    def get_validation_summary(config: AppConfig) -> str:
        """Get a user-friendly validation summary
        
        Args:
            config: Configuration to validate
            
        Returns:
            Formatted validation summary
        """
        errors = ConfigValidator.validate_config(config)
        
        if not errors:
            return "Configuration is valid ✓"
        
        summary = "Configuration validation found issues:\n\n"
        for error in errors:
            summary += f"• {error}\n"
        
        return summary