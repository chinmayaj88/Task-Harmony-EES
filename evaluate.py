import json
import os
import logging
from typing import Dict, Any, List, Optional

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("Evaluator")

class ShipmentEvaluator:
    """Evaluates the accuracy of extracted shipment data against ground truth."""
    
    def __init__(self, ground_truth_path: str, prediction_path: str):
        self.ground_truth_path = ground_truth_path
        self.prediction_path = prediction_path
        self.evaluated_fields = [
            "product_line", "origin_port_code", "origin_port_name",
            "destination_port_code", "destination_port_name", "incoterm",
            "cargo_weight_kg", "cargo_cbm", "is_dangerous"
        ]

    def _load_json(self, path: str) -> List[Dict[str, Any]]:
        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {path}")
        with open(path, "r", encoding='utf-8') as f:
            return json.load(f)

    @staticmethod
    def _normalize(val: Any) -> Any:
        """Normalizes strings for comparison."""
        if isinstance(val, str):
            val = val.strip().upper()
            return val if val not in ["", "NULL", "NONE", "N/A"] else None
        return val

    def _compare(self, field: str, gt: Any, pred: Any) -> bool:
        """Field-specific comparison logic."""
        gt_norm = self._normalize(gt)
        pred_norm = self._normalize(pred)

        if field in ["cargo_weight_kg", "cargo_cbm"]:
            if gt_norm is None and pred_norm is None: return True
            if gt_norm is None or pred_norm is None: return False
            return abs(float(gt_norm) - float(pred_norm)) < 0.01

        if field == "is_dangerous":
            return bool(gt_norm) == bool(pred_norm)

        return gt_norm == pred_norm

    def calculate_metrics(self):
        """Calculates and prints accuracy metrics."""
        try:
            gt_data = self._load_json(self.ground_truth_path)
            pred_data = self._load_json(self.prediction_path)
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            return

        gt_map = {item["id"]: item for item in gt_data}
        pred_map = {item["id"]: item for item in pred_data}
        
        field_accuracy = {field: 0 for field in self.evaluated_fields}
        total_emails = len(gt_map)
        correct_fields = 0
        total_fields = 0

        for email_id, gt_entry in gt_map.items():
            pred_entry = pred_map.get(email_id, {})
            
            for field in self.evaluated_fields:
                is_correct = self._compare(field, gt_entry.get(field), pred_entry.get(field))
                if is_correct:
                    field_accuracy[field] += 1
                    correct_fields += 1
                total_fields += 1

        print("\n" + "="*30)
        print("   ACCURACY CALCULATION")
        print("="*30)
        print(f"Total Emails Evaluated: {total_emails}")
        print("-" * 30)
        
        for field, count in field_accuracy.items():
            acc = (count / total_emails) * 100 if total_emails > 0 else 0
            print(f"{field:<22}: {acc:>6.1f}%")

        overall_acc = (correct_fields / total_fields) * 100 if total_fields > 0 else 0
        print("-" * 30)
        print(f"{'OVERALL ACCURACY':<22}: {overall_acc:>6.1f}%")
        print("="*30 + "\n")

if __name__ == "__main__":
    evaluator = ShipmentEvaluator("data/ground_truth.json", "output.json")
    evaluator.calculate_metrics()
