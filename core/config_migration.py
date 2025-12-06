"""Configuration migration utilities"""

import json
from typing import Dict, Any
from .config_models import AppConfig, GeneticAlgorithmConfig, AdvancedOptimizerConfig, Environment
from .config_manager import ConfigurationManager


class ConfigMigration:
    """Handles migration from old configuration format to new format"""
    
    def __init__(self, config_manager: ConfigurationManager):
        """Initialize migration utility
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
    
    def migrate_from_old_format(self) -> bool:
        """Migrate from existing scattered configuration
        
        Returns:
            True if migration successful, False otherwise
        """
        try:
            # Load old optimization settings
            old_settings_path = self.config_manager.config_file.parent / "optimization_settings.json"
            
            if old_settings_path.exists():
                with open(old_settings_path, 'r') as f:
                    old_data = json.load(f)
                
                # Create new config from old data
                new_config = self._convert_old_to_new_config(old_data)
                
                # Validate new config
                from .config_validator import ConfigValidator
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
                    print(f"Migration completed. Old config backed up to: {backup_path}")
                    return True
                else:
                    print("Failed to save new configuration")
                    return False
            else:
                print("No old configuration file found")
                return False
        
        except Exception as e:
            print(f"Migration error: {e}")
            return False
    
    def _convert_old_to_new_config(self, old_data: Dict[str, Any]) -> AppConfig:
        """Convert old format to new AppConfig
        
        Args:
            old_data: Old configuration data
            
        Returns:
            AppConfig instance with converted data
        """
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
            faz6_six_tank_tolerance=old_data.get('faz6_six_tank_tolerance', 0.05),
            mandatory_retry_increment=old_data.get('mandatory_retry_increment', 0.01),
            mandatory_max_relaxation=old_data.get('mandatory_max_relaxation', 0.35)
        )
        
        # Create full config
        return AppConfig(
            environment=Environment(old_data.get('environment', 'development')),
            genetic_algorithm=ga_config,
            advanced_optimizer=advanced_config,
            last_profile_id=old_data.get('last_profile_id'),
            recent_plans=old_data.get('recent_plans', []),
            optimization_algorithm=old_data.get('optimization_algorithm', 'genetic')
        )
    
    def _auto_fix_migration_issues(self, config: AppConfig, errors: list) -> AppConfig:
        """Automatically fix common migration issues
        
        Args:
            config: Configuration with potential issues
            errors: List of validation errors
            
        Returns:
            Fixed configuration
        """
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
