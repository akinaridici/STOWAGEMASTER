"""Draggable tank card widget for drag-and-drop operations """

from PyQt6.QtWidgets import (QGroupBox, QVBoxLayout, QLabel, QProgressBar,
                             QWidget, QMenu)
from PyQt6.QtCore import Qt, QMimeData, QByteArray, QTimer
from PyQt6.QtGui import QDrag, QPixmap, QPainter, QColor
import json
from typing import Optional

from models.plan import TankAssignment
from models.ship import Tank
from models.suggested_tank_info import SuggestedTankInfo


class DraggableTankCard(QGroupBox):
    """Tank card widget with drag-and-drop support"""
    
    def __init__(self, tank: Tank, assignment: TankAssignment = None, 
                 utilization: float = 0.0, color: str = "#E0E0E0", 
                 parent=None, is_excluded: bool = False, is_planned: bool = False,
                 is_suggested: bool = False, fit_info: Optional[SuggestedTankInfo] = None,
                 is_fixed: bool = False):
        super().__init__(tank.name, parent)
        self.tank = tank
        self.assignment = assignment
        self.utilization = utilization
        self.color = color
        self.is_excluded = is_excluded
        self.is_planned = is_planned
        self.is_suggested = is_suggested
        self.fit_info = fit_info
        self.is_fixed = is_fixed
        
        self.setMaximumWidth(180)
        self.setMinimumWidth(150)
        self.setAcceptDrops(True)
        
        # Animation for pulsing effect
        self.pulse_timer = None
        self.pulse_phase = 0.0
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 5)  # Reduce top margin (less space above title)
        layout.setSpacing(3)  # Reduce spacing between elements
        
        # Capacity info
        info_label = QLabel(f"{self.tank.volume:.0f} m³")
        info_label.setStyleSheet("font-weight: bold; font-size: 10pt;")
        layout.addWidget(info_label)
        
        if self.assignment:
            # Cargo type with receiver info
            cargo_text = self.assignment.cargo.cargo_type
            if self.assignment.cargo.receivers:
                receiver_names = ", ".join([r.name for r in self.assignment.cargo.receivers])
                cargo_text += f"\n({receiver_names})"
            else:
                cargo_text += "\n(Genel)"
            
            cargo_label = QLabel(cargo_text)
            cargo_label.setStyleSheet(
                f"background-color: {self.color}; padding: 3px; "
                f"border-radius: 2px; font-weight: bold;"
            )
            cargo_label.setWordWrap(True)
            layout.addWidget(cargo_label)
            
            # Quantity loaded
            qty_label = QLabel(f"{self.assignment.quantity_loaded:.0f} m³")
            qty_label.setStyleSheet("font-size: 9pt;")
            layout.addWidget(qty_label)
        else:
            empty_label = QLabel("Boş")
            empty_label.setStyleSheet(
                "background-color: #E0E0E0; padding: 3px; border-radius: 2px;"
            )
            layout.addWidget(empty_label)
        
        # Progress bar
        progress = QProgressBar()
        progress.setMinimum(0)
        progress.setMaximum(100)
        progress.setValue(int(self.utilization))
        progress.setFormat(f"{self.utilization:.0f}%")
        progress.setStyleSheet(
            f"QProgressBar::chunk {{ background-color: {self.color}; }}"
        )
        progress.setMaximumHeight(20)
        layout.addWidget(progress)
        
        # Suggested label with fit info (if tank is suggested for current cargo)
        if self.is_suggested and not self.assignment and self.fit_info:
            # Rank badge
            rank_label = QLabel(f"#{self.fit_info.rank}")
            rank_label.setStyleSheet(
                "background-color: #333; color: white; padding: 2px 6px; "
                "border-radius: 10px; font-weight: bold; font-size: 9pt;"
            )
            rank_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(rank_label)
            
            # Fit score and reason
            fit_score_label = QLabel(f"{self.fit_info.fit_score:.0f}% Fit")
            fit_score_label.setStyleSheet(
                f"background-color: {self.fit_info.get_border_color()}; color: white; "
                "padding: 3px; border-radius: 3px; font-weight: bold; font-size: 10pt;"
            )
            fit_score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(fit_score_label)
            
            # Fit reason
            reason_label = QLabel(self.fit_info.fit_reason)
            reason_label.setStyleSheet("font-size: 7pt; color: #666;")
            reason_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            reason_label.setWordWrap(True)
            layout.addWidget(reason_label)
            
            # Utilization preview (if empty tank)
            if not self.assignment:
                util_preview = QProgressBar()
                util_preview.setMinimum(0)
                util_preview.setMaximum(100)
                util_preview.setValue(int(self.fit_info.utilization))
                util_preview.setFormat(f"{self.fit_info.utilization:.0f}%")
                util_preview.setStyleSheet(
                    f"QProgressBar::chunk {{ background-color: {self.fit_info.get_border_color()}; }}"
                )
                util_preview.setMaximumHeight(15)
                layout.addWidget(util_preview)
            
            # Set tooltip with detailed info
            tooltip_text = (
                f"Best Fit #{self.fit_info.rank}\n"
                f"Fit Score: {self.fit_info.fit_score:.1f}%\n"
                f"Utilization: {self.fit_info.utilization:.1f}%\n"
                f"Reason: {self.fit_info.fit_reason}\n"
                f"Quantity: {self.fit_info.quantity_to_load:.2f} m³\n"
                f"Deviation: ±{self.fit_info.deviation_percent:.2f}%"
            )
            self.setToolTip(tooltip_text)
        
        # Planned label (if tank belongs to planned cargo)
        if self.is_planned and self.assignment:
            planned_label = QLabel("🔒 Planlandı")
            planned_label.setStyleSheet(
                "background-color: #4ECDC4; color: white; padding: 2px; "
                "border-radius: 2px; font-weight: bold; font-size: 8pt;"
            )
            planned_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(planned_label)
        
        # Excluded label (if tank is excluded from planning)
        if self.is_excluded:
            excluded_label = QLabel("⚠ Planlama Dışı")
            excluded_label.setStyleSheet(
                "background-color: #FF6B6B; color: white; padding: 2px; "
                "border-radius: 2px; font-weight: bold; font-size: 8pt;"
            )
            excluded_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(excluded_label)
        
        # Fixed label (if tank has fixed assignment from drag-drop)
        if self.is_fixed:
            fixed_label = QLabel("🔒 Kilitli")
            fixed_label.setStyleSheet(
                "background-color: #FF9500; color: white; padding: 2px; "
                "border-radius: 2px; font-weight: bold; font-size: 8pt;"
            )
            fixed_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(fixed_label)
        
        # Apply excluded/planned styling to the card itself
        self.update_excluded_style()
    
    def mousePressEvent(self, event):
        """Handle mouse press for drag start"""
        try:
            # Check if widget still exists
            if not self or not hasattr(self, 'assignment'):
                return
            
            # Prevent dragging if tank is fixed (locked after "Plan Remaining Cargos")
            if self.is_fixed:
                super().mousePressEvent(event)
                return
            
            if event.button() == Qt.MouseButton.LeftButton and self.assignment:
                # Only allow dragging if there's an assignment
                self.drag_start_position = event.position().toPoint()
                super().mousePressEvent(event)
        except RuntimeError:
            # Widget has been deleted, ignore
            pass
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for drag operation"""
        try:
            # Check if widget still exists
            if not self or not hasattr(self, 'assignment'):
                return
            
            if not hasattr(self, 'drag_start_position'):
                super().mouseMoveEvent(event)
                return
                
            if not (event.buttons() & Qt.MouseButton.LeftButton):
                super().mouseMoveEvent(event)
                return
            
            if not self.assignment:
                super().mouseMoveEvent(event)
                return
            
            # Prevent dragging if tank is planned
            if self.is_planned:
                super().mouseMoveEvent(event)
                return
            
            # Prevent dragging if tank is fixed (locked after "Plan Remaining Cargos")
            if self.is_fixed:
                super().mouseMoveEvent(event)
                return
            
            # Check if moved enough to start drag
            if ((event.position().toPoint() - self.drag_start_position).manhattanLength() 
                < 10):
                super().mouseMoveEvent(event)
                return
            
            # Create drag
            drag = QDrag(self)
            mime_data = QMimeData()
            
            # Store tank and assignment data
            drag_data = {
                'source_tank_id': self.tank.id,
                'assignment': {
                    'cargo': {
                        'cargo_type': self.assignment.cargo.cargo_type,
                        'quantity': self.assignment.quantity_loaded,
                        'unique_id': self.assignment.cargo.unique_id,
                        'receivers': [r.name for r in self.assignment.cargo.receivers]
                    },
                    'quantity_loaded': self.assignment.quantity_loaded
                }
            }
            
            mime_data.setData("application/x-tank-assignment", 
                             QByteArray(json.dumps(drag_data).encode()))
            drag.setMimeData(mime_data)
            
            # Create drag pixmap
            pixmap = self.grab()
            drag.setPixmap(pixmap)
            drag.setHotSpot(event.position().toPoint())
            
            # Execute drag
            drop_action = drag.exec(Qt.DropAction.MoveAction)
            
            super().mouseMoveEvent(event)
        except RuntimeError:
            # Widget has been deleted, ignore
            pass
    
    def dragEnterEvent(self, event):
        """Handle drag enter event"""
        try:
            # Accept both tank-to-tank swaps and cargo-to-tank drops
            if (event.mimeData().hasFormat("application/x-tank-assignment") or 
                event.mimeData().hasFormat("application/x-cargo-id")):
                # Don't accept if tank is planned
                if self.is_planned:
                    event.ignore()
                # Don't accept if tank is fixed (locked after "Plan Remaining Cargos")
                elif self.is_fixed:
                    event.ignore()
                else:
                    event.acceptProposedAction()
            else:
                event.ignore()
        except RuntimeError:
            # Widget has been deleted, ignore
            event.ignore()
    
    def dragMoveEvent(self, event):
        """Handle drag move event"""
        try:
            # Accept both tank-to-tank swaps and cargo-to-tank drops
            if (event.mimeData().hasFormat("application/x-tank-assignment") or 
                event.mimeData().hasFormat("application/x-cargo-id")):
                # Don't accept if tank is planned
                if self.is_planned:
                    event.ignore()
                # Don't accept if tank is fixed (locked after "Plan Remaining Cargos")
                elif self.is_fixed:
                    event.ignore()
                else:
                    event.acceptProposedAction()
            else:
                event.ignore()
        except RuntimeError:
            # Widget has been deleted, ignore
            event.ignore()
    
    def dropEvent(self, event):
        """Handle drop event"""
        try:
            # Check if widget still exists
            if not self or not hasattr(self, 'tank'):
                event.ignore()
                return
            
            # Don't accept if tank is planned
            if self.is_planned:
                event.ignore()
                return
            
            # Don't accept if tank is fixed (locked after "Plan Remaining Cargos")
            if self.is_fixed:
                event.ignore()
                return
            
            # Check MIME data formats
            mime = event.mimeData()
            if mime.hasFormat("application/x-tank-assignment"):
                # Tank-to-tank swap
                data = json.loads(event.mimeData().data("application/x-tank-assignment").data().decode())
                source_tank_id = data['source_tank_id']
                
                # Don't allow dropping on itself
                if source_tank_id == self.tank.id:
                    event.ignore()
                    return
                
                # Notify parent to handle the swap
                if self.parent():
                    # Try to find the main window or card container
                    widget = self.parent()
                    while widget:
                        if hasattr(widget, 'handle_tank_swap'):
                            widget.handle_tank_swap(source_tank_id, self.tank.id)
                            event.acceptProposedAction()
                            return
                        widget = widget.parent()
                
                event.acceptProposedAction()
            elif mime.hasFormat("application/x-cargo-id"):
                # Cargo-to-tank drop from LEGEND
                try:
                    data_bytes = mime.data("application/x-cargo-id").data()
                    data = json.loads(data_bytes.decode())
                    cargo_id = data['cargo_id']
                    
                    # Notify parent to handle the cargo assignment
                    # Try to find MainWindow - check self first, then parent chain
                    widget = self
                    while widget:
                        if hasattr(widget, 'handle_cargo_drop'):
                            widget.handle_cargo_drop(cargo_id, self.tank.id)
                            event.acceptProposedAction()
                            return
                        widget = widget.parent()
                    
                    # If no handler found, still accept to prevent error
                    event.acceptProposedAction()
                except Exception as e:
                    # If parsing fails, ignore but log for debugging
                    import traceback
                    print(f"Error in cargo drop: {e}")
                    traceback.print_exc()
                    event.ignore()
            else:
                event.ignore()
        except RuntimeError:
            # Widget has been deleted, ignore
            event.ignore()
    
    def mouseDoubleClickEvent(self, event):
        """Handle double click to edit tank cargo"""
        try:
            # Check if widget still exists
            if not self or not hasattr(self, 'tank'):
                return
            
            # Find main window to access plan and ship
            widget = self.parent()
            while widget:
                if hasattr(widget, 'handle_tank_double_click'):
                    widget.handle_tank_double_click(self.tank.id)
                    return
                widget = widget.parent()
        except RuntimeError:
            # Widget has been deleted, ignore
            pass
    
    def contextMenuEvent(self, event):
        """Handle right-click context menu"""
        try:
            # Check if widget still exists
            if not self or not hasattr(self, 'tank'):
                return
            
            # Find main window
            widget = self.parent()
            main_window = None
            while widget:
                if hasattr(widget, 'current_plan'):
                    main_window = widget
                    break
                widget = widget.parent()
            
            if not main_window:
                return
            
            # Create context menu
            menu = QMenu(self)
            
            # If tank is locked and has assignment, show "Kilidi kaldır" option
            if self.is_fixed and self.assignment is not None:
                unlock_action = menu.addAction("Kilidi kaldır")
                selected_action = menu.exec(event.globalPos())
                
                if selected_action == unlock_action:
                    # Unlock the tank
                    if main_window:
                        main_window.handle_unlock_tank(self.tank.id)
                return
            
            # If tank has assignment and is not locked, show "Boşalt" option
            if self.assignment is not None and not self.is_fixed:
                empty_action = menu.addAction("Boşalt")
                selected_action = menu.exec(event.globalPos())
                
                if selected_action == empty_action:
                    # Empty the tank
                    if main_window:
                        main_window.handle_empty_tank(self.tank.id)
                return
            
            # If tank is empty, show exclusion menu
            if self.assignment is None:
                # Exclusion menu for empty tanks
                if self.is_excluded:
                    action = menu.addAction("Planlamaya Dahil Et")
                else:
                    action = menu.addAction("Planlama Dışı Bırak")
                
                # Show menu and handle selection
                selected_action = menu.exec(event.globalPos())
                
                if selected_action == action:
                    # Toggle exclusion status
                    new_excluded = not self.is_excluded
                    if main_window:
                        main_window.handle_exclude_tank(self.tank.id, new_excluded)
                        # Update this card's visual state
                        self.set_excluded(new_excluded)
                        
                        # Show confirmation message
                        if new_excluded:
                            from PyQt6.QtWidgets import QMessageBox
                            QMessageBox.information(
                                main_window,
                                "Bilgi",
                                f"{self.tank.name} tankı planlama dışı bırakıldı.\n\n"
                                f"Bu tank optimizasyon sırasında kullanılmayacak."
                            )
                        else:
                            from PyQt6.QtWidgets import QMessageBox
                            QMessageBox.information(
                                main_window,
                                "Bilgi",
                                f"{self.tank.name} tankı planlamaya dahil edildi.\n\n"
                                f"Bu tank optimizasyon sırasında kullanılabilecek."
                            )
                    
        except RuntimeError:
            # Widget has been deleted, ignore
            pass
    
    def set_excluded(self, excluded: bool):
        """Set excluded status and update visual appearance"""
        self.is_excluded = excluded
        self.update_excluded_style()
        
        # Update or remove excluded label
        layout = self.layout()
        if layout:
            # Remove existing excluded label if any
            for i in range(layout.count() - 1, -1, -1):
                item = layout.itemAt(i)
                if item:
                    widget = item.widget()
                    if widget and isinstance(widget, QLabel) and "Planlama Dışı" in widget.text():
                        layout.removeWidget(widget)
                        widget.deleteLater()
            
            # Add excluded label if needed
            if excluded:
                excluded_label = QLabel("⚠ Planlama Dışı")
                excluded_label.setStyleSheet(
                    "background-color: #FF6B6B; color: white; padding: 2px; "
                    "border-radius: 2px; font-weight: bold; font-size: 8pt;"
                )
                excluded_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(excluded_label)
    
    def update_excluded_style(self):
        """Update visual style based on excluded/planned/suggested status"""
        if self.is_suggested and not self.assignment and self.fit_info:
            # Get border color based on fit quality
            border_color = self.fit_info.get_border_color()
            quality = self.fit_info.get_fit_quality()
            
            # Different background colors for different qualities
            bg_colors = {
                "excellent": "#F0FDF4",  # Light green
                "good": "#FFF9E6",  # Light yellow
                "acceptable": "#FFF3E0",  # Light orange
                "poor": "#FFEBEE"  # Light red
            }
            bg_color = bg_colors.get(quality, "#FFF9E6")
            
            # Show suggested status with color-coded border
            border_width = 4 if quality == "excellent" else 3
            self.setStyleSheet(
                f"""
                QGroupBox {{
                    border: {border_width}px solid {border_color};
                    background-color: {bg_color};
                }}
                QGroupBox::title {{
                    color: {border_color};
                    font-weight: bold;
                    subcontrol-origin: margin;
                    subcontrol-position: top left;
                    padding: 0px 3px;
                }}
                """
            )
            
            # Start pulse animation for suggested tanks
            self.start_pulse_animation()
        elif self.is_suggested and not self.assignment:
            # Fallback if no fit_info (shouldn't happen, but just in case)
            self.setStyleSheet(
                """
                QGroupBox {
                    border: 3px solid #FFE66D;
                    background-color: #FFF9E6;
                }
                QGroupBox::title {
                    color: #B8860B;
                    font-weight: bold;
                    subcontrol-origin: margin;
                    subcontrol-position: top left;
                    padding: 0px 3px;
                }
                """
            )
        elif self.is_planned:
            # Show planned status with border
            self.setStyleSheet(
                """
                QGroupBox {
                    border: 2px solid #4ECDC4;
                    background-color: #F0FDFC;
                }
                QGroupBox::title {
                    color: #2C7A7B;
                    font-weight: bold;
                    subcontrol-origin: margin;
                    subcontrol-position: top left;
                    padding: 0px 3px;
                }
                """
            )
        elif self.is_excluded:
            # Gray out the card with diagonal lines pattern
            self.setStyleSheet(
                """
                QGroupBox {
                    border: 2px dashed #999999;
                    background-color: #F5F5F5;
                    color: #666666;
                }
                QGroupBox::title {
                    color: #666666;
                    subcontrol-origin: margin;
                    subcontrol-position: top left;
                    padding: 0px 3px;
                }
                """
            )
        else:
            # Reset to default style (with reduced title padding)
            self.setStyleSheet("QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0px 3px; }")
            # Stop pulse animation if running
            self.stop_pulse_animation()
    
    def start_pulse_animation(self):
        """Start pulsing animation for suggested tanks using border glow effect"""
        if not self.is_suggested or self.assignment or not self.fit_info:
            return
        
        # Stop any existing animation
        self.stop_pulse_animation()
        
        # Use timer-based animation for border glow effect
        self.pulse_phase = 0.0
        self.pulse_timer = QTimer(self)
        self.pulse_timer.timeout.connect(self._update_pulse_glow)
        self.pulse_timer.start(50)  # Update every 50ms for smooth animation
    
    def _update_pulse_glow(self):
        """Update pulse glow effect"""
        if not self.is_suggested or not self.fit_info:
            self.stop_pulse_animation()
            return
        
        # Calculate glow intensity (0.0 to 1.0)
        import math
        self.pulse_phase += 0.05  # Increment phase
        if self.pulse_phase >= 2 * math.pi:
            self.pulse_phase = 0.0
        
        # Sinusoidal pulse (0.7 to 1.0)
        glow_intensity = 0.7 + 0.3 * (1.0 + math.sin(self.pulse_phase)) / 2.0
        
        # Get base border color
        base_color = self.fit_info.get_border_color()
        
        # Adjust opacity based on glow
        # Convert hex to RGB, adjust brightness
        from PyQt6.QtGui import QColor
        color = QColor(base_color)
        r, g, b = color.red(), color.green(), color.blue()
        
        # Apply glow effect by adjusting border color brightness
        glow_r = min(255, int(r + (255 - r) * (1 - glow_intensity) * 0.3))
        glow_g = min(255, int(g + (255 - g) * (1 - glow_intensity) * 0.3))
        glow_b = min(255, int(b + (255 - b) * (1 - glow_intensity) * 0.3))
        
        glow_color = f"#{glow_r:02x}{glow_g:02x}{glow_b:02x}"
        
        # Update border color
        border_width = 4 if self.fit_info.get_fit_quality() == "excellent" else 3
        quality = self.fit_info.get_fit_quality()
        bg_colors = {
            "excellent": "#F0FDF4",
            "good": "#FFF9E6",
            "acceptable": "#FFF3E0",
            "poor": "#FFEBEE"
        }
        bg_color = bg_colors.get(quality, "#FFF9E6")
        
        self.setStyleSheet(
            f"""
            QGroupBox {{
                border: {border_width}px solid {glow_color};
                background-color: {bg_color};
            }}
            QGroupBox::title {{
                color: {glow_color};
                font-weight: bold;
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0px 3px;
            }}
            """
        )
    
    def stop_pulse_animation(self):
        """Stop pulsing animation"""
        if self.pulse_timer:
            self.pulse_timer.stop()
            self.pulse_timer = None
        self.setWindowOpacity(1.0)
