"""Main window UI for Stowage Plan application"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QComboBox, QLabel, QMessageBox,
                             QMenuBar, QMenu, QSplitter, QGroupBox, QScrollArea,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QProgressBar, QDoubleSpinBox, QLineEdit, QDialog,
                             QDialogButtonBox, QSizePolicy, QApplication)
from PyQt6.QtCore import Qt
from typing import Optional

from models.ship import Ship
from models.cargo import Cargo
from models.plan import StowagePlan, TankAssignment
from storage.storage_manager import StorageManager
from ui.ship_profile_dialog import ShipProfileDialog
from ui.cargo_input_dialog import CargoInputDialog
from ui.plan_viewer import PlanViewer


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.storage = StorageManager()
        self.current_ship: Optional[Ship] = None
        self.current_cargo_requests: list[Cargo] = []
        self.current_plan: Optional[StowagePlan] = None
        self.excluded_tanks: set[str] = set()  # Tank IDs excluded from planning
        self.last_tank_swap_state: Optional[dict] = None  # History for UNDO (drag-drop only)
        self.optimization_settings = self.storage.load_optimization_settings()  # Load optimization settings
        self.fixed_assignments: dict[str, TankAssignment] = {}  # Manual assignments that should be preserved
        
        self.init_ui()
        
        # Auto-load last profile if available
        self.load_last_profile()
    
    def load_last_profile(self):
        """Load the last used ship profile automatically"""
        try:
            last_profile_id = self.storage.load_last_profile_id()
            if last_profile_id:
                ship = self.storage.load_ship_profile(last_profile_id)
                if ship:
                    self.current_ship = ship
                    # Reset excluded tanks when ship changes
                    self.excluded_tanks.clear()
                    # Show tanks in schematic if no plan exists
                    if self.current_plan is None:
                        from models.plan import StowagePlan
                        empty_plan = StowagePlan(
                            ship_name=self.current_ship.name,
                            ship_profile_id=self.current_ship.id,
                            cargo_requests=[]
                        )
                        self.display_tank_cards_in_panel(empty_plan, self.current_ship)
                    self.update_optimize_button_state()
                    # Update window title
                    self.update_window_title()
        except Exception as e:
            # Silently continue if profile loading fails (corrupted or deleted file)
            print(f"Error loading last profile: {e}")
    
    def update_window_title(self):
        """Update window title with current ship name"""
        if self.current_ship:
            self.setWindowTitle(f"Tanker Stowage Plan - {self.current_ship.name} - Yükleme Planı")
        else:
            self.setWindowTitle("Tanker Stowage Plan - Yükleme Planı")
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Tanker Stowage Plan - Yükleme Planı")
        self.setGeometry(100, 100, 1400, 800)
        
        # Set window icon
        from pathlib import Path
        from PyQt6.QtGui import QIcon
        icon_path = Path(__file__).parent.parent / "storage_manager.ico"
        if not icon_path.exists():
            # Fallback to stowmanager.ico if storage_manager.ico doesn't exist
            icon_path = Path(__file__).parent.parent / "stowmanager.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create main vertical splitter for top (40%) and bottom (60%) sections
        main_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Top panel - Control Panel (40% of screen)
        top_panel = self.create_top_panel()
        main_splitter.addWidget(top_panel)
        
        # Bottom splitter for cargo input and plan viewer (60% of screen)
        bottom_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Cargo input
        left_panel = self.create_middle_panel()  # Renamed: middle -> left
        bottom_splitter.addWidget(left_panel)
        
        # Right panel - Plan viewer
        right_panel = self.create_right_panel()
        bottom_splitter.addWidget(right_panel)
        
        # Set bottom splitter proportions (40% cargo input, 60% plan viewer)
        # Plan viewer'ın daha fazla alan alması için başlangıç oranları ayarlandı
        # Kullanıcı splitter'ı elle ayarlayarak istediği oranı seçebilir
        bottom_splitter.setSizes([400, 1000])
        
        main_splitter.addWidget(bottom_splitter)
        
        # Set main splitter proportions (40% top, 60% bottom)
        # Assuming window height ~800px: 40% = 320px, 60% = 480px
        main_splitter.setSizes([320, 480])
        
        main_layout.addWidget(main_splitter)
    
    def create_menu_bar(self):
        """Create application menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('Dosya')
        
        load_plan_action = file_menu.addAction('Plan Yükle', self.load_plan_from_archive)
        load_plan_action.setShortcut('Ctrl+O')
        
        save_plan_action = file_menu.addAction('Planı Kaydet', self.save_current_plan)
        save_plan_action.setShortcut('Ctrl+S')
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction('Çıkış', self.close)
        exit_action.setShortcut('Ctrl+Q')
        
        # Ship menu - Add ship profile management
        ship_menu = menubar.addMenu('Gemi Profili')
        ship_menu.addAction('Gemi Profili Seç/Yönet', self.manage_ship_profiles)
        ship_menu.addAction('Yeni Gemi Profili', self.create_new_ship_profile)
        
        # Settings menu
        settings_menu = menubar.addMenu('Ayarlar')
        settings_menu.addAction('Optimizasyon Ayarları', self.open_optimization_settings)
        settings_menu.addSeparator()
        settings_menu.addAction('Gemi Profillerini Yönet', self.manage_ship_profiles)
        
        # Plan menu - Add plan management actions
        plan_menu = menubar.addMenu('Plan')
        self.undo_action = plan_menu.addAction('Son İşlemi Geri Al', self.undo_last_swap)
        self.undo_action.setShortcut('Ctrl+Z')
        self.undo_action.setEnabled(False)  # Initially disabled
        plan_menu.addSeparator()
        clear_all_tanks_action = plan_menu.addAction('Tüm Tankları Boşalt', self.clear_all_tanks)
        clear_all_tanks_action.setShortcut('Ctrl+E')
        
        # Help menu
        help_menu = menubar.addMenu('Yardım')
        help_menu.addAction('Kullanım Kılavuzu', self.show_help)
        help_menu.addAction('Hakkında', self.show_about)
    
    def create_top_panel(self) -> QWidget:
        """Create top control panel with cargo legend and ship schematic"""
        panel = QGroupBox("Kontrol Paneli")
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)  # Reduce margins
        layout.setSpacing(5)  # Reduce spacing between widgets
        
        # Cargo legend and button in same row
        legend_button_layout = QHBoxLayout()
        legend_button_layout.setSpacing(10)
        
        # Cargo legend widget (left side, takes available space)
        from ui.cargo_legend_widget import CargoLegendWidget
        self.cargo_legend = CargoLegendWidget(self)
        legend_button_layout.addWidget(self.cargo_legend, 1)  # Stretch factor 1
        
        # "%100 Yap" button (right side, fixed size)
        self.fill_100_btn = QPushButton("%100 Yap")
        self.fill_100_btn.setMinimumHeight(35)
        self.fill_100_btn.setMinimumWidth(100)
        self.fill_100_btn.setStyleSheet("font-size: 10pt; font-weight: bold;")
        self.fill_100_btn.clicked.connect(self.fill_tanks_to_100_percent)
        self.fill_100_btn.setEnabled(False)  # Initially disabled
        legend_button_layout.addWidget(self.fill_100_btn)  # Fixed size on right
        
        layout.addLayout(legend_button_layout)
        
        # Ship schematic widget (replaces horizontal scroll layout)
        from ui.ship_schematic_widget import ShipSchematicWidget
        self.ship_schematic = ShipSchematicWidget(self)
        self.ship_schematic.setParent(self)
        layout.addWidget(self.ship_schematic, 1)  # Expanding
        
        # Keep reference for backward compatibility (for dynamic sizing if needed)
        self.tanks_scroll_area = None
        
        panel.setLayout(layout)
        return panel
    
    # Removed create_left_panel - ship profile is now in popup dialog
    
    def create_middle_panel(self) -> QWidget:
        """Create middle panel for cargo input"""
        panel = QGroupBox("Yükleme Talepleri")
        layout = QVBoxLayout()
        
        # Cargo input widget - genişleyebilmeli (stretch faktörü 1)
        self.cargo_input_widget = CargoInputDialog(parent=self, embedded=True)
        self.cargo_input_widget.cargo_list_changed.connect(self.on_cargo_list_changed)
        layout.addWidget(self.cargo_input_widget, 1)
        
        # Optimize button at the bottom of cargo input panel - sabit boyut
        self.optimize_btn = QPushButton("Yükleme Planını Oluştur")
        self.optimize_btn.setMinimumHeight(40)
        self.optimize_btn.setStyleSheet("font-size: 12pt; font-weight: bold;")
        self.optimize_btn.clicked.connect(self.create_optimized_plan)
        self.optimize_btn.setEnabled(False)
        layout.addWidget(self.optimize_btn, 0)  # Sabit boyut, en altta
        
        # "Kalan Yükleri Planla" button - only visible when there are manual assignments
        self.remaining_cargo_btn = QPushButton("Kalan Yükleri Planla")
        self.remaining_cargo_btn.setMinimumHeight(40)
        self.remaining_cargo_btn.setStyleSheet("font-size: 12pt; font-weight: bold; background-color: #4ECDC4;")
        self.remaining_cargo_btn.clicked.connect(self.create_remaining_cargo_plan)
        self.remaining_cargo_btn.setEnabled(False)
        self.remaining_cargo_btn.setVisible(False)  # Initially hidden
        layout.addWidget(self.remaining_cargo_btn, 0)  # Sabit boyut, en altta
        
        panel.setLayout(layout)
        return panel
    
    def create_right_panel(self) -> QWidget:
        """Create right panel for plan visualization"""
        panel = QGroupBox("Yükleme Planı")
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)  # Minimize margins
        layout.setSpacing(5)  # Minimize spacing
        
        self.plan_viewer = PlanViewer()
        # Stretch faktörü ile ekle - plan viewer genişleyebilmeli
        layout.addWidget(self.plan_viewer, 1)
        
        panel.setLayout(layout)
        return panel
    
    # Removed load_ship_profiles and on_ship_selected - moved to popup dialog
    
    def create_new_ship_profile(self):
        """Open dialog to create new ship profile"""
        from ui.ship_profile_manager_dialog import ShipProfileManagerDialog
        
        dialog = ShipProfileManagerDialog(self, self.storage, self.current_ship)
        # Trigger new ship profile creation
        dialog.create_new_ship_profile()
        # Then show the dialog
        if dialog.exec():
            selected_ship = dialog.selected_ship
            if selected_ship:
                self.current_ship = selected_ship
                # Reset excluded tanks when ship changes
                self.excluded_tanks.clear()
                # Show tanks in schematic if no plan exists
                if self.current_plan is None:
                    from models.plan import StowagePlan
                    empty_plan = StowagePlan(
                        ship_name=self.current_ship.name,
                        ship_profile_id=self.current_ship.id,
                        cargo_requests=[]
                    )
                    self.display_tank_cards_in_panel(empty_plan, self.current_ship)
                self.update_optimize_button_state()
                # Update window title and save last profile
                self.update_window_title()
                self.storage.save_last_profile_id(selected_ship.id)
    
    def manage_ship_profiles(self):
        """Open dialog to manage ship profiles"""
        from ui.ship_profile_manager_dialog import ShipProfileManagerDialog
        
        dialog = ShipProfileManagerDialog(self, self.storage, self.current_ship)
        if dialog.exec():
            # User clicked OK, update current ship
            selected_ship = dialog.selected_ship
            if selected_ship:
                self.current_ship = selected_ship
                # Reset excluded tanks when ship changes
                self.excluded_tanks.clear()
                # Show tanks in schematic if no plan exists
                if self.current_plan is None:
                    from models.plan import StowagePlan
                    empty_plan = StowagePlan(
                        ship_name=self.current_ship.name,
                        ship_profile_id=self.current_ship.id,
                        cargo_requests=[]
                    )
                    self.display_tank_cards_in_panel(empty_plan, self.current_ship)
                self.update_optimize_button_state()
                # Update window title and save last profile
                self.update_window_title()
                self.storage.save_last_profile_id(selected_ship.id)
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.information(
            self,
            "Hakkında",
            "Tanker Stowage Plan Uygulaması\n\n"
            "Bu uygulama, tanker yükleme planlamasına yardımcı olmak üzere Akın Kaptan (akinkaptan77@hotmail.com) tarafından geliştirilmiştir."
        )
    
    def on_cargo_list_changed(self):
        """Handle cargo list changes (including planned status changes)"""
        # Get current cargo list
        cargo_list = self.cargo_input_widget.get_cargo_list()
        
        # Update current_cargo_requests
        self.current_cargo_requests = cargo_list
        
        # Update plan's cargo_requests if plan exists
        if self.current_plan:
            self.current_plan.cargo_requests = cargo_list
        
        # Initialize empty plan if doesn't exist and we have ship and cargo
        if not self.current_plan and self.current_ship and cargo_list:
            self.initialize_empty_plan()
        
        # Update LEGEND with cargo list and colors
        if hasattr(self, 'cargo_legend'):
            if self.current_plan:
                # Use current cargo list (which is now synced with plan)
                cargo_colors = self._generate_colors(len(cargo_list))
                self.cargo_legend.set_cargo_list(cargo_list, cargo_colors, self.current_plan)
            elif cargo_list:
                # Generate colors for current cargo list
                cargo_colors = self._generate_colors(len(cargo_list))
                self.cargo_legend.set_cargo_list(cargo_list, cargo_colors, None)
            else:
                self.cargo_legend.set_cargo_list([], [], None)
        
        # Refresh tank cards display to show updated planned status
        if self.current_plan and self.current_ship:
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(100, lambda: self.display_tank_cards_in_panel(self.current_plan, self.current_ship))
        
        # Update button states
        self.update_optimize_button_state()
        self.update_fill_100_button_state()
    
    def update_optimize_button_state(self):
        """Update optimize button enabled state"""
        has_ship = self.current_ship is not None
        
        # Get current cargo list directly from widget
        if hasattr(self, 'cargo_input_widget'):
            cargo_list = self.cargo_input_widget.get_cargo_list()
            has_cargo = len(cargo_list) > 0
        else:
            has_cargo = len(self.current_cargo_requests) > 0 if hasattr(self, 'current_cargo_requests') else False
        
        # Check if "Kalan Yükleri Planla" button is visible/active
        remaining_btn_visible = False
        if hasattr(self, 'remaining_cargo_btn'):
            remaining_btn_visible = self.remaining_cargo_btn.isVisible()
        
        # If "Kalan Yükleri Planla" is visible, hide and disable "Yükleme Planı Oluştur"
        if remaining_btn_visible:
            self.optimize_btn.setVisible(False)
            self.optimize_btn.setEnabled(False)
        else:
            # Otherwise, show and enable based on ship and cargo
            self.optimize_btn.setVisible(True)
            self.optimize_btn.setEnabled(has_ship and has_cargo)
        
        # Also update remaining cargo button state (but don't update optimize button again to avoid loop)
        if hasattr(self, 'remaining_cargo_btn'):
            self._update_remaining_cargo_button_state_internal()
    
    def _update_remaining_cargo_button_state_internal(self):
        """Internal method to update remaining cargo button state (without updating optimize button)"""
        if not hasattr(self, 'remaining_cargo_btn'):
            return
        
        # Button should be visible if there's a plan and at least one assignment in the plan
        # (Before "Kalan Yükleri Planla" is pressed, fixed_assignments is empty,
        # so we check the plan directly)
        has_plan = self.current_plan is not None
        has_assignments = has_plan and len(self.current_plan.assignments) > 0
        
        # Button is visible if there's a plan and assignments (user can lock and plan remaining)
        # Button is always enabled if visible, because create_remaining_cargo_plan
        # will lock current assignments and plan remaining cargos
        should_show = has_plan and has_assignments
        
        self.remaining_cargo_btn.setVisible(should_show)
        self.remaining_cargo_btn.setEnabled(should_show)  # Always enabled if visible
    
    def update_remaining_cargo_button_state(self):
        """Update 'Kalan Yükleri Planla' button visibility and enabled state"""
        # Update remaining cargo button state
        self._update_remaining_cargo_button_state_internal()
        
        # Update optimize button state when remaining cargo button state changes
        # (to hide/show "Yükleme Planı Oluştur" accordingly)
        if hasattr(self, 'optimize_btn'):
            remaining_btn_visible = False
            if hasattr(self, 'remaining_cargo_btn'):
                remaining_btn_visible = self.remaining_cargo_btn.isVisible()
            
            if remaining_btn_visible:
                # Hide and disable "Yükleme Planı Oluştur"
                self.optimize_btn.setVisible(False)
                self.optimize_btn.setEnabled(False)
            else:
                # Show and enable "Yükleme Planı Oluştur" based on ship and cargo
                has_ship = self.current_ship is not None
                if hasattr(self, 'cargo_input_widget'):
                    cargo_list = self.cargo_input_widget.get_cargo_list()
                    has_cargo = len(cargo_list) > 0
                else:
                    has_cargo = len(self.current_cargo_requests) > 0 if hasattr(self, 'current_cargo_requests') else False
                
                self.optimize_btn.setVisible(True)
                self.optimize_btn.setEnabled(has_ship and has_cargo)
    
    def initialize_empty_plan(self):
        """Initialize an empty plan for manual planning"""
        if not self.current_ship:
            QMessageBox.warning(
                self,
                "Eksik Bilgi",
                "Lütfen gemi profili seçin."
            )
            return
        
        # Get cargo requests from input widget
        self.current_cargo_requests = self.cargo_input_widget.get_cargo_list()
        
        if not self.current_cargo_requests:
            QMessageBox.warning(
                self,
                "Eksik Bilgi",
                "Lütfen en az bir yükleme talebi girin."
            )
            return
        
        # Create empty plan
        from models.plan import StowagePlan
        self.current_plan = StowagePlan(
            ship_name=self.current_ship.name,
            ship_profile_id=self.current_ship.id,
            cargo_requests=self.current_cargo_requests,
            plan_name="Manuel Plan"
        )
        
        # Clear fixed assignments and UNDO history
        self.fixed_assignments.clear()
        self.last_tank_swap_state = None
        self.update_undo_menu_state()
        
        # Generate colors for cargo types
        cargo_colors = self._generate_colors(len(self.current_plan.cargo_requests)) if self.current_plan else []
        
        # Display empty plan
        self.plan_viewer.display_plan(self.current_plan, self.current_ship, cargo_colors)
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(100, lambda: self.display_tank_cards_in_panel(self.current_plan, self.current_ship))
        
        # Update LEGEND
        if hasattr(self, 'cargo_legend'):
            self.cargo_legend.set_cargo_list(self.current_cargo_requests, cargo_colors, self.current_plan)
        
        # Update button states
        self.update_remaining_cargo_button_state()
        self.update_fill_100_button_state()
        
        QMessageBox.information(
            self,
            "Plan Başlatıldı",
            "Yeni plan başlatıldı.\n\n"
            "Yükleri LEGEND bölümünden sürükleyip tanklara bırakarak yerleştirebilirsiniz."
        )
    
    def handle_exclude_tank(self, tank_id: str, exclude: bool):
        """Handle tank exclusion from planning"""
        if exclude:
            self.excluded_tanks.add(tank_id)
        else:
            self.excluded_tanks.discard(tank_id)
        
        # Refresh tank cards display to show excluded status
        if hasattr(self, 'ship_schematic') and self.current_ship:
            from PyQt6.QtCore import QTimer
            if self.current_plan is None:
                # Create empty plan for display purposes (no assignments)
                from models.plan import StowagePlan
                empty_plan = StowagePlan(
                    ship_name=self.current_ship.name,
                    ship_profile_id=self.current_ship.id,
                    cargo_requests=self.current_cargo_requests or []
                )
                QTimer.singleShot(50, lambda: self.display_tank_cards_in_panel(empty_plan, self.current_ship))
            else:
                # Plan exists - refresh to show excluded status on empty tanks
                QTimer.singleShot(50, lambda: self.display_tank_cards_in_panel(self.current_plan, self.current_ship))
    
    def is_tank_excluded(self, tank_id: str) -> bool:
        """Check if a tank is excluded from planning"""
        return tank_id in self.excluded_tanks
    
    def handle_empty_tank(self, tank_id: str):
        """Handle emptying a single tank"""
        if not self.current_plan or not self.current_ship:
            return
        
        # Remove assignment from plan
        self.current_plan.remove_assignment(tank_id)
        
        # Remove from fixed_assignments if present
        if tank_id in self.fixed_assignments:
            del self.fixed_assignments[tank_id]
        
        # Clear UNDO history after manual edit
        self.last_tank_swap_state = None
        self.update_undo_menu_state()
        
        # Generate colors for cargo types
        cargo_colors = self._generate_colors(len(self.current_plan.cargo_requests)) if self.current_plan else []
        
        # Refresh display
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(100, lambda: self.display_tank_cards_in_panel(self.current_plan, self.current_ship))
        self.plan_viewer.display_plan(self.current_plan, self.current_ship, cargo_colors)
        
        # Update LEGEND with new loaded quantities
        if hasattr(self, 'cargo_legend') and self.current_plan:
            self.cargo_legend.update_loaded_quantities(self.current_plan)
        
        # Update button states
        self.update_remaining_cargo_button_state()
        self.update_fill_100_button_state()
    
    def handle_unlock_tank(self, tank_id: str):
        """Handle unlocking a locked tank"""
        if not self.current_plan or not self.current_ship:
            return
        
        # Remove from fixed_assignments if present (unlock the tank)
        if tank_id in self.fixed_assignments:
            del self.fixed_assignments[tank_id]
        else:
            # Tank is not locked, nothing to do
            return
        
        # Keep assignment in current_plan.assignments (do NOT remove assignment)
        # The tank still has its cargo, just becomes unlocked
        
        # Clear UNDO history after manual edit
        self.last_tank_swap_state = None
        self.update_undo_menu_state()
        
        # Generate colors for cargo types
        cargo_colors = self._generate_colors(len(self.current_plan.cargo_requests)) if self.current_plan else []
        
        # Refresh display to update visual state (remove "Kilitli" label, enable dragging)
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(100, lambda: self.display_tank_cards_in_panel(self.current_plan, self.current_ship))
        self.plan_viewer.display_plan(self.current_plan, self.current_ship, cargo_colors)
        
        # Update LEGEND (quantities remain the same, but display may need refresh)
        if hasattr(self, 'cargo_legend') and self.current_plan:
            self.cargo_legend.update_loaded_quantities(self.current_plan)
        
        # Update button states
        self.update_remaining_cargo_button_state()
        self.update_fill_100_button_state()
    
    def create_optimized_plan(self):
        """Create optimized stowage plan"""
        if not self.current_ship:
            QMessageBox.warning(
                self,
                "Eksik Bilgi",
                "Lütfen gemi profili seçin."
            )
            return
        
        # Get cargo requests from input widget
        self.current_cargo_requests = self.cargo_input_widget.get_cargo_list()
        
        if not self.current_cargo_requests:
            QMessageBox.warning(
                self,
                "Eksik Bilgi",
                "Lütfen en az bir yükleme talebi girin."
            )
            return
        
        from optimizer.stowage_optimizer import StowageOptimizer
        from ui.plan_selection_dialog import PlanSelectionDialog
        
        # Validate
        is_valid, error_msg = StowageOptimizer.validate_plan(
            self.current_ship, self.current_cargo_requests
        )
        
        if not is_valid:
            QMessageBox.critical(self, "Hata", error_msg)
            return
        
        # Check which optimization algorithm to use (from settings)
        algorithm = self.optimization_settings.get('optimization_algorithm', 'genetic')
        
        # Set cursor to wait (hourglass) during optimization
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        
        solutions = None
        try:
            if algorithm == 'genetic':
                # Use Genetic Algorithm optimizer
                from optimizer.genetic_optimizer import GeneticOptimizer
                
                # Validate using GA validator
                is_valid, error_msg = GeneticOptimizer.validate_plan(
                    self.current_ship, self.current_cargo_requests
                )
                
                if not is_valid:
                    QMessageBox.critical(self, "Hata", error_msg)
                    return
                
                # Create GA optimizer
                ga_optimizer = GeneticOptimizer(
                    self.current_ship,
                    self.current_cargo_requests,
                    excluded_tanks=self.excluded_tanks if self.excluded_tanks else None,
                    settings=self.optimization_settings
                )
                
                # Run optimization
                best_plan = ga_optimizer.optimize()
                
                # Score the plan
                from optimizer.stowage_optimizer import StowageOptimizer
                score = StowageOptimizer.score_plan(best_plan, self.current_ship)
                solutions = [(best_plan, score, "Genetik Algoritma")]
            else:
                # Use advanced optimizer with retry mechanism (default)
                from optimizer.advanced_optimizer import AdvancedStowageOptimizer
                
                # Generate plan using advanced optimizer with multiple retries
                best_plan = AdvancedStowageOptimizer.optimize_with_fixed_and_retry(
                    self.current_ship,
                    self.current_cargo_requests,
                    excluded_tanks=self.excluded_tanks if self.excluded_tanks else None,
                    fixed_assignments=None,
                    num_retries=5,
                    settings=self.optimization_settings
                )
                
                # For compatibility with existing code, create solutions list
                from optimizer.stowage_optimizer import StowageOptimizer
                score = StowageOptimizer.score_plan(best_plan, self.current_ship)
                solutions = [(best_plan, score, "Gelişmiş Algoritma")]
        finally:
            # Restore normal cursor
            QApplication.restoreOverrideCursor()
        
        if not solutions:
            QMessageBox.critical(self, "Hata", "Hiçbir çözüm üretilemedi.")
            return
        
        # If only one solution or all are identical, use it directly
        if len(solutions) == 1:
            self.current_plan = solutions[0][0]
        else:
            # Show selection dialog
            dialog = PlanSelectionDialog(self, solutions)
            if dialog.exec():
                self.current_plan = dialog.selected_plan
            else:
                # User cancelled, use best solution anyway
                self.current_plan = solutions[0][0]
        
        # Keep excluded tanks (empty tanks can still be excluded after plan creation)
        # Don't clear excluded_tanks - allow excluding empty tanks even after plan creation
        
        # Clear fixed assignments and UNDO history when new plan is created
        self.fixed_assignments.clear()
        self.last_tank_swap_state = None
        self.update_undo_menu_state()
        
        # Generate colors for cargo types
        cargo_colors = self._generate_colors(len(self.current_plan.cargo_requests)) if self.current_plan else []
        
        # Display plan (table in right panel, cards in top panel)
        self.plan_viewer.display_plan(self.current_plan, self.current_ship, cargo_colors)
        # Use QTimer to ensure scroll area has proper width before calculating card sizes
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(100, lambda: self.display_tank_cards_in_panel(self.current_plan, self.current_ship))
        
        # Check for unfulfilled cargo
        unfulfilled = StowageOptimizer.get_unfulfilled_cargo(self.current_plan)
        if unfulfilled:
            msg = "Bazı yükler tam olarak yüklenemedi:\n\n"
            for cargo in unfulfilled:
                msg += f"- {cargo.cargo_type}: {cargo.quantity:.2f} kaldı\n"
            QMessageBox.warning(self, "Uyarı", msg)
        
        # Update LEGEND and button states
        if hasattr(self, 'cargo_legend') and self.current_plan:
            self.cargo_legend.set_cargo_list(self.current_plan.cargo_requests, cargo_colors, self.current_plan)
        self.update_remaining_cargo_button_state()
        self.update_fill_100_button_state()
    
    def create_remaining_cargo_plan(self):
        """Create plan for remaining cargos using fixed assignments"""
        if not self.current_plan or not self.current_ship:
            QMessageBox.warning(
                self,
                "Plan Yok",
                "Lütfen önce bir plan oluşturun."
            )
            return
        
        # Check if there are any manual assignments in the plan
        if not self.current_plan.assignments:
            QMessageBox.warning(
                self,
                "Manuel Atama Yok",
                "Kalan yükleri planlamak için önce manuel atama yapmalısınız."
            )
            return
        
        # STEP 0: On first call, lock all current assignments as fixed
        # On subsequent calls, identify and clear only algorithm results
        is_first_call = len(self.fixed_assignments) == 0
        
        if is_first_call:
            # First call: Lock all current assignments as fixed (drag-drop assignments)
            for tank_id, assignment in self.current_plan.assignments.items():
                self.fixed_assignments[tank_id] = assignment
        else:
            # Subsequent calls: Identify and clear only algorithm results
            current_fixed_tank_ids = set(self.fixed_assignments.keys())
            algorithm_result_tank_ids = []
            for tank_id in list(self.current_plan.assignments.keys()):
                if tank_id not in current_fixed_tank_ids:
                    algorithm_result_tank_ids.append(tank_id)
            
            # STEP 1: Clear algorithm results from current plan (keep only fixed assignments)
            for tank_id in algorithm_result_tank_ids:
                self.current_plan.remove_assignment(tank_id)
            
            # STEP 2: Update fixed_assignments with any new manual assignments
            # (in case user added new drag-drop assignments after first call)
            for tank_id, assignment in self.current_plan.assignments.items():
                if tank_id not in self.fixed_assignments:
                    # New manual assignment, add to fixed
                    self.fixed_assignments[tank_id] = assignment
        
        # STEP 3: Get remaining cargos and tanks (after clearing algorithm results)
        remaining_cargos = self.current_plan.get_remaining_cargos(self.fixed_assignments)
        remaining_tanks = self.current_plan.get_remaining_tanks(
            self.current_ship, 
            self.fixed_assignments, 
            self.excluded_tanks
        )
        
        # If no remaining cargos, check if we should clear algorithm results and re-plan
        if not remaining_cargos:
            # Check if there are algorithm results (non-fixed assignments) that can be cleared
            if is_first_call:
                # First call: All assignments were just locked as fixed
                # If remaining_cargos is empty, it means all cargos are assigned
                # Since this is the first call, all assignments are likely algorithm results
                # Clear all assignments and fixed_assignments, then re-plan
                self.current_plan.assignments.clear()
                self.fixed_assignments.clear()
                
                # Recalculate remaining cargos (should now be all cargos)
                remaining_cargos = self.current_plan.get_remaining_cargos(self.fixed_assignments)
                remaining_tanks = self.current_plan.get_remaining_tanks(
                    self.current_ship, 
                    self.fixed_assignments, 
                    self.excluded_tanks
                )
                
                # If still no remaining cargos, it means all cargos are in manual assignments
                # This shouldn't happen, but check anyway
                if not remaining_cargos:
                    QMessageBox.information(
                        self,
                        "Bilgi",
                        "Tüm yükler zaten atanmış. Planlamaya gerek yok."
                    )
                    return
            else:
                # Subsequent call: Check if there are any non-fixed assignments
                # If all assignments are fixed (manual), then truly no remaining cargos
                current_fixed_tank_ids = set(self.fixed_assignments.keys())
                non_fixed_assignments = [
                    tank_id for tank_id in self.current_plan.assignments.keys()
                    if tank_id not in current_fixed_tank_ids
                ]
                
                if non_fixed_assignments:
                    # There are algorithm results, but remaining_cargos is empty
                    # This shouldn't happen, but clear them anyway and re-plan
                    for tank_id in non_fixed_assignments:
                        self.current_plan.remove_assignment(tank_id)
                    
                    # Recalculate remaining cargos
                    remaining_cargos = self.current_plan.get_remaining_cargos(self.fixed_assignments)
                    remaining_tanks = self.current_plan.get_remaining_tanks(
                        self.current_ship, 
                        self.fixed_assignments, 
                        self.excluded_tanks
                    )
                    
                    if not remaining_cargos:
                        QMessageBox.information(
                            self,
                            "Bilgi",
                            "Tüm yükler zaten atanmış. Planlamaya gerek yok."
                        )
                        return
                else:
                    # All assignments are fixed (manual), truly no remaining cargos
                    QMessageBox.information(
                        self,
                        "Bilgi",
                        "Tüm yükler zaten atanmış. Planlamaya gerek yok."
                    )
                    return
        
        if not remaining_tanks:
            QMessageBox.warning(
                self,
                "Tank Yok",
                "Kalan yükleri planlamak için boş tank bulunmuyor."
            )
            return
        
        # Validate remaining cargos
        from optimizer.stowage_optimizer import StowageOptimizer
        is_valid, error_msg = StowageOptimizer.validate_plan(
            self.current_ship, remaining_cargos
        )
        
        if not is_valid:
            QMessageBox.critical(self, "Hata", error_msg)
            return
        
        # Check which optimization algorithm to use
        algorithm = self.algo_combo.currentData() if hasattr(self, 'algo_combo') else 'genetic'
        
        # Set cursor to wait (hourglass) during optimization
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        
        try:
            # STEP 4: Prepare excluded tanks (include fixed tank IDs for algorithm)
            fixed_tank_ids = set(self.fixed_assignments.keys())
            excluded_tanks_for_algo = (self.excluded_tanks.copy() if self.excluded_tanks else set()) | fixed_tank_ids
            
            if algorithm == 'genetic':
                # Use Genetic Algorithm optimizer
                from optimizer.genetic_optimizer import GeneticOptimizer
                
                # Validate using GA validator
                is_valid, error_msg = GeneticOptimizer.validate_plan(
                    self.current_ship, remaining_cargos
                )
                
                if not is_valid:
                    QMessageBox.critical(self, "Hata", error_msg)
                    return
                
                # Create GA optimizer - fixed tanks are already in excluded_tanks
                ga_optimizer = GeneticOptimizer(
                    self.current_ship,
                    remaining_cargos,
                    excluded_tanks=excluded_tanks_for_algo,
                    fixed_assignments=None,  # Not passed to algorithm - fixed tanks are in excluded_tanks
                    settings=self.optimization_settings
                )
                
                # Run optimization
                remaining_plan = ga_optimizer.optimize()
                
                # STEP 5: Merge remaining plan into current plan
                # Fixed assignments are already in current_plan, just add remaining plan assignments
                for tank_id, assignment in remaining_plan.assignments.items():
                    # Skip if this tank already has a fixed assignment
                    if tank_id not in self.fixed_assignments:
                        self.current_plan.add_assignment(tank_id, assignment)
            else:
                # Use advanced optimizer
                from optimizer.advanced_optimizer import AdvancedStowageOptimizer
                
                # Generate plan using advanced optimizer - fixed tanks are already in excluded_tanks
                remaining_plan = AdvancedStowageOptimizer.optimize_with_fixed_and_retry(
                    self.current_ship,
                    remaining_cargos,
                    excluded_tanks=excluded_tanks_for_algo,
                    fixed_assignments=None,  # Not passed to algorithm - fixed tanks are in excluded_tanks
                    num_retries=5,
                    settings=self.optimization_settings
                )
                
                # STEP 5: Merge remaining plan into current plan
                # Fixed assignments are already in current_plan, just add remaining plan assignments
                for tank_id, assignment in remaining_plan.assignments.items():
                    # Skip if this tank already has a fixed assignment
                    if tank_id not in self.fixed_assignments:
                        self.current_plan.add_assignment(tank_id, assignment)
        finally:
            # Restore normal cursor
            QApplication.restoreOverrideCursor()
        
        # Generate colors for cargo types
        cargo_colors = self._generate_colors(len(self.current_plan.cargo_requests)) if self.current_plan else []
        
        # Display updated plan
        self.plan_viewer.display_plan(self.current_plan, self.current_ship, cargo_colors)
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(100, lambda: self.display_tank_cards_in_panel(self.current_plan, self.current_ship))
        
        # Update LEGEND
        if hasattr(self, 'cargo_legend') and self.current_plan:
            self.cargo_legend.update_loaded_quantities(self.current_plan)
        
        # Update button state
        self.update_remaining_cargo_button_state()
        self.update_fill_100_button_state()
        
        # Check for unfulfilled cargo
        from optimizer.stowage_optimizer import StowageOptimizer
        unfulfilled = StowageOptimizer.get_unfulfilled_cargo(self.current_plan)
        if unfulfilled:
            msg = "Bazı yükler tam olarak yüklenemedi:\n\n"
            for cargo in unfulfilled:
                msg += f"- {cargo.cargo_type}: {cargo.quantity:.2f} kaldı\n"
            QMessageBox.warning(self, "Uyarı", msg)
        else:
            QMessageBox.information(
                self,
                "Başarılı",
                "Kalan yükler başarıyla planlandı."
            )
    
    def save_current_plan(self):
        """Save current plan to file"""
        if not self.current_plan:
            QMessageBox.warning(
                self,
                "Plan Yok",
                "Kaydedilecek bir plan bulunmuyor."
            )
            return
        
        # Open file save dialog directly
        from PyQt6.QtWidgets import QFileDialog
        
        # Generate default filename from plan name
        default_filename = "Plan.json"
        if self.current_plan.plan_name:
            # Remove invalid characters from filename
            invalid_chars = '<>:"/\\|?*'
            plan_name = self.current_plan.plan_name
            for char in invalid_chars:
                plan_name = plan_name.replace(char, '_')
            default_filename = f"{plan_name}.json"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Planı Kaydet",
            default_filename,
            "JSON Dosyaları (*.json);;Tüm Dosyalar (*.*)"
        )
        
        if file_path:
            # Update plan's excluded_tanks before saving
            self.current_plan.excluded_tanks = list(self.excluded_tanks) if self.excluded_tanks else []
            
            # Update plan's cargo_requests with current cargo input values
            # This ensures that any changes made in the cargo input dialog are saved
            if hasattr(self, 'current_cargo_requests') and self.current_cargo_requests:
                self.current_plan.cargo_requests = self.current_cargo_requests
            
            # Save plan to selected file
            if self.storage.save_plan_to_file(self.current_plan, file_path):
                QMessageBox.information(
                    self,
                    "Başarılı",
                    f"Plan başarıyla kaydedildi.\n"
                    f"Konum: {file_path}"
                )
            else:
                QMessageBox.critical(
                    self,
                    "Hata",
                    f"Plan kaydedilirken bir hata oluştu.\n"
                    f"Konum: {file_path}"
                )
    
    def load_plan_from_archive(self):
        """Load a plan from file"""
        from PyQt6.QtWidgets import QFileDialog
        
        # Open file dialog directly
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Plan Yükle",
            "",
            "JSON Dosyaları (*.json);;Tüm Dosyalar (*.*)"
        )
        
        if file_path:
            plan = self.storage.load_plan_from_file(file_path)
            if plan:
                self.current_plan = plan
                # Load associated ship
                self.current_ship = self.storage.load_ship_profile(plan.ship_profile_id)
                if self.current_ship:
                    # Load excluded tanks from plan
                    if plan.excluded_tanks:
                        self.excluded_tanks = set(plan.excluded_tanks)
                    else:
                        self.excluded_tanks.clear()
                    # Clear fixed assignments and UNDO history when loading plan
                    self.fixed_assignments.clear()
                    self.last_tank_swap_state = None
                    self.update_undo_menu_state()
                    # Load cargo requests
                    self.current_cargo_requests = plan.cargo_requests
                    self.cargo_input_widget.set_cargo_list(self.current_cargo_requests)
                    # Generate colors for cargo types
                    cargo_colors = self._generate_colors(len(plan.cargo_requests)) if plan.cargo_requests else []
                    # Display plan
                    self.plan_viewer.display_plan(plan, self.current_ship, cargo_colors)
                    self.display_tank_cards_in_panel(plan, self.current_ship)
                    
                    # Update LEGEND
                    if hasattr(self, 'cargo_legend'):
                        self.cargo_legend.set_cargo_list(plan.cargo_requests, cargo_colors, plan)
                    
                    # Update optimize button state after loading plan
                    self.update_optimize_button_state()
                    self.update_fill_100_button_state()
                    
                    # Update window title and save last profile
                    self.update_window_title()
                    self.storage.save_last_profile_id(self.current_ship.id)
                    
                    QMessageBox.information(
                        self,
                        "Plan Yüklendi",
                        f"Plan '{plan.plan_name}' başarıyla yüklendi."
                    )
                else:
                    # Update button state even if ship profile not found
                    self.update_optimize_button_state()
                    self.update_fill_100_button_state()
                    QMessageBox.critical(
                        self,
                        "Hata",
                        f"Plan ile ilişkili gemi profili bulunamadı: {plan.ship_profile_id}"
                    )
            else:
                QMessageBox.critical(
                    self,
                    "Hata",
                    "Plan dosyası yüklenirken bir hata oluştu.\n"
                    "Dosya formatı geçersiz olabilir."
                )
    
    def display_tank_cards_in_panel(self, plan: StowagePlan, ship: Ship):
        """Display tank cards in ship schematic grid layout"""
        if not ship:
            return
        
        if not hasattr(self, 'ship_schematic'):
            # Fallback to old method if schematic widget doesn't exist
            return
        
        # Generate colors for cargo types
        cargo_colors = self._generate_colors(len(plan.cargo_requests))
        
        # Create a callback function to create tank cards
        def create_card(tank, assignment, utilization, color, is_excluded=False):
            # Check if tank has fixed assignment
            is_fixed = tank.id in self.fixed_assignments
            return self._create_tank_card_compact(tank, assignment, utilization, color, 150, is_excluded, is_fixed)
        
        # Store colors for use in schematic widget if needed
        create_card._cargo_colors = cargo_colors
        
        # Display tanks in schematic (pass excluded tanks info)
        # Show excluded status for empty tanks (both before and after plan creation)
        excluded_tanks_to_show = self.excluded_tanks
        self.ship_schematic.display_tanks(plan, ship, create_card, excluded_tanks_to_show)
    
    def handle_cargo_drop(self, cargo_id: str, tank_id: str):
        """Handle cargo drop from LEGEND to tank
        
        Args:
            cargo_id: Unique ID of the cargo being dropped
            tank_id: ID of the tank receiving the drop
        """
        if not self.current_plan or not self.current_ship:
            QMessageBox.warning(
                self,
                "Plan Yok",
                "Lütfen önce gemi profili seçin ve yük listesi oluşturun."
            )
            return
        
        # Find the cargo
        cargo = None
        for c in self.current_plan.cargo_requests:
            if c.unique_id == cargo_id:
                cargo = c
                break
        
        if not cargo:
            return
        
        # Get the tank
        tank = self.current_ship.get_tank_by_id(tank_id)
        if not tank:
            return
        
        # Calculate quantity to load
        # Option: Use cargo's full quantity if fits, otherwise use tank capacity
        remaining_cargo = cargo.quantity - self.current_plan.get_cargo_total_loaded(cargo.unique_id)
        quantity_to_load = min(remaining_cargo, tank.volume)
        
        # If no remaining cargo, ask user
        if remaining_cargo <= 0.001:
            QMessageBox.warning(
                self,
                "Yük Tamamlandı",
                f"{cargo.cargo_type} yükünün tamamı zaten yüklenmiş."
            )
            return
        
        # Create assignment
        from models.plan import TankAssignment
        new_assignment = TankAssignment(
            tank_id=tank_id,
            cargo=cargo,
            quantity_loaded=quantity_to_load
        )
        
        # Check if tank already has an assignment
        existing_assignment = self.current_plan.get_assignment(tank_id)
        if existing_assignment:
            reply = QMessageBox.question(
                self,
                "Tank Dolu",
                f"{tank.name} tankı zaten {existing_assignment.cargo.cargo_type} ile dolu.\n\n"
                f"Yeni yükü bu tanka atamak istiyor musunuz?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        # Add assignment
        self.current_plan.add_assignment(tank_id, new_assignment)
        
        # Note: Do NOT mark as fixed assignment here - fixed assignments will be set
        # when "Kalan Yükleri Planla" button is pressed
        
        # Refresh display
        cargo_colors = self._generate_colors(len(self.current_plan.cargo_requests)) if self.current_plan else []
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(100, lambda: self.display_tank_cards_in_panel(self.current_plan, self.current_ship))
        self.plan_viewer.display_plan(self.current_plan, self.current_ship, cargo_colors)
        
        # Update LEGEND with new loaded quantities
        if hasattr(self, 'cargo_legend') and self.current_plan:
            self.cargo_legend.update_loaded_quantities(self.current_plan)
        
        # Update "Kalan Yükleri Planla" button visibility
        self.update_remaining_cargo_button_state()
        self.update_fill_100_button_state()
    
    def handle_tank_double_click(self, tank_id: str):
        """Handle double click on tank card to edit cargo assignment"""
        if not self.current_plan or not self.current_ship:
            return
        
        tank = self.current_ship.get_tank_by_id(tank_id)
        if not tank:
            return
        
        # Otherwise, show edit dialog
        from ui.tank_cargo_edit_dialog import TankCargoEditDialog
        
        dialog = TankCargoEditDialog(
            self,
            plan=self.current_plan,
            ship=self.current_ship,
            tank=tank
        )
        
        if dialog.exec():
            from models.plan import TankAssignment
            
            if dialog.selected_cargo:
                # Assign cargo to tank
                new_assignment = TankAssignment(
                    tank_id=tank_id,
                    cargo=dialog.selected_cargo,
                    quantity_loaded=dialog.selected_quantity
                )
                # Add assignment
                self.current_plan.add_assignment(tank_id, new_assignment)
                # Note: Do NOT mark as fixed assignment here - fixed assignments will be set
                # when "Kalan Yükleri Planla" button is pressed
            else:
                # Empty the tank
                self.current_plan.remove_assignment(tank_id)
                # Note: Do NOT remove from fixed_assignments here - fixed assignments will be set
                # when "Kalan Yükleri Planla" button is pressed
            
            # Generate colors for cargo types
            cargo_colors = self._generate_colors(len(self.current_plan.cargo_requests)) if self.current_plan else []
            
            # Refresh display immediately (no timer delay to ensure fixed_assignments is updated)
            self.display_tank_cards_in_panel(self.current_plan, self.current_ship)
            self.plan_viewer.display_plan(self.current_plan, self.current_ship, cargo_colors)
            
            # Update LEGEND with new loaded quantities
            if hasattr(self, 'cargo_legend') and self.current_plan:
                self.cargo_legend.update_loaded_quantities(self.current_plan)
            
            # Clear UNDO history after manual edit (double-click)
            self.last_tank_swap_state = None
            self.update_undo_menu_state()
            
            # Update "Kalan Yükleri Planla" button visibility
            self.update_remaining_cargo_button_state()
            self.update_fill_100_button_state()
    
    def handle_tank_swap(self, source_tank_id: str, target_tank_id: str):
        """Handle tank assignment swap via drag-and-drop"""
        if not self.current_plan or not self.current_ship:
            return
        
        source_assignment = self.current_plan.get_assignment(source_tank_id)
        target_assignment = self.current_plan.get_assignment(target_tank_id)
        
        if not source_assignment:
            return
        
        source_tank = self.current_ship.get_tank_by_id(source_tank_id)
        target_tank = self.current_ship.get_tank_by_id(target_tank_id)
        
        if not source_tank or not target_tank:
            return
        
        # Plan oluşturulduktan sonra elle düzenleme yapılırken yük miktarı kısıtı kaldırıldı
        # Artık yükün toplam miktarı (cargo.quantity) kontrolü yapılmıyor
        # Sadece tank kapasitesi kısıtı uygulanıyor
        
        # Save current state for UNDO (before making changes)
        from models.plan import TankAssignment
        from models.cargo import Cargo, Receiver
        
        # Deep copy assignments for UNDO
        saved_source_assignment = None
        saved_target_assignment = None
        
        if source_assignment:
            # Deep copy cargo and receivers
            copied_receivers = [Receiver(name=r.name) for r in source_assignment.cargo.receivers]
            copied_cargo = Cargo(
                cargo_type=source_assignment.cargo.cargo_type,
                quantity=source_assignment.cargo.quantity,
                receivers=copied_receivers,
                unique_id=source_assignment.cargo.unique_id
            )
            saved_source_assignment = TankAssignment(
                tank_id=source_tank_id,
                cargo=copied_cargo,
                quantity_loaded=source_assignment.quantity_loaded
            )
        
        if target_assignment:
            # Deep copy cargo and receivers
            copied_receivers = [Receiver(name=r.name) for r in target_assignment.cargo.receivers]
            copied_cargo = Cargo(
                cargo_type=target_assignment.cargo.cargo_type,
                quantity=target_assignment.cargo.quantity,
                receivers=copied_receivers,
                unique_id=target_assignment.cargo.unique_id
            )
            saved_target_assignment = TankAssignment(
                tank_id=target_tank_id,
                cargo=copied_cargo,
                quantity_loaded=target_assignment.quantity_loaded
            )
        
        # Store state for UNDO
        self.last_tank_swap_state = {
            'source_tank_id': source_tank_id,
            'target_tank_id': target_tank_id,
            'source_assignment': saved_source_assignment,
            'target_assignment': saved_target_assignment
        }
        
        # Remove old assignments for these two tanks
        if source_tank_id in self.current_plan.assignments:
            del self.current_plan.assignments[source_tank_id]
        if target_tank_id in self.current_plan.assignments:
            del self.current_plan.assignments[target_tank_id]
        
        # Calculate new quantities: adjust to tank capacities
        # Plan oluşturulduktan sonra elle düzenleme yapılırken yük miktarı kısıtı kaldırıldı
        # Kullanıcı tank kapasitesine kadar yükleyebilir (sadece tank kapasitesi kısıtı)
        # Target tank: fill with source cargo up to tank capacity
        target_quantity = target_tank.volume
        
        # Source tank: if swapping, fill with target cargo up to tank capacity
        source_quantity = 0.0
        if target_assignment:
            source_quantity = source_tank.volume
        
        # Check warning threshold for target tank
        drag_drop_threshold = self.optimization_settings.get('drag_drop_warning_threshold', 0.70) * 100
        target_utilization = (target_quantity / target_tank.volume * 100) if target_tank.volume > 0 else 0
        if target_quantity > 0 and target_utilization < drag_drop_threshold:
            reply = QMessageBox.question(
                self,
                "Uyarı",
                f"Hedef tank {target_utilization:.1f}% dolacak. Minimum {drag_drop_threshold:.0f}% kuralı ihlal ediliyor.\n"
                f"Yine de devam etmek istiyor musunuz?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                # Restore assignments
                if source_assignment:
                    self.current_plan.add_assignment(source_tank_id, source_assignment)
                if target_assignment:
                    self.current_plan.add_assignment(target_tank_id, target_assignment)
                # Clear history since operation was cancelled
                self.last_tank_swap_state = None
                self.update_undo_menu_state()
                return
        
        # Check warning threshold for source tank (only if swapping and quantity > 0)
        if source_quantity > 0.001:
            source_utilization = (source_quantity / source_tank.volume * 100) if source_tank.volume > 0 else 0
            if source_utilization < drag_drop_threshold:
                reply = QMessageBox.question(
                    self,
                    "Uyarı",
                    f"Kaynak tank {source_utilization:.1f}% dolacak. Minimum {drag_drop_threshold:.0f}% kuralı ihlal ediliyor.\n"
                    f"Yine de devam etmek istiyor musunuz?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    # Restore assignments
                    if source_assignment:
                        self.current_plan.add_assignment(source_tank_id, source_assignment)
                    if target_assignment:
                        self.current_plan.add_assignment(target_tank_id, target_assignment)
                    # Clear history since operation was cancelled
                    self.last_tank_swap_state = None
                    self.update_undo_menu_state()
                    return
        
        # Create new assignments with maximized quantities
        # Target gets source's cargo (filled to capacity if available)
        new_target_assignment = TankAssignment(
            tank_id=target_tank_id,
            cargo=source_assignment.cargo,
            quantity_loaded=target_quantity
        )
        # Add assignments
        self.current_plan.add_assignment(target_tank_id, new_target_assignment)
        
        # Source gets target's cargo (if swapping) or becomes empty
        # ÖNCE new_source_assignment'ı oluştur (eğer swap durumu varsa)
        new_source_assignment = None
        if target_assignment and source_quantity > 0.001:
            new_source_assignment = TankAssignment(
                tank_id=source_tank_id,
                cargo=target_assignment.cargo,
                quantity_loaded=source_quantity
            )
            self.current_plan.add_assignment(source_tank_id, new_source_assignment)
        
        # Note: Do NOT update fixed_assignments here - fixed assignments will be set
        # when "Kalan Yükleri Planla" button is pressed
        
        # Generate colors for cargo types
        cargo_colors = self._generate_colors(len(self.current_plan.cargo_requests)) if self.current_plan else []
        
        # Refresh display (cards and comparison table)
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(100, lambda: self.display_tank_cards_in_panel(self.current_plan, self.current_ship))
        self.plan_viewer.display_plan(self.current_plan, self.current_ship, cargo_colors)  # This updates comparison table too
        
        # Calculate utilization percentages
        target_util = (target_quantity / target_tank.volume * 100) if target_tank.volume > 0 else 0
        source_util = (source_quantity / source_tank.volume * 100) if source_tank.volume > 0 and source_quantity > 0 else 0
        
        # Build informative message
        msg = f"Yük {source_tank.name} tankından {target_tank.name} tankına taşındı.\n\n"
        
        # Show adjustment info if cargo was larger than tank capacity
        if source_assignment.quantity_loaded > target_tank.volume:
            msg += f"⚠ {target_tank.name} kapasitesi ({target_tank.volume:.2f} m³) yük miktarından ({source_assignment.quantity_loaded:.2f} m³) küçük olduğu için yük tank kapasitesine göre ayarlandı.\n\n"
        
        msg += f"{target_tank.name}: {target_quantity:.2f} m³ ({target_util:.1f}%)\n"
        if source_quantity > 0:
            if target_assignment and target_assignment.quantity_loaded > source_tank.volume:
                msg += f"⚠ {source_tank.name} kapasitesi ({source_tank.volume:.2f} m³) yük miktarından ({target_assignment.quantity_loaded:.2f} m³) küçük olduğu için yük tank kapasitesine göre ayarlandı.\n"
            msg += f"{source_tank.name}: {source_quantity:.2f} m³ ({source_util:.1f}%)\n"
        else:
            msg += f"{source_tank.name}: Boş\n"
        
        msg += "\nHer iki tank da kapasitelerine göre ayarlandı."
        
        QMessageBox.information(self, "Başarılı", msg)
        
        # Update UNDO menu state after successful swap
        self.update_undo_menu_state()
        
        # Update LEGEND with new loaded quantities
        if hasattr(self, 'cargo_legend') and self.current_plan:
            self.cargo_legend.update_loaded_quantities(self.current_plan)
        
        # Update "Kalan Yükleri Planla" button visibility
        self.update_remaining_cargo_button_state()
        self.update_fill_100_button_state()
    
    def handle_tank_double_click(self, tank_id: str):
        """Handle double click on tank card to edit cargo assignment"""
        if not self.current_plan or not self.current_ship:
            return
        
        tank = self.current_ship.get_tank_by_id(tank_id)
        if not tank:
            return
        
        from ui.tank_cargo_edit_dialog import TankCargoEditDialog
        
        dialog = TankCargoEditDialog(
            self,
            plan=self.current_plan,
            ship=self.current_ship,
            tank=tank
        )
        
        if dialog.exec():
            from models.plan import TankAssignment
            
            if dialog.selected_cargo:
                # Assign cargo to tank
                new_assignment = TankAssignment(
                    tank_id=tank_id,
                    cargo=dialog.selected_cargo,
                    quantity_loaded=dialog.selected_quantity
                )
                # Add assignment
                self.current_plan.add_assignment(tank_id, new_assignment)
            else:
                # Empty the tank
                if tank_id in self.current_plan.assignments:
                    del self.current_plan.assignments[tank_id]
            
            # Generate colors for cargo types
            cargo_colors = self._generate_colors(len(self.current_plan.cargo_requests)) if self.current_plan else []
            
            # Refresh display
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(100, lambda: self.display_tank_cards_in_panel(self.current_plan, self.current_ship))
            self.plan_viewer.display_plan(self.current_plan, self.current_ship, cargo_colors)
            
            # Update LEGEND with new loaded quantities
            if hasattr(self, 'cargo_legend') and self.current_plan:
                self.cargo_legend.update_loaded_quantities(self.current_plan)
            
            # Clear UNDO history after manual edit (double-click)
            self.last_tank_swap_state = None
            self.update_undo_menu_state()
            
            # Update button states
            self.update_remaining_cargo_button_state()
            self.update_fill_100_button_state()
    
    def can_undo(self) -> bool:
        """Check if UNDO is available (last swap can be undone)"""
        return self.last_tank_swap_state is not None
    
    def undo_last_swap(self):
        """Undo the last drag-drop swap operation"""
        if not self.can_undo():
            QMessageBox.warning(
                self,
                "Geri Al",
                "Geri alınacak bir işlem bulunmuyor."
            )
            return
        
        if not self.current_plan or not self.current_ship:
            return
        
        # Get saved state
        state = self.last_tank_swap_state
        source_tank_id = state['source_tank_id']
        target_tank_id = state['target_tank_id']
        saved_source_assignment = state['source_assignment']
        saved_target_assignment = state['target_assignment']
        
        # Remove current assignments
        if source_tank_id in self.current_plan.assignments:
            del self.current_plan.assignments[source_tank_id]
        if target_tank_id in self.current_plan.assignments:
            del self.current_plan.assignments[target_tank_id]
        
        # Restore saved assignments
        if saved_source_assignment:
            self.current_plan.add_assignment(source_tank_id, saved_source_assignment)
        if saved_target_assignment:
            self.current_plan.add_assignment(target_tank_id, saved_target_assignment)
        
        # Clear history (only one undo step)
        self.last_tank_swap_state = None
        
        # Refresh display
        cargo_colors = self._generate_colors(len(self.current_plan.cargo_requests)) if self.current_plan else []
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(100, lambda: self.display_tank_cards_in_panel(self.current_plan, self.current_ship))
        self.plan_viewer.display_plan(self.current_plan, self.current_ship, cargo_colors)
        
        # Update LEGEND with new loaded quantities
        if hasattr(self, 'cargo_legend') and self.current_plan:
            self.cargo_legend.update_loaded_quantities(self.current_plan)
        
        # Update UNDO menu state
        self.update_undo_menu_state()
        
        # Update button states
        self.update_remaining_cargo_button_state()
        self.update_fill_100_button_state()
        
        # Show success message
        source_tank = self.current_ship.get_tank_by_id(source_tank_id)
        target_tank = self.current_ship.get_tank_by_id(target_tank_id)
        QMessageBox.information(
            self,
            "Geri Alındı",
            f"Son işlem geri alındı.\n\n"
            f"{source_tank.name if source_tank else 'Kaynak tank'} ve "
            f"{target_tank.name if target_tank else 'hedef tank'} eski durumlarına döndürüldü."
        )
    
    def update_undo_menu_state(self):
        """Update UNDO menu item enabled/disabled state"""
        if hasattr(self, 'undo_action'):
            self.undo_action.setEnabled(self.can_undo())
    
    def _create_tank_card_compact(self, tank, assignment: Optional[TankAssignment], 
                                  utilization: float, color: str, card_width: int = 150,
                                  is_excluded: bool = False, is_fixed: bool = False) -> QWidget:
        """Create a compact draggable tank card for top panel"""
        from ui.draggable_tank_card import DraggableTankCard
        
        # Use passed is_excluded or check from excluded_tanks
        if not is_excluded:
            is_excluded = tank.id in self.excluded_tanks
        
        # Check if tank has fixed assignment (manual drag-drop assignment)
        if not is_fixed:
            is_fixed = tank.id in self.fixed_assignments
        
        card = DraggableTankCard(tank, assignment, utilization, color, self, is_excluded, 
                                is_planned=False, is_suggested=False, fit_info=None, is_fixed=is_fixed)
        card.setMaximumWidth(card_width)
        card.setMinimumWidth(card_width)
        # Allow cards to resize vertically if needed
        card.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        return card
    
    def _generate_colors(self, count: int) -> list:
        """Generate distinct colors for cargo types"""
        if count == 0:
            return []
        
        # Color palette
        base_colors = [
            "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7",
            "#DDA15E", "#BC6C25", "#6C757D", "#E9C46A", "#F4A261"
        ]
        
        colors = []
        for i in range(count):
            colors.append(base_colors[i % len(base_colors)])
        
        return colors
    
    def fill_tanks_to_100_percent(self):
        """Fill all loaded tanks to 100% capacity while preserving cargo type"""
        if not self.current_plan or not self.current_ship:
            return
        
        # Check if there are any loaded tanks
        has_loaded_tanks = False
        for tank in self.current_ship.tanks:
            assignment = self.current_plan.get_assignment(tank.id)
            if assignment:
                has_loaded_tanks = True
                break
        
        if not has_loaded_tanks:
            QMessageBox.information(
                self,
                "Bilgi",
                "Yüklü tank bulunamadı."
            )
            return
        
        # Fill each loaded tank to 100%
        filled_count = 0
        for tank in self.current_ship.tanks:
            assignment = self.current_plan.get_assignment(tank.id)
            if assignment:
                # Preserve cargo type, just update quantity to tank capacity
                new_assignment = TankAssignment(
                    tank_id=tank.id,
                    cargo=assignment.cargo,  # Preserve cargo type
                    quantity_loaded=tank.volume  # Fill to 100%
                )
                self.current_plan.add_assignment(tank.id, new_assignment)
                filled_count += 1
        
        # Refresh UI
        cargo_colors = self._generate_colors(len(self.current_plan.cargo_requests)) if self.current_plan else []
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(100, lambda: self.display_tank_cards_in_panel(self.current_plan, self.current_ship))
        self.plan_viewer.display_plan(self.current_plan, self.current_ship, cargo_colors)
        
        # Update LEGEND with new loaded quantities
        if hasattr(self, 'cargo_legend') and self.current_plan:
            self.cargo_legend.update_loaded_quantities(self.current_plan)
        
        # Update button state
        self.update_fill_100_button_state()
        
        # Show confirmation message
        QMessageBox.information(
            self,
            "Tamamlandı",
            f"{filled_count} tank %100 kapasiteye getirildi.\n\n"
            f"Not: Bu işlem sipariş miktarını aşabilir."
        )
    
    def update_fill_100_button_state(self):
        """Update '%100 Yap' button enabled state"""
        if not hasattr(self, 'fill_100_btn'):
            return
        
        # Button should be enabled if there's a plan and at least one tank has an assignment
        has_plan = self.current_plan is not None
        has_assignments = False
        
        if has_plan and self.current_ship:
            # Check if at least one tank has an assignment
            for tank in self.current_ship.tanks:
                if self.current_plan.get_assignment(tank.id):
                    has_assignments = True
                    break
        
        self.fill_100_btn.setEnabled(has_plan and has_assignments)
    
    def clear_all_tanks(self):
        """Clear all tank assignments (CTRL+E)"""
        if not self.current_plan:
            QMessageBox.information(
                self,
                "Bilgi",
                "Aktif bir plan bulunmuyor."
            )
            return
        
        # Check if there are locked tanks
        has_locked_tanks = len(self.fixed_assignments) > 0
        cleared_only_planned = False
        
        if has_locked_tanks:
            # Show dialog with three options for locked tanks
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Tüm Tankları Boşalt")
            msg_box.setText("Kilitli tanklar bulunuyor. Nasıl devam etmek istersiniz?")
            msg_box.setInformativeText(
                f"Toplam {len(self.fixed_assignments)} kilitli tank var.\n\n"
                "• Tümünü Boşalt: Tüm tankları (kilitli dahil) boşaltır\n"
                "• Sadece Planlananları Boşalt: Sadece algoritma sonuçlarını boşaltır, kilitli tankları korur\n"
                "• İptal: İşlemi iptal eder"
            )
            
            # Create custom buttons
            clear_all_btn = msg_box.addButton("Tümünü Boşalt", QMessageBox.ButtonRole.AcceptRole)
            clear_planned_btn = msg_box.addButton("Sadece Planlananları Boşalt", QMessageBox.ButtonRole.AcceptRole)
            cancel_btn = msg_box.addButton("İptal", QMessageBox.ButtonRole.RejectRole)
            msg_box.setDefaultButton(cancel_btn)
            
            reply = msg_box.exec()
            
            if reply == QMessageBox.StandardButton.Cancel or msg_box.clickedButton() == cancel_btn:
                return
            elif msg_box.clickedButton() == clear_all_btn:
                # Clear all assignments and fixed assignments
                self.current_plan.assignments.clear()
                self.fixed_assignments.clear()
            elif msg_box.clickedButton() == clear_planned_btn:
                # Only clear non-fixed assignments
                fixed_tank_ids = set(self.fixed_assignments.keys())
                for tank_id in list(self.current_plan.assignments.keys()):
                    if tank_id not in fixed_tank_ids:
                        self.current_plan.remove_assignment(tank_id)
                cleared_only_planned = True
            else:
                return
        else:
            # No locked tanks - proceed with simple Yes/No confirmation
            reply = QMessageBox.question(
                self,
                "Tüm Tankları Boşalt",
                "Tüm tank atamalarını temizlemek istediğinizden emin misiniz?\n\n"
                "Bu işlem geri alınamaz.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply != QMessageBox.StandardButton.Yes:
                return
            
            # Clear all assignments and fixed assignments
            self.current_plan.assignments.clear()
            self.fixed_assignments.clear()
        
        # Clear UNDO history when clearing all tanks
        self.last_tank_swap_state = None
        self.update_undo_menu_state()
        
        # Update button states (this will show "Yükleme Planı Oluştur" again)
        self.update_optimize_button_state()
        self.update_remaining_cargo_button_state()
        self.update_fill_100_button_state()
        
        # Update LEGEND
        if hasattr(self, 'cargo_legend') and self.current_plan:
            self.cargo_legend.update_loaded_quantities(self.current_plan)
        
        # Generate colors for cargo types
        cargo_colors = self._generate_colors(len(self.current_plan.cargo_requests)) if self.current_plan else []
        
        # Refresh display
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(100, lambda: self.display_tank_cards_in_panel(self.current_plan, self.current_ship))
        self.plan_viewer.display_plan(self.current_plan, self.current_ship, cargo_colors)
        
        # Show appropriate success message
        success_msg = "Planlanan tanklar boşaltıldı." if cleared_only_planned else "Tüm tanklar boşaltıldı."
        QMessageBox.information(
            self,
            "Başarılı",
            success_msg
        )
    
    def open_optimization_settings(self):
        """Open optimization settings dialog"""
        from ui.optimization_settings_dialog import OptimizationSettingsDialog
        
        dialog = OptimizationSettingsDialog(self, self.optimization_settings)
        if dialog.exec():
            # Get new settings
            new_settings = dialog.get_settings()
            
            # Save settings
            if self.storage.save_optimization_settings(new_settings):
                self.optimization_settings = new_settings
                QMessageBox.information(
                    self,
                    "Ayarlar Kaydedildi",
                    "Optimizasyon ayarları başarıyla kaydedildi."
                )
                # No automatic re-planning - user can manually trigger planning if needed
            else:
                QMessageBox.critical(
                    self,
                    "Hata",
                    "Ayarlar kaydedilirken bir hata oluştu."
                )
    
    def show_help(self):
        """Show help dialog with user manual"""
        from ui.help_dialog import HelpDialog
        dialog = HelpDialog(self)
        dialog.exec()
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "Hakkında",
            "<b>Tanker Stowage Plan Uygulaması</b><br><br>"
            "Bu uygulama, tanker yükleme planlamasına yardımcı olmak üzere Akın Kaptan (akinkaptan77@hotmail.com) tarafından geliştirilmiştir."
        )

