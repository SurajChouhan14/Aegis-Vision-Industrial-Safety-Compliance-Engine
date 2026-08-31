"""
Automated Unit Test Suite for Aegis-Vision Industrial Safety Engine.
Verifies Ray-Casting Polygon Containment, Spatial IoGA Gear Mapping, 4-State Temporal Transitions, TIMED_OUT Escalation, and Mid-Grace Donning.
"""

import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.spatial_association_engine import SpatialComplianceEngine
from src.temporal_state_machine import TemporalAlertStateMachine
from src.data_loader import IndustrialSurveillanceLoader


class TestIndustrialSafetyEngine(unittest.TestCase):
    def setUp(self):
        self.spatial = SpatialComplianceEngine()
        self.state_machine = TemporalAlertStateMachine(
            initial_grace_sec=30.0,
            alarm_duration_sec=10.0,
            reminder_interval_sec=20.0,
            escalation_timeout_sec=120.0,
            debounce_frames=2
        )
        self.danger_polygon = [[100.0, 150.0], [500.0, 150.0], [500.0, 450.0], [100.0, 450.0]]

    def test_1_ray_casting_polygon_containment(self):
        """Verify inside, outside, and boundary coordinates."""
        inside_point = (300.0, 300.0)
        outside_point = (50.0, 50.0)
        far_outside_point = (600.0, 600.0)

        self.assertTrue(self.spatial.is_point_in_polygon(inside_point, self.danger_polygon))
        self.assertFalse(self.spatial.is_point_in_polygon(outside_point, self.danger_polygon))
        self.assertFalse(self.spatial.is_point_in_polygon(far_outside_point, self.danger_polygon))

    def test_2_anatomical_gear_association(self):
        """Verify helmet on head is associated while helmet at feet is rejected."""
        person_bbox = [100.0, 100.0, 200.0, 300.0]  # Width=100, Height=200
        helmet_on_head = [130.0, 100.0, 170.0, 140.0]  # Top 20%
        helmet_at_feet = [130.0, 260.0, 170.0, 300.0]  # Bottom 20%

        # True helmet on head
        self.assertTrue(self.spatial.is_gear_associated_with_person(person_bbox, helmet_on_head, gear_type="helmet"))
        # False helmet at feet (dropped on ground or held in hand)
        self.assertFalse(self.spatial.is_gear_associated_with_person(person_bbox, helmet_at_feet, gear_type="helmet"))

    def test_3_vest_torso_association(self):
        """Verify high-vis vest on torso is associated."""
        person_bbox = [100.0, 100.0, 200.0, 300.0]
        vest_on_torso = [110.0, 140.0, 190.0, 240.0]

        self.assertTrue(self.spatial.is_gear_associated_with_person(person_bbox, vest_on_torso, gear_type="vest"))

    def test_4_temporal_state_machine_transitions(self):
        """Verify 4-state lifecycle: PENDING (t=0) -> ALARMING (t=31s) -> REMINDING (t=45s) -> COMPLIANT (exit)."""
        track_id = 999

        # 1. First violation at t=0s -> PENDING
        res1 = self.state_machine.update_worker_state(track_id, is_in_violation=True, current_timestamp=0.0)
        self.assertEqual(res1["state"], "PENDING")
        self.assertEqual(res1["action"], "GRACE_PERIOD_ACTIVE")

        # 2. At t=25s (<30s) -> Still PENDING
        res2 = self.state_machine.update_worker_state(track_id, is_in_violation=True, current_timestamp=25.0)
        self.assertEqual(res2["state"], "PENDING")

        # 3. At t=31s (>=30s) -> Transitions to ALARMING
        res3 = self.state_machine.update_worker_state(track_id, is_in_violation=True, current_timestamp=31.0)
        self.assertEqual(res3["state"], "ALARMING")
        self.assertEqual(res3["action"], "TRIGGER_AUDIBLE_ALARM")

        # 4. At t=45s (>= 31 + 10s) -> Transitions to REMINDING
        res4 = self.state_machine.update_worker_state(track_id, is_in_violation=True, current_timestamp=45.0)
        self.assertEqual(res4["state"], "REMINDING")

        # 5. Worker exits violation: 1st safe frame -> DEBOUNCE_BUFFER
        res5 = self.state_machine.update_worker_state(track_id, is_in_violation=False, current_timestamp=50.0)
        self.assertEqual(res5["action"], "DEBOUNCE_BUFFER")

        # 6. 2nd consecutive safe frame -> CLEARED to COMPLIANT
        res6 = self.state_machine.update_worker_state(track_id, is_in_violation=False, current_timestamp=52.5)
        self.assertEqual(res6["state"], "COMPLIANT")
        self.assertEqual(res6["action"], "CLEARED")

    def test_5_timed_out_escalation_lifecycle(self):
        """Verify continuous violation >= 120s triggers TIMED_OUT escalation state."""
        fsm = TemporalAlertStateMachine(escalation_timeout_sec=120.0)
        track_id = 888

        # Enter violation at t=0
        fsm.update_worker_state(track_id, is_in_violation=True, current_timestamp=0.0)
        # Advance to t=125s (>= 120s)
        res = fsm.update_worker_state(track_id, is_in_violation=True, current_timestamp=125.0)
        self.assertEqual(res["state"], "TIMED_OUT")
        self.assertEqual(res["action"], "ESCALATE_TO_SUPERVISOR_LEDGER")

    def test_6_dynamic_mid_grace_donning(self):
        """Verify Worker 105 dynamic gear donning at t=20s clears to COMPLIANT with zero alarms."""
        fsm = TemporalAlertStateMachine(initial_grace_sec=30.0, debounce_frames=2)
        track_id = 105

        # Starts non-compliant at t=0s -> PENDING
        res1 = fsm.update_worker_state(track_id, is_in_violation=True, current_timestamp=0.0)
        self.assertEqual(res1["state"], "PENDING")

        # Worker dons helmet at t=20s (< 30s grace) -> is_in_violation becomes False
        fsm.update_worker_state(track_id, is_in_violation=False, current_timestamp=22.5)
        res_cleared = fsm.update_worker_state(track_id, is_in_violation=False, current_timestamp=25.0)
        self.assertEqual(res_cleared["state"], "COMPLIANT")
        self.assertEqual(res_cleared["action"], "CLEARED")


if __name__ == '__main__':
    unittest.main()
