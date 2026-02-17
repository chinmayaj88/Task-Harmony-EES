import json
import os
import logging
from typing import Dict, Any, List, Optional

# Professional Evaluation Engine
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s [%(levelname)s] Evaluator: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("AccuracyBenchmark")

class ShipmentEvaluator:
    """
    Core engine for auditing extraction performance. 
    Compares LLM predictions against audited ground truth fields.
    """
    
    def __init__(self, ground_truth_path: str, prediction_path: str):
        self.ground_truth_path = ground_truth_path
        self.prediction_path = prediction_path
        self.evaluated_fields = [
            "product_line", "origin_port_code", "origin_port_name",
            "destination_port_code", "destination_port_name", "incoterm",
            "cargo_weight_kg", "cargo_cbm", "is_dangerous"
        ]

    def _load_json(self, path: str) -> List[Dict[str, Any]]:
        """Safe JSON loading with validation."""
        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing Data Source: {path}")
        try:
            with open(path, "r", encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Data Corruption: '{path}' is not valid JSON. Detail: {e}")

    @staticmethod
    def _normalize(val: Any) -> Any:
        # Standardize strings to handle case-sensitivity and whitespace discrepancies
        if isinstance(val, str):
            val = val.strip().upper()
            return val if val not in ["", "NULL", "NONE", "N/A"] else None
        return val

    def _compare(self, field: str, gt: Any, pred: Any) -> bool:
        """
        Deep comparison of fields with specialized logic for numbers and booleans.
        """
        gt_norm = self._normalize(gt)
        pred_norm = self._normalize(pred)

        # Precision handling for floating point metrics
        if field in ["cargo_weight_kg", "cargo_cbm"]:
            if gt_norm is None and pred_norm is None: return True
            if gt_norm is None or pred_norm is None: return False
            try:
                # We allow for a 1% floating point variance in rounding logic
                return abs(float(gt_norm) - float(pred_norm)) < 0.01
            except (ValueError, TypeError):
                return False

        if field == "is_dangerous":
            return bool(gt_norm) == bool(pred_norm)

        return gt_norm == pred_norm

    def calculate_metrics(self):
        """Generates a professional performance report."""
        logger.info(f"Loading datasets for audit...")
        try:
            gt_data = self._load_json(self.ground_truth_path)
            pred_data = self._load_json(self.prediction_path)
        except Exception as e:
            logger.critical(f"Audit aborted: {e}")
            return

        # Indexing for O(1) lookups
        gt_map = {item["id"]: item for item in gt_data}
        pred_map = {item["id"]: item for item in pred_data}
        
        field_accuracy = {field: 0 for field in self.evaluated_fields}
        total_emails = len(gt_map)
        correct_fields = 0
        total_fields = 0

        logger.info(f"Auditing results for {total_emails} records...")

        mismatches = []
        for email_id, gt_entry in gt_map.items():
            pred_entry = pred_map.get(email_id, {})
            
            for field in self.evaluated_fields:
                is_correct = self._compare(field, gt_entry.get(field), pred_entry.get(field))
                if is_correct:
                    field_accuracy[field] += 1
                    correct_fields += 1
                else:
                    mismatches.append({
                        "id": email_id,
                        "field": field,
                        "gt": gt_entry.get(field),
                        "pred": pred_entry.get(field)
                    })
                total_fields += 1

        # Mismatch logging (Top 10)
        if mismatches:
            print("\nSAMPLE MISMATCHES:")
            for m in mismatches[:10]:
                print(f"[{m['id']}] {m['field']}: GT='{m['gt']}' | PRED='{m['pred']}'")

        # Professional Terminal Report
        print("\n" + "╔" + "═"*48 + "╗")
        print(f"║{'LOGISTICS AI EXTRACTION BENCHMARK':^48}║")
        print("╠" + "═"*48 + "╣")
        print(f"║ Total Shipment Records: {total_emails:<23} ║")
        print("╟" + "─"*48 + "╢")
        
        for field, count in field_accuracy.items():
            acc = (count / total_emails) * 100 if total_emails > 0 else 0
            # Indicator for fields needing attention
            status = "PASS" if acc >= 95 else "LOW " 
            label = field.replace('_', ' ').title()
            print(f"║ {status} | {label:<22}: {acc:>6.1f}%{'':<11}║")

        overall_acc = (correct_fields / total_fields) * 100 if total_fields > 0 else 0
        
        print("╠" + "═"*48 + "╣")
        print(f"║ OVERALL ACCURACY SCORE : {overall_acc:>6.1f}%{'':<16} ║")
        print("╚" + "═"*48 + "╝\n")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    gt_path = os.getenv("GROUND_TRUTH_PATH", "data/ground_truth.json")
    pred_path = os.getenv("OUTPUT_PATH", "outputs/output_v6.json")
    
    evaluator = ShipmentEvaluator(gt_path, pred_path)
    evaluator.calculate_metrics()
