# Architecture Diagrams

## Progress Indicator Architecture

```mermaid
graph TD
    A[MainWindow] --> B[OptimizationWorker]
    B --> C[ProgressReporter Interface]
    B --> D[Genetic Algorithm]
    B --> E[Advanced Optimizer]
    
    C --> F[ThreadProgressReporter]
    F --> G[Progress Dialog]
    
    D --> H[GA Progress Reporting]
    E --> I[FAZ Progress Reporting]
    
    G --> J[Progress Bar]
    G --> K[Stage Label]
    G --> L[Details Log]
    G --> M[Cancel Button]
    
    subgraph "Progress Stages"
        N[Initialization]
        O[Mandatory Placement]
        P[FAZ 1: Single Tank]
        Q[FAZ 2: Two Tank]
        R[FAZ 3: Three Tank]
        S[FAZ 4: Four Tank]
        T[FAZ 5: Five Tank]
        U[FAZ 6: Six Tank]
        V[FAZ 7: Multi Tank]
        W[Finalization]
        X[Scoring]
    end
    
    H --> N
    H --> O
    H --> P
    H --> Q
    H --> R
    H --> S
    H --> T
    H --> U
    H --> V
    H --> W
    H --> X
    
    I --> N
    I --> O
    I --> P
    I --> Q
    I --> R
    I --> S
    I --> T
    I --> U
    I --> V
    I --> W
    I --> X
```

## Configuration Management Architecture

```mermaid
graph TD
    A[AppConfig] --> B[GeneticAlgorithmConfig]
    A --> C[AdvancedOptimizerConfig]
    A --> D[UIConfig]
    A --> E[ValidationConfig]
    
    F[ConfigurationManager] --> A
    F --> G[ConfigValidator]
    F --> H[ConfigMigration]
    
    I[MainWindow] --> F
    J[OptimizationSettingsDialog] --> F
    K[StorageManager] --> F
    
    L[Environment Detection] --> F
    M[JSON Config File] --> F
    
    subgraph "Configuration Flow"
        N[Load Config]
        O[Validate Config]
        P[Apply Config]
        Q[Notify Watchers]
        R[Save Config]
    end
    
    F --> N
    N --> O
    O --> P
    P --> Q
    P --> R
```

## Integration Flow Diagram

```mermaid
sequenceDiagram
    participant User
    participant MainWindow
    participant ConfigManager
    participant ProgressDialog
    participant OptimizationWorker
    participant GeneticAlgorithm
    participant ProgressReporter
    
    User->>MainWindow: Start Optimization
    MainWindow->>ConfigManager: Load Configuration
    ConfigManager-->>MainWindow: Validated Config
    
    MainWindow->>ProgressDialog: Show Progress Dialog
    MainWindow->>OptimizationWorker: Start Threaded Optimization
    
    OptimizationWorker->>GeneticAlgorithm: Optimize with ProgressReporter
    GeneticAlgorithm->>ProgressReporter: Report Progress
    
    loop Progress Updates
        ProgressReporter->>ProgressDialog: Update Progress
        ProgressDialog-->>User: Show Current Status
    end
    
    GeneticAlgorithm-->>OptimizationWorker: Return Result
    OptimizationWorker-->>MainWindow: Optimization Complete
    MainWindow->>ProgressDialog: Close Dialog
    ProgressDialog-->>User: Operation Complete
```

## Component Relationship Diagram

```mermaid
graph LR
    subgraph "Core Components"
        A[ProgressReporter Interface]
        B[ConfigurationManager]
        C[ConfigValidator]
        D[ConfigMigration]
    end
    
    subgraph "UI Components"
        E[ProgressDialog]
        F[OptimizationSettingsDialog]
        G[MainWindow]
    end
    
    subgraph "Algorithm Components"
        H[GeneticAlgorithm]
        I[AdvancedOptimizer]
        J[StowageOptimizer]
    end
    
    subgraph "Data Models"
        K[AppConfig]
        L[GeneticAlgorithmConfig]
        M[AdvancedOptimizerConfig]
        N[UIConfig]
        O[ValidationConfig]
    end
    
    A --> E
    B --> F
    B --> G
    C --> B
    D --> B
    
    H --> A
    I --> A
    J --> A
    
    K --> B
    L --> K
    M --> K
    N --> K
    O --> K
    
    E --> A
    F --> B
    G --> B
```

## File Structure Diagram

```mermaid
graph TD
    A[Project Root] --> B[core/]
    A --> C[ui/]
    A --> D[optimizer/]
    A --> E[storage/]
    A --> F[models/]
    A --> G[utils/]
    A --> H[tests/]
    A --> I[docs/]
    
    B --> J[progress_reporter.py]
    B --> K[config_manager.py]
    B --> L[config_models.py]
    B --> M[config_validator.py]
    B --> N[config_migration.py]
    B --> O[optimization_worker.py]
    B --> P[thread_progress_reporter.py]
    
    C --> Q[progress_dialog.py]
    C --> R[main_window.py - Modified]
    C --> S[optimization_settings_dialog.py - Modified]
    
    D --> T[genetic_optimizer.py - Modified]
    D --> U[advanced_optimizer.py - Modified]
    D --> V[stowage_optimizer.py - Modified]
    
    E --> W[storage_manager.py - Modified]
    
    H --> X[test_config_manager.py]
    H --> Y[test_progress_reporter.py]
    H --> Z[test_optimization_worker.py]
    H --> AA[test_integration.py]
    
    I --> BB[progress_indicator_design.md]
    I --> CC[configuration_management_design.md]
    I --> DD[implementation_plan.md]
    I --> EE[improvements_summary.md]
    I --> FF[architecture_diagram.md]
```

## Data Flow Diagram

```mermaid
flowchart TD
    A[Start Application] --> B[Load Configuration]
    B --> C{Config Valid?}
    C -->|Yes| D[Use Configuration]
    C -->|No| E[Create Default Config]
    E --> F[Save Default Config]
    F --> D
    D --> G[Initialize UI]
    
    G --> H[User Action]
    H --> I{Optimization?}
    I -->|Yes| J[Show Progress Dialog]
    I -->|No| K[Handle Other Action]
    
    J --> L[Start Background Thread]
    L --> M[Initialize Progress Reporter]
    M --> N[Run Optimization Algorithm]
    
    N --> O{Progress Update?}
    O -->|Yes| P[Update Progress Dialog]
    O -->|No| Q[Continue Optimization]
    
    P --> R{User Cancelled?}
    R -->|Yes| S[Cancel Thread]
    R -->|No| Q
    
    S --> T[Cleanup Resources]
    T --> U[Close Progress Dialog]
    U --> V[Return to Main UI]
    
    N --> W[Optimization Complete]
    W --> X[Generate Result]
    X --> Y[Update UI with Result]
    Y --> Z[Save Configuration if Changed]
    Z --> AA[Return to Main UI]
```

## Class Hierarchy Diagram

```mermaid
classDiagram
    class ProgressReporter {
        <<interface>>
        +report_progress()
        +report_subtask()
        +is_cancelled()
    }
    
    class ThreadProgressReporter {
        +progress_signal
        +cancelled_check
        +report_progress()
        +report_subtask()
        +is_cancelled()
    }
    
    class OptimizationWorker {
        +progress: pyqtSignal
        +completed: pyqtSignal
        +error: pyqtSignal
        +run()
        +cancel()
    }
    
    class ConfigurationManager {
        +config_file: Path
        +load_config()
        +save_config()
        +get_config_value()
        +set_config_value()
        +add_watcher()
    }
    
    class AppConfig {
        +environment: Environment
        +genetic_algorithm: GeneticAlgorithmConfig
        +advanced_optimizer: AdvancedOptimizerConfig
        +ui: UIConfig
        +validation: ValidationConfig
    }
    
    class GeneticAlgorithmConfig {
        +population_size: int
        +max_generations: int
        +crossover_rate: float
        +mutation_rate: float
    }
    
    class AdvancedOptimizerConfig {
        +min_utilization: float
        +faz_tolerances: Dict
        +score_weights: Dict
    }
    
    ProgressReporter <|-- ThreadProgressReporter
    OptimizationWorker --> ProgressReporter
    ConfigurationManager --> AppConfig
    AppConfig --> GeneticAlgorithmConfig
    AppConfig --> AdvancedOptimizerConfig
```

These diagrams illustrate the complete architecture for the proposed improvements, showing the relationships between components, data flow, and integration points.