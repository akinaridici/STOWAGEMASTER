"""Dialog for loading saved plans"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QTableWidget, QTableWidgetItem, QPushButton,
                             QHeaderView, QMessageBox, QDialogButtonBox,
                             QFileDialog)
from PyQt6.QtCore import Qt
from typing import Optional

from models.plan import StowagePlan
from storage.storage_manager import StorageManager


class PlanLoaderDialog(QDialog):
    """Dialog for loading a saved plan from archive"""
    
    def __init__(self, parent=None, storage: StorageManager = None):
        super().__init__(parent)
        self.storage = storage or StorageManager()
        self.selected_plan: Optional[StowagePlan] = None
        self.init_ui()
        self.load_plans()
    
    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("Plan Yükle")
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)
        
        layout = QVBoxLayout(self)
        
        # Info label
        info_label = QLabel("Kaydedilmiş planları seçin:")
        layout.addWidget(info_label)
        
        # Plans table
        self.plans_table = QTableWidget()
        self.plans_table.setColumnCount(5)
        self.plans_table.setHorizontalHeaderLabels(["Plan Adı", "Gemi", "Tarih", "Yük Sayısı", "Notlar"])
        self.plans_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.plans_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.plans_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.plans_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.plans_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.plans_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.plans_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.plans_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.plans_table.doubleClicked.connect(self.accept_selection)
        layout.addWidget(self.plans_table)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        # File browse button
        browse_btn = QPushButton("Dosyadan Yükle...")
        browse_btn.clicked.connect(self.browse_file)
        button_layout.addWidget(browse_btn)
        
        delete_btn = QPushButton("Seçili Planı Sil")
        delete_btn.clicked.connect(self.delete_selected_plan)
        button_layout.addWidget(delete_btn)
        
        button_layout.addStretch()
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept_selection)
        buttons.rejected.connect(self.reject)
        button_layout.addWidget(buttons)
        
        layout.addLayout(button_layout)
    
    def load_plans(self):
        """Load all saved plans"""
        plans = self.storage.get_all_plans()
        
        self.plans_table.setRowCount(len(plans))
        
        for row, plan in enumerate(plans):
            self.plans_table.setItem(row, 0, QTableWidgetItem(plan.plan_name))
            self.plans_table.setItem(row, 1, QTableWidgetItem(plan.ship_name))
            
            date_str = ""
            if plan.created_date:
                date_str = plan.created_date.strftime("%Y-%m-%d %H:%M")
            self.plans_table.setItem(row, 2, QTableWidgetItem(date_str))
            
            cargo_count = len(plan.cargo_requests)
            self.plans_table.setItem(row, 3, QTableWidgetItem(str(cargo_count)))
            
            # Notes column - show truncated version if long
            notes_text = plan.notes if plan.notes else ""
            if len(notes_text) > 50:
                notes_text = notes_text[:47] + "..."
            self.plans_table.setItem(row, 4, QTableWidgetItem(notes_text))
            
            # Store plan ID in item data
            self.plans_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, plan.id)
    
    def accept_selection(self):
        """Accept the selected plan"""
        current_row = self.plans_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir plan seçin.")
            return
        
        plan_id_item = self.plans_table.item(current_row, 0)
        if not plan_id_item:
            return
        
        plan_id = plan_id_item.data(Qt.ItemDataRole.UserRole)
        if not plan_id:
            return
        
        self.selected_plan = self.storage.load_plan(plan_id)
        if self.selected_plan:
            self.accept()
        else:
            QMessageBox.critical(self, "Hata", "Plan yüklenirken bir hata oluştu.")
    
    def delete_selected_plan(self):
        """Delete the selected plan"""
        current_row = self.plans_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen silmek istediğiniz planı seçin.")
            return
        
        plan_id_item = self.plans_table.item(current_row, 0)
        if not plan_id_item:
            return
        
        plan_id = plan_id_item.data(Qt.ItemDataRole.UserRole)
        if not plan_id:
            return
        
        reply = QMessageBox.question(
            self,
            "Plan Sil",
            "Bu planı silmek istediğinizden emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.storage.delete_plan(plan_id):
                self.load_plans()
                QMessageBox.information(self, "Başarılı", "Plan silindi.")
            else:
                QMessageBox.critical(self, "Hata", "Plan silinirken bir hata oluştu.")
    
    def browse_file(self):
        """Open file dialog to load plan from file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Plan Yükle",
            "",
            "JSON Dosyaları (*.json);;Tüm Dosyalar (*.*)"
        )
        
        if file_path:
            plan = self.storage.load_plan_from_file(file_path)
            if plan:
                self.selected_plan = plan
                self.accept()
            else:
                QMessageBox.critical(
                    self,
                    "Hata",
                    "Plan dosyası yüklenirken bir hata oluştu.\n"
                    "Dosya formatı geçersiz olabilir."
                )

