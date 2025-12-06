# Product Requirements Document (PRD)
## Tanker Stowage Plan Application

**Version:** 1.0  
**Date:** 2025-12-06  
**Status:** Draft

---

## 1. Executive Summary
- Desktop stowage-planning tool for tanker cargo officers; optimizes cargo distribution while enabling manual control.
- Primary users: shipboard officers (offline-capable); secondary: shore planners.
- Priorities: optimization accuracy, safety-aware constraints, speed, bilingual TR/EN UI.

## 2. Goals and Success Metrics
- Accuracy: >95% cargo fulfillment in typical cases; min tank utilization rule (>=65%).
- Efficiency: Typical optimization <60s (10–20 tanks, 5–10 cargos); planning time cut by >50% vs manual.
- Reliability: <1% plan/save/load errors; crash rate <1%.
- Adoption: Repeat use per vessel; positive user feedback (>80% would recommend).

## 3. User Personas
- **Shipboard Cargo Officer:** Needs fast, reliable plans, manual overrides, warnings; works under time pressure and often offline.
- **Shore Planner:** Reviews/approves plans, tracks history, compares alternatives; higher technical comfort.

## 4. Core User Stories
- Ship profiles: create/edit/save; auto-load last used.
- Cargo input: add cargos with quantity (m³ or ton+density), receivers, optional color; validate vs capacity.
- Automated optimization: choose GA or FAZ; show progress; allow cancel; warn on unfulfilled cargo.
- Manual planning: drag/drop, swap, empty, lock tanks; plan remaining cargos respecting locks and exclusions.
- Visualization: tank cards, schematic layout, comparison table, cargo legend with colors/quantities.
- Persistence: save/load plans (JSON); recent plans menu; preserve excluded tanks/notes.
- Settings: configure optimization parameters; validate; defaults; reset.
- Localization: Turkish and English UI, messages, help.

## 5. Functional Requirements (Selected)
- **Ship Profiles:** Unique tank names per ship; volumes >0; persistent storage; last profile auto-load.
- **Cargo Requests:** Quantity >0; total cargo ≤ total capacity; density >0 when converting ton→m³; optional mandatory flag/custom color.
- **Optimization:** Inputs: ship, cargos, excluded tanks, fixed assignments; outputs: plan + score + warnings; constraints: min 65% utilization, respect exclusions, preserve locks.
- **Progress & Cancel:** Progress dialog (percent, stage, log); cancel stops run cleanly.
- **Manual Ops:** Drag/drop create assignments; swap tanks; edit via dialog; empty tank; lock/unlock; warnings when utilization below threshold; plan remaining cargo fills only unlocked tanks.
- **Visualization:** Tank cards show cargo, quantity, utilization, badges (locked/excluded); schematic organized bow→stern and port/starboard; comparison table shows requested/loaded/remaining per cargo.
- **Persistence:** Save/load plans with cargos, assignments, excluded tanks, notes, profile id; maintain recent plans list (last 5).
- **Settings:** Algorithm choice; GA/FAZ parameters; thresholds; validated; defaults provided; stored centrally.
- **Localization:** TR/EN strings; language choice in settings (restart may be required); all UI/errors/help localized.

## 6. Non-Functional Requirements
- Performance: <60s typical optimization; responsive UI during runs (threaded); startup <3s; memory <500MB typical.
- Reliability: No data loss on save/load; backward-compatible plan/profile loading; graceful error dialogs.
- Usability: New user can create first plan <10 minutes; clear warnings; consistent color legend.
- Security/Privacy: Local-only data; validate file inputs; avoid sensitive info in errors.
- Compatibility: Windows 10/11 primary; Python 3.8+; PyQt6; offline-first.

## 7. Constraints and Assumptions
- Desktop-only; no web/mobile; JSON storage (no DB); offline operation required.
- Tanker liquid cargos; users know maritime operations; safety/regulatory checks remain user responsibility.
- Minimum utilization rule enforced; single maintainer and incremental releases.

## 8. Scope Boundaries
- **Out of scope:** Real-time loading tracking; multi-vessel dashboard; cloud sync; mobile; advanced analytics; regulatory rule engine; 3D viz; external APIs.
- **Future candidates:** Multi-vessel view, cloud sharing, richer reports, VMS integration, compliance checks, mobile companion.

## 9. Risks and Mitigations
- UI freeze/thread safety: use worker threads and thread-safe progress reporter.
- Invalid configs: typed config + validation + defaults; migrations with backup.
- Performance variance: tunable settings; progress + cancel; warnings on partial fulfillment.
- Adoption: bilingual UI, help dialog, sensible defaults, recent plans.

## 10. Success Criteria
- >95% fulfillment, <60s typical run, <1% errors/crashes, positive repeated use per vessel.

## 11. Glossary
- Stowage plan, tank, cargo, receiver, utilization, FAZ (multi-phase fitting), Genetic Algorithm (evolutionary optimizer).
