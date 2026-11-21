module query(input [31:0] a, b, input [3:0] op, output trigger);
    wire [31:0] actual, reversed, shifted, expected;
    alu dut(.a(a), .b(b), .op(op), .result(actual));

    // Reversing the bit order turns a right shift into a left shift.
    for (genvar i = 0; i < 32; i = i + 1)
        assign reversed[i] = a[31-i];
`ifdef FAULTY_SPEC
    assign shifted = reversed >> b[3:0];
`else
    assign shifted = reversed >> b[4:0];
`endif
    for (genvar i = 0; i < 32; i = i + 1)
        assign expected[i] = shifted[31-i];

    assign trigger = (op == 7) && (actual != expected);
endmodule
