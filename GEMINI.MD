# GEMINI.MD - Tanker Stowage Plan Application Documentation

## 1. Project Overview
The **Tanker Stowage Plan** application is a desktop automation tool designed for tanker ship cargo officers. It assists in creating optimal cargo loading plans (stowage plans) by calculating how to distribute various liquid cargos into ship tanks to maximize capacity utilization and ensure safety/stability (trim, list).

## 2. Technology Stack
- **Language**: Python 3.8+
- **GUI Framework**: PyQt6 (>=6.5.0)
- **Data Persistence**: JSON (for plans, profiles, and settings)
- **Packaging**: PyInstaller (for generating standalone Windows executables)
- **Dependencies**: `PyQt6` (Core dependency). No heavy external data science libs (numpy/pandas) are used; math is implemented in pure Python for portability and minimized size.

## 3. Architecture
The application follows a modular layered architecture:

- **UI Layer (`ui/`)**: Handles all user interaction. Main window, dialogs (Cargo Input, Ship Profile, Settings), and custom widgets (Ship Schematic, Plan Viewer).
- **Core Layer (`core/`)**: Application services such as Configuration Management, Progress Reporting, and Threading infrastructure (`OptimizationWorker`).
- **Models Layer (`models/`)**: Data classes representing business entities (`Ship`, `Tank`, `Cargo`, `StowagePlan`).
- **Optimizer Layer (`optimizer/`)**: Contains the core logic for stowage planning algorithms.
- **Storage Layer (`storage/`)**: Manages file I/O, persistence of ship profiles, plans, and legacy settings.

## 4. Functionality
### key Features
1.  **Ship Profile Management**: Create, edit, and save ship configurations (tank definitions, capacities, geometry).
2.  **Cargo Request Management**: Input multiple cargo batches with specific quantities, densities, and receivers.
3.  **Automated Optimization**:
    -   **Basic**: Fast heuristic providing a "good enough" starting point.
    -   **Genetic Algorithm**: Evolutionary approach for global optimization.
    -   **Advanced (FAZ)**: Systematic multi-phase fitting algorithm mimicking human expert logic.
4.  **Manual Planning**: Drag-and-drop interface for manual adjustments, locking specific assignments, and defining excluded tanks.
5.  **Validation**: Real-time checks for tank overfill, minimum utilization, and basic stability (trim/list).
6.  **Progress & Control**: Real-time feedback during optimization with the ability to cancel long-running processes.
7.  **ASCII Reporting**: Generate text-based visual reports of the stowage plan for printing or sharing.

## 5. Algorithms & Logic
The application features three distinct optimization strategies:

### A. Genetic Algorithm (`optimizer/genetic_optimizer_with_progress.py`)
An evolutionary approach useful for finding non-intuitive optimal solutions.
-   **Chromosome Representation**: A list of `(cargo_id, quantity)` tuples, one for each tank in the ship.
-   **Population**: Fixed size (default 500), evolved over generations (default 2000).
-   **Fitness Function**:
    -   **Base Score**: Total quantity of cargo loaded.
    -   **Penalties**:
        -   *Symmetry Penalty*: Unbalanced loading between Port/Starboard tanks.
        -   *Trim Penalty*: Longitudinal Center of Gravity deviation from ideal.
        -   *Operational Penalty*: Splitting a single receiver's cargo across too many tanks.
-   **Operators**:
    -   *Selection*: Tournament or Roulette Wheel.
    -   *Crossover*: Two-point crossover.
    -   *Mutation*: Swap (swap contents of two tanks), Transfer (move cargo from one tank to another), Shift (move cargo between tanks of same receiver).
-   **Constraints**: Hard constraints (tank capacity) are enforced via a "Repair" step after every operation.

### B. Advanced "FAZ" Optimizer (`optimizer/advanced_optimizer_with_progress.py`)
A deterministic, multi-phase algorithm designed to mimic optimal manual planning patterns. It executes in 8 phases (Phases 0-7):
-   **FAZ 0 (Mandatory)**: Places mandatory cargos first. Strict 100% volume requirement. failing this prevents the plan.
-   **FAZ 1 (Single Tank)**: Fits cargos that fit perfectly into a single tank (within tolerance).
-   **FAZ 2 (Two Tanks)**: Finds pairs. Prioritizes Symmetric pairs (Port/Stbd same row) -> Partial Symmetric -> Asymmetric.
-   **FAZ 3-6 (Multi-Tank)**: Iteratively fits cargos requiring 3, 4, 5, or 6 tanks.
    -   *Rule*: For 4-tank cargos, prevents clustering all tanks in just Bow or just Stern sections to avoid trim issues.
-   **FAZ 7 (Best Fit)**: Remaining cargos are placed using a general best-fit greedy strategy.

### C. Basic Heuristic (`optimizer/stowage_optimizer.py`)
A fast, greedy strategy used for "Quick Plan" or fallback.
1.  Sorts cargos by quantity (descending).
2.  Attempts **Exact Fit** (single tank).
3.  Attempts **Two-Tank Split**.
4.  Falls back to **Largest Available Tank**.

## 6. Storage & File Structure
-   **Config**: `config/app_config.json` - Centralized application settings (Algorithm parameters, UI limits).
-   **Ship Profiles**: `storage/ship_profiles.json` - Database of defined ships.
-   **Saved Plans**: `storage/saved_plans/*.json` - User-saved stowage plans.
-   **Legacy**: `storage/optimization_settings.json` - Old settings file (migrated automatically).

### Directory Structure
```
root/
├── main.py                    # Application Entry Point
├── build_exe.bat              # Build Script
├── core/                      # System Services
│   ├── config_manager.py      # Configuration Logic
│   ├── optimization_worker.py # Threading Logic
│   └── progress_reporter.py   # Progress Interface
├── models/                    # Data Classes
│   ├── ship.py                # Ship & Tank logic
│   └── plan.py                # Plan & Assignment logic
├── optimizer/                 # Algorithms
│   ├── advanced_*.py          # FAZ Algo
│   └── genetic_*.py           # GA Algo
├── storage/                   # File I/O
├── ui/                        # PyQt6 Interface
│   ├── main_window.py         # Main Controller
│   └── *.py                   # Dialogs & Widgets
└── docs/                      # Documentation (PRD, SPEC, etc.)
```

## 7. Key Logic Flows
### Startup
1.  `main.py` initializes `QApplication`.
2.  `MainWindow` loads.
3.  `ConfigMigration` runs safely to upgrade any old settings.
4.  `ConfigurationManager` loads active config.
5.  Last used Ship Profile is auto-loaded.

### Optimization Flow
1.  User clicks "Optimize".
2.  `OptimizationProgressDialog` opens (modal).
3.  `OptimizationWorker` thread starts designed algorithm (GA or FAZ).
4.  Algorithm reports progress via `ProgressReporter` interface.
    -   Checks user 'Cancel' request periodically.
5.  On completion, `StowagePlan` is returned to Main Thread.
6.  `MainWindow` applies plan to the visualizer.

### Threading Model
-   **UI Thread**: Handles all drawing and user events.
-   **Worker Thread**: Runs computationally expensive optimization.
-   **Communication**: Via PyQt Signals/Slots to ensure thread safety (UI updates only occur on UI thread).

## 8. Development & Build
-   **Build System**: `build_exe.bat` uses `PyInstaller` to package the app.
-   **Specs**: `TankerStowagePlan.spec` defines the build configuration (hidden imports, data files).
-   **Tests**: `tests/` folder contains unit and integration tests, particularly for the config and progress systems.
