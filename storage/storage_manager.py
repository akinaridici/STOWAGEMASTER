"""Storage manager for ship profiles and stowage plans"""

import json
import os
import sys
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime

from models.ship import Ship
from models.plan import StowagePlan


def get_base_dir() -> Path:
    """Get the base directory for storage.
    
    In PyInstaller onefile mode, returns the directory where the EXE is located.
    Otherwise, returns the current working directory.
    """
    # Check if running as PyInstaller bundle
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Running as compiled EXE (PyInstaller onefile mode)
        # sys.executable is the path to the EXE file
        # We want the directory where the EXE is located, not the temp directory
        exe_path = Path(sys.executable)
        if exe_path.is_file() and exe_path.suffix.lower() == '.exe':
            return exe_path.parent
        else:
            # Fallback: use current working directory
            return Path.cwd()
    elif getattr(sys, 'frozen', False):
        # Running as compiled EXE (but not onefile mode)
        exe_path = Path(sys.executable)
        if exe_path.is_file():
            return exe_path.parent
        else:
            return Path.cwd()
    else:
        # Running as Python script
        return Path.cwd()


class StorageManager:
    """Manages persistence of ship profiles and stowage plans"""
    
    def __init__(self, base_dir: str = None):
        """Initialize storage manager
        
        Args:
            base_dir: Base directory for storage. If None, uses EXE directory or current directory.
        """
        if base_dir is None:
            base_dir = get_base_dir()
        else:
            base_dir = Path(base_dir)
        
        self.base_dir = Path(base_dir)
        self.profiles_file = self.base_dir / "storage" / "ship_profiles.json"
        self.plans_dir = self.base_dir / "storage" / "saved_plans"
        self.settings_file = self.base_dir / "storage" / "optimization_settings.json"
        
        # Create directories if they don't exist
        self.profiles_file.parent.mkdir(parents=True, exist_ok=True)
        self.plans_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize profiles file if it doesn't exist
        if not self.profiles_file.exists():
            self._save_profiles({})
    
    # Ship Profile Methods
    
    def save_ship_profile(self, ship: Ship) -> bool:
        """Save or update a ship profile"""
        try:
            profiles = self.load_all_profiles()
            profiles[ship.id] = ship.to_dict()
            self._save_profiles(profiles)
            return True
        except Exception as e:
            print(f"Error saving ship profile: {e}")
            return False
    
    def load_ship_profile(self, ship_id: str) -> Optional[Ship]:
        """Load a ship profile by ID"""
        try:
            profiles = self.load_all_profiles()
            if ship_id in profiles:
                return Ship.from_dict(profiles[ship_id])
            return None
        except Exception as e:
            print(f"Error loading ship profile: {e}")
            return None
    
    def load_all_profiles(self) -> Dict[str, dict]:
        """Load all ship profiles as dictionary"""
        try:
            if not self.profiles_file.exists():
                return {}
            
            with open(self.profiles_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading profiles: {e}")
            return {}
    
    def get_all_ships(self) -> List[Ship]:
        """Get all ship profiles as Ship objects"""
        profiles = self.load_all_profiles()
        return [Ship.from_dict(data) for data in profiles.values()]
    
    def delete_ship_profile(self, ship_id: str) -> bool:
        """Delete a ship profile"""
        try:
            profiles = self.load_all_profiles()
            if ship_id in profiles:
                del profiles[ship_id]
                self._save_profiles(profiles)
                return True
            return False
        except Exception as e:
            print(f"Error deleting ship profile: {e}")
            return False
    
    def save_ship_profile_to_file(self, ship: Ship, filepath: str) -> bool:
        """Save a ship profile to a specific file path
        
        Args:
            ship: Ship to save
            filepath: Full path to the JSON file where ship will be saved
            
        Returns:
            True if successful, False otherwise
        """
        try:
            file_path = Path(filepath)
            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(ship.to_dict(), f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving ship profile to file: {e}")
            return False
    
    def load_ship_profile_from_file(self, filepath: str) -> Optional[Ship]:
        """Load a ship profile from a specific file path
        
        Args:
            filepath: Full path to the JSON file containing the ship profile
            
        Returns:
            Ship if successful, None otherwise
        """
        try:
            file_path = Path(filepath)
            
            if not file_path.exists():
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return Ship.from_dict(data)
        except Exception as e:
            print(f"Error loading ship profile from file: {e}")
            return None
    
    def _save_profiles(self, profiles: Dict[str, dict]):
        """Internal method to save profiles to file"""
        with open(self.profiles_file, 'w', encoding='utf-8') as f:
            json.dump(profiles, f, indent=2, ensure_ascii=False)
    
    # Stowage Plan Methods
    
    def save_plan(self, plan: StowagePlan) -> bool:
        """Save a stowage plan to archive"""
        try:
            filename = f"{plan.id}.json"
            filepath = self.plans_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(plan.to_dict(), f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving plan: {e}")
            return False
    
    def load_plan(self, plan_id: str) -> Optional[StowagePlan]:
        """Load a stowage plan by ID"""
        try:
            filename = f"{plan_id}.json"
            filepath = self.plans_dir / filename
            
            if not filepath.exists():
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return StowagePlan.from_dict(data)
        except Exception as e:
            print(f"Error loading plan: {e}")
            return None
    
    def get_all_plans(self) -> List[StowagePlan]:
        """Get all saved plans"""
        plans = []
        try:
            for filepath in self.plans_dir.glob("*.json"):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        plan = StowagePlan.from_dict(data)
                        plans.append(plan)
                except Exception as e:
                    print(f"Error loading plan from {filepath}: {e}")
                    continue
        except Exception as e:
            print(f"Error listing plans: {e}")
        
        # Sort by creation date (newest first)
        plans.sort(key=lambda p: p.created_date if p.created_date else datetime.min, reverse=True)
        return plans
    
    def delete_plan(self, plan_id: str) -> bool:
        """Delete a saved plan"""
        try:
            filename = f"{plan_id}.json"
            filepath = self.plans_dir / filename
            
            if filepath.exists():
                filepath.unlink()
                return True
            return False
        except Exception as e:
            print(f"Error deleting plan: {e}")
            return False
    
    def save_plan_to_file(self, plan: StowagePlan, filepath: str) -> bool:
        """Save a stowage plan to a specific file path
        
        Args:
            plan: StowagePlan to save
            filepath: Full path to the JSON file where plan will be saved
            
        Returns:
            True if successful, False otherwise
        """
        try:
            file_path = Path(filepath)
            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(plan.to_dict(), f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving plan to file: {e}")
            return False
    
    def load_plan_from_file(self, filepath: str) -> Optional[StowagePlan]:
        """Load a stowage plan from a specific file path
        
        Args:
            filepath: Full path to the JSON file containing the plan
            
        Returns:
            StowagePlan if successful, None otherwise
        """
        try:
            file_path = Path(filepath)
            
            if not file_path.exists():
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return StowagePlan.from_dict(data)
        except Exception as e:
            print(f"Error loading plan from file: {e}")
            return None
    
    # Optimization Settings Methods
    
    def get_default_settings(self) -> Dict:
        """Get default optimization settings"""
        return {
            'optimization_algorithm': 'genetic',  # Default: Genetic Algorithm
            'min_utilization': 0.65,
            'drag_drop_warning_threshold': 0.70,
            'score_weights': {
                'single_fit': 0.40,
                'symmetry': 0.25,
                'bow_stern': 0.15,
                'best_fit': 0.20
            },
            'waste_utilization_weights': {
                'waste': 0.7,
                'utilization': 0.3
            },
            'exact_fit_threshold': 0.01,
            'bow_stern_violation_threshold': 3,
            'symmetric_pair_min_threshold': 0.65,
            # FAZ tolerance parameters
            'faz1_single_tank_tolerance': 0.05,
            'faz2_two_tank_tolerance': 0.05,
            'faz2_asymmetric_tolerance_factor': 0.2,
            'faz3_three_tank_tolerance': 0.04,
            'faz4_four_tank_tolerance': 0.04,
            'faz5_five_tank_tolerance': 0.04,
            'mandatory_retry_increment': 0.01,
            'mandatory_max_relaxation': 0.35,
            # Genetic Algorithm parameters
            'ga_population_size': 500,
            'ga_max_generations': 2000,
            'ga_crossover_rate': 0.90,
            'ga_mutation_rate': 0.11,
            'ga_tournament_size': 3,
            'ga_use_elitism': True,
            'ga_elitism_count': 5,
            'ga_symmetry_penalty_coef': 3000.0,
            'ga_trim_penalty_coef': 1500.0,
            'ga_operational_penalty_coef': 100.0,
            'ga_receiver_tolerance': 0.03,
            'ga_convergence_threshold': 0.0001,
            'ga_convergence_generations': 60
        }
    
    def load_optimization_settings(self) -> Dict:
        """Load optimization settings from file, or return defaults"""
        try:
            if not self.settings_file.exists():
                print("Debug load_optimization_settings: Settings file does not exist")
                return self.get_default_settings()
            
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                print(f"Debug load_optimization_settings: Raw settings keys = {list(settings.keys())}")
                print(f"Debug load_optimization_settings: Raw recent_plans = {settings.get('recent_plans', 'NOT FOUND')}")
                
                # Merge with defaults to ensure all keys exist (deep merge for nested dicts)
                defaults = self.get_default_settings()
                # Start with defaults, then update with settings
                # This preserves keys that exist in settings but not in defaults (like recent_plans, last_profile_id)
                merged = defaults.copy()
                # Merge nested dictionaries properly
                for key in defaults:
                    if key in settings and isinstance(defaults[key], dict) and isinstance(settings[key], dict):
                        merged[key] = defaults[key].copy()
                        merged[key].update(settings[key])
                    elif key in settings:
                        merged[key] = settings[key]
                # Add any keys from settings that are not in defaults (like recent_plans, last_profile_id)
                for key in settings:
                    if key not in defaults:
                        merged[key] = settings[key]
                
                print(f"Debug load_optimization_settings: Merged settings keys = {list(merged.keys())}")
                print(f"Debug load_optimization_settings: Merged recent_plans = {merged.get('recent_plans', 'NOT FOUND')}")
                return merged
        except Exception as e:
            print(f"Error loading optimization settings: {e}")
            import traceback
            traceback.print_exc()
            return self.get_default_settings()
    
    def save_optimization_settings(self, settings: Dict) -> bool:
        """Save optimization settings to file"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
                f.flush()  # Ensure data is written to disk
                import os
                os.fsync(f.fileno())  # Force write to disk
            print(f"Debug save_optimization_settings: Saved settings with keys = {list(settings.keys())}")
            print(f"Debug save_optimization_settings: recent_plans = {settings.get('recent_plans', 'NOT FOUND')}")
            return True
        except Exception as e:
            print(f"Error saving optimization settings: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # Last Profile Tracking Methods
    
    def save_last_profile_id(self, ship_id: str) -> bool:
        """Save the last loaded ship profile ID
        
        Args:
            ship_id: ID of the ship profile to save as last loaded
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Load current settings
            settings = self.load_optimization_settings()
            # Add or update last_profile_id
            settings['last_profile_id'] = ship_id
            # Save settings
            return self.save_optimization_settings(settings)
        except Exception as e:
            print(f"Error saving last profile ID: {e}")
            return False
    
    def load_last_profile_id(self) -> Optional[str]:
        """Load the last loaded ship profile ID
        
        Returns:
            Ship profile ID if found, None otherwise
        """
        try:
            settings = self.load_optimization_settings()
            return settings.get('last_profile_id')
        except Exception as e:
            print(f"Error loading last profile ID: {e}")
            return None
    
    # Recent Plans History Methods
    
    def save_recent_plan(self, file_path: str) -> bool:
        """Save a recently opened plan file path to history
        
        Args:
            file_path: Full path to the plan file that was opened
            
        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"Debug: Saving recent plan: {file_path}")
            # Load current settings
            settings = self.load_optimization_settings()
            
            # Get current recent plans list
            recent_plans = settings.get('recent_plans', [])
            print(f"Debug: Current recent plans before save: {recent_plans}")
            
            # Remove the file_path if it already exists (to avoid duplicates)
            if file_path in recent_plans:
                recent_plans.remove(file_path)
            
            # Add to the beginning of the list
            recent_plans.insert(0, file_path)
            
            # Keep only the last 5 plans
            recent_plans = recent_plans[:5]
            
            # Update settings
            settings['recent_plans'] = recent_plans
            print(f"Debug: Updated recent plans: {recent_plans}")
            
            # Save settings
            result = self.save_optimization_settings(settings)
            print(f"Debug: Save result: {result}")
            return result
        except Exception as e:
            print(f"Error saving recent plan: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def load_recent_plans(self) -> List[str]:
        """Load the list of recently opened plan file paths
        
        Returns:
            List of file paths (up to 5), most recent first
        """
        try:
            settings = self.load_optimization_settings()
            recent_plans = settings.get('recent_plans', [])
            print(f"Debug load_recent_plans: settings keys = {list(settings.keys())}")
            print(f"Debug load_recent_plans: recent_plans from settings = {recent_plans}")
            
            # Filter out non-existent files
            valid_plans = []
            for plan_path in recent_plans:
                if Path(plan_path).exists():
                    valid_plans.append(plan_path)
            
            # Update settings if some files were removed
            if len(valid_plans) != len(recent_plans):
                settings['recent_plans'] = valid_plans
                self.save_optimization_settings(settings)
            
            return valid_plans
        except Exception as e:
            print(f"Error loading recent plans: {e}")
            import traceback
            traceback.print_exc()
            return []

