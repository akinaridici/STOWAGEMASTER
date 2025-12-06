# Technical Specification (SPEC)
## Tanker Stowage Plan Application

**Version:** 1.0  
**Date:** 2025-12-06  
**Status:** Draft

---

## 1. Architecture Overview
- **Client:** PyQt6 desktop app; single process; background threads for optimization.
- **Layers:** UI (`ui/`), models (`models/`), optimizers (`optimizer/`), core services (`core/`), storage (`storage/`).
- **State:** Held in `MainWindow` (current ship, cargos, plan, fixed assignments, exclusions, settings).
- **Persistence:** JSON files for ship profiles, plans, settings (config/app_config.json; legacy storage/optimization_settings.json).
- **Localization:** Turkish (default) and English; string literals in UI code; selection via settings (restart may be needed).

## 2. Key Modules
- `main.py`: QApplication bootstrap, icons, launches `MainWindow`.
- `ui/main_window.py`: Primary UI; menus, cargo input, legend, schematic, plan viewer; orchestrates load/save, optimization, manual edits, locks/exclusions, undo, progress dialog wiring.
- `ui/*`: Dialogs/widgets (`cargo_input_dialog`, `ship_profile_dialog`, `optimization_settings_dialog`, `plan_viewer`, `cargo_legend_widget`, `ship_schematic_widget`, `progress_dialog`, etc.).
- `models/ship.py`: `Ship`, `Tank`; capacity helpers, position info, port/starboard pairs.
- `models/cargo.py`: `Cargo`, `Receiver`; quantity/density handling, custom color.
- `models/plan.py`: `StowagePlan`, `TankAssignment`; assignments map, remaining cargos/tanks, serialization.
- `optimizer/stowage_optimizer.py`: Basic heuristic optimizer; scoring; unfulfilled detection.
- `optimizer/genetic_optimizer.py`, `_with_progress.py`: GA implementation; progress-enabled variant supports cancel.
- `optimizer/advanced_optimizer.py`, `_with_progress.py`: FAZ multi-phase optimizer; progress-enabled variant.
- `core/config_manager.py`: Typed config load/save, watchers, legacy update bridge, default path resolution.
- `core/config_migration.py`: Migrates legacy settings; non-blocking on failure.
- `core/config_models.py`: Dataclasses for app/genetic/advanced/ui/validation configs.
- `core/config_validator.py`: Validation rules.
- `core/optimization_worker.py`: Threaded execution wrapper with progress reporter.
- `core/progress_reporter.py`: Progress interface (stages, percent, messages, cancel flag).
- `storage/storage_manager.py`: JSON persistence for ship profiles, plans, legacy optimization settings, recent plans, last profile ID; PyInstaller-aware base dir.

## 3. Data Models (Essential Fields)
- **Ship:** `id`, `name`, `tanks: List[Tank]`; helpers: `get_total_capacity`, `get_tank_by_id`, `get_tank_pairs`, position info (bow/stern, port/starboard, row).
- **Tank:** `id`, `name`, `volume`.
- **Cargo:** `unique_id`, `cargo_type`, `quantity` (m³), `receivers`, `is_mandatory`, `ton`, `density`, `custom_color` (hex).
- **TankAssignment:** `tank_id`, `cargo`, `quantity_loaded`.
- **StowagePlan:** `id`, `plan_name`, `ship_name`, `ship_profile_id`, `cargo_requests`, `assignments`, `excluded_tanks`, `created_date`, `notes`.

## 4. Core Flows
- **Startup:** `main.py` → `MainWindow`; run config migration; load config; auto-load last profile; update recent plans menu.
- **Ship profile management:** StorageManager loads/saves profiles; dialogs create/edit/delete; last profile persisted.
- **Cargo entry:** `CargoInputDialog` emits list; `MainWindow` syncs `current_cargo_requests`, updates legend/viewer, initializes empty plan when needed.
- **Manual planning:** Drag-drop cargos to tanks; swap; double-click edit; empty; lock via remaining-cargo flow; undo last swap; toggle excluded tanks; refresh legend/viewer.
- **Optimization flow:**
  - Gather cargo list; detect manual assignments (treated as fixed/excluded for algorithm); validate cargo vs capacity.
  - Choose algorithm (GA or FAZ) from settings.
  - Show `OptimizationProgressDialog`; run optimizer (progress-enabled variant when available); support cancel.
  - Merge manual assignments into resulting plan; score plan; warn on unfulfilled cargo; keep excluded tanks.
- **Plan remaining cargos:** Lock current assignments; clear non-fixed algorithm results; optimize remaining cargos only; merge back.
- **Persistence:** Save plan (includes cargos, assignments, excluded tanks, notes, profile id) to chosen path; load plan (restore ship, cargos, exclusions, legend, viewer, recent plans history); save/load profiles and settings.
- **Settings:** `OptimizationSettingsDialog` edits settings; validation via config models; stored through `ConfigurationManager`; legacy formats mapped.

## 5. Algorithms (High Level)
- **Basic heuristic (stowage_optimizer):** Sort cargos (quantity, receiver count); try exact/near fit, best fit, then largest tank; enforce min utilization 65%; track available capacity; scoring = completion (40%), tank utilization (30%), avg fill (20%), empty penalty (10% deduction capped).
- **Genetic Algorithm:** Chromosome = tank assignments; population evolve with crossover/mutation; respects excluded tanks + fixed assignments; tunables: population, generations, rates, elitism, penalties; progress-enabled variant reports stages and checks cancel.
- **Advanced FAZ:** Multi-phase fitting (mandatory → single → paired → multi-tank phases); respects exclusions and fixed assignments; uses tolerance/threshold settings; progress-enabled variant reports per phase.

## 6. Configuration
- **File:** `config/app_config.json` (default path; PyInstaller-aware); created with defaults if missing.
- **Sections:** environment, genetic_algorithm, advanced_optimizer, ui, validation, runtime (`last_profile_id`, `recent_plans`, `optimization_algorithm`).
- **APIs:** `ConfigurationManager.get_config()`, `to_dict()` for legacy compatibility, `update_config()` / `update_from_legacy_settings()`.
- **Migration:** `ConfigMigration.migrate_from_old_format()` maps legacy keys, backs up old data, validates; errors are logged but non-fatal.

## 7. Progress & Threading
- **Interface:** `ProgressReporter` (stage, percent, detail message, cancel flag).
- **UI:** `OptimizationProgressDialog` shows bar, stage, log, cancel button.
- **Execution:** `OptimizationWorker` runs optimizers in background; optimizers periodically check cancel and emit progress; UI remains responsive.

## 8. Error Handling & Validation
- Pre-optimization validation: total cargo vs capacity; min utilization checks; warnings on low-utilization drag/drop or swaps.
- File I/O guarded with dialogs; load errors reported; plan load validates ship profile presence.
- Migration errors do not block startup; defaults used when needed.

## 9. Localization
- Supported languages: Turkish (default) and English.
- Scope: UI labels, dialogs, errors, help text, progress messages.
- Selection via settings; may require restart to apply.

## 10. Persistence Details
- Ship profiles: `storage/ship_profiles.json`.
- Plans: `storage/saved_plans/*.json` (or user-selected path); recent plans tracked (last 5), relative paths used when under saved_plans.
- Settings: `config/app_config.json`; legacy optimization settings in `storage/optimization_settings.json` still loadable.

## 11. Testing Strategy (Minimum)
- **Unit:** model serialization; config load/save/validation; stowage_optimizer scoring/unfulfilled; storage manager paths/history.
- **Integration:** GA/FAZ runs on sample ships/cargos; progress dialog updates; remaining-cargo flow with locks/exclusions.
- **UI smoke:** load/save plan; drag/drop; swap; undo; lock/unlock; exclude tanks; settings dialog; help/about.
- **Regression:** migration from legacy settings; plan load when ship profile missing (error path).

## 12. Open Risks / Follow-ups
- Thread-safety of all progress callbacks must be maintained.
- Localization coverage: ensure all dialogs/messages are translated (TR/EN).
- Performance on large tank/cargo sets may require tuning and profiling.
- Safety/regulatory validation is minimal; relies on user judgment.

---

**End of SPEC**
