"""Data structures for suggested tank information"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SuggestedTankInfo:
    """Information about a suggested tank for cargo placement"""
    tank_id: str
    fit_score: float  # 0-100, how well it fits
    rank: int  # 1st best, 2nd best, etc.
    utilization: float  # Percentage of tank that would be filled (0-100)
    fit_reason: str  # "Exact fit", "Near fit ±2%", "Multi-tank solution", etc.
    quantity_to_load: float  # Amount that would be loaded in this tank
    deviation_percent: float  # Deviation from ideal fit (0-100)
    
    def get_fit_quality(self) -> str:
        """Get fit quality category"""
        if self.fit_score >= 95:
            return "excellent"
        elif self.fit_score >= 80:
            return "good"
        elif self.fit_score >= 65:
            return "acceptable"
        else:
            return "poor"
    
    def get_border_color(self) -> str:
        """Get border color based on fit quality"""
        quality = self.get_fit_quality()
        colors = {
            "excellent": "#4CAF50",  # Green
            "good": "#FFE66D",  # Yellow
            "acceptable": "#FF9800",  # Orange
            "poor": "#FF6B6B"  # Red
        }
        return colors.get(quality, "#FFE66D")

