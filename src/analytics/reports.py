import os
import json
from .evaluator import run_evaluation

def generate_reports(output_dir="data"):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    summary, calibration = run_evaluation()
    
    with open(os.path.join(output_dir, "performance_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
        
    with open(os.path.join(output_dir, "calibration_report.json"), "w") as f:
        json.dump(calibration, f, indent=2)
        
    print(f"Reports successfully generated in {output_dir}/")

if __name__ == "__main__":
    generate_reports()
