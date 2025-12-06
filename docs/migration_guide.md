# Configuration Migration Guide

This guide explains how to migrate from the existing scattered configuration system to the new centralized configuration management system.

## Overview

The new configuration system provides:
- Type-safe configuration with validation
- Environment-specific settings
- Centralized configuration management
- Automatic migration from existing settings
- Configuration change notifications

## Migration Steps

### 1. Backup Existing Configuration

Before starting the migration, create a backup of your existing configuration files:

```bash
# Create backup directory
mkdir -p config_backup

# Backup existing configuration files
cp storage/optimization_settings.json config_backup/
cp storage/ship_profiles_akin.json config_backup/
cp storage/ship_profiles.json config_backup/
```

### 2. Automatic Migration

The new system includes automatic migration capabilities:

```python
from core.config_manager import ConfigurationManager
from core.config_migration import ConfigMigration

# Initialize configuration manager
config_manager = ConfigurationManager()

# Run migration
migration = ConfigMigration(config_manager)
success = migration.migrate_from_old_format()

if success:
    print("Migration completed successfully")
else:
    print("Migration failed - check logs for details")
```

### 3. Manual Migration (if needed)

If automatic migration fails, you can manually migrate your settings:

#### Genetic Algorithm Settings

Old format (`storage/optimization_settings.json`):
```json
{
  "ga_population_size": 500,
  "ga_max_generations": 2000,
  "ga_crossover_rate": 0.90,
  "ga_mutation_rate": 0.11,
  "ga_tournament_size": 3,
  "ga_use_elitism": true,
  "ga_elitism_count": 5,
  "ga_symmetry_penalty_coef": 3000.0,
  "ga_trim_penalty_coef": 1500.0,
  "ga_operational_penalty_coef": 100.0,
  "ga_receiver_tolerance": 0.03,
  "ga_convergence_threshold": 0.0001,
  "ga_convergence_generations": 60
}
```

New format (`config/app_config.json`):
```json
{
  "environment": "production",
  "genetic_algorithm": {
    "population_size": 500,
    "max_generations": 2000,
    "crossover_rate": 0.90,
    "mutation_rate": 0.11,
    "tournament_size": 3,
    "use_elitism": true,
    "elitism_count": 5,
    "symmetry_penalty_coef": 3000.0,
    "trim_penalty_coef": 1500.0,
    "operational_penalty_coef": 100.0,
    "receiver_tolerance": 0.03,
    "convergence_threshold": 0.0001,
    "convergence_generations": 60
  },
  "advanced_optimizer": {
    // ... advanced optimizer settings
  },
  "app": {
    // ... application settings
  }
}
```

#### Advanced Optimizer Settings

The migration automatically converts all advanced optimizer settings from the old format to the new structure.

### 4. Validation

After migration, validate your configuration:

```python
from core.config_manager import ConfigurationManager
from core.config_validator import ConfigValidator

# Load and validate configuration
config_manager = ConfigurationManager()
config = config_manager.load_config()

# Validate
errors = ConfigValidator.validate_config(config)
if errors:
    print("Configuration validation errors:")
    for error in errors:
        print(f"  - {error}")
else:
    print("Configuration is valid")
```

### 5. Update Application Code

Update your application code to use the new configuration system:

#### Before (Old System)
```python
import json

# Load optimization settings
with open('storage/optimization_settings.json', 'r') as f:
    settings = json.load(f)

# Use settings
population_size = settings.get('ga_population_size', 500)
```

#### After (New System)
```python
from core.config_manager import ConfigurationManager

# Load configuration
config_manager = ConfigurationManager()
config = config_manager.get_config()

# Use settings
population_size = config.genetic_algorithm.population_size
```

### 6. Environment-Specific Configuration

Create environment-specific configuration files if needed:

```bash
# Development configuration
cp config/app_config.json config/app_config.development.json

# Production configuration
cp config/app_config.json config/app_config.production.json

# Edit environment-specific files as needed
```

## Configuration File Locations

### Old System
- `storage/optimization_settings.json` - Optimization parameters
- `storage/ship_profiles_akin.json` - Ship profiles
- `storage/ship_profiles.json` - Additional ship profiles

### New System
- `config/app_config.json` - Main configuration
- `config/app_config.development.json` - Development overrides
- `config/app_config.production.json` - Production overrides
- `config/app_config.test.json` - Test environment overrides

## Migration Troubleshooting

### Common Issues

#### 1. Invalid Configuration Values
**Problem**: Configuration values are outside valid ranges
**Solution**: The migration automatically fixes common issues, but you may need to manually adjust some values.

#### 2. Missing Configuration Files
**Problem**: Old configuration files don't exist
**Solution**: The system will create default configuration files.

#### 3. Permission Errors
**Problem**: Cannot write new configuration files
**Solution**: Ensure the application has write permissions to the config directory.

#### 4. JSON Syntax Errors
**Problem**: Old configuration files have invalid JSON
**Solution**: Fix JSON syntax errors in the original files before migration.

### Recovery

If migration fails, you can recover from the backup:

```bash
# Restore from backup
cp config_backup/optimization_settings.json storage/
cp config_backup/ship_profiles_akin.json storage/
cp config_backup/ship_profiles.json storage/
```

## Testing Migration

Test the migration process in a development environment before applying to production:

1. Create a test environment with your current configuration
2. Run the migration process
3. Validate the new configuration
4. Test application functionality
5. Verify optimization results match expected behavior

## Post-Migration Benefits

After migration, you'll have:

- **Type Safety**: All configuration is validated at runtime
- **Environment Support**: Different settings for development/production
- **Change Notifications**: Automatic updates when configuration changes
- **Validation**: Comprehensive validation of all configuration values
- **Documentation**: Self-documenting configuration structure
- **Maintainability**: Centralized configuration management

## Support

If you encounter issues during migration:

1. Check the application logs for detailed error messages
2. Validate your configuration using the built-in validator
3. Consult the configuration schema documentation
4. Restore from backup if necessary and try manual migration