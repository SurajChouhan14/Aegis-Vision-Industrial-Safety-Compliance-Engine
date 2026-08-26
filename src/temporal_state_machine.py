"""
4-State Temporal Anti-Alarm-Fatigue State Machine.
Tracks worker violation states:
1. PENDING: Initial violation entry, 30s grace period (prevents nuisance false alarms on transient entry)
2. ALARMING: Active audible alarm triggered after 30s
3. REMINDING: Intermittent warning every 20s for 2 minutes
4. TIMED_OUT: Incident escalated to safety supervisor ledger
"""

from typing import Dict, Any, Optional


class TemporalAlertStateMachine:
    """
    Maintains worker state lifecycles to prevent alarm fatigue and log safety violations.
    Includes temporal debounce / exit hysteresis against single-frame detector jitter.
    """

    def __init__(
        self,
        initial_grace_sec: float = 30.0,
        alarm_duration_sec: float = 10.0,
        reminder_interval_sec: float = 20.0,
        escalation_timeout_sec: float = 120.0,
        debounce_frames: int = 2
    ):
        self.initial_grace_sec = initial_grace_sec
        self.alarm_duration_sec = alarm_duration_sec
        self.reminder_interval_sec = reminder_interval_sec
        self.escalation_timeout_sec = escalation_timeout_sec
        self.debounce_frames = debounce_frames
        self.worker_states: Dict[int, Dict[str, Any]] = {}

    def update_worker_state(self, track_id: int, is_in_violation: bool, current_timestamp: float) -> Dict[str, Any]:
        """
        Updates the 4-state lifecycle for a specific worker with debounce buffer.
        """
        if not is_in_violation:
            if track_id in self.worker_states:
                st = self.worker_states[track_id]
                st["safe_consecutive_frames"] = st.get("safe_consecutive_frames", 0) + 1
                if st["safe_consecutive_frames"] >= self.debounce_frames:
                    del self.worker_states[track_id]
                    return {"track_id": track_id, "state": "COMPLIANT", "action": "CLEARED"}
                else:
                    return {"track_id": track_id, "state": st["state"], "action": "DEBOUNCE_BUFFER"}
            return {"track_id": track_id, "state": "COMPLIANT", "action": "NONE"}

        if track_id not in self.worker_states:
            # First frame in violation -> Enter PENDING state
            self.worker_states[track_id] = {
                "state": "PENDING",
                "violation_start_time": current_timestamp,
                "alarm_start_time": None,
                "last_reminder_time": None,
                "safe_consecutive_frames": 0
            }
            return {"track_id": track_id, "state": "PENDING", "action": "GRACE_PERIOD_ACTIVE"}

        st = self.worker_states[track_id]
        st["safe_consecutive_frames"] = 0
        elapsed_since_start = current_timestamp - st["violation_start_time"]

        # Check for incident escalation timeout (>= 120s)
        if elapsed_since_start >= self.escalation_timeout_sec:
            st["state"] = "TIMED_OUT"
            return {"track_id": track_id, "state": "TIMED_OUT", "action": "ESCALATE_TO_SUPERVISOR_LEDGER"}

        # Transition 1: PENDING -> ALARMING
        if st["state"] == "PENDING":
            if elapsed_since_start >= self.initial_grace_sec:
                st["state"] = "ALARMING"
                st["alarm_start_time"] = current_timestamp
                return {"track_id": track_id, "state": "ALARMING", "action": "TRIGGER_AUDIBLE_ALARM"}
            return {"track_id": track_id, "state": "PENDING", "action": "GRACE_PERIOD_ACTIVE"}

        # Transition 2: ALARMING -> REMINDING
        if st["state"] == "ALARMING":
            if current_timestamp - st["alarm_start_time"] >= self.alarm_duration_sec:
                st["state"] = "REMINDING"
                st["last_reminder_time"] = current_timestamp
                return {"track_id": track_id, "state": "REMINDING", "action": "PERIODIC_WARNING"}
            return {"track_id": track_id, "state": "ALARMING", "action": "ALARM_ACTIVE"}

        # Transition 3: REMINDING -> Periodic reminder intervals
        if st["state"] == "REMINDING":
            if current_timestamp - st["last_reminder_time"] >= self.reminder_interval_sec:
                st["last_reminder_time"] = current_timestamp
                return {"track_id": track_id, "state": "REMINDING", "action": "PERIODIC_WARNING"}
            return {"track_id": track_id, "state": "REMINDING", "action": "MONITORING"}

        return {"track_id": track_id, "state": st["state"], "action": "NONE"}
