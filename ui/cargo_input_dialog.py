"""Dialog/widget for cargo input"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QTableWidget, QTableWidgetItem, QPushButton,
                             QLineEdit, QDoubleSpinBox, QMessageBox,
                             QHeaderView, QDialog, QDialogButtonBox, QCheckBox)
from PyQt6.QtCore import Qt, pyqtSignal
from typing import List

from models.cargo import Cargo, Receiver
from utils.validators import validate_positive_number


class CargoInputDialog(QWidget):
    """Widget for entering cargo loading requests"""
    
    # Signal emitted when cargo list changes
    cargo_list_changed = pyqtSignal()
    
    def __init__(self, parent=None, embedded: bool = False):
        super().__init__(parent)
        self.embedded = embedded
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        
        # Table for cargo entries - genişleyebilmeli (stretch faktörü 1)
        self.cargo_table = QTableWidget()
        self.cargo_table.setColumnCount(7)
        self.cargo_table.setHorizontalHeaderLabels(["Yük Tipi", "Ton", "Density (ton/m³)", "Hacim (m³)", "Alıcı(lar)", "Mutlak", ""])
        self.cargo_table.setSortingEnabled(False)  # Disable automatic sorting to preserve user's order
        self.cargo_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.cargo_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.cargo_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.cargo_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.cargo_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.cargo_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.cargo_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        
        # Make table read-only for embedded mode
        if self.embedded:
            self.cargo_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Tabloyu stretch faktörü ile ekle - bölümün büyük kısmını kullanacak
        layout.addWidget(self.cargo_table, 1)
        
        # Input controls - sabit boyut (stretch faktörü 0)
        if self.embedded:
            input_group = QHBoxLayout()
            
            self.cargo_type_input = QLineEdit()
            self.cargo_type_input.setPlaceholderText("Yük tipi (örn: Gasoil)")
            input_group.addWidget(self.cargo_type_input)
            
            self.ton_input = QDoubleSpinBox()
            self.ton_input.setMinimum(0.01)
            self.ton_input.setMaximum(1000000)
            self.ton_input.setSuffix(" ton")
            self.ton_input.setDecimals(2)
            self.ton_input.valueChanged.connect(self.calculate_volume)
            input_group.addWidget(self.ton_input)
            
            self.density_input = QDoubleSpinBox()
            self.density_input.setMinimum(0.01)
            self.density_input.setMaximum(10.0)
            self.density_input.setDecimals(3)
            self.density_input.setSingleStep(0.01)
            self.density_input.setValue(0.85)  # Default density
            self.density_input.setToolTip("Yoğunluk (ton/m³)")
            self.density_input.valueChanged.connect(self.calculate_volume)
            input_group.addWidget(self.density_input)
            
            # Volume display (read-only)
            self.volume_label = QLabel("Hacim: 0.00 m³")
            self.volume_label.setStyleSheet("font-weight: bold; color: #0066cc;")
            input_group.addWidget(self.volume_label)
            
            self.receiver_input = QLineEdit()
            self.receiver_input.setPlaceholderText("Alıcı adı (virgülle ayırın)")
            input_group.addWidget(self.receiver_input)
            
            self.mandatory_checkbox = QCheckBox("Mutlak Yük")
            self.mandatory_checkbox.setToolTip("Bu yük mutlaka planlanacak, miktarı azaltılamaz")
            input_group.addWidget(self.mandatory_checkbox)
            
            add_btn = QPushButton("Ekle")
            add_btn.clicked.connect(self.add_cargo)
            input_group.addWidget(add_btn)
            
            remove_btn = QPushButton("Seçiliyi Sil")
            remove_btn.clicked.connect(self.remove_selected_cargo)
            input_group.addWidget(remove_btn)
            
            # Input controls'e stretch faktörü verme - sabit boyut
            layout.addLayout(input_group, 0)
    
    def calculate_volume(self):
        """Calculate volume from ton and density"""
        ton = self.ton_input.value()
        density = self.density_input.value()
        
        if density > 0:
            volume = ton / density
            self.volume_label.setText(f"Hacim: {volume:.2f} m³")
        else:
            self.volume_label.setText("Hacim: 0.00 m³")
    
    def add_cargo(self):
        """Add a new cargo entry"""
        cargo_type = self.cargo_type_input.text().strip()
        ton = self.ton_input.value()
        density = self.density_input.value()
        receiver_text = self.receiver_input.text().strip()
        
        if not cargo_type:
            QMessageBox.warning(self, "Hata", "Lütfen yük tipi girin.")
            return
        
        if ton <= 0:
            QMessageBox.warning(self, "Hata", "Ton miktarı pozitif bir sayı olmalıdır.")
            return
        
        if density <= 0:
            QMessageBox.warning(self, "Hata", "Yoğunluk pozitif bir sayı olmalıdır.")
            return
        
        # Calculate volume
        volume = ton / density
        
        # Parse receivers
        receivers = []
        if receiver_text:
            receiver_names = [name.strip() for name in receiver_text.split(',')]
            receivers = [Receiver(name=name) for name in receiver_names if name]
        
        # Get mandatory flag
        is_mandatory = self.mandatory_checkbox.isChecked()
        
        # Add to table
        row = self.cargo_table.rowCount()
        self.cargo_table.insertRow(row)
        
        self.cargo_table.setItem(row, 0, QTableWidgetItem(cargo_type))
        self.cargo_table.setItem(row, 1, QTableWidgetItem(f"{ton:.2f}"))
        self.cargo_table.setItem(row, 2, QTableWidgetItem(f"{density:.3f}"))
        self.cargo_table.setItem(row, 3, QTableWidgetItem(f"{volume:.2f}"))
        receiver_names_str = ", ".join([r.name for r in receivers]) if receivers else "Genel"
        self.cargo_table.setItem(row, 4, QTableWidgetItem(receiver_names_str))
        
        # Mandatory checkbox in table
        mandatory_checkbox = QCheckBox()
        mandatory_checkbox.setChecked(is_mandatory)
        mandatory_checkbox.stateChanged.connect(lambda: self.cargo_list_changed.emit())
        self.cargo_table.setCellWidget(row, 5, mandatory_checkbox)
        
        # Store cargo object in item data
        cargo = Cargo(cargo_type=cargo_type, quantity=volume, ton=ton, density=density, 
                     receivers=receivers, is_mandatory=is_mandatory)
        self.cargo_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, cargo)
        
        # Edit button - use dynamic row finding to avoid closure issues
        edit_btn = QPushButton("Düzenle")
        edit_btn.clicked.connect(self._on_edit_button_clicked)
        self.cargo_table.setCellWidget(row, 6, edit_btn)
        
        # Clear inputs
        self.cargo_type_input.clear()
        self.ton_input.setValue(0.01)
        self.density_input.setValue(0.85)
        self.volume_label.setText("Hacim: 0.00 m³")
        self.receiver_input.clear()
        self.mandatory_checkbox.setChecked(False)
        
        # Emit signal
        self.cargo_list_changed.emit()
    
    def remove_selected_cargo(self):
        """Remove selected cargo entry"""
        current_row = self.cargo_table.currentRow()
        if current_row >= 0:
            reply = QMessageBox.question(
                self,
                "Yük Sil",
                "Bu yükü silmek istediğinizden emin misiniz?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.cargo_table.removeRow(current_row)
                # Reconnect all edit buttons after row removal to fix closure issue
                self._reconnect_edit_buttons()
                # Emit signal
                self.cargo_list_changed.emit()
        else:
            QMessageBox.warning(self, "Uyarı", "Lütfen silmek istediğiniz yükü seçin.")
    
    def _reconnect_edit_buttons(self):
        """Reconnect all edit buttons with correct row indices after row removal"""
        for row in range(self.cargo_table.rowCount()):
            # Get or create edit button
            edit_btn = self.cargo_table.cellWidget(row, 6)
            if edit_btn:
                # Disconnect old signal
                try:
                    edit_btn.clicked.disconnect()
                except TypeError:
                    # No connections to disconnect
                    pass
            else:
                # Create new button if missing
                edit_btn = QPushButton("Düzenle")
                self.cargo_table.setCellWidget(row, 6, edit_btn)
            
            # Reconnect with a method that finds the row dynamically
            # This avoids closure issues by finding the row at click time
            edit_btn.clicked.connect(self._on_edit_button_clicked)
    
    def _on_edit_button_clicked(self):
        """Handle edit button click by finding the row dynamically"""
        from PyQt6.QtWidgets import QPushButton
        
        # Get the button that was clicked
        button = self.sender()
        if not isinstance(button, QPushButton):
            return
        
        # Find which row this button is in
        for row in range(self.cargo_table.rowCount()):
            if self.cargo_table.cellWidget(row, 6) == button:
                self.edit_cargo(row)
                return
    
    def edit_cargo(self, row: int):
        """Edit cargo at specified row"""
        cargo_item = self.cargo_table.item(row, 0)
        if not cargo_item:
            return
        
        cargo = cargo_item.data(Qt.ItemDataRole.UserRole)
        if not cargo:
            return
        
        # Open edit dialog
        dialog = CargoEditDialog(self, cargo)
        if dialog.exec():
            updated_cargo = dialog.get_cargo()
            
            # Update table
            self.cargo_table.setItem(row, 0, QTableWidgetItem(updated_cargo.cargo_type))
            ton_display = f"{updated_cargo.ton:.2f}" if updated_cargo.ton else "-"
            density_display = f"{updated_cargo.density:.3f}" if updated_cargo.density else "-"
            self.cargo_table.setItem(row, 1, QTableWidgetItem(ton_display))
            self.cargo_table.setItem(row, 2, QTableWidgetItem(density_display))
            self.cargo_table.setItem(row, 3, QTableWidgetItem(f"{updated_cargo.quantity:.2f}"))
            receiver_names_str = ", ".join([r.name for r in updated_cargo.receivers]) if updated_cargo.receivers else "Genel"
            self.cargo_table.setItem(row, 4, QTableWidgetItem(receiver_names_str))
            
            # Update mandatory checkbox
            mandatory_widget = self.cargo_table.cellWidget(row, 5)
            if mandatory_widget:
                mandatory_widget.setChecked(updated_cargo.is_mandatory)
            else:
                mandatory_checkbox = QCheckBox()
                mandatory_checkbox.setChecked(updated_cargo.is_mandatory)
                mandatory_checkbox.stateChanged.connect(lambda: self.cargo_list_changed.emit())
                self.cargo_table.setCellWidget(row, 5, mandatory_checkbox)
            
            # Update stored cargo
            self.cargo_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, updated_cargo)
            
            # Emit signal
            self.cargo_list_changed.emit()
    
    def get_cargo_list(self) -> List[Cargo]:
        """Get list of all cargo entries"""
        cargo_list = []
        
        for row in range(self.cargo_table.rowCount()):
            cargo_item = self.cargo_table.item(row, 0)
            if cargo_item:
                cargo = cargo_item.data(Qt.ItemDataRole.UserRole)
                if cargo:
                    # Update mandatory flag from checkbox
                    mandatory_widget = self.cargo_table.cellWidget(row, 5)
                    if mandatory_widget and isinstance(mandatory_widget, QCheckBox):
                        cargo.is_mandatory = mandatory_widget.isChecked()
                    cargo_list.append(cargo)
        
        return cargo_list
    
    def set_cargo_list(self, cargo_list: List[Cargo]):
        """Set cargo list (for loading saved plans)"""
        self.cargo_table.setRowCount(0)
        
        for cargo in cargo_list:
            row = self.cargo_table.rowCount()
            self.cargo_table.insertRow(row)
            
            self.cargo_table.setItem(row, 0, QTableWidgetItem(cargo.cargo_type))
            ton_display = f"{cargo.ton:.2f}" if cargo.ton else "-"
            density_display = f"{cargo.density:.3f}" if cargo.density else "-"
            self.cargo_table.setItem(row, 1, QTableWidgetItem(ton_display))
            self.cargo_table.setItem(row, 2, QTableWidgetItem(density_display))
            self.cargo_table.setItem(row, 3, QTableWidgetItem(f"{cargo.quantity:.2f}"))
            receiver_names_str = ", ".join([r.name for r in cargo.receivers]) if cargo.receivers else "Genel"
            self.cargo_table.setItem(row, 4, QTableWidgetItem(receiver_names_str))
            
            # Mandatory checkbox
            mandatory_checkbox = QCheckBox()
            mandatory_checkbox.setChecked(cargo.is_mandatory)
            mandatory_checkbox.stateChanged.connect(lambda: self.cargo_list_changed.emit())
            self.cargo_table.setCellWidget(row, 5, mandatory_checkbox)
            
            # Store cargo object
            self.cargo_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, cargo)
            
            # Edit button (use default parameter to avoid closure issue)
            edit_btn = QPushButton("Düzenle")
            edit_btn.clicked.connect(lambda checked=False, r=row: self.edit_cargo(r))
            self.cargo_table.setCellWidget(row, 6, edit_btn)


class CargoEditDialog(QDialog):
    """Dialog for editing a single cargo entry"""
    
    def __init__(self, parent=None, cargo: Cargo = None):
        super().__init__(parent)
        self.cargo = cargo or Cargo(cargo_type="", quantity=0.0)
        self.init_ui()
        
        if cargo:
            self.load_cargo_data()
    
    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("Yük Düzenle")
        layout = QVBoxLayout(self)
        
        # Cargo type
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Yük Tipi:"))
        self.cargo_type_input = QLineEdit()
        type_layout.addWidget(self.cargo_type_input)
        layout.addLayout(type_layout)
        
        # Ton
        ton_layout = QHBoxLayout()
        ton_layout.addWidget(QLabel("Ton:"))
        self.ton_input = QDoubleSpinBox()
        self.ton_input.setMinimum(0.01)
        self.ton_input.setMaximum(1000000)
        self.ton_input.setSuffix(" ton")
        self.ton_input.setDecimals(2)
        self.ton_input.valueChanged.connect(self.calculate_volume)
        ton_layout.addWidget(self.ton_input)
        layout.addLayout(ton_layout)
        
        # Density
        density_layout = QHBoxLayout()
        density_layout.addWidget(QLabel("Density (ton/m³):"))
        self.density_input = QDoubleSpinBox()
        self.density_input.setMinimum(0.01)
        self.density_input.setMaximum(10.0)
        self.density_input.setDecimals(3)
        self.density_input.setSingleStep(0.01)
        self.density_input.setToolTip("Yoğunluk (ton/m³)")
        self.density_input.valueChanged.connect(self.calculate_volume)
        density_layout.addWidget(self.density_input)
        layout.addLayout(density_layout)
        
        # Volume display (read-only)
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("Hacim:"))
        self.volume_label = QLabel("0.00 m³")
        self.volume_label.setStyleSheet("font-weight: bold; color: #0066cc;")
        volume_layout.addWidget(self.volume_label)
        volume_layout.addStretch()
        layout.addLayout(volume_layout)
        
        # Receivers
        receiver_layout = QHBoxLayout()
        receiver_layout.addWidget(QLabel("Alıcı(lar):"))
        self.receiver_input = QLineEdit()
        self.receiver_input.setPlaceholderText("Virgülle ayırın")
        receiver_layout.addWidget(self.receiver_input)
        layout.addLayout(receiver_layout)
        
        # Mandatory checkbox
        mandatory_layout = QHBoxLayout()
        self.mandatory_checkbox = QCheckBox("Mutlak Yük")
        self.mandatory_checkbox.setToolTip("Bu yük mutlaka planlanacak, miktarı azaltılamaz")
        mandatory_layout.addWidget(self.mandatory_checkbox)
        mandatory_layout.addStretch()
        layout.addLayout(mandatory_layout)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def load_cargo_data(self):
        """Load cargo data into inputs"""
        self.cargo_type_input.setText(self.cargo.cargo_type)
        
        if self.cargo.ton is not None:
            self.ton_input.setValue(self.cargo.ton)
        else:
            self.ton_input.setValue(0.01)
        
        if self.cargo.density is not None:
            self.density_input.setValue(self.cargo.density)
        else:
            self.density_input.setValue(0.85)
        
        self.calculate_volume()
        
        if self.cargo.receivers:
            receiver_names = ", ".join([r.name for r in self.cargo.receivers])
            self.receiver_input.setText(receiver_names)
        
        self.mandatory_checkbox.setChecked(self.cargo.is_mandatory)
    
    def calculate_volume(self):
        """Calculate volume from ton and density"""
        ton = self.ton_input.value()
        density = self.density_input.value()
        
        if density > 0:
            volume = ton / density
            self.volume_label.setText(f"{volume:.2f} m³")
        else:
            self.volume_label.setText("0.00 m³")
    
    def get_cargo(self) -> Cargo:
        """Get updated cargo object"""
        cargo_type = self.cargo_type_input.text().strip()
        ton = self.ton_input.value()
        density = self.density_input.value()
        receiver_text = self.receiver_input.text().strip()
        
        # Calculate volume
        volume = ton / density if density > 0 else 0.0
        
        receivers = []
        if receiver_text:
            receiver_names = [name.strip() for name in receiver_text.split(',')]
            receivers = [Receiver(name=name) for name in receiver_names if name]
        
        return Cargo(
            cargo_type=cargo_type,
            quantity=volume,
            ton=ton,
            density=density,
            receivers=receivers,
            unique_id=self.cargo.unique_id,  # Preserve ID
            is_mandatory=self.mandatory_checkbox.isChecked()
        )

