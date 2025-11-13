"""Widget for displaying ship schematic with tank cards in grid layout"""

from PyQt6.QtWidgets import (QWidget, QGridLayout, QVBoxLayout, QLabel,
                             QSpacerItem, QSizePolicy)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor

from models.ship import Ship
from models.plan import StowagePlan, TankAssignment


class ShipSchematicWidget(QWidget):
    """Widget that displays ship schematic with tanks arranged in grid"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.plan: StowagePlan = None
        self.ship: Ship = None
        self.tank_cards = {}  # {(row, side): DraggableTankCard}
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 5)  # Reduce top margin significantly
        
        # Title removed - not needed
        
        # Main container with grid layout
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(5)  # Reduced from 15 to 5
        self.grid_layout.setContentsMargins(5, 2, 5, 5)  # Reduced top margin
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # No side headers needed - tank cards are self-explanatory
        
        layout.addWidget(self.grid_container)
        layout.addStretch()
    
    def group_tanks_by_row(self, ship: Ship) -> dict:
        """
        Group tanks by row number based on their order
        Returns: {row_number: {"port": Tank, "starboard": Tank}}
        """
        groups = {}
        for idx, tank in enumerate(ship.tanks):
            row_number = (idx // 2) + 1
            side = "port" if idx % 2 == 0 else "starboard"
            if row_number not in groups:
                groups[row_number] = {}
            groups[row_number][side] = tank
        return groups
    
    def display_tanks(self, plan: StowagePlan, ship: Ship, 
                     create_card_callback, excluded_tanks: set = None):
        """Display tanks in grid layout"""
        self.plan = plan
        self.ship = ship
        
        # Clear existing cards
        self.clear_tanks()
        
        if not ship or not ship.tanks:
            return
        
        excluded_tanks = excluded_tanks or set()
        
        # Group tanks by row
        tank_groups = self.group_tanks_by_row(ship)
        
        # Colors are already applied in the callback function
        
        # Horizontal layout: rows are sides (Port=row 1, Starboard=row 2), columns are tank numbers
        # Ship's bow is on the right, so tanks are ordered right-to-left (Tank 1 on right)
        # Tank 1 should be rightmost, so we reverse the column positions
        tank_numbers_sorted = sorted(tank_groups.keys())  # Normal order: 1, 2, 3, 4, 5...
        max_tank_number = max(tank_groups.keys()) if tank_groups else 0
        
        # Create mapping: tank_number -> column_position (rightmost = highest column number)
        # Tank 1 gets highest column number (rightmost), Tank N gets column 1 (leftmost)
        tank_to_col = {tank_num: max_tank_number - tank_num + 1 for tank_num in tank_numbers_sorted}
        
        # Column headers (tank numbers) - right to left
        for tank_number in tank_numbers_sorted:
            col_pos = tank_to_col[tank_number]
            col_header = QLabel(f"Tank {tank_number}")
            col_header.setStyleSheet("font-weight: bold; font-size: 11pt; margin: 0px; padding: 0px;")
            col_header.setContentsMargins(0, 0, 0, 0)
            col_header.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
            col_header.setMinimumHeight(15)  # Reduce minimum height
            col_header.setMaximumHeight(20)  # Limit maximum height
            self.grid_layout.addWidget(col_header, 0, col_pos, Qt.AlignmentFlag.AlignCenter)
        
        # Add tanks to grid (horizontal layout, right to left)
        # Row 1: Port tanks (top), Row 2: Starboard tanks (bottom)
        for tank_number in tank_numbers_sorted:
            col_pos = tank_to_col[tank_number]  # Column position (Tank 1 = rightmost)
            
            # Port tank (row 1)
            if "port" in tank_groups[tank_number]:
                port_tank = tank_groups[tank_number]["port"]
                port_assignment = plan.get_assignment(port_tank.id) if plan else None
                # Only show excluded status for empty tanks
                port_excluded = port_tank.id in excluded_tanks and port_assignment is None
                
                if port_assignment:
                    utilization = (port_assignment.quantity_loaded / port_tank.volume * 100) if port_tank.volume > 0 else 0
                    cargo_index = next(
                        (i for i, c in enumerate(plan.cargo_requests) 
                         if c.unique_id == port_assignment.cargo.unique_id),
                        -1
                    )
                    # Get colors from callback if available, otherwise use default
                    if hasattr(create_card_callback, '_cargo_colors'):
                        cargo_colors = create_card_callback._cargo_colors
                        color = cargo_colors[cargo_index] if cargo_index >= 0 and cargo_index < len(cargo_colors) else "#CCCCCC"
                    else:
                        color = "#CCCCCC"
                    card = create_card_callback(port_tank, port_assignment, utilization, color, port_excluded)
                else:
                    card = create_card_callback(port_tank, None, 0.0, "#E0E0E0", port_excluded)
                
                self.grid_layout.addWidget(card, 1, col_pos)  # Row 1 for Port (top row)
                self.tank_cards[(tank_number, "port")] = card
            else:
                # Empty space placeholder
                spacer = QLabel("")
                spacer.setMinimumWidth(150)
                spacer.setMinimumHeight(100)
                self.grid_layout.addWidget(spacer, 1, col_pos)
            
            # Starboard tank (row 2 - bottom row, gemiye göre sağı)
            if "starboard" in tank_groups[tank_number]:
                starboard_tank = tank_groups[tank_number]["starboard"]
                starboard_assignment = plan.get_assignment(starboard_tank.id) if plan else None
                # Only show excluded status for empty tanks
                starboard_excluded = starboard_tank.id in excluded_tanks and starboard_assignment is None
                
                if starboard_assignment:
                    utilization = (starboard_assignment.quantity_loaded / starboard_tank.volume * 100) if starboard_tank.volume > 0 else 0
                    cargo_index = next(
                        (i for i, c in enumerate(plan.cargo_requests) 
                         if c.unique_id == starboard_assignment.cargo.unique_id),
                        -1
                    )
                    # Get colors from callback if available, otherwise use default
                    if hasattr(create_card_callback, '_cargo_colors'):
                        cargo_colors = create_card_callback._cargo_colors
                        color = cargo_colors[cargo_index] if cargo_index >= 0 and cargo_index < len(cargo_colors) else "#CCCCCC"
                    else:
                        color = "#CCCCCC"
                    card = create_card_callback(starboard_tank, starboard_assignment, utilization, color, starboard_excluded)
                else:
                    card = create_card_callback(starboard_tank, None, 0.0, "#E0E0E0", starboard_excluded)
                
                self.grid_layout.addWidget(card, 2, col_pos)  # Row 2 for Starboard (bottom row)
                self.tank_cards[(tank_number, "starboard")] = card
            else:
                # Empty space placeholder
                spacer = QLabel("")
                spacer.setMinimumWidth(150)
                spacer.setMinimumHeight(100)
                self.grid_layout.addWidget(spacer, 2, col_pos)
    
    def clear_tanks(self):
        """Clear all tank cards from grid"""
        # Remove all widgets from grid
        while self.grid_layout.count() > 0:
            item = self.grid_layout.takeAt(0)
            if item:
                widget = item.widget()
                if widget:
                    widget.deleteLater()
        
        self.tank_cards.clear()
    
    def paintEvent(self, event):
        """Optional: Draw ship shape in background"""
        super().paintEvent(event)
        # Can add ship outline drawing here if needed

