"""Dialog for editing tank cargo assignment"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QComboBox, QPushButton, QDoubleSpinBox,
                             QDialogButtonBox, QMessageBox, QGroupBox, QSlider)
from PyQt6.QtCore import Qt
from typing import Optional, List

from models.plan import StowagePlan, TankAssignment
from models.ship import Ship, Tank
from models.cargo import Cargo


class TankCargoEditDialog(QDialog):
    """Dialog for assigning/editing cargo for a specific tank"""
    
    def __init__(self, parent=None, plan: StowagePlan = None, 
                 ship: Ship = None, tank: Tank = None):
        super().__init__(parent)
        self.plan = plan
        self.ship = ship
        self.tank = tank
        self.selected_cargo: Optional[Cargo] = None
        self.selected_quantity: float = 0.0
        self._updating_slider = False  # Flag to prevent circular updates
        
        self.init_ui()
        self.load_cargo_options()
        self.load_current_assignment()
    
    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle(f"Tank Yük Düzenleme: {self.tank.name}")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Tank info
        tank_info = QGroupBox("Tank Bilgisi")
        tank_layout = QVBoxLayout()
        tank_layout.addWidget(QLabel(f"Tank: {self.tank.name}"))
        tank_layout.addWidget(QLabel(f"Kapasite: {self.tank.volume:.2f} m³"))
        tank_info.setLayout(tank_layout)
        layout.addWidget(tank_info)
        
        # Cargo selection
        cargo_group = QGroupBox("Yük Seçimi")
        cargo_layout = QVBoxLayout()
        
        cargo_layout.addWidget(QLabel("Yük Tipi:"))
        self.cargo_combo = QComboBox()
        self.cargo_combo.currentIndexChanged.connect(self.on_cargo_selected)
        cargo_layout.addWidget(self.cargo_combo)
        
        # Quantity input
        cargo_layout.addWidget(QLabel("Miktar (m³):"))
        quantity_input_layout = QHBoxLayout()
        self.quantity_spin = QDoubleSpinBox()
        self.quantity_spin.setMinimum(0.0)
        self.quantity_spin.setMaximum(self.tank.volume)
        self.quantity_spin.setDecimals(2)
        self.quantity_spin.setSuffix(" m³")
        # Yeterli genişlik ayarla (büyük sayılar için)
        self.quantity_spin.setMinimumWidth(200)
        self.quantity_spin.setAlignment(Qt.AlignmentFlag.AlignRight)
        # Büyük sayıları desteklemek için step size ayarla
        self.quantity_spin.setSingleStep(1.0)
        self.quantity_spin.valueChanged.connect(self.on_quantity_changed)
        quantity_input_layout.addWidget(self.quantity_spin)
        cargo_layout.addLayout(quantity_input_layout)
        
        # Quantity slider for quick adjustment
        slider_layout = QVBoxLayout()
        slider_label_layout = QHBoxLayout()
        slider_label_layout.addWidget(QLabel("0%"))
        slider_label_layout.addStretch()
        slider_label_layout.addWidget(QLabel("50%"))
        slider_label_layout.addStretch()
        slider_label_layout.addWidget(QLabel("100%"))
        slider_layout.addLayout(slider_label_layout)
        
        self.quantity_slider = QSlider(Qt.Orientation.Horizontal)
        self.quantity_slider.setMinimum(0)
        self.quantity_slider.setMaximum(1000)  # 1000 steps for smooth adjustment
        self.quantity_slider.setTickPosition(QSlider.TickPosition.NoTicks)
        self.quantity_slider.valueChanged.connect(self.on_slider_changed)
        slider_layout.addWidget(self.quantity_slider)
        cargo_layout.addLayout(slider_layout)
        
        # Utilization display
        self.utilization_label = QLabel("Doluluk: 0%")
        self.utilization_label.setStyleSheet("font-weight: bold;")
        cargo_layout.addWidget(self.utilization_label)
        
        cargo_group.setLayout(cargo_layout)
        layout.addWidget(cargo_group)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def load_cargo_options(self):
        """Load available cargo options from plan"""
        if not self.plan or not self.plan.cargo_requests:
            return
        
        self.cargo_combo.clear()
        self.cargo_combo.addItem("-- Boş Bırak --", None)
        
        for cargo in self.plan.cargo_requests:
            # Format: "CargoType (Receiver1, Receiver2)" or "CargoType (Genel)"
            receiver_text = cargo.get_receiver_names()
            display_text = f"{cargo.cargo_type} ({receiver_text})"
            self.cargo_combo.addItem(display_text, cargo)
    
    def load_current_assignment(self):
        """Load current tank assignment if exists"""
        if not self.plan:
            return
        
        assignment = self.plan.get_assignment(self.tank.id)
        if assignment:
            # Find cargo in combo box
            for i in range(self.cargo_combo.count()):
                cargo = self.cargo_combo.itemData(i)
                if cargo and cargo.unique_id == assignment.cargo.unique_id:
                    self.cargo_combo.setCurrentIndex(i)
                    # Set quantity - slider will update automatically via on_quantity_changed
                    self.quantity_spin.setValue(assignment.quantity_loaded)
                    break
    
    def on_cargo_selected(self, index: int):
        """Handle cargo selection change"""
        cargo = self.cargo_combo.itemData(index)
        if cargo:
            # Get current assignment for this tank (if exists)
            current_assignment = self.plan.get_assignment(self.tank.id)
            current_tank_qty = current_assignment.quantity_loaded if current_assignment and current_assignment.cargo.unique_id == cargo.unique_id else 0.0
            
            # Plan oluşturulduktan sonra elle düzenleme yapılırken yük miktarı kısıtı kaldırıldı
            # Tank kapasitesini her zaman maksimum olarak ayarla
            # Kullanıcı tam kapasiteye kadar girebilmeli
            self.quantity_spin.setMaximum(self.tank.volume)  # Her zaman tank kapasitesine izin ver
            
            # Auto-fill: prefer current quantity if same cargo, else fill to tank capacity
            if current_tank_qty > 0 and current_assignment and current_assignment.cargo.unique_id == cargo.unique_id:
                # Mevcut yük varsa, mevcut miktarı göster (kullanıcı isterse artırabilir)
                self.quantity_spin.setValue(current_tank_qty)
            else:
                # Yeni yük seçildiğinde tank kapasitesine kadar otomatik doldur
                self.quantity_spin.setValue(self.tank.volume)
        else:
            # Empty selected
            self.quantity_spin.setValue(0.0)
        
        # Slider will be updated automatically via on_quantity_changed
        self.update_utilization()
    
    def on_quantity_changed(self, value: float):
        """Handle quantity change from spinbox"""
        if not self._updating_slider:
            # Update slider position based on quantity
            slider_value = int((value / self.tank.volume * 1000) if self.tank.volume > 0 else 0)
            slider_value = max(0, min(1000, slider_value))  # Clamp to 0-1000
            self._updating_slider = True
            self.quantity_slider.setValue(slider_value)
            self._updating_slider = False
        self.update_utilization()
    
    def on_slider_changed(self, value: int):
        """Handle slider change"""
        if not self._updating_slider:
            # Convert slider value (0-1000) to quantity (0 to tank.volume)
            quantity = (value / 1000.0) * self.tank.volume
            self._updating_slider = True
            self.quantity_spin.setValue(quantity)
            self._updating_slider = False
    
    def update_utilization(self):
        """Update utilization percentage display"""
        quantity = self.quantity_spin.value()
        utilization = (quantity / self.tank.volume * 100) if self.tank.volume > 0 else 0
        
        # Color code
        if utilization >= 70:
            color = "#96CEB4"  # Green
        elif utilization >= 50:
            color = "#FFEAA7"  # Yellow
        else:
            color = "#FF6B6B"  # Red
        
        self.utilization_label.setText(
            f'Doluluk: <span style="color: {color};">{utilization:.1f}%</span>'
        )
    
    def accept(self):
        """Accept dialog and assign cargo"""
        cargo = self.cargo_combo.currentData()
        quantity = self.quantity_spin.value()
        
        # Check if cargo selected and quantity > 0
        if cargo and quantity > 0.001:
            # Check 70% minimum rule
            utilization = (quantity / self.tank.volume * 100) if self.tank.volume > 0 else 0
            if utilization < 70.0:
                reply = QMessageBox.question(
                    self,
                    "Uyarı",
                    f"Tank {utilization:.1f}% dolacak. Minimum %70 kuralı ihlal ediliyor.\n"
                    f"Yine de devam etmek istiyor musunuz?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return
            
            # Plan oluşturulduktan sonra elle düzenleme yapılırken yük miktarı kısıtı kaldırıldı
            # Kullanıcı tank kapasitesine kadar yükleyebilir (sadece tank kapasitesi kısıtı)
            # Yükün başlangıçtaki toplam miktarı (cargo.quantity) kısıtı kaldırıldı
            
            self.selected_cargo = cargo
            self.selected_quantity = quantity
            super().accept()
        elif cargo is None:
            # User wants to empty the tank
            self.selected_cargo = None
            self.selected_quantity = 0.0
            super().accept()
        else:
            QMessageBox.warning(
                self,
                "Uyarı",
                "Lütfen bir yük tipi seçin ve miktar girin."
            )

