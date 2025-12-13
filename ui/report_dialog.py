from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                             QTextEdit, QPushButton, QApplication, 
                             QFileDialog, QMessageBox)
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt

class ReportDialog(QDialog):
    """Dialog to display ASCII report and offer export options"""
    
    def __init__(self, report_text: str, parent=None):
        super().__init__(parent)
        self.report_text = report_text
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Gemi Yukleme Raporu / Stowage Plan Report")
        self.setMinimumSize(800, 600)
        self.resize(900, 700)
        
        layout = QVBoxLayout(self)
        
        # Text Display
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setPlainText(self.report_text)
        
        # Set Monospace Font for alignment
        font = QFont("Courier New", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.text_edit.setFont(font)
        self.text_edit.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        
        layout.addWidget(self.text_edit)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.btn_copy = QPushButton("Kopyala / Copy")
        self.btn_copy.clicked.connect(self.copy_to_clipboard)
        self.btn_copy.setMinimumHeight(40)
        
        self.btn_save = QPushButton("Dosyaya Kaydet / Save to File")
        self.btn_save.clicked.connect(self.save_to_file)
        self.btn_save.setMinimumHeight(40)
        
        self.btn_close = QPushButton("Kapat / Close")
        self.btn_close.clicked.connect(self.accept)
        self.btn_close.setMinimumHeight(40)
        
        button_layout.addWidget(self.btn_copy)
        button_layout.addWidget(self.btn_save)
        button_layout.addStretch()
        button_layout.addWidget(self.btn_close)
        
        layout.addLayout(button_layout)
        
    def copy_to_clipboard(self):
        """Copy report text to clipboard"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.report_text)
        QMessageBox.information(self, "Basarili / Success", 
                                "Rapor panoya kopyalandi.\nReport copied to clipboard.")
        
    def save_to_file(self):
        """Save report text to a file"""
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Raporu Kaydet / Save Report",
            "stowage_report.txt",
            "Text Files (*.txt);;All Files (*)"
        )
        
        if file_name:
            try:
                with open(file_name, 'w', encoding='utf-8') as f:
                    f.write(self.report_text)
                QMessageBox.information(self, "Basarili / Success", 
                                      f"Rapor kaydedildi:\n{file_name}")
            except Exception as e:
                QMessageBox.critical(self, "Hata / Error", 
                                   f"Kayit sirasinda hata olustu:\n{str(e)}")
