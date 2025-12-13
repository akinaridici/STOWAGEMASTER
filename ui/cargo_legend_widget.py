"""Widget for displaying cargo legend with drag-and-drop support"""

from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QLabel, QScrollArea,
                             QFrame, QVBoxLayout, QMenu, QSizePolicy)
from PyQt6.QtCore import Qt, QMimeData, QByteArray, pyqtSignal
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
        
        # Quantity info - show remaining quantity or excess
        remaining_qty = cargo.quantity - self.loaded_quantity
        if remaining_qty > 0.001:
            # Still need to load more
            qty_text = f"{remaining_qty:.0f} m³ kaldı"
            qty_color = "#FF0000"  # Red for remaining
        elif remaining_qty < -0.001:
            # Overloaded - show excess
            excess_qty = abs(remaining_qty)
            qty_text = f"{excess_qty:.0f} m³ fazla"
            qty_color = "#FF6B00"  # Orange for excess
        else:
            # Perfect match
            qty_text = "Tamamlandı"
            qty_color = "#006600"  # Green for completed
        
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
    
    def contextMenuEvent(self, event):
        """Handle right-click context menu"""
        menu = QMenu(self)
        
        change_color_action = menu.addAction("Renk Değiştir")
        change_color_action.triggered.connect(self._change_color)
        
        menu.exec(event.globalPos())
    
    def _change_color(self):
        """Open color selection dialog"""
        from ui.cargo_color_dialog import CargoColorDialog
        
        # Get current color (custom_color if exists, otherwise use card color)
        current_color = self.cargo.custom_color if self.cargo.custom_color else self.color
        
        # Open color dialog
        dialog = CargoColorDialog(self, current_color)
        if dialog.exec():
            selected_color = dialog.get_selected_color()
            
            # Update cargo's custom_color
            self.cargo.custom_color = selected_color
            
            # Update card color
            if selected_color:
                self.color = selected_color
                self.setStyleSheet(f"background-color: {selected_color}; border: 2px solid #333; border-radius: 5px;")
                
                # Update text color for contrast
                text_color = self._get_contrast_color(selected_color)
                layout = self.layout()
                if layout:
                    for i in range(layout.count()):
                        item = layout.itemAt(i)
                        if item and item.widget():
                            widget = item.widget()
                            if isinstance(widget, QLabel):
                                widget.setStyleSheet(widget.styleSheet().replace(
                                    f"color: {self._get_contrast_color(self.color)}",
                                    f"color: {text_color}"
                                ))
            else:
                # Reset to default (will be handled by parent widget)
                self.cargo.custom_color = None
            
            # Notify parent widget that color changed
            parent = self.parent()
            while parent:
                if isinstance(parent, CargoLegendWidget):
                    parent.on_color_changed(self.cargo)
                    break
                parent = parent.parent()


class CargoLegendWidget(QWidget):
    """Widget displaying cargo legend with drag-and-drop support"""
    
    # Signal emitted when cargo color changes
    color_changed = pyqtSignal(object)  # Emits Cargo object
    
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
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setMinimumHeight(100)  # Give legend more vertical room
        scroll_area.setMaximumHeight(180)  # Cap to avoid overtaking the schematic
        scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        
        # Container widget for cards
        self.cards_container = QWidget()
        self.cards_layout = QHBoxLayout(self.cards_container)
        self.cards_layout.setSpacing(10)
        self.cards_layout.setContentsMargins(5, 5, 5, 5)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
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

        # Adjust legend area height so cards are never clipped
        self._adjust_scroll_height(len(cargo_list))
    
    def _clear_cards(self):
        """Clear all cargo cards"""
        # Remove all widgets except the stretch
        while self.cards_layout.count() > 1:  # Keep the stretch
            item = self.cards_layout.takeAt(0)
            if item:
                widget = item.widget()
                if widget:
                    widget.deleteLater()

    def _adjust_scroll_height(self, cargo_count: int):
        """Resize scroll area to fit legend without clipping while keeping a reasonable cap."""
        base_height = 100
        # Add extra room for additional rows; cap at the scroll area's maximum height.
        extra = 0
        if cargo_count > 4:
            extra = 20
        if cargo_count > 8:
            extra = 40
        target = min(base_height + extra, 180)
        self.scroll_area.setMinimumHeight(target)
        self.scroll_area.setMaximumHeight(180)
    
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
                
                # Show remaining quantity or excess
                if remaining_qty > 0.001:
                    # Still need to load more
                    qty_text = f"{remaining_qty:.0f} m³ kaldı"
                    qty_color = "#FF0000"  # Red for remaining
                elif remaining_qty < -0.001:
                    # Overloaded - show excess
                    excess_qty = abs(remaining_qty)
                    qty_text = f"{excess_qty:.0f} m³ fazla"
                    qty_color = "#FF6B00"  # Orange for excess
                else:
                    # Perfect match
                    qty_text = "Tamamlandı"
                    qty_color = "#006600"  # Green for completed
                
                qty_label.setText(qty_text)
                # Use more opaque white background (0.85) for better contrast, larger font (9pt)
                qty_label.setStyleSheet(f"color: {qty_color}; font-size: 9pt; font-weight: bold; background-color: rgba(255, 255, 255, 0.85); padding: 2px 4px; border-radius: 3px; border: 1px solid rgba(0, 0, 0, 0.2);")
    
    def on_color_changed(self, cargo: Cargo):
        """Handle color change for a cargo
        
        Args:
            cargo: Cargo object whose color was changed
        """
        # Find the card for this cargo and update its color
        for i in range(self.cards_layout.count() - 1):  # Exclude stretch
            item = self.cards_layout.itemAt(i)
            if item:
                card = item.widget()
                if isinstance(card, DraggableCargoCard) and card.cargo.unique_id == cargo.unique_id:
                    # Update card color based on custom_color or default
                    if cargo.custom_color:
                        card.color = cargo.custom_color
                        card.setStyleSheet(f"background-color: {cargo.custom_color}; border: 2px solid #333; border-radius: 5px;")
                        
                        # Update text color for contrast
                        text_color = card._get_contrast_color(cargo.custom_color)
                        layout = card.layout()
                        if layout:
                            for j in range(layout.count()):
                                layout_item = layout.itemAt(j)
                                if layout_item and layout_item.widget():
                                    widget = layout_item.widget()
                                    if isinstance(widget, QLabel):
                                        # Update text color
                                        current_style = widget.styleSheet()
                                        # Extract non-color parts and update color
                                        if "color:" in current_style:
                                            parts = current_style.split("color:")
                                            if len(parts) > 1:
                                                color_part = parts[1].split(";")[0]
                                                new_style = current_style.replace(color_part.strip(), text_color)
                                                widget.setStyleSheet(new_style)
                    else:
                        # Reset to default color (from cargo_colors list)
                        cargo_index = next((idx for idx, c in enumerate(self.cargo_list) if c.unique_id == cargo.unique_id), None)
                        if cargo_index is not None and cargo_index < len(self.cargo_colors):
                            default_color = self.cargo_colors[cargo_index]
                            card.color = default_color
                            card.setStyleSheet(f"background-color: {default_color}; border: 2px solid #333; border-radius: 5px;")
                            
                            # Update text color for contrast
                            text_color = card._get_contrast_color(default_color)
                            layout = card.layout()
                            if layout:
                                for j in range(layout.count()):
                                    layout_item = layout.itemAt(j)
                                    if layout_item and layout_item.widget():
                                        widget = layout_item.widget()
                                        if isinstance(widget, QLabel):
                                            current_style = widget.styleSheet()
                                            if "color:" in current_style:
                                                parts = current_style.split("color:")
                                                if len(parts) > 1:
                                                    color_part = parts[1].split(";")[0]
                                                    new_style = current_style.replace(color_part.strip(), text_color)
                                                    widget.setStyleSheet(new_style)
                    break
        
        # Emit signal to notify parent
        self.color_changed.emit(cargo)

