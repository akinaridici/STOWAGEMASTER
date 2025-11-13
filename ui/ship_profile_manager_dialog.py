"""Dialog for managing ship profile selection and operations"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QComboBox, QMessageBox, QFileDialog)
from PyQt6.QtCore import Qt
from typing import Optional

from models.ship import Ship
from storage.storage_manager import StorageManager
from ui.ship_profile_dialog import ShipProfileDialog


class ShipProfileManagerDialog(QDialog):
    """Dialog for ship profile selection and management"""
    
    def __init__(self, parent=None, storage: StorageManager = None, current_ship: Optional[Ship] = None):
        super().__init__(parent)
        self.storage = storage or StorageManager()
        self.current_ship = current_ship
        self.selected_ship: Optional[Ship] = None
        
        self.init_ui()
        self.load_ship_profiles()
        
        # Select current ship if provided
        if self.current_ship:
            index = self.ship_combo.findData(self.current_ship.id)
            if index >= 0:
                self.ship_combo.setCurrentIndex(index)
    
    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("Gemi Profili Yönetimi")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Gemi Profili Seçimi ve Yönetimi")
        title_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Ship selection
        ship_label = QLabel("Gemi Seç:")
        layout.addWidget(ship_label)
        
        self.ship_combo = QComboBox()
        self.ship_combo.currentIndexChanged.connect(self.on_ship_selected)
        layout.addWidget(self.ship_combo)
        
        # Ship info
        self.ship_info_label = QLabel("Gemi bilgisi seçilmedi")
        self.ship_info_label.setWordWrap(True)
        self.ship_info_label.setStyleSheet(
            "padding: 10px; "
            "background-color: #2b2b2b; "
            "color: #ffffff; "
            "border-radius: 5px;"
        )
        layout.addWidget(self.ship_info_label)
        
        layout.addSpacing(20)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        new_ship_btn = QPushButton("Yeni Gemi Profili")
        new_ship_btn.clicked.connect(self.create_new_ship_profile)
        btn_layout.addWidget(new_ship_btn)
        
        edit_ship_btn = QPushButton("Profili Düzenle")
        edit_ship_btn.clicked.connect(self.edit_ship_profile)
        edit_ship_btn.setEnabled(False)
        self.edit_ship_btn = edit_ship_btn
        btn_layout.addWidget(edit_ship_btn)
        
        layout.addLayout(btn_layout)
        
        # File operations buttons
        file_btn_layout = QHBoxLayout()
        
        save_file_btn = QPushButton("Dosyaya Kaydet...")
        save_file_btn.clicked.connect(self.save_to_file)
        save_file_btn.setEnabled(False)
        self.save_file_btn = save_file_btn
        file_btn_layout.addWidget(save_file_btn)
        
        load_file_btn = QPushButton("Dosyadan Yükle...")
        load_file_btn.clicked.connect(self.load_from_file)
        file_btn_layout.addWidget(load_file_btn)
        
        layout.addLayout(file_btn_layout)
        
        layout.addStretch()
        
        # Dialog buttons
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("Tamam")
        ok_btn.clicked.connect(self.accept)
        ok_btn.setDefault(True)
        button_layout.addWidget(ok_btn)
        
        layout.addLayout(button_layout)
    
    def load_ship_profiles(self):
        """Load ship profiles into combo box"""
        self.ship_combo.clear()
        ships = self.storage.get_all_ships()
        
        for ship in ships:
            self.ship_combo.addItem(ship.name, ship.id)
        
        if len(ships) == 0:
            self.ship_combo.addItem("-- Gemi profili yok --", None)
    
    def on_ship_selected(self, index: int):
        """Handle ship selection"""
        ship_id = self.ship_combo.itemData(index)
        
        if ship_id:
            ship = self.storage.load_ship_profile(ship_id)
            if ship:
                self.selected_ship = ship
                tank_count = len(ship.tanks)
                total_capacity = ship.get_total_capacity()
                self.ship_info_label.setText(
                    f"<b>{ship.name}</b><br>"
                    f"Tank Sayısı: {tank_count}<br>"
                    f"Toplam Kapasite: {total_capacity:.2f} m³"
                )
                self.edit_ship_btn.setEnabled(True)
                self.save_file_btn.setEnabled(True)
            else:
                self.selected_ship = None
                self.ship_info_label.setText("Gemi bilgisi yüklenemedi")
                self.edit_ship_btn.setEnabled(False)
                self.save_file_btn.setEnabled(False)
        else:
            self.selected_ship = None
            self.ship_info_label.setText("Gemi bilgisi seçilmedi")
            self.edit_ship_btn.setEnabled(False)
            self.save_file_btn.setEnabled(False)
    
    def create_new_ship_profile(self):
        """Open dialog to create new ship profile"""
        dialog = ShipProfileDialog(self, self.storage)
        if dialog.exec():
            self.load_ship_profiles()
            # Select the newly created ship
            new_ship = dialog.ship
            if new_ship:
                index = self.ship_combo.findData(new_ship.id)
                if index >= 0:
                    self.ship_combo.setCurrentIndex(index)
    
    def edit_ship_profile(self):
        """Open dialog to edit current ship profile"""
        if not self.selected_ship:
            return
        
        dialog = ShipProfileDialog(self, self.storage, self.selected_ship)
        if dialog.exec():
            self.load_ship_profiles()
            # Reselect the edited ship
            edited_ship = dialog.ship
            if edited_ship:
                index = self.ship_combo.findData(edited_ship.id)
                if index >= 0:
                    self.ship_combo.setCurrentIndex(index)
    
    def save_to_file(self):
        """Save selected ship profile to a file"""
        if not self.selected_ship:
            QMessageBox.warning(self, "Uyarı", "Lütfen kaydetmek istediğiniz gemi profilini seçin.")
            return
        
        # Get default filename from ship name
        default_filename = f"{self.selected_ship.name}.json"
        # Remove invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            default_filename = default_filename.replace(char, '_')
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Gemi Profilini Kaydet",
            default_filename,
            "JSON Dosyaları (*.json);;Tüm Dosyalar (*.*)"
        )
        
        if file_path:
            if self.storage.save_ship_profile_to_file(self.selected_ship, file_path):
                QMessageBox.information(
                    self,
                    "Başarılı",
                    f"Gemi profili '{self.selected_ship.name}' başarıyla kaydedildi.\n"
                    f"Konum: {file_path}"
                )
            else:
                QMessageBox.critical(
                    self,
                    "Hata",
                    f"Gemi profili kaydedilirken bir hata oluştu.\n"
                    f"Konum: {file_path}"
                )
    
    def load_from_file(self):
        """Load ship profile from a file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Gemi Profili Yükle",
            "",
            "JSON Dosyaları (*.json);;Tüm Dosyalar (*.*)"
        )
        
        if file_path:
            ship = self.storage.load_ship_profile_from_file(file_path)
            if ship:
                # Save to default storage location
                if self.storage.save_ship_profile(ship):
                    QMessageBox.information(
                        self,
                        "Başarılı",
                        f"Gemi profili '{ship.name}' başarıyla yüklendi ve kaydedildi."
                    )
                    # Reload profiles and select the loaded ship
                    self.load_ship_profiles()
                    index = self.ship_combo.findData(ship.id)
                    if index >= 0:
                        self.ship_combo.setCurrentIndex(index)
                else:
                    QMessageBox.critical(
                        self,
                        "Hata",
                        "Gemi profili yüklendi ancak varsayılan klasöre kaydedilemedi."
                    )
            else:
                QMessageBox.critical(
                    self,
                    "Hata",
                    "Gemi profili dosyası yüklenirken bir hata oluştu.\n"
                    "Dosya formatı geçersiz olabilir."
                )

