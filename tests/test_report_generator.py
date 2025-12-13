from unittest import TestCase
from unittest.mock import MagicMock
from models.ship import Ship, Tank
from models.plan import StowagePlan, TankAssignment
from models.cargo import Cargo
from core.report_generator import ASCIIReportGenerator

class TestASCIIReportGenerator(TestCase):
    def setUp(self):
        # Create a mock ship
        self.ship = MagicMock(spec=Ship)
        self.ship.name = "Test Ship"
        self.ship.tanks = []
        
        # Create some tanks
        self.tank1 = Tank(id="t1", name="1P", volume=1000)
        self.tank2 = Tank(id="t2", name="1S", volume=1000)
        self.ship.tanks = [self.tank1, self.tank2]
        
        # Mock position info
        def get_pos_info(tank_id):
            if tank_id == "t1":
                return {'row_number': 1, 'side': 'port', 'position': 'bow'}
            if tank_id == "t2":
                return {'row_number': 1, 'side': 'starboard', 'position': 'bow'}
            return None
        self.ship.get_tank_position_info.side_effect = get_pos_info
        
        # Mock get_tank_by_id
        def get_tank(tid):
            if tid == "t1": return self.tank1
            if tid == "t2": return self.tank2
            return None
        self.ship.get_tank_by_id.side_effect = get_tank
        
        # Create a mock plan
        self.plan = MagicMock(spec=StowagePlan)
        self.plan.ship_name = "Test Ship"
        self.plan.plan_name = "Test Plan"
        self.plan.notes = "Test Notes"
        self.plan.assignments = {}
        self.plan.get_total_loaded.return_value = 500.0

        # Create Cargo
        self.cargo = Cargo(cargo_type="Diesel", quantity=1000, unique_id="c1", receivers=[], ton=1000, density=0.85)
        # self.cargo.cargo_name = "Diesel Fuel" - Removed because cargo_name attribute does not exist

        # Mock assignments
        assignment = TankAssignment(tank_id="t1", cargo=self.cargo, quantity_loaded=500)
        self.plan.get_assignment.side_effect = lambda tid: assignment if tid == "t1" else None
        
        # Mock assignments dict for summary
        self.plan.assignments = {"t1": assignment}

    def test_generate_report(self):
        report = ASCIIReportGenerator.generate_report(self.plan, self.ship)
        
        # Check Header
        self.assertIn("GEMI YUKLEME RAPORU", report)
        self.assertIn("Gemi / Ship: Test Ship", report)
        
        
        # Check Tank 1 (Assigned)
        self.assertIn("Tank: 1P", report)
        self.assertIn("Diesel (Genel)", report) # "Genel" because mock cargo receivers are empty
        
        # Check Tank 2 (Empty)
        self.assertIn("Tank: 1S", report)
        self.assertIn("BOS / EMPTY", report)
        
        # Check Summary
        self.assertIn("YUK OZETI", report)
        # Expected format: Diesel (Genel) (1P)
        self.assertIn("Diesel (Genel) (1P)", report)
        # 588.235... -> 588.235 m3 (3 decimal places in summary)
        # quantity_loaded = 500 M3, density = 0.85
        # Mass = 500 * 0.85 = 425 MT
        self.assertIn("425 MT (500 M3)", report)
        # Check Total
        self.assertIn("TOPLAM / TOTAL", report)
        self.assertIn("425 MT (500 M3)", report)
