"""Widget for displaying cargo legend with drag-and-drop support"""

from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QLabel, QScrollArea,
                             QFrame, QVBoxLayout)
from PyQt6.QtCore import Qt, QMimeData, QByteArray
from PyQt6.QtGui import QDrag, QPixmap, QPainter, QColor, QFont
import json

from models.cargo import Cargo


class DraggableCargoCard(QFrame):
    """Draggable card representing a cargo type"""
    
    def __init__(self, cargo: Cargo, color: str, parent=None, loaded_quantity: float = 0.0):
        super().__init__(parent)
        self.cargo = cargo
        self.color = color
        self.loaded_quantity = loaded_quantity  # Quantity already loaded in tanks
        
        self.setMinimumSize(120, 60)
        self.setMaximumSize(150, 75)
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setLineWidth(2)
        
        # Set background color
        self.setStyleSheet(f"background-color: {color}; border: 2px solid #333; border-radius: 5px;")
        
        # Enable drag and drop
        self.setAcceptDrops(False)  # Don't accept drops, only drag
        
        # Set cursor to indicate draggability
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        
        # Enable mouse tracking for drag
        self.setMouseTracking(True)
        
        # Layout for card content
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 3, 5, 3)
        layout.setSpacing(2)
        
        # Cargo type name
        name_label = QLabel(cargo.cargo_type)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Choose text color based on background brightness with better contrast
        text_color = self._get_contrast_color(color)
        name_label.setStyleSheet(f"color: {text_color}; font-weight: bold; font-size: 9pt;")
        name_label.setWordWrap(True)
        name_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)  # Don't block mouse events
        layout.addWidget(name_label)
        
        # Receiver info - between cargo type and quantity
        receiver_names = cargo.get_receiver_names()
        receiver_label = QLabel(receiver_names)
        receiver_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Use same style as cargo type (same font size, weight, and color)
        receiver_label.setStyleSheet(f"color: {text_color}; font-weight: bold; font-size: 9pt;")
        receiver_label.setWordWrap(True)
        receiver_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)  # Don't block mouse events
        layout.addWidget(receiver_label)
        
        # Quantity info - show only remaining quantity
        remaining_qty = cargo.quantity - self.loaded_quantity
        qty_text = f"{remaining_qty:.0f} m³ kaldı"
        # Use high contrast colors for quantity with better background
        qty_color = "#FF0000" if remaining_qty > 0.001 else "#006600"  # Darker red/green for better contrast
        
        qty_label = QLabel(qty_text)
        qty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Use more opaque white background (0.85) for better contrast, larger font (9pt)
        qty_label.setStyleSheet(f"color: {qty_color}; font-size: 9pt; font-weight: bold; background-color: rgba(255, 255, 255, 0.85); padding: 2px 4px; border-radius: 3px; border: 1px solid rgba(0, 0, 0, 0.2);")
        qty_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)  # Don't block mouse events
        layout.addWidget(qty_label)
    
    def _get_contrast_color(self, hex_color: str) -> str:
        """Get contrasting text color (white or black) based on background brightness
        Uses improved contrast calculation for better readability"""
        # Remove # if present
        hex_color = hex_color.lstrip('#')
        
        # Handle short hex colors (e.g., #FFF -> #FFFFFF)
        if len(hex_color) == 3:
            hex_color = ''.join([c*2 for c in hex_color])
        
        # Convert to RGB
        try:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
        except (ValueError, IndexError):
            # Fallback to black if color parsing fails
            return "#000000"
        
        # Calculate relative luminance using WCAG formula for better contrast
        # Normalize RGB values to 0-1
        def normalize(val):
            val = val / 255.0
            if val <= 0.03928:
                return val / 12.92
            return ((val + 0.055) / 1.055) ** 2.4
        
        r_norm = normalize(r)
        g_norm = normalize(g)
        b_norm = normalize(b)
        
        # Calculate relative luminance
        luminance = 0.2126 * r_norm + 0.7152 * g_norm + 0.0722 * b_norm
        
        # Use higher threshold (0.4 instead of 0.5) to prefer black text for better readability
        # This ensures better contrast on medium-brightness backgrounds
        return "#FFFFFF" if luminance < 0.4 else "#000000"
    
    def mousePressEvent(self, event):
        """Handle mouse press to start drag"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.position().toPoint()
            self.dragging = False
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move to initiate drag"""
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            super().mouseMoveEvent(event)
            return
        
        if not hasattr(self, 'drag_start_position'):
            super().mouseMoveEvent(event)
            return
        
        # Check if moved enough to start drag (minimum 3 pixels)
        current_pos = event.position().toPoint()
        drag_distance = (current_pos - self.drag_start_position).manhattanLength()
        if drag_distance < 3:
            super().mouseMoveEvent(event)
            return
        
        # Prevent multiple drag starts
        if hasattr(self, 'dragging') and self.dragging:
            super().mouseMoveEvent(event)
            return
        
        # Mark as dragging
        self.dragging = True
        
        # Start drag operation
        self._start_drag(event)
        
        # Reset dragging flag
        self.dragging = False
        
        super().mouseMoveEvent(event)
    
    def _start_drag(self, event):
        """Start drag operation"""
        # Create drag object
        drag = QDrag(self)
        mime_data = QMimeData()
        
        # Set MIME data with cargo ID
        cargo_data = {
            "cargo_id": self.cargo.unique_id,
            "type": "cargo"
        }
        mime_data.setData("application/x-cargo-id", QByteArray(json.dumps(cargo_data).encode()))
        drag.setMimeData(mime_data)
        
        # Create drag pixmap (preview) - use grab() for better quality
        try:
            pixmap = self.grab()
        except:
            # Fallback to manual pixmap creation
            pixmap = QPixmap(self.size())
            pixmap.fill(QColor(self.color))
            painter = QPainter(pixmap)
            text_color = self._get_contrast_color(self.color)
            painter.setPen(QColor(text_color))
            painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, self.cargo.cargo_type)
            painter.end()
        
        drag.setPixmap(pixmap)
        
        # Calculate hotspot relative to widget
        hotspot = event.position().toPoint() - self.rect().topLeft()
        drag.setHotSpot(hotspot)
        
        # Change cursor during drag
        self.setCursor(Qt.CursorShape.ClosedHandCursor)
        
        # Execute drag
        result = drag.exec(Qt.DropAction.MoveAction)
        
        # Reset cursor after drag
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        
        # Clear drag start position after drag completes
        if hasattr(self, 'drag_start_position'):
            delattr(self, 'drag_start_position')


class CargoLegendWidget(QWidget):
    """Widget displaying cargo legend with drag-and-drop support"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cargo_list: list[Cargo] = []
        self.cargo_colors: list[str] = []
        self.current_plan = None  # Reference to current plan to calculate loaded quantities
        self.drag_distance_threshold = 10  # Minimum pixels to start drag
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)  # Reduce top and bottom margins
        
        # Scrollable area for cargo cards
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setMinimumHeight(80)
        scroll_area.setMaximumHeight(80)
        
        # Container widget for cards
        self.cards_container = QWidget()
        self.cards_layout = QHBoxLayout(self.cards_container)
        self.cards_layout.setSpacing(10)
        self.cards_layout.setContentsMargins(5, 5, 5, 5)
        self.cards_layout.addStretch()  # Add stretch at end
        
        scroll_area.setWidget(self.cards_container)
        layout.addWidget(scroll_area)
        
        # Store reference to scroll area
        self.scroll_area = scroll_area
    
    def set_cargo_list(self, cargo_list: list[Cargo], cargo_colors: list[str], plan=None):
        """Update cargo list and colors
        
        Args:
            cargo_list: List of cargo objects
            cargo_colors: List of color hex strings (same order as cargo_list)
            plan: Optional StowagePlan to calculate loaded quantities
        """
        self.cargo_list = cargo_list
        self.cargo_colors = cargo_colors
        self.current_plan = plan
        
        # Clear existing cards
        self._clear_cards()
        
        # Create cards for each cargo
        for cargo, color in zip(cargo_list, cargo_colors):
            # Calculate loaded quantity for this cargo
            loaded_qty = 0.0
            if plan:
                loaded_qty = plan.get_cargo_total_loaded(cargo.unique_id)
            
            card = DraggableCargoCard(cargo, color, self, loaded_qty)
            self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)  # Insert before stretch
    
    def _clear_cards(self):
        """Clear all cargo cards"""
        # Remove all widgets except the stretch
        while self.cards_layout.count() > 1:  # Keep the stretch
            item = self.cards_layout.takeAt(0)
            if item:
                widget = item.widget()
                if widget:
                    widget.deleteLater()
    
    def update_loaded_quantities(self, plan):
        """Update loaded quantities for all cargo cards
        
        Args:
            plan: StowagePlan to get loaded quantities from
        """
        self.current_plan = plan
        
        # Update all cards with new loaded quantities
        for i in range(self.cards_layout.count() - 1):  # Exclude stretch
            item = self.cards_layout.itemAt(i)
            if item:
                card = item.widget()
                if isinstance(card, DraggableCargoCard):
                    # Calculate loaded quantity
                    loaded_qty = 0.0
                    if plan:
                        loaded_qty = plan.get_cargo_total_loaded(card.cargo.unique_id)
                    
                    # Update card's loaded quantity
                    card.loaded_quantity = loaded_qty
                    
                    # Update the quantity label
                    self._update_card_quantity_label(card)
    
    def _update_card_quantity_label(self, card: DraggableCargoCard):
        """Update the quantity label on a cargo card"""
        # Find the quantity label (third label in layout: cargo type, receiver, quantity)
        layout = card.layout()
        if layout and layout.count() >= 3:
            qty_label = layout.itemAt(2).widget()  # Third widget (index 2)
            if isinstance(qty_label, QLabel):
                cargo = card.cargo
                remaining_qty = cargo.quantity - card.loaded_quantity
                
                # Show only remaining quantity
                qty_text = f"{remaining_qty:.0f} m³ kaldı"
                # Use high contrast colors for quantity with better background
                qty_color = "#FF0000" if remaining_qty > 0.001 else "#006600"  # Darker red/green for better contrast
                
                qty_label.setText(qty_text)
                # Use more opaque white background (0.85) for better contrast, larger font (9pt)
                qty_label.setStyleSheet(f"color: {qty_color}; font-size: 9pt; font-weight: bold; background-color: rgba(255, 255, 255, 0.85); padding: 2px 4px; border-radius: 3px; border: 1px solid rgba(0, 0, 0, 0.2);")

