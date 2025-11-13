"""Help dialog for displaying user manual"""

import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QPlainTextEdit, QPushButton, 
                             QDialogButtonBox, QHBoxLayout, QApplication)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextOption


def get_help_file_path() -> Path:
    """Get the path to help.txt file
    
    Returns:
        Path to help.txt file (works in both development and PyInstaller EXE mode)
    """
    if getattr(sys, 'frozen', False):
        # Running as compiled EXE (PyInstaller)
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller onefile mode
            base_path = Path(sys._MEIPASS)
        else:
            # PyInstaller onedir mode
            base_path = Path(sys.executable).parent
    else:
        # Running as Python script
        base_path = Path(__file__).parent.parent
    
    return base_path / "help.txt"


class HelpDialog(QDialog):
    """Dialog for displaying help documentation"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Kullanım Kılavuzu")
        self.setMinimumSize(800, 600)
        self.init_ui()
        self.load_help()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Plain text edit for help content (no formatting, just plain text)
        self.text_edit = QPlainTextEdit(self)
        self.text_edit.setReadOnly(True)
        
        # Detect dark mode by checking application palette
        palette = QApplication.palette()
        is_dark = palette.color(palette.ColorRole.Window).lightness() < 128
        
        # Set stylesheet based on dark mode
        if is_dark:
            self.text_edit.setStyleSheet("""
                QPlainTextEdit {
                    background-color: #1e1e1e;
                    color: #e0e0e0;
                    border: 1px solid #444444;
                    border-radius: 4px;
                    padding: 10px;
                    font-family: Arial, sans-serif;
                    font-size: 10pt;
                }
            """)
        else:
            self.text_edit.setStyleSheet("""
                QPlainTextEdit {
                    background-color: #ffffff;
                    color: #333333;
                    border: 1px solid #cccccc;
                    border-radius: 4px;
                    padding: 10px;
                    font-family: Arial, sans-serif;
                    font-size: 10pt;
                }
            """)
        
        # Set text option for word wrapping and no left padding
        text_option = QTextOption()
        text_option.setWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
        text_option.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.text_edit.document().setDefaultTextOption(text_option)
        
        # Remove left margin/padding
        self.text_edit.document().setDocumentMargin(0)
        
        layout.addWidget(self.text_edit)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def load_help(self):
        """Load help.txt file and display it"""
        help_path = get_help_file_path()
        
        if not help_path.exists():
            error_text = f"""Yardım Dosyası Bulunamadı

Yardım dosyası şu konumda bulunamadı:
{help_path}

Lütfen uygulamanın kurulumunu kontrol edin."""
            self.text_edit.setPlainText(error_text)
            return
        
        try:
            with open(help_path, 'r', encoding='utf-8') as f:
                text_content = f.read()
            
            # Set plain text content (no formatting)
            self.text_edit.setPlainText(text_content)
            
        except Exception as e:
            error_text = f"""Hata

Yardım dosyası okunurken bir hata oluştu:
{str(e)}"""
            self.text_edit.setPlainText(error_text)
