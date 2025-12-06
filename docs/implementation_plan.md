# Implementation Plan: Progress Indicators and Configuration Management

## Overview
This document outlines the implementation plan for adding progress indicators and centralized configuration management to the Tanker Stowage Plan application.

## Implementation Phases

### Phase 1: Infrastructure Setup (Week 1)

#### 1.1 Create Core Components
- [ ] Create `core/` directory for new infrastructure
- [ ] Implement `core/progress_reporter.py` - Progress reporting interface
- [ ] Implement `core/config_manager.py` - Centralized configuration system
- [ ] Implement `core/config_models.py` - Configuration dataclasses
- [ ] Implement `core/config_validator.py` - Configuration validation

#### 1.2 Create Progress Dialog
- [ ] Implement `ui/progress_dialog.py` - Progress indication dialog
- [ ] Add cancellation support
- [ ] Add detailed progress logging
- [ ] Implement dark/light theme support

#### 1.3 Create Threading Support
- [ ] Implement `core/optimization_worker.py` - Threaded optimization wrapper
- [ ] Implement `core/thread_progress_reporter.py` - Thread-safe progress reporting
- [ ] Add proper error handling for threaded operations

### Phase 2: Configuration System Implementation (Week 2)

#### 2.1 Configuration Data Models
- [ ] Create all configuration dataclasses with proper typing
- [ ] Add validation methods to each dataclass
- [ ] Implement serialization/deserialization
- [ ] Add environment-specific defaults

#### 2.2 Configuration Manager
- [ ] Implement file-based configuration loading/saving
- [ ] Add configuration change notifications
- [ ] Implement environment detection
- [ ] Add configuration migration utilities

#### 2.3 Configuration Validation
- [ ] Implement comprehensive validation rules
- [ ] Add validation error reporting
- [ ] Create validation tests
- [ ] Add auto-fix for common issues

### Phase 3: Algorithm Integration (Week 3)

#### 3.1 Genetic Algorithm Integration
- [ ] Modify `optimizer/genetic_optimizer.py` to accept ProgressReporter
- [ ] Add progress reporting at key points:
  - Initialization
  - Population creation
  - Each generation (every 10%)
  - Convergence detection
  - Final plan creation
- [ ] Implement cancellation checks throughout algorithm
- [ ] Add subtask reporting for complex operations

#### 3.2 Advanced Optimizer Integration
- [ ] Modify `optimizer/advanced_optimizer.py` to accept ProgressReporter
- [ ] Add progress reporting for each FAZ phase:
  - FAZ 0: Mandatory cargo placement
  - FAZ 1: Single tank fitting
  - FAZ 2: Two tank fitting
  - FAZ 3-7: Multi-tank fitting
  - Final scoring
- [ ] Implement phase weighting for overall progress
- [ ] Add detailed subtask reporting

#### 3.3 Basic Optimizer Integration
- [ ] Modify `optimizer/stowage_optimizer.py` for basic progress
- [ ] Add progress reporting for strategy selection
- [ ] Implement progress for multiple solution generation

### Phase 4: UI Integration (Week 4)

#### 4.1 MainWindow Updates
- [ ] Modify `ui/main_window.py` to use ConfigurationManager
- [ ] Replace direct settings access with config manager calls
- [ ] Add configuration change handlers
- [ ] Implement threaded optimization with progress dialog

#### 4.2 Settings Dialog Updates
- [ ] Modify `ui/optimization_settings_dialog.py` to use new config
- [ ] Add validation feedback
- [ ] Implement real-time configuration updates
- [ ] Add reset to defaults with confirmation

#### 4.3 Other UI Components
- [ ] Update `ui/cargo_input_dialog.py` to use validation config
- [ ] Update `ui/plan_selection_dialog.py` for progress context
- [ ] Add configuration-related menu items
- [ ] Implement configuration backup/restore

### Phase 5: Migration and Testing (Week 5)

#### 5.1 Migration Implementation
- [ ] Implement `core/config_migration.py`
- [ ] Add migration from current JSON format
- [ ] Create backup of old configuration
- [ ] Add migration validation and rollback
- [ ] Implement migration logging

#### 5.2 Testing Framework
- [ ] Create unit tests for configuration system
- [ ] Create unit tests for progress reporting
- [ ] Create integration tests for threaded optimization
- [ ] Create UI tests for configuration changes
- [ ] Create performance tests for large configurations

#### 5.3 Documentation
- [ ] Update README.md with new features
- [ ] Create configuration guide for users
- [ ] Document migration process
- [ ] Add troubleshooting section
- [ ] Create developer documentation

## Implementation Details

### Progress Reporting Integration Points

#### Genetic Algorithm
```python
# Key integration points in optimize() method:
1. After mandatory placement (10% progress)
2. After population initialization (20% progress)
3. Every 100 generations (30-70% progress)
4. After convergence detection (80% progress)
5. During final plan creation (90% progress)
6. After post-processing (100% progress)
```

#### Advanced Optimizer
```python
# Phase-based progress distribution:
- FAZ 0 (Mandatory): 10% of total progress
- FAZ 1 (Single): 10% of total progress
- FAZ 2 (Two): 10% of total progress
- FAZ 3 (Three): 10% of total progress
- FAZ 4 (Four): 15% of total progress (more complex)
- FAZ 5 (Five): 15% of total progress (more complex)
- FAZ 6 (Six): 10% of total progress
- FAZ 7 (Multi): 10% of total progress
- Final scoring: 5% of total progress
```

### Configuration Migration Mapping

#### From Old JSON to New AppConfig
```python
# Mapping of old keys to new structure:
{
    # Genetic Algorithm
    "ga_population_size": "genetic_algorithm.population_size",
    "ga_max_generations": "genetic_algorithm.max_generations",
    "ga_crossover_rate": "genetic_algorithm.crossover_rate",
    # ... other GA settings
    
    # Advanced Optimizer
    "min_utilization": "advanced_optimizer.min_utilization",
    "drag_drop_warning_threshold": "advanced_optimizer.drag_drop_warning_threshold",
    "faz1_single_tank_tolerance": "advanced_optimizer.faz1_single_tank_tolerance",
    # ... other FAZ settings
    
    # UI Settings
    "last_profile_id": "last_profile_id",
    "recent_plans": "recent_plans",
    # ... other UI settings
}
```

## File Structure Changes

### New Files to Create
```
core/
├── __init__.py
├── progress_reporter.py          # Progress reporting interface
├── config_manager.py            # Centralized configuration
├── config_models.py             # Configuration dataclasses
├── config_validator.py          # Configuration validation
├── config_migration.py          # Migration utilities
├── optimization_worker.py       # Threading support
└── thread_progress_reporter.py # Thread-safe progress

ui/
├── progress_dialog.py           # Progress indication dialog
└── [existing files modified]

tests/
├── __init__.py
├── test_config_manager.py      # Configuration tests
├── test_progress_reporter.py  # Progress reporting tests
├── test_optimization_worker.py # Threading tests
└── test_integration.py         # Integration tests

docs/
├── configuration_guide.md       # User configuration guide
├── migration_guide.md          # Migration documentation
└── developer_guide.md          # Developer documentation
```

### Files to Modify
```
ui/main_window.py                # Add configuration manager, progress dialog
ui/optimization_settings_dialog.py # Use centralized config
optimizer/genetic_optimizer.py     # Add progress reporting
optimizer/advanced_optimizer.py    # Add progress reporting
optimizer/stowage_optimizer.py      # Add basic progress
storage/storage_manager.py          # Use centralized config
```

## Risk Mitigation

### Technical Risks
1. **Thread Safety**: Ensure all progress reporting is thread-safe
2. **Memory Usage**: Monitor memory usage during long optimizations
3. **UI Responsiveness**: Test with very large cargo sets
4. **Configuration Loss**: Implement automatic backup before migration

### User Experience Risks
1. **Confusion**: Clear migration documentation needed
2. **Performance**: Progress reporting shouldn't slow down optimization
3. **Compatibility**: Ensure old configurations still work

### Migration Risks
1. **Data Loss**: Multiple backup strategies
2. **Invalid Migration**: Comprehensive validation
3. **Rollback Issues**: Keep old file until successful migration

## Success Criteria

### Progress Indicators
- [ ] Optimization operations show progress dialog
- [ ] Users can cancel long-running operations
- [ ] Progress accurately reflects operation state
- [ ] UI remains responsive during optimization
- [ ] Cancellation properly cleans up resources

### Configuration Management
- [ ] All settings accessible through centralized system
- [ ] Configuration changes applied immediately
- [ ] Invalid configurations rejected with helpful errors
- [ ] Migration from old format works seamlessly
- [ ] Environment-specific configurations supported

## Timeline

### Week 1: Infrastructure
- Days 1-2: Create core components
- Day 3: Implement progress dialog
- Day 4: Add threading support
- Day 5: Test basic functionality

### Week 2: Configuration System
- Days 1-2: Implement configuration models
- Day 3: Create configuration manager
- Day 4: Add validation system
- Day 5: Test configuration functionality

### Week 3: Algorithm Integration
- Days 1-2: Modify genetic algorithm
- Days 3-4: Modify advanced optimizer
- Day 5: Update basic optimizer
- Weekend: Test optimization with progress

### Week 4: UI Integration
- Days 1-2: Update MainWindow
- Days 3-4: Update settings dialog
- Day 5: Update other UI components
- Weekend: Test UI integration

### Week 5: Migration and Testing
- Days 1-2: Implement migration
- Days 3-4: Create test suite
- Day 5: Final testing and documentation
- Weekend: Code review and deployment preparation

## Next Steps

1. Review and approve this implementation plan
2. Create detailed task breakdown for Phase 1
3. Set up development environment with proper branching
4. Begin implementation of core infrastructure components
5. Establish testing framework early in the process

## Dependencies

### External Dependencies
- No new external dependencies required
- Using only Python standard library and PyQt6

### Internal Dependencies
- Existing model classes (Ship, Cargo, StowagePlan)
- Existing optimization algorithms
- PyQt6 threading and signal/slot mechanism

## Code Quality Standards

### Documentation Requirements
- All new classes must have comprehensive docstrings
- Complex algorithms need inline comments
- Configuration options need user-friendly descriptions

### Testing Requirements
- Minimum 80% code coverage for new components
- Integration tests for all major workflows
- Performance tests for large datasets

### Error Handling Requirements
- Graceful degradation for non-critical errors
- User-friendly error messages
- Comprehensive logging for debugging

This implementation plan provides a structured approach to adding progress indicators and centralized configuration management while maintaining the existing functionality and improving the overall user experience.