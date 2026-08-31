"""
Synthetic CCTV Scenario Stream & Danger Zone Benchmark Loader.
Generates multi-frame synthetic CCTV surveillance sequences (50 scripted keyframes over 122.5s) across factory zones with:
- Deterministic worker trajectories (Track IDs: 101 to 105)
- Ground-truth spatial bounding boxes for workers, hardhats/helmets, and high-visibility safety vests
- Realistic entries/exits into restricted heavy-machinery danger polygon
- Timestamp tracking over 122.5 seconds of operational surveillance
"""

import json
import os
from typing import List, Dict, Any, Tuple


class IndustrialSurveillanceLoader:
    """
    Manages synthetic multi-frame surveillance video streams and ground-truth worker safety benchmarks.
    """

    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        self.stream_path = os.path.join(self.data_dir, "industrial_surveillance_stream.json")

    def load_or_create_stream(self) -> Tuple[List[List[float]], List[Dict[str, Any]]]:
        """
        Loads or generates a synthetic 50-frame factory surveillance stream with diverse worker scenarios.
        """
        if os.path.exists(self.stream_path):
            try:
                with open(self.stream_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if len(data.get("frames", [])) >= 50:
                    return data["danger_zone"], data["frames"]
            except Exception:
                pass

        return self.generate_and_save_surveillance_stream()

    def generate_and_save_surveillance_stream(self) -> Tuple[List[List[float]], List[Dict[str, Any]]]:
        """
        Generates 50 synthetic surveillance keyframes over 122.5 seconds.
        Danger Zone: Restricted Heavy-Machinery Polygon [[100, 150], [500, 150], [500, 450], [100, 450]]

        Scripted Worker Scenarios:
        - Worker 101: Fully Compliant (Helmet + Vest). Enters danger zone at t=0s, stays inside throughout. State: COMPLIANT (0 alarms).
        - Worker 102: Missing Helmet (Has Vest). Enters danger zone at t=0s. Transitions: PENDING (t=0-30s) -> ALARMING (t=31-40s) -> REMINDING (t=41-90s) -> Exits zone at t=95s -> Cleared.
        - Worker 103: Safe Assembly Zone (No PPE). Operates strictly outside danger zone (X=20..80, Y=20..120). State: COMPLIANT (Zero false positives outside zone).
        - Worker 104: Complete Non-Compliance (No Helmet, No Vest). Enters danger zone at t=40s. Transitions: PENDING (t=40-70s) -> ALARMING (t=71-80s) -> REMINDING (t=81-122.5s).
        - Worker 105: Dynamic Gear Donning (Starts non-compliant, dons helmet at t=20s before 30s grace period expires). Transitions: PENDING -> COMPLIANT (Grace period prevents false alarm).
        """
        danger_zone_polygon = [[100.0, 150.0], [500.0, 150.0], [500.0, 450.0], [100.0, 450.0]]

        frames = []
        total_frames = 50
        time_step = 2.5  # 2.5 seconds per keyframe -> 0.0s to 122.5s

        for f_idx in range(total_frames):
            timestamp = round(f_idx * time_step, 1)
            frame_detections = []

            # -------------------------------------------------------------
            # Worker 101: Fully Compliant (Helmet + Vest, Inside Danger Zone)
            # -------------------------------------------------------------
            w101_x = 150.0 + (f_idx * 1.2)
            w101_y = 200.0 + (f_idx * 0.8)
            w101_bbox = [w101_x, w101_y, w101_x + 90.0, w101_y + 200.0]
            frame_detections.append({"track_id": 101, "class": "person", "bbox": w101_bbox})
            # Associated Helmet & Vest
            frame_detections.append({"track_id": None, "class": "helmet", "bbox": [w101_x + 25.0, w101_y, w101_x + 65.0, w101_y + 35.0]})
            frame_detections.append({"track_id": None, "class": "vest", "bbox": [w101_x + 10.0, w101_y + 40.0, w101_x + 80.0, w101_y + 130.0]})

            # -------------------------------------------------------------
            # Worker 102: Missing Helmet (Has Vest only, Inside Danger Zone until t=95s)
            # -------------------------------------------------------------
            if timestamp <= 95.0:
                w102_x = 320.0 + (f_idx * 0.5)
                w102_y = 220.0 + (f_idx * 0.6)
                w102_bbox = [w102_x, w102_y, w102_x + 90.0, w102_y + 200.0]
                frame_detections.append({"track_id": 102, "class": "person", "bbox": w102_bbox})
                # Vest only (NO helmet)
                frame_detections.append({"track_id": None, "class": "vest", "bbox": [w102_x + 10.0, w102_y + 40.0, w102_x + 80.0, w102_y + 130.0]})
            else:
                # Exits to safe zone (Y=490 > 450)
                w102_bbox = [350.0, 490.0, 440.0, 690.0]
                frame_detections.append({"track_id": 102, "class": "person", "bbox": w102_bbox})

            # -------------------------------------------------------------
            # Worker 103: Safe Assembly Zone (Strictly outside danger zone, No PPE)
            # -------------------------------------------------------------
            w103_x = 20.0 + (f_idx * 0.4)
            w103_y = 20.0 + (f_idx * 0.3)
            w103_bbox = [w103_x, w103_y, w103_x + 60.0, w103_y + 100.0]
            frame_detections.append({"track_id": 103, "class": "person", "bbox": w103_bbox})

            # -------------------------------------------------------------
            # Worker 104: Complete Non-Compliance (Enters zone at t=40s)
            # -------------------------------------------------------------
            if timestamp >= 40.0:
                w104_x = 220.0 + ((f_idx - 16) * 1.5)
                w104_y = 180.0 + ((f_idx - 16) * 1.0)
                w104_bbox = [w104_x, w104_y, w104_x + 85.0, w104_y + 190.0]
                frame_detections.append({"track_id": 104, "class": "person", "bbox": w104_bbox})

            # -------------------------------------------------------------
            # Worker 105: Dynamic Donning (Starts non-compliant, dons helmet at t=20s)
            # -------------------------------------------------------------
            w105_x = 400.0 - (f_idx * 0.8)
            w105_y = 250.0 + (f_idx * 0.4)
            w105_bbox = [w105_x, w105_y, w105_x + 85.0, w105_y + 190.0]
            frame_detections.append({"track_id": 105, "class": "person", "bbox": w105_bbox})
            frame_detections.append({"track_id": None, "class": "vest", "bbox": [w105_x + 10.0, w105_y + 35.0, w105_x + 75.0, w105_y + 120.0]})
            if timestamp >= 20.0:
                # Dons helmet at t=20s before 30s grace period expires!
                frame_detections.append({"track_id": None, "class": "helmet", "bbox": [w105_x + 20.0, w105_y, w105_x + 65.0, w105_y + 35.0]})

            frames.append({
                "frame_id": f_idx + 1,
                "timestamp_sec": timestamp,
                "detections": frame_detections
            })

        data = {"danger_zone": danger_zone_polygon, "frames": frames}
        with open(self.stream_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        return danger_zone_polygon, frames
