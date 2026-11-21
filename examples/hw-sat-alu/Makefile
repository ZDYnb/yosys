YOSYS ?= yosys
PYTHON ?= python3
HW_SAT ?= ./hw_sat

.PHONY: export compare
export:
	mkdir -p inputs
	$(YOSYS) -p 'read_verilog -sv alu.sv query.sv; script export.ys; sat -set trigger 1 -dump_cnf inputs/good.cnf'
	$(YOSYS) -p 'read_verilog -sv -DFAULTY_SPEC alu.sv query.sv; script export.ys; sat -set trigger 1 -dump_cnf inputs/bug.cnf'

compare:
	$(PYTHON) compare.py "$(HW_SAT)"
