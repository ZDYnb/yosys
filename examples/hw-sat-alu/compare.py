"""Run both solver modes on the same exported DIMACS files."""
import argparse
import hashlib
import json
import platform
import statistics
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HW = """--mode full --four-cnf --bcp-variant all-pipeline --fixed-clause-order
--check-cdcl --cycle-model-v3 --input-tree-stages 2 --clock-ns 2.2
--arrays 4096 --rows 128 --variables 65536 --ait-rows 65536 --stack-rows 65536
--source-tokens 16384 --conflict-budget 0""".split()


def solve(binary, cnf, flags, expected):
    run = subprocess.run([binary, "--cnf", cnf, *flags], capture_output=True, text=True)
    if run.returncode != {"SAT": 10, "UNSAT": 20}[expected]:
        raise RuntimeError(f"{cnf.name}: {run.returncode} {run.stderr} {run.stdout[:300]}")
    result = json.loads(run.stdout)
    if result["status"] != expected:
        raise ValueError(f"Unexpected status for {cnf.name}")
    if expected == "SAT":
        truth = set(result["assignment"])
        if 0 in truth or any(-lit in truth for lit in truth):
            raise ValueError("Inconsistent witness")
        # Yosys writes one complete clause per line.
        for line in cnf.read_text().splitlines():
            if line and line[0] not in "pc":
                clause = [int(word) for word in line.split()]
                if clause[-1] != 0 or not any(lit in truth for lit in clause[:-1]):
                    raise ValueError(f"Witness fails clause: {line}")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", type=Path, help="HW-SAT integrated hw_sat executable")
    parser.add_argument("--output", type=Path, default=Path("local-results.json"))
    args = parser.parse_args()
    binary = args.binary.resolve()
    report = {"binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
              "host": platform.system() + " " + platform.machine(), "hw_flags": HW, "cases": {}}
    for variant, expected in [("good", "UNSAT"), ("bug", "SAT")]:
        cnf = ROOT / "inputs" / (variant + ".cnf")
        native = [solve(binary, cnf, ["--mode", "minisat", "--conflict-budget", "0"], expected)
                  for _ in range(7)]
        hw = solve(binary, cnf, HW, expected)
        timing = hw["cycle_model"]
        if not timing["complete"] or timing["scope"] != "solve_only":
            raise ValueError("Incomplete solve timing")
        samples = [r["solve_seconds"] for r in native]
        report["cases"][variant] = {
            "cnf_sha256": hashlib.sha256(cnf.read_bytes()).hexdigest(),
            "variables": hw["variables"], "clauses": hw["input_clauses"],
            "minisat": native[0]["status"], "hw_sat": hw["status"],
            "sat_witnesses_checked": expected == "SAT",
            "minisat_solve_s": samples, "minisat_median_s": statistics.median(samples),
            "modeled_cycles": timing["total_cycles"], "estimated_hw_s": timing["estimated_ns"] * 1e-9,
            "emulator_host_solve_s": hw["solve_seconds"]}
        print(variant, report["cases"][variant], flush=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
