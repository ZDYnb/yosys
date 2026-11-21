# Checking a 32-bit ALU with Yosys, MiniSAT and HW-SAT

Can any pair of operands make the ALU shift left by the wrong amount? This exercise starts with a circuit, exports that question as a SAT problem, and compares two solvers on the same file.

## 1. Read the design

[alu.sv](alu.sv) is a standalone RV32-style integer ALU. For operation 7 it computes `a << b[4:0]`. Five bits select a shift of 0 through 31 positions.

[query.sv](query.sv) builds an independent reference. It reverses the bits of `a`, shifts right, then reverses the result. The single output `trigger` goes high when operation 7 is selected and the ALU disagrees with the reference. Both operands and the operation are symbolic inputs.

## 2. Predict the answer

| Reference | Example or reasoning | Expected answer for trigger = 1 |
|---|---|---|
| Five shift bits | Reversing the bit order twice makes the right shift equivalent to the ALU's left shift. | UNSAT |
| Four shift bits | With a = 1 and b = 16, the ALU returns 65,536. The faulty reference shifts by zero and returns 1. | SAT |

The experiment changes one line in the reference using `FAULTY_SPEC`. Both queries use the same ALU.

## 3. Export the SAT problems

From this directory, run:

```sh
make export
```

The Makefile reads both Verilog files, flattens the check, and calls `sat -set trigger 1 -dump_cnf`. Yosys both exports the query and solves it. The checked-in files came from YoWASP Yosys 0.71 (b4c586fd3). To use that executable, run `make export YOSYS=yowasp-yosys`. Different tool revisions or synthesis passes can change the encoding.

| Exported DIMACS | Variables | Initial clauses | Yosys result |
|---|---:|---:|---|
| [Correct reference](inputs/good.cnf) | 4,966 | 13,949 | UNSAT |
| [Faulty reference](inputs/bug.cnf) | 4,917 | 13,802 | SAT |

These are general CNFs. Both solver modes receive identical bytes for each case. Four-literal conversion happens inside the hardware model.

## 4. Compare the results and runtime

The comparison uses the project's integrated `hw_sat` executable. Its `--mode minisat` runs the software MiniSAT baseline. Its `--mode full` runs the four-literal ALL-UP pipeline model. With a compatible HW-SAT checkout, build the executable at its repository root using `make -f model/Makefile all`. Then run from this example directory:

```sh
make compare HW_SAT=/absolute/path/to/build/integrated/hw_sat
```

[compare.py](compare.py) checks the expected answer and solver exit status. For SAT it also checks the returned assignment against every clause of the original DIMACS. For UNSAT the check is agreement with the expected equivalence result and the reference solvers. The command writes `local-results.json`. The recorded run is in [results.json](results.json), including the binary hash, input hashes, hardware settings, and all seven software timing samples.

| Query | MiniSAT | HW-SAT | MiniSAT solve, median | Modeled cycles | Estimated HW solve | HW estimate / software |
|---|---|---|---:|---:|---:|---:|
| Correct reference | UNSAT | UNSAT | 64.39 ms | 89,202,841 | 196.25 ms | 3.05× |
| Faulty reference | SAT | SAT | 6.51 ms | 5,185,252 | 11.41 ms | 1.75× |

Software time is measured around the native solve on an arm64 Mac. HW time is cycles × an assumed 2.2 ns period for the two-stage input tree. Both columns exclude RTL processing and initial formula loading. The measured C++ emulator solve times were 15.46 s and 1.10 s respectively. The hardware clock is an architectural assumption awaiting timing validation.

Both answers match. On these two queries the modeled hardware takes longer than software. This experiment exercises the solver interface through DIMACS files. Measuring an integrated Yosys backend would also require accounting for transfers and returning the result to Yosys.
