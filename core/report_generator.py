from typing import List, Dict, Tuple
from models.plan import StowagePlan
from models.ship import Ship
from datetime import datetime

class ASCIIReportGenerator:
    """Generates ASCII text reports for stowage plans"""
    
    @staticmethod
    def generate_report(plan: StowagePlan, ship: Ship) -> str:
        """
        Generate a visual ASCII report of the stowage plan.
        
        Args:
            plan: The stowage plan containing cargo assignments
            ship: The ship model containing tank layout
            
        Returns:
            str: The formatted ASCII report
        """
        lines = []
        
        # 1. Header
        lines.append("=" * 80)
        lines.append(f"GEMI YUKLEME RAPORU / STOWAGE PLAN REPORT".center(80))
        lines.append("=" * 80)
        lines.append(f"Gemi / Ship: {plan.ship_name}")
        lines.append(f"Plan: {plan.plan_name}")
        lines.append(f"Tarih / Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        if plan.notes:
            lines.append("-" * 80)
            lines.append(f"Notlar / Notes:\n{plan.notes}")
        lines.append("=" * 80)
        lines.append("")
        
        # 2. Tank Grid
        # Group tanks by row
        rows: Dict[int, Dict[str, any]] = {}
        
        for tank in ship.tanks:
            info = ship.get_tank_position_info(tank.id)
            if not info:
                continue
            
            row_num = info['row_number']
            if row_num not in rows:
                rows[row_num] = {'port': None, 'starboard': None, 'center': None} # Simplify to Port/Stbd generally
                
            # Naive assignment based on side. 
            # ship.py defines sides as 'port' and 'starboard' based on index parity.
            # Let's trust get_tank_position_info
            rows[row_num][info['side']] = tank

        # Sort rows
        sorted_row_nums = sorted(rows.keys())
        
        for row_num in sorted_row_nums:
            row_data = rows[row_num]
            lines.append(f"SIRALAMA {row_num} / ROW {row_num}")
            
            # Prepare cards
            p_card = ASCIIReportGenerator._create_tank_card(row_data.get('port'), plan)
            s_card = ASCIIReportGenerator._create_tank_card(row_data.get('starboard'), plan)
            
            # Merge cards side-by-side
            combined_card = ASCIIReportGenerator._merge_cards_side_by_side(p_card, s_card)
            lines.extend(combined_card)
            lines.append("") # Empty line between rows
            
        # 3. Summary
        lines.append("=" * 80)
        lines.append("YUK OZETI / CARGO SUMMARY".center(80))
        lines.append("-" * 80)
        
        cargo_totals = {}
        for tank_id, assignment in plan.assignments.items():
            c_id = assignment.cargo.unique_id
            if c_id not in cargo_totals:
                cargo_totals[c_id] = {
                    'cargo_obj': assignment.cargo,
                    'total_mt': 0.0,
                    'total_m3': 0.0,
                    'tanks': []
                }
            
            # quantity_loaded is already in M3 (volume)
            vol_m3 = assignment.quantity_loaded
            cargo_totals[c_id]['total_m3'] += vol_m3
            
            # Calculate mass: Mass = Volume * Density
            mass_mt = vol_m3 * assignment.cargo.density if assignment.cargo.density > 0 else 0
            cargo_totals[c_id]['total_mt'] += mass_mt
            
            # Get tank name
            tank = ship.get_tank_by_id(tank_id)
            tank_name = tank.name if tank else tank_id
            cargo_totals[c_id]['tanks'].append(tank_name)
        
        total_vol_m3 = 0.0
        total_mass_mt = 0.0
        
        for c_id, data in cargo_totals.items():
            cargo = data['cargo_obj']
            # Sort tanks natural sort might be nice but list is fine
            tanks_str = ",".join(sorted(data['tanks']))
            receivers_str = cargo.get_receiver_names()
            
            # Format: TYPE (RECEIVER) (TANKS)
            # KBZ (ALICI ADI) (HANGİ TANKLAR)
            row_label = f"{cargo.cargo_type} ({receivers_str}) ({tanks_str})"
            
            # Truncate label if it's too long for the layout, but let's give it more space
            # Layout: Label (left aligned) : Value (right) Unit
            # Max width 80. Val+Unit takes ~15 chars. Label has ~60 chars.
            if len(row_label) > 60:
                row_label = row_label[:57] + "..."
            
            # Format: Mass MT (Volume M3)
            # Use tracked values - integers only
            val_str = f"{data['total_mt']:.0f} MT ({data['total_m3']:.0f} M3)"
            lines.append(f"{row_label:<50} : {val_str:>25}")
            
            total_vol_m3 += data['total_m3']
            total_mass_mt += data['total_mt']
            
        lines.append("-" * 80)
        total_str = f"{total_mass_mt:.0f} MT ({total_vol_m3:.0f} M3)"
        lines.append(f"{'TOPLAM / TOTAL':<50} : {total_str:>25}")
        lines.append("=" * 80)
        
        return "\n".join(lines)

    @staticmethod
    def _create_tank_card(tank, plan: StowagePlan) -> List[str]:
        """Creates a list of strings representing a tank card"""
        width = 35
        if not tank:
            # Empty placeholder
            return [" " * width for _ in range(6)]
            
        assignment = plan.get_assignment(tank.id)
        
        border = "+" + "-" * (width - 2) + "+"
        empty_line = "|" + " " * (width - 2) + "|"
        
        lines = [border]
        
        # Tank Name
        tank_name = f"Tank: {tank.name}"
        lines.append(f"| {tank_name:<{width-4}} |")
        
        # Cargo Name & Receiver
        if assignment:
            cargo_name = assignment.cargo.cargo_type
            receiver_names = assignment.cargo.get_receiver_names()
            
            # Format: 'Diesel (Shell)'
            full_str = f"{cargo_name} ({receiver_names})"
            
            # Truncate if too long
            if len(full_str) > width - 4:
                full_str = full_str[:width-7] + "..."
            lines.append(f"| {full_str:<{width-4}} |")
            
            # Blank line to maintain height (replaces percentage bar)
            lines.append(f"| {'':<{width-4}} |")
            
        else:
            lines.append(f"| {'BOS / EMPTY':<{width-4}} |")
            lines.append(f"| {'':<{width-4}} |")
            
        # Capacity info always shown
        cap_str = f"Cap:  {tank.volume:.1f} m3"
        lines.append(f"| {cap_str:<{width-4}} |")
        
        lines.append(border)
        return lines

    @staticmethod
    def _merge_cards_side_by_side(left_card: List[str], right_card: List[str]) -> List[str]:
        """Merges two card line lists side by side with spacing"""
        gap = "   "
        max_lines = max(len(left_card), len(right_card))
        result = []
        
        for i in range(max_lines):
            l = left_card[i] if i < len(left_card) else " " * len(left_card[0])
            r = right_card[i] if i < len(right_card) else " " * len(right_card[0])
            result.append(f"{l}{gap}{r}")
            
        return result
