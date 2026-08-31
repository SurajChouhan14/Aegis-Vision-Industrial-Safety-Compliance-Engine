"""
Spatial Bounding Box Association & Danger Zone Polygon Evaluation Engine.
Solves the global-frame false association bug via Anatomical Spatial Intersection over Gear Area (IoGA)
with horizontal and vertical body region gating and 1-to-1 greedy association.
"""

from typing import List, Tuple, Dict, Any
import numpy as np


class SpatialComplianceEngine:
    """
    Computes spatial polygon containment and anatomical bounding box gear association.
    """

    @staticmethod
    def is_point_in_polygon(point: Tuple[float, float], polygon: List[List[float]]) -> bool:
        """
        Ray-casting algorithm to determine if worker bottom-center coordinate is inside restricted zone.
        Shoots a ray horizontally to the right and counts polygon edge intersections (Jordan Curve Theorem).
        """
        x, y = point
        n = len(polygon)
        inside = False

        p1x, p1y = polygon[0]
        for i in range(n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y

        return inside

    @staticmethod
    def compute_iou(boxA: List[float], boxB: List[float]) -> float:
        """
        Computes standard Intersection over Union (IoU) between two bounding boxes [x1, y1, x2, y2].
        """
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])

        interArea = max(0.0, xB - xA) * max(0.0, yB - yA)
        boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
        boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])

        iou = interArea / float(boxAArea + boxBArea - interArea + 1e-6)
        return float(iou)

    @classmethod
    def is_gear_associated_with_person(
        cls,
        person_bbox: List[float],
        gear_bbox: List[float],
        gear_type: str = "helmet",
        min_overlap: float = 0.60
    ) -> bool:
        """
        Determines if a safety gear piece (helmet/vest) is anatomically worn by a specific person.
        Calculates Intersection over Gear Area (IoGA) and verifies 2D anatomical body regions:
        - Helmet: Must reside in upper 40% vertical head zone and 20%-80% horizontal center.
        - Vest: Must reside in upper-mid torso zone (10% to 80% vertical, 15%-85% horizontal).
        """
        px1, py1, px2, py2 = person_bbox
        gx1, gy1, gx2, gy2 = gear_bbox
        p_height = py2 - py1
        p_width = px2 - px1

        gear_center_y = (gy1 + gy2) / 2.0
        gear_center_x = (gx1 + gx2) / 2.0
        relative_y = (gear_center_y - py1) / float(p_height + 1e-6)
        relative_x = (gear_center_x - px1) / float(p_width + 1e-6)

        # 1. 2D Anatomical Boundary Check
        if gear_type in ["helmet", "hardhat"]:
            if relative_y > 0.40 or relative_x < 0.20 or relative_x > 0.80:
                return False
        elif gear_type in ["vest", "safety_vest"]:
            if relative_y < 0.10 or relative_y > 0.80 or relative_x < 0.15 or relative_x > 0.85:
                return False

        # 2. Geometric Intersection over Gear Area (IoGA)
        inter_x1 = max(px1, gx1)
        inter_y1 = max(py1, gy1)
        inter_x2 = min(px2, gx2)
        inter_y2 = min(py2, gy2)

        if inter_x1 >= inter_x2 or inter_y1 >= inter_y2:
            return False

        inter_area = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
        gear_area = (gx2 - gx1) * (gy2 - gy1)

        overlap_fraction = inter_area / float(gear_area + 1e-6)
        return overlap_fraction >= min_overlap

    @classmethod
    def associate_gears_to_persons(cls, persons: List[Dict[str, Any]], gears: List[Dict[str, Any]]) -> Dict[int, Dict[str, bool]]:
        """
        Performs 1-to-1 greedy anatomical association of detected gears to persons.
        """
        person_gear_map = {p["track_id"]: {"has_helmet": False, "has_vest": False} for p in persons}
        
        helmets = [g for g in gears if g["class"] in ["helmet", "hardhat"]]
        vests = [g for g in gears if g["class"] in ["vest", "safety_vest"]]

        for h in helmets:
            best_person = None
            best_score = 0.0
            for p in persons:
                if cls.is_gear_associated_with_person(p["bbox"], h["bbox"], gear_type="helmet"):
                    px1, py1, px2, py2 = p["bbox"]
                    gx1, gy1, gx2, gy2 = h["bbox"]
                    inter_area = max(0.0, min(px2, gx2) - max(px1, gx1)) * max(0.0, min(py2, gy2) - max(py1, gy1))
                    gear_area = (gx2 - gx1) * (gy2 - gy1)
                    score = inter_area / float(gear_area + 1e-6)
                    if score > best_score:
                        best_score = score
                        best_person = p["track_id"]
            if best_person is not None:
                person_gear_map[best_person]["has_helmet"] = True

        for v in vests:
            best_person = None
            best_score = 0.0
            for p in persons:
                if cls.is_gear_associated_with_person(p["bbox"], v["bbox"], gear_type="vest"):
                    px1, py1, px2, py2 = p["bbox"]
                    gx1, gy1, gx2, gy2 = v["bbox"]
                    inter_area = max(0.0, min(px2, gx2) - max(px1, gx1)) * max(0.0, min(py2, gy2) - max(py1, gy1))
                    gear_area = (gx2 - gx1) * (gy2 - gy1)
                    score = inter_area / float(gear_area + 1e-6)
                    if score > best_score:
                        best_score = score
                        best_person = p["track_id"]
            if best_person is not None:
                person_gear_map[best_person]["has_vest"] = True

        return person_gear_map
