"""Widget for displaying stowage plan"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from models.plan import StowagePlan
from models.ship import Ship


class PlanViewer(QWidget):
    """Widget for visualizing stowage plan"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_plan: StowagePlan = None
        self.current_ship: Ship = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)  # Minimize margins
        layout.setSpacing(5)  # Minimize spacing between widgets
        
        # Comparison table: requested vs loaded (label removed) - at the top
        # Table should start immediately from the top
        self.comparison_table = QTableWidget()
        self.comparison_table.setColumnCount(6)
        self.comparison_table.setHorizontalHeaderLabels([
            "Yük Tipi", "Alıcı(lar)", "Sipariş (m³)", "Yüklenen (m³)", "Fark (m³)", "Durum"
        ])
        self.comparison_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.comparison_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.comparison_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.comparison_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.comparison_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.comparison_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.comparison_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        # Tablo genişleyebilmeli - maksimum yükseklik kısıtı kaldırıldı
        # Tabloyu layout'a stretch faktörü ile ekle (1 = genişleyebilir)
        layout.addWidget(self.comparison_table, 1)
        
        # Summary labels (left and right aligned) - at the bottom
        summary_layout = QHBoxLayout()
        summary_layout.setContentsMargins(0, 0, 0, 0)
        summary_layout.setSpacing(0)
        
        # Left side: Capacity, Loaded, Ratio
        self.summary_label_left = QLabel("Henüz plan oluşturulmadı")
        self.summary_label_left.setWordWrap(False)
        self.summary_label_left.setContentsMargins(0, 0, 0, 0)
        summary_layout.addWidget(self.summary_label_left)
        
        # Right side: Demand Fulfillment (will be added dynamically)
        summary_layout.addStretch()  # Push right label to the right
        
        self.summary_label_right = QLabel("")
        self.summary_label_right.setWordWrap(False)
        self.summary_label_right.setContentsMargins(0, 0, 0, 0)
        summary_layout.addWidget(self.summary_label_right)
        
        # Add summary layout to main layout
        layout.addLayout(summary_layout, 0)
        
        # Tank doluluk tablosu kaldırıldı - sadece karşılaştırma tablosu kullanılıyor
    
    def display_plan(self, plan: StowagePlan, ship: Ship, cargo_colors: list = None):
        """Display a stowage plan
        
        Args:
            plan: Stowage plan to display
            ship: Ship object
            cargo_colors: Optional list of colors for cargo types (in same order as cargo_requests)
        """
        self.current_plan = plan
        self.current_ship = ship
        self.cargo_colors = cargo_colors or []
        
        if not plan or not ship:
            self.clear_display()
            return
        
        # Update summary
        total_capacity = ship.get_total_capacity()
        total_loaded = plan.get_total_loaded()
        utilization = (total_loaded / total_capacity * 100) if total_capacity > 0 else 0
        
        # Calculate demand fulfillment ratio
        total_requested = sum(cargo.quantity for cargo in plan.cargo_requests)
        demand_fulfillment = (total_loaded / total_requested * 100) if total_requested > 0 else 0
        
        # Display remaining info: left side (Capacity, Loaded, Ratio)
        self.summary_label_left.setText(
            f"<b>Kapasite:</b> {total_capacity:.2f} m³  |  "
            f"<b>Yüklenen:</b> {total_loaded:.2f} m³  |  "
            f"<b>Oran:</b> {utilization:.1f}%"
        )
        
        # Display right side: Demand Fulfillment (always aligned to the right)
        self.summary_label_right.setText(
            f"<b>Talep Karşılama:</b> {demand_fulfillment:.1f}%"
        )
        
        # Display comparison table: requested vs loaded
        self.comparison_table.setRowCount(len(plan.cargo_requests))
        
        for row, cargo in enumerate(plan.cargo_requests):
            # Get cargo color from cargo_colors list (same order as cargo_requests)
            cargo_color = self.cargo_colors[row] if row < len(self.cargo_colors) else "#E0E0E0"
            
            # Cargo type
            cargo_type_item = QTableWidgetItem(cargo.cargo_type)
            cargo_type_item.setBackground(QColor(cargo_color))
            self.comparison_table.setItem(row, 0, cargo_type_item)
            
            # Receivers
            receiver_names = cargo.get_receiver_names()
            receiver_item = QTableWidgetItem(receiver_names)
            receiver_item.setBackground(QColor(cargo_color))
            self.comparison_table.setItem(row, 1, receiver_item)
            
            # Requested quantity
            requested = cargo.quantity
            requested_item = QTableWidgetItem(f"{requested:.2f}")
            requested_item.setBackground(QColor(cargo_color))
            self.comparison_table.setItem(row, 2, requested_item)
            
            # Loaded quantity
            loaded = plan.get_cargo_total_loaded(cargo.unique_id)
            loaded_item = QTableWidgetItem(f"{loaded:.2f}")
            loaded_item.setBackground(QColor(cargo_color))
            self.comparison_table.setItem(row, 3, loaded_item)
            
            # Difference
            difference = loaded - requested
            diff_item = QTableWidgetItem(f"{difference:+.2f}")
            
            # Color code difference (use cargo color as base, but keep status colors)
            if abs(difference) < 0.01:  # Perfect match
                diff_item.setBackground(QColor("#96CEB4"))  # Green
            elif difference < 0:  # Underloaded
                diff_item.setBackground(QColor("#FFEAA7"))  # Yellow
            else:  # Overloaded (shouldn't happen)
                diff_item.setBackground(QColor("#FF6B6B"))  # Red
            
            self.comparison_table.setItem(row, 4, diff_item)
            
            # Status
            if abs(difference) < 0.01:
                status = "✓ Tamamlandı"
                status_item = QTableWidgetItem(status)
                status_item.setBackground(QColor("#96CEB4"))
            elif difference < 0:
                # Eksik: yüklenen yüzdesini göster
                percentage = (loaded / requested * 100) if requested > 0 else 0
                status = f"Eksik ({percentage:.1f}%)"
                status_item = QTableWidgetItem(status)
                status_item.setBackground(QColor("#FFEAA7"))
            else:
                # Fazla: fazla yüzdesini göster
                percentage = (difference / requested * 100) if requested > 0 else 0
                status = f"Fazla ({percentage:.1f}%)"
                status_item = QTableWidgetItem(status)
                status_item.setBackground(QColor("#FF6B6B"))
            
            self.comparison_table.setItem(row, 5, status_item)
        
        self.comparison_table.resizeRowsToContents()
        
        # Tank doluluk tablosu kaldırıldı - tank bilgileri kontrol panelindeki kroki görünümünde görülebilir
    
    # _generate_colors_for_table metodu kaldırıldı - tank tablosu olmadığı için gerekmiyor
    
    def clear_display(self):
        """Clear the display"""
        self.summary_label_left.setText("Henüz plan oluşturulmadı")
        self.summary_label_right.setText("")
        self.comparison_table.setRowCount(0)

