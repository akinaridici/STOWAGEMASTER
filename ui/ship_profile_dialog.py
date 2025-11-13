"""Dialog for creating/editing ship profiles"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
                             QMessageBox, QHeaderView, QDoubleSpinBox)
from PyQt6.QtCore import Qt
from typing import Optional

from models.ship import Ship, Tank
from storage.storage_manager import StorageManager
from utils.validators import validate_positive_number, validate_tank_name


class ShipProfileDialog(QDialog):
    """Dialog for ship profile creation/editing"""
    
    def __init__(self, parent=None, storage: StorageManager = None, ship: Ship = None):
        super().__init__(parent)
        self.storage = storage or StorageManager()
        self.ship = ship
        self.init_ui()
        
        if self.ship:
            self.load_ship_data()
    
    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("Gemi Profili" + (" - Düzenle" if self.ship else " - Yeni"))
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        
        layout = QVBoxLayout(self)
        
        # Ship name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Gemi Adı:"))
        self.name_input = QLineEdit()
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)
        
        # Tank table
        tanks_label = QLabel("Tanklar:")
        layout.addWidget(tanks_label)
        
        self.tank_table = QTableWidget()
        self.tank_table.setColumnCount(2)
        self.tank_table.setHorizontalHeaderLabels(["Tank Adı", "Kapasite (m³)"])
        self.tank_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tank_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.tank_table)
        
        # Tank controls
        tank_controls = QHBoxLayout()
        
        self.tank_name_input = QLineEdit()
        self.tank_name_input.setPlaceholderText("Tank adı")
        tank_controls.addWidget(self.tank_name_input)
        
        self.tank_volume_input = QDoubleSpinBox()
        self.tank_volume_input.setMinimum(0.01)
        self.tank_volume_input.setMaximum(1000000)
        self.tank_volume_input.setSuffix(" m³")
        self.tank_volume_input.setDecimals(2)
        tank_controls.addWidget(self.tank_volume_input)
        
        add_tank_btn = QPushButton("Tank Ekle")
        add_tank_btn.clicked.connect(self.add_tank)
        tank_controls.addWidget(add_tank_btn)
        
        remove_tank_btn = QPushButton("Seçili Tankı Sil")
        remove_tank_btn.clicked.connect(self.remove_selected_tank)
        tank_controls.addWidget(remove_tank_btn)
        
        layout.addLayout(tank_controls)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        save_btn = QPushButton("Kaydet")
        save_btn.clicked.connect(self.save_ship)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def load_ship_data(self):
        """Load existing ship data"""
        if not self.ship:
            return
        
        self.name_input.setText(self.ship.name)
        
        self.tank_table.setRowCount(len(self.ship.tanks))
        for row, tank in enumerate(self.ship.tanks):
            self.tank_table.setItem(row, 0, QTableWidgetItem(tank.name))
            self.tank_table.setItem(row, 1, QTableWidgetItem(str(tank.volume)))
            # Store tank ID in item data
            self.tank_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, tank.id)
    
    def add_tank(self):
        """Add a new tank to the table"""
        name = self.tank_name_input.text().strip()
        volume = self.tank_volume_input.value()
        
        if not name:
            QMessageBox.warning(self, "Hata", "Lütfen tank adı girin.")
            return
        
        # Check for duplicate names
        existing_names = []
        for row in range(self.tank_table.rowCount()):
            item = self.tank_table.item(row, 0)
            if item:
                existing_names.append(item.text())
        
        is_valid, error_msg = validate_tank_name(name, existing_names)
        if not is_valid:
            QMessageBox.warning(self, "Hata", error_msg)
            return
        
        # Add to table
        row = self.tank_table.rowCount()
        self.tank_table.insertRow(row)
        self.tank_table.setItem(row, 0, QTableWidgetItem(name))
        self.tank_table.setItem(row, 1, QTableWidgetItem(str(volume)))
        
        # Clear inputs
        self.tank_name_input.clear()
        self.tank_volume_input.setValue(0.01)
    
    def remove_selected_tank(self):
        """Remove selected tank from table"""
        current_row = self.tank_table.currentRow()
        if current_row >= 0:
            reply = QMessageBox.question(
                self,
                "Tank Sil",
                "Bu tankı silmek istediğinizden emin misiniz?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.tank_table.removeRow(current_row)
        else:
            QMessageBox.warning(self, "Uyarı", "Lütfen silmek istediğiniz tankı seçin.")
    
    def save_ship(self):
        """Save ship profile"""
        ship_name = self.name_input.text().strip()
        if not ship_name:
            QMessageBox.warning(self, "Hata", "Lütfen gemi adı girin.")
            return
        
        # Collect tanks from table
        tanks = []
        existing_names = []
        for row in range(self.tank_table.rowCount()):
            name_item = self.tank_table.item(row, 0)
            volume_item = self.tank_table.item(row, 1)
            
            if name_item and volume_item:
                name = name_item.text().strip()
                try:
                    volume = float(volume_item.text())
                except ValueError:
                    QMessageBox.warning(
                        self,
                        "Hata",
                        f"Satır {row + 1}: Geçersiz kapasite değeri."
                    )
                    return
                
                if not name:
                    QMessageBox.warning(
                        self,
                        "Hata",
                        f"Satır {row + 1}: Tank adı boş olamaz."
                    )
                    return
                
                if name in existing_names:
                    QMessageBox.warning(
                        self,
                        "Hata",
                        f"Satır {row + 1}: '{name}' isimli tank zaten var."
                    )
                    return
                
                existing_names.append(name)
                
                # Check if this is an existing tank (has ID in data)
                tank_id = None
                if name_item.data(Qt.ItemDataRole.UserRole):
                    tank_id = name_item.data(Qt.ItemDataRole.UserRole)
                
                tank = Tank(id=tank_id, name=name, volume=volume)
                tanks.append(tank)
        
        if len(tanks) == 0:
            QMessageBox.warning(self, "Hata", "En az bir tank tanımlanmalıdır.")
            return
        
        # Create or update ship
        if self.ship:
            # Update existing ship
            self.ship.name = ship_name
            self.ship.tanks = tanks
        else:
            # Create new ship
            self.ship = Ship(name=ship_name, tanks=tanks)
        
        # Save to storage
        if self.storage.save_ship_profile(self.ship):
            QMessageBox.information(self, "Başarılı", "Gemi profili kaydedildi.")
            self.accept()
        else:
            QMessageBox.critical(self, "Hata", "Gemi profili kaydedilirken bir hata oluştu.")

