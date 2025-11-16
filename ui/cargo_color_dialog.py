"""Dialog for selecting custom color for cargo"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QWidget, QDialogButtonBox, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from utils.color_palette import (COLOR_PALETTE, get_color_name, get_color_tones,
                                 get_main_color, get_all_color_keys)


class CargoColorDialog(QDialog):
    """Dialog for selecting custom color for cargo"""
    
    def __init__(self, parent=None, current_color: str = None):
        super().__init__(parent)
        self.selected_color = current_color  # Initially set to current color
        self.selected_color_key = None
        self.selected_tone_index = None
        
        self.setWindowTitle("Renk Seç")
        self.setMinimumSize(500, 400)
        
        self.init_ui()
        
        # If current_color is provided, try to find it in palette and select it
        if current_color:
            result = self._find_color_in_palette(current_color)
            if result:
                color_key, tone_index = result
                self._select_color(color_key)
                self._select_tone(tone_index)
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Yük Rengi Seç")
        title_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Main color selection (6 buttons)
        main_colors_label = QLabel("Ana Renk Seçin:")
        main_colors_label.setStyleSheet("font-size: 11pt; font-weight: bold; margin-top: 10px;")
        layout.addWidget(main_colors_label)
        
        main_colors_widget = QWidget()
        main_colors_layout = QHBoxLayout(main_colors_widget)
        main_colors_layout.setSpacing(10)
        
        self.color_buttons = {}
        color_keys = get_all_color_keys()
        
        for color_key in color_keys:
            main_color = get_main_color(color_key)
            color_name = get_color_name(color_key)
            
            btn = QPushButton(color_name)
            btn.setMinimumSize(80, 60)
            btn.setMaximumSize(80, 60)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {main_color};
                    border: 3px solid #333;
                    border-radius: 5px;
                    color: white;
                    font-weight: bold;
                    font-size: 10pt;
                }}
                QPushButton:hover {{
                    border: 3px solid #000;
                }}
                QPushButton:pressed {{
                    border: 3px solid #666;
                }}
            """)
            btn.clicked.connect(lambda checked=False, key=color_key: self._select_color(key))
            self.color_buttons[color_key] = btn
            main_colors_layout.addWidget(btn)
        
        main_colors_layout.addStretch()
        layout.addWidget(main_colors_widget)
        
        # Tone selection (shown after color is selected)
        self.tone_label = QLabel("Ton Seçin:")
        self.tone_label.setStyleSheet("font-size: 11pt; font-weight: bold; margin-top: 10px;")
        self.tone_label.setVisible(False)
        layout.addWidget(self.tone_label)
        
        self.tone_widget = QWidget()
        self.tone_layout = QHBoxLayout(self.tone_widget)
        self.tone_layout.setSpacing(10)
        self.tone_widget.setVisible(False)
        layout.addWidget(self.tone_widget)
        
        # Preview
        self.preview_label = QLabel("Önizleme:")
        self.preview_label.setStyleSheet("font-size: 11pt; font-weight: bold; margin-top: 10px;")
        layout.addWidget(self.preview_label)
        
        self.preview_widget = QWidget()
        self.preview_widget.setMinimumHeight(80)
        self.preview_widget.setMaximumHeight(80)
        self.preview_widget.setStyleSheet("border: 2px solid #333; border-radius: 5px; background-color: #E0E0E0;")
        layout.addWidget(self.preview_widget)
        
        # Default button
        default_btn = QPushButton("Varsayılan Renk")
        default_btn.setStyleSheet("font-size: 10pt; padding: 5px;")
        default_btn.clicked.connect(self._select_default)
        layout.addWidget(default_btn)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def _select_color(self, color_key: str):
        """Select a main color and show tone options"""
        self.selected_color_key = color_key
        
        # Highlight selected color button
        for key, btn in self.color_buttons.items():
            if key == color_key:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {get_main_color(key)};
                        border: 4px solid #FFD700;
                        border-radius: 5px;
                        color: white;
                        font-weight: bold;
                        font-size: 10pt;
                    }}
                    QPushButton:hover {{
                        border: 4px solid #FFA500;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {get_main_color(key)};
                        border: 3px solid #333;
                        border-radius: 5px;
                        color: white;
                        font-weight: bold;
                        font-size: 10pt;
                    }}
                    QPushButton:hover {{
                        border: 3px solid #000;
                    }}
                """)
        
        # Clear previous tone buttons
        while self.tone_layout.count():
            item = self.tone_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Create tone buttons
        tones = get_color_tones(color_key)
        self.tone_buttons = []
        
        for tone_index, tone_hex in enumerate(tones):
            btn = QPushButton(f"Ton {tone_index + 1}")
            btn.setMinimumSize(70, 50)
            btn.setMaximumSize(70, 50)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {tone_hex};
                    border: 2px solid #333;
                    border-radius: 5px;
                    color: {'white' if tone_index < 2 else 'black'};
                    font-weight: bold;
                    font-size: 9pt;
                }}
                QPushButton:hover {{
                    border: 2px solid #000;
                }}
            """)
            btn.clicked.connect(lambda checked=False, idx=tone_index: self._select_tone(idx))
            self.tone_buttons.append(btn)
            self.tone_layout.addWidget(btn)
        
        self.tone_layout.addStretch()
        
        # Show tone selection
        self.tone_label.setVisible(True)
        self.tone_widget.setVisible(True)
        
        # Auto-select first tone (main color)
        if tones:
            self._select_tone(0)
    
    def _select_tone(self, tone_index: int):
        """Select a tone and update preview"""
        if self.selected_color_key is None:
            return
        
        self.selected_tone_index = tone_index
        tones = get_color_tones(self.selected_color_key)
        
        if 0 <= tone_index < len(tones):
            self.selected_color = tones[tone_index]
            
            # Highlight selected tone button
            for idx, btn in enumerate(self.tone_buttons):
                if idx == tone_index:
                    btn.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {tones[idx]};
                            border: 3px solid #FFD700;
                            border-radius: 5px;
                            color: {'white' if idx < 2 else 'black'};
                            font-weight: bold;
                            font-size: 9pt;
                        }}
                    """)
                else:
                    btn.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {tones[idx]};
                            border: 2px solid #333;
                            border-radius: 5px;
                            color: {'white' if idx < 2 else 'black'};
                            font-weight: bold;
                            font-size: 9pt;
                        }}
                        QPushButton:hover {{
                            border: 2px solid #000;
                        }}
                    """)
            
            # Update preview
            self.preview_widget.setStyleSheet(f"""
                border: 2px solid #333;
                border-radius: 5px;
                background-color: {self.selected_color};
            """)
    
    def _select_default(self):
        """Select default (None) color"""
        self.selected_color = None
        self.selected_color_key = None
        self.selected_tone_index = None
        
        # Reset color button highlights
        for key, btn in self.color_buttons.items():
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {get_main_color(key)};
                    border: 3px solid #333;
                    border-radius: 5px;
                    color: white;
                    font-weight: bold;
                    font-size: 10pt;
                }}
                QPushButton:hover {{
                    border: 3px solid #000;
                }}
            """)
        
        # Hide tone selection
        self.tone_label.setVisible(False)
        self.tone_widget.setVisible(False)
        
        # Update preview to gray
        self.preview_widget.setStyleSheet("border: 2px solid #333; border-radius: 5px; background-color: #E0E0E0;")
    
    def _find_color_in_palette(self, hex_color: str):
        """Find color key and tone index for a hex color"""
        from utils.color_palette import find_color_for_hex
        return find_color_for_hex(hex_color)
    
    def get_selected_color(self) -> str:
        """Get selected color hex code
        
        Returns:
            Hex color code or None for default
        """
        return self.selected_color

