"""Dialog for selecting from multiple optimization solutions"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QTableWidget, QTableWidgetItem, QPushButton,
                             QHeaderView, QDialogButtonBox, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from typing import Optional, List, Tuple

from models.plan import StowagePlan
from models.ship import Ship


class PlanSelectionDialog(QDialog):
    """Dialog for selecting from multiple optimization solutions"""
    
    def __init__(self, parent=None, solutions: List[Tuple[StowagePlan, float, str]] = None):
        super().__init__(parent)
        self.solutions = solutions or []
        self.selected_plan: Optional[StowagePlan] = None
        self.selected_index = -1
        self.init_ui()
        self.load_solutions()
    
    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("Optimizasyon Çözümleri")
        self.setMinimumWidth(800)
        self.setMinimumHeight(500)
        
        layout = QVBoxLayout(self)
        
        # Info label
        info_label = QLabel(
            "Birden fazla optimizasyon çözümü bulundu. "
            "Skorlarına göre en iyiden kötüye sıralanmıştır:"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Solutions table
        self.solutions_table = QTableWidget()
        self.solutions_table.setColumnCount(5)
        self.solutions_table.setHorizontalHeaderLabels([
            "Sıra", "Strateji", "Skor", "Yüklenen (m³)", "Tamamlanma %"
        ])
        self.solutions_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.solutions_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.solutions_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.solutions_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.solutions_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.solutions_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.solutions_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.solutions_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.solutions_table.doubleClicked.connect(self.accept_selection)
        layout.addWidget(self.solutions_table)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept_selection)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def load_solutions(self):
        """Load solutions into table"""
        self.solutions_table.setRowCount(len(self.solutions))
        
        for row, (plan, score, strategy) in enumerate(self.solutions):
            # Rank
            self.solutions_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
            
            # Strategy
            self.solutions_table.setItem(row, 1, QTableWidgetItem(strategy))
            
            # Score
            score_item = QTableWidgetItem(f"{score:.2f}")
            # Color code: green for high scores, yellow for medium, red for low
            if score >= 80:
                score_item.setBackground(QColor("#96CEB4"))  # Light green
            elif score >= 60:
                score_item.setBackground(QColor("#FFEAA7"))  # Light yellow
            else:
                score_item.setBackground(QColor("#D3D3D3"))  # Light gray
            self.solutions_table.setItem(row, 2, score_item)
            
            # Total loaded
            total_loaded = plan.get_total_loaded()
            self.solutions_table.setItem(row, 3, QTableWidgetItem(f"{total_loaded:.2f}"))
            
            # Completion percentage
            total_requested = sum(cargo.quantity for cargo in plan.cargo_requests)
            completion = (total_loaded / total_requested * 100) if total_requested > 0 else 0
            self.solutions_table.setItem(row, 4, QTableWidgetItem(f"{completion:.1f}%"))
            
            # Store plan in item data
            self.solutions_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, row)
        
        # Select first row (best solution) by default
        if len(self.solutions) > 0:
            self.solutions_table.selectRow(0)
    
    def accept_selection(self):
        """Accept the selected solution"""
        current_row = self.solutions_table.currentRow()
        if current_row < 0:
            # No selection, use first (best) solution
            if len(self.solutions) > 0:
                self.selected_plan = self.solutions[0][0]
                self.selected_index = 0
                self.accept()
            else:
                QMessageBox.warning(self, "Uyarı", "Seçilecek çözüm bulunamadı.")
        else:
            self.selected_plan = self.solutions[current_row][0]
            self.selected_index = current_row
            self.accept()

