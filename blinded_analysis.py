#!/usr/bin/env python3
"""
Blinded Analysis Script for Sovereign Labyrinth Validation

This script performs statistical analysis on simulation results WITHOUT
revealing which dataset is intervention vs. control. It receives labeled
datasets (A/B) and outputs statistical test results with full audit trail.

USAGE:
    python3 blinded_analysis.py --dataset-a path/to/dataset_a.json --dataset-b path/to/dataset_b.json

OUTPUT:
    - statistical_analysis.json (blinded results)
    - analysis_audit.log (complete operation log)
"""

import argparse
import json
import hashlib
import datetime
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
import statistics

# Prevent any post-hoc metric selection by pre-defining all analysis parameters
PRIMARY_METRIC = "mean_time_to_collapse"  # Simulated years
SIGNIFICANCE_LEVEL = 0.05
MIN_EFFECT_SIZE = 0.10  # 10% improvement threshold


def compute_hash(data: Any) -> str:
    """Compute SHA256 hash of data for audit trail."""
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def load_dataset(path: str) -> Dict[str, Any]:
    """Load and validate dataset structure."""
    with open(path, 'r') as f:
        data = json.load(f)
    
    required_fields = ["run_id", "survival_time_years", "phase_lock_violations", 
                       "threshold_adaptations", "extinction_events_recovered"]
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
    
    return data


def t_test_two_sample(sample_a: List[float], sample_b: List[float]) -> Dict[str, float]:
    """
    Perform two-sample t-test (Welch's t-test for unequal variances).
    Returns t-statistic, degrees of freedom, and p-value.
    """
    n_a, n_b = len(sample_a), len(sample_b)
    mean_a, mean_b = statistics.mean(sample_a), statistics.mean(sample_b)
    var_a, var_b = statistics.variance(sample_a) if n_a > 1 else 0, \
                   statistics.variance(sample_b) if n_b > 1 else 0
    
    # Welch's t-test
    se = ((var_a / n_a) + (var_b / n_b)) ** 0.5
    if se == 0:
        return {"t_statistic": 0.0, "df": 0.0, "p_value": 1.0}
    
    t_stat = (mean_a - mean_b) / se
    
    # Welch-Satterthwaite degrees of freedom
    num = ((var_a / n_a) + (var_b / n_b)) ** 2
    denom = ((var_a / n_a) ** 2 / (n_a - 1)) + ((var_b / n_b) ** 2 / (n_b - 1))
    df = num / denom if denom > 0 else 0
    
    # Approximate p-value using normal distribution for large df
    # (In production, use scipy.stats.t.sf for exact calculation)
    from math import erf, sqrt
    p_value = 2 * (1 - erf(abs(t_stat) / sqrt(2))) if df > 30 else 0.05  # Simplified
    
    return {
        "t_statistic": round(t_stat, 6),
        "degrees_of_freedom": round(df, 2),
        "p_value": round(p_value, 6)
    }


def analyze_datasets(dataset_a: Dict, dataset_b: Dict) -> Dict[str, Any]:
    """Perform blinded statistical analysis."""
    
    # Extract primary metric values
    survival_a = [dataset_a["survival_time_years"]] if isinstance(dataset_a["survival_time_years"], (int, float)) else dataset_a["survival_time_years"]
    survival_b = [dataset_b["survival_time_years"]] if isinstance(dataset_b["survival_time_years"], (int, float)) else dataset_b["survival_time_years"]
    
    # Compute descriptive statistics
    stats_a = {
        "mean": statistics.mean(survival_a),
        "median": statistics.median(survival_a),
        "std_dev": statistics.stdev(survival_a) if len(survival_a) > 1 else 0.0,
        "min": min(survival_a),
        "max": max(survival_a),
        "n": len(survival_a)
    }
    
    stats_b = {
        "mean": statistics.mean(survival_b),
        "median": statistics.median(survival_b),
        "std_dev": statistics.stdev(survival_b) if len(survival_b) > 1 else 0.0,
        "min": min(survival_b),
        "max": max(survival_b),
        "n": len(survival_b)
    }
    
    # Calculate effect size (Cohen's d)
    pooled_std = ((stats_a["std_dev"]**2 + stats_b["std_dev"]**2) / 2) ** 0.5
    effect_size = (stats_a["mean"] - stats_b["mean"]) / pooled_std if pooled_std > 0 else 0.0
    percent_improvement = (stats_a["mean"] - stats_b["mean"]) / stats_b["mean"] if stats_b["mean"] > 0 else 0.0
    
    # Perform t-test
    t_result = t_test_two_sample(survival_a, survival_b)
    
    # Determine if acceptance criteria met
    criteria_met = {
        "effect_size_threshold": abs(percent_improvement) >= MIN_EFFECT_SIZE,
        "statistical_significance": t_result["p_value"] < SIGNIFICANCE_LEVEL,
        "direction_correct": percent_improvement > 0  # Assuming A should be better
    }
    
    overall_pass = all(criteria_met.values())
    
    return {
        "descriptive_statistics": {
            "dataset_a": stats_a,
            "dataset_b": stats_b
        },
        "effect_analysis": {
            "absolute_difference": round(stats_a["mean"] - stats_b["mean"], 4),
            "percent_improvement": round(percent_improvement * 100, 2),
            "cohens_d": round(effect_size, 4)
        },
        "statistical_test": t_result,
        "acceptance_criteria": {
            "minimum_effect_threshold": MIN_EFFECT_SIZE,
            "significance_level": SIGNIFICANCE_LEVEL,
            "criteria_results": criteria_met,
            "overall_pass": overall_pass
        },
        "interpretation": "PASS" if overall_pass else "FAIL"
    }


def main():
    parser = argparse.ArgumentParser(description="Blinded statistical analysis for validation")
    parser.add_argument("--dataset-a", required=True, help="Path to dataset A JSON")
    parser.add_argument("--dataset-b", required=True, help="Path to dataset B JSON")
    parser.add_argument("--output-dir", default=".", help="Output directory for results")
    args = parser.parse_args()
    
    # Initialize audit log
    audit_log = []
    timestamp = datetime.datetime.utcnow().isoformat() + "Z"
    
    def log_operation(operation: str, details: Dict):
        entry = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "operation": operation,
            "details": details
        }
        audit_log.append(entry)
        print(f"[AUDIT] {entry['timestamp']} - {operation}")
    
    log_operation("SCRIPT_START", {"script": "blinded_analysis.py", "version": "1.0"})
    
    try:
        # Load datasets
        log_operation("LOAD_DATASET_A", {"path": args.dataset_a})
        dataset_a = load_dataset(args.dataset_a)
        dataset_a["input_hash"] = compute_hash(dataset_a)
        
        log_operation("LOAD_DATASET_B", {"path": args.dataset_b})
        dataset_b = load_dataset(args.dataset_b)
        dataset_b["input_hash"] = compute_hash(dataset_b)
        
        # Verify datasets are blinded (no group labels)
        if "group_label" in dataset_a or "group_label" in dataset_b:
            raise ValueError("Datasets must be blinded - remove group_label fields")
        
        log_operation("BLINDING_VERIFICATION", {"status": "PASSED"})
        
        # Perform analysis
        log_operation("STATISTICAL_ANALYSIS", {"method": "two_sample_t_test"})
        results = analyze_datasets(dataset_a, dataset_b)
        
        # Add metadata
        results["metadata"] = {
            "analysis_timestamp": timestamp,
            "script_version": "1.0",
            "primary_metric": PRIMARY_METRIC,
            "significance_level": SIGNIFICANCE_LEVEL,
            "minimum_effect_threshold": MIN_EFFECT_SIZE
        }
        
        results["input_hashes"] = {
            "dataset_a": dataset_a.get("input_hash"),
            "dataset_b": dataset_b.get("input_hash")
        }
        
        results["audit_statement"] = "This analysis was performed on blinded datasets. The identity of intervention vs. control groups was not revealed during computation."
        
        # Save results
        output_path = Path(args.output_dir) / "statistical_analysis.json"
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        log_operation("SAVE_RESULTS", {"path": str(output_path), "hash": compute_hash(results)})
        
        # Save audit log
        audit_output = Path(args.output_dir) / "analysis_audit.log"
        with open(audit_output, 'w') as f:
            for entry in audit_log:
                f.write(json.dumps(entry) + "\n")
        
        print(f"\n✅ Analysis complete. Results saved to: {output_path}")
        print(f"📋 Audit log saved to: {audit_output}")
        print(f"\n🎯 RESULT: {results['interpretation']}")
        print(f"   Effect Size: {results['effect_analysis']['percent_improvement']:.2f}%")
        print(f"   P-Value: {results['statistical_test']['p_value']:.6f}")
        print(f"   Criteria Met: {results['acceptance_criteria']['overall_pass']}")
        
        return 0
        
    except Exception as e:
        log_operation("ERROR", {"message": str(e)})
        print(f"❌ Error: {e}", file=sys.stderr)
        
        # Save error audit log
        audit_output = Path(args.output_dir) / "analysis_audit.log"
        with open(audit_output, 'w') as f:
            for entry in audit_log:
                f.write(json.dumps(entry) + "\n")
        
        return 1


if __name__ == "__main__":
    sys.exit(main())
