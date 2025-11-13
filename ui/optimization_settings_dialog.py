"""Dialog for optimization algorithm settings"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QDoubleSpinBox, QSpinBox, QPushButton,
                             QGroupBox, QDialogButtonBox, QMessageBox, QCheckBox, QComboBox)
from PyQt6.QtCore import Qt
from typing import Dict


class OptimizationSettingsDialog(QDialog):
    """Dialog for configuring optimization algorithm parameters"""
    
    def __init__(self, parent=None, settings: Dict = None):
        super().__init__(parent)
        self.settings = settings or {}
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("Optimizasyon Ayarları")
        self.setMinimumWidth(600)
        self.setMinimumHeight(700)
        
        layout = QVBoxLayout(self)
        
        # Algorithm Selection
        algo_group = QGroupBox("Optimizasyon Algoritması")
        algo_layout = QVBoxLayout()
        
        algo_label = QLabel("Kullanılacak optimizasyon algoritmasını seçin:")
        algo_layout.addWidget(algo_label)
        
        self.algo_combo = QComboBox()
        # Add Genetic Algorithm first (default, index 0)
        self.algo_combo.addItem("Genetik Algoritma (GA)", "genetic")
        # Add Advanced Algorithm second (index 1)
        self.algo_combo.addItem("Gelişmiş Algoritma (FAZ)", "advanced")
        algo_layout.addWidget(self.algo_combo)
        
        algo_group.setLayout(algo_layout)
        layout.addWidget(algo_group)
        
        # Tank Minimum Yükleme
        min_util_group = QGroupBox("Tank Minimum Yükleme")
        min_util_layout = QVBoxLayout()
        
        min_util_label = QLabel("Tanklar en az yüzde kaç dolu olmalı? (0-100%)")
        min_util_layout.addWidget(min_util_label)
        
        self.min_utilization_spin = QDoubleSpinBox()
        self.min_utilization_spin.setMinimum(0.0)
        self.min_utilization_spin.setMaximum(100.0)
        self.min_utilization_spin.setSuffix("%")
        self.min_utilization_spin.setDecimals(0)
        self.min_utilization_spin.setSingleStep(5.0)
        min_util_layout.addWidget(self.min_utilization_spin)
        
        min_util_group.setLayout(min_util_layout)
        layout.addWidget(min_util_group)
        
        # Genetic Algorithm Parameters
        ga_group = QGroupBox("Genetik Algoritma Parametreleri")
        ga_layout = QVBoxLayout()
        
        # Population Size
        pop_size_layout = QHBoxLayout()
        pop_size_layout.addWidget(QLabel("Popülasyon Boyutu:"))
        self.ga_population_size_spin = QSpinBox()
        self.ga_population_size_spin.setMinimum(10)
        self.ga_population_size_spin.setMaximum(1000)
        self.ga_population_size_spin.setSingleStep(10)
        pop_size_layout.addWidget(self.ga_population_size_spin)
        pop_size_layout.addStretch()
        ga_layout.addLayout(pop_size_layout)
        
        # Max Generations
        max_gen_layout = QHBoxLayout()
        max_gen_layout.addWidget(QLabel("Maksimum Nesil Sayısı:"))
        self.ga_max_generations_spin = QSpinBox()
        self.ga_max_generations_spin.setMinimum(50)
        self.ga_max_generations_spin.setMaximum(5000)
        self.ga_max_generations_spin.setSingleStep(50)
        max_gen_layout.addWidget(self.ga_max_generations_spin)
        max_gen_layout.addStretch()
        ga_layout.addLayout(max_gen_layout)
        
        # Crossover Rate
        crossover_layout = QHBoxLayout()
        crossover_layout.addWidget(QLabel("Çaprazlama Oranı:"))
        self.ga_crossover_rate_spin = QDoubleSpinBox()
        self.ga_crossover_rate_spin.setMinimum(0.0)
        self.ga_crossover_rate_spin.setMaximum(1.0)
        self.ga_crossover_rate_spin.setDecimals(2)
        self.ga_crossover_rate_spin.setSingleStep(0.05)
        crossover_layout.addWidget(self.ga_crossover_rate_spin)
        crossover_layout.addStretch()
        ga_layout.addLayout(crossover_layout)
        
        # Mutation Rate
        mutation_layout = QHBoxLayout()
        mutation_layout.addWidget(QLabel("Mutasyon Oranı:"))
        self.ga_mutation_rate_spin = QDoubleSpinBox()
        self.ga_mutation_rate_spin.setMinimum(0.0)
        self.ga_mutation_rate_spin.setMaximum(1.0)
        self.ga_mutation_rate_spin.setDecimals(2)
        self.ga_mutation_rate_spin.setSingleStep(0.01)
        mutation_layout.addWidget(self.ga_mutation_rate_spin)
        mutation_layout.addStretch()
        ga_layout.addLayout(mutation_layout)
        
        # Tournament Size
        tournament_layout = QHBoxLayout()
        tournament_layout.addWidget(QLabel("Turnuva Boyutu:"))
        self.ga_tournament_size_spin = QSpinBox()
        self.ga_tournament_size_spin.setMinimum(2)
        self.ga_tournament_size_spin.setMaximum(10)
        self.ga_tournament_size_spin.setSingleStep(1)
        tournament_layout.addWidget(self.ga_tournament_size_spin)
        tournament_layout.addStretch()
        ga_layout.addLayout(tournament_layout)
        
        # Use Elitism
        elitism_layout = QHBoxLayout()
        self.ga_use_elitism_check = QCheckBox("Elitizm Kullan")
        elitism_layout.addWidget(self.ga_use_elitism_check)
        elitism_layout.addStretch()
        ga_layout.addLayout(elitism_layout)
        
        # Elitism Count
        elitism_count_layout = QHBoxLayout()
        elitism_count_layout.addWidget(QLabel("Elitizm Sayısı:"))
        self.ga_elitism_count_spin = QSpinBox()
        self.ga_elitism_count_spin.setMinimum(1)
        self.ga_elitism_count_spin.setMaximum(50)
        self.ga_elitism_count_spin.setSingleStep(1)
        elitism_count_layout.addWidget(self.ga_elitism_count_spin)
        elitism_count_layout.addStretch()
        ga_layout.addLayout(elitism_count_layout)
        
        # Symmetry Penalty Coefficient
        symmetry_penalty_layout = QHBoxLayout()
        symmetry_penalty_layout.addWidget(QLabel("Simetri Cezası Katsayısı:"))
        self.ga_symmetry_penalty_spin = QDoubleSpinBox()
        self.ga_symmetry_penalty_spin.setMinimum(0.0)
        self.ga_symmetry_penalty_spin.setMaximum(10000.0)
        self.ga_symmetry_penalty_spin.setDecimals(1)
        self.ga_symmetry_penalty_spin.setSingleStep(100.0)
        symmetry_penalty_layout.addWidget(self.ga_symmetry_penalty_spin)
        symmetry_penalty_layout.addStretch()
        ga_layout.addLayout(symmetry_penalty_layout)
        
        # Trim Penalty Coefficient
        trim_penalty_layout = QHBoxLayout()
        trim_penalty_layout.addWidget(QLabel("Trim Cezası Katsayısı:"))
        self.ga_trim_penalty_spin = QDoubleSpinBox()
        self.ga_trim_penalty_spin.setMinimum(0.0)
        self.ga_trim_penalty_spin.setMaximum(10000.0)
        self.ga_trim_penalty_spin.setDecimals(1)
        self.ga_trim_penalty_spin.setSingleStep(100.0)
        trim_penalty_layout.addWidget(self.ga_trim_penalty_spin)
        trim_penalty_layout.addStretch()
        ga_layout.addLayout(trim_penalty_layout)
        
        # Operational Penalty Coefficient
        operational_penalty_layout = QHBoxLayout()
        operational_penalty_layout.addWidget(QLabel("Operasyonel Cezası Katsayısı:"))
        self.ga_operational_penalty_spin = QDoubleSpinBox()
        self.ga_operational_penalty_spin.setMinimum(0.0)
        self.ga_operational_penalty_spin.setMaximum(10000.0)
        self.ga_operational_penalty_spin.setDecimals(1)
        self.ga_operational_penalty_spin.setSingleStep(10.0)
        operational_penalty_layout.addWidget(self.ga_operational_penalty_spin)
        operational_penalty_layout.addStretch()
        ga_layout.addLayout(operational_penalty_layout)
        
        # Receiver Tolerance
        receiver_tolerance_layout = QHBoxLayout()
        receiver_tolerance_layout.addWidget(QLabel("Alıcı Yük Bütünlüğü Toleransı:"))
        self.ga_receiver_tolerance_spin = QDoubleSpinBox()
        self.ga_receiver_tolerance_spin.setMinimum(1.0)  # %1 minimum
        self.ga_receiver_tolerance_spin.setMaximum(20.0)  # %20 maximum
        self.ga_receiver_tolerance_spin.setSuffix("%")
        self.ga_receiver_tolerance_spin.setDecimals(2)
        self.ga_receiver_tolerance_spin.setSingleStep(0.1)
        receiver_tolerance_layout.addWidget(self.ga_receiver_tolerance_spin)
        receiver_tolerance_layout.addStretch()
        ga_layout.addLayout(receiver_tolerance_layout)
        
        # Convergence Threshold
        convergence_threshold_layout = QHBoxLayout()
        convergence_threshold_layout.addWidget(QLabel("Yakınsama Eşiği:"))
        self.ga_convergence_threshold_spin = QDoubleSpinBox()
        self.ga_convergence_threshold_spin.setMinimum(0.0)
        self.ga_convergence_threshold_spin.setMaximum(1.0)
        self.ga_convergence_threshold_spin.setDecimals(4)
        self.ga_convergence_threshold_spin.setSingleStep(0.0001)
        convergence_threshold_layout.addWidget(self.ga_convergence_threshold_spin)
        convergence_threshold_layout.addStretch()
        ga_layout.addLayout(convergence_threshold_layout)
        
        # Convergence Generations
        convergence_gen_layout = QHBoxLayout()
        convergence_gen_layout.addWidget(QLabel("Yakınsama Nesil Sayısı:"))
        self.ga_convergence_generations_spin = QSpinBox()
        self.ga_convergence_generations_spin.setMinimum(10)
        self.ga_convergence_generations_spin.setMaximum(200)
        self.ga_convergence_generations_spin.setSingleStep(5)
        convergence_gen_layout.addWidget(self.ga_convergence_generations_spin)
        convergence_gen_layout.addStretch()
        ga_layout.addLayout(convergence_gen_layout)
        
        ga_group.setLayout(ga_layout)
        layout.addWidget(ga_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        reset_btn = QPushButton("Varsayılanlara Dön")
        reset_btn.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(reset_btn)
        
        button_layout.addStretch()
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Kaydet")
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        button_layout.addWidget(buttons)
        
        layout.addLayout(button_layout)
    
    def load_settings(self):
        """Load settings into UI"""
        # Algorithm selection
        current_algo = self.settings.get('optimization_algorithm', 'genetic')
        if current_algo == 'advanced':
            self.algo_combo.setCurrentIndex(1)
        else:
            self.algo_combo.setCurrentIndex(0)  # Default: Genetic Algorithm
        
        min_util = self.settings.get('min_utilization', 0.65) * 100
        self.min_utilization_spin.setValue(min_util)
        
        # GA parameters
        self.ga_population_size_spin.setValue(self.settings.get('ga_population_size', 500))
        self.ga_max_generations_spin.setValue(self.settings.get('ga_max_generations', 2000))
        self.ga_crossover_rate_spin.setValue(self.settings.get('ga_crossover_rate', 0.90))
        self.ga_mutation_rate_spin.setValue(self.settings.get('ga_mutation_rate', 0.11))
        self.ga_tournament_size_spin.setValue(self.settings.get('ga_tournament_size', 3))
        self.ga_use_elitism_check.setChecked(self.settings.get('ga_use_elitism', True))
        self.ga_elitism_count_spin.setValue(self.settings.get('ga_elitism_count', 5))
        self.ga_symmetry_penalty_spin.setValue(self.settings.get('ga_symmetry_penalty_coef', 3000.0))
        self.ga_trim_penalty_spin.setValue(self.settings.get('ga_trim_penalty_coef', 1500.0))
        self.ga_operational_penalty_spin.setValue(self.settings.get('ga_operational_penalty_coef', 100.0))
        self.ga_receiver_tolerance_spin.setValue(self.settings.get('ga_receiver_tolerance', 0.03) * 100)
        self.ga_convergence_threshold_spin.setValue(self.settings.get('ga_convergence_threshold', 0.0001))
        self.ga_convergence_generations_spin.setValue(self.settings.get('ga_convergence_generations', 60))
    
    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        # Algorithm selection - default to Genetic Algorithm
        self.algo_combo.setCurrentIndex(0)
        
        self.min_utilization_spin.setValue(65.0)
        
        # GA defaults
        self.ga_population_size_spin.setValue(500)
        self.ga_max_generations_spin.setValue(2000)
        self.ga_crossover_rate_spin.setValue(0.90)
        self.ga_mutation_rate_spin.setValue(0.11)
        self.ga_tournament_size_spin.setValue(3)
        self.ga_use_elitism_check.setChecked(True)
        self.ga_elitism_count_spin.setValue(5)
        self.ga_symmetry_penalty_spin.setValue(3000.0)
        self.ga_trim_penalty_spin.setValue(1500.0)
        self.ga_operational_penalty_spin.setValue(100.0)
        self.ga_receiver_tolerance_spin.setValue(3.0)
        self.ga_convergence_threshold_spin.setValue(0.0001)
        self.ga_convergence_generations_spin.setValue(60)
    
    def validate_and_accept(self):
        """Validate settings and accept dialog"""
        self.accept()
    
    def get_settings(self) -> Dict:
        """Get settings from UI"""
        return {
            'optimization_algorithm': self.algo_combo.currentData(),
            'min_utilization': self.min_utilization_spin.value() / 100.0,
            # GA parameters
            'ga_population_size': self.ga_population_size_spin.value(),
            'ga_max_generations': self.ga_max_generations_spin.value(),
            'ga_crossover_rate': self.ga_crossover_rate_spin.value(),
            'ga_mutation_rate': self.ga_mutation_rate_spin.value(),
            'ga_tournament_size': self.ga_tournament_size_spin.value(),
            'ga_use_elitism': self.ga_use_elitism_check.isChecked(),
            'ga_elitism_count': self.ga_elitism_count_spin.value(),
            'ga_symmetry_penalty_coef': self.ga_symmetry_penalty_spin.value(),
            'ga_trim_penalty_coef': self.ga_trim_penalty_spin.value(),
            'ga_operational_penalty_coef': self.ga_operational_penalty_spin.value(),
            'ga_receiver_tolerance': self.ga_receiver_tolerance_spin.value() / 100.0,
            'ga_convergence_threshold': self.ga_convergence_threshold_spin.value(),
            'ga_convergence_generations': self.ga_convergence_generations_spin.value()
        }

