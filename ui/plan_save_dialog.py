"""Dialog for saving a plan with name and notes"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QTextEdit, QDialogButtonBox, QPushButton,
                             QFileDialog)
from PyQt6.QtCore import Qt
from pathlib import Path

from models.plan import StowagePlan


class PlanSaveDialog(QDialog):
    """Dialog for saving a plan with custom name and notes"""
    
    def __init__(self, parent=None, plan: StowagePlan = None):
        super().__init__(parent)
        self.plan = plan
        self.selected_file_path: str = None
        self.init_ui()
        
        # Load existing plan data if available
        if plan:
            self.load_plan_data()
    
    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("Planı Kaydet")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        layout = QVBoxLayout(self)
        
        # Plan name input
        name_layout = QVBoxLayout()
        name_label = QLabel("Plan Adı:")
        name_label.setStyleSheet("font-weight: bold;")
        name_layout.addWidget(name_label)
        
        self.plan_name_input = QLineEdit()
        self.plan_name_input.setPlaceholderText("Plan adını girin...")
        name_layout.addWidget(self.plan_name_input)
        
        layout.addLayout(name_layout)
        
        # File path selection
        file_layout = QVBoxLayout()
        file_label = QLabel("Kayıt Konumu:")
        file_label.setStyleSheet("font-weight: bold;")
        file_layout.addWidget(file_label)
        
        file_path_layout = QHBoxLayout()
        self.file_path_input = QLineEdit()
        self.file_path_input.setPlaceholderText("Kaydetmek istediğiniz klasör ve dosya adını seçin...")
        self.file_path_input.setReadOnly(True)
        file_path_layout.addWidget(self.file_path_input)
        
        browse_btn = QPushButton("Klasör Seç...")
        browse_btn.clicked.connect(self.browse_file)
        file_path_layout.addWidget(browse_btn)
        
        file_layout.addLayout(file_path_layout)
        layout.addLayout(file_layout)
        
        # Notes input
        notes_layout = QVBoxLayout()
        notes_label = QLabel("Notlar (Detaylı açıklama):")
        notes_label.setStyleSheet("font-weight: bold;")
        notes_layout.addWidget(notes_label)
        
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Plan hakkında detaylı notlar yazabilirsiniz...\nÖrn: Yükleme sırası, özel gereksinimler, önemli notlar vb.")
        self.notes_input.setMinimumHeight(200)
        notes_layout.addWidget(self.notes_input)
        
        layout.addLayout(notes_layout)
        
        # Info label
        info_label = QLabel(
            "Not: Plan adı boş bırakılırsa otomatik olarak oluşturulacaktır.\n"
            "Kayıt konumu seçilmezse varsayılan klasöre kaydedilir."
        )
        info_label.setStyleSheet("color: #666666; font-size: 9pt;")
        layout.addWidget(info_label)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Kaydet")
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def load_plan_data(self):
        """Load existing plan data into inputs"""
        if self.plan:
            if self.plan.plan_name:
                self.plan_name_input.setText(self.plan.plan_name)
            if self.plan.notes:
                self.notes_input.setPlainText(self.plan.notes)
    
    def validate_and_accept(self):
        """Validate input and accept dialog"""
        plan_name = self.plan_name_input.text().strip()
        
        # Plan name is optional - will use default if empty
        # No validation needed
        
        self.accept()
    
    def get_plan_name(self) -> str:
        """Get entered plan name"""
        name = self.plan_name_input.text().strip()
        return name if name else None
    
    def get_notes(self) -> str:
        """Get entered notes"""
        return self.notes_input.toPlainText().strip()
    
    def browse_file(self):
        """Open file dialog to select save location"""
        plan_name = self.plan_name_input.text().strip()
        if not plan_name:
            plan_name = "Plan"
        
        # Remove invalid characters from filename
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            plan_name = plan_name.replace(char, '_')
        
        default_filename = f"{plan_name}.json"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Planı Kaydet",
            default_filename,
            "JSON Dosyaları (*.json);;Tüm Dosyalar (*.*)"
        )
        
        if file_path:
            self.selected_file_path = file_path
            self.file_path_input.setText(file_path)
    
    def get_file_path(self) -> str:
        """Get selected file path"""
        return self.selected_file_path

